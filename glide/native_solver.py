"""Optional ctypes bridge to the native C++ solver.

If the compiled library (``glide_native.dll`` / ``.so`` / ``.dylib``) is present
next to this package, ``par()`` uses the fast C++ bitmask BFS. Otherwise it
transparently falls back to the pure-Python solver, so the game always runs even
when the extension has not been built.

Build the library with:

    cmake -S native -B native/build && cmake --build native/build --config Release
"""

import ctypes
import glob
import os

from . import solver as py_solver

_LIB = None
_TRIED = False


def _load():
    global _LIB, _TRIED
    if _TRIED:
        return _LIB
    _TRIED = True
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    for pattern in ("glide_native*.dll", "glide_native*.so", "glide_native*.dylib"):
        candidates.extend(glob.glob(os.path.join(here, pattern)))
    for path in candidates:
        try:
            lib = ctypes.CDLL(path)
            lib.glide_solve_par.restype = ctypes.c_int
            lib.glide_solve_par.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
            lib.glide_abi_version.restype = ctypes.c_int
            if lib.glide_abi_version() == 1:
                _LIB = lib
                break
        except OSError:
            continue
    return _LIB


def is_native_available():
    return _load() is not None


def par(level):
    """Optimal move count for a level, via C++ if built, else pure Python."""
    lib = _load()
    if lib is None:
        solution = py_solver.solve(level, *level.initial_state())
        return len(solution) if solution is not None else -1

    # Flatten the padded grid to row-major chars for the C ABI.
    flat = "".join(row.ljust(level.w, "#") for row in level.grid).encode("ascii")
    return lib.glide_solve_par(flat, level.w, level.h)


def backend():
    return "c++" if is_native_available() else "python"
