#!/usr/bin/env python
"""
CLI: run a single LS-DYNA case (direct solver call)

Examples
--------
# Basic
python -m lsdyna_py.runner.cli --k case.k --ncpu 8 --memory 4000m

# With dump/restart output
python -m lsdyna_py.runner.cli --k case.k --ncpu 8 --memory 4000m --dump dump01

Notes
-----
- This uses the "direct" solver invocation (lsdyna_dp.exe i=... ncpu=... memory=...).
- If you prefer LS-Run (bat) based launching, add another backend under lsdyna_py/runner later.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from .dyna_direct import run_lsdyna

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", required=True, help="Path to input .k file")
    ap.add_argument("--ncpu", type=int, default=8)
    ap.add_argument("--memory", default="4000m", help="LS-DYNA memory string, e.g. 4000m")
    ap.add_argument("--dump", default=None, help="Optional R= dump/restart file name")
    ap.add_argument("--work-dir", default=None, help="Working directory to run in (default: k-file directory)")
    ap.add_argument("--solver", default=None, help="Override dynasolver_path (lsdyna_dp.exe)")

    args = ap.parse_args()

    k = Path(args.k).expanduser().resolve()
    work_dir = args.work_dir or str(k.parent)

    # Call your original function. If solver is None, your default path inside run_lsdyna.py will be used.
    if args.solver:
        run_lsdyna(str(k), args.ncpu, args.memory, dump_file=args.dump, work_dir=work_dir, dynasolver_path=args.solver)
    else:
        run_lsdyna(str(k), args.ncpu, args.memory, dump_file=args.dump, work_dir=work_dir)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
