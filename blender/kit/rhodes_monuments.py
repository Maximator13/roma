import math
import random

from mathutils import Matrix, Vector

from . import rhodes_plan as plan
from .geometry import MATTE, MeshBuilder
from .nimes_figures import tube
from .olympie_doric import Peripteral, cella_box, doric_column, painted
from .olympie_monuments import stoa

STONE = "limestone"
MARBLE = "marble"
PAVING = "paving"
PLASTER = "plaster"
VOID = "shadow_void"
TAU = 2 * math.pi
SEAT = (0.92, 0.88, 0.80)
WARM = (1.0, 0.95, 0.86)
OCHRE = (1.0, 0.82, 0.56)
RED = (0.72, 0.18, 0.12)

COLUMN_BUILDS = {
    "pythion": lambda: doric_column(1.0, 7.0, "plaster", 20, "high"),
    "athena": lambda: doric_column(1.15, 7.8, "plaster", 20, "medium"),
    "stoa_doric": lambda: doric_column(0.78, 5.3, "plaster", 12, "medium"),
    "stoa_inner": lambda: doric_column(0.62, 6.4, "plaster", 0, "low"),
    "stoa_plain": lambda: doric_column(0.7, 5.0, "plaster", 0, "low"),
}


def temple(length, width, front, flank, diameter, height, key, cella_colour=OCHRE, pediment=(0.16, 0.34, 0.72)):
    built = Peripteral(length, width, front, flank, diameter, height, diameter * 0.78, diameter * 0.8,
                       diameter * 0.34, 3, 0.36, width * 0.15, material="plaster", roof="terracotta_tiles",
                       tile_pitch=0.6, stone="limestone")
    builder = MeshBuilder()
    built.krepis(builder, 2.4)
    eave_x, eave_y = built.entablature(builder)
    apex = built.pediments(builder, eave_x, eave_y, pediment)
    built.roof_cover(builder, eave_x, eave_y)
    naos_x = built.half_x - 2.2 * diameter
    naos_y = built.half_y - 1.6 * diameter
    cella_box(builder, -naos_x, naos_x, naos_y, 0.8, height + 0.4, "plaster", cella_colour, door={1: (2.4, 4.6)},
              base_colour=RED)
    inner_x = built.half_x - 0.4
    inner_y = built.half_y - 0.4
    z0 = built.frieze_top - 0.3
    for x0, x1, y0, y1 in ((naos_x, inner_x, -inner_y, inner_y), (-inner_x, -naos_x, -inner_y, inner_y),
                           (-naos_x, naos_x, naos_y, inner_y), (-naos_x, naos_x, -inner_y, -naos_y)):
        painted(builder, (0.16, 0.24, 0.46), lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box(
            (x0, y0, z0), (x1, y1, built.frieze_top), MATTE))
    columns = [(key, x, y) for x, y in built.column_positions()]
    for y in (-2.2, 2.2):
        columns.append((key, naos_x + 1.4 * diameter, y))
    return builder, columns, built, apex


def pythion():
    length, width = plan.TEMPLE_SIZE
    return temple(length, width, 6, 12, 1.0, 7.0, "pythion")


def athena():
    return temple(37.0, 18.6, 6, 13, 1.15, 7.8, "athena", (0.98, 0.9, 0.74), (0.66, 0.14, 0.10))


def altar(length=9.0, width=4.2, height=1.8):
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-length / 2 - 1.2, -width / 2 - 1.2, -1.0),
                                               (length / 2 + 1.2, width / 2 + 1.2, 0.3), STONE, bottom=False))
    painted(builder, (1.0, 0.98, 0.94), lambda: builder.box((-length / 2, -width / 2, 0.3), (length / 2, width / 2,
                                                                                            height), MARBLE))
    painted(builder, (0.98, 0.94, 0.88), lambda: builder.box((-length / 2 - 0.2, -width / 2 - 0.2, height),
                                                             (length / 2 + 0.2, width / 2 + 0.2, height + 0.25),
                                                             MARBLE))
    for side in (-1, 1):
        painted(builder, (1.0, 0.97, 0.92), lambda side=side: builder.box(
            (side * length / 2 - 0.5, -width / 2 - 0.2, height + 0.25), (side * length / 2 + 0.5, width / 2 + 0.2,
                                                                       height + 0.75), MARBLE))
    for k in range(3):
        painted(builder, (0.12, 0.10, 0.09), lambda k=k: builder.box((-1.6 + k * 1.1, -0.5, height + 0.25),
                                                                     (-1.0 + k * 1.1, 0.5, height + 0.42), MATTE))
    return builder


