import math
import random

from mathutils import Matrix, Vector

from . import alexandrie_city as acity
from .geometry import MATTE, MeshBuilder
from .orders import gable_roof

STONE = "limestone"
MARBLE = "marble"
PLASTER = "plaster"
PAVING = "paving"
TILES = "terracotta_tiles"
VOID = "shadow_void"
TAU = 2 * math.pi
WALL_TONES = [(1.0, 0.95, 0.86), (0.98, 0.82, 0.60), (0.96, 0.74, 0.56), (1.0, 0.88, 0.76), (0.94, 0.66, 0.50),
              (0.98, 0.92, 0.70), (0.90, 0.78, 0.66)]
ROOF_TONES = [(1.0, 0.92, 0.86), (0.96, 0.82, 0.74), (1.0, 0.86, 0.76), (0.92, 0.78, 0.70)]
CLOTHS = [(0.80, 0.18, 0.12), (0.94, 0.72, 0.22), (0.22, 0.40, 0.70), (0.96, 0.93, 0.86)]


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def court_roof(builder, x0, y0, x1, y1, height, wall, roof):
    width, depth = x1 - x0, y1 - y0
    wing = min(width, depth) * 0.3
    cx0, cy0, cx1, cy1 = x0 + wing, y0 + wing, x1 - wing, y1 - wing
    floor = (0.46, 0.58, 0.28) if (int(x0 * 7 + y0 * 3) % 2) else (0.94, 0.88, 0.76)
    painted(builder, floor, lambda: builder.oriented([(cx0, cy0, 0.1), (cx1, cy0, 0.1), (cx1, cy1, 0.1),
                                                     (cx0, cy1, 0.1)], (0, 0, 1), PLASTER))
    inner = [(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)]
    normals = [(0, 1, 0), (-1, 0, 0), (0, -1, 0), (1, 0, 0)]
    shade = tuple(v * 0.9 for v in wall)
    for k in range(4):
        a, b = inner[k], inner[(k + 1) % 4]
        painted(builder, shade, lambda a=a, b=b, k=k: builder.oriented(
            [(a[0], a[1], 0.1), (b[0], b[1], 0.1), (b[0], b[1], height), (a[0], a[1], height)], normals[k], PLASTER))
    rise = wing * 0.32
    outer = [(x0 - 0.5, y0 - 0.5), (x1 + 0.5, y0 - 0.5), (x1 + 0.5, y1 + 0.5), (x0 - 0.5, y1 + 0.5)]
    for k in range(4):
        a, b = outer[k], outer[(k + 1) % 4]
        c, d = inner[(k + 1) % 4], inner[k]
        points = [(a[0], a[1], height + rise), (b[0], b[1], height + rise), (c[0], c[1], height), (d[0], d[1], height)]
        painted(builder, roof, lambda points=points: builder.oriented(points, (0, 0, 1), TILES))
    edges = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    outward = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
    for k in range(4):
        a, b = edges[k], edges[(k + 1) % 4]
        painted(builder, wall, lambda a=a, b=b, k=k: builder.oriented(
            [(a[0], a[1], height), (b[0], b[1], height), (b[0], b[1], height + rise), (a[0], a[1], height + rise)],
            outward[k], PLASTER))


def gable_house_roof(builder, x0, y0, x1, y1, height, wall, roof):
    width, depth = x1 - x0, y1 - y0
    roof_builder = MeshBuilder()
    if width >= depth:
        rise = depth * 0.2
        gable_roof(roof_builder, x0 - 0.4, x1 + 0.4, depth / 2 + 0.5, height, height + rise, TILES, along_axis="x",
                   imbrex=False)
        shift = (0.0, (y0 + y1) / 2, 0.0)
        middle = (y0 + y1) / 2
        ends = [([(x0, y1, height), (x0, y0, height), (x0, middle, height + rise)], (-1, 0, 0)),
                ([(x1, y0, height), (x1, y1, height), (x1, middle, height + rise)], (1, 0, 0))]
    else:
        rise = width * 0.2
        gable_roof(roof_builder, y0 - 0.4, y1 + 0.4, width / 2 + 0.5, height, height + rise, TILES, along_axis="y",
                   imbrex=False)
        shift = ((x0 + x1) / 2, 0.0, 0.0)
        middle = (x0 + x1) / 2
        ends = [([(x0, y0, height), (x1, y0, height), (middle, y0, height + rise)], (0, -1, 0)),
                ([(x1, y1, height), (x0, y1, height), (middle, y1, height + rise)], (0, 1, 0))]
    roof_builder.tint(0, roof)
    builder.merge(roof_builder, Matrix.Translation(shift))
    for points, normal in ends:
        painted(builder, wall, lambda points=points, normal=normal: builder.oriented(points, normal, PLASTER))


