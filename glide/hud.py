"""HUD text, a progress bar, and the menu / win / stuck overlays."""

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, TextNode, Vec4

from . import settings


def _card(parent, l, r, b, t, color):
    cm = CardMaker("panel")
    cm.set_frame(l, r, b, t)
    np = parent.attach_new_node(cm.generate())
    np.set_color(*color)
    np.set_transparency(True)
    return np


class Hud:
    def __init__(self, base):
        self.a2d = base.aspect2d
        self.tl = base.a2dTopLeft
        self.bl = base.a2dBottomLeft
        self._overlay = []

        self.panel = _card(self.tl, 0.04, 0.72, -0.46, -0.03, (0.05, 0.06, 0.12, 0.55))
        common = dict(fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), mayChange=True)
        self.title = OnscreenText(parent=self.tl, text="", pos=(0.1, -0.13),
                                  scale=0.075, align=TextNode.ALeft, **common)
        self.stats = OnscreenText(parent=self.tl, text="", pos=(0.1, -0.235),
                                  scale=0.048, align=TextNode.ALeft, **common)
        # Fill-progress bar.
        self.bar_bg = _card(self.tl, 0.1, 0.66, -0.42, -0.39, (0.16, 0.18, 0.26, 0.9))
        self.bar_fill = _card(self.tl, 0.1, 0.66, -0.42, -0.39,
                              settings.FILLED_COLOR + (1.0,))
        self.hint = OnscreenText(parent=self.bl, text="", pos=(0.08, 0.09),
                                 scale=0.04, align=TextNode.ALeft,
                                 fg=(0.65, 0.8, 1, 1), shadow=(0, 0, 0, 0.6),
                                 mayChange=True)

    def set_playing(self, name, moves, par, best, filled, total):
        self.panel.show()
        self.bar_bg.show()
        self.bar_fill.show()
        self.title.setText(name)
        best_s = str(best) if best is not None else "-"
        par_s = str(par) if par is not None else "-"
        self.stats.setText("Moves {}     Par {}     Best {}".format(moves, par_s, best_s))
        frac = filled / total if total else 0.0
        self.bar_fill.set_scale(max(0.001, frac), 1, 1)
        self.hint.setText("Arrows/WASD glide    U undo    R restart    "
                          "H hint    N/P level    ESC menu")

    def clear_playing(self):
        for t in (self.title, self.stats, self.hint):
            t.setText("")
        self.panel.hide()
        self.bar_bg.hide()
        self.bar_fill.hide()

    # -- overlays ------------------------------------------------------------
    def _dim(self):
        self._overlay.append(_card(self.a2d, -2, 2, -1.1, 1.1, (0.02, 0.02, 0.05, 0.65)))

    def _line(self, text, y, scale, color):
        self._overlay.append(OnscreenText(
            parent=self.a2d, text=text, pos=(0, y), scale=scale, fg=color,
            shadow=(0, 0, 0, 0.7), align=TextNode.ACenter))

    def clear_overlay(self):
        for n in self._overlay:
            if hasattr(n, "destroy"):
                n.destroy()
            else:
                n.remove_node()
        self._overlay = []

    def show_menu(self, levels):
        """levels: list of (name, par)."""
        self.clear_overlay()
        self._dim()
        self._line("GLIDE", 0.66, 0.22, Vec4(0.15, 0.98, 0.82, 1))
        self._line("You can't stop until you hit something.", 0.45, 0.05,
                   Vec4(0.9, 0.95, 1, 1))
        self._line("Light every tile in one journey -- your glowing trail is a wall.",
                   0.37, 0.045, Vec4(0.78, 0.83, 1, 1))
        y = 0.16
        for i, (nm, par) in enumerate(levels):
            self._line("{}.  {}   (par {})".format(i + 1, nm, par if par else "-"),
                       y - i * 0.075, 0.05, Vec4(0.5, 1, 0.85, 1))
        self._line("Press 1-{} or ENTER to start      ESC quit".format(len(levels)),
                   y - len(levels) * 0.075 - 0.05, 0.045, Vec4(0.7, 0.8, 1, 1))

    def show_win(self, moves, par, best, has_next):
        self.clear_overlay()
        self._dim()
        if par is not None and moves <= par:
            label, color = "PERFECT", Vec4(1, 0.85, 0.3, 1)
        elif par is not None and moves <= round(par * 1.34):
            label, color = "GREAT", Vec4(0.3, 0.95, 1, 1)
        else:
            label, color = "SOLVED", Vec4(0.85, 0.95, 1, 1)
        self._line(label, 0.34, 0.16, color)
        self._line("{} moves    (par {})".format(moves, par if par else "-"),
                   0.16, 0.055, Vec4(0.9, 0.95, 1, 1))
        if best is not None:
            self._line("best {}".format(best), 0.08, 0.045, Vec4(0.6, 0.7, 0.9, 1))
        nxt = "ENTER next level" if has_next else "ENTER finish"
        self._line(nxt + "     R replay     ESC menu", -0.08, 0.048,
                   Vec4(0.7, 0.8, 1, 1))

    def show_stuck(self):
        self.clear_overlay()
        self._line("NO TILE LEFT TO REACH", 0.1, 0.06, Vec4(1, 0.5, 0.4, 1))
        self._line("U undo    R restart    H hint", -0.02, 0.05,
                   Vec4(0.85, 0.9, 1, 1))

    def show_done(self):
        self.clear_overlay()
        self._dim()
        self._line("ALL LEVELS CLEARED", 0.3, 0.13, Vec4(0.15, 0.98, 0.82, 1))
        self._line("Thanks for playing GLIDE.", 0.13, 0.055, Vec4(0.9, 0.95, 1, 1))
        self._line("ENTER back to menu", -0.03, 0.05, Vec4(0.7, 0.8, 1, 1))
