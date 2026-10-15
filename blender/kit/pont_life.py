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


def legs(builder, spec, skin):
    stride = spec.stride
    lower = wool(spec.braccae) if spec.braccae else skin
    for side in (-1, 1):
        if spec.kneel:
            if side < 0:
                knee = (side * 0.1, 0.32, 0.5)
                foot = (side * 0.1, 0.36, 0.04)
            else:
                knee = (side * 0.1, 0.0, 0.06)
                foot = (side * 0.1, -0.42, 0.06)
            hip = (side * 0.1, 0.0, 0.52 if side < 0 else 0.5)
        else:
            swing = side * stride
            foot = (side * 0.1, swing, 0.06)
            knee = (side * 0.1, swing * 0.55 + 0.02, 0.5)
            hip = (side * 0.1, 0.0, 0.9)
        tube(builder, foot, knee, 0.048, 0.058, lower, MATTE if spec.braccae else SKIN_MATERIAL, 6)
        tube(builder, knee, hip, 0.062, 0.085, lower, MATTE if spec.braccae else SKIN_MATERIAL, 6)
        heel = Vector(foot) + Vector((0.0, -0.06, -0.04))
        toe = Vector(foot) + Vector((0.0, 0.16, -0.035))
        if spec.kneel and side > 0:
            heel = Vector(foot) + Vector((0.0, 0.04, -0.02))
            toe = Vector(foot) + Vector((0.0, -0.18, -0.03))
        tube(builder, heel, toe, 0.045, 0.04, LEATHER, MATTE, 5)


def garment(builder, spec):
    colour = wool(spec.tunic)
    lift = -0.4 if spec.kneel else 0.0
    hem = spec.hem + lift
    flare = 0.25 if spec.female else 0.22
    if spec.kneel:
        hem = 0.1
        flare = 0.3
    skirt = [(flare, hem), (flare * 0.95, hem + 0.1), (0.195, (hem + 1.0 + lift) / 2), (0.19, 0.97 + lift),
             (0.172, 1.02 + lift)]
    shell(builder, skirt, colour, folds=0.09, fold_count=11, lift=0.0)
    torso = [(0.17, 1.0 + lift), (0.186, 1.1 + lift), (0.202, 1.24 + lift), (0.214, 1.34 + lift),
             (0.198, 1.41 + lift), (0.13, 1.46 + lift), (0.06, 1.5 + lift)]
    shell(builder, torso, colour, folds=0.025, fold_count=7)
    if spec.belt:
        shell(builder, [(0.174, 0.98 + lift), (0.176, 1.05 + lift)], wool(spec.belt), MATTE, 10)
    return lift


