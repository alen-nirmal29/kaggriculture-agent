"""Build the exact, single-file Kaggriculture V9 upload artifact."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"

MODULES = [
    "agent_v2.state", "agent_v2.crops", "agent_v2.economics",
    "agent_v2.endgame", "agent_v2.market", "agent_v2.routing",
    "agent_v3.state", "agent_v3.crops", "agent_v3.economics",
    "agent_v3.endgame", "agent_v3.market", "agent_v3.routing",
    "agent_v3.strategy",
    "agent_v4.state", "agent_v4.crops", "agent_v4.economics",
    "agent_v4.endgame", "agent_v4.market", "agent_v4.routing",
    "agent_v4.workers", "agent_v4.strategy",
    "agent_v6.state", "agent_v6.animals", "agent_v6.strategy",
    "agent_v8.state", "agent_v8.opponent",
    "agent_v9.config", "agent_v9.state", "agent_v9.workers",
    "agent_v9.strategy", "main_v9",
]


def source_path(name: str) -> Path:
    parts = name.split(".")
    return ROOT.joinpath(*parts).with_suffix(".py")


def build() -> str:
    lines = [
        '"""Kaggriculture V9 final standalone agent. Generated; do not hand-edit."""',
        "import sys as _sys, types as _types",
        "def _pkg(name):",
        "    if name not in _sys.modules:",
        "        m=_types.ModuleType(name);m.__path__=[];m.__package__=name;_sys.modules[name]=m",
        "def _load(name, source):",
        "    parent=name.rpartition('.')[0]",
        "    if parent:_pkg(parent)",
        "    m=_types.ModuleType(name);m.__file__='<v9-standalone>/'+name.replace('.','/')+'.py';m.__package__=parent;_sys.modules[name]=m",
        "    if parent:setattr(_sys.modules[parent],name.rpartition('.')[2],m)",
        "    exec(compile(source,m.__file__,'exec'),m.__dict__)",
    ]
    for name in MODULES:
        source = source_path(name).read_text(encoding="utf-8")
        lines.append(f"_load({name!r}, {source!r})")
    lines += [
        "agent=_sys.modules['main_v9'].agent",
        "del _load, _pkg",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    artifact = build()
    (OUT / "main.py").write_text(artifact, encoding="utf-8")
    (OUT / "final_agent.py").write_text(artifact, encoding="utf-8")


if __name__ == "__main__":
    main()
