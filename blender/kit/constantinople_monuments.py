import math
import random

from mathutils import Matrix, Vector

from .arles_details import darker
from .arles_life import ellipsoid as body_part
from .arles_life import tube as limb
from .constantinople_sophia import (TAU, WARM_WHITE, annulus, box, colonnade, cross, facing_quad, grid_surface,
                                    revolve_band, shell, tinted, window)
from .geometry import MeshBuilder, placement
from .nimes_figures import Look, person, tube
from .orders import column

BRONZE_TONE = (0.86, 0.62, 0.34)
GILT_TONE = (1.0, 0.82, 0.48)
PURPLE = (0.42, 0.10, 0.26)
TRACK_HALF = 39.0
CAVEA_OUTER = 63.0
HIPPO_HALF_LENGTH = 225.0
SPHENDONE_Y = HIPPO_HALF_LENGTH - TRACK_HALF
SEAT_ROWS = 28
SEAT_RISE = 0.42
SEAT_DEPTH = 0.75
WALKWAY_ROW = 14
WALKWAY = 1.2
WALKWAY_STEP = 1.6
PODIUM = 3.2
SEAT_TONES = [(0.84, 0.80, 0.72), (0.78, 0.74, 0.66)]
SEAT_WEAR = (0.6, 0.56, 0.5)
RISER_TONE = (0.72, 0.69, 0.64)
FACTION_CLOTHS = [(0.14, 0.30, 0.66), (0.16, 0.50, 0.26), (0.92, 0.9, 0.84), (0.74, 0.16, 0.12)]
SPINA_BASINS = [(-127.0, -114.0), (-86.0, -66.0), (-25.0, 1.0), (64.0, 86.0)]


def row_offset(row):
    return row * SEAT_DEPTH + (WALKWAY if row >= WALKWAY_ROW else 0.0)


def row_z(row):
    return PODIUM + row * SEAT_RISE + (WALKWAY_STEP if row >= WALKWAY_ROW else 0.0)


CAVEA_TOP = row_z(SEAT_ROWS - 1) + SEAT_RISE
CAVEA_BACK = TRACK_HALF + 1.2 + row_offset(SEAT_ROWS - 1) + SEAT_DEPTH


def cavea_steps():
    steps = []
    for row in range(SEAT_ROWS):
        if row == WALKWAY_ROW:
            steps.append((row_offset(row) - WALKWAY, row_offset(row), PODIUM + row * SEAT_RISE, None))
        steps.append((row_offset(row), row_offset(row) + SEAT_DEPTH, row_z(row), row))
    return steps


def bronzed(builder, tone=BRONZE_TONE, material="bronze_gilt"):
    builder.materials = [material]
    builder.polygon_materials = [0] * len(builder.polygons)
    builder.polygon_colors = [tone] * len(builder.polygons)
    return builder


def statue_person(look, tone=BRONZE_TONE):
    return bronzed(person(look), tone)


def pedestal(builder, width, height, material="marble_white", colour=WARM_WHITE):
    w = width / 2
    box(builder, (-w - 0.2, -w - 0.2, -1.0), (w + 0.2, w + 0.2, 0.35), material, colour)
    box(builder, (-w, -w, 0.35), (w, w, height - 0.3), material, colour)
    box(builder, (-w - 0.15, -w - 0.15, height - 0.3), (w + 0.15, w + 0.15, height), material, colour)


def spiral_tube(builder, centre_radius, tube_radius, pitch, height, phase, colour, turns_detail=10):
    points = []
    radii = []
    steps = int(height / pitch * turns_detail)
    for k in range(steps + 1):
        z = height * k / steps
        a = phase + TAU * z / pitch
        taper = 1.0 - 0.25 * (z / height)
        points.append((centre_radius * math.cos(a), centre_radius * math.sin(a), z))
        radii.append(tube_radius * taper)
    tube(builder, points, radii, colour, 7, "bronze")


def serpent_column():
    builder = MeshBuilder()
    pedestal(builder, 2.2, 1.6)
    tone = (0.52, 0.42, 0.28)
    height = 6.2
    for k in range(3):
        spiral_tube(builder, 0.24, 0.2, 1.05, height, TAU * k / 3, tone)
    for k in range(3):
        a = TAU * k / 3 + 0.4
        neck0 = Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 1.6 + height))
        neck1 = Vector((0.75 * math.cos(a), 0.75 * math.sin(a), 1.6 + height + 0.9))
        head = Vector((1.05 * math.cos(a), 1.05 * math.sin(a), 1.6 + height + 1.05))
        tube(builder, [neck0, neck1, head], [0.17, 0.15, 0.14], tone, 7, "bronze")
        direction = (head - neck1).normalized()
        frame = Matrix.Translation(head + direction * 0.25) @ direction.to_track_quat("Y", "Z").to_matrix().to_4x4()
        first = len(builder.polygons)
        builder.lathe([(0.0, -0.3), (0.2, -0.2), (0.22, 0.05), (0.14, 0.3), (0.0, 0.42)], 8, "bronze", smooth=True,
                      matrix=frame @ Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Diagonal((1.0, 0.7, 1.0, 1.0)))
        builder.tint(first, tone)
    for x in (-1.3, 1.3):
        first = len(builder.polygons)
        builder.box((x - 0.05, -1.3, 0.0), (x + 0.05, 1.3, 1.0), "bronze", bottom=False)
        builder.tint(first, (0.3, 0.24, 0.18))
    return builder


def obelisk_theodosius():
    builder = MeshBuilder()
    box(builder, (-3.0, -3.0, -1.0), (3.0, 3.0, 0.5), "marble_white", WARM_WHITE)
    box(builder, (-2.6, -2.6, 0.5), (2.6, 2.6, 1.0), "marble_white", WARM_WHITE)
    box(builder, (-2.1, -2.1, 1.0), (2.1, 2.1, 3.9), "marble_white", (0.96, 0.93, 0.88))
    for side in range(4):
        angle = side * math.pi / 2
        outward = Vector((math.cos(angle), math.sin(angle), 0.0))
        right = Vector((-outward.y, outward.x, 0.0))
        for row, z in enumerate((1.25, 2.25)):
            for k in range(7):
                x = -1.6 + k * 0.53
                centre = outward * 2.11 + right * x + Vector((0, 0, z))
                first = len(builder.polygons)
                builder.lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.5), (0.1, 0.62), (0.0, 0.65)], 5, "marble_white",
                              matrix=Matrix.Translation(centre) @ Matrix.Diagonal((1.0, 1.0, 1.0, 1.0)))
                builder.tint(first, (0.84, 0.8, 0.74))
        top_panel = [outward * 2.12 + right * -1.8 + Vector((0, 0, 3.2)), outward * 2.12 + right * 1.8 + Vector((0, 0, 3.2)),
                     outward * 2.12 + right * 1.8 + Vector((0, 0, 3.75)), outward * 2.12 + right * -1.8 + Vector((0, 0, 3.75))]
        facing_quad(builder, top_panel, outward, "marble_white", colour=(0.82, 0.78, 0.72))
    box(builder, (-2.3, -2.3, 3.9), (2.3, 2.3, 4.3), "marble_white", WARM_WHITE)
    for x in (-1.2, 1.2):
        for y in (-1.2, 1.2):
            first = len(builder.polygons)
            builder.box((x - 0.32, y - 0.32, 4.3), (x + 0.32, y + 0.32, 4.9), "bronze_gilt", bottom=False)
            builder.tint(first, BRONZE_TONE)
    shaft = 18.6
    z0 = 4.9
    b0, b1 = 1.2, 0.85
    outline0 = [(-b0, -b0), (b0, -b0), (b0, b0), (-b0, b0)]
    outline1 = [(-b1, -b1), (b1, -b1), (b1, b1), (-b1, b1)]
    for i in range(4):
        j = (i + 1) % 4
        quad = [(outline0[i][0], outline0[i][1], z0), (outline0[j][0], outline0[j][1], z0),
                (outline1[j][0], outline1[j][1], z0 + shaft), (outline1[i][0], outline1[i][1], z0 + shaft)]
        normal = Vector((outline0[i][0] + outline0[j][0], outline0[i][1] + outline0[j][1], 0.0))
        facing_quad(builder, quad, normal, "granite_rose", colour=(1.0, 0.86, 0.82))
    apex = (0.0, 0.0, z0 + shaft + 1.5)
    for i in range(4):
        j = (i + 1) % 4
        tri = [(outline1[i][0], outline1[i][1], z0 + shaft), (outline1[j][0], outline1[j][1], z0 + shaft), apex]
        normal = Vector((outline1[i][0] + outline1[j][0], outline1[i][1] + outline1[j][1], 0.6))
        facing_quad(builder, tri, normal, "granite_rose", colour=(1.0, 0.86, 0.82))
    return builder


