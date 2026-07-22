"""HUD text and the menu / win / stuck overlays."""

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, Vec4


class Hud:
    def __init__(self, base):
        self.a2d = base.aspect2d
        self.tl = base.a2dTopLeft
        self.bl = base.a2dBottomLeft
        self._overlay = []

        common = dict(fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.6), mayChange=True)
        self.title = OnscreenText(parent=self.tl, text="", pos=(0.08, -0.12),
                                  scale=0.07, align=TextNode.ALeft, **common)
        self.stats = OnscreenText(parent=self.tl, text="", pos=(0.08, -0.22),
                                  scale=0.05, align=TextNode.ALeft, **common)
        self.hint = OnscreenText(parent=self.bl, text="", pos=(0.08, 0.09),
                                 scale=0.042, align=TextNode.ALeft,
                                 fg=(0.7, 0.85, 1, 1), shadow=(0, 0, 0, 0.6),
                                 mayChange=True)

    def set_playing(self, name, moves, par, best):
        self.title.setText(name)
        best_s = str(best) if best is not None else "-"
        par_s = str(par) if par is not None else "-"
        self.stats.setText("Moves {}    Best {}    Par {}".format(moves, best_s, par_s))
        self.hint.setText("Arrows/WASD glide   U undo   R restart   H hint   "
                          "N/P level   ESC menu")

    def clear_playing(self):
        for t in (self.title, self.stats, self.hint):
            t.setText("")

    # -- overlays ------------------------------------------------------------
    def _line(self, text, y, scale, color):
        self._overlay.append(OnscreenText(
            parent=self.a2d, text=text, pos=(0, y), scale=scale, fg=color,
            shadow=(0, 0, 0, 0.7), align=TextNode.ACenter))

    def clear_overlay(self):
        for n in self._overlay:
            n.destroy()
        self._overlay = []

    def show_menu(self, level_names):
        self.clear_overlay()
        self._line("GLIDE", 0.6, 0.2, Vec4(0.15, 0.95, 0.8, 1))
        self._line("You can't stop until you hit something.", 0.4, 0.05,
                   Vec4(0.9, 0.95, 1, 1))
        self._line("Light up every tile in one journey -- but your own glowing",
                   0.31, 0.045, Vec4(0.8, 0.85, 1, 1))
        self._line("trail becomes a wall. Amber tiles halt your slide.",
                   0.25, 0.045, Vec4(0.8, 0.85, 1, 1))
        y = 0.08
        self._line("Select a level (1-{}):".format(len(level_names)),
                   y + 0.05, 0.05, Vec4(1, 1, 1, 1))
        for i, nm in enumerate(level_names):
            self._line("{}.  {}".format(i + 1, nm), y - i * 0.07, 0.045,
                       Vec4(0.5, 1, 0.85, 1))
        self._line("ENTER start    ESC quit", y - len(level_names) * 0.07 - 0.04,
                   0.045, Vec4(0.7, 0.8, 1, 1))

    def show_win(self, moves, par, best, has_next):
        self.clear_overlay()
        star = "PERFECT!" if (par is not None and moves <= par) else "SOLVED"
        self._line(star, 0.35, 0.14, Vec4(0.55, 1, 0.7, 1))
        self._line("{} moves   (par {})".format(moves, par if par else "-"),
                   0.2, 0.055, Vec4(0.9, 0.95, 1, 1))
        nxt = "ENTER next level" if has_next else "ENTER finish"
        self._line(nxt + "    R replay    ESC menu", 0.05, 0.05,
                   Vec4(0.7, 0.8, 1, 1))

    def show_stuck(self):
        self.clear_overlay()
        self._line("STUCK -- no tile left to reach", 0.12, 0.06,
                   Vec4(1, 0.5, 0.4, 1))
        self._line("U undo    R restart    H hint", -0.02, 0.05,
                   Vec4(0.8, 0.85, 1, 1))

    def show_done(self):
        self.clear_overlay()
        self._line("ALL LEVELS CLEARED", 0.3, 0.13, Vec4(0.15, 0.95, 0.8, 1))
        self._line("Thanks for playing GLIDE.", 0.13, 0.055, Vec4(0.9, 0.95, 1, 1))
        self._line("ENTER back to menu", -0.03, 0.05, Vec4(0.7, 0.8, 1, 1))
