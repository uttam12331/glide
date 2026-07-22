"""Level model and the pure slide/fill rules.

A level is an ASCII grid:
    '.'  fillable empty cell
    'o'  start (also fillable)
    's'  stop tile -- a slide halts here even if it could continue
    '#'  wall / gap (blocks movement, never filled)

The move rules are deliberately tiny and side-effect free so they can be reused
by both the game and the solver without any engine dependency.
"""

import json
import os

LEVELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "levels")

DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def list_levels():
    files = [f for f in os.listdir(LEVELS_DIR) if f.endswith(".json")]
    return [os.path.join(LEVELS_DIR, f) for f in sorted(files)]


class Level:
    def __init__(self, data):
        self.name = data.get("name", "Level")
        self.par = data.get("par")            # optimal move count (solver-computed)
        rows = data["grid"]
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.grid = [r.ljust(self.w, "#") for r in rows]

        self.start = None
        self.fillable = set()
        self.stops = set()
        for r in range(self.h):
            for c in range(self.w):
                ch = self.grid[r][c]
                if ch in ".os":
                    self.fillable.add((r, c))
                if ch == "o":
                    self.start = (r, c)
                if ch == "s":
                    self.stops.add((r, c))
        if self.start is None:
            raise ValueError("Level '{}' has no start 'o'".format(self.name))

    def is_wall(self, r, c):
        if r < 0 or r >= self.h or c < 0 or c >= self.w:
            return True
        return self.grid[r][c] not in ".os"

    def initial_state(self):
        return self.start, frozenset([self.start])

    def is_win(self, filled):
        return self.fillable <= filled


def slide(level, player, filled, direction):
    """Slide from *player* in *direction* until something stops us.

    Returns ``(path_cells, new_player, new_filled)`` or ``None`` if the move
    makes no progress (immediately blocked).
    """
    dr, dc = DIRS[direction]
    r, c = player
    path = []
    while True:
        tr, tc = r + dr, c + dc
        if level.is_wall(tr, tc):
            break
        if (tr, tc) in filled:            # our own lit trail is a wall
            break
        r, c = tr, tc
        path.append((r, c))
        if (r, c) in level.stops:         # stop tiles halt the slide
            break
    if not path:
        return None
    return path, (r, c), filled | set(path)


def legal_moves(level, player, filled):
    return [d for d in DIRS if slide(level, player, filled, d) is not None]


def load(path):
    # utf-8-sig tolerates a byte-order mark if an editor added one.
    with open(path, "r", encoding="utf-8-sig") as fh:
        return Level(json.load(fh))
