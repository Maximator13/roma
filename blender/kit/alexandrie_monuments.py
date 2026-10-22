import math
import random

from mathutils import Matrix, Vector

from . import colisee_monuments as cmon
from .alexandrie_pharos import arcade, painted
from .geometry import MATTE, MeshBuilder
from .nimes_figures import drape, ellipsoid, tube
from .orders import gable_roof

STONE = "limestone"
MARBLE = "marble"
PLASTER = "plaster"
PAVING = "paving"
TILES = "terracotta_tiles"
GRANITE = "granite"
GLYPHS = "granite_glyphs"
GILT = "bronze_gilt"
VOID = "shadow_void"
TAU = 2 * math.pi
UNIT = cmon.UNIT
WARM = (0.98, 0.93, 0.84)
CREAM = (1.0, 0.95, 0.86)
OCHRES = [(1.0, 0.86, 0.62), (0.98, 0.78, 0.56), (1.0, 0.93, 0.80), (0.95, 0.70, 0.52), (1.0, 0.97, 0.92),
          (0.92, 0.80, 0.66)]
RED = (0.72, 0.20, 0.13)
BLUE = (0.20, 0.36, 0.62)
WOOD = (0.46, 0.33, 0.22)
CLOTHS = [(0.78, 0.18, 0.12), (0.92, 0.70, 0.22), (0.20, 0.38, 0.66), (0.95, 0.92, 0.84), (0.70, 0.30, 0.46),
          (0.30, 0.55, 0.40)]
QUAY_WALL = [(-0.45, -4.5), (-0.45, 1.25), (-0.62, 1.3), (-0.62, 1.68), (0.7, 1.68), (0.7, 1.2)]


def column_frame(x, y, z, diameter, height):
    return cmon.column_frame(x, y, z, diameter, height)


def unit_column(order="ionic"):
    return cmon.unit_column(order, "low", MARBLE)


def simple_column():
    return cmon.simple_column(MARBLE)


def oriented_ring(points, land_inside):
    area = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        area += x0 * y1 - x1 * y0
    counter_clockwise = area > 0
    ring = list(points)
    if counter_clockwise == land_inside:
        ring.reverse()
    return ring + ring[:1]


def quay(path, height=0.0):
    builder = MeshBuilder()
    points = [Vector((p[0], p[1], height)) for p in path]
    painted(builder, WARM, lambda: builder.sweep(points, QUAY_WALL, STONE, caps=True))
    return builder


def apron(path, width, top=1.665):
    builder = MeshBuilder()
    points = [Vector((p[0], p[1])) for p in path]
    first = len(builder.polygons)
    last = len(points) - 2
    for k, (a, b) in enumerate(zip(points[:-1], points[1:])):
        direction = b - a
        if direction.length < 0.5:
            continue
        direction.normalize()
        right = Vector((direction.y, -direction.x))
        z = top + 0.004 * (k % 9)
        reach = width * 0.4
        start = 0.0 if k == 0 else 1.0
        end = 0.0 if k == last else 1.0
        near_a = a + right * 0.6 - direction * 0.4 * start
        near_b = b + right * 0.6 + direction * 0.4 * end
        far_a = a + right * width - direction * reach * start
        far_b = b + right * width + direction * reach * end
        quad = [(near_a.x, near_a.y, z), (near_b.x, near_b.y, z), (far_b.x, far_b.y, z), (far_a.x, far_a.y, z)]
        builder.oriented(quad, (0, 0, 1), PAVING)
    builder.tint(first, (1.0, 0.97, 0.9))
    return builder


def bollard():
    builder = MeshBuilder()
    painted(builder, (0.9, 0.86, 0.78), lambda: builder.lathe([(0.0, 0.0), (0.24, 0.0), (0.2, 0.45), (0.27, 0.6),
                                                               (0.24, 0.72), (0.0, 0.74)], 8, STONE, smooth=True))
    return builder


def causeway(builder, y0, y1, z0, z1, width, foot=-5.0):
    hw = width / 2
    corners = [(-hw, y0, foot), (hw, y0, foot), (hw, y1, foot), (-hw, y1, foot),
               (-hw, y0, z0 - 0.4), (hw, y0, z0 - 0.4), (hw, y1, z1 - 0.4), (-hw, y1, z1 - 0.4)]
    indices = builder.points(corners)
    first = len(builder.polygons)
    for quad in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        builder.face([indices[q] for q in quad], STONE)
    builder.tint(first, WARM)
    first = len(builder.polygons)
    for side in (-1, 1):
        x = side * hw
        builder.oriented([(x, y0, z0 - 0.45), (x, y1, z1 - 0.45), (x + side * 0.35, y1, z1 - 0.35),
                          (x + side * 0.35, y0, z0 - 0.35)], (side, 0, -1), STONE)
        builder.oriented([(x + side * 0.35, y0, z0 - 0.35), (x + side * 0.35, y1, z1 - 0.35),
                          (x + side * 0.35, y1, z1), (x + side * 0.35, y0, z0)], (side, 0, 0), STONE)
    builder.tint(first, CREAM)
    first = len(builder.polygons)
    builder.oriented([(-hw - 0.35, y0, z0), (hw + 0.35, y0, z0), (hw + 0.35, y1, z1), (-hw - 0.35, y1, z1)],
                     (0, 0, 1), PAVING)
    builder.tint(first, (1.0, 0.96, 0.88))
    first = len(builder.polygons)
    x = -hw + 0.3
    builder.sweep([Vector((x, y0, z0)), Vector((x, y1, z1))], [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.85), (-0.3, 0.85)],
                  STONE, caps=True)
    builder.tint(first, WARM)


def heptastadion_pieces(length, bridges, gap=30.0, ramp=24.0, top=2.4, bridge_top=5.6):
    pieces = []
    y = -30.0
    for fraction in bridges:
        centre = length * fraction
        a = centre - gap / 2
        pieces.append(("flat", y, a - ramp, top, top))
        pieces.append(("ramp", a - ramp, a, top, bridge_top))
        pieces.append(("bridge", a, a + gap, bridge_top, bridge_top))
        pieces.append(("ramp", a + gap, a + gap + ramp, bridge_top, top))
        y = a + gap + ramp
    pieces.append(("flat", y, length + 30.0, top, top))
    return pieces


