#!/usr/bin/env python
"""Generate guaranteed-solvable GLIDE levels and verify them with the solver.

Method: run a random sequence of legal slides on a full rectangle, then turn
every never-visited cell into a wall. A slide only ever stops at the trail or an
edge, so walling off the unvisited cells cannot change any executed slide -- the
recorded run therefore still solves the resulting level. Each candidate is then
re-checked with the independent BFS solver and tagged with its optimal par.

Usage:
    python tools/generate_levels.py            # print candidate levels
    python tools/generate_levels.py --write    # (re)write levels/*.json
"""

import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glide.level import DIRS, Level, slide          # noqa: E402
from glide.solver import solve                       # noqa: E402

LEVELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "levels")

# (name, width, height, min_cells, max_cells, stop_probability)
TARGETS = [
    ("First Glide", 3, 3, 7, 9, 0.0),
    ("Four Corners", 4, 4, 11, 15, 0.0),
    ("Switchback", 4, 5, 14, 19, 0.0),
    ("Anchor Point", 5, 5, 17, 24, 0.14),
    ("Crosscurrent", 5, 6, 21, 29, 0.12),
    ("The Long Way", 6, 6, 26, 35, 0.12),
]
SLUGS = ["01-first-glide", "02-four-corners", "03-switchback",
         "04-anchor-point", "05-crosscurrent", "06-the-long-way"]


def generate(w, h, seed, stop_prob):
    rng = random.Random(seed)
    start = (rng.randrange(h), rng.randrange(w))
    grid = [["."] * w for _ in range(h)]
    stops = set()
    if stop_prob:
        for r in range(h):
            for c in range(w):
                if (r, c) != start and rng.random() < stop_prob:
                    grid[r][c], _ = "s", stops.add((r, c))
    grid[start[0]][start[1]] = "o"
    lvl = Level({"name": "g", "grid": ["".join(r) for r in grid]})
    player, filled = start, {start}
    for _ in range(1500):
        legal = [d for d in DIRS if slide(lvl, player, filled, d)]
        if not legal:
            break
        _cells, player, filled = slide(lvl, player, filled, rng.choice(legal))
        if lvl.is_win(filled):
            break
    out = [["#"] * w for _ in range(h)]
    for (r, c) in filled:
        out[r][c] = "s" if (r, c) in stops else "."
    out[start[0]][start[1]] = "o"
    return ["".join(r) for r in out], len(filled)


def best_for(name, w, h, lo, hi, stop_prob, seeds=6000):
    """Search seeds for the hardest dense board matching the size window."""
    pick = None
    for seed in range(seeds):
        grid, n = generate(w, h, seed, stop_prob)
        if not (lo <= n <= hi) or n / (w * h) < 0.62:
            continue
        lvl = Level({"name": name, "grid": grid})
        sol = solve(lvl, *lvl.initial_state())
        if sol is None:
            continue
        if pick is None or len(sol) > pick["par"]:
            pick = {"name": name, "grid": grid, "par": len(sol)}
    return pick


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write levels/*.json")
    args = ap.parse_args()

    for slug, target in zip(SLUGS, TARGETS):
        lvl = best_for(*target)
        if lvl is None:
            print("NO LEVEL for", target[0])
            continue
        print("== {} (par {}) ==".format(lvl["name"], lvl["par"]))
        for row in lvl["grid"]:
            print("   " + row)
        if args.write:
            path = os.path.join(LEVELS_DIR, slug + ".json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(lvl, fh, indent=2)
            print("   -> wrote", path)


if __name__ == "__main__":
    main()
