#!/usr/bin/env python3
"""beforeShellExecution: block gh PRs aimed at public upstream MONAI.

Agents must open draft PRs on the fork only. Closing a wrong-repo PR does not
delete it, so this gate fails closed on upstream targets and on ambiguous
creates that omit --repo when origin is a fork and upstream exists.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from urllib.parse import urlparse

UPSTREAM_REPO = "project-monai/monai"

# gh global / pr flags that take a following value (non-exhaustive; used to skip).
VALUE_FLAGS = {
    "-R",
    "--repo",
    "-b",
    "--base",
    "-H",
    "--head",
    "-t",
    "--title",
    "-F",
    "--body-file",
    "--body",
    "-a",
    "--assignee",
    "-r",
    "--reviewer",
    "-l",
    "--label",
    "-m",
    "--milestone",
    "--project",
    "--template",
    "-c",
    "--cwd",
    "--hostname",
}


def emit(decision: dict) -> None:
    json.dump(decision, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def allow() -> None:
    emit({"permission": "allow"})


def deny(agent_message: str, user_message: str) -> None:
    emit(
        {
            "permission": "deny",
            "agent_message": agent_message,
            "user_message": user_message,
        }
    )


def workspace_cwd(payload: dict) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return cwd
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots")
    if isinstance(roots, list) and roots and isinstance(roots[0], str):
        return roots[0]
    return os.getcwd()


def run_git(args: list[str], cwd: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return (out.stdout or "").strip()


def normalize_repo(value: str) -> str | None:
    """Return owner/repo in lowercase, or None if unparseable."""
    raw = value.strip()
    if not raw:
        return None
    if "://" in raw or raw.startswith("git@"):
        if raw.startswith("git@"):
            path = raw.split(":", 1)[-1]
        else:
            path = urlparse(raw).path.lstrip("/")
        raw = path
    raw = raw.removesuffix(".git").strip("/")
    parts = [p for p in raw.split("/") if p]
    if len(parts) < 2:
        return None
    return f"{parts[-2]}/{parts[-1]}".lower()


def remote_repo(cwd: str, name: str) -> str | None:
    url = run_git(["remote", "get-url", name], cwd)
    if not url:
        return None
    return normalize_repo(url)


def extract_gh_segments(command: str) -> list[list[str]] | None:
    """Pull out argv lists for bare `gh ...` invocations inside a shell line.

    Returns None when the line cannot be tokenized (fail closed in main).
    Returns an empty list when the line parses but contains no `gh` command —
    e.g. a commit message or grep pattern that only mentions the words.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None

    segments: list[list[str]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        base = os.path.basename(tok)
        if base == "gh":
            j = i + 1
            while j < len(tokens) and tokens[j] not in {
                "&&",
                "||",
                ";",
                "|",
                "&",
            }:
                j += 1
            segments.append(tokens[i:j])
            i = j
        else:
            i += 1
    return segments


def looks_like_gh_pr_create(command: str) -> bool:
    lowered = command.lower()
    if re.search(r"\bgh\b", lowered) is None:
        return False
    if re.search(r"\bpr\b", lowered) and re.search(r"\bcreate\b", lowered):
        return True
    return False


def flag_value(argv: list[str], long_name: str, short_name: str | None = None) -> str | None:
    """Return the value of --repo / -R style flags."""
    for i, tok in enumerate(argv):
        if tok == long_name or (short_name and tok == short_name):
            if i + 1 < len(argv):
                return argv[i + 1]
            return ""
        prefix = long_name + "="
        if tok.startswith(prefix):
            return tok[len(prefix) :]
        if short_name and tok.startswith(short_name + "="):
            return tok.split("=", 1)[1]
    return None


def positional_subcommands(argv: list[str]) -> list[str]:
    """Return non-flag tokens after `gh`, skipping known flag values."""
    out: list[str] = []
    i = 1  # skip gh
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            out.extend(argv[i + 1 :])
            break
        if tok.startswith("-"):
            if "=" in tok:
                i += 1
                continue
            # Boolean-ish short clusters (-fd) have no separate value.
            if tok in VALUE_FLAGS:
                i += 2
                continue
            # Unknown long option with value: --foo bar
            if tok.startswith("--"):
                # Heuristic: if next token exists and does not look like a flag, skip it.
                if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                    i += 2
                else:
                    i += 1
                continue
            # Short flag without bundled value policy: skip one arg if next is not a flag
            # and this short opt is commonly valued; otherwise skip flag only.
            if len(tok) == 2 and i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                # Ambiguous; only skip value for known VALUE_FLAGS (handled above).
                i += 1
                continue
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def is_pr_create_argv(argv: list[str]) -> bool:
    pos = positional_subcommands(argv)
    return len(pos) >= 2 and pos[0] == "pr" and pos[1] == "create"


def repo_from_argv(argv: list[str]) -> str | None:
    raw = flag_value(argv, "--repo", "-R")
    if raw is None:
        return None
    return normalize_repo(raw)


def decide_for_segment(argv: list[str], cwd: str) -> dict | None:
    """Return a deny decision dict, or None to continue/allow this segment."""
    if not is_pr_create_argv(argv):
        return None

    repo_flag = repo_from_argv(argv)
    origin = remote_repo(cwd, "origin")
    upstream = remote_repo(cwd, "upstream")

    if repo_flag == UPSTREAM_REPO:
        return {
            "permission": "deny",
            "agent_message": (
                "Blocked: `gh pr create` targets Project-MONAI/MONAI. "
                "Default policy is fork-only PRs. Resolve the fork with "
                '`FORK=$(gh repo view --json nameWithOwner -q .nameWithOwner)` '
                'and run `gh pr create --draft --repo "$FORK" --base <base> --head <branch>`. '
                "If the human explicitly asked for an upstream PR in this chat, they must "
                "run that command themselves (or temporarily disable this hook) — agents must not."
            ),
            "user_message": (
                "Denied gh pr create against Project-MONAI/MONAI (fork-only PR policy)."
            ),
        }

    if repo_flag is None:
        if origin and upstream and origin != UPSTREAM_REPO and upstream == UPSTREAM_REPO:
            return {
                "permission": "deny",
                "agent_message": (
                    "Blocked: `gh pr create` omitted `--repo` in a fork-with-upstream clone. "
                    "Pass `--repo <fork>` explicitly (e.g. `--repo felimartina/MONAI`). "
                    "Do not open a PR on Project-MONAI/MONAI."
                ),
                "user_message": (
                    "Denied gh pr create without --repo while origin is a fork and upstream exists."
                ),
            }
        if origin == UPSTREAM_REPO:
            return {
                "permission": "deny",
                "agent_message": (
                    "Blocked: origin appears to be Project-MONAI/MONAI and `gh pr create` "
                    "has no `--repo` flag. Open PRs on the fork only unless a human takes over."
                ),
                "user_message": "Denied gh pr create: origin is upstream MONAI and --repo is missing.",
            }
        if origin is None or upstream is None:
            return {
                "permission": "deny",
                "agent_message": (
                    "Blocked: could not confirm remotes for `gh pr create` without `--repo`. "
                    "Pass `--repo <fork>` (never Project-MONAI/MONAI unless a human opts in)."
                ),
                "user_message": "Denied ambiguous gh pr create (missing --repo; remotes unclear).",
            }

    return None


def command_mentions_upstream_repo(command: str) -> bool:
    return bool(
        re.search(r"project-monai/monai", command, flags=re.IGNORECASE)
        or re.search(r"github\.com[:/]project-monai/monai", command, flags=re.IGNORECASE)
    )


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        deny(
            "Fork-only PR hook received an unreadable payload and denied the shell command.",
            "deny-upstream-pr hook could not parse its input; command denied (fail-closed).",
        )
        return

    if not isinstance(payload, dict):
        allow()

    command = payload.get("command") or payload.get("command_line") or ""
    if not isinstance(command, str) or not command.strip():
        allow()

    cwd = workspace_cwd(payload)

    if not looks_like_gh_pr_create(command):
        allow()

    segments = extract_gh_segments(command)
    if segments is None:
        # shlex could not tokenize — fail closed when the line still looks like a create.
        if command_mentions_upstream_repo(command):
            deny(
                "Blocked: shell line looks like `gh pr create` targeting Project-MONAI/MONAI.",
                "Denied upstream-targeted gh pr create (unparseable shell line).",
            )
        deny(
            "Blocked: shell line looks like `gh pr create` but could not be parsed safely. "
            "Re-run with a simple command and explicit `--repo <fork>`.",
            "Denied unparseable gh pr create (fail-closed).",
        )
    if not segments:
        # Parsed cleanly but no bare `gh` invocation — mention-only (commit/grep/echo).
        allow()

    for seg in segments:
        decision = decide_for_segment(seg, cwd)
        if decision is not None:
            emit(decision)

    allow()


if __name__ == "__main__":
    main()
