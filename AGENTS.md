# Working in the MONAI repository

MONAI (Medical Open Network for AI) is a PyTorch library for deep learning in medical imaging: domain-specific transforms, losses, metrics, networks, dataset and I/O layers, and application pipelines. It is mature and convention-heavy, and most review friction comes from missing conventions rather than wrong logic.

`CONTRIBUTING.md` is the canonical policy. This file is the map — where things live, how to approach a change, and which paths are off limits.

## Layout

| Path | Contents |
|------|----------|
| `monai/` | The library: `transforms/`, `data/`, `networks/`, `losses/`, `metrics/`, `inferers/`, `handlers/`, `apps/` (application domains such as `apps/detection/`), `utils/` (shared helpers) |
| `tests/` | Unit tests mirroring the library layout (`tests/transforms/`, `tests/apps/detection/`). Shared helpers in `tests/test_utils.py`; minimal-CI exclusions in `tests/min_tests.py` |
| `docs/source/` | Sphinx documentation; public APIs are listed in the `.rst` files here |
| `.github/` | Contribution machinery: templates, `CODEOWNERS`, workflows |
| `runtests.sh` | Entry point for lint, type checks, and tests |

Transforms usually exist in parallel forms that must stay consistent: an array version in `.../array.py`, a dictionary version in `.../dictionary.py` (suffixed `d`), plus `D` and `Dict` aliases. Change one and check the others.

## Sources of truth

| File | Use it for |
|------|-----------|
| `CONTRIBUTING.md` | Coding style, license header, unit testing, docs, optional dependencies, DCO, backwards compatibility, `[skip ci]` policy |
| `.github/pull_request_template.md` | The PR body contract: `Fixes #`, Description, Types of changes |
| `.github/ISSUE_TEMPLATE/` | `bug_report.md` and `feature_request.md`; usage questions belong in Discussions |
| `.github/CODEOWNERS` | Path ownership, including subtrees with specialized owners |
| `.coderabbit.yaml` | Docstring, naming, and test expectations applied automatically at review |

## Approaching a change

- **Explore first.** Find the closest existing implementation and its tests, and follow that pattern. MONAI is highly patterned; the answer usually exists a few files away.
- **Minimal diff.** Scope it to the task. No drive-by refactors, no reformatting untouched code, no renaming unrelated symbols.
- **No invented dependencies.** Adding one requires human agreement and coordinated updates — see `CONTRIBUTING.md` → "Adding new optional dependencies". Optional imports stay lazy via `monai.utils.optional_import`; prefer existing `monai/utils/` helpers.
- **Hot zones.** Check `.github/CODEOWNERS` before editing and confirm with a human on specialized paths.
- **Bugs: reproduce before fixing, and check the premise.** Capture the actual values first. A report can be a convention mismatch rather than a defect — for example MONAI treats the first spatial array axis as `x`, which is the opposite of the computer-vision reading. If the code matches its own convention and only the documentation is silent, the fix is documentation.
- **Public API changes** need exports, Google-style docstrings, tests for the new branches, and a `docs/source/*.rst` entry. Details live in `.cursor/rules/`.

## Commands

```bash
python -m pip install -U -r requirements-dev.txt   # dev tooling

./runtests.sh --ruff                               # fast lint
./runtests.sh --autofix                            # apply style fixes
./runtests.sh --quick --unittests                  # quick unit sweep
python -m tests.apps.detection.test_box_transform  # one test module (dotted path, no .py)

git commit -s -m "message"                         # DCO sign-off is mandatory
```

Branches for a tracked issue are named `[ticket_id]-[task_name]` and are cut from `cursor-onboarding`, the integration branch in this repository. Pull requests open as drafts early and target `cursor-onboarding`; a change contributed upstream to `Project-MONAI/MONAI` targets `dev` instead.

## Policy

- **DCO.** Every commit needs `Signed-off-by` — `git commit -s`.
- **License header.** Required on every `.py` file under `monai/` and `tests/`; the license hook inserts it and owns the canonical text.
- **`[skip ci]`.** Documentation and repository metadata only — never `monai/`, `tests/`, or dependencies.
- **No binary test data.** Reference remote data through `tests/testing_data/data_config.json`.
- **American English** in names and documentation.
- **Backwards compatibility.** Opt-in defaults; migrate with the `monai.utils` deprecation helpers. See `CONTRIBUTING.md` → "Backwards compatibility".
- **Never claim tests passed without running them.** Paste the command and its result.

## Protected paths

Enforced by `.cursor/hooks/protect-platform-paths.py`, in three tiers.

**Blocked** — the files that define how the guardrails themselves behave: `AGENTS.md`, `.cursor/hooks.json`, `.cursor/hooks/**`, `.cursor/agents/**`, `.cursor/BUGBOT.md`, `.cursor/skills/implement-change/**`, `.cursor/skills/create-issue/**`, `.github/workflows/**`, `.github/CODEOWNERS`, `.github/dco.yml`, `.pre-commit-config.yaml`, `LICENSE`, `CODE_OF_CONDUCT.md`.

**Human approval** — `.cursor/rules/**`, `requirements*.txt`, `setup.py`, `setup.cfg`, `pyproject.toml`, `environment-dev.yml`, `tests/min_tests.py`, and deletions under `monai/`.

**Open** — `monai/`, `tests/`, `docs/`, and new skills of your own under `.cursor/skills/<name>/`.

If a task appears to need a blocked path, stop and ask rather than finding another route.

---

Structured workflows live in `.cursor/skills/`: `implement-change` for making a library change, `create-issue` for filing one. Validated against upstream `dev` @ `3ee058bd`.
