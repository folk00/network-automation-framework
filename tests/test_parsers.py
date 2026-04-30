"""Smoke tests for the parsers — run with `python -m unittest tests/test_parsers.py`."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsers.interfaces import parse_ip_int_brief
from src.parsers.ospf import parse_ospf_neighbors, parse_ospf_interface_brief


SAMPLE_IP_INT_BRIEF = """\
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/1   10.20.1.1       YES manual up                    up
GigabitEthernet0/0/2   10.20.1.5       YES manual up                    up
GigabitEthernet0/0/4   10.20.1.13      YES manual down                  down
Loopback0              10.255.0.11     YES manual up                    up
""".splitlines()

SAMPLE_OSPF_NBRS = """\
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.255.0.12     1     FULL/DR         00:00:35    10.20.1.18      GigabitEthernet0/0/5
10.255.0.21     1     FULL/BDR        00:00:33    10.20.1.10      GigabitEthernet0/0/3
""".splitlines()

SAMPLE_OSPF_IB = """\
Interface             PID   Area    IP Address/Mask        Cost  State Nbrs F/C
Lo0                   10    0       10.255.0.11/32         1     LOOP  0/0
Gi0/0/1               10    0       10.20.1.1/30           1     P2P   1/1
""".splitlines()


class ParserTests(unittest.TestCase):

    def test_ip_int_brief(self):
        s = parse_ip_int_brief(SAMPLE_IP_INT_BRIEF)
        self.assertEqual(s["GigabitEthernet0/0/1"].status, "up")
        self.assertEqual(s["GigabitEthernet0/0/4"].status, "down")
        self.assertIn("Loopback0", s)

    def test_ospf_neighbors(self):
        n = parse_ospf_neighbors(SAMPLE_OSPF_NBRS)
        self.assertEqual(len(n), 2)
        self.assertTrue(n[0].state.startswith("FULL"))
        self.assertEqual(n[0].interface, "GigabitEthernet0/0/5")

    def test_ospf_interface_brief(self):
        i = parse_ospf_interface_brief(SAMPLE_OSPF_IB)
        self.assertEqual(len(i), 2)
        self.assertEqual(i[1].pid, 10)
        self.assertEqual(i[1].state, "P2P")


if __name__ == "__main__":
    unittest.main()
