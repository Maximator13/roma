import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement
from .life import HAIR, LEATHER, SKIN, TERRACOTTA, WOOD, WOOL

TAU = 2 * math.pi
FRONT = math.pi / 2
UP = Vector((0.0, 0.0, 1.0))
BRONZE_PIN = (0.78, 0.60, 0.32)
LOD = [1.0]


def detail(count, minimum=3):
    return max(minimum, int(round(count * LOD[0])))


def coarse(build, scale=0.4):
    LOD[0] = scale
    try:
        return build()
    finally:
        LOD[0] = 1.0


def perpendicular(axis, hint=None):
    if hint is not None:
        candidate = hint - axis * hint.dot(axis)
        if candidate.length > 1e-5:
            return candidate.normalized()
    helper = UP if abs(axis.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    return axis.cross(helper).normalized()


def tube(builder, path, radii, color, sides=6, material=MATTE, cap=True, start_cap=False, squash=1.0):
    path = [Vector(point) for point in path]
    sides = detail(sides)
    first = len(builder.polygons)
    rings = []
    u = None
    for index, (point, radius) in enumerate(zip(path, radii)):
        a = path[max(index - 1, 0)]
        b = path[min(index + 1, len(path) - 1)]
        axis = (b - a).normalized()
        u = perpendicular(axis, u)
        v = axis.cross(u).normalized()
        if radius < 1e-6:
            rings.append([builder.point(point)] * sides)
            continue
        rings.append([builder.point(point + (u * math.cos(TAU * k / sides) + v * squash * math.sin(TAU * k / sides))
                                    * radius) for k in range(sides)])
    for lower, upper in zip(rings[:-1], rings[1:]):
        for k in range(sides):
            j = (k + 1) % sides
            builder.face([lower[k], lower[j], upper[j], upper[k]], material, True)
    if cap and radii[-1] > 1e-6:
        builder.face(list(rings[-1]), material)
    if start_cap and radii[0] > 1e-6:
        builder.face(list(reversed(rings[0])), material)
    builder.tint(first, color)


def ellipsoid(builder, center, radii, color, segments=10, rings=6, material=MATTE, matrix=None):
    segments = detail(segments)
    rings = detail(rings, 2)
    profile = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    transform = Matrix.Translation(center) @ Matrix.Diagonal((*radii, 1.0))
    if matrix is not None:
        transform = matrix @ transform
    first = len(builder.polygons)
    builder.lathe(profile, segments, material, smooth=True, matrix=transform)
    builder.tint(first, color)


def drape(builder, color, profile, segments=16, start=0.0, sweep=TAU, folds=(9, 0.05, 0.0), dip=None, squash=0.74,
          center=(0.0, 0.0), material=MATTE, fade=1.0, matrix=None):
    full = abs(sweep - TAU) < 1e-6
    segments = detail(segments)
    count = segments if full else segments + 1
    angles = [start + sweep * step / segments for step in range(count)]
    transform = matrix if matrix is not None else Matrix.Identity(4)
    rings = []
    last = len(profile) - 1
    for row, (radius, height) in enumerate(profile):
        t = row / last if last else 0.0
        if radius < 1e-6:
            rings.append([builder.point(transform @ Vector((center[0], center[1], height)))] * count)
            continue
        ring = []
        for angle in angles:
            wave = 1.0 + folds[1] * (1.0 - 0.75 * t) * math.sin(folds[0] * angle + folds[2])
            dz = dip(angle) * (1.0 - fade * t) if dip is not None else 0.0
            ring.append(builder.point(transform @ Vector((center[0] + radius * wave * math.cos(angle),
                                                         center[1] + radius * wave * math.sin(angle) * squash,
                                                         height + dz))))
        rings.append(ring)
    for row in range(last):
        for step in range(segments):
            following = (step + 1) % count if full else step + 1
            first = len(builder.polygons)
            builder.face([rings[row][step], rings[row][following], rings[row + 1][following], rings[row + 1][step]],
                         material, True)
            if callable(color):
                angle = start + sweep * (step + 0.5) / segments
                builder.tint(first, color(angle, (profile[row][1] + profile[row + 1][1]) / 2))
            else:
                builder.tint(first, color)


def strip(builder, color, path, width, facing, material=MATTE, ridge=0.018):
    rows = []
    for index, point in enumerate(path):
        point = Vector(point)
        swell = ridge * (1.0 if index % 2 else 0.6)
        rows.append([point + Vector((-width / 2, 0.0, 0.0)), point + Vector((0.0, facing * swell, 0.0)),
                     point + Vector((width / 2, 0.0, 0.0))])
    first = len(builder.polygons)
    for lower, upper in zip(rows[:-1], rows[1:]):
        for column in range(2):
            builder.oriented([lower[column], lower[column + 1], upper[column + 1], upper[column]], (0, facing, 0),
                             material, True)
    builder.tint(first, color)


class Look:
    def __init__(self, tunic="undyed", hem=0.55, skin=0, hair=0, scale=1.0, stride=0.0, arms="down", toga=None,
                 praetexta=None, palla=None, veil=False, cloak=None, hood=None, hat=None, apron=None, belt=None,
                 carry=None, hair_style="short", stripe=None, sleeves="short", exomis=False, female=False, child=False,
                 hem_radius=None, mono=None, material=MATTE, seed=0):
        self.tunic = tunic
        self.hem = hem
        self.skin = skin
        self.hair = hair
        self.scale = scale
        self.stride = stride
        self.arms = arms
        self.toga = toga
        self.praetexta = praetexta
        self.palla = palla
        self.veil = veil
        self.cloak = cloak
        self.hood = hood
        self.hat = hat
        self.apron = apron
        self.belt = belt
        self.carry = carry
        self.hair_style = hair_style
        self.stripe = stripe
        self.sleeves = sleeves
        self.exomis = exomis
        self.female = female
        self.child = child
        self.hem_radius = hem_radius
        self.mono = mono
        self.material = material
        self.seed = seed


TOGA_WOOL = (0.84, 0.81, 0.72)


def tone(spec, value):
    if spec.mono is not None:
        return spec.mono
    if value == "white" and spec.toga is not None:
        return TOGA_WOOL
    if isinstance(value, str):
        return WOOL[value]
    return value


POSES = {
    "down": [((0.255, -0.01, 1.1), (0.305, 0.04, 0.86)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "forward": [((0.225, 0.05, 1.12), (0.17, 0.3, 1.1)), ((-0.225, 0.05, 1.12), (-0.17, 0.3, 1.1))],
    "gesture": [((0.27, 0.12, 1.22), (0.31, 0.3, 1.43)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "carry": [((0.31, 0.03, 1.43), (0.25, 0.01, 1.61)), ((-0.215, 0.0, 1.1), (-0.22, 0.08, 0.87))],
    "head": [((0.27, 0.02, 1.58), (0.13, 0.01, 1.77)), ((-0.27, 0.02, 1.58), (-0.13, 0.01, 1.77))],
    "swing": [((0.215, -0.09, 1.1), (0.225, -0.17, 0.88)), ((-0.215, 0.09, 1.1), (-0.225, 0.18, 0.89))],
    "toga": [((0.255, -0.01, 1.1), (0.305, 0.05, 0.86)), ((-0.235, 0.02, 1.1), (-0.17, 0.25, 1.06))],
    "toga_gesture": [((0.27, 0.12, 1.22), (0.31, 0.3, 1.43)), ((-0.235, 0.02, 1.1), (-0.17, 0.25, 1.06))],
    "hip": [((0.3, -0.03, 1.13), (0.18, 0.03, 0.99)), ((-0.215, -0.01, 1.1), (-0.225, 0.05, 0.86))],
    "staff": [((0.24, 0.06, 1.1), (0.25, 0.2, 1.0)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "shoulder": [((0.29, 0.06, 1.4), (0.22, 0.12, 1.58)), ((-0.215, 0.09, 1.1), (-0.225, 0.18, 0.89))],
}


def torso_profile(spec, waist):
    if spec.female:
        return [(0.158, waist - 0.03), (0.162, 1.08), (0.188, 1.2), (0.19, 1.27), (0.188, 1.33), (0.165, 1.4),
                (0.095, 1.46), (0.0, 1.475)]
    rows = [(0.168, waist - 0.03)]
    if spec.belt is not None:
        rows.append((0.188, 1.065))
    rows += [(0.192, 1.2), (0.202, 1.32), (0.176, 1.405), (0.1, 1.465), (0.0, 1.48)]
    return rows


def torso_radius(profile, height):
    for (r0, z0), (r1, z1) in zip(profile[:-1], profile[1:]):
        if z0 <= height <= z1:
            return r0 + (r1 - r0) * (height - z0) / max(z1 - z0, 1e-6)
    return profile[0][0] if height < profile[0][1] else profile[-1][0]


def balteus(builder, color, profile, material, segments=16):
    segments = detail(segments)
    rings = []
    for offset, push in ((-0.09, 0.03), (0.0, 0.055), (0.09, 0.03)):
        ring = []
        for step in range(segments):
            angle = TAU * step / segments
            middle = 1.2 + 0.19 * math.cos(angle - math.pi)
            height = middle + offset
            radius = torso_radius(profile, min(height, 1.44)) + push
            ring.append(builder.point((radius * math.cos(angle), radius * math.sin(angle) * 0.7, height)))
        rings.append(ring)
    first = len(builder.polygons)
    for lower, upper in zip(rings[:-1], rings[1:]):
        for step in range(segments):
            following = (step + 1) % segments
            builder.face([lower[step], lower[following], upper[following], upper[step]], material, True)
    builder.tint(first, color)


def nose(builder, color, material):
    tip = (0.0, 0.123, 1.588)
    top = (0.0, 0.104, 1.642)
    left = (-0.017, 0.099, 1.582)
    right = (0.017, 0.099, 1.582)
    first = len(builder.polygons)
    builder.oriented([left, tip, top], (-1, 0.6, 0), material, True)
    builder.oriented([right, top, tip], (1, 0.6, 0), material, True)
    builder.oriented([left, right, tip], (0, 0.3, -1), material, True)
    builder.tint(first, color)


def hair_cap(builder, color, style, material):
    center = Vector((0.0, 0.004, 1.618))
    radii = (0.094, 0.11, 0.126)
    segments = detail(12)
    rows = 4

    def lowest(angle):
        front = 0.5 + 0.5 * math.cos(angle - FRONT)
        back = -0.75 if style == "long" else -0.62
        return back + front * (0.55 - back)
    rings = []
    for row in range(rows + 1):
        t = row / rows
        if row == rows:
            rings.append([builder.point(center + Vector((0.0, 0.0, radii[2])))] * segments)
            continue
        ring = []
        for step in range(segments):
            angle = TAU * step / segments
            latitude = lowest(angle) + (math.pi / 2 - lowest(angle)) * t
            tuft = 1.0 + 0.09 * math.sin(7 * angle + 2.0 * row) * (1.0 - t)
            fringe = 0.02 * max(0.0, math.cos(angle - FRONT)) * (1.0 - t)
            ring.append(builder.point(center + Vector(((radii[0] * tuft + fringe) * math.cos(latitude) * math.cos(angle),
                                                        (radii[1] * tuft + fringe) * math.cos(latitude) * math.sin(angle),
                                                        radii[2] * math.sin(latitude)))))
        rings.append(ring)
    first = len(builder.polygons)
    for lower, upper in zip(rings[:-1], rings[1:]):
        for step in range(segments):
            following = (step + 1) % segments
            builder.face([lower[step], lower[following], upper[following], upper[step]], material, True)
    builder.tint(first, color)
    if style == "long":
        ellipsoid(builder, (0.0, -0.105, 1.6), (0.055, 0.045, 0.05), color, 7, 4, material)


def head_parts(spec, skin, hair, material):
    top = MeshBuilder()
    tube(top, [(0.0, 0.0, 1.43), (0.0, 0.012, 1.535)], [0.05, 0.045], skin, 8, material, cap=False)
    ellipsoid(top, (0.0, 0.008, 1.615), (0.086, 0.102, 0.118), skin, 12, 8, material)
    ellipsoid(top, (0.0, 0.05, 1.535), (0.058, 0.05, 0.04), skin, 8, 4, material)
    nose(top, skin, material)
    if spec.hood is None and not spec.veil and not spec.female:
        for side in (-1, 1):
            ellipsoid(top, (side * 0.088, -0.004, 1.607), (0.012, 0.022, 0.03), skin, 5, 3, material)
    if spec.hood is None:
        hair_cap(top, hair, "long" if spec.female else spec.hair_style, material)
    veil = spec.palla if (spec.veil and spec.palla) else (spec.toga if spec.veil else None)
    if veil is not None:
        drape(top, tone(spec, veil), [(0.205, 1.37), (0.155, 1.47), (0.128, 1.56), (0.126, 1.645), (0.1, 1.725),
                                      (0.048, 1.768), (0.0, 1.78)], 14, start=FRONT + 0.7, sweep=TAU - 1.4,
              folds=(7, 0.035, spec.seed), squash=0.92, center=(0.0, -0.014), material=material)
    if spec.hood is not None:
        cowl = tone(spec, spec.hood)
        drape(top, cowl, [(0.215, 1.36), (0.162, 1.46), (0.134, 1.56), (0.132, 1.66)], 14, start=FRONT + 0.62,
              sweep=TAU - 1.24, folds=(5, 0.04, spec.seed), squash=0.92, center=(0.0, -0.02), material=material)
        drape(top, cowl, [(0.132, 1.66), (0.1, 1.74), (0.04, 1.8), (0.0, 1.83)], 10, folds=(3, 0.03, spec.seed),
              squash=0.92, center=(0.0, -0.03), material=material)
    if spec.hat is not None:
        straw = tone(spec, spec.hat)
        drape(top, straw, [(0.215, 1.7), (0.1, 1.722)], 12, folds=(3, 0.02, 0.0), squash=1.0, material=material)
        drape(top, tuple(c * 0.8 for c in straw), [(0.1, 1.71), (0.215, 1.695)], 12, folds=(3, 0.02, 0.0),
              squash=1.0, material=material)
        drape(top, straw, [(0.1, 1.715), (0.096, 1.78), (0.055, 1.805), (0.0, 1.81)], 10, folds=(0, 0.0, 0.0),
              squash=1.0, material=material)
    return top


def limb_set(builder, spec, skin, sleeve, arm, material):
    for index, (elbow, wrist) in enumerate(POSES[spec.arms]):
        side = 1 if index == 0 else -1
        elbow = Vector(elbow)
        wrist = Vector(wrist)
        shoulder = Vector((side * 0.182, 0.0, 1.38))
        covered = arm[index]
        upper_end = shoulder.lerp(elbow, 0.55 if spec.sleeves == "short" else 1.0)
        tube(builder, [shoulder + Vector((0.0, 0.0, 0.03)), shoulder.lerp(upper_end, 0.5), upper_end],
             [0.066, 0.068, 0.062], sleeve[index], 7, material)
        tube(builder, [shoulder.lerp(elbow, 0.35), elbow, elbow.lerp(wrist, 0.5), wrist], [0.046, 0.04, 0.037, 0.03],
             covered, 6, material, cap=False)
        direction = (wrist - elbow).normalized()
        tube(builder, [wrist, wrist + direction * 0.04, wrist + direction * 0.08, wrist + direction * 0.11],
             [0.03, 0.036, 0.032, 0.012], skin, 5, material, cap=False, squash=0.55)
        forward = Vector((0.0, 1.0, 0.0)) - direction * direction.y
        forward = forward.normalized() if forward.length > 1e-4 else Vector((0.0, 1.0, 0.0))
        thumb = wrist + direction * 0.025 + forward * 0.022
        tube(builder, [thumb, thumb + direction * 0.035 + forward * 0.018], [0.012, 0.008], skin, 4, material)


def legs(builder, spec, skin, leather, material):
    long = spec.hem < 0.25
    for side in (-1, 1):
        x = side * 0.085
        y = side * spec.stride
        if long:
            tube(builder, [(x, y - 0.02, 0.038), (x, y + 0.13, 0.03)], [0.037, 0.033], leather, 6, material,
                 start_cap=True)
            continue
        tube(builder, [(x, y - 0.06, 0.04), (x, y + 0.15, 0.03)], [0.038, 0.034], leather, 6, material,
             start_cap=True)
        tube(builder, [(x, y - 0.035, 0.05), (x * 1.02, y * 0.75, 0.25), (x * 1.04, y * 0.55, 0.46),
                       (x * 1.1, y * 0.25, spec.hem + 0.09)], [0.04, 0.052, 0.05, 0.064], skin, 6, material, cap=False)


def carried(builder, spec, material):
    terracotta = tone(spec, TERRACOTTA)
    if spec.carry == "amphora":
        frame = Matrix.Translation((0.19, -0.04, 1.6)) @ Matrix.Rotation(math.radians(-72), 4, "Y")
        drape(builder, terracotta, [(0.0, -0.32), (0.05, -0.28), (0.125, -0.13), (0.135, 0.04), (0.08, 0.17),
                                    (0.045, 0.2), (0.045, 0.3), (0.0, 0.31)], 8, folds=(0, 0.0, 0.0), squash=1.0,
              material=material, matrix=frame)
    elif spec.carry == "jar":
        drape(builder, terracotta, [(0.0, 1.765), (0.1, 1.79), (0.13, 1.88), (0.09, 1.99), (0.05, 2.02),
                                    (0.058, 2.07), (0.03, 2.07)], 9, folds=(0, 0.0, 0.0), squash=1.0,
              material=material)
    elif spec.carry == "basket":
        wicker = tone(spec, (0.62, 0.50, 0.32))
        drape(builder, wicker, [(0.0, 1.77), (0.15, 1.78), (0.2, 1.89), (0.21, 1.91)], 10, folds=(10, 0.03, 0.0),
              squash=1.0, material=material)
        drape(builder, tone(spec, (0.45, 0.55, 0.25)), [(0.2, 1.9), (0.13, 1.96), (0.0, 1.98)], 8,
              folds=(5, 0.12, 0.0), squash=1.0, material=material)
    elif spec.carry == "patera":
        frame = Matrix.Translation((0.31, 0.36, 1.43))
        drape(builder, tone(spec, (0.85, 0.66, 0.36)), [(0.0, -0.02), (0.1, 0.0), (0.11, 0.02)], 10,
              folds=(0, 0.0, 0.0), squash=1.0, material=material, matrix=frame)
    elif spec.carry == "bundle":
        ellipsoid(builder, (0.0, -0.21, 1.17), (0.17, 0.11, 0.21), tone(spec, (0.62, 0.55, 0.42)), 6, 4, material)
        tube(builder, [(0.15, 0.12, 1.4), (-0.08, 0.15, 1.15), (-0.18, 0.05, 0.98)], [0.016, 0.016, 0.016],
             tone(spec, LEATHER), 4, material)
    elif spec.carry == "staff":
        tube(builder, [(0.255, 0.26, 0.01), (0.25, 0.2, 1.0), (0.245, 0.15, 1.52)], [0.018, 0.018, 0.016],
             tone(spec, WOOD), 5, material)
    elif spec.carry == "pole":
        tube(builder, [(0.23, 0.34, 1.47), (0.21, 0.0, 1.63), (0.16, -0.6, 1.72)], [0.02, 0.02, 0.018],
             tone(spec, WOOD), 5, material, start_cap=True)
        ellipsoid(builder, (0.16, -0.6, 1.5), (0.13, 0.12, 0.17), tone(spec, (0.58, 0.47, 0.30)), 7, 4, material)
    elif spec.carry == "scroll":
        tube(builder, [(0.29, 0.36, 1.41), (0.33, 0.33, 1.47)], [0.02, 0.02], tone(spec, (0.86, 0.80, 0.66)), 5,
             material, start_cap=True)


def person(spec):
    builder = MeshBuilder()
    m = spec.material
    rng = random.Random(spec.seed)
    phase = rng.uniform(0, TAU)
    skin = tone(spec, SKIN[spec.skin])
    hair = tone(spec, tuple(min(1.0, value * 1.2) for value in HAIR[spec.hair]))
    tunic = tone(spec, spec.tunic)
    leather = tone(spec, LEATHER)
    waist = 1.0
    legs(builder, spec, skin, leather, m)
    hem_radius = spec.hem_radius or (0.215 if spec.hem < 0.25 else 0.205)
    hem_radius += spec.stride * 0.3
    if spec.toga is None:
        middle = (spec.hem + waist) / 2
        skirt = [(hem_radius, spec.hem), (hem_radius * 0.93 + 0.012, middle), (0.172, waist)]
        drape(builder, tunic, skirt, 20, folds=(5, 0.045, phase), squash=0.74, material=m,
              dip=lambda angle: 0.03 * math.sin(angle) if spec.female else 0.0)
        if spec.stripe is not None:
            stripe = tone(spec, spec.stripe)
            for side in (-1, 1):
                strip(builder, stripe, [(side * 0.07, 0.132, 1.38), (side * 0.072, 0.132, 1.0),
                                        (side * 0.08, 0.152, spec.hem + 0.06)], 0.035, 1, m, 0.004)
    profile = torso_profile(spec, waist)
    torso_colour = tunic
    if spec.exomis:
        torso_colour = lambda angle, height: skin if (math.cos(angle) > 0.2 and height > 1.17) else tunic
    drape(builder, torso_colour, profile, 12, folds=(3, 0.02, phase), squash=0.66, material=m)
    if spec.belt is not None:
        drape(builder, tone(spec, spec.belt), [(0.177, 0.985), (0.179, 1.03)], 12, folds=(0, 0.0, 0.0),
              squash=0.68, material=m)
    sleeve = [tunic, tunic]
    arm = [skin, skin]
    if spec.exomis:
        sleeve[0] = skin
    if spec.toga is not None:
        toga = tone(spec, spec.toga)
        sleeve[1] = toga
        arm[1] = toga
        dusty = tuple(value * 0.9 for value in toga)
        hem_colour = lambda angle, height, toga=toga, dusty=dusty: dusty if height < 0.3 else toga
        drape(builder, hem_colour, [(0.19, 0.1), (0.235, 0.45), (0.225, 0.8), (0.19, 1.03)], 20,
              folds=(7, 0.07, phase), squash=0.76, material=m, dip=lambda angle: -0.05 * math.sin(angle))
        swag = lambda angle: -0.11 * max(0.0, math.cos(angle - FRONT - 0.35))
        drape(builder, toga, [(0.262, 0.52), (0.252, 0.78), (0.222, 1.02), (0.2, 1.14)], 16, start=FRONT - 1.25,
              sweep=2.4, folds=(8, 0.09, phase), squash=0.8, material=m, dip=swag)
        if spec.praetexta is not None:
            drape(builder, tone(spec, spec.praetexta), [(0.266, 0.505), (0.265, 0.56)], 16, start=FRONT - 1.25,
                  sweep=2.4, folds=(8, 0.09, phase), squash=0.8, material=m, dip=swag, fade=0.0)
        balteus(builder, toga, profile, m)
        strip(builder, toga, [(-0.11, 0.13, 1.43), (-0.12, 0.165, 1.08), (-0.135, 0.19, 0.7), (-0.135, 0.2, 0.34)],
              0.15, 1, m)
        strip(builder, toga, [(-0.12, -0.13, 1.43), (-0.1, -0.165, 0.95), (-0.08, -0.185, 0.42)], 0.2, -1, m)
        strip(builder, toga, [(-0.2, 0.22, 1.06), (-0.22, 0.24, 0.82), (-0.23, 0.25, 0.6)], 0.12, 1, m)
    if spec.palla is not None:
        mantle = tone(spec, spec.palla)
        sleeve[1] = mantle
        drape(builder, mantle, [(0.238, 0.58), (0.25, 0.86), (0.234, 1.16), (0.207, 1.34), (0.13, 1.45)], 20,
              start=math.radians(125), sweep=math.radians(290), folds=(6, 0.06, phase), squash=0.78, material=m,
              dip=lambda angle: 0.12 * math.cos(angle))
    if spec.cloak is not None:
        sagum = tone(spec, spec.cloak)
        sleeve[1] = sagum
        drape(builder, sagum, [(0.122, 1.475), (0.238, 1.385), (0.258, 1.0), (0.272, 0.64)], 16,
              start=math.radians(100), sweep=math.radians(250), folds=(4, 0.06, phase), squash=0.8, material=m,
              dip=lambda angle: -0.06 * math.sin(angle))
        ellipsoid(builder, (0.15, 0.1, 1.41), (0.025, 0.02, 0.025), tone(spec, BRONZE_PIN), 5, 3, m)
    if spec.apron is not None:
        drape(builder, tone(spec, spec.apron), [(0.212, 0.56), (0.2, 0.8), (0.184, 1.0)], 7, start=FRONT - 0.85,
              sweep=1.7, folds=(5, 0.03, phase), squash=0.78, material=m)
    limb_set(builder, spec, skin, sleeve, arm, m)
    top = head_parts(spec, skin, hair, m)
    if spec.carry in ("jar", "basket"):
        carried(top, spec, m)
    else:
        carried(builder, spec, m)
    head_scale = 1.2 if spec.child else 1.0
    builder.merge(top, Matrix.Translation((0.0, 0.0, 1.45)) @ Matrix.Scale(head_scale, 4)
                  @ Matrix.Translation((0.0, 0.0, -1.45)))
    if spec.scale != 1.0:
        scaled = MeshBuilder()
        scaled.merge(builder, Matrix.Scale(spec.scale, 4))
        return scaled
    return builder


FIGURES = {
    "fig_toga": Look("white", hem=0.12, skin=0, hair=0, toga="white", arms="toga", seed=1),
    "fig_toga_gesture": Look("white", hem=0.12, skin=1, hair=2, toga="white", arms="toga_gesture", carry="scroll",
                             seed=2),
    "fig_priest": Look("white", hem=0.12, skin=0, hair=2, toga="white", praetexta="purple", veil=True,
                       arms="toga_gesture", carry="patera", seed=3),
    "fig_worker": Look("ochre", hem=0.55, skin=2, hair=1, belt=LEATHER, arms="shoulder", carry="pole", exomis=True,
                       hat=(0.80, 0.68, 0.42), seed=4),
    "fig_porter": Look("madder", hem=0.56, skin=1, hair=3, belt="brown", arms="carry", carry="amphora", seed=5),
    "fig_rural": Look("undyed", hem=0.52, skin=2, hair=1, cloak="brown", belt="dark", carry="staff", arms="staff",
                      hood="brown", seed=6),
    "fig_matron": Look("woad", hem=0.03, skin=0, hair=0, palla="rose", veil=True, female=True, sleeves="long",
                       arms="hip", scale=0.95, seed=7),
    "fig_woman": Look("weld", hem=0.04, skin=1, hair=1, palla="green", arms="head", carry="jar", female=True,
                      sleeves="long", scale=0.95, seed=8),
    "fig_child": Look("white", hem=0.5, skin=0, hair=1, scale=0.64, belt="madder", stripe="madder", child=True,
                      seed=9),
    "fig_merchant": Look("grey", hem=0.55, skin=1, hair=0, apron="undyed", arms="gesture", belt="brown", seed=10),
}

WALKERS = {
    "walker_citizen": Look("white", hem=0.12, skin=1, hair=0, toga="white", arms="toga", stride=0.17, seed=11),
    "walker_worker": Look("brown", hem=0.55, skin=2, hair=1, belt="dark", stride=0.2, arms="swing", seed=12),
    "walker_woman": Look("madder", hem=0.05, skin=0, hair=1, palla="undyed", stride=0.14, female=True,
                         sleeves="long", arms="swing", scale=0.95, seed=13),
    "walker_porter": Look("ochre", hem=0.55, skin=1, hair=3, stride=0.2, arms="carry", carry="amphora", belt="brown",
                          seed=14),
    "walker_matron": Look("rose", hem=0.04, skin=1, hair=2, palla="woad", veil=True, female=True, sleeves="long",
                          arms="swing", stride=0.14, scale=0.95, seed=15),
    "walker_rural": Look("green", hem=0.52, skin=2, hair=0, cloak="dark", belt="brown", stride=0.2, arms="swing",
                         hat=(0.78, 0.66, 0.40), carry="bundle", seed=16),
}


ANIMALS = {
    "mule": dict(length=1.25, height=0.72, girth=0.48, colour=(0.38, 0.28, 0.2), neck=0.5, ears=0.2, horns=0.0,
                 lift=0.55),
    "donkey": dict(length=1.02, height=0.56, girth=0.42, colour=(0.52, 0.47, 0.42), neck=0.42, ears=0.25, horns=0.0,
                   lift=0.45),
    "ox": dict(length=1.8, height=0.62, girth=0.72, colour=(0.80, 0.74, 0.62), neck=0.4, ears=0.1, horns=0.32,
               lift=0.05),
    "goat": dict(length=0.74, height=0.36, girth=0.3, colour=(0.30, 0.24, 0.18), neck=0.28, ears=0.09, horns=0.18,
                 lift=0.5),
    "dog": dict(length=0.66, height=0.26, girth=0.23, colour=(0.55, 0.42, 0.28), neck=0.2, ears=0.07, horns=0.0,
                lift=0.6),
}


def beast(kind):
    builder = MeshBuilder()
    s = ANIMALS[kind]
    c = s["colour"]
    dark = tuple(value * 0.62 for value in c)
    g = s["girth"]
    half = s["length"] / 2
    body_z = s["height"] + g * 0.55
    ellipsoid(builder, (0.0, 0.0, body_z), (g * 0.5, half * 1.05, g * 0.55), c, 10, 6)
    shoulder = Vector((0.0, half * 0.72, body_z + g * 0.12))
    head_base = shoulder + Vector((0.0, s["neck"] * 0.45, s["neck"] * s["lift"] + g * 0.15))
    tube(builder, [shoulder, shoulder.lerp(head_base, 0.5), head_base], [g * 0.3, g * 0.25, g * 0.2], c, 6)
    snout = head_base + Vector((0.0, s["neck"] * 0.6, -s["neck"] * 0.42))
    tube(builder, [head_base - Vector((0.0, 0.03, -0.02)), head_base.lerp(snout, 0.45), snout],
         [g * 0.21, g * 0.2, g * 0.13], c, 6, start_cap=True)
    for side in (-1, 1):
        for end in (-1, 1):
            top = Vector((side * g * 0.27, end * (half * 0.74), body_z - g * 0.1))
            knee = Vector((side * g * 0.25, end * (half * 0.74) + 0.03 * end, s["height"] * 0.5))
            hoof = Vector((side * g * 0.25, end * (half * 0.74), 0.0))
            tube(builder, [top, knee, hoof + Vector((0.0, 0.0, 0.06))], [g * 0.21, g * 0.12, g * 0.1], c, 5,
                 cap=False)
            tube(builder, [hoof + Vector((0.0, 0.0, 0.07)), hoof + Vector((0.0, 0.01, 0.0))], [g * 0.09, g * 0.1],
                 dark, 5)
        if s["ears"]:
            tube(builder, [head_base + Vector((side * 0.05, -0.02, 0.05)),
                           head_base + Vector((side * 0.11, -0.06, 0.05 + s["ears"]))], [0.028, 0.006], c, 4)
        if s["horns"]:
            tube(builder, [head_base + Vector((side * 0.07, 0.03, 0.07)),
                           head_base + Vector((side * (0.12 + s["horns"] * 0.6), 0.08, 0.1)),
                           head_base + Vector((side * (0.1 + s["horns"]), 0.12, 0.08 + s["horns"] * 0.7))],
                 [0.035, 0.025, 0.006], (0.86, 0.82, 0.70), 4)
    tail = Vector((0.0, -half * 1.02, body_z + g * 0.2))
    tube(builder, [tail, tail + Vector((0.0, -0.08, -g * 0.6)), tail + Vector((0.0, -0.06, -g * 1.25))],
         [0.03, 0.025, 0.04], dark, 4)
    return builder


def pack_beast(kind):
    builder = beast(kind)
    s = ANIMALS[kind]
    top = s["height"] + s["girth"] * 1.1
    for side in (-1, 1):
        ellipsoid(builder, (side * 0.3, 0.0, top - 0.18), (0.13, 0.26, 0.2), (0.55, 0.43, 0.28), 7, 4)
    drape(builder, (0.40, 0.22, 0.16), [(0.3, top - 0.12), (0.24, top - 0.02), (0.0, top + 0.02)], 8,
          folds=(0, 0.0, 0.0), squash=1.4)
    return builder


def wheel(builder, x, y, radius, width, spokes=0):
    frame = Matrix.Translation((x, y, radius)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    if spokes:
        drape(builder, WOOD, [(radius - 0.06, -width / 2), (radius, -width / 2), (radius, width / 2),
                              (radius - 0.06, width / 2), (radius - 0.06, -width / 2)], 12, folds=(0, 0.0, 0.0),
              squash=1.0, matrix=frame)
        for index in range(spokes):
            angle = math.pi * index / spokes
            direction = Vector((0.0, math.cos(angle), math.sin(angle))) * (radius - 0.04)
            tube(builder, [Vector((x, y, radius)) - direction, Vector((x, y, radius)) + direction], [0.025, 0.025],
                 WOOD, 4)
        drape(builder, WOOD, [(0.0, -width), (0.09, -width), (0.09, width), (0.0, width)], 6, folds=(0, 0.0, 0.0),
              squash=1.0, matrix=frame)
    else:
        drape(builder, (0.40, 0.29, 0.19), [(0.0, -width / 2), (radius, -width / 2), (radius, width / 2),
                                            (0.0, width / 2)], 12, folds=(0, 0.0, 0.0), squash=1.0, matrix=frame)


def boxed(builder, color, minimum, maximum):
    first = len(builder.polygons)
    builder.box(minimum, maximum, MATTE)
    builder.tint(first, color)


def ox_cart():
    builder = MeshBuilder()
    for side in (-1, 1):
        wheel(builder, side * 0.78, -0.6, 0.6, 0.14)
        builder.merge(beast("ox"), placement(side * 0.55, 2.45, 0.0))
    boxed(builder, WOOD, (-0.7, -1.9, 0.72), (0.7, 0.7, 0.86))
    for side in (-1, 1):
        boxed(builder, (0.40, 0.29, 0.19), (side * 0.7 - 0.05, -1.9, 0.86), (side * 0.7 + 0.05, 0.7, 1.3))
    tube(builder, [(0.0, 0.6, 0.8), (0.0, 3.25, 1.3)], [0.06, 0.05], WOOD, 5)
    tube(builder, [(-0.85, 3.25, 1.48), (0.85, 3.25, 1.48)], [0.065, 0.065], WOOD, 5, start_cap=True)
    for index, (x, y) in enumerate(((-0.35, -1.4), (0.3, -1.3), (-0.3, -0.6), (0.35, -0.5), (0.0, 0.1))):
        sack = (0.62, 0.55, 0.42) if index % 2 else (0.72, 0.62, 0.45)
        ellipsoid(builder, (x, y, 1.08), (0.24, 0.32, 0.2), sack, 7, 4)
    builder.merge(person(Look("brown", hem=0.55, skin=2, hair=1, cloak="dark", stride=0.18, arms="staff",
                              carry="staff", hat=(0.78, 0.66, 0.40), seed=21)), placement(-1.3, 2.0, 0.0))
    return builder


def mule_wagon():
    builder = MeshBuilder()
    for x in (-0.8, 0.8):
        for y in (-1.6, 0.4):
            wheel(builder, x, y, 0.5, 0.08, spokes=4)
    boxed(builder, WOOD, (-0.72, -2.0, 0.62), (0.72, 0.8, 1.15))
    arch = [(-0.75 * math.cos(math.pi * i / 6), 1.15 + 0.7 * math.sin(math.pi * i / 6)) for i in range(7)]
    rows = [[(x, y, z) for x, z in arch] for y in (-2.0, -1.2, -0.4)]
    for facing in (1, -1):
        first = len(builder.polygons)
        builder.surface(rows if facing > 0 else list(reversed(rows)), MATTE, smooth=True, facing=(0, 0, facing))
        builder.tint(first, (0.82, 0.76, 0.62))
    tube(builder, [(0.0, 0.8, 0.75), (0.0, 3.3, 1.1)], [0.045, 0.04], WOOD, 5)
    for side in (-1, 1):
        builder.merge(beast("mule"), placement(side * 0.45, 2.5, 0.0))
    builder.merge(person(Look("madder", hem=0.55, skin=1, hair=0, cloak="brown", arms="forward", seed=22)),
                  placement(0.0, 0.25, 0.55))
    return builder


def basket(builder, x, y, z, radius, produce, seed):
    drape(builder, (0.62, 0.50, 0.32), [(radius * 0.8, z), (radius, z + radius * 0.8), (radius * 1.05,
                                                                                         z + radius * 0.9)], 9,
          folds=(9, 0.03, 0.0), squash=1.0, center=(x, y))
    drape(builder, produce, [(radius, z + radius * 0.85), (radius * 0.6, z + radius * 1.25), (0.0, z + radius * 1.4)],
          7, folds=(4, 0.12, seed), squash=1.0, center=(x, y))


def amphora(builder, matrix, color=TERRACOTTA):
    drape(builder, color, [(0.0, -0.05), (0.05, 0.02), (0.15, 0.25), (0.16, 0.5), (0.07, 0.72), (0.05, 0.9),
                           (0.06, 0.93)], 7, folds=(0, 0.0, 0.0), squash=1.0, matrix=matrix)


def market_stall(seed=0, awning=(0.80, 0.72, 0.58)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    boxed(builder, WOOD, (-1.2, -0.45, 0.75), (1.2, 0.45, 0.82))
    cloth = (0.86, 0.80, 0.66)
    first = len(builder.polygons)
    builder.surface([[(x, -0.47 - 0.02 * math.sin(x * 9.0), 0.8) for x in (-1.2, -0.6, 0.0, 0.6, 1.2)],
                     [(x, -0.5 - 0.03 * math.sin(x * 9.0 + 1.0), 0.35) for x in (-1.2, -0.6, 0.0, 0.6, 1.2)]],
                    MATTE, smooth=True, facing=(0, -1, 0))
    builder.tint(first, cloth)
    boxed(builder, (0.48, 0.37, 0.26), (-1.15, -0.4, 0.0), (1.15, 0.4, 0.75))
    for x in (-1.25, 1.25):
        for y in (-0.5, 0.9):
            tube(builder, [(x, y, 0.0), (x, y, 2.2 if y > 0 else 2.0)], [0.04, 0.035], WOOD, 5)
    light = awning
    dark = (0.66, 0.30, 0.22) if seed % 2 else (0.42, 0.48, 0.56)
    columns = 10
    rows_count = 4
    grid = []
    for row in range(rows_count + 1):
        t = row / rows_count
        y = -0.8 + 1.85 * t
        line = []
        for column in range(columns + 1):
            s = column / columns
            x = -1.45 + 2.9 * s
            sag = 0.09 * math.sin(math.pi * s) * math.sin(math.pi * t)
            ripple = 0.03 * math.sin(column * math.pi + row * 0.7)
            line.append((x, y, 1.95 + 0.35 * t - sag + ripple))
        grid.append(line)
    for row in range(rows_count):
        for column in range(columns):
            color = light if (column // 2) % 2 else dark
            quad = [grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]]
            for facing in (1, -1):
                first = len(builder.polygons)
                builder.oriented(quad, (0, 0, facing), MATTE, True)
                builder.tint(first, color if facing > 0 else tuple(v * 0.85 for v in color))
    front = grid[0]
    for column in range(columns):
        a, b = front[column], front[column + 1]
        drop = 0.22 if column % 2 else 0.16
        quad = [a, b, (b[0], b[1], b[2] - drop), (a[0], a[1], a[2] - drop)]
        color = light if (column // 2) % 2 else dark
        for facing in (-1, 1):
            first = len(builder.polygons)
            builder.oriented(quad, (0, facing, 0), MATTE)
            builder.tint(first, color)
    goods = [(0.62, 0.48, 0.26), (0.45, 0.58, 0.28), (0.70, 0.30, 0.18), (0.85, 0.72, 0.40), (0.42, 0.22, 0.30)]
    for index in range(5):
        x = -0.95 + index * 0.47
        basket(builder, x, rng.uniform(-0.15, 0.1), 0.82, 0.17, goods[(index + seed) % len(goods)], seed + index)
    for index in range(3):
        tube(builder, [(-1.05 + index * 0.05, 0.42, 1.95), (-1.05 + index * 0.05, 0.42, 1.55 - index * 0.05)],
             [0.035, 0.05], goods[(index + 2) % len(goods)], 5)
    for index, color in enumerate(((0.64, 0.28, 0.20), (0.42, 0.49, 0.58), (0.80, 0.71, 0.42))):
        tube(builder, [(0.6, -0.1 + index * 0.17, 0.89), (1.1, -0.1 + index * 0.17, 0.89)], [0.075, 0.075],
             color, 6, start_cap=True)
    amphora(builder, Matrix.Translation((1.5, 0.3, 0.0)))
    amphora(builder, Matrix.Translation((1.55, -0.05, 0.0)), (0.78, 0.55, 0.40))
    amphora(builder, Matrix.Translation((1.62, 0.12, 0.08)) @ Matrix.Rotation(math.radians(80), 4, "Y"),
            (0.66, 0.40, 0.27))
    builder.merge(person(FIGURES["fig_merchant"]), placement(0.0, 0.9, 0.0, math.pi))
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
        spec = Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=(1.0, 1.0, 1.0), material="bronze",
                    seed=31)
    else:
        spec = Look("white", hem=0.03, palla="white", veil=True, female=True, sleeves="long", arms="hip",
                    mono=(0.97, 0.95, 0.9), material="lens_smooth", seed=32)
    builder.merge(person(spec), Matrix.Translation((0.0, 0.0, 1.7)) @ Matrix.Rotation(math.pi, 4, "Z")
                  @ Matrix.Scale(1.12, 4))
    return builder
