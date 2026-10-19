import numpy as np

from . import pantheon_architecture as arch
from . import pantheon_materials as materials
from .geometry import MeshBuilder, placement
from .orders import corinthian_entablature_profile, gable_roof, tile_roof
from .pantheon_architecture import (PIAZZA, PLAZA_HALF, PLAZA_NORTH, PORTICO_BACK, PORTICO_COLUMN, PORTICO_D,
                                    PORTICO_EDGE, PORTICO_FLOOR, PORTICO_LINE, PORTICO_SPACING, STEP_RISE, STEP_TREAD,
                                    plaza_floor, quad)
from .pont_materials import luminance, periodic_noise

ENTABLATURE = 2.5 * PORTICO_D
BEAM_TOP = PORTICO_FLOOR + PORTICO_COLUMN + ENTABLATURE
RAISE = ENTABLATURE - 0.9
RIDGE = 11.8 + RAISE
WALL_TOP = 11.6 + RAISE
CEILING = 11.4 + RAISE
EAVE_INSET = 1.25
EAVE_Z = BEAM_TOP + 0.1
NORTH_LINE = PLAZA_NORTH + 2.25
PAVONAZZETTO_TILE = 3.0
HALL_CORNICE = [(-0.3, 0.0), (0.0, 0.0), (0.0, 0.25), (0.22, 0.36), (0.42, 0.52), (0.55, 0.55), (0.55, 0.68),
                (-0.3, 0.68)]


def warped_cells(cells, seed, amplitude=34.0):
    size = materials.SIZE
    generator = np.random.default_rng(seed)
    points = generator.uniform(0, size, (cells, 2))
    weights = generator.uniform(0.0, 18.0, cells)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    xs = xs + amplitude * (periodic_noise(size, 2.3, seed + 11) - 0.5) * 2
    ys = ys + amplitude * (periodic_noise(size, 2.3, seed + 12) - 0.5) * 2
    first = np.full((size, size), np.inf, dtype=np.float32)
    second = np.full((size, size), np.inf, dtype=np.float32)
    owner = np.zeros((size, size), dtype=np.int32)
    for index, (px, py) in enumerate(points):
        dx = np.abs(xs - px) % size
        dy = np.abs(ys - py) % size
        distance = np.hypot(np.minimum(dx, size - dx), np.minimum(dy, size - dy)) - weights[index]
        closer = distance < first
        second = np.where(closer, first, np.minimum(second, distance))
        owner = np.where(closer, index, owner)
        first = np.where(closer, distance, first)
    return first, second, owner


def pavonazzetto(source, cells=150, seed=94):
    size = materials.SIZE
    generator = np.random.default_rng(seed + 1)
    first, second, owner = warped_cells(cells, seed)
    tones = generator.normal(1.0, 0.03, cells)
    violet = generator.random(cells) < 0.08
    clast = np.array([0.95, 0.93, 0.9])[None, None, :] * tones[owner][..., None]
    clast = np.where(violet[owner][..., None], clast * np.array([0.9, 0.84, 0.88]), clast)
    clast *= (0.92 + 0.08 * materials.normalise(luminance(source)))[..., None]
    edge = second - first
    width = 0.8 + 4.5 * periodic_noise(size, 1.4, seed + 2) ** 1.5
    presence = materials.smoothstep(periodic_noise(size, 1.3, seed + 3), 0.25, 0.55)
    vein = (1.0 - materials.smoothstep(edge, 0.0, width)) * (0.35 + 0.65 * presence)
    halo = (1.0 - materials.smoothstep(edge, 0.0, width * 3.0)) * presence
    cloud = materials.smoothstep(periodic_noise(size, 2.0, seed + 4), 0.55, 0.85)
    violet_tone = np.array([0.66, 0.5, 0.62])
    tinted = clast * (1.0 - 0.18 * (halo + 0.5 * cloud)[..., None]) + violet_tone * 0.18 * (halo + 0.5 * cloud)[..., None]
    colour = tinted * (1.0 - vein[..., None]) + np.array([0.44, 0.3, 0.42]) * vein[..., None]
    return np.clip(colour * materials.patina(33, 0.04), 0, 1)


