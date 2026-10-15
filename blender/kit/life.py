import math

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement, rotation_toward

SKIN = [(0.80, 0.60, 0.47), (0.72, 0.52, 0.39), (0.62, 0.44, 0.32)]
HAIR = [(0.17, 0.12, 0.09), (0.30, 0.20, 0.12), (0.50, 0.46, 0.42), (0.12, 0.10, 0.09)]
WOOL = {
    "undyed": (0.80, 0.75, 0.64), "white": (0.93, 0.91, 0.86), "ochre": (0.74, 0.56, 0.32),
    "madder": (0.64, 0.28, 0.20), "brown": (0.46, 0.34, 0.23), "weld": (0.80, 0.71, 0.42),
    "woad": (0.42, 0.49, 0.58), "green": (0.48, 0.50, 0.34), "grey": (0.55, 0.51, 0.47),
    "dark": (0.30, 0.26, 0.23), "purple": (0.40, 0.16, 0.24), "rose": (0.74, 0.50, 0.44),
}
LEATHER = (0.30, 0.21, 0.14)
WOOD = (0.45, 0.33, 0.22)
TERRACOTTA = (0.70, 0.42, 0.28)
SQUASH = Matrix.Diagonal((1.0, 0.72, 1.0, 1.0))


def painted(builder, color, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, color)


def limb(builder, start, end, width, depth, color, material=MATTE):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    frame = rotation_toward(direction)
    frame.translation = start
    painted(builder, color, lambda: builder.box((-width / 2, 0.0, -depth / 2), (width / 2, direction.length, depth / 2),
                                                material, matrix=frame))


def ring(builder, profile, color, segments=8, matrix=None, start=0.0, sweep=2 * math.pi, material=MATTE, caps=False):
    transform = matrix if matrix is not None else Matrix.Identity(4)
    painted(builder, color, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=transform,
                                                  start=start, sweep=sweep, caps=caps))


class Figure:
    def __init__(self, garment="undyed", hem=0.55, skin=0, hair=0, scale=1.0, stride=0.0, arms="down",
                 toga=False, veiled=False, palla=None, cloak=None, apron=None, belt=None, carry=None, hair_bun=False,
                 hem_radius=0.21, stripe=None, mono=None, material=MATTE):
        self.garment = garment
        self.hem = hem
        self.skin = skin
        self.hair = hair
        self.scale = scale
        self.stride = stride
        self.arms = arms
        self.toga = toga
        self.veiled = veiled
        self.palla = palla
        self.cloak = cloak
        self.apron = apron
        self.belt = belt
        self.carry = carry
        self.hair_bun = hair_bun
        self.hem_radius = hem_radius
        self.stripe = stripe
        self.mono = mono
        self.material = material


def colour(spec, value):
    if spec.mono is not None:
        return spec.mono
    if isinstance(value, str):
        return WOOL[value]
    return value


