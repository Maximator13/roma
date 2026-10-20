import math
import random

from mathutils import Matrix, Vector

from . import arles_details, arles_life, nimes_figures
from .arles_monuments import temple as arles_temple
from .buildings import amphitheatre_cavea
from .geometry import MATTE, MeshBuilder, placement
from .monuments import hillside_theatre
from .nimes_figures import Look, drape, ellipsoid, person, tube
from .orders import column
from .pompei_materials import remap
from .pompei_town import STONE, TILES, VOID, compluviate_roof, gable_roof, quad, tinted

STUCCO = (0.84, 0.80, 0.72)
TUFF = (0.66, 0.60, 0.50)
TIMBER = (0.42, 0.31, 0.20)
DARK_TIMBER = (0.30, 0.22, 0.15)
BASALT = (0.30, 0.29, 0.28)
COCCIO = (0.98, 0.66, 0.54)
RED_LOWER = (0.62, 0.16, 0.11)
PORTICO_DOWN = (4.6, 0.58)
PORTICO_UP = (3.6, 0.44)


def columns_template(order, diameter, height, detail="low", colour=STUCCO, red_lower=False):
    builder = remap(column(order, diameter, height, detail, "lens_smooth"))
    builder.materials = ["plaster" if name == "marble" else name for name in builder.materials]
    builder.tint(0, colour)
    if red_lower:
        for index, polygon in enumerate(builder.polygons):
            if max(builder.positions[i][2] for i in polygon) < height * 0.36:
                builder.polygon_colors[index] = RED_LOWER
    return builder


