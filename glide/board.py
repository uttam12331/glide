"""Visual board: tiles, the orb, the fill animation, and pop effects."""

import random

from panda3d.core import PointLight, Vec3, Vec4

from . import settings
from .geometry import make_box, make_sphere


class Board:
    def __init__(self, render, level):
        self.render = render
        self.level = level
        self.root = render.attach_new_node("board")
        self.tiles = {}          # (r, c) -> NodePath
        self.markers = {}        # (r, c) -> stop-tile marker NodePath
        self._pops = []          # active particle bursts

        for (r, c) in level.fillable:
            tile = make_box(settings.TILE_SIZE / 2, settings.TILE_SIZE / 2,
                            settings.TILE_THICK / 2, settings.EMPTY_COLOR)
            tile.reparent_to(self.root)
            tile.set_pos(self.cell_pos(r, c, z=0))
            tile.set_light_off()             # tiles are flat neon; only the orb is lit
            self.tiles[(r, c)] = tile
            if (r, c) in level.stops:
                m = make_box(0.18, 0.18, 0.05, settings.STOP_COLOR)
                m.reparent_to(self.root)
                m.set_pos(self.cell_pos(r, c, z=settings.TILE_THICK / 2 + 0.03))
                m.set_light_off()
                self.markers[(r, c)] = m

        # The orb + a soft light that travels with it.
        self.orb = make_sphere(settings.ORB_RADIUS, settings.ORB_COLOR)
        self.orb.reparent_to(self.root)     # orb stays lit so it reads as a 3D ball
        plight = PointLight("orb_light")
        plight.set_color(Vec4(0.5, 1.0, 0.9, 1))
        plight.set_attenuation((1, 0.15, 0.03))
        self.orb_light = self.root.attach_new_node(plight)
        self.render.set_light(self.orb_light)

        self.reset_visual(level.start)

    # -- coordinate helpers --------------------------------------------------
    def cell_pos(self, r, c, z=0.0):
        return Vec3(c * settings.TILE, -r * settings.TILE, z)

    def orb_z(self):
        return settings.TILE_THICK / 2 + settings.ORB_RADIUS

    # -- visual state --------------------------------------------------------
    def reset_visual(self, start):
        for cell, tile in self.tiles.items():
            tile.set_color(*settings.EMPTY_COLOR, 1.0)
            tile.set_pos(self.cell_pos(cell[0], cell[1], z=0))
        self.fill_tile(start, pop=False)
        self.place_orb(start)

    def fill_tile(self, cell, pop=True):
        tile = self.tiles.get(cell)
        if not tile:
            return
        color = settings.START_COLOR if cell == self.level.start else settings.FILLED_COLOR
        tile.set_color(*color, 1.0)                 # brighter neon = "filled"
        tile.set_pos(self.cell_pos(cell[0], cell[1], z=0.05))
        if pop:
            self._spawn_pop(cell, color)

    def apply_state(self, filled, player):
        """Repaint the board to match a logic state (used by undo / restart)."""
        self.reset_visual(self.level.start)
        for cell in filled:
            self.fill_tile(cell, pop=False)
        self.place_orb(player)

    def place_orb(self, cell):
        self.orb.set_pos(self.cell_pos(cell[0], cell[1], z=self.orb_z()))
        self.orb_light.set_pos(self.cell_pos(cell[0], cell[1], z=self.orb_z() + 0.3))

    def move_orb(self, world_xy):
        pos = Vec3(world_xy.x, world_xy.y, self.orb_z())
        self.orb.set_pos(pos)
        self.orb_light.set_pos(pos + Vec3(0, 0, 0.3))

    # -- fill-pop particles --------------------------------------------------
    def _spawn_pop(self, cell, color):
        base = self.cell_pos(cell[0], cell[1], z=0.1)
        for _ in range(6):
            p = make_box(0.06, 0.06, 0.06, color)
            p.reparent_to(self.root)
            p.set_pos(base)
            p.set_light_off()
            p.set_transparency(True)
            vel = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                       random.uniform(1.5, 3.0))
            self._pops.append([p, vel, 0.0])

    def update(self, dt):
        alive = []
        for p, vel, t in self._pops:
            t += dt
            if t >= settings.POP_TIME:
                p.remove_node()
                continue
            p.set_pos(p.get_pos() + vel * dt)
            frac = 1.0 - t / settings.POP_TIME
            p.set_scale(max(0.05, frac))
            p.set_alpha_scale(frac)
            alive.append([p, vel, t])
        self._pops = alive

    def celebrate(self):
        for cell in self.level.fillable:
            self._spawn_pop(cell, settings.WIN_COLOR)
            tile = self.tiles[cell]
            tile.set_color(*settings.WIN_COLOR, 1.0)

    def setup_camera(self, camera, lens):
        import math
        cx = (self.level.w - 1) * settings.TILE / 2.0
        cy = -(self.level.h - 1) * settings.TILE / 2.0
        span = max(self.level.w, self.level.h) * settings.TILE
        dist = span + settings.CAM_MARGIN
        ang = math.radians(settings.CAM_ANGLE)
        camera.set_pos(cx, cy - math.cos(ang) * dist, math.sin(ang) * dist)
        camera.look_at(cx, cy, 0)
        lens.set_fov(55)

    def destroy(self):
        self.render.clear_light(self.orb_light)
        self.root.remove_node()
