import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .nimes_figures import beast, ellipsoid, tube
from .orders import gable_roof, ridge_cap, tile_roof
from .olympie_doric import (REGULA, SIMA_BLUE, SIMA_RED, STUCCO, TAENIA, TRIGLYPH, TYMPANUM, Peripteral, cella_box,
                            in_antis_building, painted)

OCHRE_WALL = (0.90, 0.70, 0.44)
RED_WALL = (0.70, 0.22, 0.14)
CREAM = (0.96, 0.92, 0.82)
POMPEIAN = (0.66, 0.16, 0.10)
YELLOW = (0.95, 0.78, 0.36)
GREEN_MARBLE = (0.46, 0.62, 0.48)
RED_MARBLE = (0.78, 0.40, 0.32)


def foundation(builder, x0, y0, x1, y1, top, material="limestone", depth=1.6):
    builder.box((x0, y0, top - depth), (x1, y1, top), material, bottom=False)


def stoa(length, depth, column_height, spacing, inner=True, wall_colour=OCHRE_WALL, roof="terracotta_tiles",
         steps=2, closed_ends=True, panels=None, back_wall=True, colonnade_key="stoa_doric", inner_key="stoa_inner"):
    builder = MeshBuilder()
    columns = []
    hl = length / 2
    hd = depth / 2
    step = 0.3
    for k in range(steps):
        grow = (steps - k) * 0.4
        builder.box((-hl - grow, -hd - grow * 0.2, -(k + 1) * step), (hl + grow, hd + grow, -k * step), "limestone",
                    bottom=False)
    foundation(builder, -hl - 1.0, -hd - 0.4, hl + 1.0, hd + 1.0, -steps * step, depth=1.4)
    builder.box((-hl, -hd, -0.02), (hl, hd, 0.0), "paving", bottom=False)
    wall = 0.7
    if back_wall:
        painted(builder, wall_colour, lambda: builder.box((-hl, -hd, 0.0), (hl, -hd + wall, column_height + 1.0),
                                                          "plaster", bottom=False))
        painted(builder, POMPEIAN, lambda: builder.box((-hl, -hd + wall, 0.0), (hl, -hd + wall + 0.02, 1.2),
                                                       "plaster", bottom=False))
        if panels:
            rng = random.Random(len(panels))
            count = int(length / 4.2)
            for k in range(count):
                x0 = -hl + 0.5 + k * length / count
                x1 = x0 + length / count - 1.0
                colour = panels[k % len(panels)]
                tone = rng.uniform(0.82, 1.0)
                painted(builder, tuple(c * tone for c in colour), lambda x0=x0, x1=x1: builder.box(
                    (x0, -hd + wall, 1.6), (x1, -hd + wall + 0.025, column_height - 0.6), "plaster", bottom=False))
    if closed_ends:
        for x0, x1 in ((-hl, -hl + wall), (hl - wall, hl)):
            painted(builder, wall_colour, lambda x0=x0, x1=x1: builder.box((x0, -hd, 0.0), (x1, hd - 1.2,
                                                                                            column_height + 1.0),
                                                                           "plaster", bottom=False))
    count = int(round(length / spacing))
    real = length / count
    front_y = hd - 0.55
    for k in range(count + 1):
        columns.append((colonnade_key, -hl + 0.5 + k * (length - 1.0) / count, front_y, 0.0))
    if inner:
        inner_count = max(int(count / 2), 1)
        for k in range(inner_count):
            columns.append((inner_key, -hl + (k + 0.5) * length / inner_count, (front_y + (-hd + wall)) / 2, 0.0))
    top = column_height
    arch = 0.62
    painted(builder, STUCCO, lambda: builder.box((-hl - 0.1, front_y - 0.42, top), (hl + 0.1, front_y + 0.42,
                                                                                     top + arch), "plaster"))
    painted(builder, TAENIA, lambda: builder.box((-hl - 0.12, front_y + 0.4, top + arch - 0.08),
                                                 (hl + 0.12, front_y + 0.46, top + arch), "plaster"))
    frieze = 0.6
    painted(builder, STUCCO, lambda: builder.box((-hl - 0.1, front_y - 0.42, top + arch), (hl + 0.1, front_y + 0.4,
                                                                                            top + arch + frieze),
                                                 "plaster"))
    tri = 0.36
    slots = int(round(length / (real / 2)))
    for k in range(slots + 1):
        x = -hl + 0.5 + k * (length - 1.0) / slots
        painted(builder, TRIGLYPH, lambda x=x: builder.box((x - tri / 2, front_y + 0.4, top + arch),
                                                           (x + tri / 2, front_y + 0.47, top + arch + frieze - 0.03),
                                                           "plaster"))
    g = top + arch + frieze
    painted(builder, STUCCO, lambda: builder.box((-hl - 0.4, -hd - 0.4, g), (hl + 0.4, front_y + 0.9, g + 0.3),
                                                 "plaster"))
    painted(builder, SIMA_RED, lambda: builder.box((-hl - 0.42, front_y + 0.8, g + 0.12), (hl + 0.42,
                                                                                            front_y + 0.95, g + 0.34),
                                                   "plaster"))
    painted(builder, (0.22, 0.30, 0.52), lambda: builder.box((-hl, -hd + wall, g - 0.05), (hl, front_y - 0.4, g),
                                                             "plaster", bottom=True))
    rise = depth * 0.22
    ridge_y = (-hd - 0.4 + front_y + 0.9) / 2
    half = (front_y + 0.9 - (-hd - 0.4)) / 2
    for side in (-1, 1):
        tile_roof(builder, Vector((-hl - 0.4, ridge_y, g + 0.3 + rise)), Vector((hl + 0.4, ridge_y, g + 0.3 + rise)),
                  Vector((0.0, side * half, -rise)), roof, 0.55, True)
    ridge_cap(builder, (-hl - 0.4, ridge_y, g + 0.36 + rise), (hl + 0.4, ridge_y, g + 0.36 + rise), 0.15, roof)
    for x, sign in ((-hl - 0.38, -1), (hl + 0.38, 1)):
        tri_face = [(x, ridge_y - half, g + 0.3), (x, ridge_y + half, g + 0.3), (x, ridge_y, g + 0.3 + rise)]
        builder.oriented(tri_face, (sign, 0, 0), "plaster")
        builder.tint(len(builder.polygons) - 1, TYMPANUM)
    return builder, columns


