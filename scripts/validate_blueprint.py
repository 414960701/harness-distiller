#!/usr/bin/env python3
"""Validate a Harness Distiller blueprint without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from new_blueprint import LEVELS, RECIPES, SURFACES, capability_manifest


STATUSES = {"selected", "implemented", "verified", "deferred", "blocked-by-evidence"}
REQUIRED_KEYS = {
    "schema_version", "recipe", "level", "surfaces", "stack", "execution",
    "security", "providers", "distribution", "capabilities", "non_goals",
    "product_acceptance_ref", "evidence", "decisions",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="blueprint.yaml or target repository root")
    args = parser.parse_args()
    path = Path(args.path).expanduser().resolve()
    target_root = path
    if path.is_dir():
        target_root = path
        path = path / ".harness-distill" / "blueprint.yaml"
    else:
        target_root = path.parent.parent if path.parent.name == ".harness-distill" else path.parent
    if not path.is_file():
        raise SystemExit(f"blueprint not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{path} must retain JSON syntax (valid YAML 1.2): {exc}"
        ) from exc

    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - data.keys())
    if missing:
        errors.append(f"missing keys: {', '.join(missing)}")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("recipe") not in RECIPES:
        errors.append(f"unknown recipe: {data.get('recipe')!r}")
    if data.get("level") not in LEVELS:
        errors.append(f"unknown level: {data.get('level')!r}")

    expected_product_acceptance = (
        Path(__file__).resolve().parents[1] / "references" / "products" /
        str(data.get("recipe")) / "acceptance-tests.md"
    )
    product_acceptance_ref = data.get("product_acceptance_ref")
    if expected_product_acceptance.is_file():
        canonical_ref = (
            f".harness-distill/contracts/references/products/"
            f"{data.get('recipe')}/acceptance-tests.md"
        )
        if product_acceptance_ref != canonical_ref:
            errors.append(f"product_acceptance_ref must equal {canonical_ref!r}")
    elif product_acceptance_ref is not None:
        errors.append("product_acceptance_ref must be null without a product dossier")
    if isinstance(product_acceptance_ref, str):
        product_acceptance_path = target_root / product_acceptance_ref
        if not product_acceptance_path.is_file() or not product_acceptance_path.stat().st_size:
            errors.append(
                f"product_acceptance_ref does not exist or is empty: "
                f"{product_acceptance_ref}"
            )

    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("surfaces must be a non-empty list")
    elif unknown := sorted(set(surfaces) - SURFACES):
        errors.append(f"unknown surfaces: {', '.join(unknown)}")

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capabilities must be a non-empty object")
    else:
        for capability, record in capabilities.items():
            if not isinstance(record, dict):
                errors.append(f"{capability}: record must be an object")
                continue
            if record.get("status") not in STATUSES:
                errors.append(f"{capability}: invalid status {record.get('status')!r}")
            if record.get("contract_version") not in {1, 2, 3, 4}:
                errors.append(f"{capability}: contract_version must be 1..4")
            introduced = record.get("introduced_at")
            target_level = record.get("target_level")
            if introduced not in LEVELS:
                errors.append(f"{capability}: invalid introduced_at {introduced!r}")
            if target_level != data.get("level"):
                errors.append(f"{capability}: target_level must equal blueprint level")
            if introduced in LEVELS and data.get("level") in LEVELS:
                if LEVELS.index(introduced) > LEVELS.index(data["level"]):
                    errors.append(f"{capability}: introduced after target level")
            if not record.get("acceptance_ref"):
                errors.append(f"{capability}: acceptance_ref is required")
            elif not isinstance(record.get("acceptance_ref"), str):
                errors.append(f"{capability}: acceptance_ref must be a string")
            elif "://" not in record["acceptance_ref"]:
                acceptance_path = target_root / record["acceptance_ref"]
                if not acceptance_path.is_file() or not acceptance_path.stat().st_size:
                    errors.append(
                        f"{capability}: acceptance_ref does not exist or is empty: "
                        f"{record['acceptance_ref']}"
                    )
            status = record.get("status")
            implementation = record.get("implementation", [])
            tests = record.get("tests", [])
            if not isinstance(implementation, list):
                errors.append(f"{capability}: implementation must be a list")
                implementation = []
            if not isinstance(tests, list):
                errors.append(f"{capability}: tests must be a list")
                tests = []
            if status in {"implemented", "verified"} and not implementation:
                errors.append(f"{capability}: {status} requires implementation paths")
            if status == "verified" and not tests:
                errors.append(f"{capability}: verified requires test paths")
            for relative in implementation + tests:
                if not isinstance(relative, str) or not relative:
                    errors.append(f"{capability}: implementation/test paths must be strings")
                elif not (target_root / relative).exists():
                    errors.append(f"{capability}: path does not exist: {relative}")

        recipe = data.get("recipe")
        level = data.get("level")
        if recipe in RECIPES and level in LEVELS:
            expected_manifest = capability_manifest(level, recipe)
            expected = set(expected_manifest)
            missing_capabilities = sorted(expected - set(capabilities))
            if missing_capabilities:
                errors.append(
                    "missing required capability closure: " + ", ".join(missing_capabilities)
                )
            for capability in sorted(expected & set(capabilities)):
                expected_ref = expected_manifest[capability]["acceptance_ref"]
                actual_ref = capabilities[capability].get("acceptance_ref")
                if actual_ref != expected_ref:
                    errors.append(
                        f"{capability}: acceptance_ref must equal {expected_ref!r}"
                    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {path} ({len(capabilities)} capabilities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