def reduced(piece, tile):
    count = max(int(round(2 * materials.SECTILE_CELL / tile)), 1)
    size = piece.shape[0]
    total = np.zeros_like(piece, dtype=np.float64)
    for a in range(count):
        rows = (np.arange(size) * count + a) % size
        for b in range(count):
            total += piece[rows][:, (np.arange(size) * count + b) % size]
    return total / (count * count)


def sectile(pieces):
    pieces = {name: reduced(piece, materials.TEXTURED[name][2]) for name, piece in pieces.items()}
    size = materials.SIZE
    cell = materials.SECTILE_CELL
    scale = size / (2 * cell)
    ys, xs = np.mgrid[0:size, 0:size]
    u = xs / scale
    v = ys / scale
    cell_u = np.floor(u / cell)
    cell_v = np.floor(v / cell)
    lu = u - cell_u * cell - cell / 2
    lv = v - cell_v * cell - cell / 2
    odd = ((cell_u + cell_v) % 2).astype(bool)
    square = np.maximum(np.abs(lu), np.abs(lv))
    radius = np.hypot(lu, lv)
    band = cell / 2 - 0.16
    colour = pieces["giallo"].copy()
    inner = square < band
    joints = np.abs(square - band) < 0.008
    first_inner = inner & ~odd
    second_inner = inner & odd
    colour[first_inner] = pieces["granite_grey"][first_inner]
    colour[second_inner] = pieces["pavonazzetto"][second_inner]
    disc = first_inner & (radius < 1.02)
    ring = first_inner & (np.abs(radius - 1.07) < 0.05)
    colour[ring] = pieces["giallo"][ring]
    colour[disc] = pieces["porphyry"][disc]
    small = second_inner & (square < 0.82)
    colour[small] = pieces["granite_rose"][small]
    joints |= first_inner & (np.abs(radius - 1.02) < 0.006)
    joints |= first_inner & (np.abs(radius - 1.12) < 0.006)
    joints |= second_inner & (np.abs(square - 0.82) < 0.006)
    colour[joints] *= 0.55
    wear = periodic_noise(size, 1.7, 71)
    colour *= (0.95 + 0.07 * wear)[..., None]
    return np.clip(colour, 0, 1)


def install_marbles():
    materials.REVISION.update({"pavonazzetto": "v8", "floor_sectile": "v8"})
    roughness, metallic, _ = materials.TEXTURED["pavonazzetto"]
    materials.TEXTURED["pavonazzetto"] = (roughness, metallic, PAVONAZZETTO_TILE)
    materials.pavonazzetto = pavonazzetto
    materials.sectile = sectile


def recolour(builder, old, new):
    if old not in builder.materials:
        return builder
    source = builder.materials.index(old)
    target = builder.slot(new)
    builder.polygon_materials = [target if index == source else index for index in builder.polygon_materials]
    builder.materials.pop(source)
    builder.polygon_materials = [index - 1 if index > source else index for index in builder.polygon_materials]
    return builder


def porch():
    saved = arch.eagle
    arch.eagle = MeshBuilder
    try:
        builder, floor, columns, statues = arch.porch()
    finally:
        arch.eagle = saved
    return recolour(builder, "bronze_gilt", "bronze"), floor, columns, statues


def niche_pedestals():
    builder = MeshBuilder()
    for side in (-1, 1):
        x = side * 11.125
        builder.box((x - 0.8, arch.BLOCK_SLAB - 1.2, 0.9), (x + 0.8, arch.BLOCK_SLAB + 0.4, 1.9), "marble_white",
                    bottom=False)
        builder.box((x - 0.9, arch.BLOCK_SLAB - 1.3, 1.9), (x + 0.9, arch.BLOCK_SLAB + 0.5, 2.1), "marble_white",
                    bottom=False)
    return builder


