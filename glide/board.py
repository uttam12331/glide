"""Visual board: bordered tiles, an animated orb with a trail, and effects."""

import math
import random
from collections import deque

from panda3d.core import LineSegs, PointLight, Vec3, Vec4

from . import settings
from .geometry import make_box, make_octahedron, make_ring, make_sphere


class Board:
    def __init__(self, render, level):
        self.render = render
        self.level = level
        self.root = render.attach_new_node("board")
        self.tiles = {}          # (r, c) -> recolorable face NodePath
        self.stop_markers = {}   # (r, c) -> diamond NodePath
        self._pops = []
        self._t = 0.0
        self._orb_base = Vec3(0, 0, 0)
        self._trail = deque(maxlen=settings.TRAIL_LENGTH)
        self._trail_np = None

        self._build_floor()
        for (r, c) in sorted(level.fillable):
            # A darker base plate gives every tile a crisp border.
            base = make_box(settings.TILE_SIZE / 2, settings.TILE_SIZE / 2,
                            settings.TILE_THICK * 0.35, settings.EMPTY_EDGE)
            base.reparent_to(self.root)
            base.set_pos(self.cell_pos(r, c, z=0))
            base.set_light_off()
            face = make_box(settings.TILE_SIZE * 0.86 / 2, settings.TILE_SIZE * 0.86 / 2,
                            settings.TILE_THICK / 2, settings.EMPTY_COLOR)
            face.reparent_to(self.root)
            face.set_pos(self.cell_pos(r, c, z=settings.TILE_THICK * 0.35))
            face.set_light_off()
            self.tiles[(r, c)] = face
            if (r, c) in level.stops:
                m = make_octahedron(0.2, settings.STOP_COLOR)
                m.reparent_to(self.root)
                m.set_light_off()
                self.stop_markers[(r, c)] = m

        # Start ring marker.
        self.start_ring = make_ring(0.34, 0.07, settings.START_COLOR)
        self.start_ring.reparent_to(self.root)
        self.start_ring.set_light_off()

        # Orb + travelling light.
        self.orb = make_sphere(settings.ORB_RADIUS, settings.ORB_COLOR)
        self.orb.reparent_to(self.root)
        plight = PointLight("orb_light")
        plight.set_color(Vec4(0.5, 1.0, 0.9, 1))
        plight.set_attenuation((1, 0.15, 0.03))
        self.orb_light = self.root.attach_new_node(plight)
        self.render.set_light(self.orb_light)

        self.reset_visual(level.start)

    # -- coordinates ---------------------------------------------------------
    def cell_pos(self, r, c, z=0.0):
        return Vec3(c * settings.TILE, -r * settings.TILE, z)

    def orb_z(self):
        return settings.TILE_THICK * 0.35 + settings.ORB_RADIUS + 0.05

    def _build_floor(self):
        segs = LineSegs()
        segs.set_color(*settings.FLOOR_COLOR, 1.0)
        segs.set_thickness(1.0)
        z = -0.7
        lo_c, hi_c = -2, self.level.w + 1
        lo_r, hi_r = -2, self.level.h + 1
        for c in range(lo_c, hi_c + 1):
            segs.move_to(c * settings.TILE, -lo_r * settings.TILE, z)
            segs.draw_to(c * settings.TILE, -hi_r * settings.TILE, z)
        for r in range(lo_r, hi_r + 1):
            segs.move_to(lo_c * settings.TILE, -r * settings.TILE, z)
            segs.draw_to(hi_c * settings.TILE, -r * settings.TILE, z)
        floor = self.root.attach_new_node(segs.create())
        floor.set_light_off()

    # -- visual state --------------------------------------------------------
    def reset_visual(self, start):
        for cell, tile in self.tiles.items():
            tile.set_color(*settings.EMPTY_COLOR, 1.0)
            tile.set_pos(self.cell_pos(cell[0], cell[1], z=settings.TILE_THICK * 0.35))
        self.fill_tile(start, pop=False)
        self.place_orb(start)

    def fill_tile(self, cell, pop=True):
        tile = self.tiles.get(cell)
        if not tile:
            return
        color = settings.START_COLOR if cell == self.level.start else settings.FILLED_COLOR
        tile.set_color(*color, 1.0)
        tile.set_pos(self.cell_pos(cell[0], cell[1], z=settings.TILE_THICK * 0.55))
        if pop:
            self._spawn_pop(cell, color)

    def apply_state(self, filled, player):
        self.reset_visual(self.level.start)
        for cell in filled:
            self.fill_tile(cell, pop=False)
        self.place_orb(player)

    def place_orb(self, cell):
        self._orb_base = self.cell_pos(cell[0], cell[1], z=self.orb_z())

    def move_orb(self, world_xy):
        self._orb_base = Vec3(world_xy.x, world_xy.y, self.orb_z())

    # -- pops ----------------------------------------------------------------
    def _spawn_pop(self, cell, color):
        base = self.cell_pos(cell[0], cell[1], z=0.15)
        for _ in range(7):
            p = make_box(0.06, 0.06, 0.06, color)
            p.reparent_to(self.root)
            p.set_pos(base)
            p.set_light_off()
            p.set_transparency(True)
            vel = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                       random.uniform(1.8, 3.4))
            self._pops.append([p, vel, 0.0])

    # -- per-frame animation -------------------------------------------------
    def update(self, dt):
        self._t += dt

        # Orb bob + light follow.
        bob = math.sin(self._t * 3.0) * settings.ORB_BOB
        orb_pos = self._orb_base + Vec3(0, 0, bob)
        self.orb.set_pos(orb_pos)
        self.orb_light.set_pos(orb_pos + Vec3(0, 0, 0.4))

        # Motion trail.
        self._trail.append(Vec3(orb_pos))
        self._rebuild_trail()

        # Start ring pulse.
        s = 1.0 + 0.12 * math.sin(self._t * 4.0)
        self.start_ring.set_scale(s)
        self.start_ring.set_pos(
            self.cell_pos(self.level.start[0], self.level.start[1],
                          z=settings.TILE_THICK * 0.6))

        # Stop diamonds spin + hover.
        for cell, m in self.stop_markers.items():
            m.set_h(self._t * 120)
            hover = 0.28 + 0.06 * math.sin(self._t * 3.5 + cell[0])
            m.set_pos(self.cell_pos(cell[0], cell[1], z=hover))

        # Pops.
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

    def _rebuild_trail(self):
        if self._trail_np:
            self._trail_np.remove_node()
            self._trail_np = None
        if len(self._trail) < 2:
            return
        segs = LineSegs()
        n = len(self._trail)
        for i, p in enumerate(self._trail):
            frac = i / (n - 1)
            segs.set_thickness(1.0 + frac * 6.0)
            segs.set_color(settings.TRAIL_COLOR[0], settings.TRAIL_COLOR[1],
                           settings.TRAIL_COLOR[2], frac * 0.8)
            if i == 0:
                segs.move_to(p)
            else:
                segs.draw_to(p)
        self._trail_np = self.root.attach_new_node(segs.create())
        self._trail_np.set_light_off()
        self._trail_np.set_transparency(True)
        self._trail_np.set_depth_write(False)

    def celebrate(self):
        for cell in self.level.fillable:
            self._spawn_pop(cell, settings.WIN_COLOR)
            self.tiles[cell].set_color(*settings.WIN_COLOR, 1.0)

    def setup_camera(self, camera, lens):
        cx = (self.level.w - 1) * settings.TILE / 2.0
        cy = -(self.level.h - 1) * settings.TILE / 2.0
        span = max(self.level.w, self.level.h) * settings.TILE
        dist = span + settings.CAM_MARGIN
        ang = math.radians(settings.CAM_ANGLE)
        camera.set_pos(cx, cy - math.cos(ang) * dist, math.sin(ang) * dist)
        camera.look_at(cx, cy, 0)
        lens.set_fov(55)

    def destroy(self):
        if self._trail_np:
            self._trail_np.remove_node()
        self.render.clear_light(self.orb_light)
        self.root.remove_node()
