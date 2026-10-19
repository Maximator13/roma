import math

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .nimes_figures import ellipsoid, tube

SKIN = (0.74, 0.54, 0.40)
DARK_SKIN = (0.52, 0.36, 0.25)
BRONZE = (0.62, 0.45, 0.22)
IRON = (0.46, 0.46, 0.47)
MAIL = (0.42, 0.42, 0.43)
WOOD = (0.47, 0.35, 0.22)
LEATHER = (0.36, 0.25, 0.16)
BLACK = (0.08, 0.07, 0.07)
PURPLE = (0.36, 0.12, 0.22)
WOOL_RED = (0.55, 0.20, 0.15)
WOOL_UNDYED = (0.78, 0.72, 0.60)
LINEN_WHITE = (0.93, 0.92, 0.88)
WOLF = (0.40, 0.33, 0.25)
HORSE_BAY = (0.42, 0.27, 0.16)
HORSE_DUN = (0.62, 0.48, 0.32)


def box(builder, center, size, color):
    first = len(builder.polygons)
    builder.centered_box(center, size, MATTE)
    builder.tint(first, color)


def quad_both(builder, corners, color):
    first = len(builder.polygons)
    builder.face(builder.points(corners), MATTE)
    builder.face(list(reversed(builder.points(corners))), MATTE)
    builder.tint(first, color)


def head(builder, center, skin, hair=None):
    ellipsoid(builder, center, (0.095, 0.105, 0.12), skin, 7, 4)
    if hair is not None:
        ellipsoid(builder, (center[0], center[1] - 0.025, center[2] + 0.035), (0.105, 0.11, 0.1), hair, 7, 3)


def montefortino(builder, center, plumes):
    first = len(builder.polygons)
    profile = [(1.28, -0.12), (1.06, 0.0), (1.02, 0.35), (0.82, 0.72), (0.42, 0.95), (0.16, 1.02), (0.12, 1.18),
               (0.0, 1.22)]
    transform = Matrix.Translation(Vector(center) + Vector((0.0, -0.012, 0.0))) @ Matrix.Diagonal((0.105, 0.115, 0.12, 1.0))
    builder.lathe(profile, 8, MATTE, smooth=True, matrix=transform)
    builder.tint(first, BRONZE)
    if not plumes:
        return
    top = Vector(center) + Vector((0.0, -0.012, 0.145))
    for index, offset in enumerate((-0.035, 0.0, 0.035)):
        color = PURPLE if index != 1 else BLACK
        base = top + Vector((offset, 0.0, 0.0))
        quad_both(builder, [base + Vector((-0.012, 0.0, 0.0)), base + Vector((0.012, 0.0, 0.0)),
                            base + Vector((0.02, -0.02, 0.34)), base + Vector((-0.02, -0.02, 0.34))], color)


def cap(builder, center, color, tail=False):
    ellipsoid(builder, (center[0], center[1] - 0.01, center[2] + 0.04), (0.108, 0.118, 0.1), color, 7, 3)
    if tail:
        tube(builder, [(center[0], center[1] - 0.1, center[2] + 0.02), (center[0], center[1] - 0.2, center[2] - 0.25)],
             [0.045, 0.02], color, 4)


def body(builder, tunic, torso, skirt_length=0.36, hem=None):
    tube(builder, [(0.0, 0.0, 0.96), (0.0, 0.0, 1.18), (0.0, 0.01, 1.43)], [0.16, 0.17, 0.2], torso, 7, squash=0.62)
    top = 0.98
    bottom = top - skirt_length
    tube(builder, [(0.0, 0.0, top), (0.0, 0.0, bottom)], [0.18, 0.24], tunic, 7, cap=False, squash=0.75)
    if hem is not None:
        tube(builder, [(0.0, 0.0, bottom + 0.06), (0.0, 0.0, bottom - 0.005)], [0.237, 0.247], hem, 7, cap=False,
             squash=0.75)
    tube(builder, [(0.0, 0.0, 1.43), (0.0, 0.0, 1.52)], [0.055, 0.05], SKIN, 5, cap=False)


