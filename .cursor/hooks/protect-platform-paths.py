#!/usr/bin/env python3
"""preToolUse guard for paths the platform team owns.

Rules and review can be argued with; this cannot. The files that define the onboarding
layer's behavior, CI configuration, and licensing sit outside the blast radius of a
routine change, so writes to them are denied and the agent is told to ask a human.

The deny list is deliberately specific rather than all of `.cursor/`: contributors are
expected to add their own skills, and tuning a rule is a normal, reviewable act. Those
are gated with "ask" or allowed outright.

Reads the hook payload on stdin and writes a permission decision on stdout.
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import subprocess
import sys

# Behavior-defining platform files. Never writable by an agent.
DENY_EXACT = {
    "AGENTS.md",
    ".cursor/hooks.json",
    ".cursor/BUGBOT.md",
    ".github/CODEOWNERS",
    ".github/dco.yml",
    ".pre-commit-config.yaml",
    "LICENSE",
    "CODE_OF_CONDUCT.md",
}
DENY_PREFIXES = (
    ".cursor/hooks/",
    ".cursor/agents/",
    ".cursor/skills/implement-change/",
    ".cursor/skills/create-issue/",
    ".github/workflows/",
)

# Legitimate to change, but a human has to agree.
ASK_EXACT = {
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "environment-dev.yml",
    "tests/min_tests.py",
    "docs/requirements.txt",
}
ASK_PREFIXES = (".cursor/rules/",)
ASK_GLOBS = ("requirements*.txt",)

# Skills the platform owns; every other skill directory is contributor territory.
PLATFORM_SKILLS = {"implement-change", "create-issue"}

# Payload keys that may carry a path, whatever the tool.
PATH_KEYS = {
    "path",
    "file_path",
    "filePath",
    "target_file",
    "targetFile",
    "target_notebook",
    "targetNotebook",
    "file",
    "filename",
    "abs_path",
    "absolutePath",
    "paths",
    "files",
}

DELETE_TOOLS = {"delete", "deletefile", "remove"}


def emit(decision: dict) -> None:
    json.dump(decision, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def allow() -> None:
    emit({"permission": "allow"})


def workspace_root(payload: dict) -> str:
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots")
    if isinstance(roots, list) and roots and isinstance(roots[0], str):
        return roots[0]
    try:
        return subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except Exception:
        return os.getcwd()


def collect_paths(node: object, found: list[str]) -> None:
    """Walk the payload and pick up anything that looks like a target path."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in PATH_KEYS:
                if isinstance(value, str):
                    found.append(value)
                elif isinstance(value, list):
                    found.extend(item for item in value if isinstance(item, str))
            else:
                collect_paths(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_paths(item, found)


def to_relative(path: str, root: str) -> str:
    normalized = os.path.normpath(path)
    if os.path.isabs(normalized) and root:
        try:
            relative = os.path.relpath(normalized, root)
        except ValueError:
            return normalized.replace(os.sep, "/")
        # Outside the workspace entirely; not ours to police.
        if relative.startswith(".."):
            return normalized.replace(os.sep, "/")
        normalized = relative
    return normalized.replace(os.sep, "/").removeprefix("./")


def classify(rel: str, tool_name: str) -> str | None:
    if rel in DENY_EXACT or rel.startswith(DENY_PREFIXES):
        return "deny"

    if rel.startswith(".cursor/skills/"):
        parts = rel.split("/")
        # A contributor's own skill directory is theirs to create and edit.
        if len(parts) >= 3 and parts[2] not in PLATFORM_SKILLS:
            return None
        return "deny"

    if rel in ASK_EXACT or rel.startswith(ASK_PREFIXES):
        return "ask"
    if any(fnmatch.fnmatch(posixpath.basename(rel), pattern) for pattern in ASK_GLOBS):
        return "ask"

    # Anything else directly under .cursor/ is platform surface we have not classified;
    # let a human confirm rather than guessing.
    if rel.startswith(".cursor/") or rel == ".cursor":
        return "ask"

    if tool_name.lower().replace("_", "") in DELETE_TOOLS and rel.startswith("monai/"):
        return "ask"
    return None


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        # failClosed is set for this hook, so a malformed payload should not be a
        # silent pass; refuse the action and let the human look.
        emit(
            {
                "permission": "deny",
                "agent_message": "Governance hook received an unreadable payload and denied the write. Ask a human to check .cursor/hooks/protect-platform-paths.py.",
                "user_message": "Governance hook could not parse its input; the write was denied.",
            }
        )
        return

    if not isinstance(payload, dict):
        allow()

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    root = workspace_root(payload)

    raw_paths: list[str] = []
    collect_paths(payload, raw_paths)
    # Matcher covers write/edit/delete tools only. If no path key matched, refuse
    # rather than failing open on an unrecognized payload shape.
    resolved = [raw for raw in raw_paths if raw]
    if not resolved:
        emit(
            {
                "permission": "deny",
                "agent_message": (
                    "Blocked: governance hook could not find a target path in the write tool "
                    "payload (unknown or missing path keys). Refusing the write (fail-closed). "
                    "Ask a human if the tool payload shape needs to be recognized in "
                    ".cursor/hooks/protect-platform-paths.py."
                ),
                "user_message": (
                    "Governance hook denied a write because no target path was found in the payload."
                ),
            }
        )

    asked: list[str] = []
    for raw in resolved:
        rel = to_relative(raw, root)
        verdict = classify(rel, tool_name)
        if verdict == "deny":
            emit(
                {
                    "permission": "deny",
                    "agent_message": (
                        f"Blocked: `{rel}` defines how this repository's guardrails behave "
                        "(see AGENTS.md -> Protected paths). Do not work around this by editing a "
                        "different file or using the shell. Stop and tell the human which path the "
                        "task appears to need and why."
                    ),
                    "user_message": f"Governance hook denied a write to the protected path {rel}.",
                }
            )
        elif verdict == "ask":
            asked.append(rel)

    if asked:
        targets = ", ".join(sorted(set(asked)))
        emit(
            {
                "permission": "ask",
                "agent_message": (
                    f"`{targets}` needs human approval before changing. Say what the change is and "
                    "why the task requires it. Dependency changes also require the coordinated "
                    "updates described in CONTRIBUTING.md -> Adding new optional dependencies."
                ),
                "user_message": f"An agent wants to modify {targets}. Approve only if that is intended.",
            }
        )

    allow()


if __name__ == "__main__":
    main()
