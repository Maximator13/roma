import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .life import SKIN
from .nimes_figures import POSES, Look, drape, ellipsoid, person, tube
from .olympie_doric import (STUCCO, SIMA_RED, TAENIA, TYMPANUM, Peripteral, box, cella_box, doric_column, painted)

POSES.update({
    "olym_spear": [((0.27, 0.1, 1.2), (0.3, 0.22, 1.45)), ((-0.24, 0.02, 1.1), (-0.25, 0.12, 0.9))],
    "olym_raise": [((0.3, 0.05, 1.5), (0.32, 0.1, 1.85)), ((-0.24, 0.02, 1.1), (-0.25, 0.12, 0.9))],
    "olym_fight": [((0.3, 0.2, 1.35), (0.36, 0.45, 1.55)), ((-0.3, 0.15, 1.3), (-0.4, 0.3, 1.5))],
    "olym_bow": [((0.24, 0.24, 1.25), (0.1, 0.42, 1.3)), ((-0.26, 0.2, 1.3), (-0.3, 0.5, 1.4))],
    "olym_run": [((0.24, 0.2, 1.15), (0.2, 0.36, 1.32)), ((-0.24, -0.18, 1.12), (-0.24, -0.3, 0.94))],
    "olym_cheer": [((0.3, 0.06, 1.55), (0.28, 0.14, 1.88)), ((-0.3, 0.06, 1.55), (-0.28, 0.14, 1.88))],
})

LENGTH = 64.12
WIDTH = 27.68
STEP = 0.507
GROUND_TO_STYLOBATE = 3 * STEP
CELLA_FLOOR = 0.6
NAOS_X = 23.42
NAOS_Y = 8.195
CELLA_X = 14.37
WALL = 1.665
NAVE_Y = 4.07
LOWER_TOP = 7.4
GALLERY = 8.45
UPPER_TOP = 13.4
CEILING = 14.6
BASE_X = (-13.95, -4.02)
POOL_X = (-4.02, 5.4)
POOL_Y = 3.32
IVORY = (1.0, 1.0, 1.0)
EBONY = (0.09, 0.06, 0.05)
DADO = (0.55, 0.12, 0.08)
WALL_OCHRE = (0.93, 0.82, 0.62)
COFFER = (0.10, 0.20, 0.55)
BEAM = (0.36, 0.20, 0.12)
MARBLE_SKIN = (1.0, 0.9, 0.78)
SPANS = [(-CELLA_X + k * CELLA_X / 3.5, -CELLA_X + (k + 1) * CELLA_X / 3.5) for k in range(7)]


def gloom(x):
    t = min(1.0, max(0.0, (x + CELLA_X) / (2 * CELLA_X + 1.0)))
    return 0.26 + 0.5 * t * t * (3 - 2 * t)


def darken_interior(builder, first=0):
    inner = NAOS_Y - WALL + 0.1
    for index in range(first, len(builder.polygons)):
        points = [builder.positions[v] for v in builder.polygons[index]]
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        if abs(y) > inner or x < -CELLA_X - 0.1 or x > CELLA_X + 0.6:
            continue
        factor = gloom(x)
        current = builder.polygon_colors[index] or (1.0, 1.0, 1.0)
        builder.polygon_colors[index] = tuple(c * factor for c in current)


def layout():
    return Peripteral(LENGTH, WIDTH, 6, 13, 2.25, 10.53, 1.77, 1.74, 0.645, 3, STEP, 3.75, front_spacing=5.22,
                      flank_spacing=5.22, material="plaster", roof="marble", tile_pitch=0.78)


def shields_spec():
    return {(1, 0): tuple(range(10)), (0, -1): tuple(range(13, 24))}


def exterior(temple):
    builder = MeshBuilder()
    temple.krepis(builder, 1.8)
    eave_x, eave_y = temple.entablature(builder, shields_spec())
    apex = temple.pediments(builder, eave_x, eave_y)
    temple.roof_cover(builder, eave_x, eave_y)
    inner_x = temple.half_x - 0.42 * temple.d
    inner_y = temple.half_y - 0.42 * temple.d
    z0 = temple.frieze_top - 0.35
    for x0, x1, y0, y1 in ((NAOS_X, inner_x, -inner_y, inner_y), (-inner_x, -NAOS_X, -inner_y, inner_y),
                           (-NAOS_X, NAOS_X, NAOS_Y, inner_y), (-NAOS_X, NAOS_X, -inner_y, -NAOS_Y)):
        painted(builder, COFFER, lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box((x0, y0, z0), (x1, y1,
                                                                                               temple.frieze_top),
                                                                               "plaster"))
    for k in range(int((2 * inner_x) / 2.6) + 1):
        x = -inner_x + k * 2.6
        for y0, y1 in ((NAOS_Y, inner_y), (-inner_y, -NAOS_Y)):
            painted(builder, (0.85, 0.8, 0.7), lambda x=x, y0=y0, y1=y1: builder.box(
                (x - 0.18, y0, z0 - 0.3), (x + 0.18, y1, z0), "plaster", bottom=True))
    ramp_x0 = LENGTH / 2 + 3 * STEP * 1.05
    a = builder.points([(ramp_x0 - 0.4, -3.4, -0.02), (ramp_x0 - 0.4, 3.4, -0.02), (ramp_x0 + 11.0, 3.4,
                                                                                  -GROUND_TO_STYLOBATE - 0.05),
                        (ramp_x0 + 11.0, -3.4, -GROUND_TO_STYLOBATE - 0.05)])
    builder.face([a[0], a[3], a[2], a[1]], "limestone")
    for side in (-1, 1):
        builder.oriented([(ramp_x0 - 0.4, side * 3.4, -0.02), (ramp_x0 + 11.0, side * 3.4, -GROUND_TO_STYLOBATE - 0.05),
                          (ramp_x0 + 11.0, side * 3.4, -GROUND_TO_STYLOBATE - 1.0),
                          (ramp_x0 - 0.4, side * 3.4, -GROUND_TO_STYLOBATE - 1.0)], (0, side, 0), "limestone")
    return builder, apex, (eave_x, eave_y)


