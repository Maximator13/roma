import math
import random

import numpy as np

from mathutils import Matrix, Vector

from .geometry import MeshBuilder, newell_normal

SKIN = [(0.78, 0.58, 0.45), (0.70, 0.50, 0.37), (0.60, 0.42, 0.31)]
HAIR = [(0.16, 0.11, 0.08), (0.30, 0.20, 0.12), (0.46, 0.42, 0.38), (0.10, 0.08, 0.07)]
WOOL = {
    "undyed": (0.78, 0.73, 0.62), "white": (0.92, 0.90, 0.85), "ochre": (0.72, 0.55, 0.32),
    "madder": (0.62, 0.27, 0.19), "brown": (0.44, 0.33, 0.22), "weld": (0.78, 0.69, 0.40),
    "woad": (0.40, 0.47, 0.57), "green": (0.46, 0.49, 0.33), "grey": (0.54, 0.51, 0.47),
    "dark": (0.28, 0.24, 0.21), "rose": (0.72, 0.49, 0.43), "russet": (0.55, 0.36, 0.24),
}
LEATHER = (0.30, 0.21, 0.14)
WOOD = (0.44, 0.32, 0.21)
CLOTH = "matte"
SKIN_MATERIAL = "matte"
MATTE = "matte"
EXTRA = [0]


def axis_matrix(start, end):
    start = Vector(start)
    direction = Vector(end) - start
    rotation = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    return Matrix.Translation(start) @ rotation, direction.length


def tinted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def tube(builder, start, end, r0, r1, colour, material=MATTE, segments=6, caps=True):
    segments += EXTRA[0]
    matrix, length = axis_matrix(start, end)
    profile = [(0.0, -r0 * 0.4), (r0, 0.0), (r1, length), (0.0, length + r1 * 0.4)] if caps else [(r0, 0.0),
                                                                                                    (r1, length)]
    tinted(builder, colour, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=matrix, caps=False))


def blob(builder, centre, radii, colour, material=MATTE, segments=7, rings=5, matrix=None, wobble=0.0, seed=0):
    rx, ry, rz = radii
    segments += EXTRA[0]
    generator = random.Random(seed)
    bumps = [1.0 + (wobble * 1.2 * generator.uniform(-1, 1) if 0 < k < rings else 0.0) for k in range(rings + 1)]
    profile = [(math.sin(math.pi * k / rings) * bumps[k], -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    phase = generator.uniform(0, 6.28)
    second = generator.uniform(0, 6.28)
    transform = Matrix.Translation(centre) @ Matrix.Diagonal((rx, ry, rz, 1.0))
    if matrix is not None:
        transform = matrix @ transform
    scale = (lambda angle: 1.0 + wobble * (0.65 * math.sin(3 * angle + phase) + 0.45 * math.sin(5 * angle + second))
             ) if wobble else None
    tinted(builder, colour, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=transform,
                                                  radius_scale=scale, caps=False))


def shell(builder, profile, colour, material=CLOTH, segments=10, start=0.0, sweep=2 * math.pi, squash=0.72,
          folds=0.0, fold_count=9, matrix=None, lift=0.0):
    segments += 2 * EXTRA[0]
    transform = Matrix.Translation((0.0, 0.0, lift)) @ Matrix.Diagonal((1.0, squash, 1.0, 1.0))
    if matrix is not None:
        transform = matrix @ transform
    scale = (lambda angle: 1.0 + folds * math.sin(fold_count * angle)) if folds else None
    tinted(builder, colour, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=transform,
                                                  start=start, sweep=sweep, radius_scale=scale,
                                                  caps=abs(sweep - 2 * math.pi) < 1e-6))


class Person:
    def __init__(self, tunic="undyed", hem=0.52, skin=0, hair=0, stride=0.0, arms="down", cloak=None, hood=False,
                 hat=None, veil=None, palla=None, braccae=None, belt=None, carry=None, scale=1.0, female=False,
                 bun=False, beard=False, kneel=False, seed=0, hood_colour="brown", roll=None, rope=None):
        self.tunic = tunic
        self.hem = hem
        self.skin = skin
        self.hair = hair
        self.stride = stride
        self.arms = arms
        self.cloak = cloak
        self.hood = hood
        self.hat = hat
        self.veil = veil
        self.palla = palla
        self.braccae = braccae
        self.belt = belt
        self.carry = carry
        self.scale = scale
        self.female = female
        self.bun = bun
        self.beard = beard
        self.kneel = kneel
        self.seed = seed
        self.hood_colour = hood_colour
        self.roll = roll
        self.rope = rope


def wool(value):
    return WOOL[value] if isinstance(value, str) else value


def limb(builder, start, end, radii, colour, material=MATTE, segments=7):
    matrix, length = axis_matrix(start, end)
    count = len(radii) - 1
    profile = [(radius, length * k / count) for k, radius in enumerate(radii)]
    tinted(builder, colour, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=matrix,
                                                  caps=False))


def legs(builder, spec, skin):
    stride = spec.stride
    lower = wool(spec.braccae) if spec.braccae else skin
    for side in (-1, 1):
        if spec.kneel:
            if side < 0:
                knee = (side * 0.1, 0.32, 0.5)
                foot = (side * 0.1, 0.36, 0.06)
            else:
                knee = (side * 0.1, 0.0, 0.08)
                foot = (side * 0.1, -0.42, 0.08)
            hip = (side * 0.1, 0.0, 0.52 if side < 0 else 0.5)
        else:
            swing = side * stride
            foot = (side * 0.095, swing, 0.07)
            knee = (side * 0.1, swing * 0.55 + 0.025, 0.5)
            hip = (side * 0.105, 0.0, 0.92)
        limb(builder, foot, knee, (0.036, 0.047, 0.056, 0.048), lower, MATTE, 7)
        if spec.kneel or spec.braccae or spec.hem > 0.5:
            limb(builder, knee, hip, (0.05, 0.068, 0.085), lower, MATTE, 6)
        heel = Vector(foot) + Vector((0.0, -0.06, -0.05))
        toe = Vector(foot) + Vector((0.0, 0.16, -0.048))
        if spec.kneel and side > 0:
            heel = Vector(foot) + Vector((0.0, 0.04, -0.04))
            toe = Vector(foot) + Vector((0.0, -0.18, -0.05))
        tube(builder, heel, toe, 0.044, 0.038, LEATHER, MATTE, 5)


def kneeling(spec):
    return spec.kneel and spec.female


def garment(builder, spec, upper=None):
    upper = upper or builder
    colour = wool(spec.tunic)
    lift = (-0.52 if kneeling(spec) else -0.4) if spec.kneel else 0.0
    hem = spec.hem + lift
    flare = 0.26 if spec.female else 0.225
    if spec.kneel:
        hem = 0.1
        flare = 0.3
    waist = 1.0 + lift
    span = waist - hem
    skirt = [(flare, hem), (flare * 0.985, hem + 0.05), (flare * 0.93, hem + span * 0.35),
             (0.205, hem + span * 0.72), (0.19, waist - 0.02), (0.176, waist + 0.03)]
    if kneeling(spec):
        skirt = [(0.3, 0.0), (0.31, 0.05), (0.28, 0.17), (0.22, 0.32), (0.19, waist - 0.02), (0.176, waist + 0.03)]
        shear = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, -0.3, 0.3 * waist), (0.0, 0.0, 1.0, 0.0),
                        (0.0, 0.0, 0.0, 1.0)))
        shell(builder, skirt, colour, segments=16, folds=0.06, fold_count=5, squash=0.82, matrix=shear)
    else:
        shell(builder, skirt, colour, segments=16, folds=0.07, fold_count=4, squash=0.72)
    chest = 0.2 if spec.female else 0.212
    top = 1.0 + lift
    torso = [(0.176, top), (0.198, top + 0.06), (chest - 0.004, top + 0.16), (chest + 0.008, top + 0.3),
             (0.212, top + 0.38), (0.17, top + 0.44), (0.065, top + 0.485)]
    shell(upper, torso, colour, segments=14, squash=0.64)
    if spec.belt:
        shell(upper, [(0.18, top - 0.01), (0.186, top + 0.025), (0.18, top + 0.055)], wool(spec.belt), MATTE, 8,
              squash=0.68)
    return lift


def kneeling_legs(builder, skin):
    for side in (-1, 1):
        hip = (side * 0.1, 0.02, 0.4)
        knee = (side * 0.11, 0.36, 0.07)
        ankle = (side * 0.1, -0.12, 0.06)
        limb(builder, hip, knee, (0.085, 0.075, 0.058), skin, MATTE, 6)
        limb(builder, knee, ankle, (0.056, 0.05, 0.036), skin, MATTE, 6)
        tube(builder, Vector(ankle) + Vector((0.0, 0.04, -0.02)), Vector(ankle) + Vector((0.0, -0.16, -0.035)),
             0.04, 0.034, LEATHER, MATTE, 5)