def heptastadion(length, width, bridges):
    builder = MeshBuilder()
    for kind, y0, y1, z0, z1 in heptastadion_pieces(length, bridges):
        if kind == "bridge":
            arcade(builder, Vector((0.0, y0, 0.0)), Vector((0.0, y1, 0.0)), width + 0.7, z0, z1, 2, STONE, WARM,
                   foot=-5.0, parapet_height=0.0)
            first = len(builder.polygons)
            x = -width / 2
            builder.sweep([Vector((x, y0, z0)), Vector((x, y1, z1))],
                          [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.95), (-0.3, 0.95)], STONE, caps=True)
            builder.tint(first, WARM)
            for yy in (y0 - 4.0, y1 + 4.0):
                first = len(builder.polygons)
                builder.box((-width / 2 - 3.2, yy - 3.2, -5.0), (-width / 2 + 3.2, yy + 3.2, 13.5), STONE,
                            bottom=False)
                builder.box((-width / 2 - 3.6, yy - 3.6, 13.5), (-width / 2 + 3.6, yy + 3.6, 14.3), STONE,
                            bottom=False)
                builder.box((-width / 2 - 3.3, yy - 3.3, 14.3), (-width / 2 + 3.3, yy + 3.3, 14.6), STONE, bottom=False)
                builder.tint(first, CREAM)
                pyramid = [(-width / 2 - 3.5, yy - 3.5, 14.6), (-width / 2 + 3.5, yy - 3.5, 14.6),
                           (-width / 2 + 3.5, yy + 3.5, 14.6), (-width / 2 - 3.5, yy + 3.5, 14.6)]
                apex = (-width / 2, yy, 16.4)
                for k in range(4):
                    builder.face(builder.points([pyramid[k], pyramid[(k + 1) % 4], apex]), TILES)
                for z in (6.0, 10.0):
                    for side in (-1, 1):
                        builder.oriented([(-width / 2 + side * 3.22, yy - 0.4, z), (-width / 2 + side * 3.22, yy + 0.4, z),
                                          (-width / 2 + side * 3.22, yy + 0.4, z + 1.3),
                                          (-width / 2 + side * 3.22, yy - 0.4, z + 1.3)], (side, 0, 0), VOID)
        else:
            causeway(builder, y0, y1, z0, z1, width)
    return builder


def aqueduct_runs(length, bridges, top=2.4, gap=30.0, ramp=24.0):
    runs = []
    for kind, y0, y1, z0, z1 in heptastadion_pieces(length, bridges, gap, ramp, top):
        runs.append((y0, y1, max(z0, z1) if kind != "flat" else z0, kind))
    return runs


def aqueduct(length, height, foot, spans):
    builder = MeshBuilder()
    arcade(builder, Vector((0.0, 0.0, 0.0)), Vector((0.0, length, 0.0)), 1.5, height, height, spans, STONE,
           (0.96, 0.9, 0.8), foot=foot, parapet_height=0.55)
    return builder


def warehouse(length=60.0, depth=16.0, height=8.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hl, hd = length / 2, depth / 2
    wall = OCHRES[rng.randrange(len(OCHRES))]
    painted(builder, wall, lambda: builder.box((-hl, -hd, -1.0), (hl, hd, height), PLASTER, bottom=False, top=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-hl - 0.15, -hd - 0.15, -0.6), (hl + 0.15, hd + 0.15, 0.5),
                                                             STONE, bottom=False, top=False))
    rise = hd * 0.42
    gable_roof(builder, -hl - 0.4, hl + 0.4, hd + 0.6, height, height + rise, TILES, along_axis="x", imbrex=False)
    for x, facing in ((-hl, -1), (hl, 1)):
        tri = [(x, -hd, height), (x, hd, height), (x, 0.0, height + rise)]
        painted(builder, wall, lambda tri=tri, facing=facing: builder.oriented(tri, (facing, 0, 0), PLASTER))
    doors = max(int(length / 10.0), 2)
    for k in range(doors):
        x = -hl + length * (k + 0.5) / doors
        builder.oriented([(x - 1.6, -hd - 0.03, 0.0), (x + 1.6, -hd - 0.03, 0.0), (x + 1.6, -hd - 0.03, 3.6),
                          (x - 1.6, -hd - 0.03, 3.6)], (0, -1, 0), VOID)
        painted(builder, (0.96, 0.92, 0.84), lambda x=x: builder.box((x - 2.0, -hd - 0.2, 3.6), (x + 2.0, -hd, 4.0),
                                                                     STONE, bottom=True))
        builder.oriented([(x - 1.2, hd + 0.03, 0.0), (x + 1.2, hd + 0.03, 0.0), (x + 1.2, hd + 0.03, 3.0),
                          (x - 1.2, hd + 0.03, 3.0)], (0, 1, 0), VOID)
        for side in (-1, 1):
            px = x + side * length / doors / 2
            painted(builder, tuple(min(1.0, c * 1.05) for c in wall), lambda px=px: builder.box(
                (px - 0.4, -hd - 0.25, 0.0), (px + 0.4, -hd, height - 0.4), PLASTER, bottom=False))
            painted(builder, tuple(min(1.0, c * 1.05) for c in wall), lambda px=px: builder.box(
                (px - 0.4, hd, 0.0), (px + 0.4, hd + 0.25, height - 0.4), PLASTER, bottom=False))
        for z in (5.6,):
            builder.oriented([(x - 0.5, -hd - 0.03, z), (x + 0.5, -hd - 0.03, z), (x + 0.5, -hd - 0.03, z + 0.9),
                              (x - 0.5, -hd - 0.03, z + 0.9)], (0, -1, 0), VOID)
            builder.oriented([(x - 0.5, hd + 0.03, z), (x + 0.5, hd + 0.03, z), (x + 0.5, hd + 0.03, z + 0.9),
                              (x - 0.5, hd + 0.03, z + 0.9)], (0, 1, 0), VOID)
        if rng.random() < 0.6:
            cloth = CLOTHS[rng.randrange(len(CLOTHS))]
            awning = [(x - 2.4, -hd, 4.4), (x + 2.4, -hd, 4.4), (x + 2.4, -hd - 3.0, 3.6), (x - 2.4, -hd - 3.0, 3.6)]
            painted(builder, cloth, lambda awning=awning: builder.oriented(awning, (0, -0.3, 1), MATTE))
            painted(builder, tuple(c * 0.7 for c in cloth), lambda awning=awning: builder.oriented(
                list(reversed(awning)), (0, 0.3, -1), MATTE))
            for px in (x - 2.3, x + 2.3):
                tube(builder, [(px, -hd - 2.95, 0.0), (px, -hd - 2.95, 3.6)], [0.05, 0.05], WOOD, 4)
    return builder