def terrace(half_x, half_y, depth=10.0, parapet=1.0, thickness=1.8, gaps=()):
    builder = MeshBuilder()
    first = len(builder.polygons)
    for x0, y0, x1, y1, side in ((-half_x, -half_y - thickness, half_x, -half_y, "south"),
                                 (-half_x, half_y, half_x, half_y + thickness, "north"),
                                 (-half_x - thickness, -half_y - thickness, -half_x, half_y + thickness, "west"),
                                 (half_x, -half_y - thickness, half_x + thickness, half_y + thickness, "east")):
        spans = [(x0, y0, x1, y1)]
        for gap_side, centre, half in gaps:
            if gap_side != side:
                continue
            if side in ("east", "west"):
                spans = [(x0, y0, x1, centre - half), (x0, centre + half, x1, y1)]
            else:
                spans = [(x0, y0, centre - half, y1), (centre + half, y0, x1, y1)]
        for a, b, c, d in spans:
            builder.box((a, b, -depth), (c, d, parapet), STONE, bottom=False)
    builder.tint(first, (0.96, 0.92, 0.84))
    painted(builder, (1.0, 0.86, 0.66), lambda: builder.box((-half_x, -half_y, -0.4), (half_x, half_y, 0.06), PAVING,
                                                           bottom=False))
    return builder


def stair(width, drop, run, steps=None, tint=(0.95, 0.91, 0.83)):
    builder = MeshBuilder()
    steps = steps or max(int(drop / 0.3), 1)
    first = len(builder.polygons)
    for k in range(steps):
        top = -drop * k / steps
        builder.box((-width / 2, k * run / steps, -drop - 3.0), (width / 2, (k + 1) * run / steps, top), STONE,
                    bottom=False)
    for side in (-1, 1):
        x = side * (width / 2 + 0.6)
        builder.box((x - 0.6, 0.0, -drop - 3.0), (x + 0.6, run, 0.9), STONE, bottom=False)
    builder.tint(first, tint)
    return builder


def propylon(width=14.0, depth=8.0, height=7.0):
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-width / 2, -depth / 2, -0.4), (width / 2, depth / 2, 0.4), STONE,
                                               bottom=False))
    for side in (-1, 1):
        painted(builder, OCHRE, lambda side=side: builder.box((side * width / 2 - side * 1.6, -depth / 2 + 0.5, 0.4),
                                                              (side * width / 2, depth / 2 - 0.5, height), PLASTER))
    painted(builder, (1.0, 0.97, 0.92), lambda: builder.box((-width / 2 - 0.3, -depth / 2, height),
                                                            (width / 2 + 0.3, depth / 2, height + 1.3), PLASTER))
    painted(builder, (0.16, 0.30, 0.66), lambda: builder.box((-width / 2 - 0.32, -depth / 2 - 0.02, height + 0.5),
                                                             (width / 2 + 0.32, depth / 2 + 0.02, height + 0.85),
                                                             MATTE, bottom=False, top=False))
    for y in (-depth / 2, depth / 2):
        sign = 1 if y > 0 else -1
        builder.oriented([(-width / 2 - 0.6, y + sign * 0.6, height + 1.3), (width / 2 + 0.6, y + sign * 0.6,
                                                                              height + 1.3),
                          (width / 2 + 0.6, 0.0, height + 3.2), (-width / 2 - 0.6, 0.0, height + 3.2)], (0, sign, 1),
                         "terracotta_tiles")
    for side in (-1, 1):
        builder.oriented([(side * (width / 2 + 0.3), -depth / 2, height + 1.3), (side * (width / 2 + 0.3), depth / 2,
                                                                                 height + 1.3),
                          (side * (width / 2 + 0.3), 0.0, height + 3.1)], (side, 0, 0), PLASTER)
    columns = [("stoa_doric", x, y) for x in (-3.4, -1.1, 1.1, 3.4) for y in (-depth / 2 + 0.6, depth / 2 - 0.6)]
    return builder, columns