def walled_obelisk():
    builder = MeshBuilder()
    box(builder, (-2.6, -2.6, -1.0), (2.6, 2.6, 2.4), "col_travertine", (0.95, 0.9, 0.82))
    height = 29.0
    b0, b1 = 2.0, 1.15
    outline0 = [(-b0, -b0), (b0, -b0), (b0, b0), (-b0, b0)]
    outline1 = [(-b1, -b1), (b1, -b1), (b1, b1), (-b1, b1)]
    z0 = 2.4
    for i in range(4):
        j = (i + 1) % 4
        quad = [(outline0[i][0], outline0[i][1], z0), (outline0[j][0], outline0[j][1], z0),
                (outline1[j][0], outline1[j][1], z0 + height), (outline1[i][0], outline1[i][1], z0 + height)]
        normal = Vector((outline0[i][0] + outline0[j][0], outline0[i][1] + outline0[j][1], 0.0))
        facing_quad(builder, quad, normal, "col_travertine", colour=(0.92, 0.86, 0.76))
    apex = (0.0, 0.0, z0 + height + 1.8)
    for i in range(4):
        j = (i + 1) % 4
        tri = [(outline1[i][0], outline1[i][1], z0 + height), (outline1[j][0], outline1[j][1], z0 + height), apex]
        normal = Vector((outline1[i][0] + outline1[j][0], outline1[i][1] + outline1[j][1], 0.6))
        facing_quad(builder, tri, normal, "col_travertine", colour=(0.9, 0.84, 0.74))
    return builder


def meta():
    builder = MeshBuilder()
    box(builder, (-3.5, -2.0, -0.5), (3.5, 2.0, 2.2), "marble_white", WARM_WHITE)
    for x in (-2.2, 0.0, 2.2):
        first = len(builder.polygons)
        builder.lathe([(0.8, 2.2), (0.7, 3.0), (0.0, 7.2)], 10, "bronze_gilt", smooth=True,
                      matrix=Matrix.Translation((x, 0.0, 0.0)))
        builder.tint(first, GILT_TONE)
        builder.lathe([(0.0, 7.1), (0.25, 7.3), (0.0, 7.6)], 6, "bronze_gilt", matrix=Matrix.Translation((x, 0.0, 0.0)))
    return builder


def charioteer_statue(seed):
    builder = MeshBuilder()
    pedestal(builder, 1.4, 2.4)
    look = Look("white", hem=0.55, skin=0, hair=1, belt="dark", arms="gesture", seed=seed)
    builder.merge(statue_person(look), placement(0.0, 0.0, 2.4, 0.0, 1.15))
    return builder


def bronze_horse_statue(seed):
    builder = MeshBuilder()
    pedestal(builder, 2.2, 2.0)
    builder.merge(bronzed(horse((0.5, 0.4, 0.3), seed)), placement(0.0, 0.0, 2.0, math.pi / 2, 1.4))
    return builder


def spina(builder, length_back, length_front, avoid=()):
    width = 7.0
    deck = (0.82, 0.78, 0.7)
    y = length_back
    for y0, y1 in SPINA_BASINS + [(length_front, length_front)]:
        if y0 > y:
            box(builder, (-width / 2, y, -0.6), (width / 2, y0, 1.3), "marble_white", deck)
        if y1 > y0:
            box(builder, (-width / 2, y0, -0.6), (width / 2, y1, 0.7), "marble_white", deck)
            for x0, x1 in ((-width / 2, -width / 2 + 0.5), (width / 2 - 0.5, width / 2)):
                box(builder, (x0, y0, 0.7), (x1, y1, 1.3), "marble_white", deck)
            facing_quad(builder, [(-width / 2 + 0.5, y0, 1.05), (width / 2 - 0.5, y0, 1.05), (width / 2 - 0.5, y1, 1.05),
                                  (-width / 2 + 0.5, y1, 1.05)], (0, 0, 1), "pool")
        y = max(y, y1)
    for y in range(int(length_back) + 10, int(length_front) - 6, 16):
        if any(y0 - 1.0 < y < y1 + 1.0 for y0, y1 in SPINA_BASINS) or any(abs(y - other) < 5.5 for other in avoid):
            continue
        for x in (-2.4, 2.4):
            box(builder, (x - 0.4, y - 0.4, 1.3), (x + 0.4, y + 0.4, 2.0), "marble_white", WARM_WHITE)
            tinted(builder, BRONZE_TONE, lambda x=x, y=y: builder.lathe(
                [(0.2, 2.0), (0.17, 4.6), (0.26, 4.75), (0.26, 4.9), (0.0, 4.9)], 8, "bronze_gilt", smooth=True,
                matrix=Matrix.Translation((x, y, 0.0))))
            tinted(builder, GILT_TONE, lambda x=x, y=y: builder.lathe(
                [(0.0, 4.9), (0.2, 5.05), (0.0, 5.3)], 6, "bronze_gilt", smooth=True, matrix=Matrix.Translation((x, y, 0.0))))