def ship_shed(width=8.0, length=44.0, height=7.0, seed=0):
    builder = MeshBuilder()
    hw = width / 2
    painted(builder, WARM, lambda: builder.box((-hw - 0.5, -length / 2, -4.5), (-hw, length / 2, height), STONE,
                                              bottom=False))
    for k in range(5):
        y = -length / 2 + length * k / 4
        painted(builder, WARM, lambda y=y: builder.box((hw - 0.45, y - 0.45, -4.5), (hw + 0.45, y + 0.45, height),
                                                      STONE, bottom=False))
    rise = 2.6
    gable_roof(builder, -length / 2, length / 2 + 0.6, hw + 0.6, height, height + rise, TILES, along_axis="y",
               imbrex=False)
    painted(builder, WARM, lambda: builder.oriented([(-hw, -length / 2, height), (hw, -length / 2, height),
                                                    (0.0, -length / 2, height + rise)], (0, -1, 0), STONE))
    painted(builder, (0.5, 0.4, 0.3), lambda: builder.oriented([(-hw + 0.3, -length / 2, 1.6), (hw - 0.3, -length / 2, 1.6),
                                                               (hw - 0.3, length / 2 + 8.0, -1.4),
                                                               (-hw + 0.3, length / 2 + 8.0, -1.4)], (0, 0, 1), MATTE))
    for k in range(11):
        y = -length / 2 + 2.0 + k * 5.0
        z = 1.6 - 3.0 * (y + length / 2) / (length + 8.0)
        tube(builder, [(-hw + 0.5, y, z + 0.05), (hw - 0.5, y, z + 0.05)], [0.09, 0.09], (0.4, 0.3, 0.2), 4)
    return builder


def temenos(length, width, height=7.5, depth=7.0, spacing=4.0, gate=0.0, outer=OCHRES[2]):
    builder = MeshBuilder()
    frames = []
    hl, hw = length / 2, width / 2
    sides = (((-hl, hw), (hl, hw), (0, -1)), ((hl, -hw), (-hl, -hw), (0, 1)), ((hl, hw), (hl, -hw), (-1, 0)),
             ((-hl, -hw), (-hl, hw), (1, 0)))
    for index, ((x0, y0), (x1, y1), (nx, ny)) in enumerate(sides):
        span = math.hypot(x1 - x0, y1 - y0)
        count = int(span / spacing)
        for k in range(1, count):
            t = k / count
            x = x0 + (x1 - x0) * t + nx * depth
            y = y0 + (y1 - y0) * t + ny * depth
            if index == 0 and gate > 0 and abs(x) < gate / 2 + 1.0:
                continue
            frames.append(column_frame(x, y, 0.4, 0.62, height))
    for x0, y0, x1, y1 in ((-hl, hw - depth - 0.7, hl, hw), (-hl, -hw, hl, -hw + depth + 0.7),
                           (hl - depth - 0.7, -hw, hl, hw), (-hl, -hw, -hl + depth + 0.7, hw)):
        painted(builder, WARM, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, height + 0.4),
                                                                              (x1, y1, height + 1.3), MARBLE))
        painted(builder, (1.0, 0.98, 0.94), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, -0.6),
                                                                                          (x1, y1, 0.4), MARBLE,
                                                                                          bottom=False))
    rise = 1.8
    for x0, x1, y_inner, y_outer in ((-hl, hl, hw - depth - 0.7, hw), (-hl, hl, -hw + depth + 0.7, -hw)):
        builder.surface([[(x0, y_inner, height + 1.3), (x1, y_inner, height + 1.3)],
                         [(x0, y_outer, height + 1.3 + rise), (x1, y_outer, height + 1.3 + rise)]], TILES,
                        facing=(0, 0, 1))
    for y0, y1, x_inner, x_outer in ((-hw, hw, hl - depth - 0.7, hl), (-hw, hw, -hl + depth + 0.7, -hl)):
        builder.surface([[(x_inner, y0, height + 1.3), (x_inner, y1, height + 1.3)],
                         [(x_outer, y0, height + 1.3 + rise), (x_outer, y1, height + 1.3 + rise)]], TILES,
                        facing=(0, 0, 1))
    top = height + 1.3 + rise
    walls = [(-hl, hw - 0.7, hl, hw), (-hl, -hw, hl, -hw + 0.7), (hl - 0.7, -hw, hl, hw), (-hl, -hw, -hl + 0.7, hw)]
    for index, (x0, y0, x1, y1) in enumerate(walls):
        if index == 0 and gate > 0:
            for a, b in ((x0, -gate / 2), (gate / 2, x1)):
                painted(builder, outer, lambda a=a, b=b: builder.box((a, y0, -0.6), (b, y1, top), PLASTER,
                                                                     bottom=False))
            builder.oriented([(-gate / 2, y0 - 0.01, 0.4), (gate / 2, y0 - 0.01, 0.4), (gate / 2, y0 - 0.01, height),
                              (-gate / 2, y0 - 0.01, height)], (0, -1, 0), VOID)
            continue
        painted(builder, outer, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, -0.6), (x1, y1, top), PLASTER,
                                                                              bottom=False))
    painted(builder, RED, lambda: builder.box((-hl - 0.03, -hw - 0.03, top - 1.0), (hl + 0.03, hw + 0.03, top - 0.7),
                                              MATTE, bottom=False, top=False))
    pilaster = tuple(min(1.0, c * 1.04) for c in outer)
    for (x0, y0), (x1, y1), (nx, ny) in (((-hl, hw), (hl, hw), (0, 1)), ((-hl, -hw), (hl, -hw), (0, -1)),
                                         ((hl, -hw), (hl, hw), (1, 0)), ((-hl, -hw), (-hl, hw), (-1, 0))):
        span = math.hypot(x1 - x0, y1 - y0)
        count = int(span / 6.0)
        for k in range(1, count):
            t = k / count
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if ny > 0 and gate > 0 and abs(x) < gate / 2 + 1.5:
                continue
            ax, ay = abs(ny) * 0.45 + abs(nx) * 0.3, abs(nx) * 0.45 + abs(ny) * 0.3
            cx, cy = x + nx * 0.3, y + ny * 0.3
            painted(builder, pilaster, lambda cx=cx, cy=cy, ax=ax, ay=ay: builder.box(
                (cx - ax, cy - ay, 0.0), (cx + ax, cy + ay, top - 1.1), PLASTER, bottom=False))
            if k % 2 == 1:
                along = Vector((abs(ny), abs(nx), 0.0))
                centre = Vector((x + nx * 0.02, y + ny * 0.02, 0.0)) + along * 3.0
                corners = [centre - along * 0.7 + Vector((0, 0, top - 4.2)), centre + along * 0.7 + Vector((0, 0, top - 4.2)),
                           centre + along * 0.7 + Vector((0, 0, top - 2.4)), centre - along * 0.7 + Vector((0, 0, top - 2.4))]
                painted(builder, (0.20, 0.15, 0.10), lambda corners=corners, nx=nx, ny=ny: builder.oriented(
                    corners, (nx, ny, 0), GILT))
    painted(builder, tuple(c * 0.86 for c in outer), lambda: builder.box((-hl - 0.35, -hw - 0.35, -0.6),
                                                                        (hl + 0.35, hw + 0.35, 1.0), PLASTER,
                                                                        bottom=False, top=False))
    return builder, frames


