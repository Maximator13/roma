import math
import random

import numpy as np
from mathutils import Matrix, Vector

from .arles_crowds import spectator
from .buildings import arched_wall, straight_moulding
from .geometry import MATTE, MeshBuilder, placement
from .orders import ENGAGED_HALF, column, gable_roof, pilaster, simple_entablature_profile
from .nimes_figures import tube

A = 43.0
B = 27.0
OUTER = 51.0
BAYS = 80
OPENING = 2.1
TRAV = "col_travertine"
MARBLE = "marble_white"
BRICK = "brick"
STUCCO = "stucco"
VOID = "shadow_void"
WOOD = (0.42, 0.30, 0.20)
LINEN = "velum_linen"
SAND = "arena_sand"
FACADE_TOP = 48.5
MAST_TOP = 56.0
RING_D = 7.0
RING_Z = 38.0
LEVELS = (0.0, 10.5, 22.3, 33.9)
TOGA = (0.90, 0.88, 0.80)
SKINS = [(0.80, 0.60, 0.47), (0.72, 0.52, 0.39), (0.62, 0.44, 0.32)]
HAIRS = [(0.17, 0.12, 0.09), (0.30, 0.20, 0.12), (0.45, 0.42, 0.38)]
COLOURS = {
    "plebs": [(0.80, 0.75, 0.64), (0.46, 0.34, 0.23), (0.74, 0.56, 0.32), (0.55, 0.51, 0.47), (0.64, 0.28, 0.20),
              (0.48, 0.50, 0.34), (0.30, 0.26, 0.23), (0.90, 0.88, 0.80)],
    "women": [(0.74, 0.50, 0.44), (0.42, 0.49, 0.58), (0.80, 0.71, 0.42), (0.64, 0.28, 0.20), (0.48, 0.50, 0.34),
              (0.40, 0.16, 0.24), (0.80, 0.75, 0.64), (0.30, 0.26, 0.23)],
}


def base(t):
    return Vector((A * math.cos(t), B * math.sin(t), 0.0))


def normal(t):
    return Vector((B * math.cos(t), A * math.sin(t), 0.0)).normalized()


def tangent(t):
    return Vector((-A * math.sin(t), B * math.cos(t), 0.0)).normalized()


def curvature(t):
    return A * B / ((A * math.sin(t)) ** 2 + (B * math.cos(t)) ** 2) ** 1.5


def oval(t, d, z=0.0):
    point = base(t) + normal(t) * d
    point.z = z
    return point


def even_angles(count, d, phase=0.0):
    ts = np.linspace(0.0, 2 * math.pi, 16385)
    nx, ny = B * np.cos(ts), A * np.sin(ts)
    length = np.hypot(nx, ny)
    xs = A * np.cos(ts) + d * nx / length
    ys = B * np.sin(ts) + d * ny / length
    cumulative = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
    total = cumulative[-1]
    targets = total * (np.arange(count) + phase) / count
    return [float(v) for v in np.interp(targets, cumulative, ts)], float(total)


def frame(t, d=OUTER, z=0.0):
    x_axis = -tangent(t)
    y_axis = normal(t)
    matrix = Matrix((x_axis, y_axis, Vector((0.0, 0.0, 1.0)))).transposed().to_4x4()
    matrix.translation = oval(t, d, z)
    return matrix


def local_ratio(depth, kappa):
    return (1.0 + (OUTER + depth) * kappa) / (1.0 + OUTER * kappa)


def taper(builder, kappa):
    builder.positions = [(x * local_ratio(y, kappa), y, z) for x, y, z in builder.positions]
    return builder


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def vault(builder, x0, x1, y_center, radius, spring, material, segments=7):
    rows = []
    for k in range(segments + 1):
        angle = math.pi * k / segments
        y = y_center + radius * math.cos(angle)
        z = spring + radius * math.sin(angle)
        rows.append([(x0, y, z), (x1, y, z)])
    builder.surface(rows, material, facing=(0, 0, -1))


