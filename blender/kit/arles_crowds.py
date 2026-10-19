import math
import random

from mathutils import Matrix, Vector

from .arles_life import HAIR, SKIN, ellipsoid, tube
from .arles_monuments import CIRCUS_DEPTH, CIRCUS_HALF_WIDTH, CIRCUS_LENGTH, cuneus_ranges, theatre_rows
from .geometry import MATTE, MeshBuilder, placement
from .life import WOOL, painted

FLAT = Matrix.Diagonal((1.0, 0.72, 1.0, 1.0))
GARMENTS = [("undyed", 4), ("white", 2), ("ochre", 2), ("madder", 2), ("woad", 2), ("brown", 2), ("weld", 1.5),
            ("green", 1), ("grey", 1.5), ("dark", 1), ("rose", 1), ("purple", 0.2)]
TOGA = (0.88, 0.85, 0.76)
CIRCUS_INNER = CIRCUS_HALF_WIDTH - CIRCUS_DEPTH


def weighted(rng, items):
    total = sum(weight for _, weight in items)
    roll = rng.random() * total
    for key, weight in items:
        roll -= weight
        if roll <= 0:
            return WOOL[key]
    return WOOL[items[-1][0]]


def shade(colour, rng, spread=0.08):
    factor = rng.uniform(1.0 - spread, 1.0 + spread)
    return tuple(min(component * factor, 1.0) for component in colour)


def spectator(seed, near=True, arms=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    female = rng.random() < 0.42
    garment = shade(weighted(rng, GARMENTS), rng)
    if not female and rng.random() < 0.3:
        mantle = shade(TOGA, rng, 0.04)
    elif female and rng.random() < 0.7:
        mantle = shade(weighted(rng, GARMENTS), rng)
    else:
        mantle = garment
    skin = SKIN[rng.randrange(len(SKIN))]
    hair = HAIR[rng.randrange(len(HAIR))]
    cover = mantle if female and rng.random() < 0.5 else hair
    scale = 0.78 if rng.random() < 0.08 else rng.uniform(0.95, 1.05)
    if near:
        tube(builder, (0.0, 0.0, 0.08), (0.0, 0.42, 0.1), 0.17, 0.15, garment, 5, caps=False, scale=(1.0, 0.5))
        tube(builder, (0.0, 0.4, 0.13), (0.0, 0.46, -0.42), 0.065, 0.055, garment if female else skin, 4,
             scale=(1.0, 1.7))
        painted(builder, garment, lambda: builder.lathe([(0.17, 0.0), (0.185, 0.24)], 6, MATTE, matrix=FLAT,
                                                        caps=False))
        painted(builder, mantle, lambda: builder.lathe([(0.185, 0.24), (0.16, 0.47), (0.06, 0.66)], 6, MATTE,
                                                       matrix=FLAT, caps=False))
        for side in ((-1, 1) if arms else ()):
            sleeve = mantle if (side < 0 and mantle != garment) else skin if rng.random() < 0.5 else garment
            tube(builder, (side * 0.19, 0.0, 0.5), (side * 0.11, 0.34, 0.2), 0.05, 0.035, sleeve, 4)
        ellipsoid(builder, (0.0, 0.015, 0.75), (0.085, 0.095, 0.11), skin, 5, 2, low=0.0, high=0.6)
        ellipsoid(builder, (0.0, -0.005, 0.755), (0.09, 0.102, 0.112), cover, 5, 2, low=0.45, high=1.0)
    else:
        painted(builder, mantle, lambda: builder.lathe([(0.17, 0.0), (0.16, 0.42), (0.06, 0.6)], 4, MATTE,
                                                       matrix=FLAT, start=math.pi / 4, caps=False))
        painted(builder, skin, lambda: builder.lathe([(0.0, 0.57), (0.085, 0.68)], 4, MATTE, caps=False))
        painted(builder, cover, lambda: builder.lathe([(0.09, 0.68), (0.0, 0.79)], 4, MATTE, caps=False))
    if scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(scale, 4))
        return scaled
    return builder


def templates(seed, near, count=20, arms=True):
    return [spectator(seed * 1000 + index, near, arms) for index in range(count)]


def facing(x, y, tx, ty):
    return math.atan2(-(tx - x), ty - y)