def legs(builder, skin, lower=None, trousers=None):
    for side in (-1, 1):
        hip = Vector((side * 0.09, 0.0, 0.94))
        knee = Vector((side * 0.1, 0.03, 0.5))
        ankle = Vector((side * 0.1, 0.0, 0.08))
        upper_color = trousers if trousers is not None else skin
        tube(builder, [hip, knee], [0.075, 0.058], upper_color, 5, cap=False)
        tube(builder, [knee, ankle], [0.058, 0.045], trousers if trousers is not None else (lower or skin), 5, cap=False)
        box(builder, (side * 0.1, 0.05, 0.035), (0.09, 0.22, 0.07), LEATHER)


def arms(builder, sleeve, skin, right_hand, left_hand):
    for side, hand in ((1, right_hand), (-1, left_hand)):
        shoulder = Vector((side * 0.22, 0.0, 1.38))
        hand = Vector(hand)
        elbow = shoulder.lerp(hand, 0.5) + Vector((side * 0.08, -0.04, -0.08))
        tube(builder, [shoulder, elbow], [0.06, 0.05], sleeve, 5, cap=False)
        tube(builder, [elbow, hand], [0.05, 0.04], skin, 5)


def scutum(builder, center, color, width=0.68, height=1.15, radius=0.55):
    rows = 7
    columns = 4
    first = len(builder.polygons)
    for layer, thickness in ((0, 0.0), (1, -0.025)):
        grid = []
        for row in range(rows + 1):
            v = -1 + 2 * row / rows
            half = max(0.3, math.sqrt(max(0.0, 1 - v * v))) * width / 2
            line = []
            for column in range(columns + 1):
                u = -1 + 2 * column / columns
                angle = u * half / radius
                line.append(Vector(center) + Vector((radius * math.sin(angle), radius * (math.cos(angle) - 1) + thickness,
                                                     v * height / 2)))
            grid.append(builder.points(line))
        for row in range(rows):
            for column in range(columns):
                quad = [grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]]
                builder.face(quad if layer else list(reversed(quad)), MATTE)
    builder.tint(first, color)
    box(builder, (center[0], center[1] + 0.02, center[2]), (0.05, 0.03, height * 0.8), tuple(c * 0.75 for c in color))
    box(builder, (center[0], center[1] + 0.04, center[2]), (0.13, 0.05, 0.16), IRON)


def round_shield(builder, center, diameter, color):
    first = len(builder.polygons)
    radius = diameter / 2
    profile = [(0.0, 0.06), (radius * 0.5, 0.045), (radius, 0.0), (radius, -0.02), (0.0, -0.02)]
    transform = Matrix.Translation(center) @ Matrix.Rotation(-math.pi / 2, 4, "X")
    builder.lathe(profile, 10, MATTE, smooth=False, matrix=transform)
    builder.tint(first, color)
    box(builder, (center[0], center[1] + 0.06, center[2]), (0.09, 0.04, 0.09), BRONZE)


def flat_oval(builder, center, color, width=0.6, height=1.12):
    first = len(builder.polygons)
    count = 12
    outline = [(math.cos(math.tau * k / count) * width / 2, math.sin(math.tau * k / count) * height / 2)
               for k in range(count)]
    front = builder.points([Vector(center) + Vector((x, 0.012, z)) for x, z in outline])
    back = builder.points([Vector(center) + Vector((x, -0.012, z)) for x, z in outline])
    builder.face(list(reversed(front)), MATTE)
    builder.face(back, MATTE)
    builder.tint(first, color)
    box(builder, (center[0], center[1] + 0.025, center[2]), (0.045, 0.03, height * 0.9), tuple(c * 0.7 for c in color))
    box(builder, (center[0], center[1] + 0.045, center[2]), (0.15, 0.05, 0.12), IRON)


def shaft(builder, start, end, radius, color, head_length=0.0, head_color=IRON):
    start = Vector(start)
    end = Vector(end)
    if head_length <= 0:
        tube(builder, [start, end], [radius, radius], color, 3)
        return
    neck = end - (end - start).normalized() * head_length
    tube(builder, [start, neck], [radius, radius], color, 3, cap=False)
    tube(builder, [neck, end], [radius * 0.9, 0.0], head_color, 3)