def storey(builder, w, z0, z1, impost, sill, order, diameter, column_top, depth=2.6):
    hw = w / 2
    arched_wall(builder, -hw, hw, -depth, 0.0, z0, column_top, [(0.0, OPENING, impost)], TRAV, segments=8, sill=sill,
                foundation=0.6 if z0 == 0.0 else 0.0)
    builder.box((-hw, -depth, column_top), (hw, -0.25, z1), TRAV, bottom=False)
    straight_moulding(builder, -hw, hw, column_top, simple_entablature_profile(z1 - column_top, 0.42), TRAV)
    base_z = z0 if z0 == 0.0 else sill
    if z0 > 0.0:
        builder.box((-hw, 0.0, z0), (hw, 0.22, z0 + 0.35), TRAV, bottom=False)
    builder.merge(column(order, diameter, column_top - base_z, detail="low", material=TRAV, arc=ENGAGED_HALF),
                  placement(-hw, 0.02, base_z))
    builder.box((-0.5, 0.0, impost + OPENING), (0.5, 0.12, impost + OPENING + 0.5), TRAV, bottom=False)


def interior(builder, w, rings):
    hw = w / 2
    builder.box((-hw, -14.6, -0.2), (hw, -2.6, 0.0), TRAV, bottom=False)
    for level, (z0, z1) in enumerate(((0.0, 10.5), (10.5, 22.3))):
        arched_wall(builder, -hw, hw, -9.3, -7.9, z0, z1 - 0.4, [(0.0, 1.9, z0 + 5.0)], BRICK, segments=6)
        vault(builder, -hw, hw, -5.25, 2.65, z1 - 3.4, STUCCO)
        vault(builder, -hw, hw, -11.8, 2.5, z1 - 3.4, STUCCO)
        builder.box((-hw, -14.6, z1 - 0.75), (hw, -2.6, z1), BRICK, bottom=False)
        arched_wall(builder, -hw, hw, -15.0, -14.3, z0, z1 - 0.4, [(0.0, 1.0, z0 + 3.4)], BRICK, segments=4)
        builder.box((-1.0, -15.4, z0), (1.0, -15.0, z0 + 4.4), VOID, bottom=False)
    arched_wall(builder, -hw, hw, -9.3, -7.9, 22.3, 33.5, [(0.0, 1.0, 25.5)], BRICK, segments=4)
    builder.box((-1.0, -9.6, 22.3), (1.0, -9.3, 26.5), VOID, bottom=False)
    vault(builder, -hw, hw, -5.25, 2.65, 30.85, STUCCO)
    builder.box((-hw, -9.3, 33.5), (hw, -1.4, 33.9), BRICK, top=False)


def attic(builder, w):
    hw = w / 2
    top = FACADE_TOP
    builder.box((-hw, -1.6, LEVELS[3]), (hw, 0.0, 45.0), TRAV, bottom=False)
    builder.box((-hw, 0.0, LEVELS[3]), (hw, 0.32, 35.1), TRAV, bottom=False)
    builder.merge(pilaster(0.95, 9.9, 0.24, TRAV), placement(-hw, 0.0, 35.1))
    builder.box((-hw, -1.6, 45.0), (hw, 0.0, 46.4), TRAV, bottom=False)
    straight_moulding(builder, -hw, hw, 46.4, simple_entablature_profile(top - 46.4, 0.9), TRAV)
    builder.box((-hw, -1.6, 46.4), (hw, -0.5, top), TRAV, bottom=False)
    for x in (-w / 3, 0.0, w / 3):
        builder.box((x - 0.24, 0.0, 42.7), (x + 0.24, 0.72, 43.5), TRAV)
        painted(builder, WOOD, lambda x=x: builder.lathe([(0.15, 43.5), (0.12, MAST_TOP - 2.0), (0.09, MAST_TOP)], 6,
                                                         MATTE, matrix=placement(x, 0.45, 0.0)))


def attic_window():
    builder = MeshBuilder()
    builder.box((-0.75, 0.0, 38.6), (0.75, 0.05, 40.0), VOID, bottom=False)
    builder.box((-0.95, 0.0, 38.4), (0.95, 0.12, 38.6), TRAV, bottom=False)
    builder.box((-0.95, 0.0, 40.0), (0.95, 0.1, 40.15), TRAV, bottom=False)
    return builder