def beam(builder, start, end, size, colour, material=MATTE):
    start, end = Vector(start), Vector(end)
    direction = (end - start).normalized()
    side = direction.cross(Vector((0.0, 0.0, 1.0)))
    if side.length < 1e-4:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()
    up = side.cross(direction).normalized()
    h = size / 2
    corners = [start + side * sx * h + up * sz * h for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ends = [end + side * sx * h + up * sz * h for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    first = len(builder.polygons)
    for index in range(4):
        a, b = corners[index], corners[(index + 1) % 4]
        c, d = ends[(index + 1) % 4], ends[index]
        builder.oriented([a, b, c, d], ((a + b) / 2 - start), material)
    builder.tint(first, colour)


def scaffold(x0, x1, y, z0, z1, depth=1.2, bay=2.4, lift=2.0):
    builder = MeshBuilder()
    count = max(int((x1 - x0) / bay), 1)
    xs = [x0 + (x1 - x0) * k / count for k in range(count + 1)]
    for x in xs:
        for dy in (0.0, depth):
            beam(builder, (x, y + dy, z0 - 0.2), (x, y + dy, z1 + 1.0), 0.1, TIMBER)
    level = z0 + lift
    while level < z1 + 0.5:
        for dy in (0.0, depth):
            beam(builder, (x0, y + dy, level), (x1, y + dy, level), 0.08, TIMBER)
        for x in xs:
            beam(builder, (x, y, level), (x, y + depth, level), 0.07, TIMBER)
        tinted(builder, (0.52, 0.42, 0.30), lambda level=level: builder.box((x0, y + 0.05, level + 0.04),
                                                                            (x1, y + depth - 0.05, level + 0.1),
                                                                            MATTE))
        level += lift
    for a, b in zip(xs[:-1], xs[1:]):
        beam(builder, (a, y + depth, z0), (b, y + depth, min(z0 + lift * 2, z1)), 0.06, DARK_TIMBER)
    return builder


def block_pile(seed, count=7, colour=TUFF, material=STONE):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(count):
        x, y = rng.uniform(-2.0, 2.0), rng.uniform(-1.5, 1.5)
        sx, sy, sz = rng.uniform(0.7, 1.4), rng.uniform(0.5, 0.9), rng.uniform(0.45, 0.7)
        z = 0.0 if index < count * 0.7 else 0.6
        frame = placement(x, y, z, rng.uniform(-0.3, 0.3))
        tinted(builder, tuple(c * rng.uniform(0.85, 1.05) for c in colour),
               lambda frame=frame, sx=sx, sy=sy, sz=sz: builder.box((-sx / 2, -sy / 2, 0.0), (sx / 2, sy / 2, sz),
                                                                    material, matrix=frame, bottom=False))
    return builder


def drums(seed, count=4, diameter=0.8, colour=(0.95, 0.94, 0.9)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(count):
        frame = placement(index * 1.1 - count * 0.5, rng.uniform(-0.4, 0.4), diameter / 2, rng.uniform(-0.2, 0.2))
        frame = frame @ Matrix.Rotation(math.pi / 2, 4, "Y")
        tinted(builder, colour, lambda frame=frame: builder.lathe([(0.0, -0.5), (diameter / 2, -0.5),
                                                                   (diameter / 2, 0.5), (0.0, 0.5)], 12, "marble",
                                                                  smooth=False, matrix=frame))
    return builder


def portico_shell(length, depth, lower, upper, back=True, top=True):
    builder = MeshBuilder()
    hl = length / 2
    z1 = lower + 0.6
    tinted(builder, (0.95, 0.93, 0.88), lambda: builder.box((-hl, 0.0, -1.0), (hl, depth, 0.35), "floor_sheltered",
                                                            bottom=False))
    tinted(builder, STUCCO, lambda: builder.box((-hl, -0.25, lower), (hl, 0.45, z1), "plaster", bottom=False))
    tinted(builder, DARK_TIMBER, lambda: builder.box((-hl, 0.45, lower + 0.3), (hl, depth, lower + 0.42), MATTE,
                                                     top=False, bottom=True))
    if top:
        z2 = z1 + upper
        tinted(builder, STUCCO, lambda: builder.box((-hl, -0.15, z1), (hl, 0.15, z1 + 1.0), "plaster", bottom=False))
        tinted(builder, STUCCO, lambda: builder.box((-hl, -0.2, z2), (hl, 0.35, z2 + 0.45), "plaster", bottom=False))
        quad(builder, [(-hl - 0.2, -0.6, z2 + 0.4), (hl + 0.2, -0.6, z2 + 0.4), (hl + 0.2, depth + 0.3, z2 + 1.8),
                       (-hl - 0.2, depth + 0.3, z2 + 1.8)], (0, -1, 1), TILES)
        wall_top = z2 + 1.8
    else:
        quad(builder, [(-hl - 0.2, -0.6, z1), (hl + 0.2, -0.6, z1), (hl + 0.2, depth + 0.3, z1 + 1.2),
                       (-hl - 0.2, depth + 0.3, z1 + 1.2)], (0, -1, 1), TILES)
        wall_top = z1 + 1.2
    if back:
        tinted(builder, (0.97, 0.95, 0.9), lambda: builder.box((-hl, depth, -1.0), (hl, depth + 0.6, wall_top + 0.3),
                                                               "plaster", bottom=False))
        doors = max(int(length / 9.0), 1)
        for index in range(doors):
            x = -hl + length * (index + 0.5) / doors
            quad(builder, [(x - 1.1, depth - 0.01, 0.35), (x + 1.1, depth - 0.01, 0.35), (x + 1.1, depth - 0.01, 3.6),
                           (x - 1.1, depth - 0.01, 3.6)], (0, -1, 0), VOID)
    return builder


def portico_columns(length, spacing):
    count = max(int(length / spacing), 1)
    return [-length / 2 + length * (k + 0.5) / count for k in range(count)]


def temple_of_jupiter():
    builder = MeshBuilder()
    hw = 8.5
    rear, front = 70.5, 43.5
    height = 3.0
    tinted(builder, TUFF, lambda: builder.box((-hw, front, -2.0), (hw, rear, height), STONE, bottom=False))
    tinted(builder, STUCCO, lambda: builder.box((-hw - 0.15, front - 0.1, height - 0.35), (hw + 0.15, rear + 0.15,
                                                                                         height), "plaster",
                                                bottom=False))
    for k in range(6):
        z0, z1 = 1.6 + k * 0.233, 1.6 + (k + 1) * 0.233
        y0 = 37.5 + k * 1.0
        tinted(builder, (0.88, 0.86, 0.80), lambda y0=y0, z1=z1: builder.box((-hw, y0, 0.0), (hw, front, z1),
                                                                             "marble", bottom=False))
    tinted(builder, TUFF, lambda: builder.box((-4.5, 33.5, -1.0), (4.5, 37.5, 1.6), STONE, bottom=False))
    tinted(builder, (0.9, 0.88, 0.82), lambda: builder.box((-1.2, 34.3, 1.6), (1.2, 36.0, 2.6), "marble"))
    for side in (-1, 1):
        for k in range(7):
            y0 = 33.5 + k * 0.57
            z1 = (k + 1) * 0.229
            tinted(builder, (0.86, 0.84, 0.78), lambda y0=y0, z1=z1, side=side: builder.box(
                (min(side * 4.5, side * 7.2), y0, -0.5), (max(side * 4.5, side * 7.2), 37.5, z1), "marble",
                bottom=False))
        tinted(builder, TUFF, lambda side=side: builder.box((min(side * 7.2, side * hw), 33.5, -1.0),
                                                            (max(side * 7.2, side * hw), 37.5, 1.6), STONE,
                                                            bottom=False))
    floor = height
    top = floor + 8.6
    tinted(builder, STUCCO, lambda: builder.box((-6.6, 53.5, floor), (6.6, rear - 0.3, top), "plaster",
                                                bottom=False, top=False))
    quad(builder, [(-2.2, 53.49, floor), (2.2, 53.49, floor), (2.2, 53.49, floor + 6.8), (-2.2, 53.49, floor + 6.8)],
         (0, -1, 0), VOID)
    for crack in ((-4.6, floor + 2.0, -3.3, floor + 6.8), (5.2, floor + 1.0, 4.1, floor + 5.5)):
        x0, z0, x1, z1 = crack
        quad(builder, [(x0, 53.47, z0), (x0 + 0.08, 53.47, z0), (x1 + 0.08, 53.47, z1), (x1, 53.47, z1)], (0, -1, 0),
             MATTE, (0.25, 0.22, 0.2))
    tinted(builder, STUCCO, lambda: builder.box((-hw + 0.2, 43.8, top), (hw - 0.2, rear - 0.2, top + 1.5),
                                                "plaster", bottom=False))
    ridge = top + 1.5 + 2.4
    for side in (-1, 1):
        x_eave = side * (hw + 0.2)
        if side > 0:
            quad(builder, [(x_eave, 43.5, top + 1.5), (x_eave, 55.0, top + 1.5), (0.0, 55.0, ridge), (0.0, 43.5, ridge)],
                 (side, 0, 1), TILES)
            quad(builder, [(x_eave, 62.5, top + 1.5), (x_eave, rear, top + 1.5), (0.0, rear, ridge), (0.0, 62.5, ridge)],
                 (side, 0, 1), TILES)
            for y in (55.6, 57.2, 58.8, 60.4, 62.0):
                beam(builder, (0.0, y, ridge - 0.15), (x_eave, y, top + 1.4), 0.22, DARK_TIMBER)
        else:
            quad(builder, [(x_eave, 43.5, top + 1.5), (x_eave, rear, top + 1.5), (0.0, rear, ridge), (0.0, 43.5, ridge)],
                 (side, 0, 1), TILES)
    tinted(builder, STUCCO, lambda: builder.oriented([(-hw + 0.2, 43.8, top + 1.5), (hw - 0.2, 43.8, top + 1.5),
                                                      (0.0, 43.8, ridge - 0.1)], (0, -1, 0), "plaster"))
    quad(builder, [(-hw + 1.6, 43.75, top + 1.75), (hw - 1.6, 43.75, top + 1.75), (0.0, 43.75, ridge - 0.7)],
         (0, -1, 0), "plaster", (0.82, 0.78, 0.70))
    tinted(builder, STUCCO, lambda: builder.oriented([(hw - 0.2, rear - 0.2, top + 1.5), (-hw + 0.2, rear - 0.2,
                                                                                         top + 1.5),
                                                      (0.0, rear - 0.2, ridge - 0.1)], (0, 1, 0), "plaster"))
    builder.merge(scaffold(-6.4, 6.4, rear - 0.1, floor, top + 1.0, depth=1.3))
    for k in range(3):
        y = 56.0 + k * 5.0
        beam(builder, (-6.7, y, floor + 6.5), (-10.4, y, -0.4), 0.3, TIMBER)
        beam(builder, (-10.6, y - 0.5, -0.3), (-10.6, y + 0.5, -0.3), 0.3, DARK_TIMBER)
    return builder


def jupiter_columns():
    frames = []
    xs = [-7.2 + 14.4 * k / 5 for k in range(6)]
    for x in xs:
        frames.append((x, 45.2))
    for y in (48.4, 51.6):
        for x in (xs[0], xs[-1]):
            frames.append((x, y))
    return frames


def shoring_column(height):
    builder = MeshBuilder()
    for x, y in ((-0.45, -0.45), (0.45, -0.45), (0.45, 0.45), (-0.45, 0.45)):
        beam(builder, (x, y, 0.0), (x * 0.6, y * 0.6, height), 0.18, TIMBER)
    for z in (1.5, 4.0, 6.5):
        beam(builder, (-0.5, -0.5, z), (0.5, 0.5, z + 0.8), 0.1, DARK_TIMBER)
    tinted(builder, (0.88, 0.86, 0.80), lambda: builder.box((-0.6, -0.6, 0.0), (0.6, 0.6, 0.35), "marble"))
    return builder


def honorific_arch(width=6.4, depth=3.0, height=9.0, opening=3.0):
    builder = MeshBuilder()
    hw = width / 2
    for side in (-1, 1):
        tinted(builder, (0.93, 0.90, 0.84), lambda side=side: builder.box(
            (min(side * hw, side * opening / 2), -depth / 2, -1.0), (max(side * hw, side * opening / 2), depth / 2,
                                                                     height), "plaster", bottom=False))
    steps = 8
    spring = height - 3.2
    for k in range(steps):
        a0, a1 = math.pi * k / steps, math.pi * (k + 1) / steps
        x0, z0 = opening / 2 * math.cos(a0), spring + opening / 2 * math.sin(a0)
        x1, z1 = opening / 2 * math.cos(a1), spring + opening / 2 * math.sin(a1)
        for y, normal in ((-depth / 2, (0, -1, 0)), (depth / 2, (0, 1, 0))):
            quad(builder, [(x0, y, z0), (x1, y, z1), (x1, y, height), (x0, y, height)], normal, "plaster", STUCCO)
        quad(builder, [(x0, -depth / 2, z0), (x1, -depth / 2, z1), (x1, depth / 2, z1), (x0, depth / 2, z0)],
             (0, 0, -1), "plaster", (0.8, 0.78, 0.72))
    tinted(builder, (0.9, 0.88, 0.82), lambda: builder.box((-hw - 0.25, -depth / 2 - 0.25, height),
                                                           (hw + 0.25, depth / 2 + 0.25, height + 0.6), "marble"))
    return builder


def hall(width, depth, height, colour=STUCCO, roof_rise=None, door=3.0, along_y=True, material="plaster", roof=True):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    tinted(builder, colour, lambda: builder.box((-hw, -hd, -2.0), (hw, hd, height), material, bottom=False, top=False))
    rise = roof_rise if roof_rise is not None else min(width, depth) * 0.17
    if roof and along_y:
        for side in (-1, 1):
            quad(builder, [(side * (hw + 0.4), -hd - 0.4, height - 0.1), (side * (hw + 0.4), hd + 0.4, height - 0.1),
                           (0.0, hd + 0.4, height + rise), (0.0, -hd - 0.4, height + rise)], (side, 0, 1), TILES)
        for y, normal in ((-hd, (0, -1, 0)), (hd, (0, 1, 0))):
            tinted(builder, colour, lambda y=y, normal=normal: builder.oriented(
                [(-hw, y, height), (hw, y, height), (0.0, y, height + rise)], normal, material))
    elif roof:
        for side in (-1, 1):
            quad(builder, [(-hw - 0.4, side * (hd + 0.4), height - 0.1), (hw + 0.4, side * (hd + 0.4), height - 0.1),
                           (hw + 0.4, 0.0, height + rise), (-hw - 0.4, 0.0, height + rise)], (0, side, 1), TILES)
        for x, normal in ((-hw, (-1, 0, 0)), (hw, (1, 0, 0))):
            tinted(builder, colour, lambda x=x, normal=normal: builder.oriented(
                [(x, -hd, height), (x, hd, height), (x, 0.0, height + rise)], normal, material))
    if door:
        quad(builder, [(-door / 2, -hd - 0.01, 0.0), (door / 2, -hd - 0.01, 0.0), (door / 2, -hd - 0.01, door * 1.5),
                       (-door / 2, -hd - 0.01, door * 1.5)], (0, -1, 0), VOID)
    return builder


def court_ring(width, depth, wall, portico, height=4.2, colour=STUCCO, sides=(True, True, True, True)):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    edges = [((-hw, -hd), (hw, -hd), (0, -1)), ((hw, -hd), (hw, hd), (1, 0)), ((hw, hd), (-hw, hd), (0, 1)),
             ((-hw, hd), (-hw, -hd), (-1, 0))]
    for (a, b, n), keep in zip(edges, sides):
        a, b = Vector(a), Vector(b)
        normal = Vector(n)
        outer_a, outer_b = a + normal * 0.0, b + normal * 0.0
        tinted(builder, colour, lambda a=outer_a, b=outer_b, normal=normal: builder.oriented(
            [(a.x, a.y, -2.0), (b.x, b.y, -2.0), (b.x, b.y, wall), (a.x, a.y, wall)], (normal.x, normal.y, 0), "plaster"))
        tinted(builder, colour, lambda a=outer_a, b=outer_b, normal=normal: builder.oriented(
            [(a.x, a.y, -2.0), (b.x, b.y, -2.0), (b.x, b.y, wall), (a.x, a.y, wall)], (-normal.x, -normal.y, 0),
            "plaster"))
        if keep and portico > 0:
            inner_a = a - normal * portico + (b - a).normalized() * portico
            inner_b = b - normal * portico - (b - a).normalized() * portico
            quad(builder, [(a.x, a.y, wall + 0.3), (b.x, b.y, wall + 0.3), (inner_b.x, inner_b.y, height - 0.6),
                           (inner_a.x, inner_a.y, height - 0.6)], (-normal.x, -normal.y, 1.5), TILES)
    return builder


def apollo_precinct():
    builder = MeshBuilder()
    builder.merge(court_ring(34.0, 56.0, 5.6, 4.0, 5.0))
    tinted(builder, (0.82, 0.79, 0.72), lambda: builder.box((-17.0, -28.0, -1.0), (17.0, 28.0, 0.12), "paving",
                                                            bottom=False))
    temple, frames, column_height, diameter = arles_temple(width=12.0, length=24.0, column_height=7.2,
                                                           podium_height=2.4)
    shaft = columns_template("corinthian", diameter, column_height, "low")
    for frame in frames:
        temple.merge(shaft, frame)
    builder.merge(remap(temple), Matrix.Translation((0.0, 4.0, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"))
    tinted(builder, (0.9, 0.88, 0.82), lambda: builder.box((-1.4, -13.0, 0.0), (1.4, -11.4, 1.1), "marble"))
    tube(builder, [(0.0, -9.5, 0.0), (0.0, -9.5, 1.3)], [0.18, 0.15], (0.92, 0.9, 0.85), 10, "marble")
    return builder


def basilica():
    builder = MeshBuilder()
    builder.merge(hall(54.0, 24.0, 11.0, (0.94, 0.90, 0.82), along_y=False, door=0.0))
    for k in range(5):
        y = -8.0 + k * 4.0
        quad(builder, [(27.01, y - 1.2, 0.0), (27.01, y + 1.2, 0.0), (27.01, y + 1.2, 5.0), (27.01, y - 1.2, 5.0)],
             (1, 0, 0), VOID)
    for k in range(9):
        x = -24.0 + k * 6.0
        quad(builder, [(x - 0.8, -12.01, 7.5), (x + 0.8, -12.01, 7.5), (x + 0.8, -12.01, 9.6), (x - 0.8, -12.01, 9.6)],
             (0, -1, 0), VOID)
        quad(builder, [(x - 0.8, 12.01, 7.5), (x + 0.8, 12.01, 7.5), (x + 0.8, 12.01, 9.6), (x - 0.8, 12.01, 9.6)],
             (0, 1, 0), VOID)
    return builder


def equestrian_base(builder, length=3.0, width=1.4, height=2.2):
    hx, hy = width / 2, length / 2
    marble = (0.80, 0.78, 0.73)
    tinted(builder, marble, lambda: builder.box((-hx - 0.12, -hy - 0.12, -0.3), (hx + 0.12, hy + 0.12, 0.3), "marble",
                                                bottom=False))
    tinted(builder, marble, lambda: builder.box((-hx, -hy, 0.3), (hx, hy, height - 0.3), "marble", bottom=False,
                                                top=False))
    tinted(builder, marble, lambda: builder.box((-hx - 0.1, -hy - 0.1, height - 0.3), (hx + 0.1, hy + 0.1, height),
                                                "marble", bottom=False))


def equestrian_statue(seed=0):
    builder = MeshBuilder()
    equestrian_base(builder)
    bronze = (1.0, 1.0, 1.0)
    horse = arles_details.horse(bronze, "stand", seed)
    horse.polygon_colors = [bronze for _ in horse.polygon_colors]
    builder.merge(horse, Matrix.Translation((0.0, 0.0, 2.2)) @ Matrix.Scale(1.15, 4))
    rider = person(Look("white", hem=0.5, arms="gesture", cloak="white", mono=bronze, seed=40 + seed))
    builder.merge(rider, Matrix.Translation((0.0, -0.05, 2.2 + 0.62)) @ Matrix.Scale(1.15, 4))
    builder.materials = ["bronze" if name == MATTE else name for name in builder.materials]
    return remap(builder)


def standing_statue(bronze=True):
    return remap(nimes_figures.honorific_statue(bronze))


def venus_site():
    builder = MeshBuilder()
    for x0, x1, y0, y1, colour in ((-7.5, 7.5, -14.5, 14.5, (0.56, 0.52, 0.47)),):
        tinted(builder, colour, lambda: builder.box((x0, y0, -0.5), (x1, y1, 3.0), STONE, bottom=False))
    for side in (-1, 1):
        x = side * 9.0
        for k in range(9):
            y = -15.0 + k * 3.3
            if side > 0 and k > 5:
                continue
            tinted(builder, tuple(c * random.Random(k * 7 + side).uniform(0.85, 1.1) for c in BASALT),
                   lambda x=x, y=y: builder.box((x - 0.8, y, -1.5), (x + 0.8, y + 3.2, 1.2 + 0.3 * (k % 2)), STONE))
    for k in range(4):
        y = -16.6
        x = -7.0 + k * 3.4
        tinted(builder, BASALT, lambda x=x: builder.box((x, -17.4, -1.5), (x + 3.2, -15.8, 0.9), STONE))
    chapel = MeshBuilder()
    for x, y in ((-1.3, -1.6), (1.3, -1.6), (1.3, 1.6), (-1.3, 1.6)):
        beam(chapel, (x, y, 0.0), (x, y, 2.6), 0.16, TIMBER)
    tinted(chapel, (0.7, 0.62, 0.5), lambda: chapel.box((-1.4, -1.7, 0.0), (1.4, 1.7, 0.6), "plaster"))
    tinted(chapel, TIMBER, lambda: chapel.box((-1.35, 0.9, 0.6), (1.35, 1.65, 2.6), MATTE))
    for side in (-1, 1):
        quad(chapel, [(side * 1.8, -2.1, 2.5), (side * 1.8, 2.1, 2.5), (0.0, 2.1, 3.4), (0.0, -2.1, 3.4)],
             (side, 0, 1), TILES)
    tinted(chapel, (0.92, 0.88, 0.8), lambda: chapel.box((-0.35, -0.2, 0.6), (0.35, 0.3, 1.5), "marble"))
    builder.merge(chapel, Matrix.Translation((0.0, 9.0, 3.0)))
    tinted(builder, (0.92, 0.9, 0.85), lambda: builder.box((-0.9, -19.5, 0.0), (0.9, -18.3, 1.1), "marble"))
    builder.merge(drums(3, 5, 0.82), Matrix.Translation((-14.0, -4.0, 0.0)) @ Matrix.Rotation(1.2, 4, "Z"))
    builder.merge(drums(5, 3, 0.82), Matrix.Translation((14.5, 6.0, 0.0)) @ Matrix.Rotation(0.3, 4, "Z"))
    shaft = MeshBuilder()
    tinted(shaft, (0.96, 0.95, 0.92), lambda: shaft.lathe([(0.0, 0.0), (0.42, 0.0), (0.36, 7.6), (0.0, 7.6)], 14,
                                                         "marble", smooth=True))
    builder.merge(shaft, Matrix.Translation((-13.0, 10.0, 0.42)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    for k in range(4):
        beam(builder, (-14.0 + k * 0.6, 9.0, 0.05), (-14.0 + k * 0.6, 19.0, 0.05), 0.12, DARK_TIMBER)
    for seed, (x, y) in enumerate(((13.0, -12.0), (-14.0, -14.0), (12.0, 15.0))):
        builder.merge(block_pile(seed + 11, 8, (0.94, 0.93, 0.9), "marble"), Matrix.Translation((x, y, 0.0)))
    builder.merge(scaffold(-7.5, 7.5, -16.8, 0.0, 4.5, depth=1.2), Matrix.Identity(4))
    return builder


def venus_terrace(width=60.0, depth=56.0, drop=7.0):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    tinted(builder, (0.78, 0.74, 0.66), lambda: builder.box((-hw, -hd, -drop), (hw, hd, 0.0), "sidewalk",
                                                            bottom=False, top=True))
    for k in range(9):
        x = -hw + width * k / 8
        tinted(builder, TUFF, lambda x=x: builder.box((x - 0.9, -hd - 1.4, -drop - 1.0), (x + 0.9, -hd, -0.6), STONE,
                                                      bottom=False))
    for k in range(9):
        y = -hd + depth * k / 8
        tinted(builder, TUFF, lambda y=y: builder.box((-hw - 1.4, y - 0.9, -drop - 1.0), (-hw, y + 0.9, -0.6), STONE,
                                                      bottom=False))
    builder.merge(court_ring(width, depth, 4.2, 5.0, 4.8, sides=(False, True, True, False)))
    return builder


MARINA_PASSAGES = ((-3.9, 1.9, 4.0), (0.3, 4.2, 6.2))
MARINA_DEPTH = 21.0
MARINA_KERB = 0.38


def ramp_warp(builder, rise, depth, top, flat=7.0):
    warped = []
    for x, y, z in builder.positions:
        shift = rise * y / depth
        if z > flat:
            shift += (rise - shift) * min((z - flat) / (top - flat), 1.0)
        warped.append((x, y, z + shift))
    builder.positions = warped
    return builder


def porta_marina(rise=0.0):
    builder = MeshBuilder()
    width, depth, height = 15.0, MARINA_DEPTH, 11.0
    hw = width / 2
    passages = MARINA_PASSAGES
    (px, pw, _), (vx, vw, _) = passages
    tinted(builder, (0.86, 0.84, 0.80), lambda: builder.box((vx - vw / 2, -2.0, -0.8), (vx + vw / 2, depth + 0.6, 0.0),
                                                            "basalt", bottom=False))
    tinted(builder, (0.95, 0.93, 0.90), lambda: builder.box((px - pw / 2, -3.0, -0.8),
                                                            (px + pw / 2, depth + 0.6, MARINA_KERB), "sidewalk",
                                                            bottom=False))
    face = (0.64, 0.61, 0.55)
    xs = sorted([-hw, hw] + [x - w / 2 for x, w, _ in passages] + [x + w / 2 for x, w, _ in passages])
    for a, b in zip(xs[0::2], xs[1::2]):
        tinted(builder, face, lambda a=a, b=b: builder.box((a, 0.0, -8.0), (b, depth, height), STONE, bottom=False))
    for x, w, h in passages:
        steps = 10
        arch = [(x + w / 2 * math.cos(math.pi * k / steps), h - w / 2 + w / 2 * math.sin(math.pi * k / steps))
                for k in range(steps + 1)]
        for y, normal in ((0.0, (0, -1, 0)), (depth, (0, 1, 0))):
            for (ax, az), (bx, bz) in zip(arch[:-1], arch[1:]):
                quad(builder, [(ax, y, az), (bx, y, bz), (bx, y, height), (ax, y, height)], normal, STONE, face)
            offset = -0.03 if y == 0.0 else 0.03
            for (ax, az), (bx, bz) in zip(arch[:-1], arch[1:]):
                outer_a = (x + (ax - x) * 1.22, h - w / 2 + (az - h + w / 2) * 1.22)
                outer_b = (x + (bx - x) * 1.22, h - w / 2 + (bz - h + w / 2) * 1.22)
                quad(builder, [(ax, y + offset, az), (bx, y + offset, bz), (outer_b[0], y + offset, outer_b[1]),
                               (outer_a[0], y + offset, outer_a[1])], normal, STONE, (0.80, 0.76, 0.68))
        for (ax, az), (bx, bz) in zip(arch[:-1], arch[1:]):
            normal = (x - (ax + bx) / 2, 0.0, h - w / 2 - (az + bz) / 2)
            quad(builder, [(ax, 0.0, az), (bx, 0.0, bz), (bx, depth, bz), (ax, depth, az)], normal, STONE,
                 (0.40, 0.38, 0.35))
        for side in (-1, 1):
            beam(builder, (x + side * (w / 2 - 0.12), 0.6, -1.0), (x + side * (w / 2 - 0.12), 0.6, h - w / 2), 0.16,
                 DARK_TIMBER)
    tinted(builder, (0.82, 0.78, 0.70), lambda: builder.box((-hw - 0.35, -0.35, height), (hw + 0.35, depth + 0.35,
                                                                                         height + 0.55), STONE))
    for k in range(6):
        x = -hw + 0.6 + k * (width - 1.2) / 5
        tinted(builder, face, lambda x=x: builder.box((x - 0.5, -0.35, height + 0.55), (x + 0.5, 1.2, height + 1.8),
                                                      STONE))
    quad(builder, [(-1.0, depth + 0.02, 6.4), (0.0, depth + 0.02, 6.4), (0.0, depth + 0.02, 8.0),
                   (-1.0, depth + 0.02, 8.0)], (0, 1, 0), VOID)
    minerva = person(Look("white", hem=0.03, palla="white", female=True, sleeves="long", arms="gesture",
                          mono=(0.76, 0.48, 0.32), seed=77))
    builder.merge(minerva, Matrix.Translation((-0.5, depth - 0.15, 6.4)) @ Matrix.Scale(0.75, 4))
    return ramp_warp(builder, rise, depth, height)


def theatre(radius=31.0, rows=20):
    builder = remap(hillside_theatre(radius, rows, 9.0))
    tinted(builder, (0.93, 0.90, 0.84), lambda: builder.box((-radius + 4, -10.0, -2.0), (radius - 4, -5.0, 12.0),
                                                            "plaster", bottom=False))
    for side in (-1, 1):
        quad(builder, [(-radius + 3.5, side * 0.0 - 10.5 if side < 0 else -4.5, 12.0),
                       (radius - 3.5, -10.5 if side < 0 else -4.5, 12.0),
                       (radius - 3.5, -7.5, 13.6), (-radius + 3.5, -7.5, 13.6)], (0, side, 1), TILES)
    for k in range(5):
        x = -12.0 + k * 6.0
        quad(builder, [(x - 1.0, -4.99, 0.0), (x + 1.0, -4.99, 0.0), (x + 1.0, -4.99, 4.5), (x - 1.0, -4.99, 4.5)],
             (0, 1, 0), VOID)
    return builder


def amphitheatre():
    builder = remap(amphitheatre_cavea(17.5, 33.4, 52.0, 67.5, 9.0, rows=26, samples=56))
    ring = []
    for z in (-3.0, 9.6):
        ring.append([Vector((52.6 * math.cos(2 * math.pi * k / 56), 68.1 * math.sin(2 * math.pi * k / 56), z))
                     for k in range(56)])
    first = len(builder.polygons)
    builder.surface(ring, STONE, closed=True, facing=(1, 0, 0))
    builder.tint(first, TUFF)
    for k in range(0, 56, 4):
        angle = 2 * math.pi * k / 56
        x, y = 52.7 * math.cos(angle), 68.2 * math.sin(angle)
        normal = Vector((math.cos(angle) / 52.7, math.sin(angle) / 68.2)).normalized()
        tangent = Vector((-normal.y, normal.x))
        a = Vector((x, y)) + tangent * 1.3
        b = Vector((x, y)) - tangent * 1.3
        quad(builder, [(a.x, a.y, 0.0), (b.x, b.y, 0.0), (b.x, b.y, 4.2), (a.x, a.y, 4.2)], (normal.x, normal.y, 0),
             VOID)
    return builder


def palaestra():
    builder = MeshBuilder()
    builder.merge(court_ring(141.0, 107.0, 5.0, 6.0, 6.2, sides=(True, True, True, False)))
    tinted(builder, (0.10, 0.18, 0.2), lambda: builder.polygon([(-17.5, -11.0, -0.6), (17.5, -11.0, -0.6),
                                                                (17.5, 11.0, -0.6), (-17.5, 11.0, -0.6)], "water"))
    tinted(builder, (0.85, 0.83, 0.78), lambda: builder.box((-18.2, -11.7, -1.6), (18.2, -11.0, 0.15), "marble"))
    tinted(builder, (0.85, 0.83, 0.78), lambda: builder.box((-18.2, 11.0, -1.6), (18.2, 11.7, 0.15), "marble"))
    tinted(builder, (0.85, 0.83, 0.78), lambda: builder.box((-18.2, -11.0, -1.6), (-17.5, 11.0, 0.15), "marble"))
    tinted(builder, (0.85, 0.83, 0.78), lambda: builder.box((17.5, -11.0, -1.6), (18.2, 11.0, 0.15), "marble"))
    return builder


def bath_block(width, depth, seed, open_roof=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    x = -width / 2
    while x < width / 2 - 4.0:
        span = min(rng.uniform(9.0, 14.0), width / 2 - x)
        height = rng.uniform(7.5, 11.0)
        colour = (0.78, 0.66, 0.54) if open_roof else (0.95, 0.90, 0.80)
        piece = hall(span, depth * 0.55, height, colour, door=0.0, along_y=False, roof=not open_roof)
        builder.merge(piece, Matrix.Translation((x + span / 2, depth * 0.2, 0.0)))
        x += span
    builder.merge(court_ring(width, depth * 0.4, 3.5, 3.5, 4.2, sides=(True, True, False, True)),
                  Matrix.Translation((0.0, -depth * 0.3, 0.0)))
    if open_roof:
        builder.merge(scaffold(-width / 2 + 2.0, -width / 2 + 14.0, depth * 0.2 - depth * 0.275 - 1.4, 0.0, 8.0))
    return builder


def triangular_forum():
    builder = MeshBuilder()
    for k in range(3):
        tinted(builder, TUFF, lambda k=k: builder.box((-7.0 + k * 0.4, -10.0 + k * 0.4, k * 0.4),
                                                      (7.0 - k * 0.4, 10.0 - k * 0.4, (k + 1) * 0.4), STONE))
    for x in (-5.5, -1.8, 1.8, 5.5):
        tube(builder, [(x, -8.4, 1.2), (x, -8.4, 1.2 + (2.2 if x < 0 else 0.9))], [0.55, 0.5], TUFF, 10, STONE)
    builder.merge(portico_shell(70.0, 5.0, 4.0, 0.0, back=True, top=False),
                  Matrix.Translation((-14.0, 0.0, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    return builder


def house_vettii():
    builder = MeshBuilder()
    floor = 0.25
    wall = (0.96, 0.93, 0.86)
    outer = (-22.0, 22.0, 0.0, 34.0)
    x0, x1, y0, y1 = outer
    tinted(builder, wall, lambda: builder.box((x0, y0, -2.0), (x1, y1, 7.2), "plaster", bottom=False, top=False))
    quad(builder, [(-1.3, -0.01, 0.0), (1.3, -0.01, 0.0), (1.3, -0.01, 3.9), (-1.3, -0.01, 3.9)], (0, -1, 0), VOID)
    for side in (-1, 1):
        quad(builder, [(side * 1.3, -0.02, 0.0), (side * 2.4, -0.02, 0.0), (side * 2.4, -0.02, 3.9),
                       (side * 1.3, -0.02, 3.9)], (0, -1, 0), MATTE, (0.36, 0.26, 0.17))
    tinted(builder, (0.62, 0.16, 0.11), lambda: builder.polygon([(x0, -0.02, 0.0), (x1, -0.02, 0.0),
                                                                 (x1, -0.02, 1.0), (x0, -0.02, 1.0)], "plaster"))
    impluvium_hole = (-2.3, 2.3, 9.1, 13.9)
    garden_hole = (-10.9, 10.9, 21.1, 30.4)
    tinted(builder, (0.42, 0.40, 0.37), lambda: builder.box((x0 + 0.3, y0 + 0.3, -0.5), (x1 - 0.3, y1 - 0.3, floor),
                                                            "sidewalk", bottom=False, top=False))
    floor_with_holes(builder, (x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3), [impluvium_hole, garden_hole], floor,
                     "floor_sheltered", (0.66, 0.62, 0.56))
    floor_with_holes(builder, (-6.0, 6.0, 4.6, 18.0), [impluvium_hole], floor + 0.01, "floor_sheltered",
                     (1.0, 0.72, 0.62))
    fresco_room(builder, -6.0, 6.0, 4.6, 18.0, floor, 7.4, open_side="back", door_front=(-1.3, 1.3))
    tinted(builder, (0.30, 0.26, 0.22), lambda: builder.box((-1.3, 0.0, floor - 0.02), (1.3, 4.6, floor + 0.01),
                                                            "sidewalk", bottom=False))
    for side in (-1, 1):
        fresco_face(builder, (side * 1.3, 0.0), (side * 1.3, 4.6), floor, floor + 4.6, 0.0, 4.0, (-side, 0))
    quad(builder, [(-1.3, 0.0, floor + 4.6), (1.3, 0.0, floor + 4.6), (1.3, 4.6, floor + 4.6), (-1.3, 4.6, floor + 4.6)],
         (0, 0, -1), MATTE, DARK_TIMBER)
    impluvium(builder, -2.0, 2.0, 9.4, 13.6, floor)
    for x in (-4.6, 4.6):
        tinted(builder, (0.82, 0.80, 0.74), lambda x=x: builder.box((x - 0.6, 14.6, floor), (x + 0.6, 15.6, floor + 0.5),
                                                                    "marble"))
        tinted(builder, (0.40, 0.28, 0.17), lambda x=x: builder.box((x - 0.55, 14.65, floor + 0.5),
                                                                    (x + 0.55, 15.55, floor + 1.25), MATTE))
        for z in (floor + 0.7, floor + 1.05):
            tinted(builder, (0.62, 0.48, 0.24), lambda x=x, z=z: builder.box((x - 0.57, 14.62, z), (x + 0.57, 15.58,
                                                                                                   z + 0.06), MATTE))
    builder.merge(remap(compluviate_atrium()), Matrix.Translation((0.0, 0.0, 0.0)))
    peristyle(builder, floor)
    for x_a, x_b, y_a, y_b in ((-22.0, -6.0, 0.0, 18.0), (6.0, 22.0, 0.0, 18.0)):
        mid = (x_a + x_b) / 2
        for side in (-1, 1):
            xa = x_a if side < 0 else x_b
            quad(builder, [(xa + side * 0.3, y_a - 0.4, 7.0), (xa + side * 0.3, y_b, 7.0), (mid, y_b, 8.6),
                           (mid, y_a - 0.4, 8.6)], (side, 0, 1), TILES)
    for x_a, x_b in ((-22.0, -14.0), (14.0, 22.0)):
        mid = (x_a + x_b) / 2
        for side in (-1, 1):
            xa = x_a if side < 0 else x_b
            quad(builder, [(xa + side * 0.3, 18.0, 6.6), (xa + side * 0.3, y1 + 0.4, 6.6), (mid, y1 + 0.4, 8.0),
                           (mid, 18.0, 8.0)], (side, 0, 1), TILES)
    for y_a, y_b in ((30.0, 34.0),):
        quad(builder, [(-14.0, y_b + 0.4, 6.6), (14.0, y_b + 0.4, 6.6), (14.0, y_a, 7.8), (-14.0, y_a, 7.8)],
             (0, 1, 1), TILES)
    return builder


def floor_with_holes(builder, rect, holes, z, material, colour):
    x0, x1, y0, y1 = rect
    xs = sorted({x0, x1} | {value for hole in holes for value in hole[:2] if x0 < value < x1})
    ys = sorted({y0, y1} | {value for hole in holes for value in hole[2:] if y0 < value < y1})
    first = len(builder.polygons)
    for xa, xb in zip(xs[:-1], xs[1:]):
        for ya, yb in zip(ys[:-1], ys[1:]):
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            if any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in holes):
                continue
            builder.polygon([(xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z)], material)
    builder.tint(first, colour)


def basin_walls(builder, x0, x1, y0, y1, bottom, top, material, colour):
    first = len(builder.polygons)
    for (ax, ay), (bx, by), normal in (((x0, y0), (x1, y0), (0, 1, 0)), ((x1, y0), (x1, y1), (-1, 0, 0)),
                                       ((x1, y1), (x0, y1), (0, -1, 0)), ((x0, y1), (x0, y0), (1, 0, 0))):
        builder.oriented([(ax, ay, bottom), (bx, by, bottom), (bx, by, top), (ax, ay, top)], normal, material)
    builder.tint(first, colour)


def fresco_room(builder, x0, x1, y0, y1, floor, height, open_side=None, door_front=None):
    band = 4.0
    upper = 5.2
    cornice = 0.25
    attic = (0.62, 0.40, 0.25)
    walls = [((x0, y0), (x1, y0), (0, 1)), ((x1, y0), (x1, y1), (-1, 0)), ((x1, y1), (x0, y1), (0, -1)),
             ((x0, y1), (x0, y0), (1, 0))]
    names = ["front", "right", "back", "left"]
    for ((ax, ay), (bx, by), normal), name in zip(walls, names):
        length = math.hypot(bx - ax, by - ay)
        if name == open_side:
            opening = 4.0
            cut = [(0.0, (length - opening) / 2), ((length + opening) / 2, length)]
            upper_wall(builder, (ax, ay), (bx, by), normal, floor, band, upper, cornice, height, attic)
        elif name == "front" and door_front is not None:
            centre = length / 2
            cut = [(0.0, centre - (door_front[1] - door_front[0]) / 2),
                   (centre + (door_front[1] - door_front[0]) / 2, length)]
        else:
            cut = [(0.0, length)]
        for s0, s1 in cut:
            pa = (ax + (bx - ax) * s0 / length, ay + (by - ay) * s0 / length)
            pb = (ax + (bx - ax) * s1 / length, ay + (by - ay) * s1 / length)
            corners = [(pa[0], pa[1], floor), (pb[0], pb[1], floor), (pb[0], pb[1], floor + band),
                       (pa[0], pa[1], floor + band)]
            uvs = [(s0, 0.0), (s1, 0.0), (s1, band), (s0, band)]
            indices = builder.points(corners)
            facing = Vector(normal + (0,))
            test = (Vector(corners[1]) - Vector(corners[0])).cross(Vector(corners[3]) - Vector(corners[0]))
            if test.dot(facing) < 0:
                indices = list(reversed(indices))
                uvs = list(reversed(uvs))
            builder.face(indices, "fresco", uvs=uvs)
        if name != open_side:
            upper_wall(builder, (ax, ay), (bx, by), normal, floor, band, upper, cornice, height, attic)
        if name in ("left", "right"):
            for door in (y0 + 2.6, y0 + 6.2):
                along = abs(door - ay) if name == "left" else abs(door - ay)
                point = (ax + (bx - ax) * along / length, ay + (by - ay) * along / length)
                n = Vector(normal + (0,))
                quad(builder, [(point[0] + n.x * 0.01, point[1] - 0.9, floor), (point[0] + n.x * 0.01, point[1] + 0.9,
                                                                                 floor),
                               (point[0] + n.x * 0.01, point[1] + 0.9, floor + 3.0),
                               (point[0] + n.x * 0.01, point[1] - 0.9, floor + 3.0)], normal + (0,), VOID)


def fresco_face(builder, a, b, z0, z1, v0, v1, normal):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    corners = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)]
    uvs = [(0.0, v0), (length, v0), (length, v1), (0.0, v1)]
    indices = builder.points(corners)
    test = (Vector(corners[1]) - Vector(corners[0])).cross(Vector(corners[3]) - Vector(corners[0]))
    if test.dot(Vector(tuple(normal) + (0,))) < 0:
        indices = list(reversed(indices))
        uvs = list(reversed(uvs))
    builder.face(indices, "fresco", uvs=uvs)


def upper_wall(builder, a, b, normal, floor, band, upper, cornice, height, attic):
    fresco_face(builder, a, b, floor + band, floor + upper, 3.2, 4.0, normal)
    quad(builder, [(a[0], a[1], floor + upper + cornice), (b[0], b[1], floor + upper + cornice),
                   (b[0], b[1], floor + height), (a[0], a[1], floor + height)], normal + (0,), "plaster", attic)
    out_a = Vector(a) + Vector(normal) * 0.14
    out_b = Vector(b) + Vector(normal) * 0.14
    stucco = (0.88, 0.85, 0.78)
    quad(builder, [(out_a.x, out_a.y, floor + upper + 0.06), (out_b.x, out_b.y, floor + upper + 0.06),
                   (out_b.x, out_b.y, floor + upper + cornice), (out_a.x, out_a.y, floor + upper + cornice)],
         normal + (0,), "plaster", stucco)
    quad(builder, [(a[0], a[1], floor + upper), (b[0], b[1], floor + upper), (out_b.x, out_b.y, floor + upper + 0.06),
                   (out_a.x, out_a.y, floor + upper + 0.06)], (normal[0], normal[1], -1.0), "plaster",
         tuple(c * 0.8 for c in stucco))
    quad(builder, [(a[0], a[1], floor + upper + cornice), (b[0], b[1], floor + upper + cornice),
                   (out_b.x, out_b.y, floor + upper + cornice), (out_a.x, out_a.y, floor + upper + cornice)],
         (0, 0, 1), "plaster", stucco)


def impluvium(builder, x0, x1, y0, y1, floor):
    tinted(builder, (0.93, 0.92, 0.88), lambda: builder.box((x0 - 0.3, y0 - 0.3, floor - 0.3), (x1 + 0.3, y1 + 0.3,
                                                                                               floor + 0.12),
                                                            "marble", bottom=False, top=False))
    for a, b in (((x0 - 0.3, y0 - 0.3), (x1 + 0.3, y0)), ((x0 - 0.3, y1), (x1 + 0.3, y1 + 0.3)),
                 ((x0 - 0.3, y0), (x0, y1)), ((x1, y0), (x1 + 0.3, y1))):
        tinted(builder, (0.93, 0.92, 0.88), lambda a=a, b=b: builder.polygon(
            [(a[0], a[1], floor + 0.12), (b[0], a[1], floor + 0.12), (b[0], b[1], floor + 0.12),
             (a[0], b[1], floor + 0.12)], "marble"))
    basin_walls(builder, x0, x1, y0, y1, floor - 0.3, floor + 0.12, "marble", (0.80, 0.78, 0.74))
    tinted(builder, (0.12, 0.16, 0.16), lambda: builder.polygon([(x0, y0, floor - 0.06), (x1, y0, floor - 0.06),
                                                                 (x1, y1, floor - 0.06), (x0, y1, floor - 0.06)],
                                                                "water"))
    drape(builder, (0.72, 0.70, 0.64), [(1.25, floor - 0.08), (0.95, floor - 0.01), (0.5, floor + 0.07),
                                        (0.0, floor + 0.11)], 12, folds=(6, 0.16, 0.3), squash=1.15,
          center=((x0 + x1) / 2 + 0.2, (y0 + y1) / 2 - 0.3), material=MATTE)
    rng = random.Random(4)
    for _ in range(36):
        x = rng.uniform(x0 + 0.1, x1 - 0.1)
        y = rng.uniform(y0 + 0.1, y1 - 0.1)
        ellipsoid(builder, (x, y, floor - 0.055), (0.04, 0.035, 0.02), (0.80, 0.78, 0.72), 4, 2, MATTE)
    for _ in range(40):
        x = rng.uniform(x0 - 1.8, x1 + 1.8)
        y = rng.uniform(y0 - 1.8, y1 + 1.8)
        if x0 - 0.3 < x < x1 + 0.3 and y0 - 0.3 < y < y1 + 0.3:
            continue
        ellipsoid(builder, (x, y, floor + 0.02), (0.035, 0.03, 0.025), (0.86, 0.84, 0.78), 4, 2, MATTE)


def compluviate_atrium():
    builder = MeshBuilder()
    compluviate_roof(builder, -6.0, 6.0, 4.6, 18.0, 7.6, 0.32)
    keep = [index for index, material in enumerate(builder.polygon_materials)
            if builder.materials[material] != VOID and builder.materials[material] != MATTE]
    trimmed = MeshBuilder()
    for index in keep:
        indices = builder.polygons[index]
        corners = [builder.positions[i] for i in indices]
        trimmed.face(trimmed.points(corners), builder.materials[builder.polygon_materials[index]],
                     color=builder.polygon_colors[index])
        below = [(x, y, z - 0.12) for x, y, z in reversed(corners)]
        trimmed.face(trimmed.points(below), MATTE, color=(0.30, 0.22, 0.16))
    for y in (4.6, 18.0):
        quad(trimmed, [(-6.0, y, 7.2), (6.0, y, 7.2), (6.0, y, 7.9), (-6.0, y, 7.9)], (0, 1 if y < 10 else -1, 0),
             "plaster", (0.94, 0.9, 0.82))
    for k in range(5):
        x = -5.0 + k * 2.5
        beam(trimmed, (x, 4.6, 7.3), (x, 18.0, 7.3), 0.16, DARK_TIMBER)
    return trimmed


def peristyle(builder, floor):
    gx0, gx1, gy0, gy1 = -10.5, 10.5, 21.5, 30.0
    px0, px1, py0, py1 = -14.0, 14.0, 18.0, 33.5
    tinted(builder, (0.34, 0.31, 0.20), lambda: builder.box((gx0, gy0, floor - 0.6), (gx1, gy1, floor - 0.25),
                                                            MATTE, bottom=False))
    tinted(builder, (0.82, 0.80, 0.76), lambda: builder.box((gx0 - 0.4, gy0 - 0.4, floor - 0.6), (gx1 + 0.4, gy1 + 0.4,
                                                                                                 floor + 0.1),
                                                            "marble", bottom=False, top=False))
    floor_with_holes(builder, (gx0 - 0.4, gx1 + 0.4, gy0 - 0.4, gy1 + 0.4), [(gx0, gx1, gy0, gy1)], floor + 0.1,
                     "marble", (0.82, 0.80, 0.76))
    basin_walls(builder, gx0, gx1, gy0, gy1, floor - 0.25, floor + 0.1, "marble", (0.70, 0.68, 0.64))
    floor_with_holes(builder, (px0, px1, py0, py1), [(gx0 - 0.4, gx1 + 0.4, gy0 - 0.4, gy1 + 0.4)], floor + 0.01,
                     "floor_sheltered", (1.0, 0.72, 0.62))
    for (ax, ay), (bx, by), normal in (((px0, py0), (px1, py0), (0, 1)), ((px1, py0), (px1, py1), (-1, 0)),
                                       ((px1, py1), (px0, py1), (0, -1)), ((px0, py1), (px0, py0), (1, 0))):
        if normal == (0, 1):
            for x_a, x_b in ((px0, -2.0), (2.0, px1)):
                fresco_strip(builder, (x_a, ay), (x_b, by), normal, floor, 6.2)
            continue
        fresco_strip(builder, (ax, ay), (bx, by), normal, floor, 6.2)
    for (ax, ay), (bx, by), normal in (((gx0 - 0.6, gy0 - 0.6), (gx1 + 0.6, gy0 - 0.6), (0, -1)),
                                       ((gx1 + 0.6, gy0 - 0.6), (gx1 + 0.6, gy1 + 0.6), (1, 0)),
                                       ((gx1 + 0.6, gy1 + 0.6), (gx0 - 0.6, gy1 + 0.6), (0, 1)),
                                       ((gx0 - 0.6, gy1 + 0.6), (gx0 - 0.6, gy0 - 0.6), (-1, 0))):
        outer_a = Vector((ax, ay)) + Vector(normal) * 3.0
        outer_b = Vector((bx, by)) + Vector(normal) * 3.0
        quad(builder, [(ax, ay, 4.4), (bx, by, 4.4), (outer_b.x, outer_b.y, 5.9), (outer_a.x, outer_a.y, 5.9)],
             (-normal[0], -normal[1], 2.0), TILES)
        quad(builder, [(ax, ay, 4.3), (bx, by, 4.3), (outer_b.x, outer_b.y, 5.8), (outer_a.x, outer_a.y, 5.8)],
             (normal[0], normal[1], -2.0), MATTE, DARK_TIMBER)
        tinted(builder, STUCCO, lambda ax=ax, ay=ay, bx=bx, by=by: builder.box(
            (min(ax, bx) - 0.2, min(ay, by) - 0.2, 4.15), (max(ax, bx) + 0.2, max(ay, by) + 0.2, 4.45), "plaster"))


def fresco_strip(builder, a, b, normal, floor, height):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    corners = [(a[0], a[1], floor), (b[0], b[1], floor), (b[0], b[1], floor + 4.0), (a[0], a[1], floor + 4.0)]
    uvs = [(0.0, 0.0), (length, 0.0), (length, 4.0), (0.0, 4.0)]
    indices = builder.points(corners)
    test = (Vector(corners[1]) - Vector(corners[0])).cross(Vector(corners[3]) - Vector(corners[0]))
    if test.dot(Vector(normal + (0,))) < 0:
        indices = list(reversed(indices))
        uvs = list(reversed(uvs))
    builder.face(indices, "fresco", uvs=uvs)
    quad(builder, [(a[0], a[1], floor + 4.0), (b[0], b[1], floor + 4.0), (b[0], b[1], floor + height),
                   (a[0], a[1], floor + height)], normal + (0,), "plaster", (0.95, 0.92, 0.84))
    count = max(int(length / 4.5), 1)
    for k in range(count):
        s = (k + 0.5) / count
        p = (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)
        tangent = Vector(((b[0] - a[0]) / length, (b[1] - a[1]) / length))
        n = Vector(normal)
        c = Vector(p) + n * 0.01
        quad(builder, [(c.x - tangent.x * 0.9, c.y - tangent.y * 0.9, floor), (c.x + tangent.x * 0.9,
                                                                                c.y + tangent.y * 0.9, floor),
                       (c.x + tangent.x * 0.9, c.y + tangent.y * 0.9, floor + 3.1),
                       (c.x - tangent.x * 0.9, c.y - tangent.y * 0.9, floor + 3.1)], normal + (0,), VOID)


def peristyle_columns():
    gx0, gx1, gy0, gy1 = -10.5, 10.5, 21.5, 30.0
    frames = []
    for k in range(9):
        x = gx0 - 0.6 + (gx1 - gx0 + 1.2) * k / 8
        frames.append((x, gy0 - 0.6))
        frames.append((x, gy1 + 0.6))
    for k in range(1, 4):
        y = gy0 - 0.6 + (gy1 - gy0 + 1.2) * k / 4
        frames.append((gx0 - 0.6, y))
        frames.append((gx1 + 0.6, y))
    return frames


def garden_props(seed=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    floor = 0.25
    for x0, x1, y0, y1 in ((-9.8, -1.2, 22.2, 25.0), (1.2, 9.8, 22.2, 25.0), (-9.8, -1.2, 26.5, 29.3),
                           (1.2, 9.8, 26.5, 29.3)):
        tinted(builder, (0.24, 0.34, 0.16), lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box(
            (x0, y0, floor - 0.3), (x1, y0 + 0.4, floor + 0.35), MATTE))
        tinted(builder, (0.24, 0.34, 0.16), lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box(
            (x0, y1 - 0.4, floor - 0.3), (x1, y1, floor + 0.35), MATTE))
        for k in range(5):
            x = rng.uniform(x0 + 0.5, x1 - 0.5)
            y = rng.uniform(y0 + 0.7, y1 - 0.7)
            drape(builder, rng.choice([(0.30, 0.40, 0.20), (0.62, 0.22, 0.18), (0.80, 0.70, 0.30)]),
                  [(0.25, floor - 0.25), (0.32, floor + 0.15), (0.0, floor + 0.45)], 6, folds=(4, 0.12, k),
                  squash=1.0, center=(x, y), material=MATTE)
    for x, y in ((-5.5, 25.75), (5.5, 25.75), (0.0, 25.75)):
        tinted(builder, (0.93, 0.92, 0.88), lambda x=x, y=y: builder.lathe(
            [(0.0, floor - 0.25), (0.75, floor - 0.25), (0.75, floor + 0.25), (0.65, floor + 0.25),
             (0.65, floor + 0.05), (0.0, floor + 0.05)], 14, "marble", smooth=False,
            matrix=Matrix.Translation((x, y, 0.0))))
        tinted(builder, (0.12, 0.17, 0.17), lambda x=x, y=y: builder.polygon(
            [(x + 0.64 * math.cos(2 * math.pi * k / 12), y + 0.64 * math.sin(2 * math.pi * k / 12), floor + 0.12)
             for k in range(12)], "water"))
        tube(builder, [(x, y, floor + 0.1), (x, y, floor + 0.9)], [0.07, 0.05], (0.92, 0.9, 0.85), 6, "marble")
    for x, y in ((-8.0, 23.4), (8.0, 23.4), (-8.0, 28.1), (8.0, 28.1), (-3.0, 23.4), (3.0, 28.1)):
        tinted(builder, (0.93, 0.92, 0.88), lambda x=x, y=y: builder.box((x - 0.2, y - 0.2, floor), (x + 0.2, y + 0.2,
                                                                                                     floor + 1.0),
                                                                         "marble"))
        cupid = person(Look("white", hem=0.5, child=True, scale=0.42, arms="gesture",
                            mono=(0.95, 0.94, 0.9), seed=int(x * 7 + y)))
        builder.merge(remap(cupid), Matrix.Translation((x, y, floor + 1.0)))
    for _ in range(90):
        x = rng.uniform(-10.0, 10.0)
        y = rng.uniform(22.0, 29.5)
        ellipsoid(builder, (x, y, floor - 0.22), (0.05, 0.04, 0.03), (0.86, 0.84, 0.78), 4, 2, MATTE)
    return builder


def thermopolium(seed=8):
    rng = random.Random(seed)
    builder = MeshBuilder()
    width, depth, height = 11.0, 14.0, 7.4
    x0, x1 = -width / 2, width / 2
    wall = (0.96, 0.93, 0.86)
    open_a, open_b = -5.0, -0.2
    for (ax, ay), (bx, by), normal in (((x1, 0.0), (x1, depth), (1, 0, 0)), ((x1, depth), (x0, depth), (0, 1, 0)),
                                       ((x0, depth), (x0, 0.0), (-1, 0, 0))):
        quad(builder, [(ax, ay, -2.5), (bx, by, -2.5), (bx, by, height), (ax, ay, height)], normal, "plaster", wall)
    for a, b, z0, z1 in ((x0, open_a, -2.5, height), (open_b, x1, -2.5, height), (open_a, open_b, 3.4, height)):
        quad(builder, [(a, 0.0, z0), (b, 0.0, z0), (b, 0.0, z1), (a, 0.0, z1)], (0, -1, 0), "plaster", wall)
    tinted(builder, (0.97, 0.94, 0.88), lambda: builder.box((open_a, 0.0, 0.0), (open_b, 6.5, 0.02), "sidewalk"))
    for x_a, x_b in ((open_a, open_a + 0.05), (open_b - 0.05, open_b)):
        quad(builder, [(x_a, 0.0, 0.0), (x_a, 6.5, 0.0), (x_a, 6.5, 3.4), (x_a, 0.0, 3.4)],
             (1 if x_a == open_a else -1, 0, 0), "plaster", (0.92, 0.88, 0.80))
    quad(builder, [(open_a, 6.5, 0.0), (open_b, 6.5, 0.0), (open_b, 6.5, 3.4), (open_a, 6.5, 3.4)], (0, -1, 0),
         "plaster", (0.92, 0.88, 0.80))
    quad(builder, [(open_a, 0.0, 3.4), (open_b, 0.0, 3.4), (open_b, 6.5, 3.4), (open_a, 6.5, 3.4)], (0, 0, -1),
         MATTE, DARK_TIMBER)
    tinted(builder, (0.45, 0.32, 0.22), lambda: builder.box((open_a - 0.1, -0.12, 2.9), (open_b + 0.1, 0.05, 3.4),
                                                            MATTE))
    counter_front = 0.1
    tinted(builder, (0.78, 0.76, 0.71), lambda: builder.box((open_a + 0.1, counter_front, 0.0),
                                                            (open_b - 1.0, counter_front + 0.75, 1.0), "marble"))
    tinted(builder, (0.78, 0.76, 0.71), lambda: builder.box((open_b - 1.75, counter_front, 0.0),
                                                            (open_b - 1.0, 5.2, 1.0), "marble"))
    xa, xb = open_a + 0.1, open_b - 1.0
    builder.face(builder.points([(xa, counter_front - 0.01, 0.05), (xb, counter_front - 0.01, 0.05),
                                 (xb, counter_front - 0.01, 0.95), (xa, counter_front - 0.01, 0.95)]), "crustae",
                 uvs=[(xa, 0.05), (xb, 0.05), (xb, 0.95), (xa, 0.95)])
    side = open_b - 1.76
    builder.face(builder.points([(side, 5.15, 0.05), (side, counter_front + 0.76, 0.05),
                                 (side, counter_front + 0.76, 0.95), (side, 5.15, 0.95)]), "crustae",
                 uvs=[(5.15, 0.05), (counter_front + 0.76, 0.05), (counter_front + 0.76, 0.95), (5.15, 0.95)])
    for k in range(3):
        cx = open_a + 0.8 + k * 1.05
        dolium_mouth(builder, cx, counter_front + 0.375, 1.0)
    dolium_mouth(builder, open_b - 1.375, 3.4, 1.0)
    for level in range(3):
        z = 0.6 + level * 0.4
        tinted(builder, (0.78, 0.74, 0.68), lambda z=z, level=level: builder.box(
            (open_a + 0.2, 5.6 - level * 0.3, 0.0), (open_a + 2.0, 6.5, z), "plaster"))
        for k in range(4):
            px = open_a + 0.4 + k * 0.42
            drape(builder, (0.70, 0.42, 0.28), [(0.0, z), (0.09, z + 0.05), (0.1, z + 0.18), (0.04, z + 0.3),
                                                (0.045, z + 0.36), (0.0, z + 0.36)], 6, folds=(0, 0.0, 0.0),
                  squash=1.0, center=(px, 6.2 - level * 0.3), material=MATTE)
    lx, lz = -1.6, 1.4
    face = [(lx - 1.0, 6.49, lz), (lx + 1.0, 6.49, lz), (lx + 1.0, 6.49, lz + 1.4), (lx - 1.0, 6.49, lz + 1.4)]
    builder.face(builder.points(face), "fresco", uvs=[(2.4, 1.0), (3.6, 1.0), (3.6, 2.9), (2.4, 2.9)])
    tinted(builder, (0.96, 0.94, 0.88), lambda: builder.oriented([(lx - 1.25, 6.45, lz + 1.4), (lx + 1.25, 6.45,
                                                                                               lz + 1.4),
                                                                  (lx, 6.45, lz + 2.0)], (0, -1, 0), "plaster"))
    for side in (-1, 1):
        tinted(builder, (0.96, 0.94, 0.88), lambda side=side: builder.box((lx + side * 1.1 - 0.08, 6.38, lz),
                                                                          (lx + side * 1.1 + 0.08, 6.5, lz + 1.4),
                                                                          "plaster"))
    for k in range(5):
        px = open_b + 0.15 + k * 0.05
        beam(builder, (px + 0.6, -0.35, 0.0), (px + 0.2, -0.08, 2.6), 0.07, (0.40, 0.29, 0.19))
    door = 2.6
    quad(builder, [(door - 0.9, -0.01, 0.0), (door + 0.9, -0.01, 0.0), (door + 0.9, -0.01, 3.1), (door - 0.9, -0.01, 3.1)],
         (0, -1, 0), MATTE, (0.38, 0.27, 0.17))
    for k in range(2):
        wx = x0 + 2.5 + k * 6.0
        quad(builder, [(wx - 0.3, -0.01, 5.2), (wx + 0.3, -0.01, 5.2), (wx + 0.3, -0.01, 5.8), (wx - 0.3, -0.01, 5.8)],
             (0, -1, 0), VOID)
    gable_roof(builder, x0, x1, depth, height, 2.2, "plaster", wall)
    return builder


def dolium_mouth(builder, x, y, z):
    drape(builder, (0.60, 0.40, 0.28), [(0.26, z + 0.005), (0.26, z + 0.04), (0.2, z + 0.04)], 12,
          folds=(0, 0.0, 0.0), squash=1.0, center=(x, y), material=MATTE)
    tinted(builder, (0.08, 0.06, 0.05), lambda: builder.polygon(
        [(x + 0.2 * math.cos(2 * math.pi * k / 12), y + 0.2 * math.sin(2 * math.pi * k / 12), z + 0.03)
         for k in range(12)], MATTE))


def crane():
    return remap(arles_life.crane())