def heraion():
    temple = Peripteral(50.01, 18.76, 6, 16, 1.25, 5.22, 1.1, 1.0, 0.45, 2, 0.4, 2.7, material="plaster",
                        roof="terracotta_tiles", tile_pitch=0.62, stone="limestone")
    builder = MeshBuilder()
    temple.krepis(builder, 1.2)
    eave_x, eave_y = temple.entablature(builder)
    apex = temple.pediments(builder, eave_x, eave_y, (0.62, 0.16, 0.10))
    temple.roof_cover(builder, eave_x, eave_y)
    naos_x = 20.5
    naos_y = 5.4
    painted(builder, (0.70, 0.66, 0.58), lambda: builder.box((-naos_x, -naos_y, 0.0), (naos_x, naos_y, 1.0),
                                                             "limestone", bottom=False))
    cella_box(builder, -naos_x, naos_x, naos_y, 0.9, temple.column_height + 1.1, "plaster", OCHRE_WALL,
              door={1: (2.6, 4.2)})
    painted(builder, RED_WALL, lambda: builder.box((-naos_x - 0.03, -naos_y - 0.03, 1.0),
                                                   (naos_x + 0.03, naos_y + 0.03, 1.25), "plaster", bottom=False))
    z0 = temple.frieze_top - 0.25
    inner_x = temple.half_x - 0.5
    inner_y = temple.half_y - 0.5
    for x0, x1, y0, y1 in ((naos_x, inner_x, -inner_y, inner_y), (-inner_x, -naos_x, -inner_y, inner_y),
                           (-naos_x, naos_x, naos_y, inner_y), (-naos_x, naos_x, -inner_y, -naos_y)):
        painted(builder, (0.40, 0.24, 0.14), lambda x0=x0, x1=x1, y0=y0, y1=y1: builder.box(
            (x0, y0, z0), (x1, y1, temple.frieze_top), "matte"))
    disk_centre = Vector((eave_x - 0.2, 0.0, apex + 1.25))
    for k, (radius, colour) in enumerate(((1.15, (0.12, 0.10, 0.09)), (0.95, (0.86, 0.22, 0.12)),
                                          (0.7, (0.96, 0.90, 0.76)), (0.45, (0.12, 0.10, 0.09)),
                                          (0.22, (0.86, 0.22, 0.12)))):
        frame = Matrix.Translation(disk_centre + Vector((0.02 * k, 0.0, 0.0))) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        first = len(builder.polygons)
        builder.lathe([(0.0, -0.08), (radius, -0.08), (radius, 0.08), (0.0, 0.08)], 20, "matte", matrix=frame)
        builder.tint(first, colour)
    columns = []
    rng = random.Random(7)
    for x, y in temple.column_positions():
        key = "heraion_a" if rng.random() < 0.55 else "heraion_b"
        columns.append((key, x, y, 0.0))
    columns.append(("heraion_oak", -naos_x - 1.3, 2.0, 0.0))
    columns.append(("heraion_b", -naos_x - 1.3, -2.0, 0.0))
    columns.append(("heraion_b", naos_x + 1.3, 2.0, 0.0))
    columns.append(("heraion_b", naos_x + 1.3, -2.0, 0.0))
    return builder, columns, temple


def metroon():
    temple = Peripteral(20.67, 10.62, 6, 11, 0.86, 4.7, 0.7, 0.66, 0.3, 2, 0.32, 1.6, material="plaster",
                        roof="terracotta_tiles", tile_pitch=0.5)
    builder = MeshBuilder()
    temple.krepis(builder, 1.0)
    eave_x, eave_y = temple.entablature(builder)
    temple.pediments(builder, eave_x, eave_y)
    temple.roof_cover(builder, eave_x, eave_y)
    cella_box(builder, -6.5, 6.5, 2.9, 0.6, temple.column_height + 0.6, "plaster", CREAM, door={1: (1.8, 3.4)})
    columns = [("metroon", x, y, 0.0) for x, y in temple.column_positions()]
    return builder, columns, temple


TREASURIES = [("sicyon", 7.4, 12.8, (0.18, 0.34, 0.66)), ("syracuse", 10.8, 12.0, (0.66, 0.18, 0.12)),
              ("epidamnos", 6.6, 9.0, (0.20, 0.48, 0.40)), ("byzantium", 6.2, 8.0, (0.62, 0.16, 0.30)),
              ("sybaris", 7.0, 9.4, (0.86, 0.60, 0.20)), ("cyrene", 7.2, 10.0, (0.22, 0.30, 0.62)),
              ("selinous", 7.6, 11.0, (0.72, 0.22, 0.12)), ("metapontum", 8.6, 12.5, (0.16, 0.40, 0.58)),
              ("megara", 6.6, 13.0, (0.70, 0.30, 0.14)), ("gela", 11.0, 13.2, (0.20, 0.36, 0.62))]