def blade(builder, hand, length, width, color=IRON):
    hand = Vector(hand)
    tip = hand + Vector((0.0, 0.25, length))
    tube(builder, [hand, hand + Vector((0.0, 0.03, 0.1))], [0.02, 0.02], LEATHER, 3, cap=False)
    tube(builder, [hand + Vector((0.0, 0.03, 0.1)), tip], [width, width * 0.3], color, 3, squash=0.25)


RIGHT_HAND = (0.27, 0.3, 1.02)
SHIELD_HAND = (-0.2, 0.3, 1.02)
SHIELD_CENTER = (-0.18, 0.45, 0.98)


def legionary(kind):
    builder = MeshBuilder()
    torso = {"hastatus": WOOL_RED, "princeps": MAIL, "triarius": MAIL}[kind]
    legs(builder, SKIN, lower=BRONZE)
    body(builder, WOOL_RED, torso, skirt_length=0.34)
    if kind == "hastatus":
        box(builder, (0.0, 0.135, 1.27), (0.2, 0.025, 0.2), BRONZE)
    arms(builder, WOOL_RED, SKIN, RIGHT_HAND, SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN)
    montefortino(builder, (0.0, 0.0, 1.62), plumes=True)
    shield_color = {"hastatus": (0.58, 0.27, 0.18), "princeps": (0.52, 0.30, 0.20), "triarius": (0.45, 0.26, 0.18)}[kind]
    scutum(builder, SHIELD_CENTER, shield_color)
    if kind == "triarius":
        shaft(builder, (0.27, 0.22, 0.15), (0.27, 0.52, 2.7), 0.018, WOOD, 0.24)
    else:
        shaft(builder, (0.27, 0.2, 0.25), (0.27, 0.42, 1.6), 0.02, WOOD)
        shaft(builder, (0.27, 0.42, 1.6), (0.27, 0.5, 2.25), 0.008, IRON, 0.06)
    return builder


def velite():
    builder = MeshBuilder()
    legs(builder, SKIN)
    body(builder, WOOL_UNDYED, WOOL_UNDYED, skirt_length=0.3)
    arms(builder, WOOL_UNDYED, SKIN, (0.27, 0.15, 1.5), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN)
    cap(builder, (0.0, 0.0, 1.62), WOLF, tail=True)
    round_shield(builder, (-0.2, 0.42, 1.02), 0.86, (0.55, 0.42, 0.28))
    for offset in (0.0, 0.05):
        shaft(builder, (0.27 + offset, -0.25, 1.35), (0.27 + offset, 0.75, 1.75), 0.012, WOOD, 0.14)
    return builder


def libyan():
    builder = MeshBuilder()
    legs(builder, DARK_SKIN, lower=BRONZE)
    body(builder, WOOL_UNDYED, MAIL, skirt_length=0.34)
    arms(builder, WOOL_UNDYED, DARK_SKIN, RIGHT_HAND, SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), DARK_SKIN)
    montefortino(builder, (0.0, 0.0, 1.62), plumes=False)
    scutum(builder, SHIELD_CENTER, (0.66, 0.55, 0.38))
    shaft(builder, (0.27, 0.22, 0.2), (0.27, 0.5, 2.5), 0.018, WOOD, 0.22)
    return builder


def celt():
    builder = MeshBuilder()
    legs(builder, SKIN, trousers=(0.36, 0.42, 0.30))
    tube(builder, [(0.0, 0.0, 0.92), (0.0, 0.0, 1.0)], [0.19, 0.18], LEATHER, 7, cap=False, squash=0.7)
    tube(builder, [(0.0, 0.0, 0.98), (0.0, 0.0, 1.18), (0.0, 0.01, 1.43)], [0.16, 0.17, 0.2], SKIN, 7, squash=0.62)
    tube(builder, [(0.0, 0.0, 1.43), (0.0, 0.0, 1.52)], [0.055, 0.05], SKIN, 5, cap=False)
    arms(builder, SKIN, SKIN, (0.3, 0.2, 1.55), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=(0.62, 0.42, 0.20))
    tube(builder, [(0.0, -0.06, 1.62), (0.0, -0.12, 1.38)], [0.08, 0.05], (0.62, 0.42, 0.20), 4)
    flat_oval(builder, SHIELD_CENTER, (0.30, 0.42, 0.30))
    hand = Vector((0.3, 0.2, 1.55))
    tube(builder, [hand, hand + Vector((0.02, -0.05, 0.1))], [0.02, 0.02], LEATHER, 3, cap=False)
    tube(builder, [hand + Vector((0.02, -0.05, 0.1)), hand + Vector((0.08, -0.35, 0.95))], [0.035, 0.03], IRON, 3,
         squash=0.25)
    return builder


