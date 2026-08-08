#!/usr/bin/env python3
"""Validate shared knowledge modules for implementation-ready structure."""

from __future__ import annotations

from pathlib import Path


EXPECTED = 35
REQUIRED_CONCEPTS = ("职责", "四级", "升级", "失败", "验收")


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "references" / "knowledge"
    modules = sorted(path for path in root.glob("*.md") if path.name != "index.md")
    errors: list[str] = []
    if len(modules) != EXPECTED:
        errors.append(f"expected {EXPECTED} modules, found {len(modules)}")
    for path in modules:
        text = path.read_text(encoding="utf-8")
        nonblank = sum(bool(line.strip()) for line in text.splitlines())
        if nonblank < 35:
            errors.append(f"{path.name}: {nonblank} nonblank lines < 35")
        for concept in REQUIRED_CONCEPTS:
            if concept not in text:
                errors.append(f"{path.name}: missing concept {concept!r}")
        if len(text.splitlines()) > 100 and "## 目录" not in text:
            errors.append(f"{path.name}: files over 100 lines require a '## 目录' section")
    if errors:
        for error in errors:
            print("ERROR: " + error)
        return 1
    print(f"OK: {len(modules)} implementation-ready knowledge modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