def theatre_seats(a0, a1, rng, spacing=0.62):
    rows = theatre_rows()
    count = len(rows)
    seats = []
    for index, (r, z, _) in enumerate(rows):
        radius = r + 0.35
        number = max(int(radius * (a1 - a0) / spacing), 1)
        fill = 0.6 - 0.26 * index / max(count - 1, 1)
        for k in range(number):
            if rng.random() > fill:
                continue
            angle = a0 + (a1 - a0) * (k + 0.5 + rng.uniform(-0.12, 0.12)) / number
            x, y = radius * math.cos(angle), radius * math.sin(angle)
            seats.append((x, y, z, facing(x, y, 0.0, 4.0)))
    return seats


def fill(seats, pool, rng):
    builder = MeshBuilder()
    for x, y, z, turn in seats:
        builder.merge(pool[rng.randrange(len(pool))], placement(x, y, z, turn + rng.uniform(-0.2, 0.2)))
    return builder


def theatre_crowd(eye, hole=5.5, near_limit=2.4, seed=3, parts=3):
    rng = random.Random(seed)
    pool = templates(seed, True)
    light = templates(seed, True, arms=False)
    sectors = []
    for c0, c1 in cuneus_ranges():
        width = (c1 - c0) / parts
        for k in range(parts):
            sectors.append((c0 + k * width, c0 + (k + 1) * width))
    base = sectors[0][0]
    width = sectors[0][1] - sectors[0][0]
    variants = {name: fill(theatre_seats(base, base + width, random.Random(seed * 7 + index)), light, rng)
                for index, name in enumerate(("crowd_theatre_a", "crowd_theatre_b"))}
    instances = {name: [] for name in variants}
    uniques = []
    detailed = []
    eye_radius = math.hypot(eye.x, eye.y)
    eye_angle = math.atan2(eye.y, eye.x) % (2 * math.pi)
    reach = math.asin(min(hole / max(eye_radius, hole + 0.1), 1.0)) + 0.02
    for index, (a0, a1) in enumerate(sectors):
        if a0 - reach < eye_angle < a1 + reach:
            seats = theatre_seats(a0, a1, random.Random(seed * 31 + index))
            kept = []
            for x, y, z, turn in seats:
                distance = math.hypot(x - eye.x, y - eye.y)
                if distance < near_limit:
                    continue
                if distance < hole:
                    detailed.append((x, y, z, turn))
                else:
                    kept.append((x, y, z, turn))
            uniques.append(fill(kept, pool, rng))
            continue
        name = "crowd_theatre_a" if (index * 7) % 3 else "crowd_theatre_b"
        instances[name].append(Matrix.Rotation(a0 - base, 4, "Z"))
    return variants, instances, uniques, detailed


def circus_block(seed, fill_rate, curved, width=4.6, spacing=0.56):
    rng = random.Random(seed)
    pool = templates(seed, False)
    builder = MeshBuilder()
    for row in range(14):
        offset = 0.9 + 0.86 * (row + 0.7)
        inward = CIRCUS_DEPTH - offset
        local = width * ((CIRCUS_INNER + offset) / CIRCUS_HALF_WIDTH if curved else 1.0)
        number = max(int(local / spacing), 1)
        z = 2.9 + 0.5 * row
        for k in range(number):
            if rng.random() > fill_rate:
                continue
            x = -local / 2 + local * (k + 0.5 + rng.uniform(-0.15, 0.15)) / number
            builder.merge(pool[rng.randrange(len(pool))], placement(x, -inward, z, math.pi + rng.uniform(-0.25, 0.25)))
    return builder


def circus_variant(frame):
    y = frame.translation.y
    if y > -CIRCUS_LENGTH / 2 + CIRCUS_HALF_WIDTH and -110.0 < y < 170.0:
        return "crowd_circus_dense"
    return "crowd_circus_curve"


CIRCUS_BUILDS = {
    "crowd_circus_dense": lambda: circus_block(71, 0.55, False),
    "crowd_circus_curve": lambda: circus_block(73, 0.42, True),
}


def crowd_carpet(builder, seed, z_low, z_high, share=0.6, blend=0.55):
    rng = random.Random(seed)
    for index, polygon in enumerate(builder.polygons):
        corners = [builder.positions[point] for point in polygon]
        if len(corners) < 3 or not z_low < min(corner[2] for corner in corners) < z_high:
            continue
        a, b, c = (Vector(corner) for corner in corners[:3])
        normal = (b - a).cross(c - a)
        if normal.length < 1e-9 or normal.normalized().z < 0.7 or rng.random() > share:
            continue
        cloth = weighted(rng, GARMENTS)
        current = builder.polygon_colors[index] or (1.0, 1.0, 1.0)
        builder.polygon_colors[index] = tuple(base * (1.0 - blend) + tint * blend for base, tint in zip(current, cloth))
    return builder


def eye_local(origin, eye):
    return origin.inverted() @ Vector(eye)
