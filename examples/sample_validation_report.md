# Example post-deployment validation report (`change_record_deploy_*.md`)

> Generated from a lab run against three IOS-XE routers.

## lab-edge-r1
- mode: `deploy`
- ok: **True**
- validation: **PASS**

## lab-edge-r2
- mode: `deploy`
- ok: **True**
- validation: **PASS**

## lab-agg-r1
- mode: `deploy`
- ok: **True**
- validation: **FAIL**
  - GigabitEthernet0/0/4: not up/up (status=down protocol=down)
  - GigabitEthernet0/0/4: no OSPF neighbor in FULL state

When `validation` is FAIL the rollback timer fires automatically (5 minutes
by default) and the router reverts to the prior config.
