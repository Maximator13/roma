import math
import random

from mathutils import Matrix, Vector

from .buildings import arched_wall, straight_moulding
from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import Look, coarse, drape, ellipsoid, person, tube
from .orders import (ENGAGED_HALF, column, facing_text_matrix, gable_roof, inscription, podium,
                     simple_entablature_profile)

MARBLE = "marble_white"
TRAV = "travertine"
BRICK = "brick"
STUCCO = "stucco"
PLASTER = "plaster"
TILES = "terracotta_tiles"
BRONZE = "bronze"
GILT = "bronze_gilt"
WATER = "water"
BASALT = "granite_grey"
VOID = "shadow_void"
PEPERINO = (0.74, 0.72, 0.66)
WOOD = (0.45, 0.33, 0.22)
UNIT = 9.0
OCHRE_RED = (0.55, 0.22, 0.18)
WINDOW = (0.12, 0.10, 0.09)
PATINA = "col_bronze_patina"
STUCCO_TINT = (0.86, 0.80, 0.70)


def window(builder, x, y, z, side, width=1.2, height=1.8, frame=0.15):
    hw = width / 2
    builder.oriented([(x - hw - frame, y + side * 0.03, z - frame), (x + hw + frame, y + side * 0.03, z - frame),
                      (x + hw + frame, y + side * 0.03, z + height + frame),
                      (x - hw - frame, y + side * 0.03, z + height + frame)], (0, side, 0), TRAV)
    painted(builder, WINDOW, lambda: builder.oriented([(x - hw, y + side * 0.05, z), (x + hw, y + side * 0.05, z),
                                                       (x + hw, y + side * 0.05, z + height),
                                                       (x - hw, y + side * 0.05, z + height)], (0, side, 0), MATTE))


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def unit_column(order, detail="low", material=MARBLE):
    return lambda: column(order, 1.0, UNIT, detail=detail, material=material)


def simple_column(material=MARBLE):
    def build():
        builder = MeshBuilder()
        builder.box((-0.7, -0.7, 0.0), (0.7, 0.7, 0.25), material, bottom=False)
        builder.lathe([(0.62, 0.25), (0.5, 0.45), (0.5, UNIT * 0.86), (0.43, UNIT * 0.9)], 10, material, caps=False)
        builder.lathe([(0.43, UNIT * 0.9), (0.62, UNIT * 0.95), (0.0, UNIT * 0.95)], 10, material, caps=False)
        builder.box((-0.68, -0.68, UNIT * 0.95), (0.68, 0.68, UNIT), material, bottom=False)
        return builder
    return build


def column_frame(x, y, z, diameter, height):
    return Matrix.Translation((x, y, z)) @ Matrix.Diagonal((diameter, diameter, height / UNIT, 1.0))


def pediment(builder, half, y, eave, ridge, facing, material=MARBLE, tympanum=(0.86, 0.84, 0.8)):
    builder.oriented([(-half, y, eave), (half, y, eave), (0.0, y, ridge)], (0, facing, 0), material)
    inner = [(-half + 0.8, y + facing * 0.03, eave + 0.25), (half - 0.8, y + facing * 0.03, eave + 0.25),
             (0.0, y + facing * 0.03, ridge - 0.45)]
    painted(builder, tympanum, lambda: builder.oriented(inner, (0, facing, 0), material))
    builder.box((-half - 0.3, y - 0.6 * (facing < 0), eave - 0.5), (half + 0.3, y + 0.6 * (facing > 0), eave),
                material, bottom=True)


def temple(width, length, podium_height, column_height, diameter, front, order, peripteral=False, pronaos=2,
           material=MARBLE, gilt=False, back_wall=True, steps=None):
    builder = MeshBuilder()
    hw = width / 2
    stair = max(podium_height * 1.15, 1.5)
    podium(builder, hw, -length / 2, length / 2, podium_height, stair, max(hw * 0.18, 1.2), material=MARBLE,
           moulding_material=MARBLE, steps=steps or max(int(podium_height / 0.3), 4))
    z = podium_height
    margin = diameter * 0.9
    spacing = (width - 2 * margin) / (front - 1)
    front_row = length / 2 - stair - diameter
    frames = []
    xs = [-hw + margin + spacing * i for i in range(front)]
    for x in xs:
        frames.append(column_frame(x, front_row, z, diameter, column_height))
    for row in range(1, pronaos):
        for x in (xs[0], xs[-1]):
            frames.append(column_frame(x, front_row - spacing * row, z, diameter, column_height))
    back = -length / 2 + margin
    cella_front = front_row - spacing * pronaos + diameter
    if peripteral:
        y = front_row - spacing * pronaos
        while y > back + 0.5:
            for x in (xs[0], xs[-1]):
                frames.append(column_frame(x, y, z, diameter, column_height))
            y -= spacing
        for x in xs:
            frames.append(column_frame(x, back, z, diameter, column_height))
        wall = hw - margin - spacing * 0.95
    else:
        wall = hw - 0.4
    top = z + column_height
    if back_wall:
        builder.box((-wall, back - diameter * 0.4 if not peripteral else back + spacing * 0.9, z),
                    (wall, cella_front, top), material, bottom=False, top=False)
        painted(builder, (0.42, 0.32, 0.2), lambda: builder.box((-1.6, cella_front, z), (1.6, cella_front + 0.05,
                                                                                         z + column_height * 0.6),
                                                                 BRONZE, bottom=False))
    entablature = diameter * 2.1
    rear = back - diameter * 0.7
    builder.box((-hw + margin - diameter * 0.7, rear, top), (hw - margin + diameter * 0.7, front_row + diameter * 0.7,
                                                              top + entablature * 0.75), material)
    straight_moulding(builder, -hw + margin - diameter * 0.7, hw - margin + diameter * 0.7, top + entablature * 0.45,
                      simple_entablature_profile(entablature * 0.55, diameter * 0.45), material,
                      y=front_row + diameter * 0.7)
    eave = top + entablature
    builder.box((-hw + margin - diameter * 0.9, rear, top + entablature * 0.75),
                (hw - margin + diameter * 0.9, front_row + diameter * 0.9, eave), material)
    painted(builder, OCHRE_RED, lambda: builder.box((-hw + margin - diameter * 0.74, rear + 0.16, top + entablature * 0.6),
                                                    (hw - margin + diameter * 0.74, front_row + diameter * 0.74,
                                                     top + entablature * 0.7), MATTE, bottom=False, top=False))
    half = hw - margin + diameter * 0.9
    ridge = eave + half * math.tan(math.radians(15))
    gable_roof(builder, rear, front_row + diameter * 0.9, half + 0.3, eave, ridge, GILT if gilt else TILES,
               along_axis="y", imbrex=not gilt, pitch=0.6)
    pediment(builder, half, front_row + diameter * 0.9, eave, ridge, 1, material, OCHRE_RED)
    pediment(builder, half, rear, eave, ridge, -1, material, OCHRE_RED)
    for x, zz in ((0.0, ridge), (-half, eave), (half, eave)):
        builder.box((x - 0.35, front_row + diameter * 0.4, zz), (x + 0.35, front_row + diameter * 1.0, zz + 1.1), GILT)
    return builder, {order: frames}


