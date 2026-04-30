# ansible-vault — quick guide

This folder shows how to handle secrets without committing them.

## Encrypt the example
```bash
cp secrets.example.yml secrets.yml
ansible-vault encrypt secrets.yml
```

## Reference from a playbook
```yaml
- hosts: all
  vars_files:
    - ../vault/secrets.yml
  roles:
    - baseline
```

## Run
```bash
ansible-playbook playbooks/baseline.yml --ask-vault-pass
# or in CI:
ansible-playbook playbooks/baseline.yml --vault-password-file ~/.vault_pass
```

## What NOT to commit
- `secrets.yml` (encrypted is fine, but easier to gitignore the whole file)
- `~/.vault_pass`
- any file matching `*.key`, `*.pem`, `.env`
