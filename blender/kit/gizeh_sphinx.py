import math

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .nimes_figures import ellipsoid, tube

TAU = 2 * math.pi
RED = (0.60, 0.38, 0.28)
DARK_RED = (0.42, 0.24, 0.17)
STONE_FACE = (0.92, 0.80, 0.64)
NEMES_A = (1.0, 0.90, 0.66)
NEMES_B = (0.86, 0.82, 0.76)
BEARD = (0.84, 0.74, 0.60)
BODY = [(-37.2, 1.2, 4.0, 3.0), (-36.4, 4.6, 7.6, 5.0), (-34.5, 7.4, 10.4, 6.0), (-30.0, 8.9, 11.8, 6.4),
        (-24.0, 8.8, 12.1, 6.5), (-16.0, 8.4, 12.3, 6.6), (-8.0, 8.2, 12.6, 6.7), (0.0, 8.4, 13.2, 6.9),
        (5.0, 8.7, 13.8, 7.1), (9.0, 8.3, 13.4, 6.9), (11.8, 6.8, 11.6, 6.0), (13.2, 4.0, 8.0, 4.4),
        (13.8, 1.4, 4.0, 2.4)]
NEMES = [(11.2, 9.7, 2.0, 4.5, 0.75), (12.6, 9.45, 2.45, 4.95, 0.7), (13.8, 9.2, 2.85, 4.75, 0.62),
         (15.0, 9.0, 3.1, 3.95, 0.6), (16.2, 8.9, 3.2, 3.38, 0.6), (17.6, 8.9, 3.15, 3.15, 0.62),
         (18.6, 9.0, 2.95, 2.9, 0.85), (19.5, 9.1, 2.4, 2.35, 0.9), (20.1, 9.2, 1.4, 1.4, 0.9),
         (20.3, 9.2, 0.2, 0.2, 0.9)]


def signed_power(value, power):
    return math.copysign(abs(value) ** power, value)


def loft_x(builder, sections, material, segments=22, power=0.45, floor=-0.6, color=None, lower_material=None,
           lower_limit=0.0):
    rows = []
    for x, half_width, top, half_height in sections:
        centre = top - half_height
        ring = []
        for k in range(segments):
            angle = TAU * k / segments
            y = half_width * signed_power(math.cos(angle), power)
            z = centre + half_height * signed_power(math.sin(angle), power)
            ring.append(Vector((x, y, max(z, floor))))
        rows.append(ring)
    first = len(builder.polygons)
    builder.surface(rows, material, closed=True)
    if lower_material is not None:
        slot = builder.slot(lower_material)
        for index in range(first, len(builder.polygons)):
            zs = [builder.positions[i][2] for i in builder.polygons[index]]
            if max(zs) < lower_limit:
                builder.polygon_materials[index] = slot
    if color is not None:
        builder.tint(first, color)
    builder.polygon(list(reversed(rows[0])), material, color=color)
    builder.polygon(rows[-1], material, color=color)
    return rows


def loft_z(builder, sections, material, segments=24, power=0.7, stripes=None):
    rows = []
    for z, centre_x, half_x, half_y, front in sections:
        ring = []
        for k in range(segments):
            angle = TAU * k / segments
            c = signed_power(math.cos(angle), power)
            depth = half_x * (front if c > 0 else 1.0)
            ring.append(Vector((centre_x + depth * c, half_y * signed_power(math.sin(angle), power), z)))
        rows.append(ring)
    first = len(builder.polygons)
    builder.surface(rows, material, closed=True)
    if stripes is not None:
        for index in range(first, len(builder.polygons)):
            points = [Vector(builder.positions[i]) for i in builder.polygons[index]]
            middle = sum(points, Vector()) / len(points)
            band = int(middle.z * 2.2) % 2
            builder.polygon_colors[index] = stripes[band]
    return rows


def paw(builder, side):
    y = side * 6.1
    sections = [(9.5, 2.0, 4.2, 2.1), (12.0, 2.0, 3.2, 1.7), (18.0, 1.95, 2.9, 1.5), (26.0, 1.9, 2.75, 1.45),
                (31.5, 1.95, 2.6, 1.4), (33.8, 1.8, 2.3, 1.25), (35.2, 1.2, 1.7, 0.9), (35.8, 0.4, 1.0, 0.5)]
    local = MeshBuilder()
    loft_x(local, sections, "restoration", 16, 0.5, -0.6)
    for k in range(4):
        offset = -1.35 + k * 0.9
        ellipsoid(local, (35.0, offset, 0.55), (0.9, 0.42, 0.55), (0.92, 0.84, 0.70), 8, 4, "restoration")
    builder.merge(local, Matrix.Translation((0.0, y, 0.0)))
    tube(builder, [Vector((6.5, y * 0.98, 10.5)), Vector((9.0, y, 7.0)), Vector((11.0, y, 4.0))], [2.4, 2.2, 2.0],
         (1.0, 1.0, 1.0), 12, "sphinx_rock")


def hind_leg(builder, side):
    y = side * 7.8
    ellipsoid(builder, (-27.0, y, 5.4), (6.6, 2.0, 5.2), (1.0, 0.97, 0.92), 14, 8, "sphinx_rock")
    local = MeshBuilder()
    loft_x(local, [(-24.0, 0.9, 2.2, 1.1), (-20.0, 1.0, 2.0, 1.0), (-15.0, 1.0, 1.8, 0.9), (-13.0, 0.5, 1.3, 0.6)],
           "restoration", 12, 0.5, -0.4)
    builder.merge(local, Matrix.Translation((0.0, side * 9.4, 0.0)))


