"""Parsers for OSPF show commands."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Neighbor ID     Pri   State           Dead Time   Address         Interface
_NEI = re.compile(
    r"^(?P<rid>\d+\.\d+\.\d+\.\d+)\s+\d+\s+(?P<state>\S+(?:/\S+)?)\s+"
    r"\S+\s+(?P<addr>\d+\.\d+\.\d+\.\d+)\s+(?P<intf>\S+)\s*$"
)

# show ip ospf interface brief
# Interface    PID   Area    IP Address/Mask    Cost  State Nbrs F/C
_INTF = re.compile(
    r"^(?P<intf>\S+)\s+(?P<pid>\d+)\s+(?P<area>\S+)\s+"
    r"(?P<ipmask>\d+\.\d+\.\d+\.\d+/\d+)\s+(?P<cost>\d+)\s+"
    r"(?P<state>\S+)\s+(?P<nbrs>\d+/\d+)\s*$"
)


@dataclass(frozen=True)
class OspfNeighbor:
    router_id: str
    state: str
    address: str
    interface: str


@dataclass(frozen=True)
class OspfInterface:
    name: str
    pid: int
    area: str
    ip_mask: str
    cost: int
    state: str
    nbrs: str


def parse_ospf_neighbors(lines: list[str]) -> list[OspfNeighbor]:
    out: list[OspfNeighbor] = []
    for raw in lines or []:
        m = _NEI.match(raw.rstrip())
        if m:
            out.append(OspfNeighbor(
                router_id=m.group("rid"),
                state=m.group("state"),
                address=m.group("addr"),
                interface=m.group("intf"),
            ))
    return out


def parse_ospf_interface_brief(lines: list[str]) -> list[OspfInterface]:
    out: list[OspfInterface] = []
    for raw in lines or []:
        m = _INTF.match(raw.rstrip())
        if m:
            out.append(OspfInterface(
                name=m.group("intf"),
                pid=int(m.group("pid")),
                area=m.group("area"),
                ip_mask=m.group("ipmask"),
                cost=int(m.group("cost")),
                state=m.group("state"),
                nbrs=m.group("nbrs"),
            ))
    return out
