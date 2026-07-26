# AGENTS.md

## Cursor Cloud specific instructions

MONAI is a PyTorch-based Python **library** for medical-imaging deep learning. There is no server/app to run — "running it" means importing the package and exercising it via scripts and the test suite. See `README.md` and `CONTRIBUTING.md` for canonical commands.

### Environment
- Dependencies are installed into a virtualenv at `/workspace/.venv` (managed by the startup update script). Activate it before doing anything: `source /workspace/.venv/bin/activate`.
- Always work with the venv active. Several tests (e.g. `tests/utils/misc/test_monai_utils_misc.py::test_run_cmd`) shell out to a bare `python`, so it must be on `PATH` — running via `.venv/bin/python` without activating makes those tests fail with `FileNotFoundError: 'python'`.
- CPU-only environment (no GPU/CUDA). PyTorch is the CPU build. GPU-only and distributed (`*_dist.py`) tests are skipped or will fail; that is expected here.
- C++/CUDA extensions are not compiled (`BUILD_MONAI` unset), so `monai.config.print_config()` shows `HAS_EXT = False`. Set `BUILD_MONAI=1` before `pip install -e .` only if you specifically need the compiled `monai._C` ops.
- A few optional deps are intentionally not installed because they break install here: `MetricsReloaded` and `segment-anything` (git installs; `MetricsReloaded` build fails on modern setuptools lacking `pkg_resources`) and `nni` (Python 3.12). Tests needing these will skip/fail; install them manually only if required.

### Tests
- Run tests via the module runner or the harness, NOT raw `pytest tests/...`. The suite defines helper functions named `test_*` (e.g. `test_script_save`) that `pytest` mis-collects as tests, producing spurious collection errors. `python -m pytest` still "passes" the real cases but reports these as errors.
- Full run of a module: `python -m tests.networks.nets.test_unet` (dotted path, no `.py`).
- Fast minimal suite (core deps only, ~9600 tests): `QUICKTEST=true python -m tests.min_tests`.
- Broader unit tests: `./runtests.sh --unittests` (add `--quick` for a faster subset). Run `./runtests.sh -h` for all options.

### Lint / format / build
- Lint & type-check: `./runtests.sh --codeformat` (black + isort + ruff + mypy). Quick individual checks: `./runtests.sh --ruff`, `--black`, `--isort`. Auto-fix formatting: `./runtests.sh --autofix`.
- "Build" (editable/dev install): `pip install -e .` from the repo root.