def propylon(width=16.0, depth=8.0, height=9.0, columns=4):
    builder = MeshBuilder()
    frames = []
    hw = width / 2
    painted(builder, WARM, lambda: builder.box((-hw - 1.0, -depth / 2 - 1.5, -0.6), (hw + 1.0, depth / 2 + 1.0, 0.5),
                                              MARBLE, bottom=False))
    for k in range(3):
        builder.box((-hw - 1.0, depth / 2 + 1.0 + k * 0.45, -0.6), (hw + 1.0, depth / 2 + 1.45 + k * 0.45,
                                                                     0.5 - 0.35 * (k + 1)), MARBLE, bottom=False)
    for k in range(columns):
        x = -hw + 1.2 + (width - 2.4) * k / (columns - 1)
        frames.append(column_frame(x, depth / 2, 0.5, 0.95, height))
        frames.append(column_frame(x, -depth / 2, 0.5, 0.95, height))
    eave = 0.5 + height + 1.8
    painted(builder, WARM, lambda: builder.box((-hw - 0.4, -depth / 2 - 0.8, 0.5 + height), (hw + 0.4, depth / 2 + 0.8,
                                                                                            eave), MARBLE))
    painted(builder, BLUE, lambda: builder.box((-hw - 0.42, depth / 2 + 0.79, 0.5 + height + 0.7),
                                               (hw + 0.42, depth / 2 + 0.82, 0.5 + height + 1.2), MATTE, bottom=False,
                                               top=False))
    ridge = eave + (hw + 0.4) * math.tan(math.radians(15))
    gable_roof(builder, -depth / 2 - 0.8, depth / 2 + 0.8, hw + 0.7, eave, ridge, TILES, along_axis="y", imbrex=False)
    cmon.pediment(builder, hw + 0.4, depth / 2 + 0.8, eave, ridge, 1, MARBLE, BLUE)
    cmon.pediment(builder, hw + 0.4, -depth / 2 - 0.8, eave, ridge, -1, MARBLE, BLUE)
    for x, zz in ((0.0, ridge), (-hw - 0.4, eave), (hw + 0.4, eave)):
        builder.box((x - 0.3, depth / 2 + 0.3, zz), (x + 0.3, depth / 2 + 0.9, zz + 1.0), GILT)
    return builder, frames


def crab(scale=1.0):
    builder = MeshBuilder()
    gold = (0.92, 0.80, 0.62)
    ellipsoid(builder, (0.0, 0.0, 0.22), (0.46, 0.36, 0.16), gold, 10, 5, GILT)
    for side in (-1, 1):
        for k in range(4):
            angle = math.radians(-50 + k * 28)
            root = Vector((side * 0.36 * math.cos(angle), 0.3 * math.sin(angle), 0.2))
            knee = root + Vector((side * 0.28 * math.cos(angle), 0.24 * math.sin(angle), 0.12))
            tip = knee + Vector((side * 0.2 * math.cos(angle), 0.18 * math.sin(angle), -0.32))
            tube(builder, [root, knee, tip], [0.05, 0.04, 0.02], gold, 5, GILT)
        arm = [Vector((side * 0.22, 0.3, 0.24)), Vector((side * 0.38, 0.55, 0.32)), Vector((side * 0.26, 0.78, 0.3))]
        tube(builder, arm, [0.06, 0.06, 0.05], gold, 5, GILT)
        ellipsoid(builder, (side * 0.22, 0.86, 0.3), (0.1, 0.16, 0.08), gold, 6, 3, GILT)
    if scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(scale, 4))
        return scaled
    return builder


def obelisk(height=21.0, base=2.45, top=1.62, pyramidion=1.9, seed=0):
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-3.4, -3.4, -0.5), (3.4, 3.4, 0.35), STONE, bottom=False))
    painted(builder, WARM, lambda: builder.box((-2.9, -2.9, 0.35), (2.9, 2.9, 0.75), STONE, bottom=False))
    painted(builder, (0.96, 0.92, 0.86), lambda: builder.box((-2.3, -2.3, 0.75), (2.3, 2.3, 2.6), MARBLE,
                                                             bottom=False))
    painted(builder, (1.0, 0.97, 0.92), lambda: builder.box((-2.5, -2.5, 0.75), (2.5, 2.5, 1.05), MARBLE,
                                                            bottom=False))
    painted(builder, (1.0, 0.97, 0.92), lambda: builder.box((-2.42, -2.42, 2.3), (2.42, 2.42, 2.6), MARBLE,
                                                            bottom=False))
    painted(builder, (1.0, 0.96, 0.9), lambda: builder.box((-2.45, -2.45, 2.6), (2.45, 2.45, 2.85), MARBLE,
                                                           bottom=False))
    lift = 2.85 + 0.42
    for sx in (-1, 1):
        for sy in (-1, 1):
            builder.merge(crab(1.0), Matrix.Translation((sx * (base / 2 - 0.25), sy * (base / 2 - 0.25), 2.85))
                          @ Matrix.Rotation(math.atan2(sy, sx) - math.pi / 2, 4, "Z"))
    shaft_top = lift + height - pyramidion
    half0, half1 = base / 2, top / 2
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        quad = [(a[0] * half0, a[1] * half0, lift), (b[0] * half0, b[1] * half0, lift),
                (b[0] * half1, b[1] * half1, shaft_top), (a[0] * half1, a[1] * half1, shaft_top)]
        uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        first = len(builder.polygons)
        builder.face(builder.points(quad), GLYPHS, uvs=uvs)
        builder.tint(first, (1.0, 0.96, 0.94))
    first = len(builder.polygons)
    builder.face(builder.points([(c[0] * half0, c[1] * half0, lift) for c in reversed(corners)]), GRANITE)
    apex = builder.point((0.0, 0.0, lift + height))
    ring = builder.points([(c[0] * half1, c[1] * half1, shaft_top) for c in corners])
    for k in range(4):
        builder.face([ring[k], ring[(k + 1) % 4], apex], GRANITE)
    builder.tint(first, (1.0, 0.95, 0.92))
    return builder