def round_temple(radius=7.5, podium_height=3.0, columns=20, column_height=8.0, diameter=0.62):
    builder = MeshBuilder()
    builder.lathe([(radius, -0.6), (radius, podium_height - 0.4), (radius + 0.2, podium_height - 0.25),
                   (radius + 0.2, podium_height)], 32, MARBLE)
    builder.lathe([(radius + 0.2, podium_height), (0.0, podium_height)], 32, MARBLE)
    for k in range(int(podium_height / 0.3)):
        builder.box((-1.6, radius - 0.2 + 0.32 * (int(podium_height / 0.3) - k), 0.3 * k - 0.6),
                    (1.6, radius + 0.32 * (int(podium_height / 0.3) - k) + 0.1, 0.3 * (k + 1)), MARBLE, bottom=False)
    frames = []
    ring = radius - diameter
    for k in range(columns):
        angle = 2 * math.pi * k / columns
        frames.append(column_frame(ring * math.cos(angle), ring * math.sin(angle), podium_height, diameter,
                                   column_height))
    top = podium_height + column_height
    builder.lathe([(radius - 2.2, podium_height), (radius - 2.2, top)], 24, MARBLE, caps=False)
    builder.lathe([(radius + 0.1, top), (radius + 0.1, top + 1.3), (radius - 2.6, top + 1.3), (radius - 2.6, top)], 32,
                  MARBLE)
    builder.lathe([(radius + 0.5, top + 1.3), (radius * 0.55, top + 4.6), (0.9, top + 6.0), (0.9, top + 6.4),
                   (0.0, top + 6.4)], 24, BRONZE)
    painted(builder, (0.82, 0.62, 0.34), lambda: builder.box((-1.0, radius - 2.25, podium_height),
                                                             (1.0, radius - 2.15, podium_height + 4.5), BRONZE,
                                                             bottom=False))
    return builder, {"corinthian": frames}


def arcade_bay(width, depth, storey=7.6, storeys=2, diameter=0.8, shops=False, aisle_roof=True, material=MARBLE):
    builder = MeshBuilder()
    hw = width / 2
    half = (width - diameter * 1.5) / 2
    for level in range(storeys):
        z0 = level * storey
        top = z0 + storey - 1.2
        sill = z0 + 1.0 if level else None
        arched_wall(builder, -hw, hw, -1.0, 0.0, z0, top, [(0.0, half, z0 + storey - 1.4 - half)], material,
                    segments=6, sill=sill, foundation=1.2 if level == 0 else 0.0)
        builder.merge(column("tuscan" if level == 0 else "ionic", diameter, storey - 1.2 - (1.0 if level else 0.0),
                             detail="low", material=material, arc=ENGAGED_HALF),
                      placement(-hw, 0.02, z0 + (1.0 if level else 0.0)))
        builder.box((-hw, -1.0, top), (hw, -0.2, z0 + storey), material, bottom=False)
        straight_moulding(builder, -hw, hw, top, simple_entablature_profile(1.2, 0.35), material)
        builder.box((-hw, -depth, z0 + storey - 0.5), (hw, -1.0, z0 + storey), STUCCO, top=level == storeys - 1)
        if shops and level == 0:
            builder.box((-hw, -6.2, z0), (hw, -5.6, z0 + storey - 0.5), PLASTER, bottom=False, top=False)
            builder.box((-1.3, -5.65, z0), (1.3, -5.55, z0 + 3.2), VOID, bottom=False)
        else:
            builder.box((-hw, -depth, z0), (hw, -depth + 0.6, z0 + storey), PLASTER, bottom=False, top=False)
    builder.box((-hw, -depth, -0.2), (hw, 0.0, 0.0), MARBLE, bottom=False)
    if aisle_roof:
        z = storeys * storey
        rise = depth * 0.22
        rows = [[(-hw, 0.4, z), (hw, 0.4, z)], [(-hw, -depth, z + rise), (hw, -depth, z + rise)]]
        builder.surface(rows, TILES, facing=(0, 0.3, 1))
        builder.box((-hw, -0.1, z), (hw, 0.3, z + 0.5), material, bottom=False)
    return builder