def iberian():
    builder = MeshBuilder()
    legs(builder, SKIN)
    body(builder, LINEN_WHITE, LINEN_WHITE, skirt_length=0.3, hem=PURPLE)
    arms(builder, LINEN_WHITE, SKIN, (0.27, 0.32, 1.12), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN)
    cap(builder, (0.0, 0.0, 1.62), (0.24, 0.18, 0.13))
    flat_oval(builder, SHIELD_CENTER, (0.62, 0.50, 0.34))
    blade(builder, (0.27, 0.32, 1.12), 0.5, 0.035)
    return builder


def slinger():
    builder = MeshBuilder()
    legs(builder, SKIN)
    body(builder, (0.66, 0.60, 0.48), (0.66, 0.60, 0.48), skirt_length=0.28)
    arms(builder, (0.66, 0.60, 0.48), SKIN, (0.3, -0.05, 1.75), (-0.2, 0.25, 1.15))
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=(0.16, 0.11, 0.08))
    tube(builder, [(0.3, -0.05, 1.75), (0.32, -0.25, 1.45), (0.3, -0.3, 1.25)], [0.01, 0.01, 0.035], LEATHER, 3)
    ellipsoid(builder, (-0.2, 0.05, 0.95), (0.08, 0.06, 0.1), LEATHER, 5, 3)
    return builder


def lonchophore():
    builder = MeshBuilder()
    legs(builder, SKIN)
    body(builder, (0.70, 0.58, 0.40), (0.70, 0.58, 0.40), skirt_length=0.3)
    arms(builder, (0.70, 0.58, 0.40), SKIN, (0.27, 0.1, 1.5), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=(0.18, 0.12, 0.08))
    round_shield(builder, (-0.2, 0.42, 1.02), 0.56, (0.42, 0.30, 0.20))
    for offset in (0.0, 0.05):
        shaft(builder, (0.27 + offset, -0.35, 1.4), (0.27 + offset, 0.7, 1.68), 0.012, WOOD, 0.16)
    return builder


def horse(builder, scale, color, cloth=None):
    s = scale
    dark = tuple(c * 0.55 for c in color)
    body_z = 1.12 * s
    ellipsoid(builder, (0.0, 0.0, body_z), (0.27 * s, 0.82 * s, 0.33 * s), color, 8, 5)
    if cloth is not None:
        tube(builder, [(0.0, -0.05 * s, body_z + 0.3 * s), (0.0, 0.25 * s, body_z + 0.3 * s)], [0.3 * s, 0.3 * s],
             cloth, 6, cap=False, squash=0.9)
    neck = [Vector((0.0, 0.55 * s, body_z + 0.15 * s)), Vector((0.0, 0.8 * s, body_z + 0.5 * s)),
            Vector((0.0, 0.92 * s, body_z + 0.75 * s))]
    tube(builder, neck, [0.18 * s, 0.14 * s, 0.11 * s], color, 6, cap=False, squash=0.7)
    tube(builder, [neck[-1], neck[-1] + Vector((0.0, 0.32 * s, -0.28 * s))], [0.11 * s, 0.07 * s], color, 5)
    tube(builder, [neck[0] + Vector((0.0, 0.1 * s, 0.25 * s)), neck[-1] + Vector((0.0, -0.05 * s, 0.1 * s))],
         [0.05 * s, 0.05 * s], dark, 3)
    for front in (-1, 1):
        for side in (-1, 1):
            top = Vector((side * 0.15 * s, front * 0.55 * s, body_z - 0.1 * s))
            knee = Vector((side * 0.15 * s, front * 0.58 * s, 0.45 * s))
            hoof = Vector((side * 0.15 * s, front * 0.56 * s, 0.0))
            tube(builder, [top, knee, hoof], [0.1 * s, 0.055 * s, 0.05 * s], color, 4, cap=False)
            box(builder, (hoof.x, hoof.y, 0.04 * s), (0.1 * s, 0.12 * s, 0.08 * s), dark)
    tail = Vector((0.0, -0.82 * s, body_z + 0.15 * s))
    tube(builder, [tail, tail + Vector((0.0, -0.15 * s, -0.35 * s)), tail + Vector((0.0, -0.12 * s, -0.75 * s))],
         [0.05 * s, 0.07 * s, 0.03 * s], dark, 4)
    return body_z + 0.33 * s