def head(builder):
    loft_z(builder, NEMES, "casing", 32, 0.6, stripes=[NEMES_A, NEMES_B])
    tube(builder, [Vector((7.2, 0.0, 11.0)), Vector((8.4, 0.0, 13.2)), Vector((8.8, 0.0, 15.0))], [3.4, 3.2, 3.0],
         (1.0, 0.95, 0.86), 16, "casing")
    for side in (-1, 1):
        lappet = [(10.0, side * 2.2), (10.9, side * 2.3), (11.3, side * 3.3), (10.3, side * 3.9)]
        if side < 0:
            lappet = list(reversed(lappet))
        first = len(builder.polygons)
        builder.prism(lappet, 11.2, 15.0, "casing")
        for index in range(first, len(builder.polygons)):
            builder.polygon_colors[index] = NEMES_A if index % 2 else NEMES_B
    face(builder)
    tube(builder, [Vector((11.45, 0.0, 18.55)), Vector((11.72, 0.0, 19.1)), Vector((11.55, 0.0, 19.55))],
         [0.2, 0.17, 0.1], (0.92, 0.66, 0.34), 8, "casing")
    ellipsoid(builder, (11.6, 0.0, 18.85), (0.12, 0.36, 0.42), (0.92, 0.66, 0.34), 8, 4, "casing")
    tube(builder, [Vector((11.55, 0.0, 13.95)), Vector((11.85, 0.0, 12.8)), Vector((11.95, 0.0, 11.5))],
         [0.7, 0.78, 0.62], BEARD, 10, "casing")
    builder.box((11.1, -0.4, 10.6), (12.1, 0.4, 11.6), "casing")


def wash(colour, amount=0.55):
    return tuple(a * (1 - amount) + b * amount for a, b in zip(STONE_FACE, colour))


def face(builder):
    skin = wash(RED)
    deep = wash(DARK_RED, 0.7)
    shadow = tuple(c * 0.62 for c in skin)
    ellipsoid(builder, (10.7, 0.0, 16.2), (1.42, 1.85, 2.45), skin, 24, 14)
    ellipsoid(builder, (11.55, 0.0, 17.42), (0.42, 1.55, 0.26), skin, 14, 6)
    ellipsoid(builder, (11.35, 0.0, 18.2), (0.5, 1.6, 0.55), skin, 14, 6)
    for side in (-1, 1):
        ellipsoid(builder, (11.78, side * 0.78, 16.98), (0.24, 0.5, 0.3), shadow, 12, 6)
        ellipsoid(builder, (11.9, side * 0.78, 16.96), (0.13, 0.36, 0.15), tuple(c * 0.92 for c in skin), 12, 6)
        ellipsoid(builder, (11.97, side * 0.78, 17.1), (0.1, 0.4, 0.07), skin, 10, 4)
        ellipsoid(builder, (11.45, side * 1.08, 15.95), (0.62, 0.62, 0.8), skin, 12, 7)
        ellipsoid(builder, (11.2, side * 1.5, 16.6), (0.5, 0.4, 0.9), skin, 10, 6)
        ellipsoid(builder, (10.3, side * 2.06, 16.5), (0.34, 0.24, 0.82), skin, 10, 6)
        ellipsoid(builder, (10.42, side * 2.2, 16.5), (0.16, 0.08, 0.5), deep, 8, 4)
    tube(builder, [Vector((11.95, 0.0, 17.25)), Vector((12.35, 0.0, 16.6)), Vector((12.62, 0.0, 16.0))],
         [0.2, 0.26, 0.3], skin, 10)
    ellipsoid(builder, (12.4, 0.0, 15.92), (0.28, 0.46, 0.2), skin, 10, 5)
    for side in (-1, 1):
        ellipsoid(builder, (12.48, side * 0.2, 15.86), (0.08, 0.1, 0.06), shadow, 6, 3)
    ellipsoid(builder, (12.0, 0.0, 15.5), (0.22, 0.78, 0.15), skin, 12, 5)
    ellipsoid(builder, (12.12, 0.0, 15.34), (0.1, 0.74, 0.04), tuple(c * 0.45 for c in deep), 12, 3)
    ellipsoid(builder, (11.96, 0.0, 15.17), (0.2, 0.64, 0.14), skin, 12, 5)
    ellipsoid(builder, (11.55, 0.0, 14.62), (0.62, 0.92, 0.55), skin, 12, 6)


def sphinx():
    builder = MeshBuilder()
    loft_x(builder, BODY, "sphinx_rock", 26, 0.38, -0.6, None, "restoration", 3.2)
    for side in (-1, 1):
        paw(builder, side)
        hind_leg(builder, side)
    tail = [Vector((-37.0, -3.0, 1.2)), Vector((-35.0, -8.5, 0.9)), Vector((-28.0, -10.2, 0.8)),
            Vector((-20.0, -10.0, 0.75)), Vector((-15.0, -9.4, 1.2))]
    tube(builder, tail, [0.6, 0.6, 0.55, 0.5, 0.7], (1.0, 1.0, 1.0), 8, "restoration")
    head(builder)
    return builder