def head(builder, spec, skin, lift):
    hair = HAIR[spec.hair]
    base = 1.49 + lift
    limb(builder, (0.0, -0.005, base - 0.04), (0.0, 0.012, base + 0.08), (0.05, 0.046, 0.045), skin, MATTE, 7)
    origin = base + 0.03
    skull = [(0.0, 0.0), (0.042, 0.008), (0.074, 0.05), (0.091, 0.11), (0.09, 0.17), (0.062, 0.215), (0.0, 0.236)]
    matrix = Matrix.Translation((0.0, 0.018, origin)) @ Matrix.Diagonal((0.82, 1.0, 1.0, 1.0))
    tinted(builder, skin, lambda: builder.lathe(skull, 12, SKIN_MATERIAL, smooth=True, matrix=matrix,
                                                radius_scale=lambda angle: 1.0 + 0.06 * math.sin(angle), caps=False))
    tube(builder, (0.0, 0.105, origin + 0.13), (0.0, 0.123, origin + 0.088), 0.017, 0.013, skin, SKIN_MATERIAL, 4)
    for side in (-1, 1):
        blob(builder, (side * 0.078, 0.01, origin + 0.115), (0.014, 0.024, 0.03), skin, SKIN_MATERIAL, 5, 2)
    if spec.beard:
        blob(builder, (0.0, 0.058, origin + 0.05), (0.072, 0.056, 0.058), hair, MATTE, 7, 4, wobble=0.12,
             seed=spec.seed + 5)
    covered = spec.hood is True or spec.veil is not None or spec.hat == "cap"
    if not covered:
        curls = lambda angle: 1.0 + 0.05 * math.sin(11 * angle) + 0.03 * math.sin(5 * angle + 1.0)
        nape = 0.03 if spec.female else 0.07
        cap = [(0.072, nape), (0.098, nape + 0.04), (0.104, 0.12), (0.1, 0.17), (0.08, 0.212), (0.044, 0.238),
               (0.0, 0.248)]
        hair_matrix = Matrix.Translation((0.0, 0.012, origin)) @ Matrix.Diagonal((0.86, 1.04, 1.0, 1.0))
        tinted(builder, hair, lambda: builder.lathe(cap, 10, MATTE, smooth=True, matrix=hair_matrix,
                                                    radius_scale=curls, start=math.radians(135),
                                                    sweep=math.radians(270), caps=False))
        fringe = [(0.096, 0.165), (0.1, 0.19), (0.07, 0.225), (0.0, 0.248)]
        tinted(builder, hair, lambda: builder.lathe(fringe, 6, MATTE, smooth=True, matrix=hair_matrix,
                                                    radius_scale=curls, start=math.radians(40),
                                                    sweep=math.radians(100), caps=False))
        if spec.bun:
            blob(builder, (0.0, -0.1, origin + 0.17), (0.055, 0.045, 0.05), hair, MATTE, 6, 4, wobble=0.1,
                 seed=spec.seed + 3)
    if spec.hood == "down":
        hood_colour = wool(spec.hood_colour)
        collar = [(0.07, 1.47 + lift - base), (0.17, 1.43 + lift - base), (0.235, 1.36 + lift - base),
                  (0.25, 1.27 + lift - base), (0.2, 1.22 + lift - base)]
        tinted(builder, hood_colour, lambda: builder.lathe(collar, 12, CLOTH, smooth=True,
                                                           matrix=Matrix.Translation((0.0, 0.0, base))
                                                           @ Matrix.Diagonal((1.0, 0.72, 1.0, 1.0)),
                                                           radius_scale=lambda angle: 1.0 + 0.05 * math.sin(7 * angle),
                                                           caps=False))
        fold = [(0.12, 1.42 + lift - base), (0.14, 1.36 + lift - base), (0.1, 1.24 + lift - base),
                (0.0, 1.15 + lift - base)]
        tinted(builder, hood_colour, lambda: builder.lathe(fold, 7, CLOTH, smooth=True,
                                                           matrix=Matrix.Translation((0.0, -0.13, base))
                                                           @ Matrix.Diagonal((1.0, 0.45, 1.0, 1.0)),
                                                           start=math.radians(180), sweep=math.radians(180),
                                                           caps=False))
    elif spec.hood:
        hood_colour = wool(spec.cloak or "brown")
        hood = [(0.13, -0.02), (0.128, 0.08), (0.116, 0.17), (0.07, 0.25), (0.0, 0.29)]
        hood_matrix = Matrix.Translation((0.0, -0.015, origin))
        tinted(builder, hood_colour, lambda: builder.lathe(hood, 10, CLOTH, smooth=True, matrix=hood_matrix,
                                                           start=math.radians(125), sweep=math.radians(290),
                                                           caps=False))
    if spec.veil is not None:
        veil_colour = wool(spec.veil)
        veil = [(0.16, -0.12), (0.13, -0.02), (0.118, 0.08), (0.112, 0.15), (0.075, 0.222), (0.0, 0.25)]
        veil_matrix = Matrix.Translation((0.0, -0.01, origin)) @ Matrix.Diagonal((0.95, 1.0, 1.0, 1.0))
        tinted(builder, veil_colour, lambda: builder.lathe(veil, 11, CLOTH, smooth=True, matrix=veil_matrix,
                                                           radius_scale=lambda angle: 1.0 + 0.045 * math.sin(9 * angle),
                                                           start=math.radians(130), sweep=math.radians(280),
                                                           caps=False))
    if spec.hat == "petasus":
        brim = [(0.0, 0.0), (0.2, 0.0), (0.215, 0.012), (0.12, 0.028), (0.09, 0.05), (0.082, 0.095), (0.0, 0.112)]
        hat_matrix = Matrix.Translation((0.0, 0.01, origin + 0.17)) @ Matrix.Rotation(math.radians(-6), 4, "X")
        tinted(builder, (0.62, 0.52, 0.34), lambda: builder.lathe(brim, 12, MATTE, smooth=True, matrix=hat_matrix,
                                                                caps=False))
    if spec.hat == "cap":
        felt = [(0.0, -0.01), (0.104, 0.02), (0.104, 0.09), (0.08, 0.16), (0.04, 0.2), (0.0, 0.21)]
        felt_matrix = Matrix.Translation((0.0, 0.012, origin + 0.08))
        tinted(builder, (0.5, 0.4, 0.28), lambda: builder.lathe(felt, 10, CLOTH, smooth=True, matrix=felt_matrix,
                                                              caps=False))


ARM_POSES = {
    "down": ((0.235, 0.02, 1.13), (0.25, 0.07, 0.88)),
    "swing": ((0.23, 0.1, 1.14), (0.24, 0.2, 0.92)),
    "forward": ((0.24, 0.12, 1.16), (0.2, 0.38, 1.12)),
    "staff": ((0.25, 0.12, 1.15), (0.25, 0.3, 1.18)),
    "carry": ((0.27, 0.0, 1.5), (0.2, 0.0, 1.66)),
    "basket": ((0.25, 0.1, 1.1), (0.22, 0.25, 1.02)),
    "pole": ((0.25, 0.18, 1.3), (0.2, 0.42, 1.5)),
    "rod": ((0.22, 0.2, 1.18), (0.12, 0.42, 1.25)),
    "lever": ((0.22, 0.2, 1.1), (0.12, 0.35, 0.95)),
    "hip": ((0.3, -0.05, 1.12), (0.2, 0.02, 1.0)),
    "lead": ((0.24, 0.08, 1.14), (0.27, 0.27, 1.0)),
    "talk": ((0.25, 0.12, 1.12), (0.2, 0.32, 1.2)),
    "dig": ((0.18, 0.25, 1.15), (0.08, 0.42, 0.95)),
    "wash": ((0.22, 0.25, 1.15), (0.14, 0.5, 0.82)),
}


def hand(builder, wrist, direction, side, skin):
    across = direction.cross(Vector((0.0, 0.0, 1.0)))
    if across.length < 1e-3:
        across = Vector((1.0, 0.0, 0.0))
    across.normalize()
    matrix, _ = axis_matrix(wrist, wrist + direction * 0.09)
    blob(builder, Vector((0.0, 0.0, 0.05)), (0.036, 0.02, 0.058), skin, SKIN_MATERIAL, 6, 3, matrix=matrix)
    root = wrist + direction * 0.03 + across * side * 0.026
    tube(builder, root, root + direction * 0.045 + across * side * 0.012, 0.011, 0.009, skin, SKIN_MATERIAL, 3)
    return wrist + direction * 0.07


def arms(builder, spec, skin, lift):
    sleeve = wool(spec.tunic)
    pose = ARM_POSES[spec.arms]
    hands = []
    for side in (-1, 1):
        elbow, wrist = pose
        if spec.arms == "swing":
            elbow = (elbow[0], -side * elbow[1], elbow[2])
            wrist = (wrist[0], -side * wrist[1], wrist[2])
        elif spec.arms in ("staff", "carry", "basket", "lead", "talk") and side < 0:
            elbow, wrist = ARM_POSES["down"]
        shoulder = Vector((side * 0.19, 0.0, 1.385 + lift))
        elbow = Vector((side * elbow[0], elbow[1], elbow[2] + lift))
        wrist = Vector((side * wrist[0], wrist[1], wrist[2] + lift))
        cuff = shoulder + (elbow - shoulder) * 0.62
        limb(builder, shoulder - (elbow - shoulder) * 0.12 - Vector((side * 0.03, 0.0, 0.0)), cuff,
             (0.05, 0.07, 0.072, 0.078), sleeve, CLOTH, 8)
        limb(builder, shoulder + (elbow - shoulder) * 0.4, elbow, (0.047, 0.045, 0.041), skin, SKIN_MATERIAL, 7)
        limb(builder, elbow, wrist, (0.041, 0.042, 0.034, 0.029), skin, SKIN_MATERIAL, 7)
        hands.append(hand(builder, wrist, (wrist - elbow).normalized(), side, skin))
    return hands


def overgarments(builder, spec, lift):
    if spec.cloak is not None:
        colour = wool(spec.cloak)
        bottom = max(spec.hem + 0.06, 0.62) + lift
        profile = [(0.075, 1.5 + lift), (0.2, 1.43 + lift), (0.235, 1.3 + lift), (0.26, 1.0 + lift),
                   (0.285, bottom)]
        shell(builder, profile, colour, CLOTH, 16, start=math.radians(112), sweep=math.radians(316), squash=0.78,
              folds=0.05, fold_count=4)
    if spec.palla is not None:
        colour = wool(spec.palla)
        profile = [(0.09, 1.47 + lift), (0.215, 1.38 + lift), (0.235, 1.1 + lift), (0.255, 0.7 + lift),
                   (0.265, 0.5 + lift)]
        shell(builder, profile, colour, CLOTH, 16, start=math.radians(120), sweep=math.radians(250), squash=0.78,
              folds=0.06, fold_count=5)


