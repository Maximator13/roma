import math
import random

from mathutils import Matrix, Vector

from . import colisee_monuments as mon
from .geometry import MATTE, MeshBuilder, placement

PEPERINO = (0.6, 0.58, 0.53)
TUFF = (0.66, 0.6, 0.48)
SLABS = "col_slabs"
SAND = "arena_sand"


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def curved_wall(builder, cx, cy, radius, thickness, z0, z1, start, sweep, material, segments=12):
    for k in range(segments):
        a = start + sweep * k / segments
        b = start + sweep * (k + 1) / segments
        mid = (a + b) / 2
        for r, sign in ((radius, -1.0), (radius + thickness, 1.0)):
            pa = (cx + r * math.cos(a), cy + r * math.sin(a))
            pb = (cx + r * math.cos(b), cy + r * math.sin(b))
            builder.oriented([(*pa, z0), (*pb, z0), (*pb, z1), (*pa, z1)], (sign * math.cos(mid), sign * math.sin(mid), 0),
                             material)
        ring = [(cx + r * math.cos(t), cy + r * math.sin(t), z1) for r, t in
                ((radius, a), (radius, b), (radius + thickness, b), (radius + thickness, a))]
        builder.oriented(ring, (0, 0, 1), material)


def roof(builder, matrix, start, end, half, eave, ridge, along="y"):
    local = MeshBuilder()
    mon.gable_roof(local, start, end, half, eave, ridge, mon.TILES, along_axis=along, imbrex=False)
    builder.merge(local, matrix)


def portico_run(builder, frames, a, b, depth, height, spacing, diameter=0.8, wall_colour=PEPERINO, gap=None):
    a, b = Vector(a), Vector(b)
    span = (b - a).length
    angle = math.atan2(b.y - a.y, b.x - a.x)
    local = MeshBuilder()
    count = max(int(span / spacing), 1)
    matrix = Matrix.Translation((a.x, a.y, 0.0)) @ Matrix.Rotation(angle, 4, "Z")
    for k in range(count + 1):
        frames.append(matrix @ mon.column_frame(span * k / count, 0.0, 0.15, diameter, height))
    local.box((-0.6, -0.8, height), (span + 0.6, depth + 0.4, height + 1.1), mon.MARBLE)
    painted(local, mon.OCHRE_RED, lambda: local.box((-0.62, -0.82, height + 0.62), (span + 0.62, -0.78, height + 0.78),
                                                     MATTE, bottom=False, top=False))
    pieces = [(-0.6, span + 0.6)] if gap is None else [(-0.6, gap[0]), (gap[1], span + 0.6)]
    for x0, x1 in pieces:
        local.box((x0, depth, -1.0), (x1, depth + 0.9, height + 2.6), mon.PLASTER, bottom=False)
    local.paint(mon.PLASTER, wall_colour)
    local.surface([[(-0.6, -0.8, height + 1.1), (span + 0.6, -0.8, height + 1.1)],
                   [(-0.6, depth + 0.4, height + 2.4), (span + 0.6, depth + 0.4, height + 2.4)]], mon.TILES,
                  facing=(0, 0, 1))
    local.box((-0.6, -1.0, -0.6), (span + 0.6, depth, 0.15), mon.MARBLE, bottom=False)
    builder.merge(local, matrix)


def floor(builder, x0, y0, x1, y1, z=0.1):
    builder.box((x0, y0, z - 1.4), (x1, y1, z), SLABS, bottom=False)