def figure(spec):
    builder = MeshBuilder()
    m = spec.material
    garment = colour(spec, spec.garment)
    skin = colour(spec, SKIN[spec.skin])
    hair = colour(spec, HAIR[spec.hair])
    leather = colour(spec, LEATHER)
    stride = spec.stride
    for side in (-1, 1):
        foot_y = side * stride
        limb(builder, (side * 0.085, foot_y, 0.05), (side * 0.085, foot_y * 0.35, max(spec.hem + 0.06, 0.55)),
             0.1, 0.11, skin if spec.hem > 0.2 else garment, m)
        limb(builder, (side * 0.085, foot_y - 0.07, 0.035), (side * 0.085, foot_y + 0.17, 0.035), 0.1, 0.07, leather, m)
    waist = 1.0
    hem_radius = spec.hem_radius + (0.03 if stride else 0.0)
    ring(builder, [(hem_radius, spec.hem), (0.18, waist)], garment, 8, SQUASH, material=m)
    if spec.stripe is not None and not spec.toga:
        stripe = colour(spec, spec.stripe)
        for side in (-1, 1):
            limb(builder, (side * 0.07, -0.11, 1.38), (side * 0.07, -0.13, spec.hem + 0.05), 0.04, 0.02, stripe, m)
    ring(builder, [(0.172, waist - 0.02), (0.195, 1.22), (0.205, 1.37), (0.12, 1.45), (0.0, 1.47)], garment, 8, SQUASH,
         material=m)
    if spec.belt is not None:
        ring(builder, [(0.182, 0.97), (0.184, 1.04)], colour(spec, spec.belt), 8, SQUASH, material=m)
    ring(builder, [(0.05, 1.44), (0.09, 1.52), (0.1, 1.6), (0.08, 1.69), (0.0, 1.73)], skin, 8, material=m)
    if not spec.veiled:
        ring(builder, [(0.106, 1.6), (0.09, 1.7), (0.0, 1.748)], hair, 8, Matrix.Translation((0.0, -0.012, 0.0)),
             material=m)
        if spec.hair_bun:
            limb(builder, (0.0, -0.1, 1.6), (0.0, -0.16, 1.62), 0.1, 0.09, hair, m)
    arm_colour = colour(spec, spec.toga) if spec.toga else garment
    poses = {
        "down": [((0.24, 0.0, 1.1), (0.25, 0.06, 0.86)), ((-0.24, 0.0, 1.1), (-0.25, 0.06, 0.86))],
        "forward": [((0.23, 0.08, 1.12), (0.2, 0.36, 1.08)), ((-0.23, 0.08, 1.12), (-0.2, 0.36, 1.08))],
        "gesture": [((0.26, 0.1, 1.2), (0.3, 0.32, 1.42)), ((-0.24, 0.0, 1.1), (-0.25, 0.06, 0.86))],
        "carry": [((0.25, 0.02, 1.48), (0.2, 0.0, 1.62)), ((-0.24, 0.02, 1.1), (-0.24, 0.1, 0.88))],
        "head": [((0.24, 0.0, 1.55), (0.12, 0.0, 1.8)), ((-0.24, 0.0, 1.55), (-0.12, 0.0, 1.8))],
        "swing": [((0.24, -0.1, 1.1), (0.25, -0.2, 0.88)), ((-0.24, 0.12, 1.1), (-0.25, 0.22, 0.88))],
        "pipes": [((0.22, 0.12, 1.2), (0.06, 0.2, 1.52)), ((-0.22, 0.12, 1.2), (-0.06, 0.2, 1.52))],
    }
    for index, (elbow, hand) in enumerate(poses[spec.arms]):
        side = 1 if index == 0 else -1
        shoulder = (side * 0.21, 0.0, 1.38)
        upper = arm_colour if (spec.toga and side < 0) else garment
        limb(builder, shoulder, elbow, 0.085, 0.09, upper, m)
        limb(builder, elbow, hand, 0.07, 0.075, skin if not (spec.toga and side < 0) else arm_colour, m)
    if spec.arms == "pipes":
        for side in (-1, 1):
            limb(builder, (side * 0.02, 0.12, 1.55), (side * 0.09, 0.45, 1.36), 0.025, 0.025, colour(spec, WOOD), m)
    if spec.toga:
        toga = colour(spec, spec.toga)
        limb(builder, (-0.2, 0.0, 1.45), (0.18, -0.02, 0.96), 0.17, 0.43, toga, m)
        ring(builder, [(0.235, 0.1), (0.225, 0.7), (0.19, 1.0)], toga, 8, SQUASH, material=m)
        if spec.stripe is not None:
            ring(builder, [(0.238, 0.1), (0.238, 0.16)], colour(spec, spec.stripe), 8, SQUASH, material=m)
    if spec.veiled:
        veil = colour(spec, spec.toga or spec.palla or spec.garment)
        ring(builder, [(0.13, 1.42), (0.128, 1.62), (0.1, 1.73), (0.0, 1.775)], veil, 8,
             Matrix.Translation((0.0, -0.02, 0.0)), start=math.radians(135), sweep=math.radians(270), material=m)
    if spec.palla is not None:
        ring(builder, [(0.12, 1.47), (0.23, 1.38), (0.24, 0.85), (0.235, 0.62)], colour(spec, spec.palla), 8, SQUASH,
             start=math.radians(125), sweep=math.radians(290), material=m)
    if spec.cloak is not None:
        ring(builder, [(0.12, 1.48), (0.24, 1.37), (0.27, 0.72)], colour(spec, spec.cloak), 8, SQUASH,
             start=math.radians(115), sweep=math.radians(310), material=m)
    if spec.apron is not None:
        builder.polygon([(-0.16, 0.135, 0.6), (0.16, 0.135, 0.6), (0.17, 0.142, 1.02), (-0.17, 0.142, 1.02)], m,
                        color=colour(spec, spec.apron))
    if spec.carry == "amphora":
        frame = Matrix.Translation((0.17, -0.02, 1.52)) @ Matrix.Rotation(math.radians(-70), 4, "Y")
        ring(builder, [(0.03, -0.38), (0.13, -0.25), (0.14, -0.05), (0.06, 0.12), (0.04, 0.24)],
             colour(spec, TERRACOTTA), 6, frame, material=m, caps=True)
    elif spec.carry == "basket":
        ring(builder, [(0.16, 1.76), (0.2, 1.92)], colour(spec, (0.62, 0.50, 0.32)), 7, material=m, caps=True)
    elif spec.carry == "jar":
        ring(builder, [(0.05, 1.75), (0.13, 1.84), (0.12, 2.02), (0.05, 2.1)], colour(spec, TERRACOTTA), 7,
             material=m, caps=True)
    elif spec.carry == "patera":
        ring(builder, [(0.0, 1.09), (0.1, 1.1), (0.11, 1.13)], colour(spec, (0.85, 0.66, 0.36)), 8,
             Matrix.Translation((0.0, 0.38, 0.0)), material=m)
    elif spec.carry == "bundle":
        limb(builder, (-0.12, -0.2, 1.05), (0.12, -0.2, 1.05), 0.26, 0.3, colour(spec, (0.62, 0.55, 0.42)), m)
    if spec.scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(spec.scale, 4))
        return scaled
    return builder


