import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, TERRACOTTA, WOOD, WOOL, painted

SKIN = [(0.82, 0.62, 0.49), (0.74, 0.54, 0.40), (0.63, 0.45, 0.33), (0.55, 0.38, 0.27)]
HAIR = [(0.16, 0.11, 0.08), (0.29, 0.19, 0.11), (0.45, 0.42, 0.39), (0.11, 0.09, 0.08), (0.42, 0.27, 0.15)]
UP = Vector((0.0, 0.0, 1.0))
FLATTEN = Matrix.Diagonal((1.0, 0.7, 1.0, 1.0))
PITCH = (0.16, 0.12, 0.10)
HULL_WOOD = (0.42, 0.30, 0.20)
PLANK = "plank_wood"


def tone(value):
    return WOOL[value] if isinstance(value, str) else value


def axis_frame(start, end):
    start, end = Vector(start), Vector(end)
    direction = end - start
    length = direction.length
    z = direction / max(length, 1e-9)
    helper = UP if abs(z.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    x = helper.cross(z).normalized()
    y = z.cross(x)
    frame = Matrix((x, y, z)).transposed().to_4x4()
    frame.translation = start
    return frame, length


def tube(builder, start, end, r0, r1, color, segments=6, material=MATTE, caps=True, scale=None):
    frame, length = axis_frame(start, end)
    if scale is not None:
        frame = frame @ Matrix.Diagonal((scale[0], scale[1], 1.0, 1.0))
    painted(builder, color, lambda: builder.lathe([(r0, 0.0), (r1, length)], segments, material, smooth=True,
                                                  matrix=frame, caps=caps))


def ellipsoid(builder, center, radii, color, segments=8, rings=5, material=MATTE, rotation=None, low=0.0, high=1.0,
              start=0.0, sweep=2 * math.pi, smooth=True):
    profile = []
    for index in range(rings + 1):
        t = math.pi * (low + (high - low) * index / rings)
        profile.append((math.sin(t), -math.cos(t)))
    frame = Matrix.Translation(center)
    if rotation is not None:
        frame = frame @ rotation
    frame = frame @ Matrix.Diagonal((*radii, 1.0))
    painted(builder, color, lambda: builder.lathe(profile, segments, material, smooth=smooth, matrix=frame,
                                                  start=start, sweep=sweep, caps=False))


def folds(count, depth, phase):
    return lambda angle: 1.0 + depth * math.sin(count * angle + phase) + depth * 0.45 * math.sin(
        (2 * count + 3) * angle + phase * 1.7)


def draped(builder, profile, color, segments, fold, material=MATTE, start=0.0, sweep=2 * math.pi, matrix=None):
    frame = FLATTEN if matrix is None else matrix @ FLATTEN
    painted(builder, color, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=frame,
                                                  radius_scale=fold, start=start, sweep=sweep, caps=False))


class Person:
    def __init__(self, garment="undyed", hem=0.5, skin=0, hair=0, beard=False, cap=None, toga=None, palla=None,
                 veil=False, cloak=None, hood=False, belt=None, pose="down", stride=0.0, carry=None, scale=1.0,
                 bun=False, apron=None, braies=None, clavi=None, mono=None, material=MATTE, seed=0, sleeves=True,
                 seated=False):
        self.garment = garment
        self.hem = hem
        self.skin = skin
        self.hair = hair
        self.beard = beard
        self.cap = cap
        self.toga = toga
        self.palla = palla
        self.veil = veil
        self.cloak = cloak
        self.hood = hood
        self.belt = belt
        self.pose = pose
        self.stride = stride
        self.carry = carry
        self.scale = scale
        self.bun = bun
        self.apron = apron
        self.braies = braies
        self.clavi = clavi
        self.mono = mono
        self.material = material
        self.seed = seed
        self.sleeves = sleeves
        self.seated = seated

    def colour(self, value):
        return self.mono if self.mono is not None else tone(value)


ARM_POSES = {
    "down": ((0.235, 0.0, 1.1), (0.25, 0.05, 0.85), (-0.235, 0.0, 1.1), (-0.25, 0.05, 0.85)),
    "swing": ((0.235, -0.09, 1.1), (0.25, -0.17, 0.87), (-0.235, 0.09, 1.1), (-0.24, 0.2, 0.88)),
    "gesture": ((0.29, 0.12, 1.2), (0.33, 0.36, 1.42), (-0.235, 0.0, 1.1), (-0.25, 0.06, 0.86)),
    "forward": ((0.23, 0.1, 1.12), (0.17, 0.34, 1.1), (-0.23, 0.1, 1.12), (-0.17, 0.34, 1.1)),
    "shoulder": ((0.31, 0.06, 1.52), (0.2, 0.04, 1.72), (-0.235, 0.09, 1.1), (-0.24, 0.2, 0.88)),
    "head": ((0.29, 0.04, 1.56), (0.14, 0.02, 1.8), (-0.29, 0.04, 1.56), (-0.14, 0.02, 1.8)),
    "pole": ((0.26, 0.16, 1.18), (0.16, 0.4, 1.24), (-0.14, 0.2, 1.22), (0.04, 0.42, 1.4)),
    "hips": ((0.34, -0.02, 1.13), (0.2, 0.05, 0.98), (-0.34, -0.02, 1.13), (-0.2, 0.05, 0.98)),
    "sack": ((0.29, 0.02, 1.5), (0.14, -0.06, 1.62), (-0.235, 0.09, 1.1), (-0.24, 0.2, 0.88)),
    "lead": ((0.25, 0.16, 1.12), (0.26, 0.42, 1.06), (-0.235, 0.0, 1.1), (-0.25, 0.06, 0.86)),
    "haul": ((0.24, -0.14, 1.28), (0.18, -0.3, 1.38), (-0.24, -0.14, 1.28), (-0.12, -0.32, 1.42)),
    "hold": ((0.24, 0.12, 1.08), (0.16, 0.3, 1.0), (-0.24, 0.12, 1.08), (-0.16, 0.3, 1.0)),
}


def legs(builder, spec, skin, shoe):
    leg_colour = spec.colour(spec.braies) if spec.braies is not None else skin
    for side in (-1, 1):
        foot_y = side * spec.stride
        hip = Vector((side * 0.09, foot_y * 0.25, 0.86))
        ankle = Vector((side * 0.085, foot_y, 0.075))
        knee = ankle.lerp(hip, 0.5) + Vector((0.0, 0.025, 0.0))
        if spec.hem > 0.25 or spec.braies is not None:
            tube(builder, ankle, knee, 0.046, 0.058, leg_colour, 6, spec.material)
            top = min(spec.hem + 0.08, 0.86)
            tube(builder, knee, knee.lerp(hip, min(max((top - knee.z) / max(hip.z - knee.z, 0.01), 0.1), 1.0)),
                 0.058, 0.07, leg_colour, 6, spec.material, caps=False)
        elif spec.stride > 0:
            tube(builder, ankle, ankle.lerp(hip, 0.35), 0.045, 0.055, leg_colour, 5, spec.material)
        frame = Matrix.Translation((side * 0.085, foot_y + 0.035, 0.0)) @ Matrix.Diagonal((0.05, 0.115, 0.075, 1.0))
        profile = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.4), (0.78, 0.8), (0.0, 1.0)]
        painted(builder, shoe, lambda frame=frame: builder.lathe(profile, 6, spec.material, smooth=True, matrix=frame,
                                                                 caps=False))