def head(builder, spec, skin, lift):
    hair = HAIR[spec.hair]
    base = 1.49 + lift
    tube(builder, (0.0, 0.0, base - 0.03), (0.0, 0.01, base + 0.07), 0.05, 0.048, skin, SKIN_MATERIAL, 6, caps=False)
    skull = [(0.0, 0.0), (0.05, 0.01), (0.083, 0.05), (0.096, 0.1), (0.093, 0.15), (0.07, 0.195), (0.0, 0.22)]
    matrix = Matrix.Translation((0.0, 0.015, base + 0.04)) @ Matrix.Diagonal((0.86, 1.0, 1.0, 1.0))
    tinted(builder, skin, lambda: builder.lathe(skull, 8, SKIN_MATERIAL, smooth=True, matrix=matrix, caps=False))
    tube(builder, (0.0, 0.1, base + 0.135), (0.0, 0.125, base + 0.1), 0.018, 0.012, skin, SKIN_MATERIAL, 4)
    if spec.beard:
        blob(builder, (0.0, 0.06, base + 0.085), (0.075, 0.05, 0.06), hair, MATTE, 6, 4)
    covered = spec.hood is True or spec.veil is not None or spec.hat == "cap"
    if not covered:
        cap = [(0.0, 0.0), (0.09, 0.05), (0.1, 0.1), (0.075, 0.155), (0.0, 0.178)]
        hair_matrix = Matrix.Translation((0.0, 0.0, base + 0.085)) @ Matrix.Diagonal((0.9, 1.05, 1.0, 1.0))
        tinted(builder, hair, lambda: builder.lathe(cap, 8, MATTE, smooth=True, matrix=hair_matrix,
                                                    start=math.radians(150), sweep=math.radians(240), caps=False))
        top = [(0.0, 0.11), (0.085, 0.125), (0.0, 0.185)]
        tinted(builder, hair, lambda: builder.lathe(top, 8, MATTE, smooth=True, matrix=hair_matrix, caps=False))
        if spec.bun:
            blob(builder, (0.0, -0.11, base + 0.17), (0.055, 0.045, 0.05), hair, MATTE, 6, 4)
    if spec.hood == "down":
        hood_colour = wool(spec.hood_colour)
        collar = [(0.07, 1.47 + lift - base), (0.17, 1.43 + lift - base), (0.235, 1.36 + lift - base),
                  (0.25, 1.27 + lift - base), (0.2, 1.22 + lift - base)]
        tinted(builder, hood_colour, lambda: builder.lathe(collar, 10, CLOTH, smooth=True,
                                                           matrix=Matrix.Translation((0.0, 0.0, base))
                                                           @ Matrix.Diagonal((1.0, 0.8, 1.0, 1.0)), caps=False))
        fold = [(0.12, 1.42 + lift - base), (0.14, 1.36 + lift - base), (0.1, 1.24 + lift - base),
                (0.0, 1.15 + lift - base)]
        tinted(builder, hood_colour, lambda: builder.lathe(fold, 7, CLOTH, smooth=True,
                                                           matrix=Matrix.Translation((0.0, -0.13, base))
                                                           @ Matrix.Diagonal((1.0, 0.45, 1.0, 1.0)),
                                                           start=math.radians(180), sweep=math.radians(180),
                                                           caps=False))
    elif spec.hood:
        hood_colour = wool(spec.cloak or "brown")
        hood = [(0.13, -0.02), (0.125, 0.08), (0.11, 0.17), (0.06, 0.25), (0.0, 0.3)]
        hood_matrix = Matrix.Translation((0.0, -0.02, base + 0.02))
        tinted(builder, hood_colour, lambda: builder.lathe(hood, 9, CLOTH, smooth=True, matrix=hood_matrix,
                                                           start=math.radians(125), sweep=math.radians(290),
                                                           caps=False))
    if spec.veil is not None:
        veil_colour = wool(spec.veil)
        veil = [(0.12, -0.05), (0.115, 0.08), (0.11, 0.15), (0.07, 0.215), (0.0, 0.24)]
        veil_matrix = Matrix.Translation((0.0, -0.015, base + 0.03)) @ Matrix.Diagonal((0.95, 1.0, 1.0, 1.0))
        tinted(builder, veil_colour, lambda: builder.lathe(veil, 9, CLOTH, smooth=True, matrix=veil_matrix,
                                                           start=math.radians(130), sweep=math.radians(280),
                                                           caps=False))
    if spec.hat == "petasus":
        brim = [(0.0, 0.0), (0.2, 0.0), (0.21, 0.015), (0.1, 0.03), (0.08, 0.09), (0.0, 0.11)]
        hat_matrix = Matrix.Translation((0.0, 0.0, base + 0.17)) @ Matrix.Rotation(math.radians(-6), 4, "X")
        tinted(builder, (0.62, 0.52, 0.34), lambda: builder.lathe(brim, 10, MATTE, smooth=True, matrix=hat_matrix,
                                                                caps=False))
    if spec.hat == "cap":
        felt = [(0.0, -0.01), (0.1, 0.02), (0.1, 0.09), (0.07, 0.16), (0.0, 0.19)]
        felt_matrix = Matrix.Translation((0.0, 0.0, base + 0.11))
        tinted(builder, (0.5, 0.4, 0.28), lambda: builder.lathe(felt, 8, CLOTH, smooth=True, matrix=felt_matrix,
                                                              caps=False))


ARM_POSES = {
    "down": ((0.23, 0.02, 1.13), (0.245, 0.07, 0.88)),
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
}