def naos(temple):
    builder = MeshBuilder()
    floor_z = CELLA_FLOOR
    cella_box(builder, -NAOS_X, NAOS_X, NAOS_Y, WALL, CEILING + 0.4, "plaster", STUCCO, closed_ends=(False, False))
    for x0, x1 in ((CELLA_X, CELLA_X + 1.15), (-CELLA_X - 1.15, -CELLA_X)):
        door = 5.0 if x0 > 0 else None
        if door:
            painted(builder, STUCCO, lambda x0=x0, x1=x1: builder.box((x0, -NAOS_Y + WALL, 0.0), (x1, -door / 2,
                                                                                                    CEILING + 0.4),
                                                                      "plaster", bottom=False))
            painted(builder, STUCCO, lambda x0=x0, x1=x1: builder.box((x0, door / 2, 0.0), (x1, NAOS_Y - WALL,
                                                                                              CEILING + 0.4),
                                                                      "plaster", bottom=False))
            painted(builder, STUCCO, lambda x0=x0, x1=x1: builder.box((x0, -door / 2, 9.6), (x1, door / 2,
                                                                                               CEILING + 0.4),
                                                                      "plaster", bottom=False))
        else:
            painted(builder, STUCCO, lambda x0=x0, x1=x1: builder.box((x0, -NAOS_Y + WALL, 0.0), (x1, NAOS_Y - WALL,
                                                                                                    CEILING + 0.4),
                                                                      "plaster", bottom=False))
    inner = NAOS_Y - WALL
    for x0, x1 in SPANS:
        for side in (-1, 1):
            y = side * (inner - 0.03)
            painted(builder, DADO, lambda y=y: builder.box((x0, min(y, y - side * 0.02), floor_z),
                                                           (x1, max(y, y - side * 0.02), floor_z + 1.6), "plaster",
                                                           bottom=False))
            painted(builder, WALL_OCHRE, lambda y=y: builder.box((x0, min(y, y - side * 0.015), floor_z + 1.6),
                                                                 (x1, max(y, y - side * 0.015), GALLERY), "plaster",
                                                                 bottom=False))
            painted(builder, TAENIA, lambda y=y: builder.box((x0, min(y, y - side * 0.03), GALLERY - 0.3),
                                                             (x1, max(y, y - side * 0.03), GALLERY), "plaster",
                                                             bottom=False))
    painted(builder, DADO, lambda: builder.box((-CELLA_X - 0.02, -inner, floor_z), (-CELLA_X, inner, floor_z + 1.6),
                                               "plaster", bottom=False))
    for x0, x1 in ((-CELLA_X, BASE_X[0]), (POOL_X[1], CELLA_X)):
        builder.box((x0, -inner, 0.0), (x1, inner, floor_z), "paving", bottom=False)
    for y0, y1 in ((-inner, -POOL_Y - 0.3), (POOL_Y + 0.3, inner)):
        builder.box((BASE_X[0], y0, 0.0), (POOL_X[1], y1, floor_z), "paving", bottom=False)
    builder.box((POOL_X[0], -POOL_Y - 0.3, 0.0), (POOL_X[1], POOL_Y + 0.3, floor_z - 0.06), "oil",
                bottom=False)
    for x0, x1, y0, y1 in ((POOL_X[0], POOL_X[1], -POOL_Y - 0.3, -POOL_Y), (POOL_X[0], POOL_X[1], POOL_Y, POOL_Y + 0.3),
                           (POOL_X[1] - 0.3, POOL_X[1], -POOL_Y, POOL_Y)):
        builder.box((x0, y0, floor_z - 0.1), (x1, y1, floor_z + 0.14), "marble", bottom=False)
    for x0, x1 in ((CELLA_X + 1.15, NAOS_X), (-NAOS_X, -CELLA_X - 1.15)):
        builder.box((x0, -inner - 0.2, 0.0), (x1, inner + 0.2, floor_z), "paving", bottom=False)
    for x_face, sign in ((NAOS_X - 0.05, 1), (-NAOS_X + 0.05, -1)):
        for k in range(2):
            z0 = floor_z - (k + 1) * 0.3
            builder.box((min(x_face, x_face + sign * 0.5 * (k + 1)), -inner - 0.2, z0),
                        (max(x_face, x_face + sign * 0.5 * (k + 1)), inner + 0.2, z0 + 0.3), "limestone",
                        bottom=False)
    for side, (a, b) in ((side, span) for side in (-1, 1) for span in SPANS):
        y = side * NAVE_Y
        painted(builder, STUCCO, lambda y=y, a=a, b=b: builder.box((a, y - 0.62, LOWER_TOP), (b, y + 0.62,
                                                                                            LOWER_TOP + 0.8), "plaster"))
        painted(builder, TAENIA, lambda y=y, a=a, b=b: builder.box((a, y - 0.64, LOWER_TOP + 0.62),
                                                                   (b, y + 0.64, LOWER_TOP + 0.72), "plaster"))
        y0, y1 = sorted((side * (NAVE_Y - 0.62), side * inner))
        painted(builder, BEAM, lambda y0=y0, y1=y1, a=a, b=b: builder.box((a, y0, GALLERY - 0.25), (b, y1, GALLERY),
                                                                          "matte", bottom=True))
        rail_y = side * (NAVE_Y - 0.5)
        painted(builder, (0.48, 0.12, 0.08), lambda rail_y=rail_y, a=a, b=b: builder.box(
            (a, rail_y - 0.06, GALLERY), (b, rail_y + 0.06, GALLERY + 1.05), "matte"))
        painted(builder, STUCCO, lambda y=y, a=a, b=b: builder.box((a, y - 0.48, UPPER_TOP), (b, y + 0.48,
                                                                                            UPPER_TOP + 0.7),
                                                                   "plaster"))
    for a, b in SPANS:
        painted(builder, COFFER, lambda a=a, b=b: builder.box((a, -inner, CEILING), (b, inner, CEILING + 0.3),
                                                              "plaster", bottom=True))
    for k in range(13):
        x = -CELLA_X + 1.1 + k * 2.2
        painted(builder, BEAM, lambda x=x: builder.box((x - 0.22, -inner, CEILING - 0.45), (x + 0.22, inner, CEILING),
                                                       "matte", bottom=True))
    for side in (-1, 1):
        for k in range(6):
            x = -CELLA_X + 2.2 + k * 4.8
            y = side * (inner - 0.6)
            painted(builder, (0.95, 0.75, 0.3), lambda x=x, y=y: builder.box((x - 0.05, y - 0.05, CEILING - 0.05),
                                                                            (x + 0.05, y + 0.05, CEILING),
                                                                            "bronze_gilt"))
    for side in (-1, 1):
        hinge_y = side * 2.5
        leaf = Matrix.Translation((CELLA_X, hinge_y, floor_z)) @ Matrix.Rotation(side * math.radians(-80), 4, "Z")
        painted(builder, (0.85, 0.62, 0.4), lambda leaf=leaf, side=side: builder.box(
            (-0.08, -side * 2.5 if side < 0 else -2.5, 0.0), (0.08, 0.0 if side < 0 else 0.0, 9.0), "bronze",
            matrix=leaf))
    darken_interior(builder)
    return builder