def forum_iulium():
    builder = MeshBuilder()
    frames = {"simple": [], "corinthian": []}
    hw, hl = 37.5, 80.0
    floor(builder, -hw, -hl, hw, hl)
    for side in (-1, 1):
        x = side * (hw - 10.0)
        a, b = (x, -hl + 3.0), (x, hl - 6.0)
        if side > 0:
            a, b = b, a
        portico_run(builder, frames["simple"], a, b, 9.0, 9.0, 4.4, 0.85)
    painted(builder, PEPERINO, lambda: builder.box((-hw, hl - 1.5, -1.0), (hw, hl, 18.0), mon.PLASTER, bottom=False))
    for x0, x1 in ((-hw, -7.0), (7.0, hw)):
        painted(builder, PEPERINO, lambda x0=x0, x1=x1: builder.box((x0, -hl, -1.0), (x1, -hl + 1.2, 13.0), mon.PLASTER,
                                                                    bottom=False))
    temple, columns = mon.temple(30.0, 45.0, 5.0, 15.0, 1.5, 8, "corinthian", peripteral=True, pronaos=3)
    tm = placement(0.0, hl - 26.0, 0.1, math.pi)
    builder.merge(temple, tm)
    frames["corinthian"].extend(tm @ f for f in columns["corinthian"])
    for side in (-1, 1):
        builder.merge(mon.scaffold(40.0, 18.0), placement(side * 16.6, hl - 26.0, 5.1, math.pi / 2))
    for x in (-9.0, 9.0):
        builder.box((x - 2.5, hl - 58.0, 0.1), (x + 2.5, hl - 54.0, 0.7), mon.MARBLE, bottom=False)
        builder.box((x - 2.2, hl - 57.7, 0.6), (x + 2.2, hl - 54.3, 0.65), mon.WATER, bottom=False)
    builder.box((-1.6, -10.0, 0.1), (1.6, -4.0, 2.6), mon.MARBLE, bottom=False)
    mon.horse(builder, placement(0.0, -7.0, 2.6, math.pi, 1.4), (1.0, 1.0, 1.0), mon.PATINA, gait=0.6)
    return builder, frames


def forum_augustum():
    builder = MeshBuilder()
    frames = {"simple": [], "corinthian": []}
    hw, hl = 62.5, 59.0
    floor(builder, -39.0, -hl, 39.0, hl)
    for side in (-1, 1):
        x = side * 27.0
        a, b = (x, -hl + 2.0), (x, 22.0)
        gap = (40.0, 78.0)
        if side > 0:
            a, b = b, a
            gap = (1.0, 39.0)
        portico_run(builder, frames["simple"], a, b, 11.0, 10.0, 3.8, 0.9, gap=gap)
        painted(builder, (0.9, 0.87, 0.8), lambda x=x: builder.box((x - 1.0 if x > 0 else x - 0.2, -hl + 1.0, 11.1),
                                                                    (x + 0.2 if x > 0 else x + 1.0, 22.6, 14.6),
                                                                    mon.MARBLE, bottom=False))
        cx = side * 38.0
        curved_wall(builder, cx, 2.0, 19.0, 1.4, -1.0, 16.0, -math.pi / 2 if side > 0 else math.pi / 2, math.pi,
                    mon.PLASTER, 14)
        builder.box((min(cx, cx + side * 21.0), -18.0, -1.0), (max(cx, cx + side * 21.0), 22.0, 0.1), SLABS,
                    bottom=False)
    temple, columns = mon.temple(36.0, 50.0, 3.5, 17.7, 1.75, 8, "corinthian", peripteral=True, pronaos=3)
    tm = placement(0.0, hl - 27.0, 0.1, math.pi)
    builder.merge(temple, tm)
    frames["corinthian"].extend(tm @ f for f in columns["corinthian"])
    painted(builder, PEPERINO, lambda: builder.box((-hw, hl, -2.0), (hw, hl + 3.0, 33.0), mon.PLASTER, bottom=False))
    for side in (-1, 1):
        painted(builder, PEPERINO, lambda side=side: builder.box((min(side * hw, side * (hw - 2.5)), -hl, -2.0),
                                                                 (max(side * hw, side * (hw - 2.5)), hl, 22.0),
                                                                 mon.PLASTER, bottom=False))
    builder.box((-2.0, -30.0, 0.1), (2.0, -24.0, 2.8), mon.MARBLE, bottom=False)
    builder.merge(mon.quadriga(), placement(0.0, -27.0, 2.8, math.pi, 1.2))
    return builder, frames


