import math
import random

import numpy as np
from mathutils import Matrix, Vector

from .arles_life import PEOPLE, Person, ellipsoid, person, tube
from .buildings import TILES
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, WOOD, painted
from .orders import STONE, simple_entablature_profile

COATS = [(0.42, 0.26, 0.16), (0.30, 0.20, 0.13), (0.66, 0.62, 0.56), (0.17, 0.13, 0.11), (0.55, 0.35, 0.19),
         (0.48, 0.40, 0.33)]
FACTIONS = {"russata": (0.68, 0.18, 0.13), "albata": (0.92, 0.9, 0.84), "prasina": (0.3, 0.5, 0.27),
            "veneta": (0.25, 0.36, 0.62)}
TUFT = (0.58, 0.55, 0.34)
TUFT_GREEN = (0.4, 0.46, 0.24)


def darker(colour, factor=0.55):
    return tuple(component * factor for component in colour)


def horse(coat, gait="stand", seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    dark = darker(coat)
    body_z = 1.24 if gait == "gallop" else 1.18
    ellipsoid(builder, (0.0, 0.0, body_z), (0.26, 0.72, 0.31), coat, 9, 6)
    ellipsoid(builder, (0.0, 0.46, body_z + 0.05), (0.24, 0.32, 0.33), coat, 7, 4)
    ellipsoid(builder, (0.0, -0.48, body_z + 0.04), (0.27, 0.32, 0.32), coat, 7, 4)
    shoulder = Vector((0.0, 0.6, body_z + 0.16))
    if gait == "gallop":
        poll = Vector((0.0, 1.1, body_z + 0.6))
        muzzle = Vector((0.0, 1.46, body_z + 0.3))
    else:
        poll = Vector((0.0, 0.96, body_z + 0.8))
        muzzle = Vector((0.0, 1.24, body_z + 0.42))
    tube(builder, shoulder, poll, 0.17, 0.1, coat, 6)
    tube(builder, poll, muzzle, 0.1, 0.06, coat, 6)
    ellipsoid(builder, muzzle, (0.06, 0.07, 0.065), dark, 5, 2)
    tube(builder, shoulder + Vector((0.0, -0.1, 0.15)), poll + Vector((0.0, -0.04, 0.07)), 0.04, 0.03, dark, 3)
    for side in (-1, 1):
        tube(builder, poll + Vector((side * 0.05, -0.03, 0.04)), poll + Vector((side * 0.08, -0.06, 0.17)), 0.025,
             0.01, coat, 3)
    if gait == "gallop":
        legs = {(1, 1): ((0.95, 0.78), (1.28, 0.42)), (-1, 1): ((0.74, 0.66), (0.56, 0.5)),
                (1, -1): ((-0.88, 0.62), (-1.28, 0.24)), (-1, -1): ((-0.38, 0.56), (-0.18, 0.06))}
    else:
        legs = {(side, end): ((end * 0.5 + 0.02, 0.5), (end * 0.5, 0.0)) for side in (-1, 1) for end in (-1, 1)}
    for (side, end), ((knee_y, knee_z), (hoof_y, hoof_z)) in legs.items():
        top = Vector((side * 0.13, end * 0.5, body_z - 0.12))
        knee = Vector((side * 0.13, knee_y, knee_z))
        hoof = Vector((side * 0.13, hoof_y, hoof_z))
        tube(builder, top, knee, 0.085, 0.05, coat, 5)
        tube(builder, knee, hoof, 0.042, 0.036, dark if rng.random() < 0.7 else coat, 4)
    tail_end = Vector((0.0, -1.38, body_z - 0.02)) if gait == "gallop" else Vector((0.0, -0.9, body_z - 0.55))
    tube(builder, (0.0, -0.76, body_z + 0.16), tail_end, 0.055, 0.02, dark, 4)
    return builder


def chariot(builder, colour):
    wood = (0.42, 0.3, 0.2)
    for side in (-1, 1):
        rim = Matrix.Translation((side * 0.62, 0.0, 0.45)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        painted(builder, wood, lambda rim=rim: builder.lathe([(0.0, -0.035), (0.45, -0.035), (0.45, 0.035),
                                                              (0.0, 0.035)], 10, MATTE, smooth=False, matrix=rim,
                                                             caps=False))
    tube(builder, (-0.66, 0.0, 0.45), (0.66, 0.0, 0.45), 0.03, 0.03, wood, 4)
    painted(builder, wood, lambda: builder.box((-0.42, -0.22, 0.42), (0.42, 0.45, 0.48), MATTE))
    painted(builder, colour, lambda: builder.lathe([(0.45, 0.48), (0.45, 1.0)], 6, MATTE, smooth=True,
                                                   matrix=placement(0.0, 0.0, 0.0), start=0.0, sweep=math.pi,
                                                   caps=False))
    tube(builder, (0.0, 0.42, 0.5), (0.0, 3.0, 1.32), 0.045, 0.035, wood, 4)
    tube(builder, (-1.25, 3.0, 1.36), (1.25, 3.0, 1.36), 0.04, 0.04, wood, 4)


def quadriga(colour, gait="gallop", seed=0, driver=True):
    builder = MeshBuilder()
    chariot(builder, colour)
    rng = random.Random(seed)
    muzzles = []
    for index, x in enumerate((-1.2, -0.4, 0.4, 1.2)):
        coat = COATS[rng.randrange(len(COATS))]
        stagger = rng.uniform(-0.12, 0.12)
        builder.merge(horse(coat, gait, seed * 10 + index), placement(x, 2.3 + stagger, 0.0))
        muzzles.append(Vector((x, 2.3 + stagger + (1.46 if gait == "gallop" else 1.24),
                               (1.54 if gait == "gallop" else 1.6))))
    if driver:
        spec = Person(colour, hem=0.55, skin=rng.randrange(3), hair=rng.randrange(4), belt="dark", cap="pileus",
                      pose="forward", stride=0.16, seed=seed + 90)
        frame = placement(0.0, 0.0, 0.48) @ Matrix.Rotation(-0.22 if gait == "gallop" else -0.05, 4, "X")
        builder.merge(person(spec), frame)
        hands = [frame @ Vector((side * 0.17, 0.36, 1.1)) for side in (-1, 1)]
        for index, muzzle in enumerate(muzzles):
            tube(builder, hands[0 if index < 2 else 1], muzzle, 0.01, 0.01, LEATHER, 3, caps=False)
    return builder


def race(seed=5):
    builder = MeshBuilder()
    slots = [((0.0, 0.0), "russata"), ((3.0, -6.0), "prasina"), ((-0.6, -12.5), "veneta"), ((3.6, -18.0), "albata")]
    for index, ((x, y), faction) in enumerate(slots):
        builder.merge(quadriga(FACTIONS[faction], "gallop", seed + index), placement(x, y, 0.0, 0.0))
    return builder


def groom(seed, colour="brown"):
    return person(Person(colour, hem=0.52, skin=seed % 4, hair=seed % 5, beard=seed % 2 == 0, belt="dark",
                         pose="lead", seed=seed))


def waiting_team(faction, seed=0):
    builder = quadriga(FACTIONS[faction], "stand", seed, driver=True)
    for side in (-1, 1):
        builder.merge(groom(seed + side + 3, "undyed" if side < 0 else "ochre"),
                      placement(side * 1.8, 3.3, 0.0, side * math.pi / 2))
    return builder


def led_horse(seed=0):
    builder = MeshBuilder()
    rng = random.Random(seed)
    builder.merge(groom(seed + 11, ["brown", "undyed", "ochre"][seed % 3]))
    builder.merge(horse(COATS[rng.randrange(len(COATS))], "stand", seed), placement(0.62, -0.95, 0.0))
    tube(builder, (0.25, 0.43, 1.06), (0.62, 0.29, 1.62), 0.01, 0.01, LEATHER, 3, caps=False)
    return builder


def litter(seed=0, curtain=(0.55, 0.16, 0.14)):
    builder = MeshBuilder()
    bearers = ["fig_worker", "fig_worker_b", "fig_sailor", "fig_porter_sack_b"]
    for index, (x, y) in enumerate(((-0.55, 1.45), (0.55, 1.45), (-0.55, -1.45), (0.55, -1.45))):
        spec = PEOPLE[bearers[(index + seed) % 4]]
        carrier = Person(spec.garment, hem=0.55, skin=spec.skin, hair=spec.hair, beard=spec.beard, belt="dark",
                         pose="shoulder", stride=0.14, seed=seed * 5 + index, sleeves=False)
        builder.merge(person(carrier), placement(x, y, 0.0, 0.0))
    for x in (-0.42, 0.42):
        tube(builder, (x, -2.2, 1.66), (x, 2.2, 1.66), 0.045, 0.045, WOOD, 4)
    painted(builder, (0.5, 0.36, 0.24), lambda: builder.box((-0.4, -0.95, 1.2), (0.4, 0.95, 1.45), MATTE))
    for x in (-0.38, 0.38):
        for y in (-0.92, 0.92):
            tube(builder, (x, y, 1.45), (x, y, 2.45), 0.025, 0.025, WOOD, 3, caps=False)
    painted(builder, curtain, lambda: builder.box((-0.45, -1.0, 2.45), (0.45, 1.0, 2.55), MATTE))
    for side in (-1, 1):
        for facing in (1, -1):
            quad = [(side * 0.4, -0.9, 1.45), (side * 0.4, 0.9, 1.45), (side * 0.4, 0.9, 2.45),
                    (side * 0.4, -0.9, 2.45)]
            builder.polygon(quad if facing * side > 0 else list(reversed(quad)), MATTE,
                            color=darker(curtain, 0.85 if facing > 0 else 0.6))
    ellipsoid(builder, (0.0, 0.3, 1.62), (0.2, 0.55, 0.16), (0.88, 0.85, 0.78), 6, 3)
    ellipsoid(builder, (0.0, 0.75, 1.85), (0.08, 0.09, 0.1), (0.8, 0.6, 0.48), 6, 3)
    return builder


def portico_ornament(length, depth=8.0, column_height=6.4, step=0.52, doors=None):
    builder = MeshBuilder()
    hl = length / 2
    top = 0.45 + column_height
    beam = 0.95
    eave_z = top + beam
    ridge_z = top + beam + 2.5
    front, back = 0.9, -depth - 0.9
    run = Vector((0.0, back - front, ridge_z - eave_z))
    normal = Vector((0.0, ridge_z - eave_z, front - back)).normalized()
    for x in np.arange(-hl + 0.3, hl - 0.2, step):
        x = float(x)
        start = Vector((x, front, eave_z))
        rows = []
        for t in (0.0, 1.0):
            point = start + run * t
            rows.append([point + Vector((-0.1, 0.0, 0.0)), point + Vector((0.0, 0.0, 0.0)) + normal * 0.075,
                         point + Vector((0.1, 0.0, 0.0))])
        first = len(builder.polygons)
        builder.surface(rows, TILES, facing=(0, 0, 1))
        builder.tint(first, (0.86, 0.76, 0.7))
        tip = [(x - 0.11, front + 0.02, eave_z - 0.02), (x + 0.11, front + 0.02, eave_z - 0.02),
               (x, front + 0.05, eave_z + 0.26)]
        first = len(builder.polygons)
        builder.oriented(tip, (0, 1, 0), TILES)
        builder.oriented(list(reversed(tip)), (0, -1, 0), TILES)
        builder.tint(first, (0.92, 0.8, 0.72))
    cornice = top + beam * 0.72
    for x in np.arange(-hl + 0.2, hl - 0.1, 0.27):
        builder.box((float(x) - 0.065, 0.38, cornice - 0.16), (float(x) + 0.065, 0.49, cornice - 0.02), STONE,
                    top=False)
    for z in (top + 0.2, top + 0.4):
        builder.box((-hl, 0.38, z), (hl, 0.405, z + 0.025), STONE, bottom=False)
    wall = -depth + 0.012
    openings = sorted(doors or [])
    edges = [-hl + 0.4] + [value for x in openings for value in (x - 1.45, x + 1.45)] + [hl - 0.4]
    for index, (x0, x1) in enumerate(zip(edges[0::2], edges[1::2])):
        if x1 - x0 < 0.8:
            continue
        builder.polygon([(x0, wall, 0.46), (x1, wall, 0.46), (x1, wall, 1.55), (x0, wall, 1.55)], MATTE,
                        color=(0.5, 0.17, 0.12))
        builder.polygon([(x0, wall, 1.55), (x1, wall, 1.55), (x1, wall, 1.68), (x0, wall, 1.68)], MATTE,
                        color=(0.16, 0.12, 0.1))
        panels = max(int((x1 - x0) / 2.4), 1)
        width = (x1 - x0) / panels
        for k in range(panels):
            p0, p1 = x0 + k * width + 0.18, x0 + (k + 1) * width - 0.18
            tone = (0.74, 0.52, 0.24) if (k + index) % 2 else (0.62, 0.2, 0.14)
            builder.polygon([(p0 - 0.08, wall, 1.92), (p1 + 0.08, wall, 1.92), (p1 + 0.08, wall, 4.72),
                             (p0 - 0.08, wall, 4.72)], MATTE, color=(0.18, 0.13, 0.11))
            builder.polygon([(p0, wall + 0.004, 2.0), (p1, wall + 0.004, 2.0), (p1, wall + 0.004, 4.64),
                             (p0, wall + 0.004, 4.64)], MATTE, color=tone)
    return builder


def raking_cornice(builder, half_width, y, eave_z, apex_z, facing):
    profile = simple_entablature_profile(0.42, 0.3)
    left = Vector((-half_width, y, eave_z))
    apex = Vector((0.0, y, apex_z))
    right = Vector((half_width, y, eave_z))
    for a, b in ((left, apex), (apex, right)):
        path = [a, b] if facing > 0 else [b, a]
        builder.sweep(path, profile, STONE, facade_normal=(0, facing, 0))
    for x, z, size in ((0.0, apex_z + 0.3, 1.0), (-half_width, eave_z + 0.2, 0.62), (half_width, eave_z + 0.2, 0.62)):
        builder.lathe([(0.0, 0.0), (0.32 * size, 0.08), (0.2 * size, 0.5 * size), (0.42 * size, 1.05 * size),
                       (0.22 * size, 1.3 * size), (0.0, 1.45 * size)], 6, STONE, smooth=True,
                      matrix=Matrix.Translation((x, y, z)))


def side_antefixes(builder, x, y0, y1, z, outward, step=0.55):
    for y in np.arange(min(y0, y1) + 0.3, max(y0, y1) - 0.2, step):
        tip = [(x, float(y) - 0.11, z - 0.02), (x, float(y) + 0.11, z - 0.02), (x + outward * 0.03, float(y), z + 0.26)]
        first = len(builder.polygons)
        builder.oriented(tip, (outward, 0, 0), TILES)
        builder.oriented(list(reversed(tip)), (-outward, 0, 0), TILES)
        builder.tint(first, (0.92, 0.8, 0.72))


def tuft(seed=0):
    builder = MeshBuilder()
    rng = random.Random(seed)
    for k in range(9):
        angle = 2 * math.pi * k / 9 + rng.uniform(-0.4, 0.4)
        lean = rng.uniform(0.08, 0.22)
        height = rng.uniform(0.16, 0.38)
        base = Vector((0.05 * math.cos(angle) + rng.uniform(-0.04, 0.04), 0.05 * math.sin(angle), -0.04))
        tip = base + Vector((lean * math.cos(angle), lean * math.sin(angle), height))
        side = Vector((-math.sin(angle), math.cos(angle), 0.0)) * 0.025
        blade = TUFT if k % 3 else TUFT_GREEN
        colour = tuple(component * rng.uniform(0.8, 1.12) for component in blade)
        for facing in (1, -1):
            points = [base - side, base + side, tip]
            builder.polygon(points if facing > 0 else list(reversed(points)), MATTE, color=colour)
    return builder


def scatter_line(points, spacing, offset, rng, jitter=0.6, keep=0.6):
    out = []
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 1e-6:
            continue
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        for along in np.arange(0.0, length, spacing):
            if rng.random() > keep:
                continue
            side = offset + rng.uniform(-jitter, jitter)
            out.append((x0 + dx * float(along) - dy * side, y0 + dy * float(along) + dx * side))
    return out


def mensa(seed=0):
    builder = MeshBuilder()
    rng = random.Random(seed)
    painted(builder, WOOD, lambda: builder.box((-0.7, -0.35, 0.72), (0.7, 0.35, 0.8), MATTE))
    for x in (-0.6, 0.6):
        for y in (-0.27, 0.27):
            tube(builder, (x, y, 0.0), (x, y, 0.72), 0.03, 0.03, WOOD, 4, caps=False)
    for index in range(5):
        ellipsoid(builder, (-0.4 + index * 0.2, rng.uniform(-0.1, 0.1), 0.81), (0.05, 0.05, 0.015),
                  (0.72, 0.6, 0.32), 5, 1, low=0.5)
    painted(builder, (0.86, 0.8, 0.62), lambda: builder.box((0.2, -0.15, 0.8), (0.45, 0.15, 0.82), MATTE))
    builder.merge(person(PEOPLE["fig_seated_tunic"]), placement(0.0, -0.75, 0.45, 0.0))
    painted(builder, WOOD, lambda: builder.box((-0.25, -0.95, 0.0), (0.25, -0.55, 0.42), MATTE))
    return builder


DETAIL_BUILDS = {"tuft": lambda: tuft(1)}


def recast(builder, mapping):
    names = list(builder.materials)
    targets = {}
    for index, name in enumerate(names):
        target, tint = mapping.get(name, (name, None))
        targets[index] = (target, tint)
    builder.materials = []
    for polygon_index, material_index in enumerate(builder.polygon_materials):
        target, tint = targets[material_index]
        builder.polygon_materials[polygon_index] = builder.slot(target)
        if tint is not None:
            current = builder.polygon_colors[polygon_index] or (1.0, 1.0, 1.0)
            builder.polygon_colors[polygon_index] = tuple(a * b for a, b in zip(current, tint))
    return builder


def bisellia(radius, z, ranges, per_range=4):
    builder = MeshBuilder()
    seats = []
    for a0, a1 in ranges:
        for k in range(per_range):
            angle = a0 + (a1 - a0) * (k + 0.5) / per_range
            x, y = radius * math.cos(angle), radius * math.sin(angle)
            turn = math.atan2(-(0.0 - x), 4.0 - y)
            frame = placement(x, y, z, turn)
            painted(builder, (0.93, 0.9, 0.84), lambda frame=frame: builder.centered_box(
                (0.0, 0.0, 0.19), (0.6, 0.45, 0.38), "lens_smooth", matrix=frame, bottom=False))
            painted(builder, (0.55, 0.16, 0.14), lambda frame=frame: builder.centered_box(
                (0.0, 0.0, 0.4), (0.56, 0.42, 0.04), MATTE, matrix=frame, bottom=False))
            seats.append((x, y, z + 0.42, turn))
    return builder, seats
