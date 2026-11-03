import math

from mathutils import Vector

from .geometry import MATTE, MeshBuilder

PITCH = (0.075, 0.062, 0.052)
STRAKE = (0.40, 0.29, 0.19)
DECK = (0.60, 0.48, 0.34)
OAR = (0.58, 0.45, 0.30)
OAR_FAR = (0.36, 0.27, 0.18)
BRONZE = (0.56, 0.38, 0.17)
TOWER = (0.62, 0.48, 0.31)
TOWER_SHADE = (0.46, 0.35, 0.23)
LINEN = (0.86, 0.80, 0.66)
MAST = (0.42, 0.31, 0.20)
TUNICS = [(0.62, 0.22, 0.16), (0.80, 0.75, 0.62), (0.52, 0.45, 0.34), (0.40, 0.38, 0.36)]
SKIN = (0.66, 0.47, 0.34)
BOTTOM = -0.5

SPECS = {
    "decere": dict(length=45.0, beam=7.0, freeboard=3.0, sheer=(1.6, 2.2), oarbox=0.9, banks=[26, 26, 24], reach=8.0,
                   towers=[(10.5, 4.2, 4.4, 4.2), (-11.0, 4.0, 4.0, 3.8)], bronze=True, crew=26, ram=2.4),
    "hexere": dict(length=40.0, beam=6.2, freeboard=2.6, sheer=(1.4, 2.0), oarbox=0.8, banks=[24, 22], reach=7.0,
                   towers=[(8.0, 3.8, 3.6, 3.6)], bronze=True, crew=18, ram=2.2),
    "quinquereme": dict(length=36.0, beam=5.4, freeboard=2.2, sheer=(1.2, 1.8), oarbox=0.7, banks=[24, 22],
                        reach=6.2, towers=[], bronze=True, crew=12, ram=2.0),
    "egyptien": dict(length=34.0, beam=5.2, freeboard=2.1, sheer=(1.2, 2.0), oarbox=0.7, banks=[22, 20], reach=6.0,
                     towers=[], bronze=False, crew=10, ram=1.9, mast=True),
    "polyreme": dict(length=37.0, beam=5.6, freeboard=2.3, sheer=(1.2, 1.8), oarbox=0.7, banks=[24, 22], reach=6.4,
                     towers=[], bronze=False, crew=14, ram=2.1),
    "trireme": dict(length=35.0, beam=4.8, freeboard=1.9, sheer=(1.1, 1.8), oarbox=0.6, banks=[27, 25, 25],
                    reach=5.4, towers=[], bronze=False, crew=8, ram=1.9),
    "liburne": dict(length=23.0, beam=3.4, freeboard=1.3, sheer=(0.9, 1.4), oarbox=0.0, banks=[16, 16], reach=4.2,
                    towers=[], bronze=False, crew=6, ram=1.4),
}


def quad(builder, corners, color, both=False):
    first = len(builder.polygons)
    builder.face(builder.points(corners), MATTE)
    if both:
        builder.face(list(reversed(builder.points(corners))), MATTE)
    builder.tint(first, color)


def block(builder, minimum, maximum, color, bottom=False):
    first = len(builder.polygons)
    builder.box(minimum, maximum, MATTE, bottom=bottom)
    builder.tint(first, color)


def half_beam(spec, t):
    return max(0.14, spec["beam"] / 2 * (1 - abs(t) ** 2.4) ** 0.5)


def gunwale(spec, t):
    bow, stern = spec["sheer"]
    return spec["freeboard"] + (bow * t ** 4 if t > 0 else stern * t ** 4)


def hull(builder, spec, stations, wale):
    length = spec["length"]
    rows = []
    for index in range(stations + 1):
        t = -1 + 2 * index / stations
        b = half_beam(spec, t)
        g = gunwale(spec, t)
        y = t * length / 2
        profile = [(b, g), (0.97 * b, 0.55 * g), (0.92 * b, 0.0), (0.55 * b, BOTTOM)] if wale else \
            [(b, g), (0.88 * b, 0.0), (0.5 * b, BOTTOM)]
        rows.append((t, y, profile))
    for (t0, y0, p0), (t1, y1, p1) in zip(rows[:-1], rows[1:]):
        for side in (-1, 1):
            for corner in range(len(p0) - 1):
                a = Vector((side * p0[corner][0], y0, p0[corner][1]))
                b = Vector((side * p1[corner][0], y1, p1[corner][1]))
                c = Vector((side * p1[corner + 1][0], y1, p1[corner + 1][1]))
                d = Vector((side * p0[corner + 1][0], y0, p0[corner + 1][1]))
                first = len(builder.polygons)
                builder.oriented([a, b, c, d], (side, 0, 0), MATTE)
                color = STRAKE if (wale and corner == 0) else PITCH
                if spec["bronze"] and t1 > 0.78 and corner > 0:
                    color = BRONZE
                builder.tint(first, color)
        first = len(builder.polygons)
        builder.oriented([Vector((-p0[0][0], y0, p0[0][1])), Vector((p0[0][0], y0, p0[0][1])),
                          Vector((p1[0][0], y1, p1[0][1])), Vector((-p1[0][0], y1, p1[0][1]))],
                         (0, 0, 1), MATTE)
        builder.tint(first, DECK)
    for t, y, profile in (rows[0], rows[-1]):
        ring = [Vector((-x, y, z)) for x, z in profile] + [Vector((x, y, z)) for x, z in reversed(profile)]
        first = len(builder.polygons)
        builder.oriented(ring, (0, 1 if t > 0 else -1, 0), MATTE)
        builder.tint(first, PITCH)


