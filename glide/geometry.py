"""Procedural meshes -- the whole game is modelled from code, no assets."""

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def _finish(name, vdata, prim):
    geom = Geom(vdata)
    geom.add_primitive(prim)
    node = GeomNode(name)
    node.add_geom(geom)
    np = NodePath(node)
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


def make_sphere(radius, color, segments=20, rings=14):
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