def hippodrome(ground_depth):
    builder = MeshBuilder()
    y_back = -HIPPO_HALF_LENGTH + 18.0
    y_curve = SPHENDONE_Y
    for side in (1, -1):
        x_track = side * TRACK_HALF
        x0, x1 = sorted((x_track, x_track + side * 1.2))
        box(builder, (x0, y_back, -3.0), (x1, y_curve, PODIUM), "marble_white", WARM_WHITE)
        steps = cavea_steps()
        for index, (o0, o1, z, row) in enumerate(steps):
            z_next = steps[index + 1][2] if index + 1 < len(steps) else CAVEA_TOP
            x_a = x_track + side * (1.2 + o0)
            x_w = x_track + side * (1.2 + o0 + (0.14 if row is not None else 0.0))
            x_b = x_track + side * (1.2 + o1)
            tone = SEAT_TONES[row % 2] if row is not None else (0.7, 0.66, 0.6)
            if row is not None:
                facing_quad(builder, [(x_a, y_back, z), (x_w, y_back, z), (x_w, y_curve, z), (x_a, y_curve, z)], (0, 0, 1),
                            "marble_white", colour=SEAT_WEAR)
            facing_quad(builder, [(x_w, y_back, z), (x_b, y_back, z), (x_b, y_curve, z), (x_w, y_curve, z)], (0, 0, 1),
                        "marble_white", colour=tone)
            facing_quad(builder, [(x_b, y_back, z), (x_b, y_curve, z), (x_b, y_curve, z_next),
                                  (x_b, y_back, z_next)], (-side, 0, 0), "marble_white", colour=RISER_TONE)
        top = CAVEA_TOP
        x_back = x_track + side * (CAVEA_BACK - TRACK_HALF)
        for k, y in enumerate(range(int(y_back) + 8, int(y_curve) - 6, 12)):
            cloth = FACTION_CLOTHS[(k + (side > 0) * 2) % len(FACTION_CLOTHS)]
            facing_quad(builder, [(x_track - side * 0.03, y - 2.0, 1.1), (x_track - side * 0.03, y + 2.0, 1.1),
                                  (x_track - side * 0.03, y + 2.0, 3.0), (x_track - side * 0.03, y - 2.0, 3.0)], (-side, 0, 0),
                        "matte", colour=cloth)
            facing_quad(builder, [(x_track - side * 0.035, y - 2.0, 2.8), (x_track - side * 0.035, y + 2.0, 2.8),
                                  (x_track - side * 0.035, y + 2.0, 3.0), (x_track - side * 0.035, y - 2.0, 3.0)],
                        (-side, 0, 0), "matte", colour=GILT_TONE)
        xa, xb = sorted((x_back, side * CAVEA_OUTER))
        facing_quad(builder, [(xa, y_back, top), (xb, y_back, top), (xb, y_curve, top), (xa, y_curve, top)],
                    (0, 0, 1), "marble_white", colour=(0.86, 0.84, 0.8))
        wx0, wx1 = sorted((side * CAVEA_OUTER, side * (CAVEA_OUTER + 2.0)))
        box(builder, (wx0, y_back, -ground_depth), (wx1, y_curve, top + 6.5), "banded")
        rows = [[(side * (CAVEA_OUTER - 4.0), y_back, top + 4.6), (side * (CAVEA_OUTER - 4.0), y_curve, top + 4.6)],
                [(side * (CAVEA_OUTER + 2.4), y_back, top + 6.6), (side * (CAVEA_OUTER + 2.4), y_curve, top + 6.6)]]
        grid_surface(builder, rows, "terracotta_tiles", lambda p, s=side: Vector((s * 0.5, 0, 1)), False)
        colonnade(builder, (side * (CAVEA_OUTER - 4.0), y_back), (side * (CAVEA_OUTER - 4.0), y_curve), 40, 4.4, 0.4,
                  top, WARM_WHITE)
        for k in range(46):
            y = y_back + 4.0 + k * (y_curve - y_back - 8.0) / 45
            for z, h in ((0.5, 5.4), (top - 3.6, 3.8)):
                window(builder, (side * (CAVEA_OUTER + 2.0), y, z), (0, -side, 0), (side, 0, 0), 2.6, h, 2.0, lit=False)
    segments = 18
    top = CAVEA_TOP
    for k in range(segments):
        a0 = math.pi * k / segments
        a1 = math.pi * (k + 1) / segments

        def at(r, a):
            return Vector((-r * math.cos(a), y_curve + r * math.sin(a)))
        steps = cavea_steps()
        for index, (o0, o1, z, row) in enumerate(steps):
            z_next = steps[index + 1][2] if index + 1 < len(steps) else CAVEA_TOP
            r_a = TRACK_HALF + 1.2 + o0
            r_w = r_a + (0.14 if row is not None else 0.0)
            r_b = TRACK_HALF + 1.2 + o1
            p0, p1, w0, w1, q0, q1 = at(r_a, a0), at(r_a, a1), at(r_w, a0), at(r_w, a1), at(r_b, a0), at(r_b, a1)
            tone = SEAT_TONES[row % 2] if row is not None else (0.7, 0.66, 0.6)
            if row is not None:
                facing_quad(builder, [(p0.x, p0.y, z), (p1.x, p1.y, z), (w1.x, w1.y, z), (w0.x, w0.y, z)], (0, 0, 1),
                            "marble_white", colour=SEAT_WEAR)
            facing_quad(builder, [(w0.x, w0.y, z), (w1.x, w1.y, z), (q1.x, q1.y, z), (q0.x, q0.y, z)], (0, 0, 1),
                        "marble_white", colour=tone)
            facing_quad(builder, [(q0.x, q0.y, z), (q1.x, q1.y, z), (q1.x, q1.y, z_next), (q0.x, q0.y, z_next)],
                        Vector((0, y_curve, 0)) - Vector(((q0.x + q1.x) / 2, (q0.y + q1.y) / 2, 0)), "marble_white",
                        colour=RISER_TONE)
        p0, p1 = at(TRACK_HALF, a0), at(TRACK_HALF, a1)
        q0, q1 = at(TRACK_HALF + 1.2, a0), at(TRACK_HALF + 1.2, a1)
        centre = Vector((0, y_curve))
        for a, b, hint in ((p0, p1, -1), (q0, q1, 1)):
            mid = (a + b) / 2
            facing_quad(builder, [(a.x, a.y, -3.0), (b.x, b.y, -3.0), (b.x, b.y, PODIUM), (a.x, a.y, PODIUM)],
                        (mid - centre).to_3d() * hint, "marble_white", colour=WARM_WHITE)
        facing_quad(builder, [(p0.x, p0.y, PODIUM), (p1.x, p1.y, PODIUM), (q1.x, q1.y, PODIUM), (q0.x, q0.y, PODIUM)],
                    (0, 0, 1), "marble_white")
        r_back = CAVEA_BACK
        b0, b1 = at(r_back, a0), at(r_back, a1)
        o0, o1 = at(CAVEA_OUTER, a0), at(CAVEA_OUTER, a1)
        facing_quad(builder, [(b0.x, b0.y, top), (b1.x, b1.y, top), (o1.x, o1.y, top), (o0.x, o0.y, top)], (0, 0, 1),
                    "marble_white", colour=(0.86, 0.84, 0.8))
        w0, w1 = at(CAVEA_OUTER + 2.0, a0), at(CAVEA_OUTER + 2.0, a1)
        mid = (w0 + w1) / 2
        outward = (mid - centre).normalized().to_3d()
        facing_quad(builder, [(w0.x, w0.y, -ground_depth), (w1.x, w1.y, -ground_depth), (w1.x, w1.y, top + 6.5),
                              (w0.x, w0.y, top + 6.5)], outward, "banded")
        facing_quad(builder, [(o0.x, o0.y, top), (o1.x, o1.y, top), (o1.x, o1.y, top + 6.5), (o0.x, o0.y, top + 6.5)],
                    -outward, "banded")
        facing_quad(builder, [(o0.x, o0.y, top + 6.5), (o1.x, o1.y, top + 6.5), (w1.x, w1.y, top + 6.5),
                              (w0.x, w0.y, top + 6.5)], (0, 0, 1), "terracotta_tiles")
        right = (w1 - w0).normalized().to_3d()
        levels = [(top - 3.6, 3.8), (0.5, 5.4)]
        depth = 0.0
        while depth > -ground_depth + 7.0:
            depth -= 7.5
            levels.append((depth, 6.0))
        for z, h in levels:
            window(builder, (mid.x, mid.y, z), right, outward, 3.2, h, 2.0, lit=False)
    carceres(builder, y_back)
    return builder