def oil_lamp(height=1.7):
    builder = MeshBuilder()
    for k in range(3):
        angle = 2 * math.pi * k / 3
        tube(builder, [(0.0, 0.0, 0.25), (math.cos(angle) * 0.3, math.sin(angle) * 0.3, 0.0)], [0.025, 0.02],
             (1.0, 1.0, 1.0), 4, "bronze")
    tube(builder, [(0.0, 0.0, 0.0), (0.0, 0.0, height)], [0.035, 0.028], (1.0, 1.0, 1.0), 5, "bronze")
    builder.lathe([(0.0, height), (0.2, height + 0.02), (0.24, height + 0.1), (0.2, height + 0.12)], 8, "bronze_gilt")
    for k in range(3):
        angle = 2 * math.pi * k / 3 + 0.3
        centre = Vector((math.cos(angle) * 0.24, math.sin(angle) * 0.24, height + 0.2))
        ellipsoid(builder, centre, (0.045, 0.045, 0.11), (1.0, 1.0, 1.0), 5, 3, "flame")
    return builder


def lamp_positions():
    return [(x, side * 3.0, CELLA_FLOOR) for x in (-1.0, 3.2, 7.4, 11.6) for side in (-1, 1)]


def furnishings():
    builder = MeshBuilder()
    floor = CELLA_FLOOR
    purple = (0.38, 0.06, 0.22)
    rows = []
    for k in range(10):
        x = -12.6 + k * 0.8
        row = []
        for j in range(5):
            y = 5.0 + j * 0.28
            z = floor + 0.02 + 0.32 * abs(math.sin(j * 1.3 + k * 0.9)) * (1.0 - j / 5.0) + 0.06 * math.sin(k * 2.1)
            row.append(Vector((x, y, z)))
        rows.append(row)
    first = len(builder.polygons)
    builder.surface(rows, "matte", smooth=True, facing=(0.0, 0.0, 1.0))
    builder.tint(first, purple)
    first = len(builder.polygons)
    builder.box((-12.6, 4.95, floor), (-5.4, 5.05, floor + 0.08), "matte")
    builder.tint(first, (0.86, 0.66, 0.24))
    builder.box((7.6, -5.75, floor), (8.6, -4.75, floor + 1.1), "marble", bottom=False)
    amber = Look((0.86, 0.48, 0.12), hem=0.1, skin=0, hair=1, toga=(0.9, 0.52, 0.14), arms="toga_gesture",
                 mono=(0.9, 0.5, 0.12), material="ivory", seed=77)
    builder.merge(person(amber), Matrix.Translation((8.1, -5.25, floor + 1.1)) @ Matrix.Scale(0.62, 4)
                  @ Matrix.Rotation(math.pi, 4, "Z"))
    first = len(builder.polygons)
    builder.box((7.0, 4.75, floor + 0.88), (9.4, 5.75, floor + 0.96), "matte")
    for x in (7.15, 9.25):
        for y in (4.9, 5.6):
            builder.box((x - 0.05, y - 0.05, floor), (x + 0.05, y + 0.05, floor + 0.88), "matte")
    builder.tint(first, (0.36, 0.22, 0.14))
    crowns = ((0.42, 0.56, 0.24), (0.42, 0.56, 0.24), (0.42, 0.56, 0.24), (0.30, 0.42, 0.16))
    for k, colour in enumerate(crowns):
        centre = Vector((7.45 + k * 0.6, 5.25, floor + 0.99))
        for j in range(10):
            angle = 2 * math.pi * j / 10
            ellipsoid(builder, centre + Vector((math.cos(angle) * 0.2, math.sin(angle) * 0.2, 0.0)), (0.07, 0.04, 0.03),
                      colour, 5, 3)
    darken_interior(builder)
    return builder