def body(builder, spec, garment, rng):
    hem = spec.hem
    flare = 0.25 if hem < 0.25 else 0.235
    skirt = [(flare, hem), (0.215, hem + 0.2 if hem < 0.25 else hem + 0.12), (0.19, 0.86), (0.168, 1.0)]
    if hem < 0.25:
        skirt.insert(1, (flare - 0.008, hem + 0.06))
    draped(builder, skirt, garment, 12, folds(9, 0.05, rng.uniform(0, 6.28)), spec.material)
    painted(builder, garment, lambda: builder.lathe([(flare * 0.98, hem + 0.002), (0.0, hem + 0.002)], 12,
                                                    spec.material, matrix=FLATTEN, caps=False))
    torso = [(0.168, 1.0), (0.18, 1.12), (0.196, 1.24), (0.19, 1.35), (0.15, 1.425), (0.06, 1.46)]
    draped(builder, torso, garment, 12, folds(7, 0.018, rng.uniform(0, 6.28)), spec.material)
    if spec.belt is not None:
        painted(builder, spec.colour(spec.belt), lambda: builder.lathe([(0.176, 0.98), (0.18, 1.03)], 12,
                                                                       spec.material, matrix=FLATTEN, caps=False))
    if spec.clavi is not None:
        stripe = spec.colour(spec.clavi)
        for side in (-1, 1):
            tube(builder, (side * 0.06, 0.135, 1.4), (side * 0.07, 0.165, hem + 0.06), 0.012, 0.014, stripe, 3,
                 spec.material, scale=(1.0, 0.4))
    if spec.apron is not None:
        builder.polygon([(-0.15, 0.142, hem + 0.1), (0.15, 0.142, hem + 0.1), (0.15, 0.13, 1.0), (-0.15, 0.13, 1.0)],
                        spec.material, color=spec.colour(spec.apron))


def head(builder, spec, skin, hair):
    m = spec.material
    tube(builder, (0.0, 0.0, 1.42), (0.0, 0.012, 1.53), 0.048, 0.044, skin, 6, m, caps=False)
    center = Vector((0.0, 0.012, 1.6))
    ellipsoid(builder, center, (0.08, 0.096, 0.108), skin, 8, 6, m)
    tube(builder, (0.0, 0.098, 1.6), (0.0, 0.118, 1.578), 0.016, 0.01, skin, 3, m)
    for side in (-1, 1):
        ellipsoid(builder, (side * 0.08, 0.0, 1.598), (0.012, 0.022, 0.03), skin, 4, 2, m)
    covered = spec.veil or spec.hood
    if not covered:
        ellipsoid(builder, center + Vector((0.0, -0.01, 0.014)), (0.087, 0.103, 0.112), hair, 8, 2, m, low=0.6)
        ellipsoid(builder, center + Vector((0.0, -0.016, 0.006)), (0.088, 0.103, 0.112), hair, 7, 3, m, low=0.32,
                  high=0.66, start=math.radians(165), sweep=math.radians(210))
        if spec.bun:
            ellipsoid(builder, center + Vector((0.0, -0.1, 0.03)), (0.05, 0.045, 0.045), hair, 6, 3, m)
    if spec.beard:
        beard = tuple(min(component * 1.35 + 0.03, 1.0) for component in hair)
        ellipsoid(builder, center + Vector((0.0, 0.004, -0.006)), (0.084, 0.1, 0.11), beard, 7, 2, m, low=0.06,
                  high=0.3, start=math.radians(-20), sweep=math.radians(220))
    if spec.cap == "pileus":
        painted(builder, spec.colour("brown"), lambda: builder.lathe(
            [(0.095, 1.64), (0.088, 1.69), (0.05, 1.75), (0.0, 1.77)], 8, m, smooth=True,
            matrix=Matrix.Translation((0.0, 0.0, 0.0)), caps=False))
    elif spec.cap == "petasus":
        painted(builder, spec.colour((0.62, 0.52, 0.34)), lambda: builder.lathe(
            [(0.0, 1.668), (0.2, 1.668), (0.2, 1.676), (0.09, 1.69), (0.08, 1.74), (0.0, 1.75)], 10, m, smooth=False,
            caps=False))
    if spec.veil:
        veil = spec.colour(spec.palla or spec.toga or spec.garment)
        ellipsoid(builder, center + Vector((0.0, -0.016, 0.006)), (0.104, 0.118, 0.13), veil, 10, 4, m, low=0.35,
                  start=math.radians(140), sweep=math.radians(260))
    if spec.hood:
        hood = spec.colour(spec.cloak or spec.garment)
        ellipsoid(builder, center + Vector((0.0, -0.02, 0.008)), (0.106, 0.12, 0.128), hood, 10, 4, m, low=0.3,
                  start=math.radians(135), sweep=math.radians(270))
        tube(builder, (0.0, -0.11, 1.68), (0.0, -0.2, 1.52), 0.04, 0.012, hood, 4, m)


def arms(builder, spec, skin, garment):
    m = spec.material
    pose = ARM_POSES[spec.pose]
    hands = []
    for index, side in enumerate((1, -1)):
        elbow = Vector(pose[2 * index])
        hand = Vector(pose[2 * index + 1])
        shoulder = Vector((side * 0.205, 0.0, 1.375))
        covered = spec.toga is not None and side < 0
        upper = spec.colour(spec.toga) if covered else garment
        if spec.sleeves or covered:
            tube(builder, shoulder, shoulder.lerp(elbow, 0.55 if not covered else 1.0), 0.064, 0.058, upper, 6, m)
        tube(builder, shoulder, elbow, 0.05, 0.043, upper if covered else skin, 6, m, caps=False)
        tube(builder, elbow, hand, 0.042, 0.032, upper if (covered and spec.pose == "down") else skin, 6, m)
        direction = (hand - elbow).normalized()
        frame, _ = axis_frame(hand, hand + direction)
        rotation = frame.to_3x3().to_4x4()
        ellipsoid(builder, hand + direction * 0.045, (0.032, 0.024, 0.05), skin, 6, 3, m, rotation=rotation)
        hands.append(hand + direction * 0.05)
    return hands