def openings(builder, x0, y0, x1, y1, floors, shops):
    width = x1 - x0
    for y, facing in ((y0, -1), (y1, 1)):
        count = max(int(width / 4.0), 1)
        for floor in range(1, floors + 1):
            z = (floor - 1) * 3.3 + (1.4 if floor == 1 else 1.0)
            for k in range(count):
                x = x0 + width * (k + 0.5) / count
                if floor == 1 and ((facing < 0 and shops) or k == count // 2):
                    builder.oriented([(x - 1.0, y + facing * 0.03, 0.0), (x + 1.0, y + facing * 0.03, 0.0),
                                      (x + 1.0, y + facing * 0.03, 2.5), (x - 1.0, y + facing * 0.03, 2.5)],
                                     (0, facing, 0), VOID)
                    continue
                builder.oriented([(x - 0.35, y + facing * 0.03, z), (x + 0.35, y + facing * 0.03, z),
                                  (x + 0.35, y + facing * 0.03, z + 0.9), (x - 0.35, y + facing * 0.03, z + 0.9)],
                                 (0, facing, 0), VOID)


def tiled_house(builder, x0, y0, x1, y1, rng, detail, shops):
    width, depth = x1 - x0, y1 - y0
    floors = rng.choice((1, 2, 2, 2, 3))
    height = floors * 3.3 + 0.3
    wall = WALL_TONES[rng.randrange(len(WALL_TONES))]
    roof = ROOF_TONES[rng.randrange(len(ROOF_TONES))]
    court = width > 14.0 and depth > 12.0 and rng.random() < 0.7
    painted(builder, wall, lambda: builder.box((x0, y0, -1.0), (x1, y1, height), PLASTER, bottom=False, top=False))
    if court:
        court_roof(builder, x0, y0, x1, y1, height, wall, roof)
    else:
        gable_house_roof(builder, x0, y0, x1, y1, height, wall, roof)
    if not detail:
        return
    openings(builder, x0, y0, x1, y1, floors, shops)
    if shops and rng.random() < 0.6:
        cloth = CLOTHS[rng.randrange(len(CLOTHS))]
        awning = [(x0 + 0.5, y0, 3.0), (x1 - 0.5, y0, 3.0), (x1 - 0.5, y0 - 2.2, 2.4), (x0 + 0.5, y0 - 2.2, 2.4)]
        painted(builder, cloth, lambda: builder.oriented(awning, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.7 for c in cloth), lambda: builder.oriented(list(reversed(awning)), (0, 0.3, -1),
                                                                                 MATTE))
    painted(builder, tuple(c * 0.85 for c in wall), lambda: builder.box((x0 - 0.05, y0 - 0.05, -0.6),
                                                                        (x1 + 0.05, y1 + 0.05, 0.6), PLASTER,
                                                                        bottom=False, top=False))


def ephesian_block(seed, detail=True, width=46.0, depth=38.0, street=("south",), plinth=8.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for x0, y0, x1, y1, i, j, columns in acity.lots(rng, width, depth):
        tiled_house(builder, x0, y0, x1, y1, random.Random(rng.random()), detail, j == 0 and "south" in street)
    painted(builder, (0.90, 0.84, 0.72), lambda: builder.box((-width / 2 + 0.4, -depth / 2 + 0.4, -plinth),
                                                             (width / 2 - 0.4, depth / 2 - 0.4, -0.4), STONE,
                                                             bottom=False, top=False))
    return builder


def theatre_cavea(radius=70.0, orchestra=12.0, rows=36, height=20.0, sweep_degrees=200.0):
    builder = MeshBuilder()
    frames = []
    sweep = math.radians(sweep_degrees)
    start = math.pi / 2 - sweep / 2
    step = (radius - orchestra - 6.0) / rows
    rise = height / rows
    profile = [(orchestra, -0.5), (orchestra, 0.4)]
    r = orchestra + 1.0
    z = 0.4
    for k in range(rows):
        if k and k % 12 == 0:
            profile.append((r + 1.4, z))
            r += 1.4
        profile += [(r, z + rise), (r + step, z + rise)]
        r += step
        z += rise
    profile.append((radius, z))
    painted(builder, (0.97, 0.94, 0.88), lambda: builder.lathe(list(reversed(profile)), 40, MARBLE, smooth=False,
                                                              start=start, sweep=sweep, caps=False))
    for k in range(9):
        angle = start + sweep * (k + 0.5) / 9
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        a = normal * (orchestra + 1.0)
        b = normal * (radius - 2.0)
        points = [a - side * 0.6 + Vector((0, 0, 0.5)), a + side * 0.6 + Vector((0, 0, 0.5)),
                  b + side * 0.6 + Vector((0, 0, height + 0.5)), b - side * 0.6 + Vector((0, 0, height + 0.5))]
        painted(builder, (0.72, 0.68, 0.62), lambda points=points: builder.oriented(points, (0, 0, 1), MARBLE))
    painted(builder, (0.96, 0.86, 0.70), lambda: builder.lathe([(radius, -8.0), (radius, height + 3.2),
                                                               (radius - 2.0, height + 3.2)], 40, STONE, smooth=False,
                                                              start=start, sweep=sweep, caps=False))
    for k in range(20):
        angle = start + sweep * (k + 0.5) / 20
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        centre = normal * (radius + 0.03)
        for z0, z1 in ((-3.0, 2.0), (height - 6.0, height - 2.0)):
            builder.oriented([centre - side * 1.4 + Vector((0, 0, z0)), centre + side * 1.4 + Vector((0, 0, z0)),
                              centre + side * 1.4 + Vector((0, 0, z1)), centre - side * 1.4 + Vector((0, 0, z1))],
                             normal, VOID)
    for angle, sign in ((start, 1.0), (start + sweep, -1.0)):
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0)) * sign
        a = normal * orchestra
        b = normal * radius
        wall = [a + Vector((0, 0, -6.0)), b + Vector((0, 0, -6.0)), b + Vector((0, 0, height + 3.2)),
                a + Vector((0, 0, 1.6))]
        painted(builder, (0.96, 0.86, 0.70), lambda wall=wall, side=side: builder.oriented(wall, -side, STONE))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.lathe([(orchestra, 0.35), (0.0, 0.35)], 32, PAVING,
                                                              start=0.0, sweep=TAU, caps=False))
    skene_y = -orchestra - 4.0
    hl = orchestra + 22.0
    painted(builder, (0.98, 0.93, 0.84), lambda: builder.box((-hl, skene_y - 9.0, -1.0), (hl, skene_y, 18.0), PLASTER,
                                                             bottom=False))
    painted(builder, (0.98, 0.96, 0.9), lambda: builder.box((-hl + 4.0, skene_y, -1.0), (hl - 4.0, skene_y + 5.0,
                                                                                         2.8), MARBLE,
                                                            bottom=False))
    for k in range(12):
        x = -hl + 6.0 + k * (2 * hl - 12.0) / 11
        frames.append(Matrix.Translation((x, skene_y + 1.2, 2.8)) @ Matrix.Scale(7.0 / 17.8, 4))
        frames.append(Matrix.Translation((x, skene_y + 1.2, 10.6)) @ Matrix.Scale(6.0 / 17.8, 4))
    for z0, z1 in ((9.8, 10.6), (16.6, 17.6)):
        painted(builder, (0.99, 0.97, 0.92), lambda z0=z0, z1=z1: builder.box((-hl + 4.0, skene_y, z0),
                                                                             (hl - 4.0, skene_y + 2.4, z1), MARBLE))
    for x in (-9.0, 0.0, 9.0):
        builder.oriented([(x - 1.5, skene_y + 0.02, 2.8), (x + 1.5, skene_y + 0.02, 2.8),
                          (x + 1.5, skene_y + 0.02, 7.6), (x - 1.5, skene_y + 0.02, 7.6)], (0, 1, 0), VOID)
    for k in range(5):
        x = -hl + 8.0 + k * (2 * hl - 16.0) / 4
        painted(builder, (0.66, 0.24, 0.18), lambda x=x: builder.oriented(
            [(x - 1.2, skene_y + 0.02, 11.4), (x + 1.2, skene_y + 0.02, 11.4), (x + 1.2, skene_y + 0.02, 15.6),
             (x - 1.2, skene_y + 0.02, 15.6)], (0, 1, 0), MATTE))
    roof = MeshBuilder()
    gable_roof(roof, -hl, hl, 5.0, 18.0, 20.5, TILES, along_axis="x", imbrex=False)
    roof.tint(0, (1.0, 0.9, 0.84))
    builder.merge(roof, Matrix.Translation((0.0, skene_y - 4.5, 0.0)))
    return builder, frames
