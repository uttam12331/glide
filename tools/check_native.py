#!/usr/bin/env python
"""Verify the C++ solver agrees with the pure-Python solver on every level.

Run in CI after building native/. With GLIDE_REQUIRE_NATIVE=1 set, it also
asserts the compiled library actually loaded (so a broken build fails CI rather
than silently falling back to Python).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glide import level as level_mod          # noqa: E402
from glide import native_solver               # noqa: E402
from glide.solver import solve                 # noqa: E402


def main():
    require_native = os.environ.get("GLIDE_REQUIRE_NATIVE") == "1"
    backend = native_solver.backend()
    print("native backend:", backend)
    if require_native and backend != "c++":
        print("FAIL: native library required but not loaded")
        return 1

    ok = True
    for path in level_mod.list_levels():
        lvl = level_mod.load(path)
        py = solve(lvl, *lvl.initial_state())
        py_par = len(py) if py is not None else -1
        nat_par = native_solver.par(lvl)
        status = "ok" if py_par == nat_par else "MISMATCH"
        if py_par != nat_par:
            ok = False
        print("  {:16} python={} native={}  {}".format(
            lvl.name, py_par, nat_par, status))

    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