def forum_transitorium():
    builder = MeshBuilder()
    frames = {"simple": [], "corinthian": []}
    hw, hl = 22.5, 60.0
    floor(builder, -hw, -hl, hw, hl)
    for side in (-1, 1):
        x0, x1 = sorted((side * hw, side * (hw - 1.6)))
        painted(builder, PEPERINO, lambda x0=x0, x1=x1: builder.box((x0, -hl, -1.0), (x1, hl, 17.0), mon.PLASTER,
                                                                    bottom=False))
        y = -hl + 3.0
        while y < hl - 30.0:
            x = side * (hw - 3.0)
            frames["simple"].append(mon.column_frame(x, y, 0.9, 1.0, 10.5))
            builder.box((x - 0.9, y - 0.9, 0.1), (x + 0.9, y + 0.9, 0.9), mon.MARBLE, bottom=False)
            xa, xb = sorted((x - side * 0.9, side * (hw - 1.6)))
            builder.box((xa, y - 0.85, 11.4), (xb, y + 0.85, 13.0), mon.MARBLE, bottom=False)
            y += 5.6
        xa, xb = sorted((side * (hw - 1.6), side * (hw - 2.4)))
        builder.box((xa, -hl, 11.4), (xb, hl - 30.0, 13.0), mon.MARBLE, bottom=False)
        painted(builder, (0.82, 0.78, 0.7), lambda xa=xa, xb=xb: builder.box((xa, -hl, 13.0), (xb, hl - 30.0, 15.4),
                                                                             mon.MARBLE, bottom=False))
    temple, columns = mon.temple(22.0, 32.0, 3.8, 14.5, 1.45, 6, "corinthian", pronaos=2)
    tm = placement(0.0, hl - 17.0, 0.1, math.pi)
    builder.merge(temple, tm)
    frames["corinthian"].extend(tm @ f for f in columns["corinthian"])
    return builder, frames


