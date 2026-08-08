#!/usr/bin/env python3
"""Create a deterministic Harness Distiller blueprint.

The file uses JSON syntax because JSON is valid YAML 1.2 and can be parsed with
the Python standard library. This keeps the installed skill dependency-free.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path


RECIPES = {
    "codex", "claude-code", "qoderwork", "cursor", "windsurf",
    "copilot-agent", "jules", "junie", "aider", "opencode", "cline",
    "roo-code", "openhands", "agentscope", "langgraph", "deep-agents",
    "autogen", "crewai", "openai-agents-sdk", "llamaindex-workflows",
    "letta", "hybrid", "custom",
}
NON_PRODUCT_RECIPES = {"hybrid", "custom"}
LEVELS = ("runnable", "usable", "productive", "polished")
SURFACES = {"headless", "cli", "tui", "ide", "desktop", "web", "sdk"}

RECIPE_DEFAULTS = {
    "codex": {"stack": "rust", "surfaces": ["headless", "tui"]},
    "claude-code": {"stack": "typescript", "surfaces": ["headless", "cli"]},
    "qoderwork": {
        "stack": "typescript+tauri-rust-executor",
        "surfaces": ["headless", "desktop"],
    },
    "aider": {"stack": "python", "surfaces": ["headless", "cli"]},
    "agentscope": {"stack": "python", "surfaces": ["headless", "sdk"]},
    "deep-agents": {"stack": "python", "surfaces": ["headless", "sdk"]},
    "openhands": {
        "stack": "python+typescript-react",
        "surfaces": ["headless", "web", "sdk"],
    },
    "opencode": {
        "stack": "typescript-bun",
        "surfaces": ["headless", "tui"],
    },
    "langgraph": {"stack": "python", "surfaces": ["headless", "sdk"]},
}

BASE_CAPABILITIES = {
    "runnable": [
        "runtime.agent-loop", "model.adapter", "protocol.events",
        "context.basic", "tools.runtime", "workspace.boundary",
        "tools.cancellation",
        "filesystem.read", "patch.apply", "shell.foreground",
        "policy.basic-approval", "testing.smoke",
    ],
    "usable": [
        "state.persistence", "context.compaction", "planning.steps",
        "tools.mcp", "diff.review",
        "reliability.retry", "testing.contracts", "testing.scenarios",
    ],
    "productive": [
        "rag.incremental-index", "context.stable-prefix", "git.worktree",
        "subagents.parallel", "hooks.lifecycle", "policy.profiles",
        "state.checkpoints", "observability.traces", "evals.regression",
    ],
    "polished": [
        "sandbox.enforced", "network.policy", "policy.auto-review",
        "plugins.lifecycle", "execution.remote", "protocol.negotiation",
        "deployment.migrations", "deployment.signed-update",
        "quality.accessibility-i18n", "reliability.slo",
    ],
}

RECIPE_CAPABILITIES = {
    "qoderwork": {
        "runnable": [
            "task.isolation", "artifacts.lifecycle", "workspace.folder-grants",
            "surface.task-workbench",
        ],
        "usable": [
            "task.parallel", "surface.task-monitor", "browser.structured",
            "artifacts.semantic-validation",
        ],
        "productive": [
            "computer.use", "memory.awareness", "scheduled.tasks",
            "artifacts.versioning",
        ],
        "polished": [
            "connectors.enterprise-governance", "artifacts.provenance-audit",
        ],
    },
    "aider": {
        "runnable": [
            "context.explicit-files", "editing.structured-format",
            "git.atomic-checkpoint",
        ],
        "usable": [
            "context.repo-map", "context.history-summary",
            "validation.lint-test",
        ],
        "productive": [
            "modes.architect-editor", "models.role-routing",
            "git.undo-dirty-provenance",
        ],
        "polished": [
            "security.sandbox-enhancement", "protocol.headless-jsonl",
        ],
    },
    "agentscope": {
        "runnable": [
            "agent.react", "model.wrapper", "tools.toolkit",
            "context.manager",
        ],
        "usable": [
            "permission.rules", "planning.notebook", "mcp.gateway",
        ],
        "productive": [
            "middleware.chain", "workspace.resources", "rag.pipeline",
            "memory.long-term", "teams.messaging", "service.deployment",
        ],
        "polished": [
            "channels.production", "runtime.distributed-state",
        ],
    },
    "deep-agents": {
        "runnable": [
            "middleware.harness-stack", "planning.todo",
            "filesystem.backend",
        ],
        "usable": [
            "subagents.isolated", "permissions.hitl", "skills.loading",
            "memory.cross-session",
        ],
        "productive": [
            "rag.pipeline", "fault-tolerance.replay", "frontend.streaming",
        ],
        "polished": [
            "backend.sandbox", "backend.remote", "service.production",
            "profiles.managed-permissions",
        ],
    },
    "openhands": {
        "runnable": [
            "conversation.event-tree", "tools.action-observation",
            "agent.parallel-actions", "workspace.adapter",
        ],
        "usable": [
            "context.condenser", "security.confirmation",
            "server.remote-conversation", "surface.agent-canvas",
        ],
        "productive": [
            "runtime.container", "browser.interaction",
            "extensions.skills-plugins", "subagents.child-conversation",
        ],
        "polished": [
            "runtime.remote-lease", "security.defense-in-depth",
            "deployment.multi-tenant",
        ],
    },
    "opencode": {
        "runnable": [
            "architecture.local-server-client",
            "surface.minimal-tui",
            "protocol.session-message-parts",
            "providers.normalized-stream", "tools.workspace-loop",
        ],
        "usable": [
            "permissions.pattern-rules", "persistence.sqlite-resume",
            "extensions.mcp-runtime", "context.session-compaction",
        ],
        "productive": [
            "protocol.openapi-sse-sdk", "workspace.pty-lsp",
            "surfaces.tui-web-desktop", "sessions.parent-worktree",
        ],
        "polished": [
            "protocol.durable-event-replay", "security.sandboxed-server",
            "sharing.policy-controlled-sync",
        ],
    },
    "langgraph": {
        "runnable": [
            "graph.state-reducers", "runtime.pregel-supersteps",
            "control.command-send", "streaming.modes",
        ],
        "usable": [
            "persistence.checkpoints", "interrupts.durable-resume",
            "subgraphs.composition", "store.cross-thread-memory",
        ],
        "productive": [
            "durability.configurable", "recovery.pending-writes",
            "time-travel.branching", "observability.task-streams",
        ],
        "polished": [
            "checkpoint.production-store",
            "frontend.snapshot-event-projection",
            "deployment.operational-boundary",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Target repository root")
    parser.add_argument("--recipe", required=True, choices=sorted(RECIPES))
    parser.add_argument("--level", required=True, choices=LEVELS)
    parser.add_argument("--surfaces", help="Comma-separated; defaults by recipe")
    parser.add_argument("--stack", help="Defaults by recipe or infer-from-repository")
    parser.add_argument("--providers", help="Comma-separated provider ids")
    parser.add_argument("--distribution", default="source")
    parser.add_argument("--execution", default="local")
    parser.add_argument("--security", default="personal")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def capability_manifest(level: str, recipe: str = "custom") -> dict[str, dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    target_index = LEVELS.index(level)
    for index, level_name in enumerate(LEVELS):
        if index > target_index:
            break
        for capability in BASE_CAPABILITIES[level_name]:
            selected[capability] = {
                "introduced_at": level_name,
                "target_level": level,
                "status": "selected",
                "contract_version": 1,
                "acceptance_ref": ".harness-distill/contracts/references/capabilities.md",
                "implementation": [],
                "tests": [],
            }
        for capability in RECIPE_CAPABILITIES.get(recipe, {}).get(level_name, []):
            selected[capability] = {
                "introduced_at": level_name,
                "target_level": level,
                "status": "selected",
                "contract_version": 1,
                "acceptance_ref": (
                    f".harness-distill/contracts/references/products/{recipe}/"
                    "acceptance-tests.md"
                ),
                "implementation": [],
                "tests": [],
            }
    return selected


def main() -> int:
    args = parse_args()
    defaults = RECIPE_DEFAULTS.get(
        args.recipe, {"stack": "infer-from-repository", "surfaces": ["headless", "cli"]}
    )
    surfaces = defaults["surfaces"]
    if args.surfaces:
        surfaces = [item.strip() for item in args.surfaces.split(",") if item.strip()]
    unknown = sorted(set(surfaces) - SURFACES)
    if unknown:
        raise SystemExit(f"unknown surfaces: {', '.join(unknown)}")
    if not surfaces:
        raise SystemExit("at least one surface is required")

    skill_root = Path(__file__).resolve().parents[1]
    product_source = skill_root / "references" / "products" / args.recipe
    if (
        args.recipe not in NON_PRODUCT_RECIPES
        and not (product_source / "acceptance-tests.md").is_file()
    ):
        raise SystemExit(
            f"recipe {args.recipe!r} is planned but not implementation-grade; "
            "complete its 13-file dossier or use hybrid/custom"
        )

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        raise SystemExit(f"target is not a directory: {target}")
    distill_dir = target / ".harness-distill"
    blueprint_path = distill_dir / "blueprint.yaml"
    if blueprint_path.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite {blueprint_path}; pass --force")

    distill_dir.mkdir(parents=True, exist_ok=True)
    contracts_dir = distill_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    reference_source = skill_root / "references"
    bundled_references = contracts_dir / "references"
    bundled_references.mkdir(parents=True, exist_ok=True)
    for shared_reference in reference_source.glob("*.md"):
        shutil.copyfile(
            shared_reference,
            bundled_references / shared_reference.name,
        )
    for shared_directory in ("knowledge", "implementation", "workflows"):
        shutil.copytree(
            reference_source / shared_directory,
            bundled_references / shared_directory,
            dirs_exist_ok=True,
        )
    product_acceptance_ref = None
    if (product_source / "acceptance-tests.md").is_file():
        shutil.copytree(
            product_source,
            bundled_references / "products" / args.recipe,
            dirs_exist_ok=True,
        )
        product_acceptance_ref = (
            f".harness-distill/contracts/references/products/{args.recipe}/"
            "acceptance-tests.md"
        )
    blueprint = {
        "schema_version": 1,
        "generated_on": date.today().isoformat(),
        "recipe": args.recipe,
        "level": args.level,
        "surfaces": surfaces,
        "stack": args.stack or defaults["stack"],
        "execution": args.execution,
        "security": args.security,
        "providers": (
            [item.strip() for item in args.providers.split(",") if item.strip()]
            if args.providers
            else ["provider-neutral-contract", "scripted-fixture"]
        ),
        "distribution": [args.distribution],
        "product_acceptance_ref": product_acceptance_ref,
        "capabilities": capability_manifest(args.level, args.recipe),
        "non_goals": [],
        "evidence": {"status": "required", "path": ".harness-distill/evidence.md"},
        "decisions": {"path": ".harness-distill/decisions.md"},
    }
    blueprint_path.write_text(
        json.dumps(blueprint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    evidence_path = distill_dir / "evidence.md"
    if not evidence_path.exists():
        evidence_path.write_text(
            "# Evidence\n\n"
            "Record claim, kind, URL, retrieval date, version/commit, and confidence.\n",
            encoding="utf-8",
        )
    decisions_path = distill_dir / "decisions.md"
    if not decisions_path.exists():
        decisions_path.write_text(
            "# Decisions\n\n"
            "Record product deltas, accepted tradeoffs, assumptions, and non-goals.\n",
            encoding="utf-8",
        )

    print(blueprint_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
