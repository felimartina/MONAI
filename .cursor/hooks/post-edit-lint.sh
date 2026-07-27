#!/bin/bash
# afterFileEdit: scoped ruff check on the single edited Python file.
# Deliberately narrow -- MONAI's full check (./runtests.sh -f -u --net --coverage) is a
# CI-scale job and must never run on an edit. Reports only; it does not rewrite code.
set -uo pipefail

emit() { jq -n --arg m "$1" '{agent_message: $m}'; exit 0; }
quiet() { echo '{}'; exit 0; }

command -v jq >/dev/null 2>&1 || { echo '{}'; exit 0; }

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.file_path // .filePath // .path // empty')
[ -n "$file" ] || quiet

case "$file" in
  *.py) ;;
  *) quiet ;;
esac

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
rel=${file#"$root"/}
rel=${rel#./}

case "$rel" in
  monai/*|tests/*) ;;
  *) quiet ;;
esac

case "$rel" in
  versioneer.py|monai/_version.py) quiet ;;
esac

[ -f "$file" ] || quiet

if [ -x "$root/.venv/bin/ruff" ]; then
  ruff_cmd=("$root/.venv/bin/ruff")
elif command -v ruff >/dev/null 2>&1; then
  ruff_cmd=(ruff)
elif python3 -m ruff --version >/dev/null 2>&1; then
  ruff_cmd=(python3 -m ruff)
else
  emit "ruff is not installed, so ${rel} was not linted. Create the project environment and install the dev tools ('python -m pip install -U -r requirements-dev.txt'), then verify with './runtests.sh --ruff' before opening the PR."
fi

cd "$root" || quiet

# --no-cache keeps the hook from leaving an untracked .ruff_cache/ behind on every edit.
output=$(NO_COLOR=1 "${ruff_cmd[@]}" check --force-exclude --no-cache --output-format concise "$rel" 2>&1)
status=$?

if [ "$status" -eq 0 ]; then
  quiet
fi

# Strip ANSI styling; older ruff versions colorize even when NO_COLOR is set.
trimmed=$(printf '%s' "$output" | sed $'s/\033\\[[0-9;]*m//g' | head -n 25)

emit "ruff reported issues in ${rel}. Fix these before continuing:

${trimmed}

Repo-wide check: ./runtests.sh --ruff"
