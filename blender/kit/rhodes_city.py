import random

from .geometry import MATTE, MeshBuilder
from .nimes_figures import tube
from .olympie_doric import painted

PLASTER = "plaster"
STONE = "limestone"
TILES = "terracotta_tiles"
PAVING = "paving"
VOID = "shadow_void"
WALLS = [(1.0, 0.97, 0.92), (1.0, 0.86, 0.60), (0.98, 0.74, 0.52), (1.0, 0.80, 0.72), (0.80, 0.88, 0.98),
         (1.0, 0.92, 0.66), (0.92, 0.62, 0.48), (1.0, 0.95, 0.84), (0.86, 0.94, 0.86), (0.96, 0.70, 0.62)]
ROOFS = [(1.0, 1.0, 1.0), (0.94, 0.86, 0.80), (1.04, 0.96, 0.88), (0.88, 0.82, 0.78)]
SOCLE = (0.82, 0.78, 0.70)
SHUTTERS = [(0.22, 0.38, 0.58), (0.46, 0.28, 0.18), (0.26, 0.46, 0.30), (0.62, 0.20, 0.14)]
CHUNK = (46.0, 43.0)
FOOT = -6.0


def facing(builder, corners, normal, material, colour=None):
    first = len(builder.polygons)
    builder.oriented(corners, normal, material)
    if colour is not None:
        builder.tint(first, colour)


def walls(builder, x0, y0, x1, y1, height, colour):
    painted(builder, SOCLE, lambda: builder.box((x0 - 0.05, y0 - 0.05, FOOT), (x1 + 0.05, y1 + 0.05, 0.5), STONE,
                                                bottom=False, top=False))
    painted(builder, colour, lambda: builder.box((x0, y0, 0.5), (x1, y1, height), PLASTER, bottom=False, top=False))


def gable(builder, x0, y0, x1, y1, z, colour, roof_tone, along_x=True, pitch=0.42, overhang=0.5):
    if along_x:
        half = (y1 - y0) / 2
        mid = (y0 + y1) / 2
        top = z + half * pitch
        for side in (-1, 1):
            eave = mid + side * (half + overhang)
            facing(builder, [(x0 - overhang, eave, z - overhang * pitch), (x1 + overhang, eave, z - overhang * pitch),
                             (x1 + overhang, mid, top), (x0 - overhang, mid, top)], (0, side, 1), TILES, roof_tone)
        for x, sign in ((x0, -1), (x1, 1)):
            facing(builder, [(x, y0, z), (x, y1, z), (x, mid, top)], (sign, 0, 0), PLASTER, colour)
    else:
        half = (x1 - x0) / 2
        mid = (x0 + x1) / 2
        top = z + half * pitch
        for side in (-1, 1):
            eave = mid + side * (half + overhang)
            facing(builder, [(eave, y0 - overhang, z - overhang * pitch), (eave, y1 + overhang, z - overhang * pitch),
                             (mid, y1 + overhang, top), (mid, y0 - overhang, top)], (side, 0, 1), TILES, roof_tone)
        for y, sign in ((y0, -1), (y1, 1)):
            facing(builder, [(x0, y, z), (x1, y, z), (mid, y, top)], (0, sign, 0), PLASTER, colour)


def openings(builder, x0, x1, y, outward, floors, rng, door=False):
    width = x1 - x0
    count = max(int(width / 4.5), 1)
    for floor in range(floors):
        z = floor * 3.4 + 1.0
        for k in range(count):
            x = x0 + width * (k + 0.5) / count + rng.uniform(-0.4, 0.4)
            if floor == 0 and door and k == count // 2:
                facing(builder, [(x - 0.8, y, 0.5), (x + 0.8, y, 0.5), (x + 0.8, y, 2.9), (x - 0.8, y, 2.9)],
                       (0, outward, 0), VOID)
                continue
            if floor == 0 and rng.random() < 0.6:
                continue
            facing(builder, [(x - 0.4, y, z + 0.4), (x + 0.4, y, z + 0.4), (x + 0.4, y, z + 1.4), (x - 0.4, y, z + 1.4)],
                   (0, outward, 0), VOID)
            if rng.random() < 0.4:
                tone = rng.choice(SHUTTERS)
                for side in (-1, 1):
                    a, b = sorted((x + side * 0.4, x + side * 0.78))
                    facing(builder, [(a, y + outward * 0.03, z + 0.4), (b, y + outward * 0.03, z + 0.4),
                                     (b, y + outward * 0.03, z + 1.4), (a, y + outward * 0.03, z + 1.4)],
                           (0, outward, 0), PLASTER, tone)