def wall(builder, a0, a1, b0, b1, along, piece=6.0):
    count = max(int(round((b1 - b0) / piece)), 1)
    for k in range(count):
        c0, c1 = b0 + (b1 - b0) * k / count, b0 + (b1 - b0) * (k + 1) / count
        if along == "y":
            builder.box((a0, c0, PIAZZA - 1.0), (a1, c1, WALL_TOP), "plaster_cream", bottom=False)
        else:
            builder.box((c0, a0, PIAZZA - 1.0), (c1, a1, WALL_TOP), "plaster_cream", bottom=False)


def portico_side(builder, floor, side):
    for step in range(1, 5):
        x0, x1 = sorted((side * (PLAZA_HALF + STEP_TREAD * (step - 1)), side * PORTICO_EDGE))
        floor.box((x0, 30.0, PIAZZA - 0.2), (x1, PLAZA_NORTH, PIAZZA + STEP_RISE * step), "giallo", bottom=False)
    x0, x1 = sorted((side * PORTICO_EDGE, side * PORTICO_BACK))
    floor.box((x0, 30.0, PIAZZA - 0.2), (x1, PLAZA_NORTH + 8.0, PORTICO_FLOOR), "giallo", bottom=False)
    wall_x0, wall_x1 = sorted((side * PORTICO_BACK, side * (PORTICO_BACK + 0.6)))
    wall(builder, wall_x0, wall_x1, 30.0, PLAZA_NORTH + 8.6, "y")
    for y in range(36, 160, 9):
        quad(builder, [(side * (PORTICO_BACK - 0.02), y - 1.2, PORTICO_FLOOR), (side * (PORTICO_BACK - 0.02), y + 1.2, PORTICO_FLOOR),
                       (side * (PORTICO_BACK - 0.02), y + 1.2, PORTICO_FLOOR + 3.6),
                       (side * (PORTICO_BACK - 0.02), y - 1.2, PORTICO_FLOOR + 3.6)], (-side, 0, 0), "shadow_void")
    eave_x = PORTICO_LINE - EAVE_INSET
    tile_roof(builder, (side * (PORTICO_BACK + 0.6), 30.0, RIDGE), (side * (PORTICO_BACK + 0.6), PLAZA_NORTH + 8.6, RIDGE),
              (-side * (PORTICO_BACK + 0.6 - eave_x), 0.0, EAVE_Z - RIDGE), "terracotta_tiles", imbrex=False)
    quad(builder, [(side * (PORTICO_LINE + 0.4), 30.0, BEAM_TOP - 0.05), (side * PORTICO_BACK, 30.0, CEILING),
                   (side * PORTICO_BACK, PLAZA_NORTH + 8.0, CEILING), (side * (PORTICO_LINE + 0.4), PLAZA_NORTH + 8.0, BEAM_TOP - 0.05)],
         (0, 0, -1), "plaster", (0.75, 0.68, 0.6))
    return [placement(side * PORTICO_LINE, 32.0 + PORTICO_SPACING * index, PORTICO_FLOOR)
            for index in range(int((PLAZA_NORTH - 33.0) / PORTICO_SPACING) + 1)]