def clerestory_hall(length, width, wall_bottom, wall_top, material=PLASTER, windows=8, roof=TILES):
    builder = MeshBuilder()
    hl, hw = length / 2, width / 2
    builder.box((-hl, -hw, wall_bottom), (hl, hw, wall_top), material, bottom=False, top=False)
    for side in (-1, 1):
        for k in range(windows):
            x = -hl + length * (k + 0.5) / windows
            y = side * (hw + 0.02)
            window(builder, x, side * hw, wall_top - 4.4, side, 1.4, 2.6)
    gable_roof(builder, -hl - 0.4, hl + 0.4, hw + 0.8, wall_top, wall_top + hw * 0.42, roof, along_axis="x",
               imbrex=False)
    for x, facing in ((-hl, -1), (hl, 1)):
        builder.oriented([(x, -hw, wall_top), (x, hw, wall_top), (x, 0.0, wall_top + hw * 0.42)], (facing, 0, 0),
                         material)
    return builder


def ring_of_bays(length, width, spacing, sides=("front", "back", "left", "right")):
    frames = []
    hl, hw = length / 2, width / 2
    count_long = max(int(round(length / spacing)), 1)
    count_short = max(int(round(width / spacing)), 1)
    step_long = length / count_long
    step_short = width / count_short
    if "front" in sides:
        frames += [(placement(-hl + step_long * (i + 0.5), hw, 0.0, 0.0), step_long) for i in range(count_long)]
    if "back" in sides:
        frames += [(placement(hl - step_long * (i + 0.5), -hw, 0.0, math.pi), step_long) for i in range(count_long)]
    if "right" in sides:
        frames += [(placement(hl, -hw + step_short * (i + 0.5), 0.0, -math.pi / 2), step_short)
                   for i in range(count_short)]
    if "left" in sides:
        frames += [(placement(-hl, hw - step_short * (i + 0.5), 0.0, math.pi / 2), step_short)
                   for i in range(count_short)]
    return frames


def basilica_julia():
    builder = MeshBuilder()
    builder.box((-50.5, -24.5, -1.0), (50.5, 24.5, 1.1), MARBLE, bottom=False)
    for k in range(5):
        builder.box((-50.5 - 0.0, 24.5 + 0.35 * (4 - k), -1.0 + 0.0), (50.5, 24.5 + 0.35 * (5 - k), 0.22 * (k + 1)),
                    MARBLE, bottom=False)
    hall = clerestory_hall(82.0, 16.0, 15.0, 24.0, material=PLASTER, windows=12)
    builder.merge(hall, Matrix.Translation((0.0, 0.0, 1.1)))
    builder.box((-41.0, -8.0, 1.1), (41.0, 8.0, 16.2), BRICK, bottom=False, top=False)
    return builder, [(Matrix.Translation((0.0, 0.0, 1.1)) @ matrix, step) for matrix, step in
                     ring_of_bays(101.0, 49.0, 5.6)]


def basilica_paulli():
    builder = MeshBuilder()
    builder.box((-45.0, -27.0, -1.0), (45.0, 6.0, 0.9), MARBLE, bottom=False)
    hall = clerestory_hall(90.0, 13.0, 14.0, 25.0, material=PLASTER, windows=12)
    builder.merge(hall, Matrix.Translation((0.0, -14.0, 0.9)))
    builder.box((-45.0, -27.0, 0.9), (45.0, -20.5, 13.5), PLASTER, bottom=False)
    builder.box((-45.0, -7.5, 0.9), (45.0, -1.0, 13.5), PLASTER, bottom=False)
    for y0, y1 in ((-27.0, -20.5), (-7.5, -1.0)):
        gable_roof(builder, -45.4, 45.4, (y1 - y0) / 2 + 0.4, 13.5, 15.0, TILES, along_axis="x", imbrex=False)
    shifted = []
    for matrix, step in ring_of_bays(90.0, 12.0, 6.0, sides=("front",)):
        shifted.append((Matrix.Translation((0.0, 0.0, 0.9)) @ matrix, step))
    return builder, shifted


def curia():
    builder = MeshBuilder()
    w, d, h = 17.6, 25.2, 21.0
    builder.box((-w / 2, -d / 2, 0.0), (w / 2, d / 2, h), PLASTER, bottom=False, top=False)
    builder.box((-w / 2 - 0.05, -d / 2 - 0.05, 0.0), (w / 2 + 0.05, d / 2 + 0.05, 3.2), MARBLE, bottom=False,
                top=False)
    for x in (-5.0, 0.0, 5.0):
        builder.oriented([(x - 1.6, d / 2 + 0.07, 13.0), (x + 1.6, d / 2 + 0.07, 13.0), (x + 1.6, d / 2 + 0.07, 18.0),
                          (x - 1.6, d / 2 + 0.07, 18.0)], (0, 1, 0), VOID)
    painted(builder, (0.48, 0.34, 0.2), lambda: builder.box((-1.7, d / 2, 0.6), (1.7, d / 2 + 0.12, 7.6), BRONZE,
                                                            bottom=False))
    for k in range(4):
        builder.box((-4.5, d / 2 + 0.6 * (4 - k), 0.15 * k - 0.4), (4.5, d / 2 + 0.6 * (5 - k), 0.15 * (k + 1)),
                    MARBLE, bottom=False)
    builder.box((-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h + 0.8), MARBLE)
    ridge = h + 0.8 + w / 2 * 0.55
    gable_roof(builder, -d / 2 - 0.4, d / 2 + 0.4, w / 2 + 0.5, h + 0.8, ridge, TILES, along_axis="y", imbrex=False)
    pediment(builder, w / 2 + 0.3, d / 2 + 0.3, h + 0.8, ridge, 1, PLASTER)
    pediment(builder, w / 2 + 0.3, -d / 2 - 0.3, h + 0.8, ridge, -1, PLASTER)
    return builder