def toga_drape(builder, spec, rng):
    m = spec.material
    toga = spec.colour(spec.toga)
    draped(builder, [(0.255, 0.1), (0.248, 0.45), (0.225, 0.8), (0.205, 1.02)], toga, 14,
           folds(11, 0.07, rng.uniform(0, 6.28)), m)
    draped(builder, [(0.205, 1.0), (0.212, 1.2), (0.21, 1.34), (0.17, 1.44), (0.07, 1.47)], toga, 12,
           folds(6, 0.04, rng.uniform(0, 6.28)), m, start=math.radians(95), sweep=math.radians(215))
    tube(builder, (0.2, 0.1, 0.9), (-0.16, 0.1, 1.42), 0.075, 0.06, toga, 6, m, scale=(1.0, 0.55))
    tube(builder, (0.05, 0.16, 1.0), (-0.12, 0.16, 1.22), 0.05, 0.03, toga, 5, m, scale=(1.0, 0.6))
    if spec.clavi is not None:
        painted(builder, spec.colour(spec.clavi), lambda: builder.lathe([(0.259, 0.1), (0.258, 0.16)], 14, m,
                                                                        matrix=FLATTEN, caps=False))


def palla_drape(builder, spec, rng):
    m = spec.material
    palla = spec.colour(spec.palla)
    draped(builder, [(0.24, 0.6), (0.235, 0.9), (0.225, 1.15), (0.215, 1.34), (0.16, 1.44), (0.07, 1.47)], palla, 12,
           folds(8, 0.05, rng.uniform(0, 6.28)), m, start=math.radians(110), sweep=math.radians(320))
    tube(builder, (0.21, 0.08, 1.38), (-0.1, 0.17, 0.95), 0.06, 0.05, palla, 5, m, scale=(1.0, 0.5))


def cloak_drape(builder, spec, rng):
    m = spec.material
    cloak = spec.colour(spec.cloak)
    draped(builder, [(0.3, 0.72), (0.27, 0.95), (0.24, 1.2), (0.21, 1.37), (0.15, 1.44), (0.065, 1.47)], cloak, 12,
           folds(7, 0.06, rng.uniform(0, 6.28)), m, start=math.radians(100), sweep=math.radians(340))


def amphora_shape(builder, matrix, color, material=MATTE, segments=7):
    profile = [(0.0, 0.0), (0.07, 0.0), (0.075, 0.05), (0.16, 0.2), (0.19, 0.42), (0.16, 0.6), (0.06, 0.72),
               (0.045, 0.86), (0.06, 0.9), (0.0, 0.9)]
    painted(builder, color, lambda: builder.lathe(profile, segments, material, smooth=True, matrix=matrix, caps=False))
    for side in (-1, 1):
        a = matrix @ Vector((side * 0.05, 0.0, 0.84))
        b = matrix @ Vector((side * 0.13, 0.0, 0.8))
        c = matrix @ Vector((side * 0.12, 0.0, 0.63))
        tube(builder, a, b, 0.016, 0.016, color, 3, material)
        tube(builder, b, c, 0.016, 0.016, color, 3, material)


def amphora_light(builder, matrix, color, handles=False):
    profile = [(0.07, 0.0), (0.17, 0.2), (0.19, 0.42), (0.07, 0.7), (0.05, 0.9)]
    painted(builder, color, lambda: builder.lathe(profile, 5, MATTE, smooth=True, matrix=matrix, caps=False))
    if handles:
        for side in (-1, 1):
            tube(builder, matrix @ Vector((side * 0.05, 0.0, 0.84)), matrix @ Vector((side * 0.12, 0.0, 0.66)), 0.016,
                 0.016, color, 3, MATTE, caps=False)


def carried(builder, spec, hands):
    m = spec.material
    if spec.carry == "amphora":
        frame, _ = axis_frame((0.24, -0.34, 1.36), (0.14, 0.36, 1.66))
        amphora_shape(builder, frame @ Matrix.Translation((0.0, 0.0, -0.05)), spec.colour(TERRACOTTA), m)
    elif spec.carry == "sack":
        ellipsoid(builder, (0.1, -0.1, 1.56), (0.24, 0.15, 0.13), spec.colour((0.76, 0.68, 0.52)), 8, 4, m)
    elif spec.carry == "basket":
        painted(builder, spec.colour((0.6, 0.47, 0.28)), lambda: builder.lathe(
            [(0.0, 1.73), (0.16, 1.74), (0.21, 1.9), (0.0, 1.9)], 8, m, smooth=False, caps=False))
        ellipsoid(builder, (0.0, 0.0, 1.9), (0.18, 0.18, 0.06), spec.colour((0.72, 0.36, 0.2)), 7, 2, m, low=0.5)
    elif spec.carry == "jar":
        amphora_shape(builder, Matrix.Translation((0.0, 0.0, 1.72)) @ Matrix.Diagonal((0.75, 0.75, 0.5, 1.0)),
                      spec.colour(TERRACOTTA), m, 6)
    elif spec.carry == "scroll":
        tube(builder, hands[1] + Vector((-0.07, 0.0, 0.0)), hands[1] + Vector((0.07, 0.0, 0.0)), 0.02, 0.02,
             spec.colour((0.88, 0.82, 0.66)), 5, m)
    elif spec.carry == "staff":
        tube(builder, (0.27, 0.12, 0.0), (0.27, 0.12, 1.55), 0.017, 0.015, spec.colour(WOOD), 4, m)
    elif spec.carry == "pole":
        a, b = hands
        direction = (b - a).normalized()
        tube(builder, a - direction * 2.6, b + direction * 1.6, 0.025, 0.022, spec.colour(WOOD), 4, m)
    elif spec.carry == "rope":
        tube(builder, hands[0], hands[0] + Vector((0.0, -1.4, -0.2)), 0.012, 0.012, spec.colour((0.55, 0.45, 0.3)),
             3, m)
    elif spec.carry == "tray":
        painted(builder, spec.colour(WOOD), lambda: builder.lathe([(0.0, 1.0), (0.22, 1.0), (0.24, 1.04),
                                                                   (0.0, 1.04)], 8, m, matrix=Matrix.Translation(
            (0.0, 0.32, 0.0)), caps=False))
        for index in range(4):
            angle = index * math.pi / 2
            ellipsoid(builder, (0.1 * math.cos(angle), 0.32 + 0.1 * math.sin(angle), 1.07), (0.06, 0.06, 0.05),
                      spec.colour([(0.62, 0.48, 0.26), (0.55, 0.62, 0.3), (0.7, 0.3, 0.18), (0.85, 0.72, 0.4)][index]),
                      5, 2, m)


def person(spec):
    builder = MeshBuilder()
    rng = random.Random(spec.seed)
    skin = spec.colour(SKIN[spec.skin])
    hair = spec.colour(HAIR[spec.hair])
    garment = spec.colour(spec.garment)
    legs(builder, spec, skin, spec.colour(LEATHER))
    body(builder, spec, garment, rng)
    if spec.toga is not None:
        toga_drape(builder, spec, rng)
    if spec.palla is not None:
        palla_drape(builder, spec, rng)
    if spec.cloak is not None:
        cloak_drape(builder, spec, rng)
    head(builder, spec, skin, hair)
    hands = arms(builder, spec, skin, garment)
    carried(builder, spec, hands)
    if spec.seated:
        builder = seat(builder, spec, skin, garment)
    if spec.scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(spec.scale, 4))
        return scaled
    return builder


SEAT_CUT = 0.8