def stadium():
    builder = MeshBuilder()
    y0, y1 = plan.STADIUM_Y
    length = y1 - y0
    depth, rise = plan.STADIUM_ROW
    half = plan.STADIUM_HALF
    painted(builder, (0.95, 0.80, 0.58), lambda: builder.box((-half, -length - 4.0, -0.6), (half, 0.0, 0.05), MATTE,
                                                             bottom=False))
    builder.lathe([(0.0, 0.05), (half, 0.05), (half, -0.6)], 24, MATTE, smooth=False, start=0.0, sweep=math.pi,
                  caps=False)
    builder.tint(len(builder.polygons) - 48, (0.95, 0.80, 0.58))
    for k in range(plan.STADIUM_ROWS):
        r0 = half + k * depth + 0.05
        r1 = r0 + depth
        top = (k + 1) * rise
        tone = SEAT if k else (1.0, 0.98, 0.94)
        material = MARBLE if k == 0 else STONE
        for side in (-1, 1):
            a, b = sorted((side * r0, side * r1))
            painted(builder, tone, lambda a=a, b=b, top=top, material=material: builder.box(
                (a, -length, top - rise - 1.4), (b, 0.0, top), material, bottom=False))
        first = len(builder.polygons)
        builder.lathe([(r0, top - rise - 1.4), (r0, top), (r1, top), (r1, top - rise - 1.4)], 28, material,
                      smooth=False, start=0.0, sweep=math.pi, caps=False)
        builder.tint(first, tone)
    outer = half + plan.STADIUM_ROWS * depth
    top = plan.STADIUM_ROWS * rise
    for side in (-1, 1):
        a, b = sorted((side * outer, side * (outer + 1.2)))
        painted(builder, (0.90, 0.86, 0.78), lambda a=a, b=b: builder.box((a, -length, -6.0), (b, 0.0, top + 0.9),
                                                                         STONE, bottom=False))
    first = len(builder.polygons)
    builder.lathe([(outer, -6.0), (outer, top + 0.9), (outer + 1.2, top + 0.9), (outer + 1.2, -6.0)], 28, STONE,
                  smooth=False, start=0.0, sweep=math.pi, caps=False)
    builder.tint(first, (0.90, 0.86, 0.78))
    for k in range(0, plan.STADIUM_ROWS, 5):
        for y in range(int(-length) + 20, -10, 40):
            for side in (-1, 1):
                x = side * (half + (k + 0.5) * depth)
                painted(builder, (0.70, 0.66, 0.58), lambda x=x, y=y, k=k: builder.box(
                    (x - depth * 0.6, y - 0.6, (k + 1) * rise), (x + depth * 0.6, y + 0.6, (k + 1) * rise + 0.03),
                    MATTE, bottom=False))
    for y in (-length + 6.0, -12.0):
        painted(builder, (1.0, 0.98, 0.95), lambda y=y: builder.box((-half + 0.5, y - 0.25, -0.2),
                                                                    (half - 0.5, y + 0.25, 0.12), MARBLE))
        for x in (-half + 3.0, 0.0, half - 3.0):
            painted(builder, (1.0, 0.98, 0.95), lambda x=x, y=y: builder.box((x - 0.2, y - 0.2, 0.1),
                                                                             (x + 0.2, y + 0.2, 1.3), MARBLE))
    return builder


