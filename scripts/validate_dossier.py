#!/usr/bin/env python3
"""Validate implementation-grade product dossiers for required depth and links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from check_inventory import IMPLEMENTATION_FILES
from new_blueprint import BASE_CAPABILITIES, RECIPE_CAPABILITIES


MIN_NONBLANK = {
    "index.md": 25,
    "sources.md": 35,
    "product-contract.md": 45,
    "architecture.md": 45,
    "agent-loop.md": 55,
    "protocol-state.md": 55,
    "context-tools.md": 45,
    "workspace-execution.md": 45,
    "safety-runtime.md": 45,
    "persistence-recovery.md": 50,
    "experience.md": 45,
    "recipe.md": 45,
    "acceptance-tests.md": 55,
}

REQUIRED_TERMS = {
    "product-contract.md": ("行为", "非目标", "证据"),
    "agent-loop.md": ("状态", "终止", "取消", "重试"),
    "protocol-state.md": ("thread", "turn", "item", "event"),
    "workspace-execution.md": ("workspace", "执行", "失败"),
    "persistence-recovery.md": ("schema", "事务", "恢复", "迁移"),
    "acceptance-tests.md": ("runnable", "usable", "productive", "polished"),
    "sources.md": ("http", "证据", "版本"),
}


def acceptance_level(text: str, capability: str) -> str | None:
    """Extract a capability's canonical minimum level from a table or section."""
    escaped = re.escape(capability)
    table = re.search(
        rf"\|\s*`{escaped}`\s*\|\s*`?(runnable|usable|productive|polished)`?\s*\|",
        text,
        flags=re.IGNORECASE,
    )
    if table:
        return table.group(1).lower()
    section = re.search(
        rf"^###\s+`{escaped}`\s*$\s*^等级：`(runnable|usable|productive|polished)`。?\s*$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return section.group(1).lower() if section else None


def validate(directory: Path) -> list[str]:
    errors: list[str] = []
    names = {path.name for path in directory.glob("*.md")}
    missing = sorted(IMPLEMENTATION_FILES - names)
    extra = sorted(names - IMPLEMENTATION_FILES)
    if missing:
        errors.append(f"missing files: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected files: {', '.join(extra)}")

    for name in sorted(IMPLEMENTATION_FILES & names):
        path = directory / name
        text = path.read_text(encoding="utf-8")
        nonblank = sum(bool(line.strip()) for line in text.splitlines())
        if nonblank < MIN_NONBLANK[name]:
            errors.append(f"{name}: {nonblank} nonblank lines < {MIN_NONBLANK[name]}")
        lowered = text.lower()
        for term in REQUIRED_TERMS.get(name, ()):
            if term.lower() not in lowered:
                errors.append(f"{name}: missing required term {term!r}")
        if len(text.splitlines()) > 100 and "## 目录" not in text:
            errors.append(f"{name}: files over 100 lines require a '## 目录' section")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            candidate = (path.parent / target.split("#", 1)[0]).resolve()
            if not candidate.exists():
                errors.append(f"{name}: broken link {target}")

    overlays = RECIPE_CAPABILITIES.get(directory.name, {})
    if overlays and "acceptance-tests.md" in names:
        base_capabilities = {
            capability
            for capabilities in BASE_CAPABILITIES.values()
            for capability in capabilities
        }
        acceptance = (directory / "acceptance-tests.md").read_text(encoding="utf-8")
        recipe = (
            (directory / "recipe.md").read_text(encoding="utf-8")
            if "recipe.md" in names
            else ""
        )
        seen_product_capabilities: set[str] = set()
        for level, capabilities in overlays.items():
            for capability in capabilities:
                if capability in seen_product_capabilities:
                    errors.append(
                        f"product capability {capability!r} appears in multiple levels"
                    )
                seen_product_capabilities.add(capability)
                if capability in base_capabilities:
                    errors.append(
                        f"product capability {capability!r} collides with a shared capability"
                    )
                if f"`{capability}`" not in acceptance:
                    errors.append(
                        "acceptance-tests.md: missing product capability oracle "
                        f"{capability!r} ({level})"
                    )
                    continue
                documented_level = acceptance_level(acceptance + "\n" + recipe, capability)
                if documented_level is None:
                    errors.append(
                        "acceptance-tests.md: missing canonical capability level/oracle "
                        f"{capability!r} ({level})"
                    )
                elif documented_level != level:
                    errors.append(
                        "acceptance-tests.md: capability level mismatch for "
                        f"{capability!r}: blueprint={level}, documented={documented_level}"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", nargs="?", default="references/products",
        help="one product directory or the products root",
    )
    args = parser.parse_args()
    path = Path(args.path).resolve()
    directories = [path]
    if path.name == "products":
        directories = sorted(item for item in path.iterdir() if item.is_dir())

    failed = False
    for directory in directories:
        names = {item.name for item in directory.glob("*.md")}
        if names != IMPLEMENTATION_FILES:
            print(f"SKIP research-grade dossier: {directory.name}")
            continue
        errors = validate(directory)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR {directory.name}: {error}")
        else:
            print(f"OK {directory.name}: implementation-grade dossier")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