def carceres(builder, y):
    depth = 16.0
    box(builder, (-CAVEA_OUTER - 2.0, y - depth, -3.0), (CAVEA_OUTER + 2.0, y, 13.0), "banded")
    facing_quad(builder, [(-CAVEA_OUTER - 2.6, y - depth - 0.6, 13.0), (CAVEA_OUTER + 2.6, y - depth - 0.6, 13.0),
                          (CAVEA_OUTER + 2.6, y + 0.6, 13.0), (-CAVEA_OUTER - 2.6, y + 0.6, 13.0)], (0, 0, 1), "lead")
    for k in range(12):
        x = -TRACK_HALF + 3.5 + k * (2 * TRACK_HALF - 7.0) / 11
        window(builder, (x, y, 0.0), (-1, 0, 0), (0, 1, 0), 4.6, 6.2, depth, lit=False)
        tinted(builder, (0.5, 0.36, 0.22), lambda x=x: builder.box((x - 2.2, y + 0.02, 0.0), (x + 2.2, y + 0.12, 3.2),
                                                                   "matte", bottom=False))
    for x in (-TRACK_HALF - 6.0, TRACK_HALF + 6.0):
        box(builder, (x - 6.0, y - depth - 2.0, -3.0), (x + 6.0, y + 2.0, 19.0), "banded")
        facing_quad(builder, [(x - 6.4, y - depth - 2.4, 19.0), (x + 6.4, y - depth - 2.4, 19.0), (x + 6.4, y + 2.4, 19.0),
                              (x - 6.4, y + 2.4, 19.0)], (0, 0, 1), "lead")
    for k in range(10):
        x = -TRACK_HALF + 3.0 + k * (2 * TRACK_HALF - 6.0) / 9
        window(builder, (x, y, 8.0), (-1, 0, 0), (0, 1, 0), 2.2, 3.6, depth, lit=False)
    for x in (-TRACK_HALF, TRACK_HALF):
        first = len(builder.polygons)
        builder.lathe([(0.5, 13.0), (0.5, 14.0)], 8, "marble_white", matrix=Matrix.Translation((x * 0.5, y, 0.0)))
        builder.tint(first, WARM_WHITE)


def kathisma():
    builder = MeshBuilder()
    width, depth, height = 34.0, 16.0, 17.0
    box(builder, (-depth, -width / 2, -4.0), (0.0, width / 2, height), "plaster", (1.0, 0.92, 0.82))
    facing_quad(builder, [(-depth - 0.6, -width / 2 - 0.6, height), (0.6, -width / 2 - 0.6, height), (0.6, width / 2 + 0.6, height),
                          (-depth - 0.6, width / 2 + 0.6, height)], (0, 0, 1), "lead")
    box(builder, (0.0, -10.0, 9.0), (4.5, 10.0, 9.8), "marble_white", WARM_WHITE, bottom=True)
    for k in range(6):
        y = -9.0 + k * 3.6
        first = len(builder.polygons)
        builder.lathe([(0.3, 9.8), (0.26, 15.0), (0.4, 15.4)], 10, "porphyry", matrix=Matrix.Translation((3.9, y, 0.0)))
        builder.tint(first, (1.0, 1.0, 1.0))
    rows = [[(-0.5, -10.6, 15.4), (-0.5, 10.6, 15.4)], [(5.0, -10.6, 14.6), (5.0, 10.6, 14.6)]]
    grid_surface(builder, rows, "bronze_tiles", lambda p: Vector((0.4, 0, 1)), False)
    for k in range(10):
        y = -9.0 + k * 2.0
        facing_quad(builder, [(4.52, y - 0.8, 9.8), (4.52, y + 0.8, 9.8), (4.52, y + 0.8, 11.0), (4.52, y - 0.8, 11.0)],
                    (1, 0, 0), "marble_white", colour=WARM_WHITE)
    for y0, y1, colour in ((-10.0, -3.4, PURPLE), (-3.2, 3.2, (0.58, 0.12, 0.3)), (3.4, 10.0, PURPLE)):
        facing_quad(builder, [(4.6, y0, 7.0), (4.6, y1, 7.0), (4.6, y1, 9.6), (4.6, y0, 9.6)], (1, 0, 0), "matte",
                    colour=colour)
        facing_quad(builder, [(4.62, y0 + 1.0, 7.2), (4.62, y1 - 1.0, 7.2), (4.62, y1 - 1.0, 7.5), (4.62, y0 + 1.0, 7.5)],
                    (1, 0, 0), "matte", colour=GILT_TONE)
    for k in range(5):
        y = -12.0 + k * 6.0
        window(builder, (0.0, y, 3.0), (0, 1, 0), (1, 0, 0), 2.0, 4.2, 2.0, lit=False)
    box(builder, (-depth - 60.0, -4.0, -4.0), (-depth, 4.0, 11.0), "plaster", (1.0, 0.92, 0.82))
    facing_quad(builder, [(-depth - 60.0, -4.5, 11.0), (-depth, -4.5, 11.0), (-depth, 4.5, 11.0), (-depth - 60.0, 4.5, 11.0)],
                (0, 0, 1), "lead")
    for k in range(12):
        x = -depth - 3.0 - k * 4.8
        for side in (1, -1):
            window(builder, (x, side * 4.0, 7.0), (side, 0, 0), (0, side, 0), 1.4, 2.6, 1.6, lit=False)
    return builder


def augusteon_portico(length, depth=6.5, height=7.0, column_count=None, roof_colour=None):
    builder = MeshBuilder()
    count = column_count or max(int(length / 4.2), 2)
    box(builder, (0.0, depth - 1.0, -2.0), (length, depth, height + 0.6), "plaster", (1.0, 0.88, 0.7))
    colonnade(builder, (0.0, 0.0), (length, 0.0), count, height - 0.8, 0.62, 0.25, WARM_WHITE)
    box(builder, (0.0, -0.45, height - 0.55), (length, 0.45, height), "marble_white", WARM_WHITE, bottom=True)
    rows = [[(-0.3, -0.9, height), (length + 0.3, -0.9, height)], [(-0.3, depth + 0.4, height + 1.8),
                                                                   (length + 0.3, depth + 0.4, height + 1.8)]]
    grid_surface(builder, rows, "terracotta_tiles", lambda p: Vector((0, -0.5, 1)), False)
    rows = [[(-0.3, -0.9, height - 0.05), (length + 0.3, -0.9, height - 0.05)],
            [(-0.3, depth + 0.4, height + 1.75), (length + 0.3, depth + 0.4, height + 1.75)]]
    grid_surface(builder, rows, "plaster", lambda p: Vector((0, 0.5, -1)), False, WARM_WHITE)
    tinted(builder, (0.9, 0.86, 0.8), lambda: builder.box((0.0, -0.5, -0.6), (length, depth - 1.0, 0.16), "marble_paving"))
    for k in range(int(length / 6.0)):
        x = 3.0 + k * 6.0
        tinted(builder, (0.5, 0.36, 0.24), lambda x=x: builder.box((x - 1.0, depth - 1.04, 0.0), (x + 1.0, depth - 1.0, 3.0),
                                                                   "matte", bottom=False))
    return builder


