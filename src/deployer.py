"""Concurrent deployer with dry-run, deploy, and IOS rollback timer.

dry-run mode  : connect, fetch running config, compute unified diff, return.
deploy mode   : arm `configure terminal revert timer N`, push config, confirm,
                run post-check show commands, return them for the validator.

The deployer reuses the shared ConnectionPool so collection and deployment
share authenticated sessions.
"""

from __future__ import annotations

import concurrent.futures
import difflib
from typing import Any

from .connection import pool

POST_CMDS = [
    "show ip interface brief",
    "show ip ospf neighbor",
    "show ip ospf interface brief",
    "show ip route ospf",
    "show running-config | section router ospf",
]

ROLLBACK_TIMER_MINUTES = 5


def _push_one(host: dict, rendered: list[str], mode: str, creds: dict) -> dict:
    ip = host["management_ip"]
    conn = pool.get(ip, **creds)
    try:
        running = conn.send_command("show running-config").splitlines()
        diff = list(difflib.unified_diff(
            running, rendered,
            fromfile=f"{host['hostname']}/running",
            tofile=f"{host['hostname']}/intended",
            lineterm="",
        ))
        if mode == "dry-run":
            return {"host": host["hostname"], "mode": "dry-run",
                    "diff": diff, "post": {}, "ok": True}

        conn.send_config_set([f"configure terminal revert timer {ROLLBACK_TIMER_MINUTES}"])
        conn.send_config_set(rendered)
        conn.send_command("configure confirm")

        post = {cmd: conn.send_command(cmd).splitlines() for cmd in POST_CMDS}
        return {"host": host["hostname"], "mode": "deploy",
                "diff": diff, "post": post, "ok": True}
    except Exception as exc:
        return {"host": host["hostname"], "mode": mode,
                "diff": [], "post": {}, "ok": False, "error": str(exc)}
    finally:
        pool.put(ip, conn)


def deploy(hosts: list[dict],
           rendered_by_host: dict[str, list[str]],
           mode: str = "dry-run",
           workers: int = 8,
           creds: dict | None = None) -> list[dict]:
    if mode not in ("dry-run", "deploy"):
        raise ValueError(f"unknown mode: {mode}")
    creds = creds or {}
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(_push_one, h, rendered_by_host[h["hostname"]], mode, creds): h
            for h in hosts
        }
        for f in concurrent.futures.as_completed(futs):
            results.append(f.result())
    return results
