import math
import random

from mathutils import Matrix, Vector

from .buildings import ASHLAR, VOID, WEATHERED, lobe, trunk
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, TERRACOTTA, WOOD
from .nimes_figures import FIGURES, Look, amphora, basket, boxed, drape, ellipsoid, person, tube

TAU = 2 * math.pi
WICKER = (0.62, 0.50, 0.32)
HEN_COLOURS = [(0.62, 0.42, 0.24), (0.86, 0.80, 0.68), (0.30, 0.24, 0.20)]
TUNICS = ["undyed", "madder", "woad", "ochre", "weld", "green", "brown", "grey", "rose", "white", "dark"]
SPECTATOR_TONES = [(0.93, 0.91, 0.86), (0.80, 0.75, 0.64), (0.64, 0.28, 0.20), (0.42, 0.49, 0.58),
                   (0.74, 0.56, 0.32), (0.80, 0.71, 0.42), (0.48, 0.50, 0.34), (0.46, 0.34, 0.23),
                   (0.74, 0.50, 0.44), (0.55, 0.51, 0.47)]


def facing(x, y, tx, ty):
    return math.atan2(-(tx - x), ty - y)


def ring_of(builder, looks, radius, rng, centre=(0.0, 0.0)):
    count = len(looks)
    for index, look in enumerate(looks):
        angle = TAU * index / count + rng.uniform(-0.25, 0.25)
        x = centre[0] + radius * rng.uniform(0.85, 1.15) * math.cos(angle)
        y = centre[1] + radius * rng.uniform(0.85, 1.15) * math.sin(angle)
        builder.merge(person(look), placement(x, y, 0.0, facing(x, y, *centre) + rng.uniform(-0.35, 0.35)))


def citizens_group(seed=41):
    rng = random.Random(seed)
    builder = MeshBuilder()
    looks = [Look("white", hem=0.12, skin=1, hair=2, toga="white", arms="toga_gesture", carry="scroll", seed=seed),
             Look("white", hem=0.12, skin=0, hair=0, toga="white", arms="toga", seed=seed + 1),
             Look("woad", hem=0.03, skin=0, hair=3, palla="madder", veil=True, female=True, sleeves="long",
                  arms="hip", scale=0.95, seed=seed + 2),
             Look("grey", hem=0.5, skin=1, hair=1, cloak="woad", belt="brown", arms="gesture", seed=seed + 3)]
    ring_of(builder, looks, 0.75, rng)
    return builder


def commoners_group(seed=51):
    rng = random.Random(seed)
    builder = MeshBuilder()
    looks = [Look("brown", hem=0.55, skin=2, hair=1, belt="dark", arms="gesture", seed=seed),
             Look("weld", hem=0.04, skin=1, hair=0, palla="woad", female=True, sleeves="long", arms="head",
                  carry="basket", scale=0.95, seed=seed + 1),
             Look("madder", hem=0.56, skin=1, hair=3, belt="brown", arms="hip", apron="undyed", seed=seed + 2)]
    ring_of(builder, looks, 0.7, rng)
    amphora(builder, Matrix.Translation((0.2, -0.15, 0.0)) @ Matrix.Rotation(math.radians(8), 4, "X"))
    return builder


