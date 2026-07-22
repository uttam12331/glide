#!/usr/bin/env python
"""Benchmark the pure-Python solver against the native C++ solver.

Build the extension first (see native/README or the CI workflow); otherwise this
reports Python-only timings.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glide import level as level_mod          # noqa: E402
from glide import native_solver               # noqa: E402
from glide.solver import solve                 # noqa: E402

REPS = 40


def main():
    levels = [level_mod.load(p) for p in level_mod.list_levels()]
    print("Backend available:", native_solver.backend())
    print("Levels:", ", ".join(l.name for l in levels))

    t0 = time.perf_counter()
    for _ in range(REPS):
        for lv in levels:
            solve(lv, *lv.initial_state())
    py = time.perf_counter() - t0
    print("\nPython solver : {:.3f} s  ({} solves)".format(py, REPS * len(levels)))

    if native_solver.is_native_available():
        t0 = time.perf_counter()
        for _ in range(REPS):
            for lv in levels:
                native_solver.par(lv)
        nat = time.perf_counter() - t0
        print("C++ solver    : {:.3f} s  ({} solves)".format(nat, REPS * len(levels)))
        if nat > 0:
            print("\nSpeedup       : {:.1f}x".format(py / nat))
    else:
        print("C++ solver    : not built -- run cmake to enable the comparison")


if __name__ == "__main__":
    main()