def rostra():
    builder = MeshBuilder()
    builder.box((-12.0, -5.0, -0.5), (12.0, 5.0, 3.2), MARBLE, bottom=False)
    for row, z in enumerate((1.0, 2.2)):
        for k in range(9 if row == 0 else 8):
            x = -10.8 + 21.6 * (k + 0.5 * row + 0.5) / 9.5
            painted(builder, (0.55, 0.42, 0.25), lambda x=x, z=z: builder.lathe(
                [(0.0, 0.0), (0.28, 0.15), (0.24, 0.9), (0.0, 1.3)], 6, BRONZE,
                matrix=Matrix.Translation((x, 5.0, z)) @ Matrix.Rotation(-math.pi / 2, 4, "X")))
    for x0, x1, y0, y1 in ((-12.0, 12.0, 4.7, 5.0), (-12.0, -11.7, -5.0, 5.0), (11.7, 12.0, -5.0, 5.0)):
        builder.box((x0, y0, 3.2), (x1, y1, 3.3), MARBLE, bottom=False)
        builder.box((x0, y0, 4.2), (x1, y1, 4.35), MARBLE)
        span = max(x1 - x0, y1 - y0)
        for k in range(int(span / 0.6)):
            t = (k + 0.5) / int(span / 0.6)
            x = x0 + (x1 - x0) * t if x1 - x0 > 1 else (x0 + x1) / 2
            y = y0 + (y1 - y0) * t if y1 - y0 > 1 else (y0 + y1) / 2
            builder.box((x - 0.09, y - 0.09, 3.3), (x + 0.09, y + 0.09, 4.2), MARBLE, bottom=False, top=False)
    for k in range(10):
        r = 12.0 - 0.6 * k
        builder.box((-r, -5.0 - 0.45 * (10 - k), -0.5), (r, -5.0 - 0.45 * (9 - k), 0.32 * (k + 1)), MARBLE,
                    bottom=False)
    return builder


def tabularium(length=72.0, base=14.0, gallery=9.0, bays=11):
    builder = MeshBuilder()
    hl = length / 2
    painted(builder, PEPERINO, lambda: builder.box((-hl, -14.0, -4.0), (hl, 0.0, base), TRAV, bottom=False))
    for k in range(6):
        painted(builder, PEPERINO, lambda k=k: builder.box((-hl + 6 + 11.0 * k, 0.0, 6.0),
                                                            (-hl + 6.6 + 11.0 * k, 0.05, 7.4), VOID, bottom=False))
    width = length / bays
    for k in range(bays):
        x0 = -hl + width * k
        arched_wall(builder, x0, x0 + width, -1.2, 0.0, base, base + gallery - 1.4,
                    [(x0 + width / 2, width * 0.32, base + gallery - 1.6 - width * 0.32)], TRAV, segments=6)
        builder.merge(column("tuscan", 0.8, gallery - 1.4, detail="low", material=TRAV, arc=ENGAGED_HALF),
                      placement(x0, 0.02, base))
    builder.box((-hl, -6.0, base), (hl, -5.4, base + gallery), PLASTER, bottom=False)
    builder.box((-hl, -6.0, base + gallery - 0.4), (hl, -1.2, base + gallery - 0.1), STUCCO, top=False, bottom=True)
    builder.box((-hl, -1.2, base + gallery - 1.4), (hl, -0.2, base + gallery), TRAV, bottom=False)
    straight_moulding(builder, -hl, hl, base + gallery - 1.4, simple_entablature_profile(1.4, 0.4), TRAV)
    builder.box((-hl, -14.0, base + gallery), (hl, -6.0, base + gallery + 6.0), PLASTER, bottom=False)
    gable_roof(builder, -hl, hl, 4.4, base + gallery + 6.0, base + gallery + 8.0, TILES, along_axis="x", imbrex=False)
    builder.merge(MeshBuilder().box((-hl, -6.4, base + gallery), (hl, -1.0, base + gallery + 0.3), TRAV),
                  Matrix.Identity(4))
    return builder


