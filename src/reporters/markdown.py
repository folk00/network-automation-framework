"""Markdown change record."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime


def write(results: list[dict],
          validations: list[dict],
          out_dir: str | Path,
          mode: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"change_record_{mode}_{ts}.md"

    lines: list[str] = [
        f"# Change record — mode: `{mode}`",
        f"_generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        f"Hosts: **{len(results)}**",
        "",
    ]

    val_by_host = {v["host"]: v for v in validations}

    for r in sorted(results, key=lambda x: x["host"]):
        lines.append(f"## {r['host']}")
        lines.append(f"- mode: `{r['mode']}`")
        lines.append(f"- ok: **{r.get('ok', False)}**")
        if not r.get("ok") and r.get("error"):
            lines.append(f"- error: `{r['error']}`")

        v = val_by_host.get(r["host"])
        if v is not None:
            lines.append(f"- validation: **{'PASS' if v['passed'] else 'FAIL'}**")
            for f in v["findings"]:
                lines.append(f"  - {f}")

        if r["diff"]:
            lines.append("")
            lines.append("<details><summary>config diff</summary>")
            lines.append("")
            lines.append("```diff")
            lines.extend(r["diff"][:400])
            if len(r["diff"]) > 400:
                lines.append(f"... ({len(r['diff']) - 400} more lines)")
            lines.append("```")
            lines.append("</details>")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