def theatre(radius=46.0, orchestra=11.0, rows=20, height=14.0):
    builder = MeshBuilder()
    frames = []
    profile = [(orchestra, 0.0), (orchestra, 1.0)]
    step = (radius - orchestra - 2.0) / rows
    rise = (height - 1.0) / rows
    for k in range(rows):
        r = orchestra + 0.8 + k * step
        z = 1.0 + k * rise
        profile += [(r, z), (r, z + rise)]
    profile += [(radius - 1.2, height), (radius, height)]
    painted(builder, (1.0, 0.96, 0.9), lambda: builder.lathe(profile, 28, MARBLE, smooth=False, start=math.pi,
                                                              sweep=math.pi, caps=False))
    painted(builder, OCHRES[0], lambda: builder.lathe([(radius, -0.5), (radius, height + 2.2), (radius - 1.2,
                                                                                               height + 2.2)],
                                                      28, PLASTER, smooth=False, start=math.pi, sweep=math.pi,
                                                      caps=False))
    for k in range(14):
        angle = math.pi + math.pi * (k + 0.5) / 14
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        for z0, z1 in ((0.6, 4.6), (7.2, 10.8)):
            centre = normal * (radius + 0.03)
            builder.oriented([centre + side * -1.3 + Vector((0, 0, z0)), centre + side * 1.3 + Vector((0, 0, z0)),
                              centre + side * 1.3 + Vector((0, 0, z1)), centre + side * -1.3 + Vector((0, 0, z1))],
                             normal, VOID)
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.lathe([(0.0, 0.3), (orchestra, 0.3)], 20, PAVING, start=0.0,
                                                               sweep=TAU, caps=False))
    painted(builder, WARM, lambda: builder.box((-radius + 4.0, 4.0, -0.5), (radius - 4.0, 9.0, 1.5), STONE,
                                              bottom=False))
    painted(builder, OCHRES[3], lambda: builder.box((-radius + 4.0, 9.0, -0.5), (radius - 4.0, 16.0, height + 4.0),
                                                    PLASTER, bottom=False))
    for k in range(10):
        x = -radius + 8.0 + (2 * radius - 16.0) * k / 9
        frames.append(column_frame(x, 8.4, 1.5, 0.7, 6.0))
        frames.append(column_frame(x, 8.4, 8.6, 0.6, 5.0))
    for x in (-12.0, 0.0, 12.0):
        builder.oriented([(x - 1.6, 8.98, 1.5), (x + 1.6, 8.98, 1.5), (x + 1.6, 8.98, 6.0), (x - 1.6, 8.98, 6.0)],
                         (0, -1, 0), VOID)
    painted(builder, WARM, lambda: builder.box((-radius + 4.0, 7.6, 7.6), (radius - 4.0, 9.0, 8.6), MARBLE))
    painted(builder, WARM, lambda: builder.box((-radius + 4.0, 7.6, 13.6), (radius - 4.0, 9.0, 14.4), MARBLE))
    gable_roof(builder, -radius + 3.6, radius - 3.6, 4.2, height + 4.0, height + 6.0, TILES, along_axis="x",
               imbrex=False, pitch=0.4)
    return builder, frames


def villa(width=26.0, depth=16.0, height=8.5, seed=0, porch=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    frames = []
    hw, hd = width / 2, depth / 2
    wall = OCHRES[rng.randrange(len(OCHRES))]
    painted(builder, wall, lambda: builder.box((-hw, -hd, -1.5), (hw, hd, height), PLASTER, bottom=False, top=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-hw - 0.2, -hd - 0.2, height - 0.6),
                                                             (hw + 0.2, hd + 0.2, height), MARBLE, bottom=False))
    painted(builder, RED, lambda: builder.box((-hw - 0.02, -hd - 0.02, -0.5), (hw + 0.02, hd + 0.02, 1.2), PLASTER,
                                              bottom=False, top=False))
    rise = hd * 0.38
    gable_roof(builder, -hw - 0.5, hw + 0.5, hd + 0.7, height, height + rise, TILES, along_axis="x", imbrex=False)
    for x, facing in ((-hw, -1), (hw, 1)):
        tri = [(x, -hd, height), (x, hd, height), (x, 0.0, height + rise)]
        painted(builder, wall, lambda tri=tri, facing=facing: builder.oriented(tri, (facing, 0, 0), PLASTER))
    for k in range(int(width / 4.0)):
        x = -hw + 2.0 + k * 4.0
        for y, n in ((-hd - 0.02, -1), (hd + 0.02, 1)):
            builder.oriented([(x - 0.5, y, 4.8), (x + 0.5, y, 4.8), (x + 0.5, y, 6.4), (x - 0.5, y, 6.4)], (0, n, 0),
                             VOID)
    if porch:
        count = max(int(width / 3.6), 3)
        for k in range(count + 1):
            frames.append(column_frame(-hw + width * k / count, -hd - 4.0, 0.3, 0.5, 4.2))
        painted(builder, WARM, lambda: builder.box((-hw - 0.3, -hd - 4.4, 4.5), (hw + 0.3, -hd, 5.2), MARBLE))
        builder.surface([[(-hw - 0.3, -hd - 4.4, 5.2), (hw + 0.3, -hd - 4.4, 5.2)],
                         [(-hw - 0.3, -hd, 6.2), (hw + 0.3, -hd, 6.2)]], TILES, facing=(0, 0, 1))
        painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((-hw - 0.5, -hd - 4.6, -0.6), (hw + 0.5, -hd, 0.3),
                                                                 MARBLE, bottom=False))
        for x in (-2.0, 2.0):
            builder.oriented([(x - 0.9, -hd - 0.03, 0.3), (x + 0.9, -hd - 0.03, 0.3), (x + 0.9, -hd - 0.03, 3.4),
                              (x - 0.9, -hd - 0.03, 3.4)], (0, -1, 0), VOID)
    return builder, frames