FIGURES = {
    "fig_toga": Figure("white", hem=0.12, skin=0, hair=0, toga="white", hem_radius=0.225),
    "fig_toga_gesture": Figure("white", hem=0.12, skin=1, hair=2, toga="white", arms="gesture", hem_radius=0.225),
    "fig_priest": Figure("white", hem=0.12, skin=0, hair=2, toga="white", veiled=True, arms="forward",
                         stripe="purple", carry="patera", hem_radius=0.225),
    "fig_worker": Figure("ochre", hem=0.55, skin=2, hair=1, belt=LEATHER, arms="down"),
    "fig_porter": Figure("madder", hem=0.56, skin=1, hair=3, belt="brown", arms="carry", carry="amphora"),
    "fig_rural": Figure("undyed", hem=0.5, skin=2, hair=1, cloak="brown", belt="dark", carry="bundle"),
    "fig_matron": Figure("woad", hem=0.03, skin=0, hair=0, palla="rose", veiled=True, hem_radius=0.225),
    "fig_woman": Figure("weld", hem=0.04, skin=1, hair=1, palla="green", arms="head", carry="jar", hair_bun=True,
                        hem_radius=0.215),
    "fig_child": Figure("white", hem=0.5, skin=0, hair=1, scale=0.64, belt="madder", stripe="madder"),
    "fig_merchant": Figure("grey", hem=0.55, skin=1, hair=0, apron="undyed", arms="gesture", belt="brown"),
}

WALKERS = {
    "walker_citizen": Figure("white", hem=0.12, skin=1, hair=0, toga="white", stride=0.16, hem_radius=0.225),
    "walker_worker": Figure("brown", hem=0.55, skin=2, hair=1, belt="dark", stride=0.2, arms="swing"),
    "walker_woman": Figure("madder", hem=0.04, skin=0, hair=1, palla="undyed", stride=0.14, hair_bun=True,
                           hem_radius=0.215),
    "walker_porter": Figure("ochre", hem=0.55, skin=1, hair=3, cloak="green", stride=0.2, arms="carry",
                            carry="amphora"),
}