def block_house(builder, x0, y0, x1, y1, rng, detail, street):
    floors = rng.choice((1, 2, 2, 2, 3))
    height = floors * 3.4 + 0.6
    colour = WALLS[rng.randrange(len(WALLS))]
    roof_tone = ROOFS[rng.randrange(len(ROOFS))]
    walls(builder, x0, y0, x1, y1, height, colour)
    gable(builder, x0, y0, x1, y1, height, colour, roof_tone, along_x=(x1 - x0) >= (y1 - y0))
    if detail:
        for y, outward in ((y0 - 0.02, -1), (y1 + 0.02, 1)):
            if (outward < 0 and "south" in street) or (outward > 0 and "north" in street):
                openings(builder, x0 + 0.5, x1 - 0.5, y, outward, floors, rng, door=True)


def court_house(builder, x0, y0, x1, y1, rng, detail, street):
    floors = rng.choice((1, 2, 2))
    height = floors * 3.4 + 0.6
    colour = WALLS[rng.randrange(len(WALLS))]
    roof_tone = ROOFS[rng.randrange(len(ROOFS))]
    wing = min(6.5, (x1 - x0) / 3.2, (y1 - y0) / 3.2)
    south = (x0, y0, x1, y0 + wing)
    north = (x0, y1 - wing, x1, y1)
    west = (x0, y0 + wing, x0 + wing, y1 - wing)
    east = (x1 - wing, y0 + wing, x1, y1 - wing)
    for index, (a, b, c, d) in enumerate((south, north, west, east)):
        lift = height + (1.6 if index == 1 and floors > 1 else 0.0)
        walls(builder, a, b, c, d, lift, colour)
        gable(builder, a, b, c, d, lift, colour, roof_tone, along_x=index < 2)
    cx0, cy0, cx1, cy1 = x0 + wing, y0 + wing, x1 - wing, y1 - wing
    painted(builder, (0.96, 0.9, 0.78), lambda: builder.box((cx0, cy0, -0.2), (cx1, cy1, 0.55), PAVING, bottom=False))
    if detail:
        for y, outward in ((y0 - 0.02, -1), (y1 + 0.02, 1)):
            if (outward < 0 and "south" in street) or (outward > 0 and "north" in street):
                openings(builder, x0 + 0.5, x1 - 0.5, y, outward, floors, rng, door=True)
        count = max(2, int((cx1 - cx0) / 3.0))
        for k in range(count + 1):
            x = cx0 + 0.6 + (cx1 - cx0 - 1.2) * k / count
            for y in (cy0 + 0.6, cy1 - 0.6):
                tube(builder, [(x, y, 0.55), (x, y, height - 0.3)], [0.2, 0.17], (1.0, 0.98, 0.94), 5, "marble",
                     cap=False)
        painted(builder, (0.14, 0.32, 0.44), lambda: builder.box(((cx0 + cx1) / 2 - 1.2, (cy0 + cy1) / 2 - 0.8, 0.5),
                                                                 ((cx0 + cx1) / 2 + 1.2, (cy0 + cy1) / 2 + 0.8, 0.6),
                                                                 MATTE, bottom=False))


def shops(builder, x0, x1, y, rng):
    count = max(int((x1 - x0) / 5.0), 1)
    for k in range(count):
        a = x0 + (x1 - x0) * k / count + 0.6
        b = x0 + (x1 - x0) * (k + 1) / count - 0.6
        facing(builder, [(a, y, 0.5), (b, y, 0.5), (b, y, 3.0), (a, y, 3.0)], (0, -1, 0), VOID)
        if rng.random() < 0.6:
            tone = rng.choice([(0.86, 0.20, 0.12), (0.96, 0.74, 0.22), (0.20, 0.42, 0.74), (0.98, 0.96, 0.9),
                               (0.30, 0.60, 0.40)])
            facing(builder, [(a - 0.2, y - 0.02, 3.2), (b + 0.2, y - 0.02, 3.2), (b + 0.2, y - 1.6, 2.5),
                             (a - 0.2, y - 1.6, 2.5)], (0, -1, 1), MATTE, tone)