def odeon():
    builder = MeshBuilder()
    rows = int((plan.ODEON["radius"] - plan.ODEON["orchestra"]) / 0.82)
    painted(builder, (1.0, 0.95, 0.86), lambda: builder.lathe([(0.0, 0.08), (plan.ODEON["orchestra"], 0.08),
                                                               (plan.ODEON["orchestra"], -0.6)], 28, MARBLE,
                                                              smooth=False))
    for k in range(rows):
        r0 = plan.ODEON["orchestra"] + 0.3 + k * 0.82
        r1 = r0 + 0.82
        top = (k + 1) * 0.47
        first = len(builder.polygons)
        builder.lathe([(r0, top - 1.8), (r0, top), (r1, top), (r1, top - 1.8)], 30, STONE if k else MARBLE,
                      smooth=False, start=math.pi / 2 - 0.12, sweep=math.pi + 0.24, caps=False)
        builder.tint(first, SEAT if k else (1.0, 0.98, 0.94))
    outer = plan.ODEON["orchestra"] + 0.3 + rows * 0.82
    first = len(builder.polygons)
    builder.lathe([(outer, -2.0), (outer, rows * 0.47 + 2.4), (outer + 1.0, rows * 0.47 + 2.4), (outer + 1.0, -2.0)],
                  30, PLASTER, smooth=False, start=math.pi / 2 - 0.12, sweep=math.pi + 0.24, caps=False)
    builder.tint(first, OCHRE)
    skene_x = plan.ODEON["orchestra"] + 2.0
    painted(builder, OCHRE, lambda: builder.box((skene_x, -8.0, -1.0), (skene_x + 3.5, 8.0, 5.5), PLASTER))
    painted(builder, (1.0, 0.96, 0.9), lambda: builder.box((skene_x - 2.0, -7.0, -1.0), (skene_x, 7.0, 1.2), MARBLE))
    for y in (-4.0, 0.0, 4.0):
        builder.oriented([(skene_x - 0.02, y - 0.8, 1.2), (skene_x - 0.02, y + 0.8, 1.2), (skene_x - 0.02, y + 0.8, 3.6),
                          (skene_x - 0.02, y - 0.8, 3.6)], (-1, 0, 0), VOID)
    for y in (-6.0, -2.0, 2.0, 6.0):
        tube(builder, [(skene_x - 1.7, y, 1.2), (skene_x - 1.7, y, 4.2)], [0.22, 0.19], (1.0, 0.98, 0.94), 8, MARBLE)
    painted(builder, (0.98, 0.94, 0.88), lambda: builder.box((skene_x - 2.1, -7.0, 4.2), (skene_x, 7.0, 4.7),
                                                             MARBLE))
    return builder


def stoa_building(length, depth=10.0, height=5.3, spacing=3.0, colour=OCHRE):
    builder, columns = stoa(length, depth, height, spacing, inner=True, wall_colour=colour)
    return builder, [(key, x, y) for key, x, y, z in columns]