def props(builder, spec, hands, lift):
    right = hands[1]
    if spec.carry == "staff":
        tube(builder, (right.x + 0.02, right.y + 0.05, 0.0), (right.x - 0.02, right.y - 0.02, 1.62 + lift), 0.018,
             0.016, WOOD, MATTE, 5, caps=False)
    elif spec.carry == "crook":
        top = Vector((right.x - 0.01, right.y, 1.7 + lift))
        tube(builder, (right.x + 0.03, right.y + 0.06, 0.0), top, 0.018, 0.016, WOOD, MATTE, 5, caps=False)
        tube(builder, top, top + Vector((0.0, 0.1, 0.06)), 0.016, 0.014, WOOD, MATTE, 4)
    elif spec.carry == "basket":
        shell(builder, [(0.12, 0.0), (0.16, 0.2), (0.165, 0.22)], (0.6, 0.48, 0.3), MATTE, 8, squash=1.0,
              matrix=Matrix.Translation((right.x, right.y + 0.05, right.z - 0.3)))
    elif spec.carry == "jar":
        shell(builder, [(0.05, 0.0), (0.13, 0.08), (0.12, 0.25), (0.05, 0.31), (0.045, 0.36)], (0.70, 0.42, 0.28),
              MATTE, 8, squash=1.0, matrix=Matrix.Translation((0.0, 0.0, 1.73 + lift)))
    elif spec.carry == "pick":
        a = Vector((0.22, -0.18, 1.48 + lift))
        b = Vector((0.18, 0.5, 1.6 + lift))
        tube(builder, a, b, 0.018, 0.018, WOOD, MATTE, 5, caps=False)
        tube(builder, b + Vector((0.0, 0.0, -0.12)), b + Vector((0.0, 0.03, 0.14)), 0.02, 0.012, (0.3, 0.3, 0.32),
             MATTE, 4)
    elif spec.carry == "pole":
        tube(builder, (0.12, 0.85, -0.6), (0.28, -0.1, 2.6), 0.025, 0.02, WOOD, MATTE, 5, caps=False)
    elif spec.carry == "probe":
        tube(builder, (0.1, 0.95, -1.3 + lift), (0.24, 0.12, 1.5 + lift), 0.022, 0.018, WOOD, MATTE, 5, caps=False)
    elif spec.carry == "rod":
        tip = Vector((0.05, 2.6, 2.2 + lift))
        tube(builder, right, tip, 0.016, 0.008, WOOD, MATTE, 4, caps=False)
        tube(builder, tip, tip + Vector((0.0, 0.3, -2.0)), 0.003, 0.003, (0.8, 0.8, 0.75), MATTE, 3, caps=False)
    elif spec.carry == "shovel":
        top = Vector((right.x + 0.02, right.y + 0.05, right.z + 0.35))
        blade = Vector((right.x - 0.05, right.y + 0.32, 0.12))
        tube(builder, top, blade, 0.018, 0.017, WOOD, MATTE, 5, caps=False)
        matrix, _ = axis_matrix(blade, blade + (blade - top).normalized() * 0.3)
        tinted(builder, (0.5, 0.4, 0.28), lambda: builder.box((-0.11, -0.012, 0.0), (0.11, 0.012, 0.3), MATTE,
                                                              matrix=matrix))
    elif spec.carry == "hoop":
        hoop = Matrix.Translation((right.x + 0.12, right.y + 0.32, 0.3)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        tinted(builder, (0.42, 0.32, 0.22), lambda: builder.lathe(
            [(0.29, -0.015), (0.3, 0.0), (0.29, 0.015), (0.28, 0.0)], 14, MATTE, smooth=True, matrix=hoop,
            caps=False))
        tube(builder, right, Vector((right.x + 0.1, right.y + 0.36, 0.42)), 0.01, 0.008, WOOD, MATTE, 4, caps=False)
    elif spec.carry == "net":
        shell(builder, [(0.03, 0.0), (0.12, -0.25), (0.22, -0.55), (0.26, -0.62)], (0.6, 0.57, 0.46), MATTE, 12,
              squash=0.8, folds=0.08, fold_count=3, matrix=Matrix.Translation((right.x, right.y + 0.12, right.z)))
    elif spec.carry == "sack":
        blob(builder, Vector((0.2, -0.03, 1.62 + lift)), (0.15, 0.17, 0.26), (0.6, 0.53, 0.38), CLOTH, 12, 6,
             wobble=0.15, seed=spec.seed + 4)
    elif spec.carry == "cloth":
        blob(builder, Vector((right.x - 0.12, right.y + 0.18, 0.03)), (0.24, 0.16, 0.035),
             (0.9, 0.88, 0.8), CLOTH, 7, 3, wobble=0.25, seed=spec.seed + 2)
    elif spec.carry == "bundle":
        tube(builder, (-0.14, -0.2, 1.2 + lift), (0.14, -0.2, 1.2 + lift), 0.15, 0.15, (0.6, 0.53, 0.4), CLOTH, 7)
    if spec.roll is not None:
        tube(builder, (-0.2, -0.12, 1.42 + lift), (0.17, -0.15, 1.0 + lift), 0.075, 0.07, wool(spec.roll), CLOTH, 7)
    if spec.rope is not None:
        sag = (right + Vector(spec.rope)) / 2 + Vector((0.0, 0.0, -0.18))
        tube(builder, right, sag, 0.012, 0.012, (0.55, 0.47, 0.33), MATTE, 4, caps=False)
        tube(builder, sag, Vector(spec.rope), 0.012, 0.012, (0.55, 0.47, 0.33), MATTE, 4, caps=False)


def person(spec):
    EXTRA[0] = 0
    builder = MeshBuilder()
    skin = SKIN[spec.skin]
    if kneeling(spec):
        kneeling_legs(builder, skin)
    elif not spec.female:
        legs(builder, spec, skin)
    else:
        for side in (-1, 1):
            tube(builder, (side * 0.09, side * spec.stride - 0.04, 0.025), (side * 0.09, side * spec.stride + 0.13,
                                                                              0.025), 0.04, 0.035, LEATHER, MATTE, 5)
    upper = MeshBuilder() if kneeling(spec) else builder
    lift = garment(builder, spec, upper)
    overgarments(upper, spec, lift)
    head(upper, spec, skin, lift)
    hands = arms(upper, spec, skin, lift)
    if kneeling(spec):
        lean = (Matrix.Translation((0.0, 0.0, 0.45)) @ Matrix.Rotation(math.radians(-28), 4, "X")
                @ Matrix.Translation((0.0, 0.0, -0.45)))
        builder.merge(upper, lean)
        hands = [lean @ point for point in hands]
    props(builder, spec, hands, lift)
    EXTRA[0] = 0
    if spec.scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(spec.scale, 4))
        return scaled
    return builder


WALKERS = {
    "walker_traveller": Person("ochre", 0.5, 1, 0, stride=0.2, arms="staff", hat="petasus", carry="staff",
                               beard=True, roll="brown", belt=LEATHER),
    "walker_herder": Person("undyed", 0.55, 2, 1, stride=0.22, arms="staff", hood="down", hood_colour="russet",
                            braccae="brown", belt="dark", carry="crook"),
    "walker_woman": Person("madder", 0.05, 0, 1, stride=0.12, arms="basket", palla="undyed", veil="undyed",
                           female=True, carry="basket"),
    "walker_worker": Person("brown", 0.52, 2, 3, stride=0.2, arms="swing", belt=LEATHER, hat="cap", carry="pick",
                            braccae="dark"),
    "walker_girl": Person("weld", 0.08, 1, 1, stride=0.12, arms="carry", female=True, bun=True, carry="jar",
                          palla="green", scale=0.8),
    "walker_porter": Person("russet", 0.5, 1, 1, stride=0.2, arms="carry", belt="dark", carry="sack", hat="cap",
                            braccae="brown", seed=7),
}

FIGURES = {
    "fig_shepherd": Person("undyed", 0.55, 2, 2, arms="staff", hood="down", hood_colour="brown", braccae="dark",
                           carry="crook", beard=True),
    "fig_keeper": Person("grey", 0.52, 1, 0, arms="lever", belt="brown", hat="cap", beard=True),
    "fig_mason": Person("ochre", 0.52, 2, 1, arms="hip", belt=LEATHER, braccae="brown"),
    "fig_kneeler": Person("brown", 0.5, 0, 3, arms="lever", belt=LEATHER, carry="probe", hat="cap", kneel=True),
    "fig_boatman": Person("russet", 0.5, 2, 1, arms="pole", hat="petasus", carry="pole", braccae="dark"),
    "fig_fisher": Person("undyed", 0.5, 1, 2, arms="rod", hat="cap", carry="rod", beard=True),
    "fig_muleteer": Person("brown", 0.52, 2, 0, stride=0.18, arms="lead", hood="down", hood_colour="dark",
                           braccae="brown", rope=(0.8, 0.32, 1.12)),
    "fig_drover": Person("undyed", 0.52, 1, 2, stride=0.16, arms="staff", carry="staff", hat="petasus",
                         belt="dark", beard=True),
    "fig_woman": Person("woad", 0.05, 0, 1, arms="down", palla="rose", veil="rose", female=True),
    "fig_child": Person("white", 0.45, 1, 1, arms="swing", scale=0.68, belt="madder"),
}


FIGURES.update({
    "fig_talker_a": Person("ochre", 0.5, 1, 1, arms="talk", hat="petasus", belt="dark", beard=True, roll="brown",
                           seed=11),
    "fig_talker_b": Person("woad", 0.52, 2, 0, arms="hip", cloak="brown", braccae="dark", seed=12),
    "fig_talker_c": Person("undyed", 0.55, 0, 2, arms="staff", carry="staff", hood="down", hood_colour="green",
                           beard=True, seed=13),
    "fig_digger": Person("brown", 0.5, 2, 3, arms="dig", belt=LEATHER, braccae="dark", carry="shovel", seed=14),
    "fig_porter": Person("undyed", 0.5, 1, 0, arms="carry", belt="brown", carry="sack", hat="cap", seed=15),
    "fig_washer": Person("rose", 0.05, 0, 1, arms="wash", female=True, kneel=True, veil="undyed", carry="cloth",
                         seed=16),
    "fig_seller": Person("green", 0.05, 1, 2, arms="talk", palla="weld", female=True, bun=True, seed=17),
    "fig_netter": Person("russet", 0.5, 2, 3, arms="rod", hat="cap", carry="net", braccae="brown", seed=18),
    "fig_child_hoop": Person("weld", 0.42, 0, 1, stride=0.22, arms="lead", scale=0.66, carry="hoop", seed=19),
    "fig_child_run": Person("madder", 0.42, 1, 0, stride=0.28, arms="swing", scale=0.62, seed=20),
    "fig_girl": Person("white", 0.08, 0, 3, arms="basket", female=True, bun=True, carry="basket", scale=0.78,
                       palla="rose", seed=21),
})