def senate():
    builder = MeshBuilder()
    width, depth, height = 34.0, 36.0, 17.0
    box(builder, (0.0, -width / 2, -3.0), (depth, width / 2, height), "plaster", (1.0, 0.9, 0.74))
    for y in (-width / 2, width / 2):
        for k in range(6):
            x = 4.0 + k * 5.6
            window(builder, (x, y, 7.0), (1 if y > 0 else -1, 0, 0), (0, 1 if y > 0 else -1, 0), 1.8, 4.2, 2.0, lit=False)
    rows = [[(-0.5, -width / 2 - 0.6, height), (depth + 0.5, -width / 2 - 0.6, height)],
            [(-0.5, 0.0, height + 5.5), (depth + 0.5, 0.0, height + 5.5)],
            [(-0.5, width / 2 + 0.6, height), (depth + 0.5, width / 2 + 0.6, height)]]
    grid_surface(builder, rows, "terracotta_tiles", lambda p: Vector((0, p.y * 0.3, 1)), False)
    for x in (0.0, depth):
        sign = -1 if x == 0.0 else 1
        facing_quad(builder, [(x, -width / 2 - 0.6, height), (x, width / 2 + 0.6, height), (x, 0.0, height + 5.5)],
                    (sign, 0, 0), "marble_white", colour=WARM_WHITE)
    porch = 8.5
    box(builder, (-porch - 1.0, -14.0, -1.6), (0.0, 14.0, 0.6), "marble_white", WARM_WHITE)
    for k in range(4):
        box(builder, (-porch - 1.0 - (k + 1) * 0.45, -14.0, -1.6), (-porch - 1.0 - k * 0.45, 14.0, 0.6 - (k + 1) * 0.45),
            "marble_white", WARM_WHITE)
    template = column("corinthian", 1.25, 12.5, "medium", "marble_white")
    for k in range(6):
        y = -11.0 + k * 4.4
        first = len(builder.polygons)
        builder.merge(template, Matrix.Translation((-porch, y, 0.6)))
        builder.tint(first, (0.98, 0.96, 0.92))
    box(builder, (-porch - 0.9, -12.6, 13.1), (0.2, 12.6, 14.9), "marble_white", WARM_WHITE, bottom=True)
    facing_quad(builder, [(-porch - 0.9, -12.6, 14.9), (-porch - 0.9, 12.6, 14.9), (-porch - 0.9, 0.0, 19.2)],
                (-1, 0, 0), "marble_white", colour=WARM_WHITE)
    for side in (1, -1):
        facing_quad(builder, [(-porch - 1.2, side * 12.9, 14.6), (0.4, side * 12.9, 14.6), (0.4, 0.0, 19.4),
                              (-porch - 1.2, 0.0, 19.4)], (0, side, 1.2), "terracotta_tiles")
    facing_quad(builder, [(-porch - 0.85, -6.5, 15.4), (-porch - 0.85, 6.5, 15.4), (-porch - 0.85, 0.0, 17.8)], (-1, 0, 0),
                "marble_white", colour=(0.7, 0.66, 0.6))
    tinted(builder, (0.56, 0.4, 0.22), lambda: builder.box((-0.06, -2.4, 0.6), (0.02, 2.4, 7.6), "bronze", bottom=False))
    for k in range(9):
        y = -12.0 + k * 3.0
        spec = Look("white", hem=0.03, skin=0, hair=k % 3, toga="white" if k % 2 else None, cloak=None if k % 2 else "white",
                    arms="gesture" if k % 3 == 0 else "toga" if k % 2 else "down", seed=200 + k)
        builder.merge(statue_person(spec, (0.98, 0.95, 0.9) if k % 3 else GILT_TONE), placement(-porch - 0.3, y, 19.4 - abs(y) * 0.36,
                                                                                            -math.pi / 2, 1.3))
    return builder


def milion():
    builder = MeshBuilder()
    w = 7.3
    pier = 2.4
    height = 9.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * w, sx * (w - pier)))
            y0, y1 = sorted((sy * w, sy * (w - pier)))
            box(builder, (x0, y0, -1.5), (x1, y1, height), "marble_white", WARM_WHITE)
    span = w - pier
    for axis in ("x", "y"):
        for side in (-1, 1):
            rows_outer = []
            rows_inner = []
            for k in range(13):
                a = math.pi * k / 12
                s = span * math.cos(a)
                z = height - span * 0.9 + span * 0.9 * math.sin(a) + 1.0
                if axis == "x":
                    rows_outer.append((s, side * w, z))
                    rows_inner.append((s, side * (w - pier), z))
                else:
                    rows_outer.append((side * w, s, z))
                    rows_inner.append((side * (w - pier), s, z))
            grid_surface(builder, [rows_outer, rows_inner], "marble_white", lambda p: Vector((0, 0, -1)), False, WARM_WHITE)
            top_z = height + 3.2
            face = rows_outer
            outward = Vector((0, side, 0)) if axis == "x" else Vector((side, 0, 0))
            for (a, b) in zip(face[:-1], face[1:]):
                a, b = Vector(a), Vector(b)
                top_a = a.copy()
                top_a.z = top_z
                top_b = b.copy()
                top_b.z = top_z
                facing_quad(builder, [a, b, top_b, top_a], outward, "marble_white", colour=WARM_WHITE)
    box(builder, (-w - 0.3, -w - 0.3, height + 3.2), (w + 0.3, w + 0.3, height + 4.0), "marble_white", WARM_WHITE, bottom=True)
    shell(builder, (0.0, 0.0, height + 4.0), 5.6, 0.0, TAU, 0.0, math.pi / 2, 16, 5, "lead", False)
    for x, scale, tone, look in ((-2.6, 1.6, GILT_TONE, Look("white", hem=0.03, skin=0, hair=0, cloak="purple", arms="gesture", seed=301)),
                                 (2.6, 1.5, GILT_TONE, Look("white", hem=0.03, skin=0, hair=1, palla="purple", veil=True,
                                                             female=True, arms="down", sleeves="long", seed=302))):
        builder.merge(statue_person(look, tone), placement(-(w - 1.0), x, height + 4.0, math.pi / 2, scale))
    cross(builder, (-(w - 1.0), 0.0, height + 4.0), 4.6)
    box(builder, (-0.9, w - 0.6, 0.0), (0.9, w + 0.4, 2.2), "marble_white", WARM_WHITE)
    return builder


def chalke():
    builder = MeshBuilder()
    w = 11.0
    height = 14.0
    box(builder, (-w, -w, -2.0), (w, w, height), "marble_white", (0.98, 0.95, 0.9))
    for side in (1, -1):
        for axis in ("x", "y"):
            for k in (-1, 1):
                pos = (k * 5.0, side * w, 4.0) if axis == "x" else (side * w, k * 5.0, 4.0)
                right = (side, 0, 0) if axis == "x" else (0, -side, 0)
                outward = (0, side, 0) if axis == "x" else (side, 0, 0)
                window(builder, pos, right, outward, 2.2, 5.6, 2.0, lit=False)
    tinted(builder, (0.6, 0.42, 0.22), lambda: builder.box((-2.4, w + 0.0, 0.0), (2.4, w + 0.1, 7.4), "bronze_gilt",
                                                          bottom=False))
    window(builder, (0.0, w, 7.6), (1, 0, 0), (0, 1, 0), 4.8, 2.6, 2.0, lit=False)
    revolve_band(builder, (0, 0, 0), 8.6, height, height + 3.0, 0.0, TAU, 20, "marble_white", True, WARM_WHITE)
    annulus(builder, (0, 0, 0), 8.6, w + 0.3, height, 0.0, TAU, 20, "bronze_tiles", True)
    shell(builder, (0.0, 0.0, height + 3.0), 8.8, 0.0, TAU, 0.0, math.pi / 2, 20, 6, "bronze_tiles", False)
    cross(builder, (0.0, 0.0, height + 11.6), 2.0)
    return builder