def arms(builder, spec, skin, lift):
    sleeve = wool(spec.tunic)
    pose = ARM_POSES[spec.arms]
    hands = []
    for side in (-1, 1):
        elbow, wrist = pose
        if spec.arms == "swing":
            elbow = (elbow[0], -side * elbow[1], elbow[2])
            wrist = (wrist[0], -side * wrist[1], wrist[2])
        elif spec.arms in ("staff", "carry", "basket", "lead") and side < 0:
            elbow, wrist = ARM_POSES["down"]
        shoulder = Vector((side * 0.185, 0.0, 1.38 + lift))
        elbow = Vector((side * elbow[0], elbow[1], elbow[2] + lift))
        wrist = Vector((side * wrist[0], wrist[1], wrist[2] + lift))
        blob(builder, shoulder, (0.06, 0.065, 0.06), sleeve, CLOTH, 6, 4)
        tube(builder, shoulder, elbow, 0.058, 0.048, sleeve, CLOTH, 6, caps=False)
        tube(builder, elbow, wrist, 0.044, 0.034, skin, SKIN_MATERIAL, 6)
        direction = (wrist - elbow).normalized()
        hand = wrist + direction * 0.07
        matrix, _ = axis_matrix(wrist, hand + direction * 0.02)
        blob(builder, Vector((0, 0, 0.045)), (0.038, 0.022, 0.06), skin, SKIN_MATERIAL, 6, 3, matrix=matrix)
        hands.append(hand)
    return hands


def overgarments(builder, spec, lift):
    if spec.cloak is not None:
        colour = wool(spec.cloak)
        bottom = max(spec.hem + 0.06, 0.62) + lift
        profile = [(0.075, 1.5 + lift), (0.2, 1.43 + lift), (0.235, 1.3 + lift), (0.26, 1.0 + lift),
                   (0.285, bottom)]
        shell(builder, profile, colour, CLOTH, 12, start=math.radians(112), sweep=math.radians(316), squash=0.78,
              folds=0.05, fold_count=7)
    if spec.palla is not None:
        colour = wool(spec.palla)
        profile = [(0.09, 1.47 + lift), (0.215, 1.38 + lift), (0.235, 1.1 + lift), (0.255, 0.7 + lift),
                   (0.265, 0.5 + lift)]
        shell(builder, profile, colour, CLOTH, 12, start=math.radians(120), sweep=math.radians(250), squash=0.78,
              folds=0.06, fold_count=8)
        sash = MeshBuilder()
        path = [Vector((-0.2, -0.03, 1.42)), Vector((0.0, 0.135, 1.2)), Vector((0.21, 0.04, 0.98))]
        sash.sweep(path, [(0.0, -0.09), (0.03, 0.0), (0.0, 0.09)], CLOTH, caps=False,
                   facade_normal=(0.0, 1.0, 0.25))
        builder.merge(sash.tint(0, colour), Matrix.Translation((0.0, 0.0, lift)))


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
    elif spec.carry == "bundle":
        tube(builder, (-0.14, -0.2, 1.2 + lift), (0.14, -0.2, 1.2 + lift), 0.15, 0.15, (0.6, 0.53, 0.4), CLOTH, 7)
    if spec.roll is not None:
        tube(builder, (-0.2, -0.12, 1.42 + lift), (0.17, -0.15, 1.0 + lift), 0.075, 0.07, wool(spec.roll), CLOTH, 7)
    if spec.rope is not None:
        sag = (right + Vector(spec.rope)) / 2 + Vector((0.0, 0.0, -0.18))
        tube(builder, right, sag, 0.012, 0.012, (0.55, 0.47, 0.33), MATTE, 4, caps=False)
        tube(builder, sag, Vector(spec.rope), 0.012, 0.012, (0.55, 0.47, 0.33), MATTE, 4, caps=False)


def person(spec):
    EXTRA[0] = 2
    builder = MeshBuilder()
    skin = SKIN[spec.skin]
    if not spec.female:
        legs(builder, spec, skin)
    else:
        for side in (-1, 1):
            tube(builder, (side * 0.09, side * spec.stride - 0.04, 0.025), (side * 0.09, side * spec.stride + 0.13,
                                                                              0.025), 0.04, 0.035, LEATHER, MATTE, 5)
    lift = garment(builder, spec)
    overgarments(builder, spec, lift)
    head(builder, spec, skin, lift)
    hands = arms(builder, spec, skin, lift)
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