def animal_body(builder, length, height, girth, colour, neck, head_size, ears, horns=0.0, tail=0.25, seed=0):
    half = length / 2
    body_z = height + girth * 0.42
    dark = tuple(c * 0.72 for c in colour)
    trunk_profile = [(0.0, -half * 1.02), (girth * 0.3, -half * 0.96), (girth * 0.46, -half * 0.72),
                     (girth * 0.5, -half * 0.25), (girth * 0.47, half * 0.25), (girth * 0.45, half * 0.66),
                     (girth * 0.32, half * 0.95), (0.0, half * 1.02)]
    along = (Matrix.Translation((0.0, 0.0, body_z)) @ Matrix.Diagonal((0.9, 1.0, 1.0, 1.0))
             @ Matrix.Rotation(math.radians(-90), 4, "X"))
    tinted(builder, colour, lambda: builder.lathe(trunk_profile, 10, MATTE, smooth=True, matrix=along,
                                                  radius_scale=lambda a: 1.0 + 0.06 * math.sin(a), caps=False))
    shoulder = Vector((0.0, half * 0.72, body_z + girth * 0.16))
    neck_top = Vector((0.0, half + neck * 0.45, body_z + neck * 0.8))
    tube(builder, shoulder, neck_top, girth * 0.3, girth * 0.19, colour, MATTE, 8)
    direction = Vector((0.0, head_size * 0.95, -head_size * 0.5))
    matrix, _ = axis_matrix(neck_top - direction * 0.1, neck_top + direction)
    blob(builder, Vector((0.0, 0.0, direction.length * 0.5)), (head_size * 0.2, head_size * 0.26,
                                                                direction.length * 0.62), colour, MATTE, 8, 5,
         matrix=matrix)
    blob(builder, Vector((0.0, 0.0, direction.length * 1.02)), (head_size * 0.15, head_size * 0.19, head_size * 0.13),
         dark, MATTE, 7, 3, matrix=matrix)
    for side in (-1, 1):
        for end, leg_y in ((-1, -half * 0.68), (1, half * 0.66)):
            top = Vector((side * girth * 0.22, leg_y, body_z - girth * 0.05))
            bend = 0.05 * height if end > 0 else -0.09 * height
            knee = Vector((side * girth * 0.21, leg_y + bend, height * 0.5))
            fetlock = Vector((side * girth * 0.2, leg_y + 0.01, height * 0.1))
            foot = Vector((side * girth * 0.2, leg_y + 0.04, 0.03))
            tube(builder, top, knee, girth * 0.2, girth * 0.11, colour, MATTE, 6, caps=False)
            tube(builder, knee, fetlock, girth * 0.095, girth * 0.075, dark, MATTE, 6, caps=False)
            tube(builder, fetlock, foot, girth * 0.08, girth * 0.09, dark, MATTE, 5, caps=False)
            blob(builder, foot, (girth * 0.085, girth * 0.1, 0.045), (0.18, 0.15, 0.12), MATTE, 6, 3)
        if ears:
            base = neck_top + Vector((side * 0.05, -0.02, 0.05))
            tip = base + Vector((side * ears * 0.3, -ears * 0.42, ears * 0.9))
            ear_matrix, ear_length = axis_matrix(base, tip)
            blob(builder, Vector((0.0, 0.0, ear_length * 0.5)), (max(0.045, ears * 0.25), 0.024, ear_length * 0.55),
                 colour, MATTE, 6, 3, matrix=ear_matrix)
        if horns:
            tube(builder, neck_top + Vector((side * 0.04, 0.03, 0.07)),
                 neck_top + Vector((side * 0.07, -0.1, 0.07 + horns)), 0.018, 0.006, (0.5, 0.45, 0.38), MATTE, 5)
    tube(builder, (0.0, -half * 1.0, body_z + girth * 0.25), (0.0, -half * 1.1, body_z - tail), 0.035, 0.02, dark,
         MATTE, 5)


def mule(packed=True, colour=(0.36, 0.27, 0.2)):
    builder = MeshBuilder()
    height, girth = 0.88, 0.62
    animal_body(builder, 1.6, height, girth, colour, 0.66, 0.6, 0.28)
    body = height + girth * 0.42
    if packed:
        for side in (-1, 1):
            blob(builder, (side * 0.34, 0.0, body - 0.02), (0.16, 0.36, 0.23), (0.56, 0.45, 0.3), CLOTH, 7, 4)
        tube(builder, (-0.3, -0.05, body + 0.42), (0.3, -0.05, body + 0.42), 0.13, 0.13, (0.66, 0.6, 0.48), CLOTH, 7)
        blob(builder, (0.0, 0.0, body + 0.27), (0.28, 0.46, 0.06), (0.42, 0.24, 0.16), CLOTH, 8, 3)
    return builder


def goat(colour=(0.3, 0.24, 0.18), scale=1.0):
    builder = MeshBuilder()
    animal_body(builder, 0.72, 0.42, 0.3, colour, 0.28, 0.22, 0.09, horns=0.16 * scale, tail=0.08)
    blob(builder, (0.0, 0.63, 0.6), (0.025, 0.03, 0.06), tuple(c * 0.7 for c in colour), MATTE, 5, 3)
    if scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(scale, 4))
        return scaled
    return builder


def donkey(colour=(0.52, 0.48, 0.44)):
    builder = MeshBuilder()
    height, girth = 0.66, 0.5
    animal_body(builder, 1.3, height, girth, colour, 0.5, 0.52, 0.3, tail=0.4)
    body = height + girth * 0.42
    for side in (-1, 1):
        shell(builder, [(0.12, 0.0), (0.17, 0.12), (0.16, 0.32), (0.14, 0.36)], (0.58, 0.46, 0.3), MATTE, 8,
              squash=0.7, matrix=Matrix.Translation((side * 0.36, 0.0, body - 0.38)))
    blob(builder, (0.0, 0.0, body + 0.22), (0.26, 0.4, 0.05), (0.36, 0.22, 0.15), CLOTH, 8, 3)
    return builder


def hen(colour=(0.62, 0.42, 0.24)):
    builder = MeshBuilder()
    blob(builder, (0.0, 0.0, 0.22), (0.11, 0.17, 0.12), colour, MATTE, 7, 4)
    blob(builder, (0.0, 0.12, 0.34), (0.05, 0.06, 0.06), colour, MATTE, 6, 3)
    blob(builder, (0.0, 0.14, 0.4), (0.012, 0.03, 0.02), (0.75, 0.18, 0.12), MATTE, 4, 2)
    tube(builder, (0.0, 0.17, 0.34), (0.0, 0.21, 0.33), 0.012, 0.004, (0.85, 0.65, 0.25), MATTE, 4)
    tube(builder, (0.0, -0.12, 0.26), (0.0, -0.2, 0.38), 0.05, 0.02, tuple(c * 0.7 for c in colour), MATTE, 5)
    for side in (-1, 1):
        tube(builder, (side * 0.04, 0.0, 0.12), (side * 0.045, 0.02, 0.0), 0.008, 0.008, (0.8, 0.62, 0.3), MATTE, 3)
    return builder


def sheep():
    builder = MeshBuilder()
    animal_body(builder, 0.8, 0.4, 0.42, (0.84, 0.81, 0.74), 0.24, 0.24, 0.08, tail=0.1)
    return builder


def dog():
    builder = MeshBuilder()
    animal_body(builder, 0.66, 0.36, 0.24, (0.52, 0.4, 0.27), 0.22, 0.22, 0.08, tail=0.2)
    return builder


def boat(length=6.2, width=1.3):
    builder = MeshBuilder()
    half = length / 2
    stations = [-half, -half * 0.6, 0.0, half * 0.6, half]
    widths = [0.55, 0.95, 1.0, 0.9, 0.35]
    rims = []
    bottoms = []
    for y, w in zip(stations, widths):
        rims.append([(-w * width / 2, y, 0.55 + 0.1 * abs(y) / half), (w * width / 2, y, 0.55 + 0.1 * abs(y) / half)])
        bottoms.append([(-w * width / 2 * 0.8, y, 0.08 + 0.25 * (abs(y) / half) ** 3),
                        (w * width / 2 * 0.8, y, 0.08 + 0.25 * (abs(y) / half) ** 3)])
    for side in (0, 1):
        rows = [[rims[k][side] for k in range(len(stations))], [bottoms[k][side] for k in range(len(stations))]]
        tinted(builder, WOOD, lambda rows=rows, side=side: builder.surface(
            rows, MATTE, facing=(1 if side else -1, 0, 0)))
        tinted(builder, (0.36, 0.26, 0.17), lambda rows=rows, side=side: builder.surface(
            list(reversed(rows)), MATTE, facing=(-1 if side else 1, 0, 0)))
    floor = [[bottoms[k][0] for k in range(len(stations))], [bottoms[k][1] for k in range(len(stations))]]
    tinted(builder, (0.38, 0.28, 0.19), lambda: builder.surface(floor, MATTE, facing=(0, 0, 1)))
    tinted(builder, (0.28, 0.2, 0.14), lambda: builder.surface(floor, MATTE, facing=(0, 0, -1)))
    for y in (-1.2, 1.1):
        tinted(builder, WOOD, lambda y=y: builder.box((-0.55, y - 0.12, 0.38), (0.55, y + 0.12, 0.44), MATTE))
    return builder


def net_basket():
    builder = MeshBuilder()
    shell(builder, [(0.18, 0.0), (0.24, 0.25), (0.22, 0.32)], (0.58, 0.46, 0.28), MATTE, 8, squash=1.0)
    return builder


def shade_faces(builder, first, colour, centre, radius, dark=0.55, light=1.08, seed=0):
    for index in range(first, len(builder.polygons)):
        builder.polygon_colors[index] = colour