def seat(standing, spec, skin, garment):
    builder = MeshBuilder()
    remap = {}
    names = standing.materials
    for polygon, material_index, smooth, uvs, color in zip(standing.polygons, standing.polygon_materials,
                                                           standing.polygon_smooth, standing.polygon_uvs,
                                                           standing.polygon_colors):
        if min(standing.positions[index][2] for index in polygon) < SEAT_CUT:
            continue
        indices = []
        for index in polygon:
            if index not in remap:
                x, y, z = standing.positions[index]
                remap[index] = builder.point((x, y, z - SEAT_CUT), standing.heights[index] - SEAT_CUT)
            indices.append(remap[index])
        builder.face(indices, names[material_index], smooth, uvs, color, raw=True)
    m = spec.material
    lap = spec.colour(spec.toga or spec.palla or spec.cloak or spec.garment) if spec.hem < 0.25 else garment
    shin = lap if spec.hem < 0.25 else skin
    for side in (-1, 1):
        x = side * 0.1
        tube(builder, (x, -0.04, 0.1), (x, 0.36, 0.11), 0.1, 0.085, lap, 6, m)
        tube(builder, (x, 0.38, 0.1), (x, 0.45, -0.32), 0.062, 0.05, shin, 5, m)
        ellipsoid(builder, (x, 0.5, -0.37), (0.05, 0.11, 0.04), spec.colour(LEATHER), 5, 2, m)
    if spec.hem < 0.25:
        for facing in (1, -1):
            quad = [(-0.21, 0.44, 0.15), (0.21, 0.44, 0.15), (0.23, 0.5, -0.3), (-0.23, 0.5, -0.3)]
            builder.polygon(quad if facing > 0 else list(reversed(quad)), m, color=lap)
    return builder


OFFWHITE = (0.84, 0.80, 0.70)
UNDYED_TOGA = (0.88, 0.85, 0.76)

PEOPLE = {
    "fig_citizen": Person(OFFWHITE, hem=0.12, skin=0, hair=0, beard=True, toga=OFFWHITE, seed=1),
    "fig_citizen_b": Person((0.80, 0.76, 0.66), hem=0.12, skin=2, hair=2, toga=UNDYED_TOGA, pose="hold", seed=41),
    "fig_orator": Person(OFFWHITE, hem=0.12, skin=1, hair=2, beard=True, toga=UNDYED_TOGA, pose="gesture", seed=2,
                         carry="scroll"),
    "fig_magistrate": Person(OFFWHITE, hem=0.12, skin=0, hair=2, beard=True, toga=(0.9, 0.87, 0.8), clavi="purple",
                             pose="forward", seed=3),
    "fig_pallium": Person("woad", hem=0.3, skin=1, hair=1, beard=True, palla="undyed", pose="hold", seed=42),
    "fig_pallium_b": Person("madder", hem=0.32, skin=2, hair=0, palla=(0.62, 0.58, 0.48), pose="gesture", seed=46),
    "fig_paenula": Person("ochre", hem=0.45, skin=2, hair=4, cloak=(0.5, 0.38, 0.3), seed=43),
    "fig_matron": Person("woad", hem=0.03, skin=0, hair=1, palla="rose", veil=True, seed=4),
    "fig_lady": Person("weld", hem=0.03, skin=1, hair=4, palla="madder", bun=True, pose="hold", seed=5),
    "fig_woman_jar": Person("undyed", hem=0.04, skin=2, hair=3, palla="green", bun=True, pose="head", carry="jar",
                            seed=6),
    "fig_woman_jar_b": Person("ochre", hem=0.04, skin=1, hair=0, palla="brown", bun=True, pose="head", carry="basket",
                              seed=47),
    "fig_merchant": Person("grey", hem=0.5, skin=1, hair=0, beard=True, belt="brown", apron="undyed", pose="gesture",
                           seed=7),
    "fig_worker": Person("ochre", hem=0.52, skin=2, hair=1, beard=True, belt=LEATHER, cap="pileus", pose="hips",
                         seed=8),
    "fig_worker_b": Person("brown", hem=0.5, skin=3, hair=2, belt="dark", pose="swing", stride=0.12, seed=48),
    "fig_porter_amphora": Person("madder", hem=0.55, skin=3, hair=3, belt="brown", pose="shoulder", carry="amphora",
                                 seed=9),
    "fig_porter_amphora_b": Person("undyed", hem=0.55, skin=2, hair=1, beard=True, belt="dark", pose="shoulder",
                                   carry="amphora", sleeves=False, seed=49),
    "fig_porter_sack": Person("undyed", hem=0.55, skin=2, hair=1, beard=True, belt="dark", pose="sack", carry="sack",
                              sleeves=False, seed=10),
    "fig_porter_sack_b": Person("woad", hem=0.55, skin=3, hair=3, belt="brown", pose="sack", carry="sack",
                                stride=0.14, seed=50),
    "fig_boatman": Person("brown", hem=0.55, skin=3, hair=0, beard=True, braies="dark", cap="pileus", pose="pole",
                          carry="pole", seed=11),
    "fig_sailor": Person("woad", hem=0.55, skin=3, hair=3, belt="brown", pose="hips", sleeves=False, seed=12),
    "fig_rural": Person("undyed", hem=0.5, skin=2, hair=1, beard=True, cloak="brown", hood=True, braies="brown",
                        carry="staff", seed=13),
    "fig_hauler": Person("ochre", hem=0.55, skin=3, hair=1, beard=True, belt="dark", pose="haul", stride=0.22,
                         carry="rope", sleeves=False, seed=14),
    "fig_child": Person("undyed", hem=0.5, skin=0, hair=1, belt="madder", scale=0.64, pose="swing", seed=15),
    "fig_vendor": Person("weld", hem=0.04, skin=1, hair=0, palla="brown", bun=True, pose="forward", carry="tray",
                         seed=16),
    "fig_traveller": Person("grey", hem=0.5, skin=1, hair=2, beard=True, cloak="dark", cap="petasus", carry="staff",
                            seed=17),
    "fig_seated_toga": Person(OFFWHITE, hem=0.12, skin=1, hair=2, beard=True, toga=UNDYED_TOGA, pose="hold",
                              seated=True, seed=51),
    "fig_seated_tunic": Person("woad", hem=0.5, skin=2, hair=0, beard=True, belt="brown", pose="hold", seated=True,
                               seed=52),
    "fig_seated_woman": Person("weld", hem=0.03, skin=0, hair=1, palla="madder", veil=True, pose="hold", seated=True,
                               seed=53),
}

WALKERS = {
    "walker_citizen": Person(OFFWHITE, hem=0.12, skin=1, hair=0, beard=True, toga=UNDYED_TOGA, stride=0.15,
                             seed=21),
    "walker_woman": Person("madder", hem=0.04, skin=0, hair=1, palla="undyed", bun=True, stride=0.13, pose="swing",
                           seed=22),
    "walker_porter": Person("ochre", hem=0.55, skin=2, hair=3, belt="brown", stride=0.2, pose="shoulder",
                            carry="amphora", seed=23),
    "walker_worker": Person("brown", hem=0.52, skin=3, hair=1, beard=True, belt="dark", stride=0.2, pose="swing",
                            cap="pileus", seed=24),
    "walker_sackman": Person("undyed", hem=0.55, skin=2, hair=0, beard=True, belt="dark", stride=0.19, pose="sack",
                             carry="sack", sleeves=False, seed=25),
    "walker_hooded": Person("grey", hem=0.5, skin=1, hair=2, cloak="brown", hood=True, braies="dark", stride=0.17,
                            pose="swing", seed=26),
}