def interior_columns():
    lower = []
    upper = []
    for side in (-1, 1):
        for k in range(7):
            x = -10.5 + 3.5 * k
            lower.append((x, side * NAVE_Y, CELLA_FLOOR))
            upper.append((x, side * NAVE_Y, GALLERY))
    return lower, upper


def antis_columns():
    return [(x, y, CELLA_FLOOR - 0.0) for x in (NAOS_X - 0.95, -NAOS_X + 0.95) for y in (-3.3, 3.3)]


def statue_base():
    builder = MeshBuilder()
    length = BASE_X[1] - BASE_X[0]
    width = 6.65
    builder.box((-length / 2, -width / 2, 0.0), (length / 2, width / 2, 1.05), "dark_stone", bottom=False)
    builder.box((-length / 2 - 0.12, -width / 2 - 0.12, 0.0), (length / 2 + 0.12, width / 2 + 0.12, 0.18),
                "marble", bottom=False)
    builder.box((-length / 2 - 0.1, -width / 2 - 0.1, 0.92), (length / 2 + 0.1, width / 2 + 0.1, 1.08), "marble")
    builder.box((length / 2 + 0.005, -width / 2 + 0.3, 0.3), (length / 2 + 0.04, width / 2 - 0.3, 0.82),
                "bronze_gilt")
    rng = random.Random(4)
    for k in range(11):
        y = -width / 2 + 0.6 + k * (width - 1.2) / 10
        h = rng.uniform(0.38, 0.48)
        tube(builder, [(length / 2 + 0.06, y, 0.34), (length / 2 + 0.07, y, 0.34 + h * 0.75)], [0.07, 0.05],
             (1.0, 1.0, 1.0), 5, "bronze_gilt")
        ellipsoid(builder, (length / 2 + 0.07, y, 0.34 + h * 0.85), (0.05, 0.05, 0.06), (1.0, 1.0, 1.0), 6, 4,
                  "bronze_gilt")
    return builder


def wing(builder, root, tip, width, colour, material):
    root = Vector(root)
    tip = Vector(tip)
    span = tip - root
    side = span.cross(Vector((0.0, 1.0, 0.0))).normalized()
    if side.length < 0.1:
        side = Vector((0.0, 0.0, 1.0))
    rows = []
    for t in (0.0, 0.35, 0.7, 1.0):
        centre = root + span * t
        w = width * (1.0 - 0.75 * t) * (1.0 if t < 0.8 else 0.7)
        rows.append([centre - side * w * 0.2, centre + Vector((0.0, -0.04, 0.0)), centre + side * w])
    first = len(builder.polygons)
    builder.surface(rows, material, smooth=True)
    builder.surface([list(reversed(row)) for row in rows], material, smooth=True)
    builder.tint(first, colour)


def nike(scale=1.0, material="bronze_gilt", colour=(1.0, 1.0, 1.0), dress=None):
    look = Look(dress or colour, hem=0.03, skin=0, hair=1, female=True, sleeves="short", arms="olym_raise",
                palla=dress or colour, material=material, seed=5, hem_radius=0.26)
    builder = person(look)
    for side in (-1, 1):
        wing(builder, (side * 0.1, -0.12, 1.38), (side * 0.75, -0.42, 1.95), 0.32, colour, material)
    if material == "bronze_gilt":
        builder.tint(0, colour)
    if scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(scale, 4))
        return scaled
    return builder


def cauldron(scale=1.0):
    builder = MeshBuilder()
    s = scale
    for k in range(3):
        angle = 2 * math.pi * k / 3
        foot = Vector((math.cos(angle) * 0.62 * s, math.sin(angle) * 0.62 * s, 0.0))
        top = Vector((math.cos(angle) * 0.5 * s, math.sin(angle) * 0.5 * s, 1.15 * s))
        tube(builder, [foot, top], [0.06 * s, 0.05 * s], (1.0, 1.0, 1.0), 6, "bronze_gilt")
    builder.lathe([(0.0, 0.85 * s), (0.36 * s, 0.9 * s), (0.6 * s, 1.15 * s), (0.66 * s, 1.45 * s),
                   (0.62 * s, 1.6 * s), (0.6 * s, 1.6 * s), (0.55 * s, 1.5 * s)], 18, "bronze_gilt", smooth=True)
    for k in range(4):
        angle = 2 * math.pi * k / 4 + 0.4
        centre = Vector((math.cos(angle) * 0.62 * s, math.sin(angle) * 0.62 * s, 1.62 * s))
        tube(builder, [centre, centre + Vector((math.cos(angle) * 0.18 * s, math.sin(angle) * 0.18 * s, 0.3 * s))],
             [0.08 * s, 0.03 * s], (1.0, 1.0, 1.0), 5, "bronze_gilt")
    return builder