def palace(width=72.0, depth=58.0, seed=0, storeys=2, hall=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    wing = 11.0
    height = 5.2 * storeys + 1.0
    wall = OCHRES[rng.randrange(len(OCHRES))]
    trim = (1.0, 0.98, 0.94)
    rects = [(-hw, -hd, hw, -hd + wing), (-hw, hd - wing, hw, hd), (-hw, -hd + wing, -hw + wing, hd - wing),
             (hw - wing, -hd + wing, hw, hd - wing)]
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((-hw - 1.0, -hd - 1.0, -1.0), (hw + 1.0, hd + 1.0, 0.6),
                                                             PLASTER, bottom=False))
    for x0, y0, x1, y1 in rects:
        painted(builder, wall, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, 0.6), (x1, y1, height), PLASTER,
                                                                              bottom=False, top=False))
        painted(builder, trim, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0 - 0.25, y0 - 0.25, height - 0.7), (x1 + 0.25, y1 + 0.25, height), PLASTER, bottom=False))
        painted(builder, RED, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0 - 0.02, y0 - 0.02, 0.6), (x1 + 0.02, y1 + 0.02, 1.8), PLASTER, bottom=False, top=False))
        if (x1 - x0) > (y1 - y0):
            mid = (y0 + y1) / 2
            local = MeshBuilder()
            gable_roof(local, x0 - 0.4, x1 + 0.4, (y1 - y0) / 2 + 0.6, height, height + (y1 - y0) * 0.2, TILES,
                       along_axis="x", imbrex=False)
            builder.merge(local, Matrix.Translation((0.0, mid, 0.0)))
            for x, facing in ((x0, -1), (x1, 1)):
                tri = [(x, y0, height), (x, y1, height), (x, mid, height + (y1 - y0) * 0.2)]
                painted(builder, wall, lambda tri=tri, facing=facing: builder.oriented(tri, (facing, 0, 0), PLASTER))
        else:
            mid = (x0 + x1) / 2
            local = MeshBuilder()
            gable_roof(local, y0, y1, (x1 - x0) / 2 + 0.6, height, height + (x1 - x0) * 0.2, TILES, along_axis="y",
                       imbrex=False)
            builder.merge(local, Matrix.Translation((mid, 0.0, 0.0)))
    levels = [4.2 + 5.2 * k for k in range(storeys)]
    for side, y in ((-1, -hd - 0.02),):
        for k in range(int(width / 6.0)):
            x = -hw + 3.0 + k * 6.0
            if abs(x) < 12.0:
                continue
            for z in levels:
                builder.oriented([(x - 0.25, y, z), (x + 0.25, y, z), (x + 0.25, y, z + 0.9), (x - 0.25, y, z + 0.9)],
                                 (0, side, 0), VOID)
    for side, x in ((-1, -hw - 0.02), (1, hw + 0.02)):
        for k in range(int(depth / 6.0)):
            y = -hd + 3.0 + k * 6.0
            for z in levels:
                builder.oriented([(x, y - 0.25, z), (x, y + 0.25, z), (x, y + 0.25, z + 0.9), (x, y - 0.25, z + 0.9)],
                                 (side, 0, 0), VOID)
    porch = hd + 4.5
    count = int(width / 3.8)
    for k in range(count + 1):
        x = -hw + 0.6 + (width - 1.2) * k / count
        tube(builder, [(x, porch, 0.6), (x, porch, 1.0)], [0.46, 0.46], trim, 6, PLASTER)
        tube(builder, [(x, porch, 1.0), (x, porch, height - 0.9)], [0.36, 0.3], trim, 7, PLASTER)
    painted(builder, trim, lambda: builder.box((-hw - 0.4, hd, height - 0.9), (hw + 0.4, porch + 0.5, height),
                                               PLASTER))
    painted(builder, RED, lambda: builder.box((-hw - 0.42, porch + 0.5, height - 0.6), (hw + 0.42, porch + 0.52,
                                                                                       height - 0.3), MATTE,
                                              bottom=False, top=False))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((-hw - 0.4, hd, -1.0), (hw + 0.4, porch + 0.9, 0.6),
                                                             PLASTER, bottom=False))
    builder.surface([[(-hw - 0.4, porch + 0.5, height), (hw + 0.4, porch + 0.5, height)],
                     [(-hw - 0.4, hd, height + 1.4), (hw + 0.4, hd, height + 1.4)]], TILES, facing=(0, 0, 1))
    cw, cd = hw - wing, hd - wing
    for x0, y0, x1, y1 in ((-cw, -cd, cw, -cd + 3.0), (-cw, cd - 3.0, cw, cd), (-cw, -cd + 3.0, -cw + 3.0, cd - 3.0),
                           (cw - 3.0, -cd + 3.0, cw, cd - 3.0)):
        builder.surface([[(x0, y0, 5.6), (x1, y0, 5.6)], [(x0, y1, 5.6), (x1, y1, 5.6)]], TILES, facing=(0, 0, 1))
    count_x = int(2 * cw / 3.6)
    count_y = int(2 * cd / 3.6)
    pillars = [(-cw + 3.0 + (2 * cw - 6.0) * k / count_x, y) for k in range(count_x + 1) for y in (-cd + 3.0, cd - 3.0)]
    pillars += [(x, -cd + 3.0 + (2 * cd - 6.0) * k / count_y) for k in range(1, count_y) for x in (-cw + 3.0,
                                                                                                    cw - 3.0)]
    for x, y in pillars:
        tube(builder, [(x, y, 0.6), (x, y, 5.6)], [0.28, 0.24], trim, 5, PLASTER)
    painted(builder, (0.94, 0.88, 0.76), lambda: builder.box((-cw + 3.5, -cd + 3.5, 0.6), (cw - 3.5, cd - 3.5, 0.72),
                                                             PLASTER, bottom=False))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * 6.5, sx * (cw - 5.5)))
            y0, y1 = sorted((sy * 4.5, sy * (cd - 5.5)))
            if x1 - x0 < 2.0 or y1 - y0 < 2.0:
                continue
            painted(builder, (0.30, 0.38, 0.16), lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box(
                (x0, y0, 0.6), (x1, y1, 0.85), MATTE, bottom=False))
    painted(builder, (0.98, 0.96, 0.9), lambda: builder.box((-5.0, -3.0, 0.6), (5.0, 3.0, 1.1), PLASTER, bottom=False))
    painted(builder, (0.24, 0.52, 0.62), lambda: builder.box((-4.5, -2.5, 1.0), (4.5, 2.5, 1.12), MATTE, bottom=False))
    for k in range(6):
        x = -9.0 + 18.0 * k / 5
        tube(builder, [(x, -hd - 5.0, 0.6), (x, -hd - 5.0, 8.1)], [0.42, 0.36], trim, 6, PLASTER)
    painted(builder, trim, lambda: builder.box((-10.5, -hd - 6.0, 8.1), (10.5, -hd, 9.6), PLASTER))
    ridge = 9.6 + 10.5 * math.tan(math.radians(15))
    gable_roof(builder, -hd - 6.0, -hd + 0.5, 10.8, 9.6, ridge, TILES, along_axis="y", imbrex=False)
    cmon.pediment(builder, 10.5, -hd - 6.0, 9.6, ridge, -1, PLASTER, BLUE)
    builder.oriented([(-2.0, -hd - 0.03, 0.6), (2.0, -hd - 0.03, 0.6), (2.0, -hd - 0.03, 5.0), (-2.0, -hd - 0.03, 5.0)],
                     (0, -1, 0), VOID)
    if hall:
        front = hd - wing - 16.0
        back = hd - wing + 2.0
        top = height + 6.0
        rise = 3.8
        painted(builder, (1.0, 0.94, 0.84), lambda: builder.box((-14.0, front, 0.6), (14.0, back, top), PLASTER,
                                                                bottom=False, top=False))
        for k in range(6):
            x = -12.0 + k * 4.8
            builder.oriented([(x - 0.7, front - 0.02, top - 4.0), (x + 0.7, front - 0.02, top - 4.0),
                              (x + 0.7, front - 0.02, top - 1.5), (x - 0.7, front - 0.02, top - 1.5)], (0, -1, 0), VOID)
        local = MeshBuilder()
        gable_roof(local, -14.6, 14.6, (back - front) / 2 + 0.5, top, top + rise, TILES, along_axis="x", imbrex=False)
        builder.merge(local, Matrix.Translation((0.0, (front + back) / 2, 0.0)))
        for x, facing in ((-14.0, -1), (14.0, 1)):
            tri = [(x, front, top), (x, back, top), (x, (front + back) / 2, top + rise)]
            painted(builder, (1.0, 0.94, 0.84), lambda tri=tri, facing=facing: builder.oriented(tri, (facing, 0, 0),
                                                                                                PLASTER))
    return builder, [], [(-cw + 6.0, -cd + 6.0), (cw - 6.0, cd - 6.0), (-cw + 6.0, cd - 6.0), (cw - 6.0, -cd + 6.0)]