def statue(spec_kind):
    builder = MeshBuilder()
    if spec_kind == "augustus":
        spec = Person("white", hem=0.12, toga="white", pose="gesture", mono=(0.96, 0.94, 0.9), material="lens_smooth",
                      seed=31)
    elif spec_kind == "venus":
        spec = Person("white", hem=0.03, palla="white", pose="hold", bun=True, mono=(0.97, 0.95, 0.91),
                      material="lens_smooth", seed=32)
    elif spec_kind == "toga":
        spec = Person("white", hem=0.12, toga="white", pose="down", beard=True, mono=(0.95, 0.93, 0.88),
                      material="lens_smooth", seed=35)
    elif spec_kind == "bronze":
        spec = Person("white", hem=0.12, toga="white", pose="gesture", mono=(1.0, 1.0, 1.0), material="bronze",
                      seed=33)
    else:
        spec = Person("white", hem=0.03, palla="white", veil=True, mono=(0.97, 0.95, 0.9), material="lens_smooth",
                      seed=34)
    builder.merge(person(spec))
    return builder


def statue_on_base(kind, height=1.6, scale=1.15):
    builder = MeshBuilder()
    builder.box((-0.6, -0.5, -0.3), (0.6, 0.5, 0.2), "lens_smooth", bottom=False)
    builder.box((-0.48, -0.4, 0.2), (0.48, 0.4, height - 0.18), "lens_smooth", bottom=False, top=False)
    builder.box((-0.58, -0.48, height - 0.18), (0.58, 0.48, height), "lens_smooth", bottom=False)
    builder.merge(statue(kind), Matrix.Translation((0.0, 0.0, height)) @ Matrix.Scale(scale, 4))
    return builder


def hull_sections(builder, stations, material, inner_material, inner_tint, outer_tint):
    rows = [[Vector(point) for point in station] for station in stations]
    first = len(builder.polygons)
    builder.surface(rows, material, facing=(-1, 0, 0))
    builder.tint(first, outer_tint)
    first = len(builder.polygons)
    builder.surface(list(reversed(rows)), inner_material, facing=(1, 0, 0))
    builder.tint(first, inner_tint)
    for station, facing in ((rows[0], -1), (rows[-1], 1)):
        first = len(builder.polygons)
        builder.oriented(station, (0, facing, 0), material)
        builder.tint(first, outer_tint)