def emperor(seed=0, cuirass=True):
    if cuirass:
        look = Look((0.86, 0.80, 0.62), hem=0.5, skin=0, hair=1, cloak=(0.62, 0.12, 0.12), belt=(0.8, 0.6, 0.2),
                    arms="olym_spear", material="marble", seed=seed)
    else:
        look = Look((0.95, 0.93, 0.88), hem=0.1, skin=0, hair=1, toga=(0.97, 0.95, 0.90), praetexta=(0.55, 0.1, 0.25),
                    arms="toga_gesture", material="marble", seed=seed)
    figure = person(look)
    builder = MeshBuilder()
    builder.box((-0.55, -0.55, 0.0), (0.55, 0.55, 1.3), "marble", bottom=False)
    builder.box((-0.62, -0.62, 1.2), (0.62, 0.62, 1.38), "marble")
    builder.merge(figure, Matrix.Translation((0.0, 0.0, 1.38)) @ Matrix.Scale(1.45, 4))
    if cuirass:
        tube(builder, [(0.44, 0.33, 1.38), (0.44, 0.33, 1.38 + 3.4)], [0.035, 0.03], (0.55, 0.42, 0.28), 5, "matte")
    return builder


def statue():
    b = MeshBuilder()
    gold = (1.0, 1.0, 1.0)
    ivory = IVORY
    seat = 4.3
    sw = 2.75
    sd = 2.0
    ebony = EBONY
    for x in (-sw, sw):
        for y in (-sd, sd - 0.2):
            painted(b, ebony, lambda x=x, y=y: b.box((x - 0.32, y - 0.32, 0.0), (x + 0.32, y + 0.32, seat), MATTE))
            painted(b, gold, lambda x=x, y=y: b.box((x - 0.36, y - 0.36, 0.0), (x + 0.36, y + 0.36, 0.35),
                                                    "bronze_gilt"))
            painted(b, gold, lambda x=x, y=y: b.box((x - 0.35, y - 0.35, seat - 0.4), (x + 0.35, y + 0.35, seat - 0.2),
                                                    "bronze_gilt"))
    for y in (-sd, sd - 0.2):
        painted(b, gold, lambda y=y: b.box((-sw, y - 0.12, 1.4), (sw, y + 0.12, 1.75), "bronze_gilt"))
    for x in (-sw, sw):
        painted(b, gold, lambda x=x: b.box((x - 0.12, -sd, 1.4), (x + 0.12, sd, 1.75), "bronze_gilt"))
    for k in range(4):
        x = -1.8 + k * 1.2
        nb = nike(0.62, "ivory", (1.0, 1.0, 1.0))
        b.merge(nb, Matrix.Translation((x, sd - 0.05, 1.75)))
    painted(b, ebony, lambda: b.box((-sw - 0.35, -sd - 0.35, seat - 0.2), (sw + 0.35, sd + 0.2, seat + 0.25), MATTE))
    painted(b, gold, lambda: b.box((-sw - 0.4, sd + 0.1, seat - 0.2), (sw + 0.4, sd + 0.3, seat + 0.3),
                                   "bronze_gilt"))
    painted(b, ebony, lambda: b.box((-sw - 0.35, -sd - 0.6, seat), (sw + 0.35, -sd - 0.15, 11.4), MATTE))
    painted(b, gold, lambda: b.box((-sw - 0.4, -sd - 0.12, seat + 0.4), (sw + 0.4, -sd - 0.1, 10.9), "bronze_gilt"))
    painted(b, ebony, lambda: b.box((-sw - 0.25, -sd - 0.11, seat + 0.6), (sw + 0.25, -sd - 0.08, 10.7), MATTE))
    for k in range(6):
        z = seat + 1.0 + k * 1.0
        painted(b, gold, lambda z=z: b.box((-sw - 0.3, -sd - 0.08, z), (sw + 0.3, -sd - 0.06, z + 0.08),
                                           "bronze_gilt"))
    for k, x in enumerate((-2.5, -1.85, -1.2, 1.2, 1.85, 2.5)):
        maiden = Look(gold, hem=0.03, skin=0, hair=2, female=True, palla=gold, arms="olym_raise" if k % 2 else "hip",
                      material="bronze_gilt", seed=60 + k, hem_radius=0.24)
        b.merge(person(maiden), Matrix.Translation((x, -sd - 0.35, 11.4)) @ Matrix.Scale(0.62, 4))
    for x in (-sw - 0.1, sw + 0.1):
        painted(b, ebony, lambda x=x: b.box((x - 0.28, -sd - 0.2, seat + 1.4), (x + 0.28, sd + 0.1, seat + 1.8),
                                            MATTE))
        painted(b, gold, lambda x=x: b.box((x - 0.3, -sd - 0.2, seat + 1.8), (x + 0.3, sd + 0.15, seat + 1.88),
                                           "bronze_gilt"))
        painted(b, ebony, lambda x=x: b.box((x - 0.15, sd - 0.1, seat), (x + 0.15, sd + 0.1, seat + 1.4), MATTE))
        sphinx_at = Vector((x, sd + 0.15, seat + 1.88))
        ellipsoid(b, sphinx_at + Vector((0.0, -0.2, 0.25)), (0.22, 0.45, 0.25), gold, 8, 5, "bronze_gilt")
        ellipsoid(b, sphinx_at + Vector((0.0, 0.25, 0.62)), (0.16, 0.16, 0.2), ivory, 8, 5, "ivory")
        wing(b, sphinx_at + Vector((0.0, -0.1, 0.4)), sphinx_at + Vector((0.0, -0.75, 1.05)), 0.3, gold, "bronze_gilt")
    stool_y = 3.3
    painted(b, gold, lambda: b.box((-2.2, stool_y - 0.8, 0.0), (2.2, stool_y + 0.8, 0.95), "bronze_gilt"))
    painted(b, ebony, lambda: b.box((-2.1, stool_y - 0.75, 0.15), (2.1, stool_y + 0.82, 0.8), MATTE))
    for x in (-1.5, 1.5):
        lion(b, Vector((x, stool_y + 1.05, 0.0)), gold)
    for side in (-1, 1):
        hip = Vector((side * 0.95, -0.8, seat + 0.75))
        knee = Vector((side * 1.15, 2.35, seat + 0.95))
        ankle = Vector((side * 1.05, stool_y - 0.05, 1.55))
        tube(b, [hip, hip.lerp(knee, 0.5) + Vector((0.0, 0.0, 0.1)), knee], [1.0, 0.95, 0.72], gold, 14,
             "bronze_gilt")
        tube(b, [knee, knee.lerp(ankle, 0.5), ankle + Vector((0.0, 0.0, 0.2))], [0.72, 0.6, 0.5], gold, 14,
             "bronze_gilt")
        tube(b, [ankle + Vector((0.0, 0.0, 0.35)), ankle + Vector((0.0, 0.0, -0.35))], [0.32, 0.3], ivory, 10, "ivory")
        ellipsoid(b, ankle + Vector((0.0, 0.42, -0.42)), (0.34, 0.68, 0.2), ivory, 10, 5, "ivory")
        ellipsoid(b, ankle + Vector((0.0, 0.42, -0.55)), (0.4, 0.74, 0.07), gold, 10, 3, "bronze_gilt")
    drape(b, gold, [(2.1, seat + 0.3), (2.15, seat + 1.1), (1.95, seat + 1.6), (1.7, seat + 1.9)], 22,
          start=math.radians(200), sweep=math.radians(140), folds=(7, 0.07, 0.4), squash=0.9, material="bronze_gilt",
          center=(0.0, -0.1))
    lap = [(Vector((-2.3, 0.2, seat + 1.85)), Vector((2.3, 0.2, seat + 1.85))),
           (Vector((-2.4, 2.5, seat + 1.6)), Vector((2.4, 2.5, seat + 1.6))),
           (Vector((-2.2, 2.9, seat + 0.6)), Vector((2.2, 2.9, seat + 0.6))),
           (Vector((-2.0, 3.0, 2.2)), Vector((2.0, 3.0, 2.2))),
           (Vector((-1.9, 3.05, 1.7)), Vector((1.9, 3.05, 1.7)))]
    rows = []
    for left, right in lap:
        row = []
        for k in range(13):
            t = k / 12
            point = left.lerp(right, t)
            point = point + Vector((0.0, 0.12 * math.sin(t * math.pi * 7), 0.0))
            row.append(point)
        rows.append(row)
    first = len(b.polygons)
    b.surface(rows, "bronze_gilt", smooth=True, facing=(0.0, 1.0, 0.2))
    b.tint(first, gold)
    torso = [(1.5, seat + 1.6), (1.52, seat + 1.95), (1.58, seat + 2.3), (1.66, seat + 2.6), (1.62, seat + 2.85),
             (1.6, seat + 3.05), (1.7, seat + 3.3), (1.82, seat + 3.6), (1.88, seat + 3.85), (1.86, seat + 4.05),
             (1.7, seat + 4.3), (1.35, seat + 4.55), (0.9, seat + 4.72), (0.5, seat + 4.82)]
    drape(b, ivory, torso, 28, folds=(0, 0.0, 0.0), squash=0.62, material="ivory", center=(0.0, -0.75))
    for side in (-1, 1):
        ellipsoid(b, (side * 0.7, -0.08, seat + 3.6), (0.78, 0.36, 0.42), ivory, 14, 8, "ivory")
        ellipsoid(b, (side * 1.55, -0.62, seat + 4.18), (0.62, 0.6, 0.5), ivory, 12, 7, "ivory")
    ellipsoid(b, (0.0, -0.12, seat + 2.5), (0.95, 0.34, 0.62), ivory, 12, 7, "ivory")
    drape(b, gold, [(0.7, seat + 4.62), (0.95, seat + 4.4), (1.25, seat + 4.0), (1.5, seat + 3.3)], 12,
          start=math.radians(150), sweep=math.radians(80), folds=(5, 0.08, 0.3), squash=0.7, material="bronze_gilt",
          center=(-1.1, -0.7))
    ellipsoid(b, (-1.6, -0.62, seat + 4.3), (0.7, 0.66, 0.5), gold, 12, 7, "bronze_gilt")
    drape(b, gold, [(1.8, seat + 1.5), (1.85, seat + 2.4), (1.95, seat + 3.4), (1.95, seat + 4.0), (1.7, seat + 4.45),
                    (1.0, seat + 4.75)], 18, start=math.radians(120), sweep=math.radians(150), folds=(8, 0.05, 1.0),
          squash=0.66, material="bronze_gilt", center=(0.0, -0.75),
          dip=lambda angle: -1.4 * max(0.0, math.cos(angle - math.radians(150))))
    tube(b, [(0.0, -0.7, seat + 4.75), (0.0, -0.62, seat + 5.25)], [0.52, 0.48], ivory, 12, "ivory")
    head = Vector((0.0, -0.5, seat + 5.55))
    ellipsoid(b, head, (0.62, 0.7, 0.82), ivory, 16, 10, "ivory")
    ellipsoid(b, head + Vector((0.0, 0.62, -0.08)), (0.1, 0.16, 0.22), ivory, 8, 5, "ivory")
    ellipsoid(b, head + Vector((0.0, 0.34, -0.62)), (0.52, 0.38, 0.64), gold, 14, 8, "bronze_gilt")
    ellipsoid(b, head + Vector((0.0, 0.5, -0.24)), (0.34, 0.14, 0.08), gold, 10, 4, "bronze_gilt")
    for k in range(12):
        angle = math.radians(-70 + k * 140 / 11)
        root = head + Vector((math.sin(angle) * 0.42, 0.3 + math.cos(angle) * 0.28, -0.42))
        tip = root + Vector((math.sin(angle) * 0.12, 0.12, -0.55 - 0.25 * math.cos(angle)))
        tube(b, [root, root.lerp(tip, 0.5) + Vector((0.0, 0.05, 0.0)), tip], [0.11, 0.09, 0.03], gold, 6,
             "bronze_gilt")
    ellipsoid(b, head + Vector((0.0, -0.24, 0.26)), (0.66, 0.62, 0.62), gold, 14, 8, "bronze_gilt")
    for side in (-1, 1):
        ellipsoid(b, head + Vector((side * 0.3, 0.48, 0.22)), (0.18, 0.08, 0.05), (0.85, 0.72, 0.5), 6, 3, "ivory")
    for k in range(18):
        angle = 2 * math.pi * k / 18
        leaf = head + Vector((math.cos(angle) * 0.72, math.sin(angle) * 0.78 - 0.04, 0.42 + 0.06 * math.sin(3 * angle)))
        ellipsoid(b, leaf, (0.13, 0.13, 0.07), (0.85, 0.9, 0.55), 6, 3, "bronze_gilt")
    for side in (-1, 1):
        for k in range(3):
            root = head + Vector((side * (0.36 + k * 0.1), -0.45 - k * 0.08, -0.05))
            tip = root + Vector((side * (0.3 + k * 0.06), -0.25, -1.25 + k * 0.15))
            tube(b, [root, root.lerp(tip, 0.5) + Vector((side * 0.06, 0.0, 0.0)), tip], [0.14, 0.12, 0.05], gold, 6,
                 "bronze_gilt")
    right_shoulder = Vector((1.75, -0.6, seat + 4.25))
    right_elbow = Vector((2.1, 0.7, seat + 2.15))
    right_hand = Vector((2.0, 2.8, seat + 2.4))
    tube(b, [right_shoulder, right_shoulder.lerp(right_elbow, 0.5), right_elbow], [0.62, 0.55, 0.45], ivory, 12,
         "ivory")
    tube(b, [right_elbow, right_elbow.lerp(right_hand, 0.5), right_hand], [0.45, 0.4, 0.32], ivory, 12, "ivory")
    ellipsoid(b, right_hand + Vector((0.0, 0.25, 0.05)), (0.35, 0.42, 0.18), ivory, 10, 5, "ivory")
    nb = nike(1.35, "bronze_gilt", gold)
    b.merge(nb, Matrix.Translation(right_hand + Vector((0.0, 0.25, 0.18))) @ Matrix.Rotation(math.radians(-10), 4, "Z"))
    left_shoulder = Vector((-1.75, -0.6, seat + 4.25))
    left_elbow = Vector((-2.55, 0.0, seat + 3.0))
    left_hand = Vector((-2.45, 0.55, seat + 4.7))
    tube(b, [left_shoulder, left_shoulder.lerp(left_elbow, 0.5), left_elbow], [0.62, 0.55, 0.45], gold, 12,
         "bronze_gilt")
    tube(b, [left_elbow, left_elbow.lerp(left_hand, 0.5), left_hand], [0.45, 0.4, 0.34], ivory, 12, "ivory")
    ellipsoid(b, left_hand, (0.32, 0.32, 0.38), ivory, 10, 5, "ivory")
    staff_bottom = Vector((-2.45, 0.8, 0.95))
    staff_top = Vector((-2.45, 0.45, 12.4))
    tube(b, [staff_bottom, staff_top], [0.1, 0.09], gold, 8, "bronze_gilt")
    for k in range(9):
        z = 1.5 + k * 1.2
        point = staff_bottom.lerp(staff_top, (z - staff_bottom.z) / (staff_top.z - staff_bottom.z))
        ellipsoid(b, point, (0.14, 0.14, 0.1), (0.4, 0.6, 0.9), 6, 3, "bronze_gilt")
    eagle = staff_top + Vector((0.0, 0.0, 0.35))
    ellipsoid(b, eagle, (0.22, 0.42, 0.3), gold, 8, 5, "bronze_gilt")
    ellipsoid(b, eagle + Vector((0.0, 0.38, 0.28)), (0.12, 0.14, 0.14), gold, 6, 4, "bronze_gilt")
    for side in (-1, 1):
        wing(b, eagle + Vector((side * 0.15, -0.05, 0.1)), eagle + Vector((side * 0.9, -0.3, 0.75)), 0.45, gold,
             "bronze_gilt")
    b.materials = ["gold_glow" if name == "bronze_gilt" else name for name in b.materials]
    return b