def animal_body(builder, length, height, girth, colour, neck, head_size, ears, horns=0.0, tail=0.25, seed=0):
    half = length / 2
    body_z = height + girth * 0.42
    dark = tuple(c * 0.72 for c in colour)
    blob(builder, (0.0, 0.0, body_z), (girth * 0.44, half * 0.95, girth * 0.48), colour, MATTE, 12, 7)
    blob(builder, (0.0, -half * 0.62, body_z + girth * 0.04), (girth * 0.46, girth * 0.62, girth * 0.52), colour,
         MATTE, 10, 6)
    blob(builder, (0.0, half * 0.62, body_z + girth * 0.02), (girth * 0.42, girth * 0.55, girth * 0.5), colour,
         MATTE, 10, 6)
    shoulder = Vector((0.0, half * 0.8, body_z + girth * 0.2))
    neck_top = Vector((0.0, half + neck * 0.45, body_z + neck * 0.8))
    tube(builder, shoulder, neck_top, girth * 0.3, girth * 0.19, colour, MATTE, 9)
    direction = Vector((0.0, head_size * 0.95, -head_size * 0.5))
    matrix, _ = axis_matrix(neck_top - direction * 0.1, neck_top + direction)
    blob(builder, Vector((0.0, 0.0, direction.length * 0.5)), (head_size * 0.2, head_size * 0.26,
                                                                direction.length * 0.62), colour, MATTE, 9, 6,
         matrix=matrix)
    blob(builder, Vector((0.0, 0.0, direction.length * 1.02)), (head_size * 0.15, head_size * 0.19, head_size * 0.13),
         dark, MATTE, 8, 4, matrix=matrix)
    for side in (-1, 1):
        for end, leg_y in ((-1, -half * 0.68), (1, half * 0.66)):
            top = Vector((side * girth * 0.22, leg_y, body_z - girth * 0.05))
            knee = Vector((side * girth * 0.21, leg_y + 0.03 * end, height * 0.5))
            foot = Vector((side * girth * 0.2, leg_y + 0.02, 0.04))
            tube(builder, top, knee, girth * 0.2, girth * 0.11, colour, MATTE, 7, caps=False)
            tube(builder, knee, foot, girth * 0.095, girth * 0.075, dark, MATTE, 7, caps=False)
            blob(builder, foot, (girth * 0.085, girth * 0.1, 0.05), (0.18, 0.15, 0.12), MATTE, 7, 3)
        if ears:
            tube(builder, neck_top + Vector((side * 0.05, -0.02, 0.06)),
                 neck_top + Vector((side * 0.1, -0.08, 0.06 + ears)), 0.035, 0.01, colour, MATTE, 5)
        if horns:
            tube(builder, neck_top + Vector((side * 0.04, 0.03, 0.07)),
                 neck_top + Vector((side * 0.07, -0.1, 0.07 + horns)), 0.018, 0.006, (0.5, 0.45, 0.38), MATTE, 5)
    tube(builder, (0.0, -half * 1.02, body_z + girth * 0.25), (0.0, -half * 1.12, body_z - tail), 0.035, 0.02, dark,
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


def goat(colour=(0.3, 0.24, 0.18)):
    builder = MeshBuilder()
    animal_body(builder, 0.72, 0.42, 0.3, colour, 0.28, 0.22, 0.09, horns=0.16, tail=0.08)
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
    stems = (2, 3, 4)[detail]
    radius = height * 0.44
    for k in range(stems):
        angle = 2 * math.pi * k / stems + generator.uniform(-0.5, 0.5)
        reach = height * generator.uniform(0.12, 0.26)
        top = (reach * math.cos(angle), reach * math.sin(angle), height * generator.uniform(0.36, 0.5))
        trunk(builder, (0.12 * math.cos(angle), 0.12 * math.sin(angle), -0.5), top, 0.12 if detail else 0.14, 0.06,
              segments=4 if detail else 3)
    lobes = (6, 7, 8)[detail]
    for k in range(lobes):
        angle = 2 * math.pi * k / lobes + generator.uniform(-0.35, 0.35)
        distance = radius * (0.25 if k == 0 else generator.uniform(0.5, 0.82))
        lift = height * (0.55 + generator.uniform(-0.12, 0.14) + (0.12 if k == 0 else 0.0))
        size = radius * (0.62 if k == 0 else generator.uniform(0.42, 0.58))
        shade = generator.uniform(0.85, 1.12)
        colour = (0.2 * shade, 0.27 * shade, 0.15 * shade)
        blob(builder, (distance * math.cos(angle), distance * math.sin(angle), lift), (size, size, size * 0.92),
             colour, "foliage", 5, 4 if detail == 2 else 3, wobble=0.3, seed=seed * 31 + k)
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


def willow(height=9.0, seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    for k in range(3):
        angle = generator.uniform(0, 6.28)
        top = (1.2 * math.cos(angle), 1.2 * math.sin(angle), height * 0.5)
        trunk(builder, (0.0, 0.0, -0.5), top, 0.18, 0.1)
    crown(builder, (0.0, 0.0, height * 0.62), height * 0.3, height * 0.62, (0.42, 0.48, 0.31), seed, 6, 0.5)
    return builder


def poplar(height=14.0, seed=0):
    builder = MeshBuilder()
    trunk(builder, (0.0, 0.0, -0.5), (0.3, 0.1, height * 0.5), 0.3, 0.16)
    trunk(builder, (0.3, 0.1, height * 0.45), (-1.4, 0.6, height * 0.7), 0.13, 0.07, segments=4)
    crown(builder, (0.1, 0.2, height * 0.66), height * 0.35, height * 0.5, (0.47, 0.53, 0.38), seed, 6, 0.55)
    return builder


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


def boulder(size=1.0, seed=0, colour=(0.8, 0.78, 0.73)):
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
        tinted(builder, (0.9, 0.86, 0.78), lambda: builder.box((-0.25, -0.12, -0.3), (0.25, 0.12, 0.75), "molasse"))
        tinted(builder, (0.9, 0.86, 0.78), lambda: builder.prism([(-0.25, -0.12), (0.25, -0.12), (0.25, 0.12),
                                                                  (-0.25, 0.12)], 0.75, 0.82, "molasse"))
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
        blob(builder, (x, y, size * 0.15), (size, size * 0.8, size * 0.55), (0.86 * shade, 0.84 * shade, 0.78 * shade),
             "urgonian", 5, 2, wobble=0.15, seed=seed + k)
    return builder


def rock_slab(seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    phase = [generator.uniform(0, 6.28) for _ in range(2)]
    profile = [(0.0, -0.2), (0.62, -0.18), (0.66, 0.02), (0.45, 0.12), (0.0, 0.14)]
    tinted(builder, (0.68, 0.66, 0.6), lambda: builder.lathe(
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


def farmhouse(seed=0):
    builder = MeshBuilder()
    width, depth, height = 12.0, 7.0, 3.6
    tinted(builder, (0.86, 0.8, 0.7), lambda: builder.box((-width / 2, -depth / 2, -0.8), (width / 2, depth / 2,
                                                                                           height), "molasse"))
    ridge = height + 1.6
    for side in (-1, 1):
        builder.polygon([(-width / 2 - 0.4, side * (depth / 2 + 0.5), height - 0.2),
                         (width / 2 + 0.4, side * (depth / 2 + 0.5), height - 0.2),
                         (width / 2 + 0.4, 0.0, ridge), (-width / 2 - 0.4, 0.0, ridge)][::side], MATTE,
                        color=(0.68, 0.38, 0.26))
    for side in (-1, 1):
        builder.polygon([(side * width / 2, -depth / 2, height), (side * width / 2, depth / 2, height),
                         (side * width / 2, 0.0, ridge)][::side], "molasse", color=(0.86, 0.8, 0.7))
    tinted(builder, (0.15, 0.12, 0.1), lambda: builder.box((-0.7, -depth / 2 - 0.02, 0.0), (0.7, -depth / 2, 2.2),
                                                           MATTE))
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
        "tomb_stele": lambda: tomb_marker(0),
        "tomb_amphora": lambda: tomb_marker(1),
        "tomb_tiles": lambda: tomb_marker(2),
        "quarry_block": quarry_block,
        "ox_cart": ox_cart,
        "house_footing_a": lambda: house_footing(41),
        "house_footing_b": lambda: house_footing(42, 4.0, 5.6),
        "kiln": kiln,
        "amphora_stack": amphora_stack,
        "farmhouse": farmhouse,
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
    }