def hall(side):
    builder = MeshBuilder()
    x0, x1 = sorted((side * 26.0, side * (PORTICO_BACK + 0.6)))
    builder.box((x0, -16.0, PIAZZA - 1.0), (x1, 16.0, 9.3), "stucco", bottom=False)
    builder.box((x0 - 0.06, -16.06, PIAZZA - 1.0), (x1 + 0.06, 16.06, PIAZZA + 0.5), "marble_white", bottom=False)
    path = [(x0, -16.0, 9.3), (x1, -16.0, 9.3), (x1, 16.0, 9.3), (x0, 16.0, 9.3)]
    builder.sweep(path, HALL_CORNICE, "marble_white", closed=True)
    inner = x0 if side > 0 else x1
    for k in range(7):
        y = -13.5 + 4.5 * k
        a, b = sorted((inner, inner - side * 0.14))
        builder.box((a, y - 0.35, PIAZZA + 0.5), (b, y + 0.35, 9.3), "marble_white", bottom=False, top=False)
    for k in range(3):
        x = side * (28.0 + 4.5 * k)
        builder.box((x - 0.35, 16.0, PIAZZA + 0.5), (x + 0.35, 16.14, 9.3), "marble_white", bottom=False, top=False)
    for x, facing in ((x0, -1), (x1, 1)):
        builder.oriented([(x, -16.0, 9.3), (x, 16.0, 9.3), (x, 0.0, 12.9)], (facing, 0, 0), "stucco")
    gable_roof(builder, x0 - 0.3, x1 + 0.3, 16.6, 10.0, 13.0, "terracotta_tiles", along_axis="x", imbrex=False)
    return builder


def piazza():
    builder = MeshBuilder()
    floor = MeshBuilder()
    plaza_floor(floor)
    frames = portico_side(builder, floor, -1) + portico_side(builder, floor, 1)
    for step in range(1, 5):
        floor.box((-PORTICO_EDGE, PLAZA_NORTH + STEP_TREAD * (step - 1), PIAZZA - 0.2),
                  (PORTICO_EDGE, PLAZA_NORTH + 1.2, PIAZZA + STEP_RISE * step), "giallo", bottom=False)
    floor.box((-PORTICO_BACK, PLAZA_NORTH + 1.2, PIAZZA - 0.2), (PORTICO_BACK, PLAZA_NORTH + 8.0, PORTICO_FLOOR), "giallo",
              bottom=False)
    back = PLAZA_NORTH + 8.0
    wall(builder, back, back + 0.6, -PORTICO_BACK - 0.6, PORTICO_BACK + 0.6, "x")
    for x in range(-27, 28, 9):
        quad(builder, [(x - 1.2, back - 0.02, PORTICO_FLOOR), (x + 1.2, back - 0.02, PORTICO_FLOOR),
                       (x + 1.2, back - 0.02, PORTICO_FLOOR + 3.6), (x - 1.2, back - 0.02, PORTICO_FLOOR + 3.6)], (0, -1, 0),
             "shadow_void")
    top = PORTICO_FLOOR + PORTICO_COLUMN
    builder.sweep([(-PORTICO_LINE, 30.0, top), (-PORTICO_LINE, NORTH_LINE, top), (PORTICO_LINE, NORTH_LINE, top),
                   (PORTICO_LINE, 30.0, top)], corinthian_entablature_profile(PORTICO_D), "marble_white")
    tile_roof(builder, (-PORTICO_BACK - 0.6, back + 0.6, RIDGE), (PORTICO_BACK + 0.6, back + 0.6, RIDGE),
              (0.0, -(back + 0.6 - NORTH_LINE + EAVE_INSET), EAVE_Z - RIDGE), "terracotta_tiles", imbrex=False)
    quad(builder, [(-PORTICO_BACK, NORTH_LINE + 0.4, BEAM_TOP - 0.05), (PORTICO_BACK, NORTH_LINE + 0.4, BEAM_TOP - 0.05),
                   (PORTICO_BACK, back, CEILING), (-PORTICO_BACK, back, CEILING)], (0, 0, -1), "plaster", (0.75, 0.68, 0.6))
    count = int(round(2 * PORTICO_LINE / PORTICO_SPACING))
    frames += [placement(-PORTICO_LINE + 2 * PORTICO_LINE * index / count, NORTH_LINE, PORTICO_FLOOR)
               for index in range(count + 1)]
    for side in (-1, 1):
        builder.merge(hall(side), placement(0.0, 6.0, 0.0))
    return builder, floor, frames
