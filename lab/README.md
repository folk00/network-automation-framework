# Lab — containerlab + cEOS

This folder spins up a 3-node Arista cEOS lab in Docker via
[containerlab](https://containerlab.dev/), then runs the same Ansible role
that targets Cisco IOS in production. The OSPF logic, validation, and report
flow are exercised against **real virtual routers**, not mocks.

## Topology

Live `containerlab graph` view of the running lab:

![lab topology](../evidence/lab_topology.png)

```
            Et1 ──────── Et1
   ┌──── r1 ────────────── r2 ────┐
   │  Et2                     Et2 │
   │                              │
   └──────── r3 ──────────────────┘
            Et1               Et2

mgmt:  r1 = 172.30.30.11   loopback: 10.255.0.11/32
       r2 = 172.30.30.12             10.255.0.12/32
       r3 = 172.30.30.13             10.255.0.13/32
links: 10.20.1.0/30, 10.20.1.4/30, 10.20.1.8/30   all OSPF area 0 + MD5
```

## Proof — actual deploy output

Real run against the cEOS lab. Render → push EOS config in atomic session →
wait for OSPF to converge → assert every interface up/up and every routed link
has an OSPF neighbor in `FULL` state. **Zero failures, three nodes:**

![ansible playbook success](../evidence/playbook_success.png)

OSPF neighbor table on r1 after deploy:

```
$ docker exec r1 Cli -p 15 -c 'show ip ospf neighbor'
Neighbor ID   Pri State      Dead Time   Address     Interface
10.255.0.13   1   FULL/DR    00:00:36    10.20.1.6   Ethernet2
10.255.0.12   1   FULL/DR    00:00:35    10.20.1.2   Ethernet1
```

ECMP routes installed via both paths:

```
$ docker exec r1 Cli -p 15 -c 'show ip route ospf'
 O   10.20.1.8/30 [110/20]
       via 10.20.1.2, Ethernet1
       via 10.20.1.6, Ethernet2
 O   10.255.0.12/32 [110/20] via 10.20.1.2, Ethernet1
 O   10.255.0.13/32 [110/20] via 10.20.1.6, Ethernet2
```

## One-time setup

### 1. Install containerlab (Linux or WSL2)
```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

### 2. Get the cEOS image (free, requires Arista account)
- Download from <https://www.arista.com/en/support/software-download>
  (look for `cEOS-lab-4.32.x.tar`).
- Import into Docker:
  ```bash
  docker import cEOS-lab-4.32.0F.tar ceos:4.32.0F
  ```

### 3. Install Ansible
```bash
pip install "ansible-core>=2.15"
ansible-galaxy collection install -r ../ansible/requirements.yml
```

## Run it

```bash
cd lab

make up        # spin up 3 cEOS containers (~30s)
make reach     # ansible reachability check via SSH
make dryrun    # render + diff vs running config (no changes)
make deploy    # push OSPF config + validate neighbors reach FULL
make destroy   # tear it all down
```

### One-shot

```bash
make all       # up + reach + deploy + validate
```

## What "validation" actually means here

`make deploy` runs `ansible-playbook deploy.yml` which:

1. Renders the **Arista** OSPF template per host (`templates/eos_ospf.j2`).
2. Pushes it via `arista.eos.eos_config` against the live cEOS container.
3. Runs the post-check show commands (`show ip ospf neighbor`,
   `show ip interface brief`).
4. Asserts every routed interface is `up/up` AND has an OSPF neighbor in
   `FULL` state.

If OSPF doesn't converge, the playbook **fails with the specific interface
and reason** — same logic the production Cisco-IOS path uses, just against
a different platform.

## Cisco IOS vs Arista EOS — what changes in the templates

| Concern | Cisco IOS template | Arista EOS template | Same? |
|---|---|---|---|
| Hostname, loopback, IP addressing | identical | identical | ✓ |
| `router ospf <pid>` + `router-id` | identical | identical | ✓ |
| Per-interface OSPF + MD5 | `ip ospf <pid> area 0` + `ip ospf message-digest-key` | same syntax | ✓ |
| Interface names | `GigabitEthernet0/0/1` | `Ethernet1` | ✗ |
| Rollback | `configure terminal revert timer` | `configure session` + `commit` | ✗ |

Two templates live side-by-side in `templates/`. The role picks the right
one based on `ansible_network_os` per host — same role, multi-vendor.

## Why this exists

To prove the framework works end-to-end against real network devices that
anyone can spin up for free. Production targets Cisco IOS/IOS-XE; the lab
targets Arista cEOS because:

- cEOS is freely downloadable.
- Cisco IOSv / CML images aren't redistributable, so they can't run in
  public CI or be cloned-and-run by anyone.

The trade-off is honest: ~70-75% of the template content is identical
between IOS and EOS. The differences (interface naming, rollback mechanism)
are isolated in dedicated templates so neither stays Cisco- or
Arista-specific.

## Troubleshooting

- **`docker permission denied`** → add yourself to the `docker` group or run
  with `sudo`.
- **`image ceos:4.32.0F not found`** → run `make check-image` for the import
  command.
- **`make up` hangs** → cEOS needs ~30-45s to boot. Run
  `docker logs clab-ospf-lab-r1` to see boot progress.
- **SSH refuses connection** → cEOS opens SSH after eAPI is up; wait
  another 10s and retry `make reach`.