def rider(builder, seat, tunic, torso, skin, head_gear, right_hand_offset, shield):
    seat = Vector((0.0, 0.0, seat))
    for side in (-1, 1):
        hip = seat + Vector((side * 0.12, 0.05, 0.05))
        knee = seat + Vector((side * 0.3, 0.3, -0.28))
        ankle = seat + Vector((side * 0.3, 0.12, -0.72))
        tube(builder, [hip, knee], [0.07, 0.055], tunic, 5, cap=False)
        tube(builder, [knee, ankle], [0.055, 0.045], skin, 5)
    tube(builder, [seat + Vector((0.0, 0.0, 0.0)), seat + Vector((0.0, 0.0, 0.22)), seat + Vector((0.0, 0.03, 0.5))],
         [0.17, 0.16, 0.19], torso, 7, squash=0.62)
    tube(builder, [seat + Vector((0.0, 0.0, 0.08)), seat + Vector((0.0, 0.0, -0.12))], [0.18, 0.22], tunic, 7,
         cap=False, squash=0.8)
    tube(builder, [seat + Vector((0.0, 0.03, 0.5)), seat + Vector((0.0, 0.03, 0.58))], [0.05, 0.05], skin, 5, cap=False)
    shoulder_z = seat.z + 0.46
    arms(builder, tunic, skin, (0.27, 0.3 + right_hand_offset[0], shoulder_z - 0.3 + right_hand_offset[1]),
         (-0.2, 0.3, shoulder_z - 0.3))
    centre = (0.0, 0.03, seat.z + 0.68)
    head(builder, centre, skin, hair=(0.16, 0.11, 0.08) if head_gear is None else None)
    if head_gear == "montefortino":
        montefortino(builder, centre, plumes=True)
    elif head_gear == "helmet":
        montefortino(builder, centre, plumes=False)
    shield(builder, shoulder_z)
    return shoulder_z


def cavalry(kind):
    builder = MeshBuilder()
    if kind == "eques":
        seat = horse(builder, 1.0, HORSE_BAY, cloth=WOOL_RED)
        shoulder = rider(builder, seat, WOOL_RED, BRONZE, SKIN, "montefortino", (0.0, 0.0),
                         lambda b, z: round_shield(b, (-0.3, 0.3, z - 0.3), 0.6, (0.55, 0.30, 0.20)))
        shaft(builder, (0.27, -0.6, shoulder - 0.4), (0.27, 1.6, shoulder - 0.1), 0.017, WOOD, 0.2)
    elif kind == "cavalier":
        seat = horse(builder, 1.0, HORSE_DUN, cloth=(0.30, 0.24, 0.20))
        shoulder = rider(builder, seat, LINEN_WHITE, MAIL, SKIN, "helmet", (0.0, 0.0),
                         lambda b, z: flat_oval(b, (-0.28, 0.32, z - 0.3), (0.55, 0.45, 0.30), 0.5, 0.85))
        shaft(builder, (0.27, -0.5, shoulder - 0.4), (0.27, 1.7, shoulder + 0.1), 0.017, WOOD, 0.22)
    else:
        seat = horse(builder, 0.86, HORSE_BAY)
        shoulder = rider(builder, seat, (0.72, 0.62, 0.46), (0.72, 0.62, 0.46), DARK_SKIN, None, (-0.15, 0.4),
                         lambda b, z: round_shield(b, (-0.3, 0.3, z - 0.3), 0.5, LEATHER))
        for offset in (0.0, 0.05):
            shaft(builder, (0.27 + offset, -0.3, shoulder + 0.3), (0.27 + offset, 0.7, shoulder + 0.15), 0.011, WOOD,
                  0.14)
    return builder