def children_group(seed=61):
    rng = random.Random(seed)
    builder = MeshBuilder()
    kids = [Look("white", hem=0.5, skin=0, hair=1, scale=0.62, belt="madder", stripe="madder", child=True,
                 arms="forward", seed=seed),
            Look("ochre", hem=0.5, skin=1, hair=3, scale=0.6, belt="brown", child=True, arms="gesture", seed=seed + 1),
            Look("rose", hem=0.08, skin=0, hair=1, scale=0.58, female=True, sleeves="long", child=True,
                 arms="forward", seed=seed + 2),
            Look("woad", hem=0.5, skin=2, hair=0, scale=0.63, belt="dark", child=True, arms="swing", stride=0.15,
                 seed=seed + 3)]
    spots = [(-0.9, 0.0), (0.9, 0.1), (0.0, 1.1), (2.2, -1.2)]
    for look, (x, y) in zip(kids[:3], spots[:3]):
        builder.merge(person(look), placement(x, y, 0.0, facing(x, y, 0.0, 0.3) + rng.uniform(-0.2, 0.2)))
    ellipsoid(builder, (0.1, 0.35, 0.09), (0.09, 0.09, 0.09), (0.70, 0.30, 0.18), 8, 5)
    x, y = spots[3]
    builder.merge(person(kids[3]), placement(x, y, 0.0, 0.4))
    hoop = Matrix.Translation((x + 0.45, y + 0.35, 0.36)) @ Matrix.Rotation(0.4, 4, "Z")
    path = [hoop @ Vector((0.0, 0.34 * math.cos(TAU * k / 14), 0.34 * math.sin(TAU * k / 14))) for k in range(15)]
    tube(builder, path, [0.014] * 15, (0.55, 0.40, 0.24), 4, cap=False)
    tube(builder, [Vector((x + 0.2, y + 0.15, 0.55)), hoop @ Vector((0.0, -0.1, 0.1))], [0.01, 0.008], WOOD, 4)
    return builder


def shoppers_group(seed=71):
    rng = random.Random(seed)
    builder = MeshBuilder()
    looks = [Look("rose", hem=0.04, skin=0, hair=1, palla="undyed", veil=True, female=True, sleeves="long",
                  arms="forward", scale=0.95, seed=seed),
             Look("green", hem=0.04, skin=1, hair=0, palla="weld", female=True, sleeves="long", arms="hip",
                  carry="basket", scale=0.94, seed=seed + 1),
             Look("white", hem=0.5, skin=0, hair=1, scale=0.64, belt="madder", stripe="madder", child=True,
                  seed=seed + 2),
             Look("undyed", hem=0.55, skin=2, hair=2, belt="brown", arms="carry", carry="amphora", seed=seed + 3)]
    for look, (x, y) in zip(looks, ((-0.7, 0.0), (0.4, -0.15), (-0.15, -0.55), (1.4, -0.6))):
        builder.merge(person(look), placement(x, y, 0.0, rng.uniform(-0.3, 0.3)))
    return builder


