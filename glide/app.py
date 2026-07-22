"""GLIDE -- application, state machine, input, and the slide animation."""

import os
import sys

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    ClockObject,
    DirectionalLight,
    TextNode,
    Vec3,
    Vec4,
)

from . import settings
from . import level as level_mod
from . import solver
from .board import Board
from .hud import Hud
from .level import legal_moves, slide

MENU, PLAYING, WIN, DONE = range(4)
globalClock = ClockObject.get_global_clock()

KEY_TO_DIR = {
    "arrow_up": "up", "arrow_down": "down",
    "arrow_left": "left", "arrow_right": "right",
    "w": "up", "s": "down", "a": "left", "d": "right",
}


class GlideApp(ShowBase):
    def __init__(self, debug=False, smoke=False, shot=False, shot_out=None):
        ShowBase.__init__(self)
        self.setBackgroundColor(*settings.BG_COLOR)
        self.disableMouse()
        self.render.set_shader_auto()

        self.smoke = smoke
        self.shot = shot
        self.shot_out = shot_out
        self.frame_count = 0
        if smoke or shot:
            globalClock.set_mode(ClockObject.M_non_real_time)
            globalClock.set_frame_rate(60)

        self._setup_lights()
        self.hud = Hud(self)

        self.level_paths = level_mod.list_levels()
        self.level_names = [level_mod.load(p).name for p in self.level_paths]
        self.best = {}                     # level index -> best move count

        self.state = None
        self.level = None
        self.board = None
        self.animating = False
        self.stuck = False
        self.toast_node = None
        self.toast_t = 0.0

        self._bind_keys()
        self.taskMgr.add(self.update, "update")

        if smoke:
            self.load_level(0)
        elif shot:
            self.load_level(min(3, len(self.level_paths) - 1))
        else:
            self.enter_menu()

    def _setup_lights(self):
        amb = AmbientLight("amb")
        amb.set_color(Vec4(0.45, 0.47, 0.55, 1))
        self.render.set_light(self.render.attach_new_node(amb))
        sun = DirectionalLight("sun")
        sun.set_color(Vec4(0.55, 0.58, 0.7, 1))
        sun_np = self.render.attach_new_node(sun)
        sun_np.set_hpr(-30, -60, 0)
        self.render.set_light(sun_np)

    def _bind_keys(self):
        for key in KEY_TO_DIR:
            self.accept(key, self._on_move, [KEY_TO_DIR[key]])
        self.accept("u", self._on_undo)
        self.accept("r", self._on_restart)
        self.accept("h", self._on_hint)
        self.accept("n", self._on_next)
        self.accept("p", self._on_prev)
        self.accept("enter", self._on_enter)
        self.accept("escape", self._on_escape)
        for i in range(1, 10):
            self.accept(str(i), self._on_select, [i - 1])

    # -- states --------------------------------------------------------------
    def enter_menu(self):
        self.state = MENU
        self._teardown_level()
        self.hud.clear_playing()
        self.hud.show_menu(self.level_names)

    def load_level(self, index):
        self.hud.clear_overlay()
        self._teardown_level()
        self.level_index = max(0, min(index, len(self.level_paths) - 1))
        self.level = level_mod.load(self.level_paths[self.level_index])
        self.board = Board(self.render, self.level)
        self.board.setup_camera(self.camera, self.camLens)

        self.player, filled = self.level.initial_state()
        self.filled = set(filled)
        self.undo_stack = []
        self.moves = 0
        self.animating = False
        self.stuck = False
        self.state = PLAYING
        self._update_hud()

        if self.smoke or self.shot:
            self.auto_solution = solver.solve(self.level, self.player, self.filled)
            self.auto_index = 0

    def _teardown_level(self):
        if self.board:
            self.board.destroy()
            self.board = None
        self.level = None

    def _win(self):
        self.state = WIN
        prev = self.best.get(self.level_index)
        if prev is None or self.moves < prev:
            self.best[self.level_index] = self.moves
        self.board.celebrate()
        has_next = self.level_index + 1 < len(self.level_paths)
        self.hud.show_win(self.moves, self.level.par,
                          self.best.get(self.level_index), has_next)

    # -- input ---------------------------------------------------------------
    def _on_move(self, direction):
        if self.state != PLAYING or self.animating or self.stuck:
            return
        old = self.player
        res = slide(self.level, self.player, self.filled, direction)
        if res is None:
            return
        path, new_player, new_filled = res
        self.undo_stack.append((old, set(self.filled)))
        self.player, self.filled = new_player, new_filled
        self.moves += 1
        self.anim_nodes = [old] + path
        self.anim_cells = path
        self.anim_p = 0.0
        self.anim_lit = 0
        self.animating = True
        self._update_hud()

    def _on_undo(self):
        if self.animating or self.state != PLAYING or not self.undo_stack:
            return
        self.player, filled = self.undo_stack.pop()
        self.filled = set(filled)
        self.moves = max(0, self.moves - 1)
        self.stuck = False
        self.hud.clear_overlay()
        self.board.apply_state(self.filled, self.player)
        self._update_hud()

    def _on_restart(self):
        if self.level is None:
            return
        self.player, filled = self.level.initial_state()
        self.filled = set(filled)
        self.undo_stack = []
        self.moves = 0
        self.animating = False
        self.stuck = False
        self.state = PLAYING
        self.hud.clear_overlay()
        self.board.apply_state(self.filled, self.player)
        self._update_hud()

    def _on_hint(self):
        if self.state != PLAYING or self.animating:
            return
        direction = solver.hint(self.level, self.player, self.filled)
        if direction:
            self._toast("Hint:  " + direction.upper())
        else:
            self._toast("No path from here -- press U to undo")

    def _on_next(self):
        if self.level_index + 1 < len(self.level_paths):
            self.load_level(self.level_index + 1)

    def _on_prev(self):
        if self.level is not None and self.level_index > 0:
            self.load_level(self.level_index - 1)

    def _on_select(self, index):
        if index < len(self.level_paths):
            self.load_level(index)

    def _on_enter(self):
        if self.state == MENU:
            self.load_level(0)
        elif self.state == WIN:
            if self.level_index + 1 < len(self.level_paths):
                self.load_level(self.level_index + 1)
            else:
                self.state = DONE
                self.hud.show_done()
        elif self.state == DONE:
            self.enter_menu()

    def _on_escape(self):
        if self.state in (PLAYING, WIN, DONE):
            self.enter_menu()
        else:
            sys.exit(0)

    # -- helpers -------------------------------------------------------------
    def _update_hud(self):
        if self.level is not None:
            self.hud.set_playing(self.level.name, self.moves, self.level.par,
                                 self.best.get(self.level_index))

    def _toast(self, text):
        if self.toast_node:
            self.toast_node.destroy()
        self.toast_node = OnscreenText(
            parent=self.aspect2d, text=text, pos=(0, -0.55), scale=0.07,
            fg=(1, 0.9, 0.4, 1), shadow=(0, 0, 0, 0.7), align=TextNode.ACenter)
        self.toast_t = 2.0

    # -- loop ----------------------------------------------------------------
    def update(self, task):
        dt = min(globalClock.get_dt(), 1.0 / 30.0)
        if self.board:
            self.board.update(dt)
        if self.animating:
            self._advance_anim(dt)
        if self.toast_t > 0:
            self.toast_t -= dt
            if self.toast_t <= 0 and self.toast_node:
                self.toast_node.destroy()
                self.toast_node = None
        if self.smoke or self.shot:
            self._auto_step()
        return task.cont

    def _advance_anim(self, dt):
        self.anim_p += settings.SLIDE_SPEED * dt
        seg = int(self.anim_p)
        if seg >= len(self.anim_nodes) - 1:
            self._finish_anim()
            return
        frac = self.anim_p - seg
        a = self.board.cell_pos(*self.anim_nodes[seg])
        b = self.board.cell_pos(*self.anim_nodes[seg + 1])
        self.board.move_orb(a * (1.0 - frac) + b * frac)
        while (self.anim_lit < len(self.anim_cells)
               and self.anim_p >= self.anim_lit + 1):
            self.board.fill_tile(self.anim_cells[self.anim_lit])
            self.anim_lit += 1

    def _finish_anim(self):
        for i in range(self.anim_lit, len(self.anim_cells)):
            self.board.fill_tile(self.anim_cells[i])
        self.board.place_orb(self.player)
        self.animating = False
        if self.level.is_win(self.filled):
            self._win()
        elif not legal_moves(self.level, self.player, self.filled):
            self.stuck = True
            self.hud.show_stuck()

    # -- headless helpers ----------------------------------------------------
    def _auto_step(self):
        self.frame_count += 1
        if self.animating:
            return
        if self.shot:
            sol = getattr(self, "auto_solution", None) or []
            target = int(len(sol) * 0.6)
            if self.auto_index < target:
                self._on_move(sol[self.auto_index])
                self.auto_index += 1
                return
            out = self.shot_out or "screenshots/glide.png"
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            self.graphicsEngine.render_frame()
            self.screenshot(namePrefix=out, defaultFilename=False)
            print("SHOT OK:", out)
            sys.exit(0)

        # smoke: play the computed solution and confirm we win.
        if self.state == WIN:
            print("SMOKE OK: solved '{}' in {} moves (par {})".format(
                self.level.name, self.moves, self.level.par))
            sys.exit(0)
        sol = getattr(self, "auto_solution", None)
        if not sol:
            print("SMOKE FAIL: no solution found")
            sys.exit(1)
        if self.auto_index < len(sol):
            self._on_move(sol[self.auto_index])
            self.auto_index += 1
        elif self.frame_count > 4000:
            print("SMOKE FAIL: solution did not win")
            sys.exit(1)
