import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement

EARTH = (0.50, 0.36, 0.25)
DITCH = (0.30, 0.22, 0.16)
STAKES = (0.36, 0.27, 0.18)
LEATHER_TENT = (0.62, 0.50, 0.36)
HIDE_TENT = (0.50, 0.40, 0.30)
LINEN_TENT = (0.80, 0.74, 0.62)
STONE = (0.70, 0.64, 0.54)
TILE = (0.66, 0.38, 0.26)


def tinted_box(builder, minimum, maximum, color, matrix=None):
    first = len(builder.polygons)
    builder.box(minimum, maximum, MATTE, matrix=matrix, bottom=False)
    builder.tint(first, color)


def rampart(builder, centre, size, angle, height_at, segment=40.0, gate=24.0):
    cx, cy = centre
    half_x, half_y = size[0] / 2, size[1] / 2
    rotation = Matrix.Rotation(angle, 4, "Z")
    corners = [Vector((-half_x, -half_y, 0)), Vector((half_x, -half_y, 0)), Vector((half_x, half_y, 0)),
               Vector((-half_x, half_y, 0))]
    for start, end in zip(corners, corners[1:] + corners[:1]):
        length = (end - start).length
        direction = (end - start).normalized()
        heading = math.atan2(direction.y, direction.x)
        pieces = max(1, int(length / segment))
        for piece in range(pieces):
            a = piece * length / pieces
            b = (piece + 1) * length / pieces
            middle = (a + b) / 2
            if abs(middle - length / 2) < gate:
                continue
            local = start + direction * middle
            world = rotation @ local
            x, y = cx + world.x, cy + world.y
            z = height_at(x, y)
            frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle + heading, 4, "Z")
            half = (b - a) / 2 + 0.6
            tinted_box(builder, (-half, -2.2, -1.5), (half, 2.2, 1.4), EARTH, frame)
            tinted_box(builder, (-half, -0.25, 1.4), (half, 0.25, 3.0), STAKES, frame)
            tinted_box(builder, (-half, -6.5, -1.0), (half, -2.6, 0.08), DITCH, frame)


def tent():
    builder = MeshBuilder()
    a, b, c, d, e, f = builder.points([(-1.5, -1.6, 0.0), (1.5, -1.6, 0.0), (0.0, -1.6, 2.0),
                                       (-1.5, 1.6, 0.0), (1.5, 1.6, 0.0), (0.0, 1.6, 2.0)])
    for face in ((a, c, b), (d, e, f), (a, d, f, c), (b, c, f, e)):
        builder.face(list(face), MATTE)
    return builder


def tent_rows(centre, size, angle, spacing, margin, height_at, seed, jitter=0.0, fill=1.0):
    generator = random.Random(seed)
    cx, cy = centre
    rotation = Matrix.Rotation(angle, 4, "Z")
    matrices = []
    half_x = size[0] / 2 - margin
    half_y = size[1] / 2 - margin
    x = -half_x
    while x <= half_x:
        y = -half_y
        while y <= half_y:
            on_street = abs(x) < spacing[0] * 1.2 or abs(y) < spacing[1] * 1.2
            if not on_street and generator.random() < fill:
                local = rotation @ Vector((x + generator.uniform(-jitter, jitter), y + generator.uniform(-jitter, jitter), 0))
                wx, wy = cx + local.x, cy + local.y
                turn = angle + (generator.uniform(-0.6, 0.6) if jitter else 0.0)
                matrices.append(placement(wx, wy, height_at(wx, wy) - 0.1, turn))
            y += spacing[1]
        x += spacing[0]
    return matrices


def granary(builder, x, y, z, angle, length, width):
    frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, "Z")
    tinted_box(builder, (-length / 2, -width / 2, -1.0), (length / 2, width / 2, 4.0), STONE, frame)
    first = len(builder.polygons)
    ridge = builder.points([frame @ Vector(p) for p in ((-length / 2 - 0.5, -width / 2 - 0.6, 4.0),
                                                        (length / 2 + 0.5, -width / 2 - 0.6, 4.0),
                                                        (length / 2 + 0.5, 0.0, 6.0), (-length / 2 - 0.5, 0.0, 6.0),
                                                        (-length / 2 - 0.5, width / 2 + 0.6, 4.0),
                                                        (length / 2 + 0.5, width / 2 + 0.6, 4.0))])
    builder.face([ridge[0], ridge[1], ridge[2], ridge[3]], MATTE)
    builder.face([ridge[3], ridge[2], ridge[5], ridge[4]], MATTE)
    builder.tint(first, TILE)


def citadel(centre, height_at, seed=11):
    generator = random.Random(seed)
    builder = MeshBuilder()
    cx, cy = centre
    for index in range(26):
        angle = math.tau * index / 26
        if generator.random() < 0.3:
            continue
        x, y = cx + 115 * math.cos(angle), cy + 85 * math.sin(angle)
        z = height_at(x, y)
        frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle + math.pi / 2, 4, "Z")
        tinted_box(builder, (-11.0, -1.2, -1.5), (11.0, 1.2, generator.uniform(0.6, 2.2)), STONE, frame)
    for index, (dx, dy) in enumerate(((-30, 10), (-5, 25), (22, 5))):
        granary(builder, cx + dx, cy + dy, height_at(cx + dx, cy + dy), 0.4, 26.0, 9.0)
    for index in range(40):
        x = cx + generator.uniform(-260, 260)
        y = cy + generator.uniform(-200, 200)
        if math.hypot((x - cx) / 120, (y - cy) / 90) < 1.0:
            continue
        frame = Matrix.Translation((x, y, height_at(x, y))) @ Matrix.Rotation(generator.uniform(0, math.pi), 4, "Z")
        size = generator.uniform(4, 8)
        tinted_box(builder, (-size, -size * 0.7, -1.0), (size, size * 0.7, generator.uniform(0.3, 1.0)),
                   (0.62, 0.55, 0.46), frame)
    return builder


CAMPS = {
    "camp_romain_grand": dict(centre=(-2700.0, 1000.0), size=(720.0, 640.0), angle=0.35, colour=LEATHER_TENT,
                              spacing=(16.0, 12.0), jitter=0.0, fill=0.92),
    "camp_romain_petit": dict(centre=(250.0, 1050.0), size=(460.0, 420.0), angle=0.1, colour=LEATHER_TENT,
                              spacing=(16.0, 12.0), jitter=0.0, fill=0.9),
    "camp_hannibal": dict(centre=(-4300.0, -700.0), size=(620.0, 520.0), angle=0.7, colour=HIDE_TENT,
                          spacing=(18.0, 15.0), jitter=4.0, fill=0.7),
}