def honorific_bases(seed=0, count=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        x = (k - (count - 1) / 2) * 2.6
        height = rng.uniform(1.2, 1.8)
        painted(builder, (0.98, 0.95, 0.9), lambda x=x, height=height: builder.box(
            (x - 0.7, -0.6, -0.6), (x + 0.7, 0.6, height), MARBLE))
        first = len(builder.polygons)
        for line in range(4):
            z = height - 0.35 - line * 0.17
            half = 0.5 - (line % 2) * 0.12
            builder.oriented([(x - half, -0.61, z), (x + half, -0.61, z), (x + half, -0.61, z + 0.06),
                              (x - half, -0.61, z + 0.06)], (0, -1, 0), MATTE)
        builder.tint(first, (0.32, 0.27, 0.24))
    return builder


def harbour_tower(size=8.0, height=11.0, pitch=0.35):
    builder = MeshBuilder()
    h = size / 2
    painted(builder, (0.90, 0.84, 0.72), lambda: builder.box((-h - 0.5, -h - 0.5, -4.0), (h + 0.5, h + 0.5, 1.2),
                                                             STONE, bottom=False))
    painted(builder, WARM, lambda: builder.box((-h, -h, 1.2), (h, h, height - 3.2), STONE, bottom=False, top=False))
    painted(builder, (1.0, 0.97, 0.9), lambda: builder.box((-h - 0.25, -h - 0.25, height - 3.2),
                                                           (h + 0.25, h + 0.25, height - 2.9), STONE, bottom=False))
    painted(builder, OCHRE, lambda: builder.box((-h, -h, height - 2.9), (h, h, height), PLASTER, bottom=False,
                                                top=False))
    painted(builder, (1.0, 0.96, 0.9), lambda: builder.box((-h - 0.4, -h - 0.4, height), (h + 0.4, h + 0.4,
                                                                                         height + 0.35), STONE))
    for k in range(4):
        angle = TAU * k / 4
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        for j in (-1, 1):
            centre = normal * (h + 0.02) + side * (j * 1.6)
            window = [centre - side * 0.45 + Vector((0, 0, height - 2.4)), centre + side * 0.45 + Vector((0, 0, height - 2.4)),
                      centre + side * 0.45 + Vector((0, 0, height - 0.8)), centre - side * 0.45 + Vector((0, 0, height - 0.8))]
            builder.oriented(window, normal, VOID)
            for flap in (-1, 1):
                hinge = centre + side * (flap * 0.45) + normal * 0.03
                leaf = [hinge + Vector((0, 0, height - 2.4)), hinge + side * (flap * 0.42) + Vector((0, 0, height - 2.4)),
                        hinge + side * (flap * 0.42) + Vector((0, 0, height - 0.8)), hinge + Vector((0, 0, height - 0.8))]
                first = len(builder.polygons)
                builder.oriented(leaf, normal, PLASTER)
                builder.tint(first, (0.46, 0.28, 0.16))
        slit = normal * (h + 0.02)
        builder.oriented([slit - side * 0.15 + Vector((0, 0, 3.5)), slit + side * 0.15 + Vector((0, 0, 3.5)),
                          slit + side * 0.15 + Vector((0, 0, 5.0)), slit - side * 0.15 + Vector((0, 0, 5.0))], normal,
                         VOID)
    eave = h + 0.9
    apex = Vector((0.0, 0.0, height + 0.35 + eave * pitch))
    for k in range(4):
        angle = TAU * k / 4 + math.pi / 4
        a = Vector((math.cos(angle) * eave * math.sqrt(2), math.sin(angle) * eave * math.sqrt(2), height + 0.2))
        b = Vector((math.cos(angle + TAU / 4) * eave * math.sqrt(2), math.sin(angle + TAU / 4) * eave * math.sqrt(2),
                    height + 0.2))
        middle = (a + b) / 2
        builder.oriented([a, b, apex], Vector((middle.x, middle.y, 0.0)).normalized() + Vector((0, 0, 1)),
                         "terracotta_tiles")
    return builder


def ship_shed_row(count, bay=7.0, length=40.0, height=6.5):
    builder = MeshBuilder()
    width = count * bay
    for k in range(count + 1):
        x = -width / 2 + k * bay
        painted(builder, WARM, lambda x=x: builder.box((x - 0.4, -length / 2, -4.5), (x + 0.4, length / 2, height),
                                                       STONE, bottom=False))
    for k in range(count):
        x0 = -width / 2 + k * bay
        x1 = x0 + bay
        mid = (x0 + x1) / 2
        for side in (-1, 1):
            edge = mid + side * (bay / 2 + 0.3)
            builder.oriented([(edge, -length / 2 - 0.5, height), (edge, length / 2, height),
                              (mid, length / 2, height + 2.2), (mid, -length / 2 - 0.5, height + 2.2)], (side, 0, 1),
                             "terracotta_tiles")
        builder.oriented([(x0 + 0.4, -length / 2, height), (x1 - 0.4, -length / 2, height),
                          (mid, -length / 2, height + 2.2)], (0, -1, 0), PLASTER)
        builder.tint(len(builder.polygons) - 1, OCHRE)
        painted(builder, (0.52, 0.42, 0.30), lambda x0=x0, x1=x1: builder.oriented(
            [(x0 + 0.5, -length / 2 - 6.0, -1.2), (x1 - 0.5, -length / 2 - 6.0, -1.2), (x1 - 0.5, length / 2, 1.5),
             (x0 + 0.5, length / 2, 1.5)], (0, 0, 1), MATTE))
    painted(builder, OCHRE, lambda: builder.box((-width / 2 - 0.4, length / 2, -4.5), (width / 2 + 0.4, length / 2 + 0.6,
                                                                                        height + 0.4), PLASTER,
                                                bottom=False))
    return builder


def warehouse(length=48.0, depth=15.0, height=8.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    colour = rng.choice([OCHRE, WARM, (0.96, 0.74, 0.56), (1.0, 0.9, 0.7)])
    painted(builder, (0.82, 0.78, 0.7), lambda: builder.box((-length / 2, -depth / 2, -5.0),
                                                            (length / 2, depth / 2, 0.6), STONE, bottom=False))
    painted(builder, colour, lambda: builder.box((-length / 2, -depth / 2, 0.6), (length / 2, depth / 2, height),
                                                 PLASTER, bottom=False, top=False))
    for side in (-1, 1):
        builder.oriented([(-length / 2 - 0.5, side * (depth / 2 + 0.5), height - 0.2),
                          (length / 2 + 0.5, side * (depth / 2 + 0.5), height - 0.2),
                          (length / 2 + 0.5, 0.0, height + depth * 0.2), (-length / 2 - 0.5, 0.0,
                                                                          height + depth * 0.2)],
                         (0, side, 1), "terracotta_tiles")
        builder.oriented([(side * length / 2, -depth / 2, height), (side * length / 2, depth / 2, height),
                          (side * length / 2, 0.0, height + depth * 0.2)], (side, 0, 0), PLASTER)
        builder.tint(len(builder.polygons) - 1, colour)
    count = int(length / 8.0)
    for k in range(count):
        x = -length / 2 + length * (k + 0.5) / count
        builder.oriented([(x - 1.4, -depth / 2 - 0.02, 0.6), (x + 1.4, -depth / 2 - 0.02, 0.6),
                          (x + 1.4, -depth / 2 - 0.02, 4.0), (x - 1.4, -depth / 2 - 0.02, 4.0)], (0, -1, 0), VOID)
    return builder


def awning_row(count=4, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    colours = [(0.86, 0.18, 0.12), (0.96, 0.76, 0.22), (0.18, 0.40, 0.76), (0.98, 0.96, 0.9), (0.30, 0.62, 0.40)]
    for k in range(count):
        x = k * 4.2
        colour = rng.choice(colours)
        for px, py in ((x - 1.8, -1.8), (x + 1.8, -1.8), (x - 1.8, 1.4), (x + 1.8, 1.4)):
            tube(builder, [(px, py, 0.0), (px, py, 2.6 if py < 0 else 3.0)], [0.05, 0.05], (0.44, 0.32, 0.22), 4)
        first = len(builder.polygons)
        builder.oriented([(x - 2.0, -2.0, 2.6), (x + 2.0, -2.0, 2.6), (x + 2.0, 1.6, 3.0), (x - 2.0, 1.6, 3.0)],
                         (0, 0, 1), MATTE)
        builder.oriented([(x - 2.0, -2.0, 2.6), (x + 2.0, -2.0, 2.6), (x + 2.0, 1.6, 3.0), (x - 2.0, 1.6, 3.0)],
                         (0, 0, -1), MATTE)
        builder.tint(first, colour)
        painted(builder, (0.56, 0.42, 0.28), lambda x=x: builder.box((x - 1.5, -1.2, 0.0), (x + 1.5, -0.4, 0.9),
                                                                     MATTE))
        for j in range(5):
            tone = rng.choice([(0.86, 0.30, 0.14), (0.40, 0.56, 0.22), (0.94, 0.80, 0.30), (0.62, 0.22, 0.30)])
            painted(builder, tone, lambda x=x, j=j: builder.box((x - 1.3 + j * 0.55, -1.1, 0.9),
                                                                (x - 0.9 + j * 0.55, -0.5, 1.08), MATTE))
    return builder


def frame(x, y, z, angle=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, "Z")