def arch_of_titus():
    builder = MeshBuilder()
    w, d = 13.5, 4.75
    hw, hd = w / 2, d / 2
    passage = 5.36 / 2
    impost = 8.3 - passage
    arched_wall(builder, -hw, hw, -hd, hd, 0.0, 11.0, [(0.0, passage, impost)], MARBLE, segments=12, foundation=0.6)
    builder.box((-hw - 0.15, -hd - 0.15, 9.2), (hw + 0.15, hd + 0.15, 11.0), MARBLE, bottom=False)
    for facing in (-1, 1):
        y = facing * hd
        flip = Matrix.Rotation(0.0 if facing > 0 else math.pi, 4, "Z")
        straight = MeshBuilder()
        straight_moulding(straight, -hw - 0.15, hw + 0.15, 10.2, simple_entablature_profile(0.8, 0.45), MARBLE,
                          y=hd + 0.15)
        builder.merge(straight, flip)
        for x in (-hw + 0.75, -passage - 0.9, passage + 0.9, hw - 0.75):
            builder.box((x - 0.75, y - 0.5 * (facing < 0), 0.0), (x + 0.75, y + 0.5 * (facing > 0), 2.6), MARBLE,
                        bottom=False)
            builder.merge(column("corinthian", 0.8, 6.6, detail="low", material=MARBLE, arc=ENGAGED_HALF),
                          Matrix.Translation((x, y, 2.6)) @ flip)
        for side in (-1, 1):
            flat = Matrix.Translation((side * (passage + 1.15), y + facing * 0.12, 7.1)) @ flip @ \
                Matrix.Rotation(side * math.radians(-68), 4, "Y") @ Matrix.Diagonal((1.35, 0.3, 1.35, 1.0)) @ \
                Matrix.Translation((0.0, 0.0, -0.9))
            builder.merge(victory(50 + side), flat)
    builder.box((-hw + 0.3, -hd + 0.3, 11.0), (hw - 0.3, hd - 0.3, 15.0), MARBLE, bottom=False)
    builder.box((-hw + 0.1, -hd + 0.1, 15.0), (hw - 0.1, hd - 0.1, 15.4), MARBLE)
    builder.box((-3.4, -2.0, 15.4), (3.4, 2.0, 16.4), MARBLE)
    builder.merge(quadriga(), placement(0.0, 0.3, 16.4, 0.0, 1.6))
    for facing in (-1, 1):
        builder.box((-hw + 0.2, facing * (hd - 0.3) - 0.1, 11.0), (hw - 0.2, facing * (hd - 0.3) + 0.1, 11.4),
                    MARBLE, bottom=False)
    builder.merge(relief_panel(True), Matrix.Translation((passage, 0.0, 2.4)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    builder.merge(relief_panel(False), Matrix.Translation((-passage, 0.0, 2.4)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    lines = ["SENATVS", "POPVLVSQVE·ROMANVS", "DIVO·TITO·DIVI·VESPASIANI·F", "VESPASIANO·AVGVSTO"]
    for index, text in enumerate(lines):
        letters, width = inscription(text, 0.42 if index < 2 else 0.36, material=MARBLE, depth=0.04)
        letters.tint(0, (0.42, 0.4, 0.37))
        builder.merge(letters, facing_text_matrix(Vector((0.0, hd - 0.28, 14.25 - 0.82 * index)), (0, 1, 0)))
    return builder


def relief_panel(menorah):
    builder = MeshBuilder()
    tone = (0.9, 0.88, 0.83)
    builder.box((-2.1, -0.05, 0.0), (2.1, 0.0, 2.1), MARBLE, bottom=False)
    flat = Matrix.Diagonal((0.24, 0.62, 0.62, 1.0))
    for k in range(7):
        x = -1.8 + 0.6 * k
        look = Look("white", hem=0.5, belt="white", arms="carry" if menorah and k in (2, 3, 4) else "forward",
                    mono=tone, material=MARBLE, stride=0.12, seed=70 + k)
        builder.merge(coarse(lambda look=look: person(look), 0.4),
                      Matrix.Translation((x, 0.05, 0.15)) @ Matrix.Rotation(-math.pi / 2, 4, "Z") @ flat)
    if menorah:
        base = Vector((0.0, 0.12, 1.25))
        tube(builder, [base, base + Vector((0.0, 0.0, 0.62))], [0.035, 0.03], tone, 5, MARBLE)
        for k, radius in enumerate((0.12, 0.22, 0.32)):
            for side in (-1, 1):
                arc = [base + Vector((side * radius * math.sin(a), 0.0, 0.28 + radius * (1 - math.cos(a))))
                       for a in (0.0, 0.6, 1.2, math.pi / 2)]
                arc.append(base + Vector((side * radius, 0.0, 0.62)))
                tube(builder, arc, [0.018] * len(arc), tone, 4, MARBLE)
        builder.box((-0.3, 0.06, 1.1), (0.3, 0.18, 1.25), MARBLE)
    else:
        for k in range(4):
            horse = Matrix.Translation((-0.6 + 0.3 * k, 0.08, 0.2)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
            ellipsoid(builder, (0.0, 0.0, 0.9), (0.18, 0.55, 0.22), tone, 6, 4, MARBLE, matrix=horse @ flat)
        painted(builder, tone, lambda: builder.box((0.4, 0.02, 0.4), (1.2, 0.2, 1.1), MARBLE))
    return builder


def meta_sudans():
    builder = MeshBuilder()
    builder.lathe([(8.2, -0.4), (8.2, 0.75), (7.7, 0.75), (7.7, -0.6)], 36, MARBLE)
    builder.lathe([(7.7, 0.35), (0.0, 0.35)], 36, WATER)
    builder.lathe([(2.6, -0.3), (2.6, 1.2), (2.9, 1.4), (2.9, 1.8), (2.5, 1.9), (2.5, 6.2), (2.75, 6.5), (2.2, 6.6),
                   (1.6, 10.5), (1.0, 14.0), (0.55, 16.4), (0.7, 16.8), (0.35, 17.3), (0.0, 17.5)], 24, MARBLE)
    builder.lathe([(2.63, 2.0), (2.63, 6.15), (2.24, 6.62), (1.63, 10.5), (1.03, 14.0), (0.58, 16.3)], 24, WATER,
                  caps=False)
    for k in range(8):
        angle = 2 * math.pi * (k + 0.5) / 8
        builder.box((-0.55, 2.4, 2.4), (0.55, 2.62, 4.8), VOID, bottom=False,
                    matrix=Matrix.Rotation(angle - math.pi / 2, 4, "Z"))
    return builder


def sol_figure(colour=(1.0, 1.0, 1.0), material=PATINA):
    body = MeshBuilder()
    c = colour
    drape(body, c, [(0.0, 0.8), (0.12, 0.81), (0.18, 0.86), (0.19, 0.94), (0.168, 1.03), (0.158, 1.1), (0.168, 1.18),
                    (0.186, 1.27), (0.2, 1.34), (0.205, 1.4), (0.16, 1.45), (0.065, 1.48), (0.0, 1.49)], 18,
          folds=(0, 0.0, 0.0), squash=0.6, material=material)
    for side, ankle, knee, hip in ((1, (0.1, 0.0, 0.075), (0.105, 0.02, 0.5), (0.09, 0.0, 0.9)),
                                   (-1, (-0.15, -0.12, 0.1), (-0.12, 0.07, 0.5), (-0.09, 0.0, 0.88))):
        ankle, knee, hip = Vector(ankle), Vector(knee), Vector(hip)
        ellipsoid(body, ankle + Vector((0.0, 0.065, -0.045)), (0.048, 0.115, 0.038), c, 8, 4, material)
        tube(body, [ankle, ankle.lerp(knee, 0.3), ankle.lerp(knee, 0.62), knee, knee.lerp(hip, 0.45), hip],
             [0.042, 0.06, 0.066, 0.056, 0.085, 0.105], c, 10, material, cap=False)
    tube(body, [(0.0, 0.0, 1.45), (0.0, 0.012, 1.52), (0.0, 0.02, 1.58)], [0.058, 0.052, 0.05], c, 10, material)
    ellipsoid(body, (0.0, 0.025, 1.645), (0.082, 0.096, 0.108), c, 12, 7, material)
    ellipsoid(body, (0.0, 0.0, 1.675), (0.09, 0.095, 0.092), c, 10, 6, material)
    tube(body, [(0.0, 0.112, 1.665), (0.0, 0.13, 1.625)], [0.012, 0.007], c, 4, material)
    for side, elbow, wrist in ((1, (0.36, 0.06, 1.25), (0.42, 0.12, 1.55)), (-1, (-0.27, 0.0, 1.13), (-0.29, 0.13, 1.0))):
        shoulder = Vector((side * 0.19, 0.0, 1.39))
        elbow, wrist = Vector(elbow), Vector(wrist)
        ellipsoid(body, shoulder + Vector((side * 0.01, 0.0, 0.0)), (0.07, 0.065, 0.065), c, 8, 5, material)
        tube(body, [shoulder, shoulder.lerp(elbow, 0.5), elbow, elbow.lerp(wrist, 0.5), wrist],
             [0.068, 0.062, 0.05, 0.047, 0.034], c, 10, material)
        direction = (wrist - elbow).normalized()
        ellipsoid(body, wrist + direction * 0.06, (0.028, 0.02, 0.055), c, 6, 4, material)
    ellipsoid(body, (-0.3, 0.2, 1.02), (0.085, 0.085, 0.085), c, 10, 6, material)
    tube(body, [(-0.2, -0.05, 1.43), (-0.29, -0.08, 1.25), (-0.33, -0.05, 1.02), (-0.33, -0.02, 0.78),
                (-0.31, 0.0, 0.62)], [0.07, 0.09, 0.1, 0.095, 0.06], c, 10, material, squash=0.35)
    tube(body, [(-0.2, -0.13, 0.02), (-0.24, -0.12, 0.92)], [0.016, 0.014], c, 5, material)
    body.box((-0.215, -0.27, 0.02), (-0.205, -0.13, 0.5), material)
    crown = MeshBuilder()
    drape(crown, (1.0, 1.0, 1.0), [(0.098, 1.68), (0.1, 1.72)], 12, folds=(0, 0.0, 0.0), squash=1.0, material=GILT)
    for k in range(7):
        angle = math.radians(-72 + 24 * k)
        root = Vector((0.0, 0.0, 1.66)) + Vector((math.sin(angle) * 0.1, -0.01, math.cos(angle) * 0.1))
        tip = Vector((0.0, 0.0, 1.66)) + Vector((math.sin(angle) * 0.31, -0.03, math.cos(angle) * 0.31))
        tube(crown, [root, tip], [0.012, 0.002], (1.0, 1.0, 1.0), 4, GILT, squash=0.3)
    body.merge(crown)
    return body


def colossus():
    builder = MeshBuilder()
    builder.box((-6.0, -6.0, -1.0), (6.0, 6.0, 5.4), MARBLE, bottom=False)
    for k in range(3):
        builder.box((-6.0 - 0.5 * (3 - k), -6.0 - 0.5 * (3 - k), -1.0), (6.0 + 0.5 * (3 - k), 6.0 + 0.5 * (3 - k),
                                                                        0.35 * (k + 1)), MARBLE, bottom=False)
    builder.box((-5.4, -5.4, 5.4), (5.4, 5.4, 6.0), MARBLE)
    builder.merge(sol_figure(), Matrix.Translation((0.0, 0.0, 6.0)) @ Matrix.Scale(17.0, 4))
    return builder


def horse(builder, matrix, colour, material, gait=0.0):
    local = MeshBuilder()
    ellipsoid(local, (0.0, 0.0, 1.35), (0.3, 0.85, 0.36), colour, 10, 6, material)
    tube(local, [(0.0, 0.6, 1.5), (0.0, 0.85, 1.95), (0.0, 0.95, 2.1)], [0.2, 0.15, 0.11], colour, 8, material)
    ellipsoid(local, (0.0, 1.12, 2.02), (0.11, 0.3, 0.13), colour, 8, 4, material,
              matrix=Matrix.Rotation(math.radians(-35), 4, "X"))
    tube(local, [(0.0, 0.62, 1.82), (0.0, 0.88, 2.2)], [0.03, 0.03], colour, 4, material, squash=0.3)
    for side in (-1, 1):
        for end, lift in ((1, gait), (-1, 0.0)):
            y = end * 0.55
            hoof = (side * 0.16, y + 0.3 * lift, 0.04 + 0.4 * lift)
            tube(local, [(side * 0.16, y, 1.2), (side * 0.16, y + 0.05 * end, 0.7), hoof], [0.09, 0.05, 0.045],
                 colour, 6, material)
    tube(local, [(0.0, -0.8, 1.45), (0.0, -1.0, 1.1), (0.0, -1.05, 0.7)], [0.06, 0.07, 0.05], colour, 5, material)
    builder.merge(local, matrix)


def quadriga(material=PATINA, colour=(1.0, 1.0, 1.0)):
    builder = MeshBuilder()
    for k, x in enumerate((-1.2, -0.4, 0.4, 1.2)):
        horse(builder, placement(x, 0.8, 0.0, 0.0, 1.05), colour, material, gait=0.6 if k in (1, 2) else 0.0)
    builder.box((-0.55, -1.15, 0.75), (0.55, -0.55, 1.3), material)
    for side in (-1, 1):
        builder.lathe([(0.0, -0.05), (0.62, -0.05), (0.62, 0.05), (0.0, 0.05)], 10, material,
                      matrix=Matrix.Translation((side * 0.82, -0.8, 0.62)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    builder.merge(coarse(lambda: person(Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=colour,
                                             material=material, seed=88)), 0.5), placement(0.0, -0.8, 1.0, 0.0, 1.25))
    return builder


def victory(seed=50):
    builder = coarse(lambda: person(Look("white", hem=0.05, palla="white", female=True, sleeves="long", arms="gesture",
                                         mono=(0.93, 0.91, 0.86), material=MARBLE, seed=seed)), 0.5)
    for side in (-1, 1):
        wing = Matrix.Translation((side * 0.12, -0.14, 1.32)) @ Matrix.Rotation(side * math.radians(28), 4, "Y")
        ellipsoid(builder, (0.0, 0.0, 0.3), (0.05, 0.22, 0.48), (0.93, 0.91, 0.86), 8, 5, MARBLE, matrix=wing)
    return builder


def portico_ring(length, width, height=6.5, depth=6.0, spacing=4.0):
    builder = MeshBuilder()
    frames = []
    hl, hw = length / 2, width / 2
    for (x0, y0), (x1, y1), (nx, ny) in (((-hl, hw), (hl, hw), (0, -1)), ((hl, -hw), (-hl, -hw), (0, 1)),
                                         ((hl, hw), (hl, -hw), (-1, 0)), ((-hl, -hw), (-hl, hw), (1, 0))):
        span = math.hypot(x1 - x0, y1 - y0)
        count = int(span / spacing)
        for k in range(count + 1):
            t = k / count
            x = x0 + (x1 - x0) * t + nx * depth
            y = y0 + (y1 - y0) * t + ny * depth
            frames.append(column_frame(x, y, 0.4, 0.6, height))
    for x0, y0, x1, y1 in ((-hl, hw - depth - 0.6, hl, hw), (-hl, -hw, hl, -hw + depth + 0.6),
                           (hl - depth - 0.6, -hw, hl, hw), (-hl, -hw, -hl + depth + 0.6, hw)):
        builder.box((x0, y0, height + 0.4), (x1, y1, height + 1.3), MARBLE)
        builder.box((x0, y0, -0.6), (x1, y1, 0.4), MARBLE, bottom=False)
    rise = 1.6
    for (x0, x1, y0, y1, normal) in ((-hl, hl, hw - depth - 0.6, hw, (0, -0.4, 1)),
                                     (-hl, hl, -hw, -hw + depth + 0.6, (0, 0.4, 1))):
        outer = hw if y1 == hw else -hw
        inner = y0 if y1 == hw else y1
        builder.surface([[(x0, inner, height + 1.3), (x1, inner, height + 1.3)],
                         [(x0, outer, height + 1.3 + rise), (x1, outer, height + 1.3 + rise)]], TILES, facing=(0, 0, 1))
    for (y0, y1, x0, x1) in ((-hw, hw, hl - depth - 0.6, hl), (-hw, hw, -hl, -hl + depth + 0.6)):
        outer = hl if x1 == hl else -hl
        inner = x0 if x1 == hl else x1
        builder.surface([[(inner, y0, height + 1.3), (inner, y1, height + 1.3)],
                         [(outer, y0, height + 1.3 + rise), (outer, y1, height + 1.3 + rise)]], TILES, facing=(0, 0, 1))
    builder.box((-hl, hw - 0.6, 0.4), (hl, hw, height + 1.3), PLASTER, bottom=False, top=False)
    builder.box((-hl, -hw, 0.4), (hl, -hw + 0.6, height + 1.3), PLASTER, bottom=False, top=False)
    builder.box((hl - 0.6, -hw, 0.4), (hl, hw, height + 1.3), PLASTER, bottom=False, top=False)
    builder.box((-hl, -hw, 0.4), (-hl + 0.6, hw, height + 1.3), PLASTER, bottom=False, top=False)
    return builder, frames


def hall(width, depth, height, material=BRICK, roof="gable", windows=3):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    builder.box((-hw, -hd, -3.0), (hw, hd, height), material, bottom=False, top=roof == "flat")
    levels = (0.62,) if height < 14 else (0.36, 0.7)
    for side in (-1, 1):
        for k in range(windows):
            x = -hw + width * (k + 0.5) / windows
            for level in levels:
                window(builder, x, side * hd, height * level, side)
        ends = max(int(windows * depth / width), 1)
        for k in range(ends):
            y = -hd + depth * (k + 0.5) / ends
            for level in levels:
                local = MeshBuilder()
                window(local, -y * side, hw, height * level, 1)
                builder.merge(local, Matrix.Rotation(-side * math.pi / 2, 4, "Z"))
    if roof in ("gable", "vault"):
        pitch = 0.4 if roof == "gable" else 0.22
        gable_roof(builder, -hd - 0.4, hd + 0.4, hw + 0.5, height, height + hw * pitch, TILES, along_axis="y",
                   imbrex=False)
        for y, facing in ((-hd, -1), (hd, 1)):
            builder.oriented([(-hw, y, height), (hw, y, height), (0.0, y, height + hw * pitch)], (0, facing, 0),
                             material)
    elif roof == "dome":
        radius = min(hw, hd) * 0.9
        builder.box((-hw, -hd, height - 0.1), (hw, hd, height), material)
        painted(builder, (0.78, 0.74, 0.68), lambda: builder.lathe(
            [(radius, height), (radius * 0.92, height + radius * 0.4), (radius * 0.7, height + radius * 0.72),
             (radius * 0.38, height + radius * 0.93), (0.0, height + radius)], 16, STUCCO))
    return builder


def court(width, depth, height=6.0, spacing=3.6, garden=True, basin=None, roof=True):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    frames = []
    for (x0, y0), (x1, y1) in (((-hw, -hd), (hw, -hd)), ((hw, -hd), (hw, hd)), ((hw, hd), (-hw, hd)),
                               ((-hw, hd), (-hw, -hd))):
        span = math.hypot(x1 - x0, y1 - y0)
        count = max(int(span / spacing), 1)
        for k in range(count):
            t = k / count
            frames.append(column_frame(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.3, 0.5, height))
    if garden:
        painted(builder, (0.42, 0.5, 0.28), lambda: builder.box((-hw + 1.2, -hd + 1.2, -0.3), (hw - 1.2, hd - 1.2, 0.36),
                                                                MATTE, bottom=False))
    builder.box((-hw - 5.0, -hd - 5.0, -0.6), (hw + 5.0, hd + 5.0, 0.3), MARBLE, bottom=False)
    if basin is not None:
        bw, bd = basin
        builder.box((-bw / 2 - 0.4, -bd / 2 - 0.4, 0.15), (bw / 2 + 0.4, bd / 2 + 0.4, 0.75), MARBLE, bottom=False)
        builder.box((-bw / 2, -bd / 2, 0.2), (bw / 2, bd / 2, 0.6), WATER, bottom=False)
    if roof:
        for x0, y0, x1, y1, n in ((-hw - 5.0, hd, hw + 5.0, hd + 5.0, (0, -1, 1)), (-hw - 5.0, -hd - 5.0, hw + 5.0, -hd,
                                                                                    (0, 1, 1)),
                                  (hw, -hd, hw + 5.0, hd, (-1, 0, 1)), (-hw - 5.0, -hd, -hw, hd, (1, 0, 1))):
            builder.box((x0, y0, height + 0.3), (x1, y1, height + 1.0), MARBLE, bottom=True, top=False)
            builder.box((x0, y0, height + 1.0), (x1, y1, height + 1.6), TILES, bottom=False)
    return builder, frames


def construction_crane(height=16.0):
    builder = MeshBuilder()
    for side in (-1, 1):
        tube(builder, [(side * 1.4, -1.5, 0.0), (side * 0.2, 0.0, height)], [0.14, 0.11], WOOD, 5)
        tube(builder, [(side * 1.4, 1.5, 0.0), (side * 0.2, 0.0, height)], [0.14, 0.11], WOOD, 5)
    tube(builder, [(0.0, 0.0, height), (0.0, 4.0, height - 2.0)], [0.08, 0.06], (0.5, 0.42, 0.3), 4)
    tube(builder, [(0.0, 4.0, height - 2.0), (0.0, 4.0, 2.0)], [0.03, 0.03], (0.5, 0.42, 0.3), 3)
    builder.box((-0.4, 3.6, 1.2), (0.4, 4.4, 2.0), TRAV)
    for k in range(10):
        angle = 2 * math.pi * k / 10
        a = Vector((-1.6, 2.3 * math.cos(angle), 2.6 + 2.3 * math.sin(angle)))
        b = Vector((1.6, 2.3 * math.cos(angle), 2.6 + 2.3 * math.sin(angle)))
        tube(builder, [a, b], [0.05, 0.05], WOOD, 3)
    for x in (-1.6, 1.6):
        painted(builder, WOOD, lambda x=x: builder.lathe([(2.4, -0.05), (2.4, 0.05)], 16, MATTE, caps=False,
                                                         matrix=Matrix.Translation((x, 0.0, 2.6))
                                                         @ Matrix.Rotation(math.pi / 2, 4, "Y")))
    return builder


def scaffold(length, height, spacing=2.5):
    builder = MeshBuilder()
    count = int(length / spacing)
    for k in range(count + 1):
        x = -length / 2 + spacing * k
        for y in (0.0, 1.4):
            tube(builder, [(x, y, 0.0), (x, y, height)], [0.06, 0.05], WOOD, 3)
    for z in range(2, int(height), 2):
        painted(builder, (0.58, 0.46, 0.32), lambda z=z: builder.box((-length / 2, -0.1, z - 0.06),
                                                                     (length / 2, 1.5, z), MATTE))
    return builder


def material_heap(seed=3):
    builder = MeshBuilder()
    rng = random.Random(seed)
    for k in range(9):
        x, y = rng.uniform(-3.0, 3.0), rng.uniform(-2.0, 2.0)
        sx, sy, sz = rng.uniform(0.8, 1.8), rng.uniform(0.6, 1.0), rng.uniform(0.5, 0.9)
        material = (MARBLE, TRAV, BRICK)[k % 3]
        builder.box((x - sx / 2, y - sy / 2, 0.0), (x + sx / 2, y + sy / 2, sz), material,
                    matrix=Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "Z"))
    painted(builder, (0.72, 0.4, 0.28), lambda: builder.box((3.5, -1.0, 0.0), (5.5, 1.0, 1.1), BRICK))
    return builder


def wall_run(builder, x0, y0, x1, y1, height, thickness=2.0, material=BRICK, arches=0):
    length = math.hypot(x1 - x0, y1 - y0)
    angle = math.atan2(y1 - y0, x1 - x0)
    local = MeshBuilder()
    if arches:
        half = length / arches * 0.28
        openings = [(-length / 2 + length * (k + 0.5) / arches, half, min(height * 0.55, height - half - 1.0))
                    for k in range(arches)]
        arched_wall(local, -length / 2, length / 2, -thickness / 2, thickness / 2, 0.0, height, openings, material,
                    segments=5, foundation=3.0)
    else:
        local.box((-length / 2, -thickness / 2, -3.0), (length / 2, thickness / 2, height), material, bottom=False)
    builder.merge(local, Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, 0.0)) @ Matrix.Rotation(angle, 4, "Z"))