def vertex_shade(mesh, dark=0.5, light=1.08, height_weight=0.5):
    count = len(mesh.loops)
    if count == 0:
        return
    vertex_index = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex_index)
    positions = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    normals = np.empty(len(mesh.vertices) * 3)
    mesh.vertex_normals.foreach_get("vector", normals)
    normals = normals.reshape(-1, 3)
    z = positions[:, 2]
    span = max(float(z.max() - max(z.min(), 0.0)), 1e-3)
    height = np.clip((z - max(z.min(), 0.0)) / span, 0, 1)
    centre = positions.mean(axis=0)
    outward = positions - centre
    outward /= np.maximum(np.linalg.norm(outward, axis=1, keepdims=True), 1e-6)
    facing = np.clip((normals * outward).sum(axis=1), 0, 1)
    up = normals[:, 2] * 0.5 + 0.5
    value = dark + (light - dark) * np.clip(0.45 * up + 0.3 * facing + height_weight * 0.5 * height, 0, 1.2)
    value = value[vertex_index]
    attribute = mesh.color_attributes.get("Col")
    colours = np.empty(count * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    colours[:, :3] = np.clip(colours[:, :3] * value[:, None], 0, 1)
    attribute.data.foreach_set("color_srgb", colours.ravel())


def crown(builder, centre, radius, height, colour, seed, lobes=5, spread=0.55, flat=0.0, segments=7, rings=4):
    generator = random.Random(seed)
    cx, cy, cz = centre
    first = len(builder.polygons)
    for k in range(lobes):
        if k == 0:
            offset = (0.0, 0.0, 0.0)
            size = 1.0
        else:
            angle = 2 * math.pi * k / (lobes - 1) + generator.uniform(-0.4, 0.4)
            distance = radius * spread * generator.uniform(0.7, 1.05)
            offset = (distance * math.cos(angle), distance * math.sin(angle), height * generator.uniform(-0.22, 0.12))
            size = generator.uniform(0.55, 0.78)
        r = radius * size
        h = height * size * (1.0 - flat)
        blob(builder, (cx + offset[0], cy + offset[1], cz + offset[2]), (r, r, h / 2), colour, "foliage", segments,
             rings, wobble=0.16, seed=seed + k)
    shade_faces(builder, first, colour, (cx, cy, cz - height * 0.25), radius * 1.2, seed=seed)


def trunk(builder, base, top, r0, r1, colour=(0.36, 0.29, 0.22), segments=5):
    tube(builder, base, top, r0, r1, colour, "foliage", segments, caps=False)


def holm_oak(height=4.6, seed=0, detail=2):
    builder = MeshBuilder()
    generator = random.Random(seed)
    stems = (2, 3, 4, 5)[detail]
    radius = height * 0.44
    tips = []
    for k in range(stems):
        angle = 2 * math.pi * k / stems + generator.uniform(-0.5, 0.5)
        reach = height * generator.uniform(0.12, 0.26)
        top = (reach * math.cos(angle), reach * math.sin(angle), height * generator.uniform(0.36, 0.5))
        trunk(builder, (0.12 * math.cos(angle), 0.12 * math.sin(angle), -0.5), top, 0.12 if detail else 0.14, 0.06,
              segments=(3, 4, 4, 6)[detail])
        tips.append(top)
    if detail == 3:
        for k, top in enumerate(tips):
            angle = math.atan2(top[1], top[0]) + generator.uniform(-0.6, 0.6)
            end = (top[0] + radius * 0.55 * math.cos(angle), top[1] + radius * 0.55 * math.sin(angle),
                   top[2] + height * 0.18)
            trunk(builder, top, end, 0.055, 0.025, segments=4)
    lobes = (6, 7, 8, 15)[detail]
    for k in range(lobes):
        angle = 2 * math.pi * k / lobes * (2.3 if detail == 3 else 1.0) + generator.uniform(-0.35, 0.35)
        distance = radius * (0.25 if k == 0 else generator.uniform(0.5, 0.82))
        lift = height * (0.55 + generator.uniform(-0.12, 0.14) + (0.12 if k == 0 else 0.0))
        size = radius * (0.62 if k == 0 else generator.uniform(0.42, 0.58))
        if detail == 3 and k:
            size *= 0.78
            lift += height * 0.08 * math.sin(k * 1.7)
        shade = generator.uniform(0.85, 1.12)
        outer = 1.0 + 0.12 * (distance / radius) + 0.1 * (lift / height - 0.55)
        colour = (0.2 * shade * outer, 0.27 * shade * outer, 0.15 * shade * outer)
        blob(builder, (distance * math.cos(angle), distance * math.sin(angle), lift), (size, size, size * 0.92),
             colour, "foliage", 7 if detail == 3 else 5, 4 if detail >= 2 else 3, wobble=0.3, seed=seed * 31 + k)
    return builder


def aleppo_pine(height=12.0, seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    top = (generator.uniform(-1.2, 1.2), generator.uniform(-1.2, 1.2), height * 0.78)
    trunk(builder, (0.0, 0.0, -0.6), top, 0.26, 0.12)
    colour = (0.30, 0.36, 0.20)
    for k in range(4):
        angle = generator.uniform(0, 6.28)
        z = height * generator.uniform(0.55, 0.85)
        reach = height * generator.uniform(0.12, 0.22)
        tip = (top[0] * z / top[2] + reach * math.cos(angle), top[1] * z / top[2] + reach * math.sin(angle), z + 0.4)
        trunk(builder, (top[0] * (z - 1) / top[2], top[1] * (z - 1) / top[2], z - 1.0), tip, 0.08, 0.04, segments=4)
        crown(builder, tip, height * 0.14, height * 0.18, colour, seed + 10 * k, 2, 0.55, 0.0, 6, 3)
    crown(builder, (top[0], top[1], top[2] + 0.4), height * 0.2, height * 0.22, colour, seed + 99, 4, 0.6, 0.0, 6, 3)
    return builder


def riverside_tree(height, seed, colour, lobes, spread, droop):
    builder = MeshBuilder()
    generator = random.Random(seed)
    tips = []
    for k in range(3):
        angle = 2 * math.pi * k / 3 + generator.uniform(-0.5, 0.5)
        top = (height * 0.14 * math.cos(angle), height * 0.14 * math.sin(angle), height * 0.5)
        trunk(builder, (0.0, 0.0, -0.5), top, 0.2, 0.09, segments=5)
        tips.append(angle)
    radius = height * spread
    for k in range(lobes):
        angle = 2 * math.pi * k / lobes * 2.6 + generator.uniform(-0.4, 0.4)
        distance = radius * (0.2 if k == 0 else generator.uniform(0.45, 0.85))
        lift = height * (0.66 + generator.uniform(-0.14, 0.16) - droop * distance / radius * 0.2)
        size = radius * (0.6 if k == 0 else generator.uniform(0.36, 0.5))
        shade = generator.uniform(0.86, 1.12) * (1.0 + 0.1 * distance / radius)
        blob(builder, (distance * math.cos(angle), distance * math.sin(angle), lift),
             (size, size, size * (1.0 + droop)), tuple(c * shade for c in colour), "foliage", 6, 4, wobble=0.18,
             seed=seed * 17 + k)
    return builder


def willow(height=9.0, seed=0):
    return riverside_tree(height, seed, (0.42, 0.48, 0.31), 11, 0.36, 0.5)


def poplar(height=14.0, seed=0):
    return riverside_tree(height, seed, (0.47, 0.53, 0.38), 10, 0.3, 0.25)


def olive(height=4.6, seed=0):
    builder = MeshBuilder()
    trunk(builder, (0.0, 0.0, -0.4), (0.3, 0.1, 1.4), 0.2, 0.14)
    crown(builder, (0.3, 0.1, height * 0.64), height * 0.36, height * 0.48, (0.47, 0.51, 0.37), seed, 5, 0.6, 0.1)
    return builder


def fig_tree(height=4.0, seed=0):
    builder = MeshBuilder()
    trunk(builder, (0.0, 0.0, -0.3), (0.2, 0.0, 1.0), 0.14, 0.1)
    crown(builder, (0.2, 0.0, height * 0.58), height * 0.45, height * 0.56, (0.30, 0.41, 0.19), seed, 5, 0.6, 0.15)
    return builder


def shrub(size=1.2, seed=0, colour=(0.27, 0.33, 0.19)):
    builder = MeshBuilder()
    crown(builder, (0.0, 0.0, size * 0.32), size * 0.6, size * 0.75, colour, seed, 2, 0.75, 0.1, 6, 4)
    return builder


def vine_stock(seed=0):
    builder = MeshBuilder()
    trunk(builder, (0.0, 0.0, -0.2), (0.05, 0.0, 0.45), 0.05, 0.04, (0.32, 0.25, 0.18), 4)
    crown(builder, (0.05, 0.0, 0.62), 0.45, 0.5, (0.36, 0.45, 0.18), seed, 3, 0.6, 0.1, 6)
    return builder


def boulder(size=1.0, seed=0, colour=(0.64, 0.62, 0.57)):
    builder = MeshBuilder()
    generator = random.Random(seed)
    phase = [generator.uniform(0, 6.28) for _ in range(3)]
    profile = [(0.0, -0.35), (0.55, -0.3), (0.62, 0.0), (0.5, 0.28), (0.25, 0.45), (0.0, 0.5)]
    matrix = Matrix.Diagonal((size, size * generator.uniform(0.6, 0.9), size * generator.uniform(0.5, 0.8), 1.0))
    tinted(builder, colour, lambda: builder.lathe(
        profile, 7, "urgonian", smooth=False, matrix=matrix,
        radius_scale=lambda a: 1.0 + 0.18 * math.sin(2 * a + phase[0]) + 0.1 * math.sin(5 * a + phase[1])))
    return builder


def rubble(seed=16):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(5):
        x, y = generator.uniform(-0.8, 0.8), generator.uniform(-0.8, 0.8)
        size = generator.uniform(0.35, 0.7)
        blob(builder, (x, y, size * 0.2), (size, size * 0.8, size * 0.5), (0.95, 0.88, 0.74), "molasse", 6, 3,
             wobble=0.2, seed=seed + k)
    return builder


def tomb_marker(kind=0):
    builder = MeshBuilder()
    if kind == 0:
        generator = random.Random(kind + 5)
        for k in range(9):
            angle = 2 * math.pi * k / 9 + generator.uniform(-0.15, 0.15)
            size = generator.uniform(0.09, 0.15)
            blob(builder, (0.48 * math.cos(angle), 0.36 * math.sin(angle), size * 0.2), (size, size * 0.8, size * 0.6),
                 (0.6, 0.58, 0.52), "urgonian", 5, 3, wobble=0.15, seed=k)
        blob(builder, (0.0, 0.0, -0.02), (0.42, 0.3, 0.07), (0.42, 0.36, 0.28), MATTE, 7, 2, wobble=0.2, seed=9)
        neck = [(0.065, -0.1), (0.06, 0.08), (0.075, 0.12), (0.07, 0.14)]
        tinted(builder, (0.72, 0.48, 0.34), lambda: builder.lathe(neck, 8, MATTE, smooth=True, caps=False))
    elif kind == 1:
        tilt = Matrix.Translation((0.0, 0.0, -0.32)) @ Matrix.Rotation(math.radians(20), 4, "X")
        body = [(0.07, 0.0), (0.075, 0.03), (0.05, 0.06), (0.12, 0.16), (0.19, 0.32), (0.2, 0.45), (0.15, 0.6),
                (0.065, 0.7), (0.06, 0.82), (0.075, 0.86), (0.07, 0.88)]
        tinted(builder, (0.74, 0.5, 0.36), lambda: builder.lathe(body, 9, MATTE, smooth=True, matrix=tilt,
                                                                  caps=False))
        for side in (-1, 1):
            start = tilt @ Vector((side * 0.065, 0.0, 0.8))
            middle = tilt @ Vector((side * 0.13, 0.0, 0.76))
            end = tilt @ Vector((side * 0.13, 0.0, 0.62))
            tube(builder, start, middle, 0.018, 0.018, (0.72, 0.48, 0.34), MATTE, 4, caps=False)
            tube(builder, middle, end, 0.018, 0.018, (0.72, 0.48, 0.34), MATTE, 4, caps=False)
    else:
        tinted(builder, (0.82, 0.76, 0.66), lambda: builder.box((-0.9, -0.5, -0.2), (0.9, 0.5, 0.12), "molasse"))
        tinted(builder, (0.66, 0.42, 0.3), lambda: builder.box((-0.75, -0.38, 0.12), (0.75, 0.38, 0.2), MATTE))
    return builder


def campfire():
    builder = MeshBuilder()
    for k in range(7):
        angle = 2 * math.pi * k / 7
        tinted(builder, (0.7, 0.68, 0.62), lambda angle=angle: builder.box(
            (0.45 * math.cos(angle) - 0.1, 0.45 * math.sin(angle) - 0.08, -0.05),
            (0.45 * math.cos(angle) + 0.1, 0.45 * math.sin(angle) + 0.08, 0.14), "urgonian"))
    for k in range(4):
        angle = math.pi * k / 4
        tube(builder, (-0.35 * math.cos(angle), -0.35 * math.sin(angle), 0.05),
             (0.35 * math.cos(angle), 0.35 * math.sin(angle), 0.18), 0.04, 0.035, (0.22, 0.17, 0.12), MATTE, 4)
    blob(builder, (0.0, 0.0, 0.18), (0.2, 0.2, 0.16), (1.0, 0.55, 0.18), MATTE, 6, 3)
    return builder


def grass_tuft(seed=0, colour=(0.6, 0.55, 0.34), green=(0.42, 0.47, 0.26)):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(10):
        angle = 2 * math.pi * k / 10 + generator.uniform(-0.4, 0.4)
        lean = generator.uniform(0.06, 0.18)
        top = (lean * math.cos(angle), lean * math.sin(angle), generator.uniform(0.14, 0.3))
        shade = generator.uniform(0.8, 1.15)
        base = (0.04 * math.cos(angle) + generator.uniform(-0.03, 0.03), 0.04 * math.sin(angle), -0.03)
        matrix, length = axis_matrix(base, top)
        blade = colour if k % 3 else green
        tinted(builder, tuple(c * shade for c in blade), lambda matrix=matrix, length=length: builder.lathe(
            [(0.012, 0.0), (0.0, length)], 3, MATTE, smooth=True, matrix=matrix, caps=False))
    return builder


def pebbles(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(4):
        x, y = generator.uniform(-0.5, 0.5), generator.uniform(-0.5, 0.5)
        size = generator.uniform(0.06, 0.16)
        shade = generator.uniform(0.85, 1.1)
        blob(builder, (x, y, size * 0.15), (size, size * 0.8, size * 0.55), (0.66 * shade, 0.64 * shade, 0.58 * shade),
             "urgonian", 5, 2, wobble=0.15, seed=seed + k)
    return builder


def rock_slab(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    phase = [generator.uniform(0, 6.28) for _ in range(2)]
    profile = [(0.0, -0.2), (0.62, -0.18), (0.66, 0.02), (0.45, 0.12), (0.0, 0.14)]
    tinted(builder, (0.58, 0.56, 0.5), lambda: builder.lathe(
        profile, 7, "urgonian", smooth=True, matrix=Matrix.Diagonal((1.0, 0.7, 1.0, 1.0)),
        radius_scale=lambda a: 1.0 + 0.2 * math.sin(2 * a + phase[0]) + 0.12 * math.sin(3 * a + phase[1])))
    return builder


def ox(builder, matrix, colour=(0.62, 0.5, 0.36)):
    part = MeshBuilder()
    animal_body(part, 2.1, 0.72, 0.9, colour, 0.36, 0.62, 0.12, horns=0.34, tail=0.55)
    builder.merge(part, matrix)


def ox_cart():
    builder = MeshBuilder()
    for side in (-1, 1):
        ox(builder, Matrix.Translation((side * 0.62, 2.9, 0.0)), (0.62, 0.5, 0.36) if side < 0 else (0.5, 0.4, 0.3))
    tinted(builder, WOOD, lambda: builder.box((-1.2, 3.6, 1.18), (1.2, 3.8, 1.32), MATTE))
    tube(builder, (0.0, -0.4, 0.82), (0.0, 3.7, 1.22), 0.07, 0.06, WOOD, MATTE, 5, caps=False)
    tinted(builder, (0.48, 0.36, 0.24), lambda: builder.box((-0.75, -1.6, 0.72), (0.75, 0.4, 0.86), MATTE))
    for side in (-1, 1):
        tinted(builder, WOOD, lambda side=side: builder.box((side * 0.75 - 0.04, -1.6, 0.86),
                                                            (side * 0.75 + 0.04, 0.4, 1.24), MATTE))
        wheel = Matrix.Translation((side * 0.92, -0.6, 0.62)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        tinted(builder, (0.36, 0.27, 0.18), lambda wheel=wheel: builder.lathe(
            [(0.0, -0.07), (0.62, -0.07), (0.62, 0.07), (0.0, 0.07)], 12, MATTE, smooth=False, matrix=wheel))
    tube(builder, (-0.95, -0.6, 0.62), (0.95, -0.6, 0.62), 0.06, 0.06, WOOD, MATTE, 5)
    for k in range(3):
        tinted(builder, (0.82, 0.76, 0.64), lambda k=k: builder.box((-0.55 + k * 0.38, -1.3, 0.86),
                                                                    (-0.25 + k * 0.38, -0.2, 1.2), "molasse"))
    return builder


def house_footing(seed=0, width=4.4, depth=5.2):
    builder = MeshBuilder()
    generator = random.Random(seed)
    thickness = 0.5
    walls = [((-width / 2, -depth / 2), (width / 2, -depth / 2 + thickness)),
             ((-width / 2, depth / 2 - thickness), (width / 2, depth / 2)),
             ((-width / 2, -depth / 2 + thickness), (-width / 2 + thickness, depth / 2 - thickness)),
             ((width / 2 - thickness, -depth / 2 + thickness), (width / 2, depth / 2 - thickness))]
    for index, ((x0, y0), (x1, y1)) in enumerate(walls):
        pieces = 3
        for k in range(pieces):
            if index == 0 and k == 1:
                continue
            if x1 - x0 > y1 - y0:
                a, b = x0 + (x1 - x0) * k / pieces, x0 + (x1 - x0) * (k + 1) / pieces
                lower, upper = (a, y0), (b, y1)
            else:
                a, b = y0 + (y1 - y0) * k / pieces, y0 + (y1 - y0) * (k + 1) / pieces
                lower, upper = (x0, a), (x1, b)
            top = generator.uniform(0.25, 0.85)
            shade = generator.uniform(0.85, 1.05)
            tinted(builder, (0.86 * shade, 0.8 * shade, 0.68 * shade), lambda lower=lower, upper=upper, top=top:
                   builder.box((lower[0], lower[1], -0.4), (upper[0], upper[1], top), "molasse", bottom=False))
    for k in range(5):
        x, y = generator.uniform(-width, width), generator.uniform(-depth, depth)
        size = generator.uniform(0.2, 0.4)
        blob(builder, (x, y, 0.02), (size, size * 0.8, size * 0.45), (0.9, 0.84, 0.72), "molasse", 5, 2,
             wobble=0.2, seed=seed + k)
    return builder


def quarry_block(length=2.2, width=1.2, height=1.1):
    builder = MeshBuilder()
    builder.box((-length / 2, -width / 2, -0.2), (length / 2, width / 2, height), "quarry_face", bottom=False)
    return builder


def kiln():
    builder = MeshBuilder()
    shell(builder, [(1.6, -0.3), (1.6, 1.2), (1.2, 2.1), (0.4, 2.6), (0.3, 2.7)], (0.62, 0.42, 0.3), MATTE, 10,
          squash=1.0)
    tinted(builder, (0.12, 0.1, 0.08), lambda: builder.box((-0.4, 1.4, 0.0), (0.4, 1.62, 0.8), MATTE))
    return builder


def amphora_stack():
    builder = MeshBuilder()
    for row in range(2):
        for index in range(5):
            x = -0.9 + index * 0.42 + (0.21 if row else 0.0)
            matrix = Matrix.Translation((x, row * 0.4, 0.0)) @ Matrix.Rotation(math.radians(-10), 4, "X")
            shell(builder, [(0.0, -0.05), (0.05, 0.02), (0.17, 0.3), (0.16, 0.6), (0.07, 0.82), (0.05, 1.0)],
                  (0.72, 0.46, 0.32) if (row + index) % 3 else (0.8, 0.58, 0.42), MATTE, 7, squash=1.0,
                  matrix=matrix)
    return builder


def tiled_roof(builder, x0, x1, y0, y1, eave, ridge, axis="x"):
    tile = (0.68, 0.38, 0.26)
    if axis != "x":
        rotated = MeshBuilder()
        tiled_roof(rotated, y0, y1, -x1, -x0, eave, ridge, "x")
        builder.merge(rotated, Matrix.Rotation(math.pi / 2, 4, "Z"))
        return
    mid = (y0 + y1) / 2
    for side in (-1, 1):
        edge = y0 - 0.45 if side < 0 else y1 + 0.45
        corners = [(x0 - 0.4, edge, eave), (x1 + 0.4, edge, eave), (x1 + 0.4, mid, ridge), (x0 - 0.4, mid, ridge)]
        builder.oriented(corners, (0, side, 1), MATTE)
        builder.tint(len(builder.polygons) - 1, tile)
        count = int((x1 - x0 + 0.8) / 0.5)
        for k in range(count + 1):
            x = x0 - 0.4 + k * (x1 - x0 + 0.8) / count
            shade = 0.9 + 0.12 * math.sin(k * 2.3)
            tube(builder, (x, edge, eave + 0.03), (x, mid, ridge + 0.03), 0.055, 0.055,
                 tuple(c * shade for c in tile), MATTE, 3, caps=False)
    tube(builder, (x0 - 0.45, mid, ridge + 0.05), (x1 + 0.45, mid, ridge + 0.05), 0.1, 0.1, (0.6, 0.33, 0.22),
         MATTE, 6)


def wing(builder, x0, x1, y0, y1, height, axis):
    wall = (0.86, 0.8, 0.7)
    tinted(builder, wall, lambda: builder.box((x0, y0, -0.8), (x1, y1, height), "molasse"))
    ridge = height + (min(x1 - x0, y1 - y0) / 2) * 0.5
    if axis == "x":
        for x, facing in ((x0, -1), (x1, 1)):
            builder.oriented([(x, y0, height), (x, y1, height), (x, (y0 + y1) / 2, ridge)], (facing, 0, 0),
                             "molasse")
            builder.tint(len(builder.polygons) - 1, wall)
    else:
        for y, facing in ((y0, -1), (y1, 1)):
            builder.oriented([(x0, y, height), (x1, y, height), ((x0 + x1) / 2, y, ridge)], (0, facing, 0),
                             "molasse")
            builder.tint(len(builder.polygons) - 1, wall)
    tiled_roof(builder, x0, x1, y0, y1, height - 0.2, ridge, axis)


def farmhouse(seed=0):
    builder = MeshBuilder()
    wing(builder, -7.0, 7.0, -3.0, 3.0, 3.8, "x")
    wing(builder, 2.0, 7.0, 3.0, 12.0, 3.2, "y")
    dark = (0.13, 0.11, 0.09)
    tinted(builder, dark, lambda: builder.box((-1.6, -3.04, 0.0), (-0.4, -3.0, 2.2), MATTE))
    tinted(builder, WOOD, lambda: builder.box((-1.8, -3.12, 2.2), (-0.2, -2.96, 2.38), MATTE))
    for x in (-5.0, 2.2, 4.8):
        tinted(builder, dark, lambda x=x: builder.box((x - 0.25, -3.04, 2.5), (x + 0.25, -3.0, 3.0), MATTE))
    for y in (6.0, 9.5):
        tinted(builder, dark, lambda y=y: builder.box((1.96, y - 0.22, 2.0), (2.0, y + 0.22, 2.5), MATTE))
    tinted(builder, dark, lambda: builder.box((1.96, 4.2, 0.0), (2.0, 5.4, 2.0), MATTE))
    tinted(builder, (0.8, 0.74, 0.64), lambda: builder.box((-7.0, 3.0, -0.4), (-6.5, 12.0, 1.4), "molasse",
                                                           bottom=False))
    tinted(builder, (0.8, 0.74, 0.64), lambda: builder.box((-7.0, 11.5, -0.4), (2.0, 12.0, 1.4), "molasse",
                                                           bottom=False))
    return builder


def net_rack(seed=0):
    builder = MeshBuilder()
    for x in (-1.3, 1.3):
        tube(builder, (x, 0.0, -0.2), (x * 0.95, 0.0, 1.75), 0.035, 0.03, WOOD, MATTE, 5, caps=False)
    tube(builder, (-1.4, 0.0, 1.7), (1.4, 0.0, 1.72), 0.03, 0.03, WOOD, MATTE, 5)
    generator = random.Random(seed)
    rows = []
    for k in range(4):
        z = 1.68 - k * 0.42
        rows.append([(x, 0.03 + 0.05 * math.sin(x * 3 + k) + generator.uniform(-0.03, 0.03),
                      z - 0.08 * math.cos(x * 1.2) * (k > 0)) for x in (-1.25, -0.6, 0.0, 0.6, 1.25)])
    for facing in (1, -1):
        tinted(builder, (0.55, 0.52, 0.42), lambda facing=facing: builder.surface(rows, MATTE,
                                                                               facing=(0, facing, 0)))
    return builder


def fish_trap():
    builder = MeshBuilder()
    trap = Matrix.Translation((0.0, -0.5, 0.18)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
    shell(builder, [(0.06, 0.0), (0.16, 0.25), (0.19, 0.6), (0.17, 0.9), (0.1, 1.05)], (0.6, 0.5, 0.32), MATTE, 9,
          squash=1.0, folds=0.06, fold_count=3, matrix=trap)
    return builder


def laundry(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    colours = [(0.9, 0.88, 0.8), (0.72, 0.55, 0.32), (0.62, 0.3, 0.22), (0.4, 0.47, 0.57)]
    for k in range(4):
        x, y = generator.uniform(-0.9, 0.9), generator.uniform(-0.5, 0.5)
        blob(builder, (x, y, 0.03), (generator.uniform(0.3, 0.5), generator.uniform(0.2, 0.35), 0.035),
             colours[k], CLOTH, 7, 3, wobble=0.25, seed=seed + k)
    shell(builder, [(0.2, 0.0), (0.26, 0.24), (0.27, 0.27)], (0.58, 0.46, 0.28), MATTE, 9, squash=0.8,
          matrix=Matrix.Translation((1.2, 0.4, -0.02)))
    blob(builder, (1.2, 0.4, 0.24), (0.22, 0.16, 0.06), (0.88, 0.86, 0.78), CLOTH, 6, 3, wobble=0.2, seed=seed + 9)
    return builder


def firewood(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for row in range(3):
        for k in range(5 - row):
            x = -0.5 + k * 0.24 + row * 0.12
            z = 0.09 + row * 0.16
            tube(builder, (x, -0.6 + generator.uniform(-0.1, 0.1), z), (x, 0.6 + generator.uniform(-0.1, 0.1), z),
                 0.08, 0.07, (0.4 + generator.uniform(-0.05, 0.05), 0.31, 0.22), MATTE, 5)
    return builder


def sherd_pile(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    blob(builder, (0.0, 0.0, -0.04), (0.6, 0.6, 0.2), (0.46, 0.39, 0.3), "urgonian", 9, 3, wobble=0.3, seed=seed)
    for k in range(14):
        angle = generator.uniform(0, 6.28)
        distance = generator.uniform(0.0, 0.55)
        x, y = distance * math.cos(angle), distance * 0.8 * math.sin(angle)
        z = 0.14 * (1 - (distance / 0.7) ** 2) + 0.01
        tilt = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(generator.uniform(0, 6.28), 4, "Z")
                @ Matrix.Rotation(generator.uniform(-0.8, 0.8), 4, "X"))
        tone = generator.uniform(0.85, 1.1)
        sweep = generator.uniform(1.4, 2.4)
        tinted(builder, (0.74 * tone, 0.47 * tone, 0.33 * tone), lambda tilt=tilt, sweep=sweep: builder.lathe(
            [(0.16, 0.0), (0.19, 0.12)], 5, MATTE, smooth=True, matrix=tilt, start=0.0, sweep=sweep, caps=False))
    return builder


def stone_basket(seed=0):
    builder = MeshBuilder()
    shell(builder, [(0.2, 0.0), (0.27, 0.22), (0.28, 0.26)], (0.56, 0.45, 0.28), MATTE, 9, squash=1.0,
          folds=0.04, fold_count=3)
    generator = random.Random(seed)
    for k in range(4):
        blob(builder, (generator.uniform(-0.1, 0.1), generator.uniform(-0.1, 0.1), 0.26), (0.11, 0.09, 0.07),
             (0.82, 0.8, 0.74), "urgonian", 5, 2, wobble=0.2, seed=seed + k)
    return builder


def tools(seed=0):
    builder = MeshBuilder()
    tube(builder, (-0.3, 0.0, 0.03), (0.6, 0.15, 0.05), 0.02, 0.02, WOOD, MATTE, 5)
    tinted(builder, (0.32, 0.31, 0.3), lambda: builder.box((0.55, 0.0, 0.02), (0.6, 0.38, 0.06), MATTE))
    tube(builder, (-0.2, 0.4, 0.03), (0.8, 0.5, 0.04), 0.02, 0.018, WOOD, MATTE, 5)
    tinted(builder, (0.48, 0.38, 0.26), lambda: builder.box((0.8, 0.38, 0.0), (1.1, 0.62, 0.03), MATTE))
    return builder


def hand_barrow():
    builder = MeshBuilder()
    for side in (-1, 1):
        tube(builder, (side * 0.32, -1.0, 0.3), (side * 0.32, 1.0, 0.3), 0.03, 0.03, WOOD, MATTE, 5)
        for y in (-0.55, 0.55):
            tube(builder, (side * 0.32, y, 0.0), (side * 0.32, y, 0.3), 0.025, 0.025, WOOD, MATTE, 4, caps=False)
    tinted(builder, (0.46, 0.35, 0.24), lambda: builder.box((-0.34, -0.6, 0.27), (0.34, 0.6, 0.31), MATTE))
    generator = random.Random(4)
    for k in range(5):
        blob(builder, (generator.uniform(-0.2, 0.2), generator.uniform(-0.4, 0.4), 0.42), (0.16, 0.13, 0.11),
             (0.85, 0.8, 0.7), "molasse", 5, 3, wobble=0.15, seed=k)
    return builder


def hut(seed=0):
    builder = MeshBuilder()
    width, depth, height = 4.6, 3.6, 2.5
    generator = random.Random(seed)
    for k in range(3):
        z0, z1 = -0.6 + k * (height + 0.6) / 3, -0.6 + (k + 1) * (height + 0.6) / 3
        tone = generator.uniform(0.86, 1.0)
        inset = 0.0 if k == 0 else 0.02
        tinted(builder, (0.84 * tone, 0.77 * tone, 0.64 * tone), lambda z0=z0, z1=z1, inset=inset: builder.box(
            (-width / 2 + inset, -depth / 2 + inset, z0), (width / 2 - inset, depth / 2 - inset, z1), "molasse",
            bottom=False, top=False))
    ridge = height + 0.9
    for side in (-1, 1):
        builder.polygon([(-width / 2 - 0.35, side * (depth / 2 + 0.4), height - 0.15),
                         (width / 2 + 0.35, side * (depth / 2 + 0.4), height - 0.15),
                         (width / 2 + 0.35, 0.0, ridge), (-width / 2 - 0.35, 0.0, ridge)][::side], MATTE,
                        color=(0.66, 0.37, 0.25))
        builder.polygon([(side * width / 2, -depth / 2, height), (side * width / 2, depth / 2, height),
                         (side * width / 2, 0.0, ridge)][::side], "molasse", color=(0.84, 0.77, 0.64))
    tube(builder, (-width / 2 - 0.35, 0.0, ridge + 0.05), (width / 2 + 0.35, 0.0, ridge + 0.05), 0.09, 0.09,
         (0.6, 0.33, 0.22), MATTE, 6)
    for k in range(7):
        x = -width / 2 + 0.3 + k * (width - 0.6) / 6
        for side in (-1, 1):
            tube(builder, (x, side * (depth / 2 + 0.4), height - 0.13), (x, side * 0.15, ridge - 0.02), 0.035, 0.035,
                 (0.6, 0.34, 0.23), MATTE, 4, caps=False)
    tinted(builder, (0.14, 0.11, 0.09), lambda: builder.box((-0.55, -depth / 2 - 0.02, 0.0),
                                                           (0.55, -depth / 2, 1.9), MATTE))
    tinted(builder, (0.42, 0.31, 0.21), lambda: builder.box((-0.7, -depth / 2 - 0.06, 1.9),
                                                           (0.7, -depth / 2 + 0.05, 2.05), MATTE))
    return builder


def peddler_goods(seed=0):
    builder = MeshBuilder()
    blob(builder, (0.0, 0.0, 0.0), (0.9, 0.65, 0.025), (0.72, 0.55, 0.32), CLOTH, 8, 2, wobble=0.1, seed=seed)
    generator = random.Random(seed)
    for k in range(6):
        x, y = -0.6 + k * 0.24, generator.uniform(-0.35, 0.35)
        shell(builder, [(0.0, 0.0), (0.06, 0.02), (0.09, 0.1), (0.07, 0.18), (0.035, 0.22), (0.04, 0.25)],
              (0.7, 0.43, 0.29) if k % 2 else (0.62, 0.5, 0.36), MATTE, 7, squash=1.0,
              matrix=Matrix.Translation((x, y, 0.02)))
    shell(builder, [(0.15, 0.0), (0.2, 0.18), (0.21, 0.2)], (0.58, 0.46, 0.28), MATTE, 9, squash=1.0,
          matrix=Matrix.Translation((0.45, 0.35, 0.0)))
    for k in range(5):
        blob(builder, (0.45 + generator.uniform(-0.08, 0.08), 0.35 + generator.uniform(-0.08, 0.08), 0.2),
             (0.045, 0.045, 0.04), (0.45, 0.3, 0.45) if k % 2 else (0.32, 0.42, 0.2), MATTE, 5, 3)
    return builder


def reed(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(14):
        angle = generator.uniform(0, 6.28)
        r = generator.uniform(0.0, 0.35)
        base = (r * math.cos(angle), r * math.sin(angle), -0.1)
        lean = generator.uniform(0.05, 0.35)
        top = (base[0] + lean * math.cos(angle), base[1] + lean * math.sin(angle), generator.uniform(1.2, 2.2))
        shade = generator.uniform(0.85, 1.15)
        colour = (0.42 * shade, 0.5 * shade, 0.26 * shade) if k % 4 else (0.62 * shade, 0.58 * shade, 0.38 * shade)
        matrix, length = axis_matrix(base, top)
        tinted(builder, colour, lambda matrix=matrix, length=length: builder.lathe(
            [(0.018, 0.0), (0.012, length * 0.6), (0.0, length)], 3, MATTE, smooth=True, matrix=matrix, caps=False))
    return builder


def broom_shrub(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(9):
        angle = 2 * math.pi * k / 9 + generator.uniform(-0.3, 0.3)
        lean = generator.uniform(0.2, 0.55)
        top = (lean * math.cos(angle), lean * math.sin(angle), generator.uniform(0.9, 1.5))
        tube(builder, (0.0, 0.0, -0.1), top, 0.025, 0.012, (0.3, 0.38, 0.18), "foliage", 4, caps=False)
        blob(builder, top, (0.16, 0.16, 0.22), (0.86, 0.72, 0.18), "foliage", 5, 3, wobble=0.25, seed=seed + k)
    crown(builder, (0.0, 0.0, 0.45), 0.45, 0.6, (0.3, 0.37, 0.18), seed + 30, 3, 0.6, 0.1, 6, 3)
    return builder


def cistus(seed=0):
    builder = MeshBuilder()
    crown(builder, (0.0, 0.0, 0.3), 0.55, 0.62, (0.5, 0.54, 0.4), seed, 4, 0.7, 0.15, 6, 3)
    generator = random.Random(seed)
    for k in range(6):
        angle = generator.uniform(0, 6.28)
        r = generator.uniform(0.2, 0.55)
        z = 0.3 + generator.uniform(0.0, 0.3) * (1 - r)
        blob(builder, (r * math.cos(angle), r * math.sin(angle), z + 0.2), (0.05, 0.05, 0.02), (0.92, 0.66, 0.78),
             "foliage", 5, 2)
    return builder


def rosemary(seed=0):
    builder = MeshBuilder()
    crown(builder, (0.0, 0.0, 0.25), 0.4, 0.55, (0.46, 0.5, 0.4), seed, 4, 0.75, 0.0, 6, 3)
    return builder


def garrigue_clump(seed=0, colour=(0.24, 0.29, 0.16), size=0.7):
    builder = MeshBuilder()
    blob(builder, (0.0, 0.0, size * 0.18), (size, size * 0.85, size * 0.55), colour, "foliage", 7, 3, wobble=0.3,
         seed=seed)
    return builder


def outcrop(seed=0, size=2.6):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(4):
        angle = generator.uniform(0, 6.28)
        distance = size * (0.0 if k == 0 else generator.uniform(0.35, 0.6))
        part = boulder(size * (1.0 if k == 0 else generator.uniform(0.45, 0.7)), seed * 7 + k,
                       (0.58 * generator.uniform(0.9, 1.05), 0.56, 0.51))
        builder.merge(part, Matrix.Translation((distance * math.cos(angle), distance * math.sin(angle), -0.1 * k))
                      @ Matrix.Rotation(generator.uniform(0, 6.28), 4, "Z"))
    return builder


def figure_builds():
    builds = {key: (lambda spec=spec: person(spec)) for key, spec in FIGURES.items()}
    builds.update({
        "mule_packed": lambda: mule(True),
        "mule_bare": lambda: mule(False, (0.46, 0.4, 0.34)),
        "goat_dark": lambda: goat(),
        "goat_light": lambda: goat((0.78, 0.72, 0.62)),
        "sheep": sheep,
        "dog": dog,
        "boat": boat,
        "basket": net_basket,
        "campfire": campfire,
        "tomb_ring": lambda: tomb_marker(0),
        "wash_stone": lambda: rock_slab(70),
        "tomb_amphora": lambda: tomb_marker(1),
        "tomb_tiles": lambda: tomb_marker(2),
        "quarry_block": quarry_block,
        "ox_cart": ox_cart,
        "house_footing_a": lambda: house_footing(41),
        "house_footing_b": lambda: house_footing(42, 4.0, 5.6),
        "kiln": kiln,
        "amphora_stack": amphora_stack,
        "farmhouse": farmhouse,
        "goat_kid": lambda: goat((0.62, 0.5, 0.38), 0.62),
        "donkey": donkey,
        "hen": hen,
        "hen_white": lambda: hen((0.86, 0.82, 0.74)),
        "net_rack": net_rack,
        "fish_trap": fish_trap,
        "laundry": laundry,
        "firewood": firewood,
        "sherd_pile": sherd_pile,
        "stone_basket": stone_basket,
        "tools": tools,
        "hand_barrow": hand_barrow,
        "hut": hut,
        "peddler_goods": peddler_goods,
    })
    return builds


def vegetation_builds():
    return {
        "holm_oak_a": lambda: holm_oak(4.6, 1, 2), "holm_oak_b": lambda: holm_oak(6.2, 2, 1),
        "holm_oak_c": lambda: holm_oak(4.8, 21, 0), "holm_oak_d": lambda: holm_oak(6.4, 22, 0),
        "pine_a": lambda: aleppo_pine(12.0, 3), "pine_b": lambda: aleppo_pine(15.0, 4),
        "willow": lambda: willow(8.0, 5), "poplar": lambda: poplar(14.0, 6),
        "olive": lambda: olive(4.6, 7), "fig": lambda: fig_tree(4.2, 8),
        "shrub_a": lambda: shrub(1.1, 9), "shrub_b": lambda: shrub(1.6, 10, (0.33, 0.37, 0.24)),
        "box_shrub": lambda: shrub(0.9, 12, (0.22, 0.30, 0.15)),
        "vine": lambda: vine_stock(13),
        "boulder_a": lambda: boulder(1.0, 14),
        "rubble": rubble,
        "tuft": lambda: grass_tuft(51),
        "pebbles": lambda: pebbles(53), "rock_slab": lambda: rock_slab(54),
        "reed": lambda: reed(61), "broom": lambda: broom_shrub(62), "cistus": lambda: cistus(63),
        "rosemary": lambda: rosemary(64), "outcrop_a": lambda: outcrop(65, 2.4), "outcrop_b": lambda: outcrop(66, 3.6),
        "holm_oak_hero": lambda: holm_oak(5.4, 3, 3),
        "kermes": lambda: garrigue_clump(71), "thyme": lambda: garrigue_clump(72, (0.46, 0.47, 0.36), 0.4),
    }