def animal(kind):
    builder = MeshBuilder()
    specs = {
        "mule": dict(length=1.15, height=1.05, girth=0.42, colour=(0.38, 0.28, 0.2), neck=0.45, ears=0.22, horns=0.0),
        "donkey": dict(length=0.95, height=0.85, girth=0.36, colour=(0.52, 0.47, 0.42), neck=0.38, ears=0.27,
                       horns=0.0),
        "ox": dict(length=1.7, height=1.15, girth=0.62, colour=(0.80, 0.74, 0.62), neck=0.35, ears=0.12, horns=0.3),
        "goat": dict(length=0.7, height=0.55, girth=0.26, colour=(0.30, 0.24, 0.18), neck=0.25, ears=0.1, horns=0.18),
        "dog": dict(length=0.62, height=0.42, girth=0.2, colour=(0.55, 0.42, 0.28), neck=0.18, ears=0.08, horns=0.0),
        "sheep": dict(length=0.85, height=0.6, girth=0.36, colour=(0.88, 0.85, 0.78), neck=0.2, ears=0.08,
                      horns=0.0),
    }
    s = specs[kind]
    half = s["length"] / 2
    leg_top = s["height"]
    body_z = leg_top + s["girth"] * 0.45
    c = s["colour"]
    limb(builder, (0.0, -half, body_z), (0.0, half, body_z + 0.03), s["girth"], s["girth"] * 1.15, c)
    head_base = Vector((0.0, half + s["neck"] * 0.4, body_z + s["neck"] * 0.9))
    limb(builder, (0.0, half - 0.1, body_z), head_base, s["girth"] * 0.5, s["girth"] * 0.6, c)
    snout = head_base + Vector((0.0, s["neck"] * 0.75, -s["neck"] * 0.35))
    limb(builder, head_base, snout, s["girth"] * 0.42, s["girth"] * 0.5, c)
    for side in (-1, 1):
        for end in (-1, 1):
            foot = (side * s["girth"] * 0.3, end * (half - 0.08), 0.0)
            limb(builder, (foot[0], foot[1], leg_top + 0.05), foot, s["girth"] * 0.22, s["girth"] * 0.24,
                 tuple(v * 0.8 for v in c))
        if s["ears"]:
            limb(builder, head_base + Vector((side * 0.06, 0.0, 0.04)),
                 head_base + Vector((side * 0.12, -0.05, 0.04 + s["ears"])), 0.05, 0.03, c)
        if s["horns"]:
            limb(builder, head_base + Vector((side * 0.08, 0.04, 0.06)),
                 head_base + Vector((side * (0.1 + s["horns"]), 0.12, 0.06 + s["horns"] * 0.6)), 0.05, 0.05,
                 (0.86, 0.82, 0.70))
    limb(builder, (0.0, -half, body_z + 0.05), (0.0, -half - 0.08, body_z - s["girth"] * 0.9), 0.05, 0.05, c)
    return builder


def pack(builder, length, height, colour=(0.55, 0.43, 0.28)):
    for side in (-1, 1):
        limb(builder, (side * 0.3, -0.25, height - 0.05), (side * 0.3, 0.25, height - 0.05), 0.2, 0.4, colour)
    limb(builder, (0.0, -0.3, height + 0.3), (0.0, 0.3, height + 0.3), 0.5, 0.08, (0.40, 0.22, 0.16))


def pack_animal(kind):
    builder = animal(kind)
    height = 1.45 if kind == "mule" else 1.2
    pack(builder, 1.0, height)
    return builder


