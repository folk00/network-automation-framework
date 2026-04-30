"""CLI entry point.

Modes:
  render   — render configs from inventory; no device connections.
  dry-run  — connect to each device, fetch running config, emit unified diff.
  deploy   — push intended config with IOS rollback timer + post-validation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make `src` importable when run as `python main.py`
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config_generator import render, render_to_file
from src.inventory_loader import load
from src.reporters import excel as excel_report
from src.reporters import markdown as md_report

OUT_DIR = ROOT / "outputs"


def _creds_from_env() -> dict:
    user = os.environ.get("NET_USER")
    pwd  = os.environ.get("NET_PASS")
    if not (user and pwd):
        sys.exit("error: NET_USER and NET_PASS environment variables are required for dry-run/deploy")
    return {"user": user, "pwd": pwd, "sec": os.environ.get("NET_SECRET")}


def main() -> int:
    ap = argparse.ArgumentParser(prog="network-automation-framework")
    ap.add_argument("--inventory", required=True, help="path to YAML inventory")
    ap.add_argument("--mode", choices=["render", "dry-run", "deploy"], default="render")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    hosts = load(args.inventory)
    rendered_by_host = {h["hostname"]: render(h) for h in hosts}

    if args.mode == "render":
        for h in hosts:
            path = render_to_file(h, OUT_DIR)
            print(f"rendered {path}")
        return 0

    # Both dry-run and deploy go through the deployer (which imports Netmiko).
    from src.deployer import deploy
    from src.validator import validate

    creds = _creds_from_env()
    results = deploy(hosts, rendered_by_host, mode=args.mode,
                     workers=args.workers, creds=creds)

    validations: list[dict] = []
    if args.mode == "deploy":
        host_by_name = {h["hostname"]: h for h in hosts}
        validations = [validate(r, host_by_name[r["host"]]) for r in results]

    md_path  = md_report.write(results, validations, OUT_DIR, args.mode)
    xls_path = excel_report.write(results, validations, OUT_DIR, args.mode)
    print(f"wrote {md_path}")
    print(f"wrote {xls_path}")

    if args.mode == "deploy" and any(not v["passed"] for v in validations):
        print("validation FAILED on one or more hosts", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