def justinian_column():
    builder = MeshBuilder()
    for k in range(7):
        w = 5.4 - k * 0.38
        box(builder, (-w, -w, -2.0 if k == 0 else k * 0.85), (w, w, k * 0.85 + 0.85), "marble_white",
            (0.96, 0.93, 0.88))
    base_top = 7 * 0.85
    box(builder, (-2.6, -2.6, base_top), (2.6, 2.6, base_top + 4.2), "marble_white", (0.96, 0.93, 0.88))
    box(builder, (-2.9, -2.9, base_top + 4.2), (2.9, 2.9, base_top + 4.8), "marble_white", WARM_WHITE)
    z0 = base_top + 4.8
    shaft = 28.0
    first = len(builder.polygons)
    builder.lathe([(2.0, z0), (2.0, z0 + 0.5), (1.85, z0 + 0.7), (1.7, z0 + shaft * 0.5), (1.55, z0 + shaft)], 20,
                  "bronze_tiles", smooth=True)
    builder.tint(first, (0.72, 0.52, 0.30))
    spiral = []
    radii = []
    steps = 160
    for k in range(steps + 1):
        t = k / steps
        z = z0 + 1.2 + t * (shaft - 2.0)
        r = 2.0 - 0.45 * (z - z0) / shaft + 0.04
        a = t * TAU * 7.0
        spiral.append((r * math.cos(a), r * math.sin(a), z))
        radii.append(0.13)
    tube(builder, spiral, radii, GILT_TONE, 6, "bronze_gilt")
    top = z0 + shaft
    first = len(builder.polygons)
    builder.lathe([(0.0, top), (1.55, top), (1.75, top + 0.3), (2.2, top + 1.2), (2.4, top + 1.5), (0.0, top + 1.5)], 16,
                  "bronze_gilt", smooth=True)
    builder.tint(first, GILT_TONE)
    box(builder, (-2.5, -2.5, top + 1.5), (2.5, 2.5, top + 2.1), "marble_white", WARM_WHITE, bottom=True)
    builder.merge(equestrian(), placement(0.0, 0.0, top + 2.1, -math.pi / 2, 2.6))
    return builder, top + 2.1


def horse(coat, seed=0, raised=None):
    rng = random.Random(seed)
    builder = MeshBuilder()
    dark = darker(coat)
    body_z = 1.18
    body_part(builder, (0.0, 0.0, body_z), (0.26, 0.72, 0.31), coat, 9, 6)
    body_part(builder, (0.0, 0.46, body_z + 0.05), (0.24, 0.32, 0.33), coat, 7, 4)
    body_part(builder, (0.0, -0.48, body_z + 0.04), (0.27, 0.32, 0.32), coat, 7, 4)
    shoulder = Vector((0.0, 0.6, body_z + 0.16))
    poll = Vector((0.0, 0.96, body_z + 0.8))
    muzzle = Vector((0.0, 1.24, body_z + 0.42))
    limb(builder, shoulder, poll, 0.17, 0.1, coat, 6)
    limb(builder, poll, muzzle, 0.1, 0.06, coat, 6)
    body_part(builder, muzzle, (0.06, 0.07, 0.065), dark, 5, 2)
    limb(builder, shoulder + Vector((0.0, -0.1, 0.15)), poll + Vector((0.0, -0.04, 0.07)), 0.04, 0.03, dark, 3)
    for side in (-1, 1):
        limb(builder, poll + Vector((side * 0.05, -0.03, 0.04)), poll + Vector((side * 0.08, -0.06, 0.17)), 0.025, 0.01,
             coat, 3)
    legs = {(side, end): ((end * 0.5 + 0.02, 0.5), (end * 0.5, 0.0)) for side in (-1, 1) for end in (-1, 1)}
    legs.update(raised or {})
    for (side, end), ((knee_y, knee_z), (hoof_y, hoof_z)) in legs.items():
        top = Vector((side * 0.13, end * 0.5, body_z - 0.12))
        knee = Vector((side * 0.13, knee_y, knee_z))
        hoof = Vector((side * 0.13, hoof_y, hoof_z))
        limb(builder, top, knee, 0.085, 0.05, coat, 5)
        limb(builder, knee, hoof, 0.042, 0.036, dark if rng.random() < 0.7 else coat, 4)
    limb(builder, (0.0, -0.76, body_z + 0.16), Vector((0.0, -0.9, body_z - 0.55)), 0.055, 0.02, dark, 4)
    return builder


def equestrian():
    builder = MeshBuilder()
    steed = horse((0.5, 0.4, 0.3), 3, {(-1, 1): ((0.62, 0.72), (0.78, 0.5))})
    builder.merge(bronzed(steed, GILT_TONE))
    rider = person(Look("white", hem=0.55, skin=0, hair=0, cloak="white", arms="gesture", seed=401))
    kept = MeshBuilder()
    for indices, material, smooth, uvs, colour in zip(rider.polygons, rider.polygon_materials, rider.polygon_smooth,
                                                      rider.polygon_uvs, rider.polygon_colors):
        if max(rider.positions[i][2] for i in indices) < 0.98:
            continue
        kept.face([kept.point(rider.positions[i]) for i in indices], rider.materials[material], smooth, None, colour, raw=True)
    for side in (-1, 1):
        tube(kept, [(side * 0.12, 0.0, 1.02), (side * 0.3, 0.32, 0.72), (side * 0.3, 0.18, 0.32)], [0.075, 0.06, 0.045],
             BRONZE_TONE, 6)
    tube(kept, [(-0.21, 0.05, 1.1), (-0.28, 0.32, 1.02)], [0.04, 0.035], BRONZE_TONE, 5)
    tinted(kept, GILT_TONE, lambda: kept.lathe([(0.0, -0.11), (0.11, -0.06), (0.12, 0.02), (0.08, 0.09), (0.0, 0.11)],
                                               8, "bronze_gilt", smooth=True, matrix=Matrix.Translation((-0.3, 0.42, 1.06))))
    cross(kept, (-0.3, 0.42, 1.16), 0.2)
    tinted(kept, GILT_TONE, lambda: kept.lathe([(0.11, 1.6), (0.125, 1.66), (0.1, 1.76), (0.0, 1.8)], 10, "bronze_gilt",
                                               smooth=True))
    builder.merge(bronzed(kept, GILT_TONE), placement(0.0, -0.1, 0.62))
    return builder


def porphyry_column():
    builder = MeshBuilder()
    box(builder, (-4.2, -4.2, -1.5), (4.2, 4.2, 1.0), "marble_white", WARM_WHITE)
    box(builder, (-3.6, -3.6, 1.0), (3.6, 3.6, 7.0), "marble_white", (0.96, 0.92, 0.86))
    box(builder, (-3.9, -3.9, 7.0), (3.9, 3.9, 7.8), "marble_white", WARM_WHITE)
    z = 7.8
    for k in range(7):
        first = len(builder.polygons)
        builder.lathe([(1.6, z), (1.6, z + 3.6)], 16, "porphyry", smooth=True, caps=False)
        builder.tint(first, (1.0, 1.0, 1.0))
        z += 3.6
        first = len(builder.polygons)
        builder.lathe([(1.62, z - 0.25), (1.75, z), (1.62, z + 0.25)], 16, "bronze_gilt", smooth=True, caps=False)
        builder.tint(first, GILT_TONE)
    box(builder, (-2.0, -2.0, z), (2.0, 2.0, z + 1.4), "marble_white", WARM_WHITE, bottom=True)
    statue = Look("white", hem=0.55, skin=0, hair=0, cloak="white", arms="gesture", carry="staff", seed=501)
    builder.merge(statue_person(statue, GILT_TONE), placement(0.0, 0.0, z + 1.4, 0.0, 2.6))
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.32
        start = Vector((0.0, 0.0, z + 1.4 + 2.6 * 1.68))
        end = start + Vector((0.32 * math.sin(a), -0.05, 0.32 * math.cos(a) + 0.15))
        tube(builder, [start, end], [0.04, 0.0], GILT_TONE, 4, "bronze_gilt")
    return builder