def lion(b, at, colour):
    ellipsoid(b, at + Vector((0.0, -0.25, 0.42)), (0.24, 0.5, 0.24), colour, 10, 6, "bronze_gilt")
    ellipsoid(b, at + Vector((0.0, 0.22, 0.62)), (0.3, 0.24, 0.3), colour, 10, 6, "bronze_gilt")
    ellipsoid(b, at + Vector((0.0, 0.42, 0.62)), (0.15, 0.16, 0.15), colour, 8, 5, "bronze_gilt")
    for dx in (-0.13, 0.13):
        for dy in (-0.6, 0.2):
            tube(b, [at + Vector((dx, dy, 0.42)), at + Vector((dx, dy + 0.05, 0.0))], [0.07, 0.06], colour, 5,
                 "bronze_gilt")
    tube(b, [at + Vector((0.0, -0.72, 0.5)), at + Vector((0.12, -0.95, 0.25)), at + Vector((0.2, -1.0, 0.05))],
         [0.04, 0.03, 0.05], colour, 4, "bronze_gilt")


def pediment_figure(kind, seed, height):
    rng = random.Random(seed)
    palette = [(0.82, 0.10, 0.06), (0.95, 0.70, 0.15), (0.20, 0.55, 0.22), (0.86, 0.36, 0.10), (0.98, 0.94, 0.82)]
    garment = palette[rng.randrange(len(palette))]
    if kind == "horse":
        from .olympie_life import horse
        figure = horse((0.96, 0.93, 0.86), material="marble")
        scale = height / 1.9
        built = MeshBuilder()
        built.merge(figure, Matrix.Scale(scale, 4))
        return built
    if kind == "centaur":
        from .olympie_life import horse
        figure = horse((0.88, 0.80, 0.66), material="marble")
        rider = person(Look(MARBLE_SKIN, hem=1.05, skin=0, hair=3, arms="olym_fight", material="marble", seed=seed))
        figure.merge(rider, Matrix.Translation((0.0, 0.55, 0.42)))
        built = MeshBuilder()
        built.merge(figure, Matrix.Scale(height / 2.3, 4))
        return built
    arms = {"stand": "olym_raise", "fight": "olym_fight", "bow": "olym_bow", "kneel": "forward", "recline": "gesture",
            "god": "olym_spear"}[kind]
    female = kind in ("kneel",) and rng.random() < 0.5
    look = Look(garment, hem=0.05 if kind in ("god", "stand") else 0.6, skin=0, hair=rng.randrange(4), arms=arms,
                palla=garment if kind == "god" else None, female=female, material="marble", seed=seed,
                stride=0.12 if kind == "fight" else 0.0)
    figure = person(look)
    built = MeshBuilder()
    if kind == "recline":
        built.merge(figure, Matrix.Scale(height / 0.62, 4) @ Matrix.Translation((0.0, 0.0, 0.18))
                    @ Matrix.Rotation(math.radians(80), 4, "Y"))
    elif kind == "kneel":
        built.merge(figure, Matrix.Translation((0.0, 0.0, -0.55 * height / 1.3)) @ Matrix.Scale(height / 1.3, 4))
    else:
        built.merge(figure, Matrix.Scale(height / 1.78, 4))
    return built