def barge(length=31.0, beam=3.0, cargo="blocks", seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    half = length / 2
    stations = []
    count = 14
    for index in range(count + 1):
        s = -half + length * index / count
        end = max(abs(s) - (half - 3.2), 0.0) / 3.2
        w = beam / 2 * (1.0 - 0.28 * end * end)
        bottom = -0.35 + 0.75 * end * end
        top = 0.62 + 0.18 * end * end
        stations.append([(-w, s, top), (-w * 0.97, s, bottom + 0.12), (-w * 0.9, s, bottom),
                         (w * 0.9, s, bottom), (w * 0.97, s, bottom + 0.12), (w, s, top)])
    hull_sections(builder, stations, PLANK, PLANK, (0.62, 0.52, 0.42), (0.55, 0.45, 0.36))
    floor_z = 0.10
    first = len(builder.polygons)
    builder.box((-beam / 2 + 0.12, -half + 3.0, floor_z - 0.05), (beam / 2 - 0.12, half - 3.0, floor_z), PLANK,
                bottom=False)
    builder.tint(first, (0.7, 0.6, 0.48))
    for s in range(-int(half) + 4, int(half) - 3, 5):
        tube(builder, (-beam / 2 + 0.05, s, 0.55), (beam / 2 - 0.05, s, 0.55), 0.06, 0.06, (0.5, 0.38, 0.26), 4, PLANK)
    mast_y = half - length / 3
    tube(builder, (0.0, mast_y, floor_z), (0.0, mast_y, 5.2), 0.1, 0.07, HULL_WOOD, 6, PLANK)
    tube(builder, (0.0, -half + 0.6, 0.9), (0.6, -half - 3.4, -0.6), 0.06, 0.05, HULL_WOOD, 5, PLANK)
    blade = Matrix.Translation((0.55, -half - 3.1, -0.45)) @ Matrix.Rotation(math.radians(-17), 4, "X")
    painted(builder, HULL_WOOD, lambda: builder.centered_box((0.0, 0.0, 0.0), (0.06, 1.4, 0.5), PLANK, matrix=blade))
    if cargo == "blocks":
        for index in range(7):
            y = -half + 5.5 + index * 3.0
            size = (rng.uniform(1.0, 1.5), rng.uniform(1.0, 1.6), rng.uniform(0.6, 0.9))
            first = len(builder.polygons)
            builder.centered_box((rng.uniform(-0.3, 0.3), y, floor_z + size[2] / 2), size, "lens_ashlar")
            builder.tint(first, (0.98, 0.95, 0.88))
    elif cargo == "amphorae":
        for row in range(8):
            for column in range(2):
                y = -half + 5.5 + row * 2.4
                x = -0.45 + column * 0.9
                frame = Matrix.Translation((x, y, floor_z + 0.02)) @ Matrix.Rotation(math.radians(8), 4, "X")
                amphora_light(builder, frame, TERRACOTTA if (row + column) % 3 else (0.78, 0.56, 0.4), True)
    elif cargo == "sacks":
        for row in range(9):
            for column in range(3):
                ellipsoid(builder, (-0.75 + column * 0.75, -half + 5.0 + row * 1.6, floor_z + 0.2),
                          (0.36, 0.55, 0.22), (0.78, 0.7, 0.54), 6, 3, MATTE)
    elif cargo == "barrels":
        for row in range(7):
            for column in range(2):
                center = Vector((-0.45 + column * 0.9, -half + 5.5 + row * 2.0, floor_z + 0.45))
                barrel(builder, Matrix.Translation(center) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    return builder


def barrel(builder, matrix, height=1.1, radius=0.42):
    profile = [(0.0, -height / 2), (radius * 0.84, -height / 2), (radius, -height * 0.18), (radius, height * 0.18),
               (radius * 0.84, height / 2), (0.0, height / 2)]
    painted(builder, (0.58, 0.42, 0.26), lambda: builder.lathe(profile, 8, PLANK, smooth=True, matrix=matrix,
                                                               caps=False))
    for z in (-0.38, -0.3, 0.3, 0.38):
        r = radius * (0.9 + 0.1 * (1 - abs(z) / 0.55))
        painted(builder, (0.3, 0.22, 0.14), lambda z=z, r=r: builder.lathe(
            [(r + 0.012, z * height - 0.03), (r + 0.012, z * height + 0.03)], 8, MATTE, matrix=matrix, caps=False))


def seagoing_ship(length=22.0, beam=6.4, seed=0):
    builder = MeshBuilder()
    half = length / 2
    stations = []
    count = 14
    for index in range(count + 1):
        s = -half + length * index / count
        t = s / half
        fullness = max(1.0 - abs(t) ** 2.4, 0.04)
        w = beam / 2 * fullness ** 0.6
        sheer = 2.1 + 1.0 * t * t + (0.6 * t if t > 0 else 0.0)
        keel = -1.0 * fullness ** 0.4
        ring = []
        for k in range(6):
            angle = math.radians(-90 + 90 * k / 5)
            ring.append((w * math.cos(angle) * (0.15 + 0.85 * k / 5) ** 0.5, s, keel * -math.sin(angle) * 1.0
                         + (sheer - 0.0) * (k / 5) ** 1.6 * (1 if k else 0)))
        points = [(-x, y, z) for x, y, z in reversed(ring)] + [(x, y, z) for x, y, z in ring[1:]]
        stations.append(points)
    hull_sections(builder, stations, PLANK, PLANK, (0.6, 0.5, 0.4), PITCH)
    first = len(builder.polygons)
    for station_a, station_b in zip(stations[:-1], stations[1:]):
        a0, a1 = station_a[0], station_a[-1]
        b0, b1 = station_b[0], station_b[-1]
        builder.surface([[(a0[0], a0[1], a0[2] - 0.05), (a0[0], a0[1], a0[2] + 0.12)],
                         [(b0[0], b0[1], b0[2] - 0.05), (b0[0], b0[1], b0[2] + 0.12)]], MATTE, facing=(-1, 0, 0))
        builder.surface([[(a1[0], a1[1], a1[2] - 0.05), (a1[0], a1[1], a1[2] + 0.12)],
                         [(b1[0], b1[1], b1[2] - 0.05), (b1[0], b1[1], b1[2] + 0.12)]], MATTE, facing=(1, 0, 0))
    builder.tint(first, (0.62, 0.22, 0.14))
    deck = 1.55
    first = len(builder.polygons)
    builder.box((-beam / 2 * 0.86, -half * 0.78, deck - 0.1), (beam / 2 * 0.86, half * 0.72, deck), PLANK,
                bottom=False)
    builder.tint(first, (0.74, 0.62, 0.48))
    stern = [Vector((0.0, -half - 0.1, 2.9)), Vector((0.0, -half - 0.9, 4.0)), Vector((0.0, -half - 0.8, 4.9)),
             Vector((0.0, -half - 0.3, 5.3)), Vector((0.0, -half + 0.2, 5.0))]
    for a, b in zip(stern[:-1], stern[1:]):
        tube(builder, a, b, 0.2, 0.17, PITCH, 6, PLANK)
    tube(builder, (0.0, half - 0.2, 2.6), (0.0, half + 0.9, 4.0), 0.18, 0.12, PITCH, 6, PLANK)
    first = len(builder.polygons)
    builder.box((-1.6, -half + 1.2, deck), (1.6, -half + 4.2, deck + 1.9), "plaster", bottom=False)
    builder.tint(first, (0.72, 0.56, 0.4))
    builder.oriented([(-1.9, -half + 0.9, deck + 1.9), (1.9, -half + 0.9, deck + 1.9), (1.9, -half + 4.5, deck + 2.3),
                      (-1.9, -half + 4.5, deck + 2.3)], (0, 0, 1), "terracotta_tiles")
    for side in (-1, 1):
        tube(builder, (side * 2.4, -half + 2.0, 3.4), (side * 2.7, -half - 1.2, -0.8), 0.09, 0.07, HULL_WOOD, 5, PLANK)
        frame = Matrix.Translation((side * 2.68, -half - 1.0, -0.4)) @ Matrix.Rotation(math.radians(-20), 4, "X")
        painted(builder, HULL_WOOD, lambda frame=frame: builder.centered_box((0.0, 0.0, 0.0), (0.08, 1.2, 1.6), PLANK,
                                                                             matrix=frame))
    mast_y = 1.0
    tube(builder, (0.0, mast_y, deck), (0.0, mast_y, deck + 13.0), 0.2, 0.12, HULL_WOOD, 8, PLANK)
    yard_z = deck + 11.8
    tube(builder, (-6.0, mast_y + 0.25, yard_z), (6.0, mast_y + 0.25, yard_z), 0.1, 0.1, HULL_WOOD, 6, PLANK)
    sail = Matrix.Translation((0.0, mast_y + 0.35, yard_z - 0.35)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    painted(builder, (0.9, 0.85, 0.74), lambda: builder.lathe(
        [(0.0, -5.9), (0.22, -5.0), (0.34, -2.0), (0.38, 0.0), (0.34, 2.0), (0.22, 5.0), (0.0, 5.9)], 6, "velum_linen",
        smooth=True, matrix=sail @ Matrix.Diagonal((1.0, 0.7, 1.0, 1.0)), caps=False))
    tube(builder, (0.0, half - 0.5, deck + 0.6), (0.0, half + 3.2, deck + 4.6), 0.1, 0.07, HULL_WOOD, 5, PLANK)
    for target in ((0.0, half + 0.4, 3.4), (0.0, -half + 0.5, 4.6), (-2.6, mast_y - 0.5, 2.2), (2.6, mast_y - 0.5, 2.2),
                   (-2.5, mast_y - 3.0, 2.2), (2.5, mast_y - 3.0, 2.2)):
        tube(builder, (0.0, mast_y, deck + 12.6), target, 0.025, 0.025, (0.3, 0.26, 0.2), 3, MATTE, caps=False)
    for side in (-1, 1):
        ellipsoid(builder, (side * beam / 2 * 0.9, half * 0.78, 2.6), (0.04, 0.25, 0.15), (0.92, 0.9, 0.84), 5, 2,
                  MATTE)
    for index in range(6):
        center = Vector((-1.6 + (index % 3) * 1.6, -2.0 + (index // 3) * 2.5, deck))
        amphora_shape(builder, Matrix.Translation(center), TERRACOTTA, MATTE, 6)
    return builder


def small_boat(length=7.0, beam=1.8, people=None):
    builder = MeshBuilder()
    half = length / 2
    stations = []
    count = 8
    for index in range(count + 1):
        s = -half + length * index / count
        t = s / half
        w = beam / 2 * max(1.0 - abs(t) ** 2.2, 0.08) ** 0.6
        top = 0.55 + 0.25 * t * t
        bottom = -0.3 + 0.35 * t * t
        stations.append([(-w, s, top), (-w * 0.8, s, bottom + 0.08), (0.0, s, bottom), (w * 0.8, s, bottom + 0.08),
                         (w, s, top)])
    hull_sections(builder, stations, PLANK, PLANK, (0.66, 0.54, 0.42), (0.5, 0.4, 0.3))
    first = len(builder.polygons)
    builder.box((-beam / 2 + 0.2, -half + 0.8, -0.12), (beam / 2 - 0.2, half - 0.8, -0.08), PLANK, bottom=False)
    builder.tint(first, (0.72, 0.6, 0.46))
    for spec, offset in (people or []):
        builder.merge(person(spec), placement(offset[0], offset[1], -0.08, offset[2] if len(offset) > 2 else 0.0))
    return builder


def ferry(seed=0):
    rng = random.Random(seed)
    riders = [(PEOPLE["fig_boatman"], (0.3, -2.4)), (PEOPLE["fig_traveller"], (-0.2, 0.6, math.pi)),
              (PEOPLE["fig_matron"], (0.25, 1.4, math.pi * 0.9))]
    if rng.random() < 0.5:
        riders.append((PEOPLE["fig_porter_sack"], (-0.2, -0.6, 0.2)))
    return small_boat(9.0, 2.6, riders)


def amphora_pile(rows=3, columns=5, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for row in range(rows):
        for column in range(columns - row):
            x = -columns * 0.21 + column * 0.42 + row * 0.21
            frame = (Matrix.Translation((x, row * 0.32, row * 0.36)) @ Matrix.Rotation(math.radians(-90), 4, "X")
                     @ Matrix.Translation((0.0, -0.18, -0.45)))
            shade = TERRACOTTA if rng.random() < 0.6 else (0.78, 0.56, 0.4) if rng.random() < 0.5 else (0.62, 0.38,
                                                                                                         0.26)
            amphora_light(builder, frame, shade, row == rows - 1)
    return builder


def standing_amphorae(count=12, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(count):
        x = (index % 4) * 0.4 - 0.6 + rng.uniform(-0.04, 0.04)
        y = (index // 4) * 0.4 + rng.uniform(-0.04, 0.04)
        amphora_light(builder, placement(x, y, 0.0, rng.uniform(0, 6.28)),
                      TERRACOTTA if index % 4 else (0.76, 0.55, 0.4), index >= count - 4)
    return builder


def sack_pile(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for layer, count in ((0, 6), (1, 4), (2, 2)):
        for index in range(count):
            x = (index % 3 - 1) * 0.7 + layer * 0.15
            y = (index // 3) * 0.95 + layer * 0.4
            ellipsoid(builder, (x, y, 0.2 + layer * 0.34), (0.36, 0.5, 0.2), (0.78 * rng.uniform(0.92, 1.05),
                                                                            0.70 * rng.uniform(0.92, 1.05), 0.54),
                      6, 3, MATTE)
    return builder


def barrel_group(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(5):
        x, y = (index % 3) * 0.95 - 0.95, (index // 3) * 0.95
        barrel(builder, placement(x + rng.uniform(-0.05, 0.05), y, 0.55))
    barrel(builder, Matrix.Translation((-0.45, 0.45, 1.5)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    return builder


def block_pile(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(6):
        size = (rng.uniform(1.0, 1.6), rng.uniform(0.8, 1.3), rng.uniform(0.6, 0.9))
        x = (index % 3) * 1.7 - 1.7
        z = 0.0 if index < 4 else 0.85
        first = len(builder.polygons)
        builder.centered_box((x + rng.uniform(-0.1, 0.1), (index // 3) * 1.4, z + size[2] / 2), size, "lens_ashlar",
                             bottom=False)
        builder.tint(first, (0.98, 0.95, 0.88))
    return builder


def crane():
    builder = MeshBuilder()
    for side in (-1, 1):
        tube(builder, (side * 1.6, -1.2, 0.0), (0.0, 2.6, 8.4), 0.13, 0.1, HULL_WOOD, 6, MATTE)
    tube(builder, (0.0, -3.6, 1.9), (0.0, 2.6, 8.4), 0.04, 0.04, (0.45, 0.36, 0.26), 3, MATTE)
    tube(builder, (0.0, 2.6, 8.4), (0.0, 2.6, 2.6), 0.03, 0.03, (0.45, 0.36, 0.26), 3, MATTE)
    first = len(builder.polygons)
    builder.centered_box((0.0, 2.6, 2.1), (0.9, 0.7, 0.9), "lens_ashlar")
    builder.tint(first, (0.98, 0.95, 0.88))
    hub = Vector((0.0, -3.6, 1.95))
    radius = 1.8
    for x in (-0.6, 0.6):
        rim = Matrix.Translation((x, hub.y, hub.z)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        painted(builder, HULL_WOOD, lambda rim=rim: builder.lathe(
            [(radius, -0.06), (radius, 0.06), (radius - 0.12, 0.06), (radius - 0.12, -0.06), (radius, -0.06)], 16,
            MATTE, smooth=False, matrix=rim, caps=False))
        for k in range(8):
            angle = 2 * math.pi * k / 8
            tip = Vector((x, hub.y + (radius - 0.1) * math.cos(angle), hub.z + (radius - 0.1) * math.sin(angle)))
            tube(builder, (x, hub.y, hub.z), tip, 0.035, 0.03, HULL_WOOD, 3, MATTE, caps=False)
    tube(builder, (-0.75, hub.y, hub.z), (0.75, hub.y, hub.z), 0.08, 0.08, HULL_WOOD, 5, MATTE)
    for k in range(14):
        angle = 2 * math.pi * k / 14
        y, z = hub.y + (radius - 0.06) * math.cos(angle), hub.z + (radius - 0.06) * math.sin(angle)
        tube(builder, (-0.6, y, z), (0.6, y, z), 0.025, 0.025, (0.5, 0.38, 0.26), 3, MATTE, caps=False)
    for side in (-1, 1):
        tube(builder, (side * 0.85, -3.6, 0.0), (side * 0.85, -3.6, 2.0), 0.08, 0.08, HULL_WOOD, 4, MATTE)
    builder.merge(person(PEOPLE["fig_worker_b"]), placement(0.0, hub.y, hub.z - radius + 0.06))
    return builder


def cart(load="amphorae", seed=0):
    builder = MeshBuilder()
    for side in (-1, 1):
        frame = Matrix.Translation((side * 0.85, -0.5, 0.62)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        painted(builder, (0.4, 0.29, 0.19), lambda frame=frame: builder.lathe(
            [(0.0, -0.08), (0.62, -0.08), (0.62, 0.08), (0.0, 0.08)], 12, MATTE, smooth=False, matrix=frame,
            caps=False))
        builder.merge(beast("ox"), placement(side * 0.55, 2.5, 0.0))
    painted(builder, WOOD, lambda: builder.box((-0.75, -2.0, 0.74), (0.75, 0.8, 0.88), MATTE))
    for side in (-1, 1):
        painted(builder, WOOD, lambda side=side: builder.box((side * 0.75 - 0.05, -2.0, 0.88),
                                                             (side * 0.75 + 0.05, 0.8, 1.3), MATTE))
    tube(builder, (0.0, 0.7, 0.8), (0.0, 3.3, 1.25), 0.06, 0.05, WOOD, 5, MATTE)
    tube(builder, (-0.9, 3.25, 1.45), (0.9, 3.25, 1.45), 0.07, 0.07, WOOD, 5, MATTE)
    if load == "amphorae":
        for row in range(4):
            for column in range(3):
                frame = (Matrix.Translation((-0.45 + column * 0.45, -1.7 + row * 0.6, 0.9))
                         @ Matrix.Rotation(math.radians(-6), 4, "X"))
                amphora_shape(builder, frame, TERRACOTTA if (row + column) % 3 else (0.78, 0.56, 0.4), MATTE, 5)
    elif load == "barrels":
        for row in range(2):
            barrel(builder, Matrix.Translation((0.0, -1.5 + row * 1.15, 1.35)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    else:
        for row in range(3):
            ellipsoid(builder, (0.0, -1.6 + row * 0.85, 1.05), (0.5, 0.4, 0.22), (0.78, 0.7, 0.54), 6, 3, MATTE)
    builder.merge(person(Person("brown", hem=0.52, skin=2, hair=1, beard=True, cloak="dark", stride=0.18,
                                pose="lead", seed=seed + 40)), placement(-1.3, 2.2, 0.0))
    return builder


BEASTS = {
    "ox": dict(length=1.75, height=0.78, girth=0.36, colour=(0.82, 0.76, 0.64), neck=0.42, head=0.26, horns=0.28,
               ears=0.1),
    "mule": dict(length=1.3, height=0.82, girth=0.27, colour=(0.38, 0.28, 0.2), neck=0.55, head=0.28, horns=0.0,
                 ears=0.2),
    "donkey": dict(length=1.05, height=0.66, girth=0.24, colour=(0.52, 0.47, 0.42), neck=0.45, head=0.25, horns=0.0,
                   ears=0.24),
    "dog": dict(length=0.62, height=0.32, girth=0.12, colour=(0.55, 0.42, 0.28), neck=0.2, head=0.13, horns=0.0,
                ears=0.07),
    "sheep": dict(length=0.85, height=0.42, girth=0.24, colour=(0.88, 0.85, 0.78), neck=0.22, head=0.15, horns=0.0,
                  ears=0.06),
}


def beast(kind):
    builder = MeshBuilder()
    s = BEASTS[kind]
    c = s["colour"]
    dark = tuple(v * 0.7 for v in c)
    half = s["length"] / 2
    body_z = s["height"] + s["girth"] * 0.8
    ellipsoid(builder, (0.0, 0.0, body_z), (s["girth"] * 0.9, half, s["girth"]), c, 9, 6)
    shoulder = Vector((0.0, half * 0.75, body_z + s["girth"] * 0.3))
    poll = shoulder + Vector((0.0, s["neck"] * 0.6, s["neck"] * 0.55))
    tube(builder, shoulder, poll, s["girth"] * 0.55, s["girth"] * 0.35, c, 6)
    muzzle = poll + Vector((0.0, s["head"] * 0.85, -s["head"] * 0.75))
    tube(builder, poll, muzzle, s["girth"] * 0.36, s["girth"] * 0.24, c, 6)
    ellipsoid(builder, muzzle, (s["girth"] * 0.25, s["girth"] * 0.22, s["girth"] * 0.22), dark, 6, 3)
    for side in (-1, 1):
        for end in (-1, 1):
            top = Vector((side * s["girth"] * 0.45, end * half * 0.68, body_z - s["girth"] * 0.3))
            knee = Vector((side * s["girth"] * 0.45, end * half * 0.68 + end * 0.02, s["height"] * 0.45))
            foot = Vector((side * s["girth"] * 0.45, end * half * 0.68, 0.0))
            tube(builder, top, knee, s["girth"] * 0.3, s["girth"] * 0.17, c, 5)
            tube(builder, knee, foot, s["girth"] * 0.16, s["girth"] * 0.13, dark, 5)
        if s["ears"]:
            tube(builder, poll + Vector((side * s["girth"] * 0.2, -0.02, 0.02)),
                 poll + Vector((side * (s["girth"] * 0.25 + s["ears"] * 0.6), -0.06, 0.02 + s["ears"] * 0.8)), 0.035,
                 0.012, c, 4)
        if s["horns"]:
            tube(builder, poll + Vector((side * 0.1, 0.03, 0.06)),
                 poll + Vector((side * (0.12 + s["horns"]), 0.1, 0.06 + s["horns"] * 0.7)), 0.04, 0.012,
                 (0.86, 0.82, 0.7), 5)
    tube(builder, (0.0, -half * 0.95, body_z + s["girth"] * 0.3), (0.0, -half * 1.05, body_z - s["girth"] * 1.2),
         0.03, 0.02, dark, 4)
    return builder


def pack_beast(kind):
    builder = beast(kind)
    s = BEASTS[kind]
    top = s["height"] + s["girth"] * 1.75
    for side in (-1, 1):
        ellipsoid(builder, (side * s["girth"] * 1.05, 0.05, top - 0.25), (0.16, 0.32, 0.22), (0.6, 0.47, 0.3), 6, 3)
    tube(builder, (0.0, -0.4, top), (0.0, 0.45, top), 0.2, 0.2, (0.42, 0.24, 0.17), 6, scale=(1.4, 0.4))
    return builder


def market_stall(seed=0, awning=(0.80, 0.72, 0.58)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    painted(builder, WOOD, lambda: builder.box((-1.2, -0.45, 0.75), (1.2, 0.45, 0.85), MATTE))
    painted(builder, (0.52, 0.40, 0.28), lambda: builder.box((-1.15, -0.4, 0.0), (1.15, 0.4, 0.75), MATTE,
                                                            bottom=False))
    for x in (-1.25, 1.25):
        for y in (-0.5, 0.9):
            tube(builder, (x, y, 0.0), (x, y, 2.2 if y > 0 else 2.0), 0.04, 0.035, WOOD, 4, MATTE)
    painted(builder, awning, lambda: builder.polygon([(-1.45, -0.75, 1.95), (1.45, -0.75, 1.95), (1.45, 1.05, 2.3),
                                                      (-1.45, 1.05, 2.3)], "velum_linen"))
    goods = [(0.62, 0.48, 0.26), (0.55, 0.62, 0.30), (0.70, 0.30, 0.18), (0.85, 0.72, 0.40), (0.40, 0.45, 0.25)]
    for index in range(6):
        x = -0.95 + index * 0.38
        ellipsoid(builder, (x, 0.0, 0.86), (0.16, 0.16, 0.08), goods[(index + seed) % len(goods)], 6, 2, MATTE,
                  low=0.5)
    amphora_shape(builder, Matrix.Translation((1.55, 0.3, 0.0)), TERRACOTTA, MATTE, 6)
    amphora_shape(builder, Matrix.Translation((1.6, -0.1, 0.0)), (0.78, 0.55, 0.40), MATTE, 6)
    seller = PEOPLE["fig_merchant"] if rng.random() < 0.6 else PEOPLE["fig_vendor"]
    builder.merge(person(seller), placement(0.0, 0.95, 0.0, math.pi))
    return builder