def forum_constantine(radius_x=62.0, radius_y=52.0):
    builder = MeshBuilder()
    segments = 40
    height = 9.0
    depth = 7.0
    for k in range(segments):
        a0 = TAU * k / segments
        a1 = TAU * (k + 1) / segments
        if any(abs(math.remainder(a - g, TAU)) < 0.12 for a in (a0, a1) for g in (0.0, math.pi)):
            continue

        def at(scale, a):
            return Vector((radius_x * scale * math.cos(a), radius_y * scale * math.sin(a)))
        p0, p1 = at(1.0, a0), at(1.0, a1)
        q0, q1 = at(1.0 + depth / radius_x, a0), at(1.0 + depth / radius_x, a1)
        mid = (q0 + q1) / 2
        facing_quad(builder, [(q0.x, q0.y, -2.0), (q1.x, q1.y, -2.0), (q1.x, q1.y, height + 0.6), (q0.x, q0.y, height + 0.6)],
                    mid.to_3d(), "plaster", colour=(1.0, 0.86, 0.68))
        facing_quad(builder, [(q0.x, q0.y, -2.0), (q1.x, q1.y, -2.0), (q1.x, q1.y, height + 0.6), (q0.x, q0.y, height + 0.6)],
                    -mid.to_3d(), "plaster", colour=WARM_WHITE)
        facing_quad(builder, [(p0.x, p0.y, height), (p1.x, p1.y, height), (q1.x, q1.y, height + 1.8), (q0.x, q0.y, height + 1.8)],
                    (0, 0, 1), "terracotta_tiles")
        first = len(builder.polygons)
        builder.merge(column("ionic", 0.7, height - 0.5, "low", "marble_white"), Matrix.Translation((p0.x, p0.y, 0.0)))
        builder.tint(first, WARM_WHITE)
        facing_quad(builder, [(p0.x, p0.y, height - 0.5), (p1.x, p1.y, height - 0.5), (p1.x, p1.y, height), (p0.x, p0.y, height)],
                    -((p0 + p1) / 2).to_3d(), "marble_white", colour=WARM_WHITE)
    for a in (0.0, math.pi):
        x = radius_x * math.cos(a)
        gate = MeshBuilder()
        box(gate, (-3.0, -9.0, -2.0), (3.0, -3.0, 14.0), "marble_white", WARM_WHITE)
        box(gate, (-3.0, 3.0, -2.0), (3.0, 9.0, 14.0), "marble_white", WARM_WHITE)
        box(gate, (-3.0, -3.0, 9.5), (3.0, 3.0, 14.0), "marble_white", WARM_WHITE)
        box(gate, (-3.4, -9.4, 14.0), (3.4, 9.4, 15.0), "marble_white", WARM_WHITE, bottom=True)
        builder.merge(gate, Matrix.Translation((x + (3.0 if a == 0.0 else -3.0), 0.0, 0.0)))
    return builder


def bath_complex():
    builder = MeshBuilder()
    box(builder, (-40.0, -30.0, -3.0), (40.0, 30.0, 11.0), "banded")
    for x0, x1, y0, y1, h, dome in ((-30.0, -6.0, -14.0, 14.0, 22.0, 11.0), (-4.0, 16.0, -10.0, 10.0, 19.0, 9.0),
                                    (18.0, 34.0, -8.0, 8.0, 16.0, 7.0)):
        box(builder, (x0, y0, 10.0), (x1, y1, h), "plaster", (1.0, 0.9, 0.76))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        shell(builder, (cx, cy, h), dome, 0.0, TAU, 0.0, math.pi / 2, 20, 6, "lead", False)
        for side in (1, -1):
            window(builder, (cx, y1 if side > 0 else y0, h - 6.5), (side, 0, 0), (0, side, 0), 3.6, 5.0, 2.0, lit=False)
    facing_quad(builder, [(-40.6, -30.6, 11.0), (40.6, -30.6, 11.0), (40.6, 30.6, 11.0), (-40.6, 30.6, 11.0)], (0, 0, 1),
                "terracotta_tiles")
    for k in range(10):
        x = -36.0 + k * 8.0
        for side in (1, -1):
            window(builder, (x, side * 30.0, 2.0), (side, 0, 0), (0, side, 0), 2.6, 5.4, 2.0, lit=False)
    portico = augusteon_portico(80.0, 6.0, 7.0)
    builder.merge(portico, Matrix.Translation((-40.0, -37.0, 0.0)))
    return builder


def wall_segment(length, height, thickness=3.2, merlons=True):
    builder = MeshBuilder()
    box(builder, (0.0, -thickness / 2, -6.0), (length, thickness / 2, height), "banded")
    box(builder, (-0.02, -thickness / 2 - 0.12, height - 0.35), (length + 0.02, thickness / 2 + 0.12, height), "marble_white",
        WARM_WHITE, bottom=True)
    if not merlons:
        return builder
    count = max(int(length / 2.6), 2)
    for k in range(count):
        x = (k + 0.5) * length / count
        box(builder, (x - 0.55, thickness / 2 - 0.9, height), (x + 0.55, thickness / 2, height + 1.2), "banded")
    return builder


def wall_tower(height, size=8.5):
    builder = MeshBuilder()
    h = size / 2
    box(builder, (-h, -h, -6.0), (h, h, height), "banded")
    for k in range(4):
        x = -h + (k + 0.5) * size / 4
        for side in (1, -1):
            box(builder, (x - 0.6, side * h - (0.9 if side > 0 else 0.0), height), (x + 0.6, side * h + (0.0 if side > 0 else 0.9),
                                                                                  height + 1.3), "banded")
            box(builder, (side * h - (0.9 if side > 0 else 0.0), x - 0.6, height), (side * h + (0.0 if side > 0 else 0.9),
                                                                                  x + 0.6, height + 1.3), "banded")
    for side in (1, -1):
        window(builder, (0.0, side * h, height - 4.0), (side, 0, 0), (0, side, 0), 0.9, 2.0, 1.0, lit=False)
    return builder


def mole(length, width=8.0, height=1.6):
    builder = MeshBuilder()
    box(builder, (0.0, -width / 2, -8.0), (length, width / 2, height), "col_travertine", (0.86, 0.82, 0.74))
    for k in range(int(length / 9.0)):
        x = 4.0 + k * 9.0
        for side in (1, -1):
            tinted(builder, (0.4, 0.34, 0.28), lambda x=x, side=side: builder.lathe(
                [(0.22, height), (0.2, height + 0.7), (0.26, height + 0.8), (0.0, height + 0.82)], 6, "col_travertine",
                matrix=Matrix.Translation((x, side * (width / 2 - 0.5), 0.0))))
    first = len(builder.polygons)
    builder.lathe([(2.4, height), (2.4, height + 6.0), (1.8, height + 7.0), (0.0, height + 9.0)], 10, "banded",
                  matrix=Matrix.Translation((length, 0.0, 0.0)))
    builder.tint(first, (1.0, 1.0, 1.0))
    return builder