def pediment_group(east=True, half=13.6, apex=3.4):
    b = MeshBuilder()
    if east:
        plan = [(0.0, "god", 1.0), (2.0, "stand", 0.88), (-2.0, "stand", 0.88), (3.5, "stand", 0.8),
                (-3.5, "stand", 0.8), (5.4, "horse", 0.62), (-5.4, "horse", 0.62), (6.4, "horse", 0.56),
                (-6.4, "horse", 0.56), (8.3, "kneel", 0.5), (-8.3, "kneel", 0.5), (10.0, "kneel", 0.38),
                (-10.0, "kneel", 0.38), (11.8, "recline", 0.22), (-11.8, "recline", 0.22)]
    else:
        plan = [(0.0, "god", 1.0), (2.2, "fight", 0.86), (-2.2, "fight", 0.86), (3.6, "centaur", 0.74),
                (-3.6, "centaur", 0.74), (5.6, "fight", 0.66), (-5.6, "fight", 0.66), (7.2, "centaur", 0.54),
                (-7.2, "centaur", 0.54), (9.0, "kneel", 0.42), (-9.0, "kneel", 0.42), (10.6, "kneel", 0.32),
                (-10.6, "kneel", 0.32), (12.0, "recline", 0.2), (-12.0, "recline", 0.2)]
    for index, (y, kind, factor) in enumerate(plan):
        height = apex * factor * 0.95 * (1.0 - abs(y) / half * 0.15)
        figure = pediment_figure(kind, 30 + index + (0 if east else 50), height)
        turn = math.pi / 2 if kind in ("horse", "centaur") else 0.0
        if kind in ("horse", "centaur") and y < 0:
            turn = -math.pi / 2
        if kind == "recline":
            turn = math.pi if y > 0 else 0.0
        b.merge(figure, Matrix.Translation((y, 0.0, 0.0)) @ Matrix.Rotation(turn, 4, "Z"))
    return b
