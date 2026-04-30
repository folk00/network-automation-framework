"""Parser for ``show ip interface brief`` (IOS / IOS-XE)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Interface  IP-Address  OK?  Method  Status  Protocol
_LINE = re.compile(
    r"^(?P<intf>\S+)\s+(?P<ip>\S+)\s+\S+\s+\S+\s+"
    r"(?P<status>administratively down|up|down)\s+(?P<protocol>up|down)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InterfaceState:
    name: str
    ip: str
    status: str
    protocol: str


def parse_ip_int_brief(lines: list[str]) -> dict[str, InterfaceState]:
    out: dict[str, InterfaceState] = {}
    for raw in lines or []:
        m = _LINE.match(raw.rstrip())
        if not m:
            continue
        s = InterfaceState(
            name=m.group("intf"),
            ip=m.group("ip"),
            status=m.group("status").lower().replace("administratively down", "admin-down"),
            protocol=m.group("protocol").lower(),
        )
        out[s.name] = s
    return out
