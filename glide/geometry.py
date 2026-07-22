"""Procedural meshes -- the whole game is modelled from code, no assets."""

import math

from panda3d.core import (
    Geom,
    GeomLines,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def _finish(name, vdata, prim, two_sided=True):
    geom = Geom(vdata)
    geom.add_primitive(prim)
    node = GeomNode(name)
    node.add_geom(geom)
    np = NodePath(node)
    if two_sided:
        np.set_two_sided(True)
    return np


def make_box(hx, hy, hz, color):
    vdata = GeomVertexData("box", GeomVertexFormat.get_v3n3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UH_static)
    counter = [0]

    def quad(p1, p2, p3, p4, normal):
        base = counter[0]
        for p in (p1, p2, p3, p4):
            vw.add_data3(*p)
            nw.add_data3(*normal)
            cw.add_data4(color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0)
        tris.add_vertices(base, base + 1, base + 2)
        tris.add_vertices(base, base + 2, base + 3)
        counter[0] += 4

    x, y, z = hx, hy, hz
    quad((x, -y, -z), (x, y, -z), (x, y, z), (x, -y, z), (1, 0, 0))
    quad((-x, y, -z), (-x, -y, -z), (-x, -y, z), (-x, y, z), (-1, 0, 0))
    quad((x, y, -z), (-x, y, -z), (-x, y, z), (x, y, z), (0, 1, 0))
    quad((-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z), (0, -1, 0))
    quad((x, -y, z), (x, y, z), (-x, y, z), (-x, -y, z), (0, 0, 1))
    quad((-x, -y, -z), (-x, y, -z), (x, y, -z), (x, -y, -z), (0, 0, -1))
    return _finish("box", vdata, tris)


def make_sphere(radius, color, segments=22, rings=16):
    vdata = GeomVertexData("sphere", GeomVertexFormat.get_v3n3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UH_static)
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segments + 1):
            theta = 2.0 * math.pi * j / segments
            nx = math.sin(phi) * math.cos(theta)
            ny = math.sin(phi) * math.sin(theta)
            nz = math.cos(phi)
            vw.add_data3(nx * radius, ny * radius, nz * radius)
            nw.add_data3(nx, ny, nz)
            cw.add_data4(color[0], color[1], color[2], 1.0)
    stride = segments + 1
    for i in range(rings):
        for j in range(segments):
            a = i * stride + j
            b = a + stride
            tris.add_vertices(a, b, a + 1)
            tris.add_vertices(a + 1, b, b + 1)
    return _finish("sphere", vdata, tris)


def make_octahedron(radius, color):
    """A faceted diamond -- used for the animated stop-tile markers."""
    vdata = GeomVertexData("octa", GeomVertexFormat.get_v3n3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UH_static)
    r = radius
    verts = [(r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)]
    faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
             (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    n = 0
    for f in faces:
        p = [verts[k] for k in f]
        for vert in p:
            length = math.sqrt(sum(c * c for c in vert)) or 1.0
            vw.add_data3(*vert)
            nw.add_data3(vert[0] / length, vert[1] / length, vert[2] / length)
            cw.add_data4(color[0], color[1], color[2], 1.0)
        tris.add_vertices(n, n + 1, n + 2)
        n += 3
    return _finish("octa", vdata, tris)


def make_ring(radius, thickness, color, segments=28):
    """A flat annulus in the XY plane -- used to mark the start tile."""
    vdata = GeomVertexData("ring", GeomVertexFormat.get_v3n3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UH_static)
    inner, outer = radius - thickness * 0.5, radius + thickness * 0.5
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        for rad in (inner, outer):
            vw.add_data3(ca * rad, sa * rad, 0)
            nw.add_data3(0, 0, 1)
            cw.add_data4(color[0], color[1], color[2], 1.0)
    for i in range(segments):
        a = 2 * i
        tris.add_vertices(a, a + 1, a + 2)
        tris.add_vertices(a + 1, a + 3, a + 2)
    return _finish("ring", vdata, tris)


def make_points(positions, colors, thickness=2.0):
    vdata = GeomVertexData("points", GeomVertexFormat.get_v3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    cw = GeomVertexWriter(vdata, "color")
    prim = GeomPoints(Geom.UH_static)
    for i, pos in enumerate(positions):
        vw.add_data3(*pos)
        cw.add_data4(*colors[i])
        prim.add_vertex(i)
    np = _finish("points", vdata, prim, two_sided=False)
    np.set_render_mode_thickness(thickness)
    return np


def make_gradient_card(width, height, top_color, bottom_color):
    """A vertical-gradient quad used as a backdrop behind the board."""
    vdata = GeomVertexData("grad", GeomVertexFormat.get_v3c4(), Geom.UH_static)
    vw = GeomVertexWriter(vdata, "vertex")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UH_static)
    w, h = width * 0.5, height * 0.5
    corners = [(-w, -h, bottom_color), (w, -h, bottom_color),
               (w, h, top_color), (-w, h, top_color)]
    for x, z, col in corners:
        vw.add_data3(x, 0, z)
        cw.add_data4(col[0], col[1], col[2], 1.0)
    tris.add_vertices(0, 1, 2)
    tris.add_vertices(0, 2, 3)
    return _finish("grad", vdata, tris, two_sided=True)