def warehouse(length=36.0, depth=12.0, height=7.0):
    builder = MeshBuilder()
    box(builder, (-length / 2, -depth / 2, -3.0), (length / 2, depth / 2, height), "banded")
    for side in (1, -1):
        facing_quad(builder, [(-length / 2 - 0.5, side * (depth / 2 + 0.5), height - 0.2),
                              (length / 2 + 0.5, side * (depth / 2 + 0.5), height - 0.2),
                              (length / 2 + 0.5, 0.0, height + depth * 0.22), (-length / 2 - 0.5, 0.0, height + depth * 0.22)],
                    (0, side, 1), "terracotta_tiles")
        facing_quad(builder, [(side * length / 2, -depth / 2, height), (side * length / 2, depth / 2, height),
                              (side * length / 2, 0.0, height + depth * 0.22)], (side, 0, 0), "banded")
    for k in range(int(length / 6.0)):
        x = -length / 2 + 3.0 + k * 6.0
        window(builder, (x, -depth / 2, 0.0), (-1, 0, 0), (0, -1, 0), 2.6, 3.8, 1.0, lit=False)
    return builder


def palace_hall(length, width, height, apse=True, colour=(1.0, 0.9, 0.78), roof="terracotta_tiles"):
    builder = MeshBuilder()
    box(builder, (-length / 2, -width / 2, -4.0), (length / 2, width / 2, height), "plaster", colour)
    for side in (1, -1):
        facing_quad(builder, [(-length / 2 - 0.6, side * (width / 2 + 0.6), height - 0.2),
                              (length / 2 + 0.6, side * (width / 2 + 0.6), height - 0.2),
                              (length / 2 + 0.6, 0.0, height + width * 0.2), (-length / 2 - 0.6, 0.0, height + width * 0.2)],
                    (0, side, 1), roof)
        facing_quad(builder, [(side * length / 2, -width / 2, height), (side * length / 2, width / 2, height),
                              (side * length / 2, 0.0, height + width * 0.2)], (side, 0, 0), "plaster", colour=colour)
        for k in range(max(int(length / 5.0), 1)):
            x = -length / 2 + 2.5 + k * 5.0
            window(builder, (x, side * width / 2, height * 0.45), (side, 0, 0), (0, side, 0), 1.6, height * 0.4, 1.0,
                   lit=False)
    if apse:
        revolve_band(builder, (length / 2, 0, 0), width * 0.35, -4.0, height * 0.8, -math.pi / 2, math.pi, 10, "plaster",
                     True, colour)
        shell(builder, (length / 2, 0.0, height * 0.8), width * 0.35, -math.pi / 2, math.pi, 0.0, math.pi / 2, 10, 4,
              "lead", False)
    return builder


def domed_chapel(size=12.0, height=9.0, colour=(1.0, 0.86, 0.7)):
    builder = MeshBuilder()
    h = size / 2
    box(builder, (-h, -h, -4.0), (h, h, height), "banded")
    for side in (1, -1):
        facing_quad(builder, [(-h - 0.4, side * (h + 0.4), height), (h + 0.4, side * (h + 0.4), height),
                              (h * 0.4, side * h * 0.4, height + 1.6), (-h * 0.4, side * h * 0.4, height + 1.6)],
                    (0, side, 1), "terracotta_tiles")
        facing_quad(builder, [(side * (h + 0.4), -h - 0.4, height), (side * (h + 0.4), h + 0.4, height),
                              (side * h * 0.4, h * 0.4, height + 1.6), (side * h * 0.4, -h * 0.4, height + 1.6)],
                    (side, 0, 1), "terracotta_tiles")
    revolve_band(builder, (0, 0, 0), h * 0.55, height + 1.0, height + 3.4, 0.0, TAU, 12, "plaster", True, colour)
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        window(builder, (h * 0.56 * math.cos(a), h * 0.56 * math.sin(a), height + 1.6),
               (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0), 0.6, 1.4, 0.5, lit=False)
    shell(builder, (0.0, 0.0, height + 3.4), h * 0.58, 0.0, TAU, 0.0, math.pi / 2, 12, 4, "lead", False)
    cross(builder, (0.0, 0.0, height + 3.4 + h * 0.58), 1.2)
    revolve_band(builder, (h, 0, 0), h * 0.5, -4.0, height * 0.75, -math.pi / 2, math.pi, 8, "banded", True)
    shell(builder, (h, 0.0, height * 0.75), h * 0.5, -math.pi / 2, math.pi, 0.0, math.pi / 2, 8, 3, "terracotta_tiles", False)
    return builder


def peristyle_court(width, depth, height=6.0, colour=(1.0, 0.9, 0.78), garden=True):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    wing = 7.0
    for (x0, y0), (x1, y1) in (((-hw, -hd), (hw, -hd + wing)), ((-hw, hd - wing), (hw, hd)),
                               ((-hw, -hd + wing), (-hw + wing, hd - wing)), ((hw - wing, -hd + wing), (hw, hd - wing))):
        box(builder, (x0, y0, -4.0), (x1, y1, height), "plaster", colour)
    for (x0, y0), (x1, y1), axis in (((-hw - 0.5, -hd - 0.5), (hw + 0.5, -hd + wing), "y"), ((-hw - 0.5, hd - wing), (hw + 0.5, hd + 0.5), "y"),
                                     ((-hw - 0.5, -hd + wing), (-hw + wing, hd - wing), "x"), ((hw - wing, -hd + wing), (hw + 0.5, hd - wing), "x")):
        if axis == "y":
            mid = (y0 + y1) / 2
            for edge in (y0, y1):
                facing_quad(builder, [(x0, edge, height), (x1, edge, height), (x1, mid, height + 2.2), (x0, mid, height + 2.2)],
                            (0, edge - mid, 1), "terracotta_tiles")
        else:
            mid = (x0 + x1) / 2
            for edge in (x0, x1):
                facing_quad(builder, [(edge, y0, height), (edge, y1, height), (mid, y1, height + 2.2), (mid, y0, height + 2.2)],
                            (edge - mid, 0, 1), "terracotta_tiles")
    cw, cd = hw - wing, hd - wing
    for (a, b) in (((-cw + 1.5, -cd + 1.5), (cw - 1.5, -cd + 1.5)), ((-cw + 1.5, cd - 1.5), (cw - 1.5, cd - 1.5))):
        colonnade(builder, a, b, max(int((b[0] - a[0]) / 3.0), 2), 4.2, 0.4, 0.0, WARM_WHITE)
    if garden:
        facing_quad(builder, [(-cw, -cd, 0.05), (cw, -cd, 0.05), (cw, cd, 0.05), (-cw, cd, 0.05)], (0, 0, 1), "matte",
                    colour=(0.32, 0.52, 0.2))
        first = len(builder.polygons)
        builder.lathe([(1.6, 0.0), (1.6, 0.6), (1.4, 0.6), (1.4, 0.3)], 10, "marble_white")
        builder.tint(first, WARM_WHITE)
        facing_quad(builder, [Vector((1.42 * math.cos(TAU * k / 10), 1.42 * math.sin(TAU * k / 10), 0.5)) for k in range(10)],
                    (0, 0, 1), "pool")
    else:
        facing_quad(builder, [(-cw, -cd, 0.05), (cw, -cd, 0.05), (cw, cd, 0.05), (-cw, cd, 0.05)], (0, 0, 1), "marble_paving")
    return builder


def statue_group(seed):
    rng = random.Random(seed)
    builder = MeshBuilder()
    pedestal(builder, 1.6, 2.6)
    look = Look("white", hem=0.03 if rng.random() < 0.5 else 0.55, skin=0, hair=rng.randrange(3),
                cloak="white" if rng.random() < 0.6 else None, arms=rng.choice(["gesture", "down", "toga"]), seed=seed)
    tone = BRONZE_TONE if rng.random() < 0.6 else (0.95, 0.93, 0.88)
    material = "bronze_gilt" if tone == BRONZE_TONE else "marble_white"
    builder.merge(bronzed(person(look), tone, material), placement(0.0, 0.0, 2.6, 0.0, 1.25))
    return builder