def trajan_worksite(seed=21):
    rng = random.Random(seed)
    builder = MeshBuilder()
    walls = []
    hw, hl = 105.0, 90.0
    builder.box((-hw, -hl, -1.5), (hw, hl, 0.15), mon.TRAV, bottom=False)
    builder.paint(mon.TRAV, (0.82, 0.74, 0.62))
    for k, (x0, x1, z, y0) in enumerate(((hw - 22.0, hw - 8.0, 14.0, -hl), (hw - 8.0, hw + 6.0, 27.0, -hl + 10.0),
                                         (hw + 6.0, hw + 20.0, 40.0, -hl + 20.0))):
        painted(builder, TUFF, lambda x0=x0, x1=x1, z=z, y0=y0: builder.box((x0, y0, -1.0), (x1, -y0, z), MATTE,
                                                                            bottom=False))
    curved_wall(builder, hw - 46.0, 0.0, 24.0, 2.4, -1.0, 15.0, -math.pi / 2, math.pi, mon.BRICK, 14)
    curved_wall(builder, hw - 46.0, 0.0, 30.0, 2.4, -1.0, 9.0, -math.pi / 2 + 0.2, math.pi - 0.4, mon.BRICK, 14)
    for k in range(13):
        angle = -math.pi / 2 + math.pi * (k + 0.5) / 13
        cx, cy = hw - 46.0 + 23.95 * math.cos(angle), 23.95 * math.sin(angle)
        side = Vector((-math.sin(angle), math.cos(angle), 0.0)) * 1.3
        n = Vector((-math.cos(angle), -math.sin(angle), 0.0))
        centre = Vector((cx, cy, 0.0))
        painted(builder, mon.WINDOW, lambda centre=centre, side=side, n=n: builder.oriented(
            [centre - side + Vector((0, 0, 0.6)), centre + side + Vector((0, 0, 0.6)),
             centre + side + Vector((0, 0, 4.4)), centre - side + Vector((0, 0, 4.4))], n, MATTE))
    for y in (-40.0, -12.0, 16.0):
        walls.append((-70.0, y, 40.0, y))
        mon.wall_run(builder, -70.0, y, 40.0, y, rng.uniform(1.2, 3.5), 2.4, mon.TRAV, 0)
    for x in (-70.0, -30.0, 10.0, 40.0):
        walls.append((x, -40.0, x, 16.0))
        mon.wall_run(builder, x, -40.0, x, 16.0, rng.uniform(0.8, 2.6), 2.0, mon.TRAV, 0)
    for k in range(10):
        x, y = rng.uniform(-60.0, 30.0), rng.uniform(-80.0, -50.0)
        builder.lathe([(0.0, -0.8), (0.75, -0.8), (0.75, 0.8), (0.0, 0.8)], 10, mon.MARBLE,
                      matrix=Matrix.Translation((x, y, 0.9)) @ Matrix.Rotation(rng.uniform(0, math.pi), 4, "Z")
                      @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    cranes = [placement(-20.0, -30.0, 0.15, 0.4), placement(35.0, 10.0, 0.15, 2.2), placement(60.0, -45.0, 0.15, 1.0)]
    scaffolds = [placement(hw - 22.0, -30.0, 0.15, math.pi / 2), placement(hw - 22.0, 25.0, 0.15, math.pi / 2)]
    heaps = [placement(-50.0, -65.0, 0.15, 0.3), placement(0.0, 60.0, 0.15, 1.2), placement(-80.0, 40.0, 0.15, 0.7),
             placement(20.0, -70.0, 0.15, 2.0)]
    return builder, walls, cranes, scaffolds, heaps


CIRCUS_HALF = 40.0
CIRCUS_START = -288.0
CIRCUS_CURVE = 230.0
CIRCUS_DEPTH = 30.0


def stadium_path(d, straight=48, arc=24):
    r = CIRCUS_HALF + d
    points = []
    for k in range(straight):
        y = CIRCUS_START + (CIRCUS_CURVE - CIRCUS_START) * k / straight
        points.append((Vector((r, y)), Vector((1.0, 0.0))))
    for k in range(arc + 1):
        angle = math.pi * k / arc
        n = Vector((math.cos(angle), math.sin(angle)))
        points.append((Vector((0.0, CIRCUS_CURVE)) + n * r, n))
    for k in range(1, straight + 1):
        y = CIRCUS_CURVE - (CIRCUS_CURVE - CIRCUS_START) * k / straight
        points.append((Vector((-r, y)), Vector((-1.0, 0.0))))
    return points


def circus_profile():
    rows = [("podium", 0.0, 0.0, 0.0, 3.6), ("walk", 0.0, 3.6, 1.6, 3.6)]
    d, z = 1.6, 3.6
    for k in range(17):
        rows.append(("seat", d, z, d, z + 0.82))
        rows.append(("seat", d, z + 0.82, d + 1.5, z + 0.82))
        d, z = d + 1.5, z + 0.82
    rows.append(("walk", d, z, CIRCUS_DEPTH - 0.8, z))
    rows.append(("back", CIRCUS_DEPTH - 0.8, z, CIRCUS_DEPTH - 0.8, 25.0))
    return rows, z


def circus_maximus():
    builder = MeshBuilder()
    rows, top = circus_profile()
    colours = {"podium": (0.93, 0.9, 0.84), "walk": (0.86, 0.84, 0.8), "seat": (0.9, 0.87, 0.82),
               "back": (0.84, 0.8, 0.74)}
    for index, (name, d0, z0, d1, z1) in enumerate(rows):
        inner = stadium_path(d0)
        outer = stadium_path(d1)
        riser = abs(d1 - d0) < 1e-6
        colour = colours[name]
        if name == "seat" and (index // 2) % 6 == 0:
            colour = tuple(c * 0.9 for c in colour)
        first = len(builder.polygons)
        for (pa, na), (pb, nb), (qa, _), (qb, _) in zip(inner[:-1], inner[1:], outer[:-1], outer[1:]):
            facing = (-(na + nb).normalized()).to_3d() if riser else Vector((0.0, 0.0, 1.0))
            builder.oriented([(pa.x, pa.y, z0), (pb.x, pb.y, z0), (qb.x, qb.y, z1), (qa.x, qa.y, z1)], facing, mon.TRAV)
        builder.tint(first, colour)
    path = stadium_path(CIRCUS_DEPTH)
    first = len(builder.polygons)
    for (pa, na), (pb, nb) in zip(path[:-1], path[1:]):
        n = (na + nb).normalized().to_3d()
        builder.oriented([(pa.x, pa.y, -3.0), (pb.x, pb.y, -3.0), (pb.x, pb.y, 25.0), (pa.x, pa.y, 25.0)], n, mon.TRAV)
    builder.tint(first, (0.9, 0.84, 0.74))
    for (pa, na), (pb, nb) in zip(path[:-1], path[1:]):
        span = (pb - pa).length
        n = (na + nb).normalized()
        count = max(int(span / 3.6), 1)
        for k in range(count):
            centre = pa.lerp(pb, (k + 0.5) / count) + n * 0.04
            side = (pb - pa).normalized() * 1.15
            for z0, z1 in ((0.0, 6.0), (9.0, 13.5)):
                painted(builder, (0.16, 0.13, 0.11), lambda centre=centre, side=side, z0=z0, z1=z1, n=n: builder.oriented(
                    [(*(centre - side), z0), (*(centre + side), z0), (*(centre + side), z1), (*(centre - side), z1)],
                    n.to_3d(), MATTE))
    roof_inner = stadium_path(CIRCUS_DEPTH - 0.8)
    for (pa, _), (pb, _), (qa, _), (qb, _) in zip(roof_inner[:-1], roof_inner[1:], path[:-1], path[1:]):
        builder.oriented([(pa.x, pa.y, 25.0), (pb.x, pb.y, 25.0), (qb.x, qb.y, 25.0), (qa.x, qa.y, 25.0)], (0, 0, 1),
                         mon.TILES)
    arena = [(p.x, p.y, 0.12) for p, _ in stadium_path(0.0)]
    builder.polygon(arena, SAND)
    builder.tint(len(builder.polygons) - 1, (0.97, 0.95, 0.92))
    builder.box((-CIRCUS_HALF - CIRCUS_DEPTH, CIRCUS_START - 12.0, -2.0), (CIRCUS_HALF + CIRCUS_DEPTH, CIRCUS_START, 11.0),
                mon.TRAV, bottom=False)
    for k in range(12):
        x = -CIRCUS_HALF + 4.0 + (2 * CIRCUS_HALF - 8.0) * (k + 0.5) / 12
        painted(builder, (0.16, 0.13, 0.11), lambda x=x: builder.oriented(
            [(x - 2.0, CIRCUS_START + 0.04, 0.1), (x + 2.0, CIRCUS_START + 0.04, 0.1),
             (x + 2.0, CIRCUS_START + 0.04, 6.0), (x - 2.0, CIRCUS_START + 0.04, 6.0)], (0, 1, 0), MATTE))
    for side in (-1, 1):
        builder.box((side * 62.0 - 8.0, CIRCUS_START - 14.0, -2.0), (side * 62.0 + 8.0, CIRCUS_START + 2.0, 17.0),
                    mon.TRAV, bottom=False)
        roof(builder, Matrix.Translation((side * 62.0, 0.0, 0.0)), CIRCUS_START - 14.4, CIRCUS_START + 2.4, 8.4, 17.0,
             19.5)
    roof(builder, Matrix.Translation((0.0, CIRCUS_START - 6.0, 0.0)), -54.0, 54.0, 6.4, 11.0, 13.5, "x")
    builder.box((-4.0, -170.0, 0.1), (4.0, 174.0, 1.6), mon.MARBLE, bottom=False)
    builder.box((-3.2, -168.0, 1.6), (3.2, 172.0, 1.65), mon.WATER, bottom=False)
    for y, end in ((-176.0, -1), (180.0, 1)):
        builder.lathe([(4.2, 0.0), (4.2, 1.8), (0.0, 1.8)], 16, mon.MARBLE, matrix=Matrix.Translation((0.0, y, 0.1)))
        for x in (-1.8, 0.0, 1.8):
            builder.lathe([(1.0, 0.0), (0.4, 7.0), (0.0, 7.6)], 8, mon.GILT,
                          matrix=Matrix.Translation((x, y, 1.9)))
    builder.box((-2.4, -3.0, 1.6), (2.4, 3.0, 6.0), mon.MARBLE, bottom=False)
    painted(builder, (0.78, 0.62, 0.5), lambda: builder.lathe([(1.25, 0.0), (0.85, 21.4), (0.0, 23.7)], 4, MATTE,
                                                              smooth=False,
                                                              matrix=Matrix.Translation((0.0, 0.0, 6.0))
                                                              @ Matrix.Rotation(math.pi / 4, 4, "Z")))
    for y in (-120.0, -60.0, 60.0, 120.0):
        builder.box((-1.6, y - 2.0, 1.6), (1.6, y + 2.0, 5.2), mon.MARBLE, bottom=False)
        mon.gable_roof(builder, y - 2.3, y + 2.3, 1.9, 5.2, 6.2, mon.TILES, along_axis="y", imbrex=False)
    builder.box((-CIRCUS_HALF - 12.0, -40.0, 0.0), (-CIRCUS_HALF - 0.5, -20.0, 13.0), mon.MARBLE, bottom=False)
    roof(builder, Matrix.Translation((0.0, -30.0, 0.0)), -CIRCUS_HALF - 12.4, -CIRCUS_HALF - 0.1, 10.4, 13.0, 16.5, "x")
    return builder


def aqueduct_segment(length, height, arches):
    builder = MeshBuilder()
    mon.wall_run(builder, -length / 2, 0.0, length / 2, 0.0, height, 2.6, mon.BRICK, arches)
    builder.box((-length / 2, -1.5, height), (length / 2, 1.5, height + 1.8), mon.BRICK, bottom=False)
    builder.box((-length / 2, -1.6, height + 1.8), (length / 2, 1.6, height + 2.1), mon.TRAV, bottom=False)
    return builder