def far_infantry(tunic, torso, shield, head_color, shield_width=0.6, spear=True):
    builder = MeshBuilder()
    box(builder, (0.0, 0.0, 0.47), (0.32, 0.22, 0.94), tunic)
    box(builder, (0.0, 0.0, 1.2), (0.38, 0.24, 0.52), torso)
    box(builder, (0.0, 0.0, 1.62), (0.22, 0.24, 0.26), head_color)
    if shield is not None:
        box(builder, (-0.15, 0.25, 0.98), (shield_width, 0.06, 1.0), shield)
    if spear:
        box(builder, (0.27, 0.3, 1.3), (0.04, 0.04, 1.9), WOOD)
    return builder


def far_cavalry(horse_color, tunic, head_color, scale=1.0):
    s = scale
    builder = MeshBuilder()
    box(builder, (0.0, 0.0, 1.12 * s), (0.5 * s, 1.6 * s, 0.6 * s), horse_color)
    box(builder, (0.0, 0.5 * s, 0.42 * s), (0.36 * s, 0.24 * s, 0.84 * s), horse_color)
    box(builder, (0.0, -0.5 * s, 0.42 * s), (0.36 * s, 0.24 * s, 0.84 * s), horse_color)
    box(builder, (0.0, 0.95 * s, 1.6 * s), (0.22 * s, 0.5 * s, 0.6 * s), horse_color)
    box(builder, (0.0, 0.0, 1.45 * s + 0.4), (0.4, 0.3, 0.7), tunic)
    box(builder, (0.0, 0.03, 1.45 * s + 0.88), (0.22, 0.24, 0.26), head_color)
    return builder


TROOPS = {
    "hastatus": (lambda: legionary("hastatus"), lambda: far_infantry(WOOL_RED, WOOL_RED, (0.58, 0.27, 0.18), BRONZE)),
    "princeps": (lambda: legionary("princeps"), lambda: far_infantry(WOOL_RED, MAIL, (0.52, 0.30, 0.20), BRONZE)),
    "triarius": (lambda: legionary("triarius"), lambda: far_infantry(WOOL_RED, MAIL, (0.45, 0.26, 0.18), BRONZE)),
    "velite": (velite, lambda: far_infantry(WOOL_UNDYED, WOOL_UNDYED, (0.55, 0.42, 0.28), WOLF, 0.5)),
    "eques": (lambda: cavalry("eques"), lambda: far_cavalry(HORSE_BAY, WOOL_RED, BRONZE)),
    "libyen": (libyan, lambda: far_infantry(WOOL_UNDYED, MAIL, (0.66, 0.55, 0.38), BRONZE)),
    "celte": (celt, lambda: far_infantry((0.36, 0.42, 0.30), SKIN, (0.30, 0.42, 0.30), (0.62, 0.42, 0.20), 0.55,
                                         spear=False)),
    "ibere": (iberian, lambda: far_infantry(LINEN_WHITE, LINEN_WHITE, (0.62, 0.50, 0.34), (0.24, 0.18, 0.13), 0.55,
                                            spear=False)),
    "frondeur": (slinger, lambda: far_infantry((0.66, 0.60, 0.48), (0.66, 0.60, 0.48), None, (0.16, 0.11, 0.08),
                                               spear=False)),
    "lonchophore": (lonchophore, lambda: far_infantry((0.70, 0.58, 0.40), (0.70, 0.58, 0.40), (0.42, 0.30, 0.20),
                                                      (0.18, 0.12, 0.08), 0.5)),
    "numide": (lambda: cavalry("numide"), lambda: far_cavalry(HORSE_BAY, (0.72, 0.62, 0.46), (0.16, 0.11, 0.08), 0.86)),
    "cavalier": (lambda: cavalry("cavalier"), lambda: far_cavalry(HORSE_DUN, MAIL, BRONZE)),
}