def house_chunk(seed, detail=True, width=CHUNK[0], depth=CHUNK[1], street=("south", "north"), shopfront=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    columns = rng.choice((2, 2, 3))
    xs = [-width / 2]
    for k in range(1, columns):
        xs.append(-width / 2 + width * k / columns + rng.uniform(-3.0, 3.0))
    xs.append(width / 2)
    split = rng.uniform(-3.0, 3.0)
    ys = [-depth / 2, split, depth / 2]
    for i in range(columns):
        for j in range(2):
            x0, x1 = xs[i] + 0.4, xs[i + 1] - 0.4
            y0, y1 = ys[j] + 0.4, ys[j + 1] - 0.4
            sides = ("south",) if j == 0 else ("north",)
            sides = tuple(s for s in sides if s in street)
            local = random.Random(rng.random())
            if x1 - x0 > 15.0 and y1 - y0 > 15.0 and local.random() < 0.7:
                court_house(builder, x0, y0, x1, y1, local, detail, sides)
            else:
                block_house(builder, x0, y0, x1, y1, local, detail, sides)
            if detail and shopfront and j == 0:
                shops(builder, x0 + 0.5, x1 - 0.5, y0 - 0.03, local)
    return builder


def portico(length=25.0, height=5.6, depth=5.0, count=7, colour=(1.0, 0.86, 0.62)):
    builder = MeshBuilder()
    for k in range(count):
        x = -length / 2 + length * (k + 0.5) / count
        tube(builder, [(x, 0.0, 0.0), (x, 0.0, 0.45)], [0.4, 0.4], (0.96, 0.94, 0.9), 6, "marble")
        tube(builder, [(x, 0.0, 0.45), (x, 0.0, height - 0.5)], [0.31, 0.26], (1.0, 0.98, 0.95), 8, "marble")
        painted(builder, (0.98, 0.95, 0.9), lambda x=x: builder.box((x - 0.42, -0.42, height - 0.5),
                                                                    (x + 0.42, 0.42, height), "marble"))
    painted(builder, (1.0, 0.97, 0.92), lambda: builder.box((-length / 2, -0.5, height), (length / 2, 0.5, height + 0.8),
                                                            "marble"))
    painted(builder, (0.66, 0.20, 0.14), lambda: builder.box((-length / 2, -0.52, height + 0.06),
                                                             (length / 2, -0.5, height + 0.12), MATTE, bottom=False,
                                                             top=False))
    for k in range(int(length / 1.5)):
        x = -length / 2 + 0.45 + k * 1.5
        painted(builder, (0.30, 0.40, 0.60), lambda x=x: builder.box((x, -0.53, height + 0.2), (x + 0.55, -0.5,
                                                                                                height + 0.7), MATTE,
                                                                     bottom=False, top=False))
    facing(builder, [(-length / 2 - 0.3, -0.8, height + 0.8), (length / 2 + 0.3, -0.8, height + 0.8),
                     (length / 2 + 0.3, depth, height + 2.0), (-length / 2 - 0.3, depth, height + 2.0)], (0, 0, 1),
           TILES)
    painted(builder, colour, lambda: builder.box((-length / 2, depth, FOOT), (length / 2, depth + 0.6, height + 2.1),
                                                 PLASTER, bottom=False))
    painted(builder, (0.96, 0.92, 0.84), lambda: builder.box((-length / 2, -0.6, FOOT), (length / 2, depth, 0.18),
                                                             PAVING, bottom=False))
    for k in range(count - 1):
        x = -length / 2 + length * (k + 1) / count
        facing(builder, [(x - 1.1, depth - 0.02, 0.18), (x + 1.1, depth - 0.02, 0.18), (x + 1.1, depth - 0.02, 3.0),
                         (x - 1.1, depth - 0.02, 3.0)], (0, -1, 0), VOID)
    return builder