def beam_path(builder, points, half_width, half_height, color):
    points = [Vector(point) for point in points]
    rings = []
    for index, point in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        tangent = (b - a).normalized()
        side = Vector((1.0, 0.0, 0.0))
        if abs(tangent.dot(side)) > 0.9:
            side = Vector((0.0, 1.0, 0.0))
        normal = tangent.cross(side).normalized()
        side = normal.cross(tangent).normalized()
        rings.append([builder.point(point + side * sx * half_width + normal * sy * half_height)
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    first = len(builder.polygons)
    for lower, upper in zip(rings[:-1], rings[1:]):
        for k in range(4):
            j = (k + 1) % 4
            builder.face([lower[k], lower[j], upper[j], upper[k]], MATTE)
    builder.face(list(reversed(rings[0])), MATTE)
    builder.face(list(rings[-1]), MATTE)
    builder.tint(first, color)


def ram(builder, spec, far):
    tip = spec["length"] / 2 + spec["ram"]
    base = spec["length"] / 2 - 0.6
    if far:
        quad(builder, [(0.0, tip, 0.2), (-0.4, base, -0.2), (0.0, base, 0.9)], BRONZE)
        quad(builder, [(0.0, tip, 0.2), (0.0, base, 0.9), (0.4, base, -0.2)], BRONZE)
        return
    beam_path(builder, [(0.0, base, 0.25), (0.0, tip - 0.6, 0.22), (0.0, tip, 0.2)], 0.36, 0.45, BRONZE)
    for z in (0.62, -0.1):
        quad(builder, [(-0.5, tip - 0.5, z), (0.5, tip - 0.5, z), (0.06, tip - 0.1, z)], BRONZE, both=True)


def stem_and_stern(builder, spec, far):
    length = spec["length"]
    bow = gunwale(spec, 1.0)
    stern = gunwale(spec, -1.0)
    width = 0.22 if far else 0.16
    beam_path(builder, [(0.0, length / 2 - 0.4, bow - 0.6), (0.0, length / 2 + 0.25, bow + 0.5),
                        (0.0, length / 2 + 0.1, bow + 1.5), (0.0, length / 2 - 0.4, bow + 1.9)], width, 0.22, PITCH)
    curve = [(0.0, -length / 2 + 0.6, stern - 0.6), (0.0, -length / 2 - 0.35, stern + 0.6),
             (0.0, -length / 2 - 0.5, stern + 1.8), (0.0, -length / 2 - 0.1, stern + 2.8),
             (0.0, -length / 2 + 0.7, stern + 3.2)]
    beam_path(builder, curve if not far else curve[::2], width + 0.05, 0.3, PITCH)
    if far:
        return
    b = half_beam(spec, -0.8)
    for side in (-1, 1):
        beam_path(builder, [(side * (b + 0.1), -length / 2 + 4.0, stern * 0.7),
                            (side * (b + 0.7), -length / 2 + 0.6, -0.3)], 0.08, 0.3, OAR)


def oars(builder, spec, far):
    banks = spec["banks"]
    if not banks:
        return
    box = spec["oarbox"]
    g = spec["freeboard"]
    width = half_beam(spec, 0.0)
    span = spec["length"] * 0.27
    for bank, count in enumerate(banks):
        z = g - 0.45 - bank * 0.5 if box else g - 0.25 - bank * 0.42
        out = width + box + 0.05 + bank * 0.12
        reach = spec["reach"] - bank * 0.6
        for side in (-1, 1):
            if far:
                quad(builder, [(side * out, -span, z), (side * out, span, z), (side * (out + reach), span - 1.0, 0.0),
                               (side * (out + reach), -span - 1.0, 0.0)], OAR_FAR, both=True)
                continue
            for index in range(count):
                y = -span + 2 * span * (index + 0.5) / count
                tip = (side * (out + reach), y - 1.0, -0.05)
                quad(builder, [(side * out, y - 0.06, z), (side * out, y + 0.06, z), (tip[0], tip[1] + 0.18, tip[2]),
                               (tip[0], tip[1] - 0.18, tip[2])], OAR, both=True)


def oarbox(builder, spec):
    box = spec["oarbox"]
    if not box:
        return
    g = spec["freeboard"]
    width = half_beam(spec, 0.0)
    span = spec["length"] * 0.29
    for side in (-1, 1):
        x0, x1 = sorted((side * (width - 0.3), side * (width + box)))
        block(builder, (x0, -span, g - 1.15), (x1, span, g - 0.25), STRAKE, bottom=True)


def tower(builder, spec, y, width, depth, height, far):
    deck = gunwale(spec, y / (spec["length"] / 2))
    block(builder, (-width / 2, y - depth / 2, deck), (width / 2, y + depth / 2, deck + height), TOWER)
    block(builder, (-width / 2 - 0.15, y - depth / 2 - 0.15, deck + height - 0.25),
          (width / 2 + 0.15, y + depth / 2 + 0.15, deck + height), TOWER_SHADE, bottom=True)
    if far:
        return
    top = deck + height
    for sx in (-1, 1):
        for k in range(3):
            x = sx * width / 2
            y0 = y - depth / 2 + depth * (k + 0.5) / 3
            block(builder, (x - 0.2, y0 - 0.35, top), (x + 0.2, y0 + 0.35, top + 0.7), TOWER)
    for sy in (-1, 1):
        for k in range(2):
            x0 = -width / 2 + width * (k + 0.5) / 2
            y0 = y + sy * depth / 2
            block(builder, (x0 - 0.35, y0 - 0.2, top), (x0 + 0.35, y0 + 0.2, top + 0.7), TOWER)


def figure(builder, x, y, z, index):
    tunic = TUNICS[index % len(TUNICS)]
    block(builder, (x - 0.22, y - 0.15, z), (x + 0.22, y + 0.15, z + 1.15), tunic)
    block(builder, (x - 0.11, y - 0.11, z + 1.15), (x + 0.11, y + 0.11, z + 1.42), SKIN)


def crew(builder, spec):
    count = spec["crew"]
    length = spec["length"]
    spots = []
    for y, width, depth, height in spec["towers"]:
        deck = gunwale(spec, y / (length / 2)) + height
        for sx in (-0.9, 0.9):
            spots.append((sx, y, deck))
    for index in range(len(spots), count):
        t = -0.45 + 0.9 * ((index * 0.618) % 1.0)
        b = half_beam(spec, t) * 0.6
        side = -1 if index % 2 else 1
        spots.append((side * b * (0.4 + 0.6 * ((index * 0.37) % 1.0)), t * length / 2, gunwale(spec, t)))
    for index, (x, y, z) in enumerate(spots[:count]):
        figure(builder, x, y, z, index)


def rig(builder, spec, far):
    if not spec.get("mast"):
        return
    deck = spec["freeboard"]
    top = deck + 12.0
    block(builder, (-0.18, 2.0, deck), (0.18, 2.36, top), MAST)
    yard = top - 1.2
    beam_path(builder, [(-7.5, 2.2, yard), (7.5, 2.2, yard)], 0.12, 0.12, MAST)
    if far:
        block(builder, (-7.0, 2.0, yard - 0.7), (7.0, 2.4, yard - 0.1), LINEN, bottom=True)
        return
    for k in range(6):
        x0 = -7.0 + k * 14.0 / 6
        block(builder, (x0, 1.95, yard - 0.75 + 0.06 * (k % 2)), (x0 + 14.0 / 6 - 0.05, 2.45, yard - 0.1), LINEN,
              bottom=True)
    for sx in (-1, 1):
        beam_path(builder, [(sx * 7.3, 2.2, yard), (sx * half_beam(spec, 0.1), 5.5, deck + 0.3)], 0.03, 0.03, MAST)
    beam_path(builder, [(0.0, 2.2, top - 0.2), (0.0, spec["length"] / 2 - 1.0, gunwale(spec, 1.0))], 0.03, 0.03, MAST)


def ship(kind, far=False):
    spec = SPECS[kind]
    builder = MeshBuilder()
    hull(builder, spec, 6 if far else 14, not far)
    ram(builder, spec, far)
    stem_and_stern(builder, spec, far)
    oars(builder, spec, far)
    if not far:
        oarbox(builder, spec)
    for y, width, depth, height in spec["towers"]:
        tower(builder, spec, y, width, depth, height, far)
    rig(builder, spec, far)
    if not far:
        crew(builder, spec)
    return builder


def land_army():
    builder = MeshBuilder()
    block(builder, (-14.0, -9.0, 0.0), (14.0, 9.0, 1.7), (0.42, 0.30, 0.22))
    block(builder, (-14.2, 7.6, 0.0), (14.2, 9.4, 1.9), (0.58, 0.44, 0.26))
    for k in range(9):
        x = -12.6 + k * 3.15
        block(builder, (x - 0.15, -8.0, 1.7), (x + 0.15, 8.0, 4.2), (0.36, 0.30, 0.24))
    return builder


TROOPS = {kind: (lambda kind=kind: ship(kind), lambda kind=kind: ship(kind, far=True)) for kind in SPECS}
TROOPS["armee"] = (land_army, land_army)
