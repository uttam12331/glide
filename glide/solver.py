"""Breadth-first solver for GLIDE.

Because a lit trail is never un-lit, the filled set only grows, so the reachable
state space is small and BFS finds a *shortest* solution quickly. This powers
three things:
  * a build-time guarantee that every shipped level is solvable,
  * the in-game hint button, and
  * the "par" (optimal move count) shown on each level.
"""

from collections import deque

from .level import DIRS, slide


def solve(level, player, filled, node_limit=400000):
    """Return the shortest list of directions that wins, or ``None``."""
    filled = frozenset(filled)             # states must be hashable for `seen`
    if level.is_win(filled):
        return []
    start = (player, filled)
    seen = {start}
    queue = deque([(player, filled, [])])
    nodes = 0
    while queue:
        p, f, path = queue.popleft()
        nodes += 1
        if nodes > node_limit:
            return None
        for d in DIRS:
            res = slide(level, p, f, d)
            if res is None:
                continue
            _cells, np_, nf = res
            key = (np_, nf)
            if key in seen:
                continue
            if level.is_win(nf):
                return path + [d]
            seen.add(key)
            queue.append((np_, nf, path + [d]))
    return None


def hint(level, player, filled):
    """The next best move from the current position, or ``None`` if stuck."""
    solution = solve(level, player, filled)
    return solution[0] if solution else None
