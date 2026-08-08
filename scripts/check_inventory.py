#!/usr/bin/env python3
"""Check the research inventory and report completed product dossiers."""

from __future__ import annotations

import argparse
from pathlib import Path


RESEARCH_FILES = {
    "index.md", "architecture.md", "context-tools.md", "safety-runtime.md",
    "experience.md", "recipe.md",
}
IMPLEMENTATION_FILES = RESEARCH_FILES | {
    "sources.md", "product-contract.md", "agent-loop.md", "protocol-state.md",
    "workspace-execution.md", "persistence-recovery.md", "acceptance-tests.md",
}
EXPECTED_KNOWLEDGE = 35
EXPECTED_PRODUCTS = 21


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true",
        help="fail until all 21 planned implementation-grade dossiers exist",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    knowledge = sorted((root / "references" / "knowledge").glob("*.md"))
    module_count = len([path for path in knowledge if path.name != "index.md"])
    product_root = root / "references" / "products"
    complete: list[str] = []
    research_only: list[str] = []
    incomplete: list[str] = []
    for directory in sorted(path for path in product_root.glob("*") if path.is_dir()):
        names = {path.name for path in directory.glob("*.md")}
        if names == IMPLEMENTATION_FILES:
            complete.append(directory.name)
        elif names == RESEARCH_FILES:
            research_only.append(directory.name)
        else:
            incomplete.append(f"{directory.name}: {sorted(IMPLEMENTATION_FILES - names)}")

    print(f"knowledge: {module_count}/{EXPECTED_KNOWLEDGE}")
    print(f"implementation-grade product dossiers: {len(complete)}/{EXPECTED_PRODUCTS}")
    if complete:
        print("complete: " + ", ".join(complete))
    if research_only:
        print("research-grade only: " + ", ".join(research_only))
    for item in incomplete:
        print("incomplete: " + item)
    product_plan_complete = len(complete) == EXPECTED_PRODUCTS
    if args.strict and not product_plan_complete:
        print("strict inventory is not complete")
    valid = module_count == EXPECTED_KNOWLEDGE and not incomplete
    if args.strict:
        valid = valid and product_plan_complete
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
