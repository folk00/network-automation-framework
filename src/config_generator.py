"""Render Cisco IOS config from a host record using Jinja2."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
)


def render(host: dict, template_name: str = "ios_ospf.j2") -> list[str]:
    rendered = _env.get_template(template_name).render(host=host)
    return rendered.splitlines()


def render_to_file(host: dict, out_dir: str | Path,
                   template_name: str = "ios_ospf.j2") -> Path:
    out = Path(out_dir) / f"rendered_{host['hostname']}.cfg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(render(host, template_name)) + "\n", encoding="utf-8")
    return out
