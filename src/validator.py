"""Post-change validation: parse show output and assert expected state."""

from __future__ import annotations

from .parsers.interfaces import parse_ip_int_brief
from .parsers.ospf import parse_ospf_neighbors


def check_interfaces_up(post: dict, expected: list[str]) -> list[str]:
    state = parse_ip_int_brief(post.get("show ip interface brief", []))
    findings = []
    for name in expected:
        s = state.get(name)
        if s is None:
            findings.append(f"{name}: not present in 'show ip interface brief'")
        elif s.status != "up" or s.protocol != "up":
            findings.append(f"{name}: not up/up (status={s.status} protocol={s.protocol})")
    return findings


def check_ospf_neighbors(post: dict, expected_intfs: list[str]) -> list[str]:
    neighbors = parse_ospf_neighbors(post.get("show ip ospf neighbor", []))
    intfs_with_full = {n.interface for n in neighbors if n.state.startswith("FULL")}
    return [f"{i}: no OSPF neighbor in FULL state" for i in expected_intfs
            if i not in intfs_with_full]


def validate(result: dict, host: dict) -> dict:
    if not result.get("ok"):
        return {"host": host["hostname"], "passed": False,
                "findings": [f"deployment failed: {result.get('error','unknown')}"]}

    routed = [i["name"] for i in host["interfaces"]]
    loop_name = f"Loopback{host['loopback']['id']}"
    findings: list[str] = []
    findings += check_interfaces_up(result["post"], routed + [loop_name])
    findings += check_ospf_neighbors(result["post"], routed)
    return {"host": host["hostname"], "passed": not findings, "findings": findings}
