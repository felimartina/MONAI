# Bugbot review guide — MONAI

Canonical policy: `CONTRIBUTING.md`. License headers, formatting, and lint are already enforced deterministically by hooks, pre-commit, and CI — do not spend review on them. Focus on the residual risk a machine cannot check. Be specific and actionable, and prefer a few high-value findings over exhaustive nitpicking.

## Flag

**Missing or weak tests.** Behavior changed under `monai/` with no matching test change. Happy-path-only coverage when the change added validation, dtype handling, or new error branches. Tests written to match the implementation rather than the requirement. For a bugfix, no test that would actually have failed beforehand.

**Silent breaks.** Defaults, signatures, or return shapes changed in place; no `deprecated` / `deprecated_arg` / `deprecated_arg_default` migration where one is warranted; only one of the old and new paths tested; a real break checked as "Non-breaking change" in the PR template.

**Unexported or contradicted API.** New public symbols missing from `__all__` or the package `__init__.py`; inconsistent `d` / `D` / `Dict` aliases; docstrings that now contradict the code, especially shape and axis-order claims.

**AI slop.** Unrelated refactors mixed into the diff; reimplementation of helpers that already exist in `monai/utils/`; narration comments restating the code; verification claimed in the PR body with no command output.

**Unjustified dependency or platform surface.** New entries in `requirements*.txt`, `setup.cfg`, `pyproject.toml`, or `tests/min_tests.py` with no reason given in the description. Any edit to `AGENTS.md`, `.cursor/hooks/**`, `.cursor/agents/**`, `.cursor/BUGBOT.md`, the `implement-change` or `create-issue` skills, `.github/workflows/**`, or `CODEOWNERS`.

**Process.** Missing DCO sign-off; `[skip ci]` on a commit touching `monai/` or `tests/`; binary test data committed instead of referenced.

## Do not

- Restate what the diff does.
- Re-enforce formatting, import order, or license headers.
- Demand tests for documentation-only changes.
