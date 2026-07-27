# AGENTS.md

## Cursor Cloud specific instructions

MONAI is a PyTorch-based Python library (plus the `monai.bundle` CLI) for medical
imaging deep learning. There is no web/GUI service — development means running the
library, the CLI, lint, and the unit tests. See `CONTRIBUTING.md` for the full
contributor workflow; the notes below only cover non-obvious, environment-specific gotchas.

### Environment facts
- CPU-only VM (no GPU/CUDA). `torch.cuda.is_available()` is `False`, so GPU/`*_dist`
  tests are skipped automatically. Don't treat GPU-dependent skips as failures.
- Python is 3.12. The update script installs into the user site (`~/.local`), so
  console scripts (`ruff`, `black`, `coverage`, ...) live in `~/.local/bin`, which is
  already on `PATH` via the default `~/.profile`.
- `python3` is the interpreter. A `python` -> `python3` symlink is installed at
  `/usr/local/bin/python` because `runtests.sh` defaults to `$(which python)` and one
  test (`test_run_cmd`) shells out to `python`. If `python` is ever missing, recreate it
  with `sudo ln -sf /usr/bin/python3 /usr/local/bin/python`, or pass `MONAI_PY_EXE=python3`
  to `runtests.sh`.

### What the update script installs
`requirements-min.txt` (torch, numpy, coverage, parameterized, ...), an editable
`pip install -e .` of MONAI, the pinned lint/type tools (ruff, black, isort, mypy), and
`fire` (needed by the `monai.bundle` CLI). This is enough for: lint, the minimal unit
test suite, importing/using the library, and the CLI.

### Lint / test / run commands
- Lint (fast): `./runtests.sh --ruff`; style: `./runtests.sh --black --isort`;
  everything: `./runtests.sh --codeformat` (also runs mypy/pytype).
- Minimal unit tests (only need `requirements-min.txt`): `QUICKTEST=true python -m tests.min_tests`.
- Single test module, e.g.: `python -m tests.losses.test_dice_loss`.
- Sanity check: `python -c "import monai; monai.config.print_config()"` and
  `python -m monai.bundle` (lists CLI commands).

### Optional / heavier dependencies
Many tests and features (nibabel, itk, scikit-image, scipy, transformers, etc.) are
optional and are NOT installed by the update script. Install them best-effort with
`pip install -r requirements-dev.txt`, but note that on this CPU/py3.12 VM some entries
are known to fail or be slow (e.g. GPU-only `cucim`, `nni==2.10.1`, TensorRT/polygraphy,
and the `git+` packages `MetricsReloaded`/`segment-anything`). Prefer installing just the
specific optional package a task needs.

### Build note
The editable install is pure-Python (`HAS_EXT = False`). To compile the optional C++/CUDA
extension set `BUILD_MONAI=1` before `pip install -e .` — not needed for normal dev.