def clipeus():
    builder = MeshBuilder()
    builder.lathe([(0.0, 0.0), (0.72, 0.0), (0.72, 0.06), (0.6, 0.1), (0.15, 0.13), (0.0, 0.2)], 16, "bronze",
                  matrix=Matrix.Translation((0.0, 0.0, 39.3)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    return builder


def bay(w, kappa, porch=False):
    builder = MeshBuilder()
    hw = w / 2
    storey(builder, w, 0.0, 10.5, 4.95, None, "tuscan", 0.95, 8.6)
    storey(builder, w, 10.5, 22.3, 16.45, 11.6, "ionic", 0.9, 20.4, 2.4)
    storey(builder, w, 22.3, 33.9, 28.2, 23.4, "corinthian", 0.85, 31.9, 2.4)
    attic(builder, w)
    builder.box((-hw, 0.0, -0.6), (hw, 0.9, 0.12), TRAV, bottom=False)
    builder.box((-hw, 0.9, -0.6), (hw, 1.5, 0.0), TRAV, bottom=False)
    interior(builder, w, 2)
    builder.paint(TRAV, (1.0, 0.97, 0.93))
    builder.paint(BRICK, (0.62, 0.56, 0.52))
    builder.paint(STUCCO, (0.62, 0.58, 0.52))
    if porch:
        for x in (-2.3, 2.3):
            builder.merge(column("corinthian", 0.7, 6.6, detail="low", material=MARBLE), placement(x, 3.6, 0.12))
        builder.box((-2.9, 0.0, 6.7), (2.9, 4.2, 7.6), MARBLE)
        gable_roof(builder, 0.0, 4.4, 3.1, 7.6, 9.0, "terracotta_tiles", along_axis="y", imbrex=False)
        builder.oriented([(-3.1, 4.4, 7.6), (3.1, 4.4, 7.6), (0.0, 4.4, 9.0)], (0, 1, 0), MARBLE)
    return taper(builder, kappa)


def bay_frames():
    angles, total = even_angles(BAYS, OUTER)
    width = total / BAYS
    kappas = [curvature(t) for t in angles]
    return angles, width, kappas


def classes(kappas, count=4):
    logs = np.log(kappas)
    edges = np.linspace(logs.min(), logs.max() + 1e-9, count + 1)
    index = np.clip(np.digitize(logs, edges) - 1, 0, count - 1)
    means = [float(np.exp(logs[index == k].mean())) for k in range(count)]
    return [int(i) for i in index], means


def numeral(value):
    table = ((50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    text = ""
    for amount, letters in table:
        while value >= amount:
            text += letters
            value -= amount
    return text


def bay_number(k):
    if k % 20 == 0:
        return None
    quadrant = (k - 60) % 80
    return quadrant - (quadrant // 20)


PROFILE = []


def cavea_profile():
    if PROFILE:
        return PROFILE
    rows = [("podium_wall", 0.0, 0.0, 0.0, 3.6), ("parapet", 0.0, 3.6, 0.0, 4.6), ("parapet_top", 0.0, 4.6, 0.35, 4.6),
            ("parapet_back", 0.35, 4.6, 0.35, 3.6)]
    terrace = [(0.35, 3.6), (1.8, 3.6), (1.8, 3.9), (3.2, 3.9), (3.2, 4.2), (5.6, 4.2)]
    for (d0, z0), (d1, z1) in zip(terrace[:-1], terrace[1:]):
        rows.append(("podium", d0, z0, d1, z1))
    seats = []

    def flight(name, d, z, count, tread, rise):
        for i in range(count):
            rows.append((name, d + i * tread, z + i * rise, d + i * tread, z + (i + 1) * rise))
            rows.append((name, d + i * tread, z + (i + 1) * rise, d + (i + 1) * tread, z + (i + 1) * rise))
            seats.append((name, d + i * tread, z + (i + 1) * rise, rise, i))
        return d + count * tread, z + count * rise
    rows.append(("balteus", 5.6, 4.2, 5.6, 6.0))
    d, z = flight("primum", 5.6, 6.0, 15, 0.8, 0.42)
    rows.append(("walk", d, z, d + 1.2, z))
    rows.append(("balteus", d + 1.2, z, d + 1.2, z + 2.1))
    d, z = flight("imum", d + 1.2, z + 2.1, 15, 0.8, 0.46)
    rows.append(("walk", d, z, d + 1.2, z))
    rows.append(("balteus", d + 1.2, z, d + 1.2, z + 2.1))
    d, z = flight("summum", d + 1.2, z + 2.1, 14, 0.8, 0.55)
    rows.append(("balteus", d, z, d, 34.4))
    rows.append(("walk", d, 34.4, 44.4, 34.4))
    d, z = flight("ligneis", 44.4, 34.4, 7, 0.62, 0.78)
    rows.append(("walk", d, z, OUTER - 1.6, z))
    rows.append(("attic_inner", OUTER - 1.6, z, OUTER - 1.6, FACADE_TOP))
    PROFILE.extend([rows, seats])
    return PROFILE


ZONE = {"podium_wall": (MARBLE, (0.93, 0.9, 0.86)), "parapet": (MARBLE, (0.97, 0.95, 0.9)),
        "parapet_top": (MARBLE, (0.97, 0.95, 0.9)), "parapet_back": (MARBLE, (0.9, 0.88, 0.84)),
        "podium": (MARBLE, (0.95, 0.93, 0.88)), "balteus": (MARBLE, (0.9, 0.87, 0.82)),
        "primum": (MARBLE, (0.92, 0.9, 0.85)), "imum": (MARBLE, (0.86, 0.84, 0.79)), "walk": (TRAV, (0.9, 0.88, 0.84)),
        "summum": (TRAV, (0.92, 0.9, 0.86)), "ligneis": (MATTE, (0.48, 0.36, 0.24)),
        "attic_inner": (TRAV, (0.86, 0.83, 0.78))}


def cavea(bay_angles, samples=240):
    rows, _ = cavea_profile()
    angles, _ = even_angles(samples, 25.0)
    builder = MeshBuilder()
    for name, d0, z0, d1, z1 in rows:
        material, colour = ZONE[name]
        riser = abs(d1 - d0) < 1e-6
        outward = name in ("parapet_back",)
        for k in range(samples):
            ta, tb = angles[k], angles[(k + 1) % samples]
            quad = [oval(ta, d0, z0), oval(tb, d0, z0), oval(tb, d1, z1), oval(ta, d1, z1)]
            if riser:
                facing = normal((ta + tb) / 2) * (1.0 if outward else -1.0)
            else:
                facing = Vector((0.0, 0.0, 1.0))
            first = len(builder.polygons)
            builder.oriented(quad, facing, material)
            builder.tint(first, colour)
    for name, d0, z0, d1, z1 in rows:
        if name != "balteus" or z0 < 6.5:
            continue
        top = min(z1, z0 + 1.75)
        for t in bay_angles:
            n = normal(t)
            side = tangent(t) * 0.55
            centre = oval(t, d0, 0.0) - n * 0.03
            quad = [centre - side + Vector((0, 0, z0)), centre + side + Vector((0, 0, z0)),
                    centre + side + Vector((0, 0, top)), centre - side + Vector((0, 0, top))]
            builder.oriented(quad, -n, VOID)
    return builder


def portico_frames(spacing=4.4):
    angles, total = even_angles(int(even_angles(8, 44.4)[1] / spacing), 44.4)
    return [frame(t, 44.4, 34.4) for t in angles]


def portico_roof(samples=160):
    builder = MeshBuilder()
    angles, _ = even_angles(samples, 44.4)
    for k in range(samples):
        ta, tb = angles[k], angles[(k + 1) % samples]
        quad = [oval(ta, 43.9, 45.4), oval(tb, 43.9, 45.4), oval(tb, OUTER - 1.6, 46.8), oval(ta, OUTER - 1.6, 46.8)]
        builder.oriented(quad, (0, 0, 1), "terracotta_tiles")
        builder.oriented(list(reversed(quad)), (0, 0, -1), MATTE)
        builder.tint(len(builder.polygons) - 1, (0.42, 0.33, 0.24))
        front = [oval(ta, 43.9, 44.6), oval(tb, 43.9, 44.6), oval(tb, 43.9, 45.4), oval(ta, 43.9, 45.4)]
        builder.oriented(front, -normal((ta + tb) / 2), TRAV)
    return builder


def arena_floor(rings=12, samples=120, seed=3):
    builder = MeshBuilder()
    rng = random.Random(seed)
    previous = None
    for ring in range(1, rings + 1):
        scale = ring / rings
        points = [Vector((A * scale * math.cos(2 * math.pi * k / samples), B * scale * math.sin(2 * math.pi * k / samples),
                          0.02)) for k in range(samples)]
        indices = [builder.point(p) for p in points]
        if previous is None:
            centre = builder.point((0.0, 0.0, 0.02))
            for k in range(samples):
                builder.face([centre, indices[k], indices[(k + 1) % samples]], SAND)
                builder.tint(len(builder.polygons) - 1, (0.97, 0.96, 0.94))
        else:
            for k in range(samples):
                j = (k + 1) % samples
                first = len(builder.polygons)
                builder.face([previous[k], indices[k], indices[j], previous[j]], SAND)
                builder.tint(first, (0.97, 0.96, 0.94))
        previous = indices
    return builder


def trapdoors():
    builder = MeshBuilder()
    spots = []
    for row in (-12.5, -6.5, 6.5, 12.5):
        for x in np.arange(-30.0, 30.1, 7.5):
            if (x / (A - 6)) ** 2 + (row / (B - 4)) ** 2 < 1.0:
                spots.append((float(x), row))
    for index, (x, y) in enumerate(spots):
        if index == 9:
            builder.box((x - 0.7, y - 1.3, -0.02), (x + 0.7, y + 1.3, 0.03), VOID, bottom=False)
            painted(builder, WOOD, lambda x=x, y=y: builder.box((x - 0.75, y + 1.3, 0.0), (x + 0.75, y + 1.42, 2.6),
                                                                 MATTE))
            painted(builder, WOOD, lambda x=x, y=y: builder.box((x - 0.8, y - 1.35, 0.0), (x + 0.8, y + 1.35, 0.06),
                                                                 MATTE, bottom=False, top=False))
            continue
        painted(builder, (0.95, 0.92, 0.88), lambda x=x, y=y: builder.box((x - 0.75, y - 1.35, 0.02), (x + 0.75, y + 1.35,
                                                                                                      0.045), SAND,
                                                                          bottom=False))
        for edge in (-1.35, 1.35):
            painted(builder, (0.62, 0.55, 0.46), lambda x=x, y=y, edge=edge: builder.box(
                (x - 0.78, y + edge - 0.04, 0.02), (x + 0.78, y + edge + 0.04, 0.05), SAND, bottom=False))
    return builder, spots


def podium_doors(count=12):
    builder = MeshBuilder()
    angles, _ = even_angles(count, 0.0, 0.5)
    for t in angles:
        n = normal(t)
        side = tangent(t) * 0.8
        centre = oval(t, -0.03, 0.0)
        builder.oriented([centre - side, centre + side, centre + side + Vector((0, 0, 2.3)),
                          centre - side + Vector((0, 0, 2.3))], -n, VOID)
        frame_side = tangent(t) * 1.0
        painted(builder, (0.9, 0.86, 0.8), lambda centre=centre, frame_side=frame_side, n=n: builder.oriented(
            [centre - frame_side - n * 0.02 + Vector((0, 0, 2.3)), centre + frame_side - n * 0.02 + Vector((0, 0, 2.3)),
             centre + frame_side - n * 0.02 + Vector((0, 0, 2.6)), centre - frame_side - n * 0.02 + Vector((0, 0, 2.6))],
            -n, MARBLE))
    for k, (low, high, colour) in enumerate(((0.0, 0.5, (0.62, 0.5, 0.42)), (3.0, 3.25, (0.86, 0.74, 0.5)))):
        ring, _ = even_angles(160, 0.0)
        for j in range(160):
            ta, tb = ring[j], ring[(j + 1) % 160]
            quad = [oval(ta, -0.01, low), oval(tb, -0.01, low), oval(tb, -0.01, high), oval(ta, -0.01, high)]
            painted(builder, colour, lambda quad=quad, ta=ta, tb=tb: builder.oriented(quad, -normal((ta + tb) / 2),
                                                                                      MARBLE))
    return builder


def pulvinar(w=10.0):
    builder = MeshBuilder()
    hw = w / 2
    builder.box((-hw, -0.6, 0.0), (hw, 5.8, 4.4), MARBLE, bottom=False)
    for x in (-hw + 0.4, hw - 0.4):
        for y in (-0.2, 5.2):
            builder.merge(column("corinthian", 0.5, 4.6, detail="low", material=MARBLE), placement(x, y, 4.4))
    builder.box((-hw - 0.2, -0.6, 9.0), (hw + 0.2, 5.9, 9.6), MARBLE)
    painted(builder, (0.45, 0.13, 0.2), lambda: builder.box((-hw + 0.1, -0.5, 9.6), (hw - 0.1, 5.8, 9.75), MATTE,
                                                            bottom=False))
    painted(builder, (0.45, 0.13, 0.2), lambda: builder.box((-hw + 0.3, -0.62, 4.4), (hw - 0.3, -0.58, 5.2), MATTE,
                                                            bottom=False))
    painted(builder, (0.82, 0.66, 0.36), lambda: builder.box((-0.6, 1.8, 4.4), (0.6, 2.8, 5.4), MATTE))
    return builder


def velarium(angles, frames):
    builder = MeshBuilder()
    tops = [f @ Vector((0.0, 0.45, MAST_TOP)) for f in frames]
    inner = [oval(t, RING_D, RING_Z) for t in angles]
    count = len(angles)
    rng = random.Random(11)
    for k in range(count):
        tube(builder, [tops[k], tops[k].lerp(inner[k], 0.5) - Vector((0, 0, 0.6)), inner[k]], [0.05, 0.05, 0.05],
             (0.55, 0.47, 0.36), 3)
    tube(builder, inner + [inner[0]], [0.12] * (count + 1), (0.5, 0.42, 0.32), 4, cap=False)
    stripes = [(0.95, 0.91, 0.82), (0.93, 0.88, 0.76), (0.86, 0.66, 0.36), (0.95, 0.91, 0.82), (0.72, 0.3, 0.22)]
    for k in range(count):
        j = (k + 1) % count
        if k % 16 == 5:
            continue
        rows = []
        for v in np.linspace(0.07, 0.74, 5):
            row = []
            for u in np.linspace(0.04, 0.96, 4):
                a = tops[k].lerp(inner[k], v)
                b = tops[j].lerp(inner[j], v)
                point = a.lerp(b, u) - Vector((0.0, 0.0, 0.55 * math.sin(math.pi * u) + 0.9 * math.sin(math.pi * v)))
                row.append(point)
            rows.append(row)
        first = len(builder.polygons)
        builder.surface(rows, LINEN, smooth=True, facing=(0, 0, -1))
        colour = stripes[k % len(stripes)]
        shade = rng.uniform(0.95, 1.02)
        builder.tint(first, tuple(min(1.0, c * shade) for c in colour))
    return builder


def seat_rows():
    _, seats = cavea_profile()
    return seats


def crowd_block(w, kappa, seed, near=None, near_radius=0.0, frame_matrix=None, pool=None):
    rng = random.Random(seed)
    builder = MeshBuilder()
    detailed = []
    for name, d, z, rise, row in seat_rows():
        depth = d - OUTER
        width = w * local_ratio(depth + 0.3, kappa)
        count = int(width / 0.52)
        fill = {"primum": 0.88, "imum": 0.9, "summum": 0.86, "ligneis": 0.8}[name]
        for i in range(count):
            x = -width / 2 + width * (i + 0.5 + rng.uniform(-0.15, 0.15)) / count
            if abs(x) > width / 2 - 0.5 or rng.random() > fill:
                continue
            if name in ("imum", "summum", "ligneis") and row < 3 and abs(x) < 0.95:
                continue
            y = depth + 0.24
            if near is not None:
                world = frame_matrix @ Vector((x, y, z))
                if (world - near).length < near_radius:
                    detailed.append((x, y, z))
                    continue
            spectator_card(builder, x, y, z, rise, name, rng)
    if pool is not None:
        for x, y, z in detailed:
            builder.merge(pool[rng.randrange(len(pool))], placement(x, y + 0.05, z - 0.02, math.pi + rng.uniform(-0.25, 0.25)))
    return builder


def spectator_card(builder, x, y, z, rise, zone, rng):
    if zone == "primum":
        body = TOGA if rng.random() < 0.72 else COLOURS["plebs"][rng.randrange(8)]
    elif zone == "imum":
        body = TOGA if rng.random() < 0.55 else COLOURS["plebs"][rng.randrange(8)]
    elif zone == "summum":
        body = COLOURS["plebs"][rng.randrange(8)]
    else:
        body = COLOURS["women"][rng.randrange(8)]
    shade = rng.uniform(0.86, 1.06)
    body = tuple(min(1.0, c * shade) for c in body)
    skin = SKINS[rng.randrange(3)]
    lean = 0.42
    scale = rng.uniform(0.92, 1.06)
    half = 0.2 * scale
    foot = Vector((x, y - 0.18, z - rise + 0.05))
    shoulder = Vector((x, y + 0.08 + lean * 0.4, z + 0.62 * scale))
    side = Vector((half, 0.0, 0.0))
    first = len(builder.polygons)
    builder.oriented([foot - side * 1.05, foot + side * 1.05, shoulder + side, shoulder - side], (0, -1, 0.4), MATTE)
    builder.tint(first, body)
    crown = shoulder + Vector((0.0, 0.05, 0.27 * scale))
    head = Vector((0.085 * scale, 0.0, 0.0))
    first = len(builder.polygons)
    builder.oriented([shoulder - head + Vector((0, -0.01, 0.02)), shoulder + head + Vector((0, -0.01, 0.02)),
                      crown + head * 0.9, crown - head * 0.9], (0, -1, 0.3), MATTE)
    cover = HAIRS[rng.randrange(3)] if zone != "ligneis" or rng.random() < 0.5 else body
    builder.polygon_colors[first] = skin
    top = len(builder.polygons)
    builder.oriented([crown - head * 0.9, crown + head * 0.9, crown + head * 0.7 + Vector((0, 0.1, 0.01)),
                      crown - head * 0.7 + Vector((0, 0.1, 0.01))], (0, 0, 1), MATTE)
    builder.tint(top, cover)


def near_pool(seed=5):
    return [spectator(seed * 1000 + index, True) for index in range(24)]


def ground_ring(samples=200):
    builder = MeshBuilder()
    angles, _ = even_angles(samples, 60.0)
    for k in range(samples):
        ta, tb = angles[k], angles[(k + 1) % samples]
        quad = [oval(ta, OUTER + 1.5, 0.0), oval(tb, OUTER + 1.5, 0.0), oval(tb, OUTER + 17.5, 0.0),
                oval(ta, OUTER + 17.5, 0.0)]
        builder.oriented(quad, (0, 0, 1), TRAV)
        edge = [oval(ta, OUTER + 17.5, 0.0), oval(tb, OUTER + 17.5, 0.0), oval(tb, OUTER + 17.5, -1.2),
                oval(ta, OUTER + 17.5, -1.2)]
        builder.oriented(edge, normal((ta + tb) / 2), TRAV)
    return builder


def cippus():
    builder = MeshBuilder()
    builder.box((-0.32, -0.32, -0.4), (0.32, 0.32, 1.3), TRAV, bottom=False, top=False)
    builder.lathe([(0.32, 1.3), (0.3, 1.45), (0.2, 1.6), (0.0, 1.66)], 8, TRAV)
    return builder


def cippi_frames():
    angles, _ = even_angles(BAYS // 2, OUTER + 17.0)
    return [frame(t, OUTER + 17.0, 0.0) for t in angles]