def paneion(radius=56.0, height=26.0, turns=2.25):
    builder = MeshBuilder()
    profile = []
    for k in range(9):
        t = k / 8
        profile.append((radius * (1 - t) ** 0.9 + 6.0 * t, height * t))
    profile.append((0.0, height))
    painted(builder, (0.76, 0.72, 0.52), lambda: builder.lathe([(radius, -1.0)] + profile, 32, MATTE, smooth=True))
    path = []
    for k in range(120):
        t = k / 119
        angle = TAU * turns * t
        r = radius * (1 - t) ** 0.9 + 6.0 * t + 0.4
        z = height * t + 0.25
        path.append(Vector((r * math.cos(angle), r * math.sin(angle), z)))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.sweep(path, [(-0.2, -0.6), (3.2, -0.6), (3.2, 0.1),
                                                                      (-0.2, 0.1)], PAVING, caps=True))
    painted(builder, WARM, lambda: builder.lathe([(7.5, height - 0.5), (7.5, height + 0.6), (0.0, height + 0.6)], 18,
                                                 MARBLE))
    ring_frames = []
    for k in range(10):
        angle = TAU * k / 10
        ring_frames.append(column_frame(5.6 * math.cos(angle), 5.6 * math.sin(angle), height + 0.6, 0.5, 4.5))
    painted(builder, WARM, lambda: builder.lathe([(6.2, height + 5.1), (6.4, height + 5.9), (0.0, height + 5.9)], 18,
                                                 MARBLE))
    painted(builder, (1.0, 0.82, 0.55), lambda: builder.lathe([(6.4, height + 5.9), (4.0, height + 7.4),
                                                               (0.0, height + 8.2)], 18, GILT))
    return builder, ring_frames


def isis_shrine():
    temple, frames = cmon.temple(10.0, 17.0, 2.0, 6.5, 0.7, 4, "ionic")
    builder = MeshBuilder()
    builder.merge(temple)
    wall, wall_frames = temenos(44.0, 36.0, height=4.0, depth=4.0, spacing=3.4, gate=6.0)
    builder.merge(wall, Matrix.Translation((0.0, 4.0, 0.0)))
    return builder, {"ionic": [Matrix.Translation((0.0, 0.0, 0.0)) @ f for f in frames.get("ionic", [])],
                     "simple": [Matrix.Translation((0.0, 4.0, 0.0)) @ f for f in wall_frames]}


def city_wall_segment(length=40.0, height=11.0, thickness=4.5):
    builder = MeshBuilder()
    painted(builder, (0.94, 0.88, 0.76), lambda: builder.box((0.0, -thickness / 2, -2.0), (length, thickness / 2,
                                                                                          height), STONE,
                                                            bottom=False))
    count = int(length / 2.6)
    for k in range(count):
        x = 1.3 + k * 2.6
        painted(builder, (0.94, 0.88, 0.76), lambda x=x: builder.box((x - 0.65, thickness / 2 - 0.7, height),
                                                                     (x + 0.65, thickness / 2, height + 1.3), STONE,
                                                                     bottom=False))
    return builder


def city_tower(size=9.0, height=16.0):
    builder = MeshBuilder()
    h = size / 2
    painted(builder, (0.96, 0.9, 0.78), lambda: builder.box((-h, -h, -2.0), (h, h, height), STONE, bottom=False))
    painted(builder, (0.96, 0.9, 0.78), lambda: builder.box((-h - 0.4, -h - 0.4, height), (h + 0.4, h + 0.4,
                                                                                           height + 0.6), STONE))
    for k in range(4):
        for j in range(3):
            angle = TAU * k / 4
            normal = Vector((math.cos(angle), math.sin(angle), 0.0))
            side = Vector((-normal.y, normal.x, 0.0))
            centre = normal * (h + 0.38) + side * ((j - 1) * 2.8)
            builder.box((centre.x - 0.6, centre.y - 0.6, height + 0.6), (centre.x + 0.6, centre.y + 0.6, height + 1.8),
                        STONE, bottom=False)
            corner = normal * (h + 0.02) + side * ((j - 1) * 2.8)
            builder.oriented([corner + side * -0.35 + Vector((0, 0, height - 5.0)),
                              corner + side * 0.35 + Vector((0, 0, height - 5.0)),
                              corner + side * 0.35 + Vector((0, 0, height - 3.6)),
                              corner + side * -0.35 + Vector((0, 0, height - 3.6))], normal, VOID)
    return builder


def city_gate(width=12.0, depth=14.0, height=15.0):
    builder = MeshBuilder()
    for side in (-1, 1):
        builder.merge(city_tower(11.0, height + 4.0), Matrix.Translation((side * (width / 2 + 5.5), 0.0, 0.0)))
    painted(builder, (0.96, 0.9, 0.78), lambda: builder.box((-width / 2, -depth / 2, 7.0), (width / 2, depth / 2, height),
                                                            STONE))
    for y in (-depth / 2 - 0.02, depth / 2 + 0.02):
        n = -1 if y < 0 else 1
        builder.oriented([(-3.2, y, 0.0), (3.2, y, 0.0), (3.2, y, 7.0), (-3.2, y, 7.0)], (0, n, 0), VOID)
    return builder


