# Ansible equivalent — same OSPF deployment, idiomatic Ansible

This folder ships the **same workflow** as the Python framework
(`render → dry-run → deploy → validate`) implemented as an Ansible role,
so you can compare the two approaches side by side.

## Layout

```
ansible/
├── ansible.cfg
├── requirements.yml                 # collections (cisco.ios, ansible.netcommon)
├── .ansible-lint                    # lint profile + skip rules
├── inventories/
│   └── lab.yml                      # 3 routers, mirrors examples/inventory.yml
├── group_vars/
│   ├── all.yml                      # site-wide defaults (NTP, DNS, SNMP, banner)
│   ├── edge.yml                     # edge-group overrides
│   └── aggregation.yml              # agg-group overrides
├── host_vars/
│   └── lab-edge-r1.yml              # per-host overrides (variable layering demo)
├── vault/
│   ├── secrets.example.yml          # template for ansible-vault
│   └── README.md                    # vault workflow
├── playbooks/
│   ├── render.yml                   # connection: local, just render to ./rendered/
│   ├── dry_run.yml                  # ios_config check_mode + diff
│   ├── deploy.yml                   # OSPF role: serial:4, rollback timer, validate
│   ├── baseline.yml                 # NTP/DNS/SNMP/users/banner via baseline role
│   ├── backup.yml                   # pull running-config to ./backups/
│   └── check_reachability.yml       # smoke test
└── roles/
    ├── ospf_edge/                   # OSPF process, router-id, MD5, validation
    └── baseline/                    # site baseline, idempotent merge
```

## Quick start

```bash
# requires: ansible-core >= 2.15
ansible-galaxy collection install -r requirements.yml

cd ansible

# 0. Reachability smoke test
NET_USER=admin NET_PASS=*** NET_SECRET=*** \
ansible-playbook playbooks/check_reachability.yml

# 1. Render only (no devices)
ansible-playbook playbooks/render.yml --connection=local

# 2. Dry-run (connects, shows diff, no changes)
ansible-playbook playbooks/dry_run.yml --diff

# 3. Pull a backup before any change
ansible-playbook playbooks/backup.yml

# 4. Apply baseline (NTP/SNMP/users/banner) — needs vault
cp vault/secrets.example.yml vault/secrets.yml
ansible-vault encrypt vault/secrets.yml
ansible-playbook playbooks/baseline.yml --ask-vault-pass

# 5. Deploy OSPF with rollback timer + post-validation
ansible-playbook playbooks/deploy.yml
```

## Multi-vendor — runs against the cEOS lab too

The same `ospf_edge` role targets both Cisco IOS (production) and Arista
EOS (lab), picking the right template based on `ansible_network_os`. To
exercise the role against real virtual routers:

```bash
# from the repo root
cd lab && make up                       # spin up 3 cEOS nodes
cd ../ansible
ansible-playbook -i inventories/clab.yml playbooks/check_reachability.yml
ansible-playbook -i inventories/clab.yml playbooks/deploy.yml
```

The lab inventory (`inventories/clab.yml`) declares `Ethernet1/2` interfaces
and `arista.eos.eos` as the network OS. The role then selects
`templates/eos_ospf.j2` instead of `ios_ospf.j2`. See `lab/README.md` for
how to obtain the free cEOS image.

## Lint + CI

`.ansible-lint` ships with a `production` profile. CI workflow at
`.github/workflows/ansible-ci.yml` runs `yamllint`, `ansible-lint`, and
`ansible-playbook --syntax-check` on every push that touches `ansible/`.

```bash
pip install ansible-lint yamllint
ansible-lint
```

## Python framework vs Ansible — when to pick which

| Concern | Python framework (`src/`) | Ansible (`ansible/`) |
|---|---|---|
| **Concurrency** | `ThreadPoolExecutor` + `ConnectionPool` (per-IP lock, `show clock` liveness) | `forks` + `serial` batches; one persistent SSH per host |
| **Idempotency** | manual — diff against running config | built into `cisco.ios.ios_config` |
| **State validation** | regex parsers + asserts in code | `assert` module against captured `stdout` |
| **Rollback** | `configure terminal revert timer N` + `configure confirm` | same, via handler |
| **Templating** | Jinja2 (StrictUndefined) | Jinja2 (Ansible's built-in) |
| **Custom parsing** | first-class — pure functions, unit-tested | possible but awkward; usually ends up calling a Python module anyway |
| **Onboarding cost** | reader needs Python | reader needs Ansible mental model |
| **Best fit** | bespoke parsing/correlation, large fan-out, custom reporting | inventory-driven config standardization across many roles/sites |

**Honest take for the demos**: in many shops Ansible would be the right
default. I built the Python tool because the *parsing and correlation*
requirements were specific enough that an Ansible task would have been a thin
wrapper around the same Python anyway, and I wanted full control over the
connection pool and the report layout. The same intent maps cleanly to
Ansible — this folder proves it.

## Design notes

- "I can implement this either way; here's the same workflow as a role."
- "I picked custom Python for the discovery tool because the classifier
  precedence and CDP/OSPF correlation were the hard part, not the SSH layer."
- "For pure config standardization across many sites, I would lead with
  Ansible roles + `cisco.ios.ios_config`, because idempotency and inventory
  scaling are solved problems there."
- "Both paths converge on the same Jinja2 template — the template is the
  source of truth for what the config should look like."