def treasury_row(x0, x1):
    builder = MeshBuilder()
    columns = []
    total = sum(width for _, width, _, _ in TREASURIES)
    gap = (x1 - x0 - total) / (len(TREASURIES) - 1)
    x = x0
    for index, (name, width, depth, colour) in enumerate(TREASURIES):
        centre = x + width / 2
        column_height = 3.4 + width * 0.12
        diameter = 0.5 + width * 0.03
        built, positions, _ = in_antis_building(width, depth, column_height, diameter, pediment_colour=colour,
                                                sima=SIMA_RED if index % 2 else (0.92, 0.66, 0.22),
                                                acroterion=(0.92, 0.62, 0.20) if index % 3 == 0 else None,
                                                wall_material="marble" if name in ("megara", "sicyon") else "plaster")
        frame = Matrix.Translation((centre, depth / 2 + 0.6, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
        builder.merge(built, frame)
        scale = diameter / 0.7
        for px, py in positions:
            world = frame @ Vector((px, py, 0.0))
            columns.append(("treasury", world.x, world.y, 0.0, scale, column_height / 4.4))
        x += width + gap
    builder.box((x0 - 6.0, -1.0, -3.6), (x1 + 6.0, 0.6, 0.0), "limestone", bottom=False)
    for k in range(int((x1 - x0 + 12.0) / 3.0)):
        sx = x0 - 6.0 + k * 3.0
        painted(builder, (0.82, 0.78, 0.70), lambda sx=sx: builder.box((sx, -1.02, -3.6), (sx + 0.04, -0.98, 0.0),
                                                                        "limestone"))
    for k in range(9):
        z = -3.6 + k * 0.4
        y = -1.0 - (9 - k) * 0.45
        builder.box((x0 + 30.0, y, -3.6), (x0 + 48.0, y + 0.45, z + 0.4), "limestone", bottom=False)
    return builder, columns


def philippeion():
    builder = MeshBuilder()
    radius = 15.24 / 2
    for k in range(3):
        r = radius - k * 0.45
        builder.lathe([(0.0, -1.2 + k * 0.38), (r, -1.2 + k * 0.38), (r, -1.2 + (k + 1) * 0.38),
                       (0.0, -1.2 + (k + 1) * 0.38)], 36, "limestone", smooth=False)
    builder.lathe([(0.0, -2.4), (radius + 0.4, -2.4), (radius + 0.4, -1.2), (0.0, -1.2)], 24, "limestone")
    builder.lathe([(0.0, -0.06), (radius - 1.3, -0.06), (radius - 1.3, 0.0), (0.0, 0.0)], 36, "paving")
    cella_r = 4.6
    height = 6.3
    first = len(builder.polygons)
    builder.lathe([(cella_r, 0.0), (cella_r, height + 0.6)], 32, "plaster", smooth=True, caps=False)
    builder.lathe([(cella_r - 0.6, height + 0.6), (cella_r - 0.6, 0.0)], 32, "plaster", smooth=True, caps=False)
    builder.tint(first, CREAM)
    for k in range(9):
        angle = 2 * math.pi * (k + 0.5) / 9
        if abs(math.cos(angle - 0.0)) > 0.93:
            continue
        p = Vector((math.cos(angle) * (cella_r + 0.01), math.sin(angle) * (cella_r + 0.01), 2.6))
        frame = Matrix.Translation(p) @ Matrix.Rotation(angle + math.pi / 2, 4, "Z")
        painted(builder, (0.10, 0.08, 0.07), lambda frame=frame: builder.box((-0.45, -0.02, 0.0), (0.45, 0.02, 1.9),
                                                                              MATTE, matrix=frame))
    door = Matrix.Translation((cella_r + 0.01, 0.0, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, "Z")
    painted(builder, (0.10, 0.08, 0.07), lambda: builder.box((-1.1, -0.03, 0.0), (1.1, 0.03, 4.2), MATTE,
                                                             matrix=door))
    ring_r = radius - 1.35
    top = height
    first = len(builder.polygons)
    builder.lathe([(ring_r - 0.5, top), (ring_r + 0.42, top), (ring_r + 0.42, top + 0.55), (ring_r + 0.5, top + 0.62),
                   (ring_r + 0.5, top + 1.05), (ring_r + 0.75, top + 1.2), (ring_r + 0.75, top + 1.4),
                   (ring_r - 0.5, top + 1.4)], 36, "marble", smooth=False)
    builder.tint(first, (0.98, 0.96, 0.92))
    painted(builder, SIMA_BLUE, lambda: builder.lathe([(ring_r + 0.43, top + 0.62), (ring_r + 0.43, top + 0.9)], 36,
                                                      "marble", caps=False))
    painted(builder, TAENIA, lambda: builder.lathe([(ring_r + 0.76, top + 1.22), (ring_r + 0.76, top + 1.34)], 36,
                                                   "marble", caps=False))
    roof = []
    for k in range(5):
        t = k / 4
        roof.append((ring_r + 0.8 - (ring_r + 0.6) * t, top + 1.4 + 2.6 * t))
    builder.lathe(roof, 36, "terracotta_tiles", smooth=False, caps=False)
    builder.lathe([(0.0, top + 3.9), (0.45, top + 4.05), (0.52, top + 4.4), (0.3, top + 4.8), (0.0, top + 4.9)], 12,
                  "bronze_gilt", smooth=True)
    columns = []
    for k in range(18):
        angle = 2 * math.pi * k / 18
        columns.append(("philippeion", math.cos(angle) * ring_r, math.sin(angle) * ring_r, 0.0, angle))
    return builder, columns


def crypt(length=32.0, width=3.7, height=4.45):
    builder = MeshBuilder()
    wall = 0.9
    hw = width / 2
    spring = height - hw
    segments = 10
    for side in (-1, 1):
        painted(builder, (0.82, 0.76, 0.64), lambda side=side: builder.box(
            (0.0, min(side * hw, side * (hw + wall)), -0.6), (length, max(side * hw, side * (hw + wall)), spring),
            "limestone", bottom=False))
    inner = []
    outer = []
    for k in range(segments + 1):
        a = math.pi * k / segments
        inner.append((math.cos(a) * hw, spring + math.sin(a) * hw))
        outer.append((math.cos(a) * (hw + wall), spring + math.sin(a) * (hw + wall)))
    for (y0, z0), (y1, z1) in zip(inner[:-1], inner[1:]):
        builder.oriented([(0.0, y0, z0), (length, y0, z0), (length, y1, z1), (0.0, y1, z1)], (0, -y0 - y1, -1),
                         "limestone")
    for (y0, z0), (y1, z1) in zip(outer[:-1], outer[1:]):
        builder.oriented([(0.0, y0, z0), (length, y0, z0), (length, y1, z1), (0.0, y1, z1)], (0, y0 + y1, 1),
                         "limestone")
    for x, sign in ((0.0, -1), (length, 1)):
        for (a, b), (c, d) in zip(zip(inner[:-1], inner[1:]), zip(outer[:-1], outer[1:])):
            builder.oriented([(x, a[0], a[1]), (x, b[0], b[1]), (x, d[0], d[1]), (x, c[0], c[1])], (sign, 0, 0),
                             "limestone")
    for x in (0.0, length - 1.2):
        painted(builder, (0.96, 0.94, 0.88), lambda x=x: builder.box((x, -hw - wall - 0.4, -0.6),
                                                                     (x + 1.2, -hw - wall, height + wall + 0.3),
                                                                     "marble", bottom=False))
        painted(builder, (0.96, 0.94, 0.88), lambda x=x: builder.box((x, hw + wall, -0.6),
                                                                     (x + 1.2, hw + wall + 0.4, height + wall + 0.3),
                                                                     "marble", bottom=False))
    painted(builder, (0.96, 0.94, 0.88), lambda: builder.box((-0.3, -hw - wall - 0.5, height + wall - 0.1),
                                                             (0.9, hw + wall + 0.5, height + wall + 0.8), "marble"))
    builder.box((0.0, -hw, -0.02), (length, hw, 0.0), "paving", bottom=False)
    return builder


def stadium_fittings(arena):
    x0, x1, y0, y1 = arena
    builder = MeshBuilder()
    for y in (y0, y1):
        builder.box((x0 - 1.0, y - 0.25, -0.6), (x1 + 1.0, y + 0.25, 0.12), "limestone", bottom=False)
        builder.box((x0 - 1.0, y + (0.25 if y == y0 else -0.75), -0.6),
                    (x1 + 1.0, y + (0.75 if y == y0 else -0.25), -0.25), "limestone", bottom=False)
    for x in (x0, x1):
        builder.box((x - 0.25, y0, -0.6), (x + 0.25, y1, 0.12), "limestone", bottom=False)
    for k in range(int((x1 - x0) / 32.0) + 1):
        x = x0 + k * 32.0
        for y in (y0 - 1.2, y1 + 1.2):
            builder.box((x - 0.5, y - 0.5, -0.6), (x + 0.5, y + 0.5, 0.1), "limestone", bottom=False)
            painted(builder, (0.18, 0.30, 0.34), lambda x=x, y=y: builder.box((x - 0.36, y - 0.36, 0.06),
                                                                             (x + 0.36, y + 0.36, 0.08), MATTE))
    for x in (x0 + 10.1, x0 + 10.1 + 192.27):
        builder.box((x - 0.25, y0 + 1.0, -0.05), (x + 0.25, y1 - 1.0, 0.06), "marble", bottom=False)
        for k in range(21):
            y = y0 + 1.6 + k * (y1 - y0 - 3.2) / 20
            builder.box((x - 0.08, y - 0.08, 0.0), (x + 0.08, y + 0.08, 1.1), "limestone", bottom=False)
    return builder


def judges_seat(width=14.0, depth=6.0):
    builder = MeshBuilder()
    builder.box((-width / 2, -depth / 2, -1.0), (width / 2, depth / 2, 0.6), "limestone", bottom=False)
    for k in range(3):
        builder.box((-width / 2 + 0.6, -depth / 2 + 0.8 + k * 1.2, 0.6), (width / 2 - 0.6, -depth / 2 + 1.8 + k * 1.2,
                                                                          1.05 + k * 0.45), "marble", bottom=False)
    painted(builder, (0.86, 0.22, 0.14), lambda: builder.box((-width / 2, depth / 2 - 0.3, 0.6),
                                                             (width / 2, depth / 2, 2.6), "plaster", bottom=False))
    for x in (-width / 2, width / 2):
        builder.box((x - 0.2, -depth / 2, 0.6), (x + 0.2, depth / 2, 2.4), "limestone", bottom=False)
    for k in range(5):
        x = -width / 2 + 1.4 + k * (width - 2.8) / 4
        for y in (-depth / 2 + 0.5,):
            tube(builder, [(x, y, 0.6), (x, y, 3.6)], [0.06, 0.05], (0.5, 0.36, 0.22), 4)
    rows = []
    for t in (0.0, 1.0):
        row = []
        for k in range(9):
            x = -width / 2 + width * k / 8
            row.append((x, -depth / 2 + 0.5 + t * (depth - 0.6), 3.6 - 0.25 * t - 0.15 * math.sin(math.pi * k / 8)))
        rows.append(row)
    for k in range(8):
        quad = [rows[0][k], rows[0][k + 1], rows[1][k + 1], rows[1][k]]
        builder.oriented(quad, (0, 0, 1), MATTE)
        builder.tint(len(builder.polygons) - 1, (0.52, 0.10, 0.30) if k % 2 else (0.96, 0.92, 0.84))
        builder.oriented(list(reversed(quad)), (0, 0, -1), MATTE)
        builder.tint(len(builder.polygons) - 1, (0.42, 0.08, 0.24) if k % 2 else (0.80, 0.76, 0.70))
    return builder


def demeter_altar():
    builder = MeshBuilder()
    builder.box((-1.9, -1.2, -0.8), (1.9, 1.2, 0.3), "marble", bottom=False)
    builder.box((-1.5, -0.9, 0.3), (1.5, 0.9, 1.3), "marble", bottom=False)
    builder.box((-1.65, -1.05, 1.3), (1.65, 1.05, 1.5), "marble")
    for x in (-1.45, 1.45):
        first = len(builder.polygons)
        builder.lathe([(0.0, 1.5), (0.18, 1.5), (0.22, 1.62), (0.18, 1.75), (0.0, 1.78)], 8, "marble",
                      smooth=True, matrix=Matrix.Translation((x, 0.0, 0.0)))
        builder.tint(first, (0.96, 0.94, 0.9))
    painted(builder, (0.30, 0.46, 0.22), lambda: builder.box((-1.52, -0.92, 0.95), (1.52, 0.92, 1.1), "marble"))
    return builder


def altis_wall(points, height=2.4, thickness=0.8, gates=()):
    builder = MeshBuilder()
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        a = Vector((ax, ay))
        b = Vector((bx, by))
        length = (b - a).length
        direction = (b - a) / length
        normal = Vector((-direction.y, direction.x))
        cuts = sorted([((Vector(g) - a).dot(direction), w) for g, w in gates
                       if 0 <= (Vector(g) - a).dot(direction) <= length and abs((Vector(g) - a).dot(normal)) < 3.0])
        spans = []
        start = 0.0
        for centre, width in cuts:
            spans.append((start, centre - width / 2))
            start = centre + width / 2
        spans.append((start, length))
        for s0, s1 in spans:
            if s1 - s0 < 0.3:
                continue
            frame = Matrix(((direction.x, normal.x, 0.0, a.x), (direction.y, normal.y, 0.0, a.y), (0.0, 0.0, 1.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0)))
            builder.box((s0, -thickness / 2, -0.8), (s1, thickness / 2, height), "limestone", matrix=frame,
                        bottom=False)
            builder.box((s0 - 0.05, -thickness / 2 - 0.12, height), (s1 + 0.05, thickness / 2 + 0.12, height + 0.22),
                        "terracotta_tiles", matrix=frame)
        for centre, width in cuts:
            for s in (centre - width / 2 - 0.5, centre + width / 2 + 0.5):
                frame = Matrix(((direction.x, normal.x, 0.0, a.x), (direction.y, normal.y, 0.0, a.y),
                                (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                builder.box((s - 0.5, -thickness / 2 - 0.2, -0.8), (s + 0.5, thickness / 2 + 0.2, height + 1.4),
                            "limestone", matrix=frame, bottom=False)
            frame = Matrix(((direction.x, normal.x, 0.0, a.x), (direction.y, normal.y, 0.0, a.y), (0.0, 0.0, 1.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0)))
            painted(builder, STUCCO, lambda frame=frame, centre=centre, width=width: builder.box(
                (centre - width / 2 - 1.0, -thickness / 2 - 0.2, height + 1.4),
                (centre + width / 2 + 1.0, thickness / 2 + 0.2, height + 2.1), "plaster", matrix=frame))
    return builder


def pelopion():
    builder = MeshBuilder()
    outline = [(-16.0, -10.0), (12.0, -14.0), (18.0, 6.0), (2.0, 18.0), (-18.0, 10.0)]
    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        a = Vector((ax, ay))
        b = Vector((bx, by))
        direction = (b - a).normalized()
        normal = Vector((-direction.y, direction.x))
        frame = Matrix(((direction.x, normal.x, 0.0, a.x), (direction.y, normal.y, 0.0, a.y), (0.0, 0.0, 1.0, 0.0),
                        (0.0, 0.0, 0.0, 1.0)))
        length = (b - a).length
        if ax == -16.0:
            builder.box((0.0, -0.4, -0.6), (length * 0.4, 0.4, 1.3), "limestone", matrix=frame, bottom=False)
            builder.box((length * 0.4 + 5.0, -0.4, -0.6), (length, 0.4, 1.3), "limestone", matrix=frame, bottom=False)
            for s in (length * 0.4 + 0.5, length * 0.4 + 4.5):
                painted(builder, STUCCO, lambda s=s, frame=frame: builder.box((s - 0.45, -1.4, -0.4), (s + 0.45, 1.4, 4.2),
                                                                              "plaster", matrix=frame, bottom=False))
            painted(builder, STUCCO, lambda frame=frame: builder.box((length * 0.4 - 0.2, -1.6, 4.2),
                                                                     (length * 0.4 + 5.2, 1.6, 5.2), "plaster",
                                                                     matrix=frame))
            painted(builder, TRIGLYPH, lambda frame=frame: builder.box((length * 0.4 - 0.2, -1.66, 4.6),
                                                                       (length * 0.4 + 5.2, -1.6, 5.0), "plaster",
                                                                       matrix=frame))
        else:
            builder.box((0.0, -0.4, -0.6), (length, 0.4, 1.3), "limestone", matrix=frame, bottom=False)
    first = len(builder.polygons)
    builder.lathe([(0.0, 2.4), (5.0, 1.8), (9.0, 0.7), (12.0, 0.0)], 14, MATTE, smooth=True, caps=False,
                  matrix=Matrix.Translation((0.0, 2.0, 0.0)))
    builder.tint(first, (0.62, 0.58, 0.34))
    return builder


def great_altar():
    builder = MeshBuilder()
    first = len(builder.polygons)
    builder.lathe([(0.0, -0.8), (6.2, -0.8), (6.2, 1.2), (5.9, 1.4), (0.0, 1.4)], 28, "limestone", smooth=False,
                  matrix=Matrix.Diagonal((1.0, 0.55, 1.0, 1.0)).to_4x4())
    builder.tint(first, (0.92, 0.88, 0.80))
    first = len(builder.polygons)
    profile = [(1.0, 1.35), (1.0, 1.9), (0.94, 2.8), (0.86, 3.8), (0.74, 4.8), (0.6, 5.7), (0.42, 6.3), (0.0, 6.5)]
    builder.lathe([(r * 1.7 if r < 0.99 else 1.7, z) for r, z in profile], 24, MATTE, smooth=True,
                  matrix=Matrix.Diagonal((1.0, 1.4 / 1.7, 1.0, 1.0)).to_4x4(),
                  radius_scale=lambda angle: 1.0 + 0.05 * math.sin(5 * angle) + 0.03 * math.sin(11 * angle + 1.3))
    for index in range(first, len(builder.polygons)):
        points = [builder.positions[v] for v in builder.polygons[index]]
        height = sum(p[2] for p in points) / len(points)
        tone = 1.0 - 0.05 * math.sin(height * 1.9) - 0.03 * (height > 5.6)
        builder.polygon_colors[index] = (0.78 * tone, 0.76 * tone, 0.72 * tone)
    builder.lathe([(0.0, 6.47), (0.42, 6.47), (0.3, 6.56), (0.0, 6.6)], 10, "flame", smooth=True)
    for k in range(6):
        y = -3.6 - k * 0.42
        builder.box((-1.6, y - 0.42, -0.8), (1.6, y, 1.4 - (k + 1) * 0.22), "limestone", bottom=False)
    return builder


def building_block(width, depth, height, wall_colour=CREAM, material="plaster", roof="terracotta_tiles", court=None,
                   windows=0, door=True, pitch=0.3, foundation_depth=1.4):
    builder = MeshBuilder()
    hw = width / 2
    hd = depth / 2
    foundation(builder, -hw - 0.3, -hd - 0.3, hw + 0.3, hd + 0.3, 0.15, depth=foundation_depth)
    if court is None:
        painted(builder, wall_colour, lambda: builder.box((-hw, -hd, 0.0), (hw, hd, height), material, bottom=False))
        rise = min(width, depth) * pitch / 2
        if width >= depth:
            gable_roof(builder, -hw - 0.5, hw + 0.5, hd + 0.5, height, height + rise, roof, along_axis="x", pitch=0.55)
            for x, sign in ((-hw, -1), (hw, 1)):
                builder.oriented([(x, -hd - 0.5, height), (x, hd + 0.5, height), (x, 0.0, height + rise)], (sign, 0, 0),
                                 material)
                builder.tint(len(builder.polygons) - 1, wall_colour)
        else:
            gable_roof(builder, -hd - 0.5, hd + 0.5, hw + 0.5, height, height + rise, roof, along_axis="y", pitch=0.55)
            for y, sign in ((-hd, -1), (hd, 1)):
                builder.oriented([(-hw - 0.5, y, height), (hw + 0.5, y, height), (0.0, y, height + rise)], (0, sign, 0),
                                 material)
                builder.tint(len(builder.polygons) - 1, wall_colour)
    else:
        cw, cd = court
        wing_x = (width - cw) / 2
        wing_y = (depth - cd) / 2
        for x0, y0, x1, y1 in ((-hw, -hd, hw, -hd + wing_y), (-hw, hd - wing_y, hw, hd),
                               (-hw, -hd + wing_y, -hw + wing_x, hd - wing_y), (hw - wing_x, -hd + wing_y, hw,
                                                                                 hd - wing_y)):
            painted(builder, wall_colour, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, 0.0), (x1, y1, height),
                                                                                       material, bottom=False))
        rise_y = wing_y * pitch
        rise_x = wing_x * pitch
        for sign in (-1, 1):
            cy = sign * (hd - wing_y / 2)
            for side in (-1, 1):
                tile_roof(builder, Vector((-hw - 0.4, cy, height + rise_y)), Vector((hw + 0.4, cy, height + rise_y)),
                          Vector((0.0, side * (wing_y / 2 + 0.45), -rise_y)), roof, 0.55, True)
            cx = sign * (hw - wing_x / 2)
            for side in (-1, 1):
                tile_roof(builder, Vector((cx, -hd + wing_y - 0.4, height + rise_x)),
                          Vector((cx, hd - wing_y + 0.4, height + rise_x)),
                          Vector((side * (wing_x / 2 + 0.45), 0.0, -rise_x)), roof, 0.55, True)
            for x in (-hw - 0.4, hw + 0.4):
                builder.oriented([(x, cy - wing_y / 2 - 0.45, height), (x, cy + wing_y / 2 + 0.45, height),
                                  (x, cy, height + rise_y)], (1 if x > 0 else -1, 0, 0), material)
                builder.tint(len(builder.polygons) - 1, wall_colour)
    if windows:
        for side in (-1, 1):
            for k in range(windows):
                x = -hw + (k + 0.5) * width / windows
                painted(builder, (0.12, 0.09, 0.07), lambda x=x, side=side: builder.box(
                    (x - 0.4, side * hd - 0.02, height * 0.55), (x + 0.4, side * hd + 0.02, height * 0.55 + 1.1),
                    MATTE))
    if door:
        painted(builder, (0.30, 0.18, 0.10), lambda: builder.box((-1.1, -hd - 0.03, 0.0), (1.1, -hd + 0.03, 3.0),
                                                                 MATTE))
    return builder


def court_columns(width, depth, spacing, key, inset=1.5):
    columns = []
    hw = width / 2 - inset
    hd = depth / 2 - inset
    nx = max(int(round(2 * hw / spacing)), 1)
    ny = max(int(round(2 * hd / spacing)), 1)
    for k in range(nx + 1):
        x = -hw + 2 * hw * k / nx
        columns.append((key, x, -hd, 0.0))
        columns.append((key, x, hd, 0.0))
    for k in range(1, ny):
        y = -hd + 2 * hd * k / ny
        columns.append((key, -hw, y, 0.0))
        columns.append((key, hw, y, 0.0))
    return columns


def leonidaion():
    width = 80.0
    depth = 74.0
    court = (30.0, 28.0)
    builder = building_block(width - 6.0, depth - 6.0, 7.2, CREAM, court=court, door=False, pitch=0.32)
    builder.box((-width / 2, -depth / 2, -0.6), (width / 2, depth / 2, 0.15), "limestone", bottom=False)
    painted(builder, (0.98, 0.96, 0.92), lambda: builder.box((-width / 2 - 0.3, -depth / 2 - 0.3, 6.4),
                                                             (width / 2 + 0.3, depth / 2 + 0.3, 7.25), "plaster"))
    painted(builder, (0.20, 0.30, 0.56), lambda: builder.box((-width / 2 - 0.32, -depth / 2 - 0.32, 6.9),
                                                             (width / 2 + 0.32, depth / 2 + 0.32, 7.05), "plaster"))
    for x0, y0, x1, y1 in ((-width / 2, -depth / 2, width / 2, -depth / 2 + 3.0), (-width / 2, depth / 2 - 3.0, width / 2,
                                                                                    depth / 2),
                           (-width / 2, -depth / 2, -width / 2 + 3.0, depth / 2), (width / 2 - 3.0, -depth / 2, width / 2,
                                                                                   depth / 2)):
        painted(builder, (0.70, 0.36, 0.22), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, 7.25),
                                                                                         (x1, y1, 7.4),
                                                                                         "terracotta_tiles"))
    cw, cd = court
    builder.box((-cw / 2, -cd / 2, 0.15), (cw / 2, cd / 2, 0.2), "paving", bottom=False)
    garden = (0.36, 0.52, 0.22)
    painted(builder, garden, lambda: builder.box((-cw / 2 + 3.0, -cd / 2 + 3.0, 0.2), (cw / 2 - 3.0, cd / 2 - 3.0, 0.32),
                                                 MATTE))
    builder.box((-6.0, -5.0, 0.0), (6.0, 5.0, 0.36), "marble", bottom=False)
    painted(builder, (0.10, 0.36, 0.48), lambda: builder.box((-5.6, -4.6, 0.36), (5.6, 4.6, 0.37), "water"))
    builder.box((-1.8, -1.6, 0.0), (1.8, 1.6, 0.6), "marble", bottom=False)
    columns = []
    columns += court_columns(width, depth, 2.25, "ionic_outer", inset=0.8)
    columns += court_columns(cw + 4.0, cd + 4.0, 3.1, "stoa_plain", inset=0.6)
    return builder, columns


def nero_house():
    builder = MeshBuilder()
    width, depth = 54.0, 40.0
    built = building_block(width, depth, 6.4, (0.86, 0.36, 0.22), "brick", court=(24.0, 16.0), door=False, pitch=0.3)
    builder.merge(built)
    for x0, x1 in ((-width / 2 - 0.05, width / 2 + 0.05),):
        painted(builder, (0.96, 0.86, 0.66), lambda: builder.box((x0, -depth / 2 - 0.05, 0.0), (x1, depth / 2 + 0.05,
                                                                                                 1.2), "plaster",
                                                                 bottom=False))
    painted(builder, (0.40, 0.56, 0.24), lambda: builder.box((-10.0, -6.0, 0.15), (10.0, 6.0, 0.28), MATTE))
    builder.box((-4.0, -2.0, 0.0), (4.0, 2.0, 0.42), "marble", bottom=False)
    painted(builder, (0.1, 0.3, 0.4), lambda: builder.box((-3.7, -1.7, 0.42), (3.7, 1.7, 0.43), "water"))
    hall = building_block(16.0, 12.0, 9.0, (0.92, 0.66, 0.40), "plaster", windows=3, door=True)
    builder.merge(hall, Matrix.Translation((width / 2 + 6.0, -6.0, 0.0)))
    columns = court_columns(28.0, 20.0, 3.0, "brick_pier", inset=2.0)
    return builder, columns


def kladeos_baths():
    builder = MeshBuilder()
    rooms = [(-8.0, 0.0, 10.0, 14.0, 7.0), (2.5, 0.0, 9.0, 14.0, 7.5), (11.5, 0.0, 8.0, 12.0, 8.0)]
    for cx, cy, w, d, h in rooms:
        built = MeshBuilder()
        built.box((-w / 2, -d / 2, -1.2), (w / 2, d / 2, h), "brick", bottom=False)
        segments = 8
        hd = d / 2
        rows = []
        for t in (0.0, 1.0):
            row = []
            for k in range(segments + 1):
                a = math.pi * k / segments
                row.append((-w / 2 - 0.3 + t * (w + 0.6), math.cos(a) * (hd + 0.2), h + math.sin(a) * hd * 0.45))
            rows.append(row)
        built.surface(rows, "terracotta_tiles", facing=(0, 0, 1))
        for x, sign in ((-w / 2 - 0.3, -1), (w / 2 + 0.3, 1)):
            ring = [(x, math.cos(math.pi * k / segments) * (hd + 0.2), h + math.sin(math.pi * k / segments) * hd * 0.45)
                    for k in range(segments + 1)]
            built.oriented(ring, (sign, 0, 0), "brick")
        for k in range(3):
            x = -w / 2 + (k + 0.5) * w / 3
            painted(built, (0.10, 0.08, 0.07), lambda x=x, built=built, d=d, h=h: built.box(
                (x - 0.6, -d / 2 - 0.03, h * 0.55), (x + 0.6, -d / 2 + 0.03, h * 0.85), MATTE))
        builder.merge(built, Matrix.Translation((cx, cy, 0.0)))
    builder.lathe([(4.0, 0.0), (4.0, 8.0), (0.0, 8.6)], 10, "brick", start=-math.pi / 2, sweep=math.pi, caps=False,
                  matrix=Matrix.Translation((15.5, 0.0, 0.0)))
    builder.box((-15.0, -12.0, 0.0), (-3.0, -7.0, 0.25), "paving", bottom=False)
    builder.box((-12.0, -11.5, 0.25), (-4.0, -7.5, 0.6), "marble", bottom=False)
    painted(builder, (0.1, 0.3, 0.4), lambda: builder.box((-11.6, -11.1, 0.5), (-4.4, -7.9, 0.52), "water"))
    return builder


def nymphaeum():
    builder = MeshBuilder()
    radius = 16.62 / 2
    height = 11.0
    segments = 22
    marble = (0.98, 0.96, 0.92)
    first = len(builder.polygons)
    builder.lathe([(radius + 1.2, -1.0), (radius + 1.2, height)], segments, "brick", start=0.0, sweep=math.pi,
                  caps=False)
    builder.lathe([(radius, height), (radius, -1.0)], segments, "marble", start=0.0, sweep=math.pi, caps=False)
    builder.tint(first + segments, marble)
    for k in range(segments):
        a0 = math.pi * k / segments
        a1 = math.pi * (k + 1) / segments
        builder.oriented([(math.cos(a0) * radius, math.sin(a0) * radius, height),
                          (math.cos(a1) * radius, math.sin(a1) * radius, height),
                          (math.cos(a1) * (radius + 1.2), math.sin(a1) * (radius + 1.2), height),
                          (math.cos(a0) * (radius + 1.2), math.sin(a0) * (radius + 1.2), height)], (0, 0, 1), "marble")
    for storey, z in enumerate((1.6, 6.2)):
        painted(builder, (0.90, 0.88, 0.84), lambda z=z: builder.lathe([(radius - 0.05, z - 0.3),
                                                                         (radius - 0.35, z - 0.15),
                                                                         (radius - 0.35, z), (radius - 0.05, z)],
                                                                        segments, "marble", start=0.0, sweep=math.pi,
                                                                        caps=False))
        for k in range(11):
            angle = math.pi * (k + 0.5) / 11
            centre = Vector((math.cos(angle) * (radius - 0.02), math.sin(angle) * (radius - 0.02), z))
            frame = Matrix.Translation(centre) @ Matrix.Rotation(angle + math.pi / 2, 4, "Z")
            colour = GREEN_MARBLE if (k + storey) % 2 else RED_MARBLE
            painted(builder, colour, lambda frame=frame: builder.box((-0.95, -0.03, 0.0), (0.95, 0.03, 3.7), "marble",
                                                                     matrix=frame))
            painted(builder, (0.16, 0.14, 0.13), lambda frame=frame: builder.box((-0.6, -0.04, 0.2), (0.6, 0.04, 3.4),
                                                                                 "marble", matrix=frame))
    painted(builder, (0.9, 0.86, 0.80), lambda: builder.lathe([(radius - 0.05, height), (radius - 0.6, height + 0.4),
                                                                (radius + 1.25, height + 0.4),
                                                                (radius + 1.25, height)], segments, "marble",
                                                               start=0.0, sweep=math.pi, caps=False))
    upper = MeshBuilder()
    upper.lathe([(0.0, 0.0), (radius - 0.3, 0.0), (radius - 0.3, 1.0), (radius - 0.8, 1.0), (radius - 0.8, 0.4),
                 (0.0, 0.4)], segments, "marble", start=math.pi, sweep=math.pi, caps=False)
    builder.merge(upper, Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Diagonal((1.0, -1.0, 1.0, 1.0)).to_4x4())
    builder.lathe([(0.0, 0.9), (radius - 0.8, 0.9)], segments, "water", start=0.0, sweep=math.pi, caps=False)
    builder.box((-radius - 1.2, -0.4, -1.0), (radius + 1.2, 0.0, 1.0), "marble", bottom=False)
    lower_length = 21.9
    builder.box((-lower_length / 2, -4.6, -0.8), (lower_length / 2, -0.4, 0.0), "marble", bottom=False)
    for x0, x1, y0, y1 in ((-lower_length / 2, lower_length / 2, -4.6, -4.2), (-lower_length / 2, lower_length / 2,
                                                                                -0.8, -0.4),
                           (-lower_length / 2, -lower_length / 2 + 0.4, -4.6, -0.4),
                           (lower_length / 2 - 0.4, lower_length / 2, -4.6, -0.4)):
        builder.box((x0, y0, 0.0), (x1, y1, 0.9), "marble", bottom=False)
    builder.box((-lower_length / 2 + 0.4, -4.2, 0.6), (lower_length / 2 - 0.4, -0.8, 0.6), "water")
    for x in (-lower_length / 2 - 2.0, lower_length / 2 + 2.0):
        first = len(builder.polygons)
        builder.lathe([(0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (0.0, 0.5)], 12, "marble",
                      matrix=Matrix.Translation((x, -2.5, 0.0)))
        for k in range(8):
            angle = 2 * math.pi * k / 8
            tube(builder, [(x + math.cos(angle) * 1.6, -2.5 + math.sin(angle) * 1.6, 0.5),
                           (x + math.cos(angle) * 1.6, -2.5 + math.sin(angle) * 1.6, 4.2)], [0.14, 0.12],
                 (0.98, 0.96, 0.92), 6, "marble")
        builder.lathe([(0.0, 4.2), (2.0, 4.2), (2.0, 4.6), (1.2, 5.3), (0.0, 5.6)], 12, "marble",
                      matrix=Matrix.Translation((x, -2.5, 0.0)))
        builder.tint(first, (0.98, 0.96, 0.92))
    bull = beast("ox")
    bull.materials = ["marble" if name == MATTE else name for name in bull.materials]
    bull.polygon_colors = [(0.98, 0.96, 0.92)] * len(bull.polygon_colors)
    builder.box((-1.4, -0.9, 0.0), (1.4, 0.9, 1.4), "marble", bottom=False)
    builder.merge(bull, Matrix.Translation((0.0, 0.0, 1.4)) @ Matrix.Rotation(math.pi / 2, 4, "Z")
                  @ Matrix.Scale(1.2, 4))
    niches = []
    for storey, z in enumerate((1.6, 6.2)):
        for k in range(11):
            angle = math.pi * (k + 0.5) / 11
            niches.append((math.cos(angle) * (radius - 0.5), math.sin(angle) * (radius - 0.5), z + 0.25,
                           angle + math.pi))
    return builder, niches


def bouleuterion():
    builder = MeshBuilder()
    for cy in (-14.0, 14.0):
        hall = MeshBuilder()
        length = 30.0
        width = 13.8
        hw = width / 2
        painted(hall, CREAM, lambda: hall.box((-length / 2, -hw, -1.0), (length / 2 - hw, hw, 7.5), "plaster",
                                              bottom=False))
        first = len(hall.polygons)
        hall.lathe([(hw, -1.0), (hw, 7.5)], 10, "plaster", start=math.pi / 2, sweep=math.pi, caps=False,
                   matrix=Matrix.Translation((-length / 2, 0.0, 0.0)))
        hall.tint(first, CREAM)
        gable_roof(hall, -length / 2, length / 2 - hw + 0.4, hw + 0.4, 7.5, 9.8, "terracotta_tiles", along_axis="x",
                   pitch=0.55)
        hall.oriented([(length / 2 - hw + 0.4, -hw - 0.4, 7.5), (length / 2 - hw + 0.4, hw + 0.4, 7.5),
                       (length / 2 - hw + 0.4, 0.0, 9.8)], (1, 0, 0), "plaster")
        hall.tint(len(hall.polygons) - 1, TYMPANUM)
        cone = []
        for k in range(4):
            t = k / 3
            cone.append(((hw + 0.4) * (1 - t) + 0.01, 7.5 + 2.3 * t))
        hall.lathe(cone, 10, "terracotta_tiles", start=math.pi / 2, sweep=math.pi, caps=False,
                   matrix=Matrix.Translation((-length / 2, 0.0, 0.0)))
        builder.merge(hall, Matrix.Translation((0.0, cy, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"))
    square = building_block(14.0, 14.0, 6.0, CREAM, door=False)
    builder.merge(square)
    portico, columns = stoa(44.0, 5.0, 5.0, 2.6, inner=False, closed_ends=False, back_wall=False,
                            colonnade_key="ionic_small")
    builder.merge(portico, Matrix.Translation((-17.5, 0.0, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    moved = []
    frame = Matrix.Translation((-17.5, 0.0, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
    for key, x, y, z in columns:
        p = frame @ Vector((x, y, z))
        moved.append((key, p.x, p.y, p.z))
    return builder, moved


def workshop():
    return building_block(14.5, 32.0, 13.5, CREAM, windows=0, door=True, pitch=0.28)


def prytaneion():
    return building_block(32.0, 32.0, 6.5, OCHRE_WALL, court=(14.0, 14.0), door=False)


def palaestra(size=66.0):
    builder = building_block(size, size, 6.4, CREAM, court=(size - 14.0, size - 14.0), door=False, pitch=0.3)
    painted(builder, (0.88, 0.76, 0.52), lambda: builder.box((-size / 2 + 7.2, -size / 2 + 7.2, 0.15),
                                                             (size / 2 - 7.2, size / 2 - 7.2, 0.18), MATTE))
    columns = court_columns(size - 14.0, size - 14.0, 2.9, "stoa_plain", inset=0.6)
    return builder, columns


def aqueduct_channel(points, height=0.9, width=1.1):
    builder = MeshBuilder()
    for (ax, ay, az), (bx, by, bz) in zip(points[:-1], points[1:]):
        a = Vector((ax, ay, az))
        b = Vector((bx, by, bz))
        direction = (b - a).normalized()
        flat = Vector((direction.x, direction.y, 0.0)).normalized()
        side = Vector((-flat.y, flat.x, 0.0))
        corners = [a - side * width / 2, b - side * width / 2, b + side * width / 2, a + side * width / 2]
        top = [c + Vector((0.0, 0.0, height)) for c in corners]
        bottom = [c - Vector((0.0, 0.0, 1.0)) for c in corners]
        builder.oriented(top, (0, 0, 1), "limestone")
        builder.oriented([bottom[0], bottom[1], top[1], top[0]], -side, "limestone")
        builder.oriented([bottom[3], bottom[2], top[2], top[3]], side, "limestone")
    return builder
