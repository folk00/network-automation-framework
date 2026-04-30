"""YAML inventory loader with light schema validation."""

from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Any

import yaml

REQUIRED_HOST_KEYS = {"hostname", "management_ip", "loopback",
                      "ospf_process_id", "ospf_router_id", "interfaces"}
REQUIRED_INTF_KEYS = {"name", "ip", "mask", "ospf_area"}


class InventoryError(ValueError):
    pass


def load(path: str | Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "routers" not in raw:
        raise InventoryError("inventory must be a mapping containing 'routers'")
    hosts = raw["routers"]
    for h in hosts:
        _validate_host(h)
    return hosts


def _validate_host(host: dict) -> None:
    missing = REQUIRED_HOST_KEYS - host.keys()
    if missing:
        raise InventoryError(f"{host.get('hostname','?')}: missing keys {sorted(missing)}")
    _check_ip(host["management_ip"], host["hostname"], "management_ip")
    _check_ip(host["loopback"]["ip"], host["hostname"], "loopback.ip")
    _check_ip(host["ospf_router_id"], host["hostname"], "ospf_router_id")
    if not host["interfaces"]:
        raise InventoryError(f"{host['hostname']}: at least one interface required")
    for intf in host["interfaces"]:
        miss = REQUIRED_INTF_KEYS - intf.keys()
        if miss:
            raise InventoryError(
                f"{host['hostname']}::{intf.get('name','?')}: missing {sorted(miss)}")
        _check_ip(intf["ip"], host["hostname"], f"{intf['name']}.ip")
        _check_ip(intf["mask"], host["hostname"], f"{intf['name']}.mask", mask=True)


def _check_ip(value: str, host: str, field: str, mask: bool = False) -> None:
    try:
        ipaddress.IPv4Address(value)
    except Exception as exc:
        raise InventoryError(f"{host}: {field} '{value}' is not a valid IPv4 {'mask' if mask else 'address'}") from exc
