"""Thread-safe Netmiko connection pool.

Keyed by management IP. Reuses live SSH sessions across collection passes
so concurrent workers don't keep reauthenticating against the same device.
Each cached connection is liveness-checked with ``show clock`` before reuse.

Importing this module does NOT require Netmiko to be installed; the import
of ``netmiko`` is deferred so unit tests and ``--mode render`` can run in a
clean environment.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Optional


class ConnectionPool:
    """Per-IP pooled Netmiko connections with a liveness check on reuse."""

    def __init__(self, fast_cli: bool = False, max_idle_per_host: int = 2):
        self.fast_cli = fast_cli
        self.max_idle_per_host = max_idle_per_host
        self._conns: dict[str, list] = defaultdict(list)
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    def get(self, ip: str, user: str, pwd: str, sec: Optional[str] = None,
            device_type: str = "cisco_ios"):
        from netmiko import ConnectHandler
        with self._locks[ip]:
            while self._conns[ip]:
                conn = self._conns[ip].pop()
                try:
                    conn.send_command("show clock", delay_factor=0.1, max_loops=5)
                    return conn
                except Exception:
                    self._safe_close(conn)
            conn = ConnectHandler(
                device_type=device_type, ip=ip,
                username=user, password=pwd, secret=sec or "",
                fast_cli=self.fast_cli,
            )
            if sec:
                conn.enable()
            conn.send_command("terminal length 0")
            return conn

    def put(self, ip: str, conn) -> None:
        with self._locks[ip]:
            if len(self._conns[ip]) < self.max_idle_per_host:
                self._conns[ip].append(conn)
            else:
                self._safe_close(conn)

    def cleanup(self) -> None:
        for ip, lst in list(self._conns.items()):
            with self._locks[ip]:
                while lst:
                    self._safe_close(lst.pop())

    @staticmethod
    def _safe_close(conn) -> None:
        try:
            conn.disconnect()
        except Exception:
            pass


pool = ConnectionPool()
