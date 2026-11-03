import math

from mathutils import Matrix

from .cannes_camps import STONE, TILE, tinted_box
from .geometry import MATTE, MeshBuilder

LIMESTONE = (0.78, 0.74, 0.66)
TIMBER = (0.52, 0.40, 0.27)

CAMPS = {
    "camp_octavien": dict(anchor=(-1933.0, 8626.0), size=(520.0, 420.0), angle=0.25, spacing=(16.0, 12.0), fill=0.85),
    "camp_antoine": dict(anchor=(900.0, -1300.0), size=(700.0, 520.0), angle=-0.3, spacing=(16.0, 12.0), fill=0.8),
}
STRAIT_TOWERS = [(-160.0, 120.0), (560.0, 620.0)]
APOLLO = (-711.0, -2931.0)


def temple(x, y, z, angle):
    builder = MeshBuilder()
    frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, "Z")
    tinted_box(builder, (-8.0, -14.0, -2.0), (8.0, 14.0, 1.2), LIMESTONE, frame)
    tinted_box(builder, (-4.8, -8.5, 1.2), (4.8, 10.5, 8.0), LIMESTONE, frame)
    for k in range(6):
        for side in (-1, 1):
            cx = side * 6.6
            cy = -12.0 + k * 4.8
            tinted_box(builder, (cx - 0.5, cy - 0.5, 1.2), (cx + 0.5, cy + 0.5, 8.0), LIMESTONE, frame)
    for k in range(1, 5):
        for side in (-1, 1):
            cx = -6.6 + k * 2.64
            cy = side * 12.0
            tinted_box(builder, (cx - 0.5, cy - 0.5, 1.2), (cx + 0.5, cy + 0.5, 8.0), LIMESTONE, frame)
    tinted_box(builder, (-7.2, -12.6, 8.0), (7.2, 12.6, 9.2), LIMESTONE, frame)
    first = len(builder.polygons)
    builder.prism([(-7.4, 9.4), (7.4, 9.4), (0.0, 12.0)], -12.9, 12.9,
                  MATTE, matrix=frame @ Matrix.Rotation(math.pi / 2, 4, "X"))
    builder.tint(first, TILE)
    return builder


def tower(x, y, z):
    builder = MeshBuilder()
    frame = Matrix.Translation((x, y, z))
    tinted_box(builder, (-4.5, -4.5, -3.0), (4.5, 4.5, 13.0), STONE, frame)
    tinted_box(builder, (-5.2, -5.2, 13.0), (5.2, 5.2, 14.2), TIMBER, frame)
    for k in range(4):
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            offset = -3.6 + k * 2.4
            cx = sx * 4.6 if sx else offset
            cy = sy * 4.6 if sy else offset
            tinted_box(builder, (cx - 0.5, cy - 0.5, 14.2), (cx + 0.5, cy + 0.5, 15.4), TIMBER, frame)
    return builder