def tomb(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    kind = seed % 3
    tone = OCHRES[rng.randrange(len(OCHRES))]
    if kind == 0:
        painted(builder, tone, lambda: builder.box((-3.0, -3.0, -0.5), (3.0, 3.0, 3.2), PLASTER, bottom=False))
        painted(builder, WARM, lambda: builder.box((-3.3, -3.3, 3.2), (3.3, 3.3, 3.7), STONE))
        painted(builder, WARM, lambda: builder.prism([(-2.6, -2.6), (2.6, -2.6), (2.6, 2.6), (-2.6, 2.6)], 3.7, 4.4,
                                                     STONE, bottom=False))
        builder.oriented([(-0.6, -3.02, 0.0), (0.6, -3.02, 0.0), (0.6, -3.02, 1.8), (-0.6, -3.02, 1.8)], (0, -1, 0),
                         VOID)
    elif kind == 1:
        painted(builder, tone, lambda: builder.box((-5.0, -4.0, -0.5), (5.0, 4.0, 1.4), PLASTER, bottom=False,
                                                   top=False))
        painted(builder, WARM, lambda: builder.box((-1.2, -1.2, -0.5), (1.2, 1.2, 2.4), STONE, bottom=False))
        painted(builder, WARM, lambda: builder.box((-1.4, -1.4, 2.4), (1.4, 1.4, 2.8), STONE))
    else:
        painted(builder, WARM, lambda: builder.box((-1.6, -1.0, -0.5), (1.6, 1.0, 1.2), STONE, bottom=False))
        painted(builder, tone, lambda: builder.prism([(-1.7, -1.1), (1.7, -1.1), (1.7, 1.1), (-1.7, 1.1)], 1.2, 1.6,
                                                     PLASTER, bottom=False))
        tube(builder, [(0.0, 0.0, 1.6), (0.0, 0.0, 2.4)], [0.25, 0.0], WARM, 6, STONE)
    return builder


def boulder(builder, centre, radii, colour, rng, material=STONE, segments=7, rings=4):
    first_point = len(builder.positions)
    first_face = len(builder.polygons)
    ellipsoid(builder, centre, radii, colour, segments, rings, material)
    centre = Vector(centre)
    for index in range(first_point, len(builder.positions)):
        point = Vector(builder.positions[index])
        offset = point - centre
        factor = rng.uniform(0.72, 1.18)
        offset = Vector((offset.x * factor, offset.y * factor, offset.z * rng.uniform(0.8, 1.1)))
        if offset.z > radii[2] * 0.45:
            offset.z = radii[2] * 0.45 + (offset.z - radii[2] * 0.45) * 0.3
        moved = centre + offset
        builder.positions[index] = (moved.x, moved.y, moved.z)
        builder.heights[index] = moved.z
    for index in range(first_face, len(builder.polygons)):
        builder.polygon_smooth[index] = False
        shade = rng.uniform(0.86, 1.08)
        current = builder.polygon_colors[index] or (1.0, 1.0, 1.0)
        builder.polygon_colors[index] = tuple(c * shade for c in current)


def lighthouse_rocks(seed=0, count=70, radius=92.0, inner=64.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        angle = rng.uniform(0, TAU)
        r = rng.uniform(inner, radius + 6.0)
        size = rng.uniform(1.4, 4.2)
        centre = (r * math.cos(angle), r * math.sin(angle), rng.uniform(-1.4, 0.4))
        tone = rng.uniform(0.74, 0.9)
        boulder(builder, centre, (size, size * rng.uniform(0.6, 1.0), size * rng.uniform(0.4, 0.7)),
                (tone, tone * 0.93, tone * 0.82), rng)
    return builder


def reef_rock(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(5):
        size = rng.uniform(0.8, 2.8)
        centre = (rng.uniform(-3.5, 3.5), rng.uniform(-3.5, 3.5), rng.uniform(-0.7, -0.1))
        tone = rng.uniform(0.46, 0.6)
        boulder(builder, centre, (size, size * rng.uniform(0.6, 1.0), size * rng.uniform(0.3, 0.55)),
                (tone, tone * 0.92, tone * 0.8), rng, segments=6, rings=3)
    return builder


def land_rock(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(4):
        size = rng.uniform(0.7, 2.2)
        centre = (rng.uniform(-3.0, 3.0), rng.uniform(-3.0, 3.0), 0.2 * size)
        tone = rng.uniform(0.92, 1.04)
        boulder(builder, centre, (size, size * rng.uniform(0.6, 1.0), size * rng.uniform(0.35, 0.55)),
                (0.82 * tone, 0.76 * tone, 0.64 * tone), rng, segments=7, rings=4)
    return builder


def mole(length, width=10.0, top=1.9, foot=-4.5):
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-width / 2, 0.0, foot), (width / 2, length, top - 0.05), STONE,
                                              bottom=False, top=False))
    painted(builder, (1.0, 0.96, 0.88), lambda: builder.box((-width / 2 - 0.2, -2.0, top - 0.3),
                                                            (width / 2 + 0.2, length + 0.2, top), PAVING,
                                                            bottom=False))
    return builder


def emporion_stoa(length=120.0, depth=14.0, height=8.0, seed=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    frames = []
    hl = length / 2
    painted(builder, (1.0, 0.97, 0.9), lambda: builder.box((-hl, -1.5, -0.6), (hl, depth, 0.45), MARBLE,
                                                           bottom=False))
    count = int(length / 4.2)
    for k in range(count + 1):
        frames.append(column_frame(-hl + length * k / count, 0.0, 0.45, 0.62, height))
    painted(builder, WARM, lambda: builder.box((-hl - 0.5, -0.7, height + 0.45), (hl + 0.5, depth, height + 1.5),
                                              MARBLE))
    painted(builder, RED, lambda: builder.box((-hl - 0.52, -0.72, height + 0.9), (hl + 0.52, -0.69, height + 1.15),
                                              MATTE, bottom=False, top=False))
    painted(builder, OCHRES[1], lambda: builder.box((-hl, depth - 0.7, -0.6), (hl, depth, height + 4.5), PLASTER,
                                                    bottom=False))
    builder.surface([[(-hl - 0.5, -0.7, height + 1.5), (hl + 0.5, -0.7, height + 1.5)],
                     [(-hl - 0.5, depth, height + 4.0), (hl + 0.5, depth, height + 4.0)]], TILES, facing=(0, 0, 1))
    for k in range(int(length / 6.0)):
        x = -hl + 3.0 + k * 6.0
        builder.oriented([(x - 1.2, depth - 0.72, 0.45), (x + 1.2, depth - 0.72, 0.45), (x + 1.2, depth - 0.72, 3.4),
                          (x - 1.2, depth - 0.72, 3.4)], (0, -1, 0), VOID)
        if rng.random() < 0.5:
            cloth = CLOTHS[rng.randrange(len(CLOTHS))]
            drape(builder, cloth, [(0.5, 0.45), (0.6, 0.7), (0.3, 1.0)], 6, folds=(4, 0.1, k), squash=1.0,
                  center=(x + rng.uniform(-1.5, 1.5), depth - 3.0))
    return builder, frames


def market_awning(width=6.0, depth=4.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    cloth = CLOTHS[rng.randrange(len(CLOTHS))]
    stripe = CLOTHS[rng.randrange(len(CLOTHS))]
    hw, hd = width / 2, depth / 2
    for k in range(6):
        x0 = -hw + width * k / 6
        x1 = -hw + width * (k + 1) / 6
        colour = cloth if k % 2 == 0 else stripe
        quad = [(x0, -hd, 2.5), (x1, -hd, 2.5), (x1, hd, 3.1), (x0, hd, 3.1)]
        painted(builder, colour, lambda quad=quad: builder.oriented(quad, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.75 for c in colour), lambda quad=quad: builder.oriented(list(reversed(quad)),
                                                                                             (0, 0.3, -1), MATTE))
    for x in (-hw + 0.1, hw - 0.1):
        for y, z in ((-hd + 0.1, 2.5), (hd - 0.1, 3.1)):
            tube(builder, [(x, y, 0.0), (x, y, z)], [0.05, 0.05], WOOD, 4)
    painted(builder, (0.62, 0.48, 0.32), lambda: builder.box((-hw + 0.4, -0.5, 0.0), (hw - 0.4, 0.5, 0.85), MATTE,
                                                             bottom=False))
    for k in range(5):
        x = -hw + 0.9 + k * (width - 1.8) / 4
        produce = [(0.86, 0.5, 0.16), (0.42, 0.62, 0.2), (0.7, 0.2, 0.18), (0.9, 0.82, 0.5), (0.5, 0.3, 0.5)]
        ellipsoid(builder, (x, 0.0, 0.92), (0.38, 0.34, 0.14), produce[(k + seed) % 5], 6, 3, MATTE)
    return builder