def crowd_group(seed=81, count=6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(count):
        roll = rng.random()
        tunic = TUNICS[rng.randrange(len(TUNICS))]
        if roll < 0.25:
            look = Look("white", hem=0.12, skin=rng.randrange(3), hair=rng.randrange(4), toga="white",
                        arms=rng.choice(["toga", "toga_gesture"]), stride=0.12, seed=seed + index)
        elif roll < 0.5:
            look = Look(tunic, hem=0.04, skin=rng.randrange(2), hair=rng.randrange(4),
                        palla=TUNICS[rng.randrange(len(TUNICS))], veil=rng.random() < 0.5, female=True,
                        sleeves="long", arms=rng.choice(["swing", "hip", "forward"]), stride=0.1, scale=0.95,
                        seed=seed + index)
        elif roll < 0.62:
            look = Look(tunic, hem=0.5, skin=rng.randrange(3), hair=rng.randrange(4), scale=0.62, belt="brown",
                        child=True, arms="swing", stride=0.12, seed=seed + index)
        else:
            look = Look(tunic, hem=0.55, skin=rng.randrange(3), hair=rng.randrange(4),
                        belt=rng.choice(["brown", "dark", None]), cloak=rng.choice([None, None, "brown", "madder"]),
                        hat=(0.80, 0.68, 0.42) if rng.random() < 0.3 else None,
                        arms=rng.choice(["swing", "gesture", "down"]), stride=0.16, seed=seed + index)
        row, column = divmod(index, 3)
        x = (column - 1) * 0.75 + rng.uniform(-0.2, 0.2)
        y = -row * 0.85 + rng.uniform(-0.2, 0.2)
        builder.merge(person(look), placement(x, y, 0.0, rng.uniform(-0.35, 0.35)))
    return builder


def hen(builder, x, y, turn, colour):
    frame = placement(x, y, 0.0, turn)
    ellipsoid(builder, (0.0, 0.0, 0.17), (0.08, 0.13, 0.09), colour, 7, 4, matrix=frame)
    ellipsoid(builder, (0.0, 0.11, 0.27), (0.04, 0.045, 0.05), colour, 6, 3, matrix=frame)
    tube(builder, [frame @ Vector((0.0, 0.15, 0.27)), frame @ Vector((0.0, 0.19, 0.26))], [0.012, 0.0],
         (0.85, 0.65, 0.25), 3, cap=False)
    tube(builder, [frame @ Vector((0.0, -0.1, 0.2)), frame @ Vector((0.0, -0.16, 0.3))], [0.05, 0.01], colour, 4)
    for side in (-1, 1):
        tube(builder, [frame @ Vector((side * 0.03, 0.0, 0.1)), frame @ Vector((side * 0.03, 0.01, 0.0))],
             [0.008, 0.008], (0.85, 0.65, 0.25), 3, cap=False)


def poultry_group(seed=91):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(person(Look("madder", hem=0.04, skin=2, hair=3, palla="brown", veil=True, female=True,
                              sleeves="long", arms="forward", scale=0.95, seed=seed)), placement(0.0, 0.6, 0.0, math.pi))
    for index, x in enumerate((-0.75, 0.0, 0.75)):
        boxed(builder, WICKER if index % 2 else tuple(v * 0.85 for v in WICKER), (x - 0.32, -0.25, 0.0),
              (x + 0.32, 0.25, 0.42))
        hen(builder, x, 0.0, rng.uniform(0, TAU), HEN_COLOURS[index % 3])
    for index in range(4):
        hen(builder, rng.uniform(-1.5, 1.5), rng.uniform(-1.4, -0.6), rng.uniform(0, TAU), HEN_COLOURS[index % 3])
    basket(builder, 1.3, 0.4, 0.0, 0.2, (0.93, 0.90, 0.82), seed)
    return builder


def stall_frame(builder, seed, light, dark):
    boxed(builder, WOOD, (-1.2, -0.45, 0.75), (1.2, 0.45, 0.82))
    boxed(builder, (0.48, 0.37, 0.26), (-1.15, -0.4, 0.0), (1.15, 0.4, 0.75))
    for x in (-1.25, 1.25):
        for y in (-0.5, 0.9):
            tube(builder, [(x, y, 0.0), (x, y, 2.2 if y > 0 else 2.0)], [0.04, 0.035], WOOD, 5)
    columns = 8
    grid = []
    for row in range(3):
        t = row / 2
        line = []
        for column in range(columns + 1):
            s = column / columns
            sag = 0.08 * math.sin(math.pi * s) * math.sin(math.pi * t)
            line.append((-1.45 + 2.9 * s, -0.8 + 1.85 * t, 1.95 + 0.35 * t - sag + 0.025 * math.sin(column * 2.1 + seed)))
        grid.append(line)
    for row in range(2):
        for column in range(columns):
            colour = light if (column // 2) % 2 else dark
            quad = [grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]]
            for side in (1, -1):
                first = len(builder.polygons)
                builder.oriented(quad, (0, 0, side), MATTE, True)
                builder.tint(first, colour if side > 0 else tuple(v * 0.85 for v in colour))


def pottery_stall(seed=5):
    rng = random.Random(seed)
    builder = MeshBuilder()
    stall_frame(builder, seed, (0.86, 0.80, 0.66), (0.55, 0.50, 0.36))
    clays = [TERRACOTTA, (0.78, 0.55, 0.40), (0.66, 0.40, 0.27), (0.62, 0.20, 0.14), (0.86, 0.74, 0.58)]
    for index in range(6):
        x = -1.0 + index * 0.4
        clay = clays[(index + seed) % len(clays)]
        if index % 2:
            drape(builder, clay, [(0.0, 0.82), (0.07, 0.83), (0.11, 0.9), (0.1, 1.02), (0.05, 1.1), (0.055, 1.14)],
                  8, folds=(0, 0.0, 0.0), squash=1.0, center=(x, rng.uniform(-0.2, 0.15)))
        else:
            drape(builder, (0.62, 0.20, 0.14), [(0.0, 0.83), (0.13, 0.84), (0.16, 0.9), (0.17, 0.92)], 9,
                  folds=(0, 0.0, 0.0), squash=1.0, center=(x, rng.uniform(-0.2, 0.15)))
    for index in range(5):
        x = -1.2 + index * 0.55
        amphora(builder, Matrix.Translation((x, -0.95, 0.0)) @ Matrix.Rotation(rng.uniform(-0.1, 0.1), 4, "X"),
                clays[index % len(clays)])
    for index in range(3):
        drape(builder, clays[(index + 2) % 5], [(0.0, 0.0), (0.14, 0.02), (0.2, 0.18), (0.16, 0.3), (0.1, 0.33)], 8,
              folds=(0, 0.0, 0.0), squash=1.0, center=(1.55, -0.5 + index * 0.45))
    builder.merge(person(Look("ochre", hem=0.55, skin=2, hair=2, apron="brown", arms="gesture", belt="brown",
                              seed=seed + 100)), placement(0.0, 0.9, 0.0, math.pi))
    return builder


def cloth_stall(seed=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    stall_frame(builder, seed, (0.92, 0.86, 0.72), (0.42, 0.48, 0.56))
    dyes = [(0.64, 0.28, 0.20), (0.42, 0.49, 0.58), (0.80, 0.71, 0.42), (0.48, 0.50, 0.34), (0.40, 0.16, 0.24),
            (0.93, 0.91, 0.86), (0.74, 0.50, 0.44)]
    for index in range(7):
        x = -1.0 + index * 0.33
        colour = dyes[(index + seed) % len(dyes)]
        tube(builder, [(x, -0.3, 0.92), (x, 0.3, 0.92)], [0.1, 0.1], colour, 6, start_cap=True)
        if index % 2 == 0:
            tube(builder, [(x + 0.1, -0.25, 1.1), (x + 0.1, 0.25, 1.1)], [0.08, 0.08], dyes[(index + 3) % len(dyes)],
                 6, start_cap=True)
    for index in range(5):
        x = -1.1 + index * 0.55
        colour = dyes[(index * 2 + seed) % len(dyes)]
        drop = rng.uniform(0.7, 1.1)
        quad = [(x - 0.22, -0.78, 2.0), (x + 0.22, -0.78, 2.0), (x + 0.24, -0.8, 2.0 - drop), (x - 0.2, -0.76, 2.0 - drop)]
        for side in (-1, 1):
            first = len(builder.polygons)
            builder.oriented(quad, (0, side, 0), MATTE)
            builder.tint(first, colour if side < 0 else tuple(v * 0.85 for v in colour))
    builder.merge(person(Look("woad", hem=0.04, skin=0, hair=0, palla="madder", female=True, sleeves="long",
                              arms="forward", scale=0.95, seed=seed + 100)), placement(0.0, 0.9, 0.0, math.pi))
    return builder


def spectators(arena_x, arena_y, outer_x, outer_y, top, rows=34, seed=7, fill=0.72, spacing=0.52, aisles=16):
    rng = random.Random(seed)
    builder = MeshBuilder()
    step_depth = (1.0 - 0.06) / rows
    step_rise = (top - 3.7) / rows
    for row in range(rows):
        s = 0.06 + step_depth * (row + 0.42)
        height = 3.7 + step_rise * (row + 1)
        semi_x = arena_x + (outer_x - arena_x) * s
        semi_y = arena_y + (outer_y - arena_y) * s
        t = 0.0
        while t < TAU:
            speed = math.hypot(semi_x * math.sin(t), semi_y * math.cos(t))
            step = spacing / max(speed, 1e-3)
            aisle = (t * aisles / TAU) % 1.0
            t += step
            if aisle < 0.06 or rng.random() > fill:
                continue
            centre = Vector((semi_x * math.cos(t), semi_y * math.sin(t), height))
            inward = Vector((-math.cos(t) / semi_x, -math.sin(t) / semi_y, 0.0)).normalized()
            side = Vector((-inward.y, inward.x, 0.0)) * 0.2
            if row < 4:
                colour = SPECTATOR_TONES[0] if rng.random() < 0.8 else SPECTATOR_TONES[rng.randrange(10)]
            else:
                colour = SPECTATOR_TONES[rng.randrange(len(SPECTATOR_TONES))]
            shade = rng.uniform(0.85, 1.05)
            colour = tuple(min(1.0, value * shade) for value in colour)
            crown = centre + Vector((0.0, 0.0, rng.uniform(0.72, 0.86))) + inward * 0.04
            front = centre + inward * 0.16
            shoulders = [crown - side * 0.55, crown + side * 0.55]
            first = len(builder.polygons)
            builder.oriented([front - side, front + side, shoulders[1], shoulders[0]], inward, MATTE)
            builder.tint(first, colour)
    return builder


def gravel(builder, points, rng, grounds):
    stones = [(0.74, 0.70, 0.62), (0.66, 0.62, 0.55), (0.80, 0.76, 0.68), (0.58, 0.53, 0.46), (0.70, 0.64, 0.52)]
    for (x, y, z), ground in zip(points, grounds):
        radius = rng.uniform(0.04, 0.16) if rng.random() < 0.85 else rng.uniform(0.18, 0.32)
        sides = 7
        turn = rng.uniform(0, TAU)
        apex = (x + rng.uniform(-0.2, 0.2) * radius, y + rng.uniform(-0.2, 0.2) * radius,
                z + radius * rng.uniform(0.12, 0.28))
        ring = [(x + radius * rng.uniform(0.75, 1.1) * math.cos(turn + TAU * (k + rng.uniform(-0.2, 0.2)) / sides),
                 y + radius * rng.uniform(0.75, 1.1) * math.sin(turn + TAU * (k + rng.uniform(-0.2, 0.2)) / sides),
                 z - 0.02) for k in range(sides)]
        colour = tuple(0.5 * value * 0.8 + 0.5 * soil for value, soil in zip(stones[rng.randrange(len(stones))], ground))
        first = len(builder.polygons)
        for k in range(sides):
            builder.oriented([ring[k], ring[(k + 1) % sides], apex], (0, 0, 1), MATTE, True)
        builder.tint(first, colour)
    return builder


def painted_dado(length, depth, stylobate=0.45, door_spacing=0.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hl = length / 2
    y = -depth + 0.012
    reds = [(0.62, 0.20, 0.14), (0.70, 0.28, 0.16), (0.56, 0.18, 0.15)]
    ochres = [(0.86, 0.66, 0.36), (0.80, 0.58, 0.30), (0.93, 0.86, 0.70)]
    doors = []
    if door_spacing > 0:
        count = max(int(length / door_spacing), 1)
        doors = [-hl + door_spacing * (index + 0.5) for index in range(count)]

    def panel(x0, x1, z0, z1, colour, offset=0.0):
        quad = [(x0, y + offset, z0), (x1, y + offset, z0), (x1, y + offset, z1), (x0, y + offset, z1)]
        first = len(builder.polygons)
        builder.oriented(quad, (0, 1, 0), "plaster")
        builder.tint(first, colour)

    edges = [-hl + 0.3]
    for door in doors:
        edges += [door - 1.05, door + 1.05]
    edges.append(hl - 0.3)
    for x0, x1 in zip(edges[0::2], edges[1::2]):
        if x1 - x0 < 0.6:
            continue
        panel(x0, x1, stylobate, stylobate + 0.95, reds[rng.randrange(3)])
        panel(x0, x1, stylobate + 0.95, stylobate + 1.02, (0.22, 0.18, 0.15), 0.002)
        bays = max(int((x1 - x0) / 2.6), 1)
        width = (x1 - x0) / bays
        for bay in range(bays):
            a = x0 + width * bay + 0.18
            b = x0 + width * (bay + 1) - 0.18
            colour = ochres[rng.randrange(3)] if bay % 2 == 0 else reds[rng.randrange(3)]
            panel(a, b, stylobate + 1.25, stylobate + 3.2, colour)
            panel(a + 0.1, b - 0.1, stylobate + 1.35, stylobate + 1.4, (0.25, 0.20, 0.16), 0.002)
            panel(a + 0.1, b - 0.1, stylobate + 3.05, stylobate + 3.1, (0.25, 0.20, 0.16), 0.002)
        panel(x0, x1, stylobate + 3.45, stylobate + 3.6, (0.30, 0.42, 0.36))
    for door in doors:
        quad = [(door - 0.8, y + 0.004, stylobate), (door + 0.8, y + 0.004, stylobate),
                (door + 0.8, y + 0.004, stylobate + 2.9), (door - 0.8, y + 0.004, stylobate + 2.9)]
        builder.oriented(quad, (0, 1, 0), VOID)
        for x0, x1, z0, z1 in ((door - 1.0, door - 0.8, stylobate, stylobate + 3.1),
                               (door + 0.8, door + 1.0, stylobate, stylobate + 3.1),
                               (door - 1.0, door + 1.0, stylobate + 2.9, stylobate + 3.15)):
            builder.box((x0, y, z0), (x1, y + 0.1, z1), ASHLAR, bottom=False)
        builder.box((door - 1.0, y, stylobate - 0.02), (door + 1.0, y + 0.5, stylobate + 0.06), ASHLAR, bottom=False)
    return builder


def roadside_shrine():
    builder = MeshBuilder()
    builder.box((-0.6, -0.5, -0.3), (0.6, 0.5, 1.1), WEATHERED, bottom=False)
    builder.box((-0.7, -0.6, 1.1), (0.7, 0.6, 1.25), ASHLAR, bottom=False)
    builder.box((-0.45, -0.35, 1.25), (0.45, 0.35, 2.3), ASHLAR, bottom=False)
    builder.box((-0.3, 0.33, 1.4), (0.3, 0.36, 2.05), VOID, bottom=False)
    builder.oriented([(-0.6, -0.5, 2.3), (0.6, -0.5, 2.3), (0.0, -0.5, 2.7)], (0, -1, 0), ASHLAR)
    builder.oriented([(0.6, 0.5, 2.3), (-0.6, 0.5, 2.3), (0.0, 0.5, 2.7)], (0, 1, 0), ASHLAR)
    builder.oriented([(-0.62, -0.52, 2.28), (-0.62, 0.52, 2.28), (0.0, 0.52, 2.72), (0.0, -0.52, 2.72)], (-1, 0, 1),
                     "terracotta_tiles")
    builder.oriented([(0.62, 0.52, 2.28), (0.62, -0.52, 2.28), (0.0, -0.52, 2.72), (0.0, 0.52, 2.72)], (1, 0, 1),
                     "terracotta_tiles")
    for x, colour in ((-0.45, (0.85, 0.30, 0.22)), (0.4, (0.92, 0.80, 0.36))):
        drape(builder, colour, [(0.06, 1.25), (0.12, 1.33), (0.0, 1.38)], 6, folds=(3, 0.2, x), squash=1.0,
              center=(x, 0.45), material=ASHLAR)
    return builder


def bench_and_jars(seed=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.box((-1.1, -0.22, 0.0), (1.1, 0.22, 0.45), ASHLAR, bottom=False)
    for index in range(3):
        amphora(builder, Matrix.Translation((1.5 + index * 0.35, rng.uniform(-0.1, 0.1), 0.0)),
                [TERRACOTTA, (0.78, 0.55, 0.40), (0.66, 0.40, 0.27)][index])
    tube(builder, [(-0.6, 0.0, 0.45), (-0.6, 0.0, 0.62)], [0.12, 0.1], LEATHER, 6)
    return builder


def umbrella_pine(height=13.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    base = height * 0.66
    lean = (rng.uniform(0.4, 1.1), rng.uniform(-0.5, 0.5))
    trunk(builder, base + 0.6, 0.26, lean)
    lobe(builder, (lean[0], lean[1], base + 1.3), height * 0.3, 2.4, "foliage_dark", 8, seed, 0.3)
    lobe(builder, (lean[0] - 2.2, lean[1] - 0.8, base + 0.2), height * 0.2, 1.9, "foliage_dark", 6, seed + 1, 0.3)
    lobe(builder, (lean[0] + 1.6, lean[1] + 1.5, base + 2.1), height * 0.17, 1.6, "foliage_dark", 6, seed + 2, 0.3)
    return builder
