#!/bin/bash
# afterFileEdit: ensure the Apache header required by CONTRIBUTING.md is present on
# Python sources under monai/ and tests/. Missing headers are injected rather than
# reported, because the block is verbatim and there is nothing to decide.
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

# testing_data holds fixtures and generated files, not library sources
case "$rel" in
  tests/testing_data/*) quiet ;;
esac

[ -f "$file" ] || quiet
[ -s "$file" ] || quiet

if head -n 15 "$file" | grep -q "Copyright (c) MONAI Consortium"; then
  quiet
fi

tmp="${file}.license-hook.tmp"
cat > "$tmp" <<'HEADER'
# Copyright (c) MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

HEADER

if ! cat "$file" >> "$tmp"; then
  rm -f "$tmp"
  emit "License-header hook could not read ${rel}; add the Apache header from CONTRIBUTING.md manually."
fi

mv "$tmp" "$file" || { rm -f "$tmp"; emit "License-header hook could not write ${rel}; add the Apache header manually."; }

emit "Added the required Apache license header to ${rel} (CONTRIBUTING.md -> Licensing information). Keep it verbatim at the top of the file."
