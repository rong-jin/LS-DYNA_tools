# LS-DYNA Python Tools (Personal Toolbox)

This repository is a **practical, script-first** collection of Python utilities that support an LS-DYNA workflow:

- **Run**: invoke LS-DYNA (direct solver call, optional restart dump)
- **Preprocess**: generate simple **FEM** and **SPH** geometries/meshes as LS-DYNA keywords
- **Postprocess**: (reserved) parsers/metrics for `nodout`, `glstat`, etc.

The repo is organized so you can:
1) run your existing scripts as-is under `scripts/`, and  
2) gradually migrate stable functionality into an importable package under `src/lsdyna_py/`.

---

## Repository layout

- `scripts/`
  - runnable scripts (your current assets; minimal refactor)
- `src/lsdyna_py/`
  - reusable library code (importable; use `pip install -e .`)
- `configs/`
  - example configuration files (paths, ncpu, memory, IDs)
- `examples/`
  - small minimal examples (no large LS-DYNA outputs)
- `outputs/`
  - generated results (gitignored)

---

## Quick start

### 1) Create a Python environment
```bash
pip install -r requirements.txt
```

### 2) Run your existing scripts (no refactor required)
```bash
python scripts/preprocess/sph_box_generate.py
python scripts/preprocess/sph_sphere_generate.py
python scripts/preprocess/sph_geo_generate.py
python scripts/preprocess/fem_box_mesh.py
python scripts/preprocess/fem_sphere_generate.py
```

### 3) Run LS-DYNA (direct solver call)
Option A: run the script you already have:
```bash
python scripts/run/run_lsdyna_direct.py
```

Option B: use the package CLI (recommended for reproducibility):
```bash
pip install -e .
python -m lsdyna_py.runner.cli --k path/to/case.k --ncpu 8 --memory 4000m --solver "C:\Program Files\...\lsdyna_dp.exe"
```

---

## Notes / Conventions

- This repo intentionally **does not** track large LS-DYNA outputs (`d3plot`, `binout`, etc.). See `.gitignore`.
- Windows paths with spaces: always quote them if passing via CLI.

---

## Next steps (suggested)

- Add `postprocess/parsers/nodout.py` and `postprocess/metrics/bfd.py`.
- Replace hard-coded parameters in generator scripts with `argparse` or YAML configs.
- Add unit tests for parsers and keyword writers in `tests/`.