def wheel(builder, x, y, radius, width, spokes=0):
    frame = Matrix.Translation((x, y, radius)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    if spokes:
        ring(builder, [(radius - 0.06, -width / 2), (radius, -width / 2), (radius, width / 2), (radius - 0.06, width / 2),
                       (radius - 0.06, -width / 2)], WOOD, 10, frame)
        for index in range(spokes):
            angle = math.pi * index / spokes
            direction = Vector((0.0, math.cos(angle), math.sin(angle))) * (radius - 0.04)
            limb(builder, Vector((x, y, radius)) - direction, Vector((x, y, radius)) + direction, 0.04, 0.04, WOOD)
        ring(builder, [(0.0, -width), (0.09, -width), (0.09, width), (0.0, width)], WOOD, 6, frame)
    else:
        ring(builder, [(0.0, -width / 2), (radius, -width / 2), (radius, width / 2), (0.0, width / 2)],
             (0.40, 0.29, 0.19), 10, frame)


def ox_cart():
    builder = MeshBuilder()
    for side in (-1, 1):
        wheel(builder, side * 0.78, -0.6, 0.6, 0.14)
        builder.merge(animal("ox"), placement(side * 0.55, 2.4, 0.0))
    painted(builder, WOOD, lambda: builder.box((-0.7, -1.9, 0.72), (0.7, 0.7, 0.86), MATTE))
    for side in (-1, 1):
        painted(builder, WOOD, lambda side=side: builder.box((side * 0.7 - 0.05, -1.9, 0.86), (side * 0.7 + 0.05, 0.7, 1.35),
                                                             MATTE))
    limb(builder, (0.0, 0.6, 0.8), (0.0, 3.2, 1.25), 0.1, 0.1, WOOD)
    limb(builder, (-0.85, 3.2, 1.45), (0.85, 3.2, 1.45), 0.12, 0.12, WOOD)
    for index, (x, y) in enumerate(((-0.35, -1.4), (0.3, -1.3), (-0.3, -0.6), (0.35, -0.5), (0.0, 0.1))):
        tone = (0.62, 0.55, 0.42) if index % 2 else (0.72, 0.62, 0.45)
        limb(builder, (x, y - 0.3, 1.1), (x, y + 0.3, 1.1), 0.5, 0.42, tone)
    builder.merge(figure(Figure("brown", hem=0.55, skin=2, hair=1, cloak="dark", stride=0.18, arms="swing")),
                  placement(-1.3, 2.0, 0.0))
    return builder


def mule_wagon():
    builder = MeshBuilder()
    for x in (-0.8, 0.8):
        for y in (-1.6, 0.4):
            wheel(builder, x, y, 0.5, 0.08, spokes=4)
    painted(builder, WOOD, lambda: builder.box((-0.72, -2.0, 0.62), (0.72, 0.8, 1.15), MATTE))
    arch = [(-0.75 * math.cos(math.pi * i / 6), 1.15 + 0.7 * math.sin(math.pi * i / 6)) for i in range(7)]
    rows = [[(x, y, z) for x, z in arch] for y in (-2.0, -0.4)]
    painted(builder, (0.82, 0.76, 0.62), lambda: builder.surface(rows, MATTE, facing=(0, 0, 1)))
    painted(builder, (0.82, 0.76, 0.62), lambda: builder.surface(list(reversed(rows)), MATTE, facing=(0, 0, -1)))
    limb(builder, (0.0, 0.8, 0.75), (0.0, 3.3, 1.1), 0.08, 0.08, WOOD)
    for side in (-1, 1):
        builder.merge(animal("mule"), placement(side * 0.45, 2.5, 0.0))
    builder.merge(figure(Figure("madder", hem=0.55, skin=1, hair=0, cloak="brown", arms="forward")),
                  placement(0.0, 0.25, 0.55))
    return builder


def amphora(builder, matrix, tone=TERRACOTTA):
    ring(builder, [(0.0, -0.05), (0.04, 0.02), (0.15, 0.25), (0.16, 0.5), (0.07, 0.72), (0.05, 0.9)], tone, 6, matrix)


def amphora_stack():
    builder = MeshBuilder()
    for row in range(3):
        for index in range(4):
            x = -0.9 + index * 0.38 + (0.19 if row % 2 else 0.0)
            frame = Matrix.Translation((x, row * 0.35, 0.0)) @ Matrix.Rotation(math.radians(-12), 4, "X")
            tone = TERRACOTTA if (row + index) % 3 else (0.78, 0.55, 0.40)
            amphora(builder, frame, tone)
    return builder


def market_stall(seed=0, awning=(0.80, 0.72, 0.58)):
    builder = MeshBuilder()
    painted(builder, WOOD, lambda: builder.box((-1.2, -0.45, 0.75), (1.2, 0.45, 0.85), MATTE))
    painted(builder, (0.52, 0.40, 0.28), lambda: builder.box((-1.15, -0.4, 0.0), (1.15, 0.4, 0.75), MATTE,
                                                            bottom=False))
    for x in (-1.25, 1.25):
        for y in (-0.5, 0.9):
            limb(builder, (x, y, 0.0), (x, y, 2.2 if y > 0 else 2.0), 0.07, 0.07, WOOD)
    painted(builder, awning, lambda: builder.polygon([(-1.45, -0.75, 1.95), (1.45, -0.75, 1.95), (1.45, 1.05, 2.3),
                                                      (-1.45, 1.05, 2.3)], MATTE))
    painted(builder, awning, lambda: builder.polygon([(-1.45, 1.05, 2.3), (1.45, 1.05, 2.3), (1.45, -0.75, 1.95),
                                                      (-1.45, -0.75, 1.95)], MATTE))
    goods = [(0.62, 0.48, 0.26), (0.55, 0.62, 0.30), (0.70, 0.30, 0.18), (0.85, 0.72, 0.40), (0.40, 0.45, 0.25)]
    for index in range(6):
        x = -0.95 + index * 0.38
        tone = goods[(index + seed) % len(goods)]
        ring(builder, [(0.0, 0.85), (0.15, 0.88), (0.13, 1.0), (0.0, 1.04)], tone, 6, Matrix.Translation((x, 0.0, 0.0)))
    amphora(builder, Matrix.Translation((1.5, 0.3, 0.0)))
    amphora(builder, Matrix.Translation((1.55, -0.05, 0.0)), (0.78, 0.55, 0.40))
    builder.merge(figure(FIGURES["fig_merchant"]), placement(0.0, 0.9, 0.0, math.pi))
    return builder


def statue_base(builder, height=1.7):
    builder.box((-0.65, -0.55, -0.3), (0.65, 0.55, 0.22), "lens_smooth", bottom=False)
    builder.box((-0.52, -0.42, 0.22), (0.52, 0.42, height - 0.2), "lens_smooth", bottom=False, top=False)
    builder.box((-0.62, -0.52, height - 0.2), (0.62, 0.52, height), "lens_smooth", bottom=False)
    first = len(builder.polygons)
    builder.polygon([(-0.38, -0.425, 0.55), (0.38, -0.425, 0.55), (0.38, -0.425, height - 0.4),
                     (-0.38, -0.425, height - 0.4)], "lens_smooth")
    builder.tint(first, (0.86, 0.85, 0.82))
    for line in range(4):
        z = height - 0.52 - line * 0.17
        half = 0.3 if line < 3 else 0.18
        first = len(builder.polygons)
        builder.polygon([(-half, -0.43, z), (half, -0.43, z), (half, -0.43, z + 0.06), (-half, -0.43, z + 0.06)],
                        "lens_smooth")
        builder.tint(first, (0.35, 0.33, 0.31))


def honorific_statue(bronze=True):
    builder = MeshBuilder()
    statue_base(builder)
    if bronze:
        spec = Figure("white", hem=0.12, toga="white", arms="gesture", hem_radius=0.225, mono=(1.0, 1.0, 1.0),
                      material="bronze")
    else:
        spec = Figure("white", hem=0.03, palla="white", veiled=True, hem_radius=0.225, mono=(0.97, 0.95, 0.9),
                      material="lens_smooth")
    builder.merge(figure(spec), Matrix.Translation((0.0, 0.0, 1.7)) @ Matrix.Rotation(math.pi, 4, "Z")
                  @ Matrix.Scale(1.12, 4))
    return builder
