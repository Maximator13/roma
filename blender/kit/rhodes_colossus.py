import math
import random

from mathutils import Matrix, Vector

from .alexandrie_monuments import boulder
from .geometry import MeshBuilder
from .nimes_figures import tube

TAU = 2 * math.pi
S = 17.8
BRONZE = "bronze_patina"
IRON = "iron_rust"
MARBLE = "marble"
STONE = "limestone"
OUTER = (1.0, 1.0, 1.0)
SEAM = (0.97, 0.96, 0.95)
INNER = (0.34, 0.29, 0.25)
RIM = (1.0, 0.80, 0.58)
BALLAST = "ballast_stone"
BALLAST_TINT = (0.62, 0.58, 0.52)
INSCRIPTION = (0.55, 0.48, 0.40)
PEDESTAL_TINT = (0.98, 0.93, 0.84)
SHELL = 0.22
PEDESTAL = [(17.0, 0.0, 3.8), (14.4, 3.8, 7.6), (12.0, 7.6, 11.2)]
TOP = 11.2
KNEE = 0.5
UP = Vector((0.0, 0.0, 1.0))


def frame_axes(direction, hint=None):
    direction = direction.normalized()
    hint = hint if hint is not None else (UP if abs(direction.dot(UP)) < 0.9 else Vector((1.0, 0.0, 0.0)))
    u = (hint - direction * hint.dot(direction)).normalized()
    v = direction.cross(u).normalized()
    return u, v


def jag(rng, count, amplitude):
    phases = [rng.uniform(0, TAU) for _ in range(3)]
    values = []
    for k in range(count):
        t = TAU * k / count
        value = (0.5 * math.sin(t * 2 + phases[0]) + 0.3 * math.sin(t * 5 + phases[1])
                 + 0.2 * math.sin(t * 9 + phases[2]) + rng.uniform(-0.25, 0.25))
        values.append(amplitude * (0.5 + 0.5 * max(-1.0, min(1.0, value))))
    return values


class Ring:
    def __init__(self, centre, u, v, a, b, shape=None, back=None):
        self.centre = Vector(centre)
        self.u = Vector(u)
        self.v = Vector(v)
        self.a = a
        self.b = b
        self.back = back if back is not None else b
        self.shape = shape

    def radius(self):
        return (self.a + self.b + self.back) / 3

    def point(self, angle, inset=0.0, push=None):
        scale = self.shape(angle) if self.shape else 1.0
        depth = self.b if math.sin(angle) >= 0 else self.back
        a = max(self.a * scale - inset, 0.02)
        b = max(depth * scale - inset, 0.02)
        offset = push if push is not None else Vector()
        return self.centre + self.u * (a * math.cos(angle)) + self.v * (b * math.sin(angle)) + offset


def shell(builder, rings, segments, rng, open_start=False, open_end=False, thickness=SHELL, amplitude=0.8,
          seams=2.4, colour=OUTER, round_end=False):
    count = len(rings)
    jags = {}
    if open_start:
        jags[0] = jag(rng, segments, amplitude)
    if open_end:
        jags[count - 1] = jag(rng, segments, amplitude)

    def axis_at(index):
        a = rings[max(index - 1, 0)].centre
        b = rings[min(index + 1, count - 1)].centre
        return (b - a).normalized()

    first_axis = axis_at(0)
    forward = rings[0].u.cross(rings[0].v).dot(first_axis) >= 0
    order = list(range(segments)) if forward else [(segments - k) % segments for k in range(segments)]
    angles = [TAU * k / segments for k in order]
    hollow = open_start or open_end
    outer = []
    inner = []
    along = []
    travelled = 0.0
    for index, ring in enumerate(rings):
        if index:
            travelled += (ring.centre - rings[index - 1].centre).length
        along.append(travelled)
        axis = axis_at(index)
        sign = 1.0 if index == 0 else -1.0
        row_outer = []
        row_inner = []
        for k, angle in enumerate(angles):
            push = axis * (sign * jags[index][k]) if index in jags else None
            row_outer.append(builder.point(ring.point(angle, 0.0, push)))
            if hollow:
                row_inner.append(builder.point(ring.point(angle, thickness, push)))
        outer.append(row_outer)
        inner.append(row_inner)
    for index in range(count - 1):
        r0 = rings[index].radius()
        r1 = rings[index + 1].radius()
        v0, v1 = along[index], along[index + 1]
        seam = int(v0 / seams) != int(v1 / seams)
        shade = tuple(c * s for c, s in zip(colour, SEAM)) if seam else colour
        for k in range(segments):
            j = (k + 1) % segments
            u0 = TAU * k / segments
            u1 = TAU * (k + 1) / segments
            uvs = [(u0 * r0, v0), (u1 * r0, v0), (u1 * r1, v1), (u0 * r1, v1)]
            builder.face([outer[index][k], outer[index][j], outer[index + 1][j], outer[index + 1][k]], BRONZE, True,
                         uvs, shade)
            if hollow:
                builder.face([inner[index][k], inner[index + 1][k], inner[index + 1][j], inner[index][j]], BRONZE,
                             True, [uvs[0], uvs[3], uvs[2], uvs[1]], INNER)
    for index, is_open, flip in ((0, open_start, True), (count - 1, open_end, False)):
        if is_open:
            for k in range(segments):
                j = (k + 1) % segments
                quad = [outer[index][k], inner[index][k], inner[index][j], outer[index][j]]
                builder.face(quad if flip else list(reversed(quad)), BRONZE, False,
                             [(k * 0.4, 0.0), (k * 0.4, 0.2), (k * 0.4 + 0.4, 0.2), (k * 0.4 + 0.4, 0.0)], RIM)
        else:
            axis = axis_at(index)
            reach = rings[index].radius() * (0.45 if round_end else 0.0)
            centre = builder.point(rings[index].centre + axis * ((-1.0 if flip else 1.0) * reach))
            ring = rings[index]
            for k in range(segments):
                j = (k + 1) % segments
                tri = [outer[index][k], outer[index][j], centre]
                uvs = [((Vector(builder.positions[v]) - ring.centre).dot(ring.u),
                        (Vector(builder.positions[v]) - ring.centre).dot(ring.v)) for v in tri]
                builder.face(list(reversed(tri)) if flip else tri, BRONZE, True,
                             list(reversed(uvs)) if flip else uvs, colour)
    return outer


def iron_cage(builder, rings, rng, depth=4, bars=6, stick_out=1.2):
    count = len(rings)
    end = rings[-1]
    start = rings[max(count - 1 - depth, 0)]
    axis = (end.centre - start.centre).normalized()
    for k in range(bars):
        angle = TAU * k / bars + rng.uniform(-0.2, 0.2)
        a = start.point(angle, SHELL + 0.2)
        b = end.point(angle, SHELL + 0.2)
        bend = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)))
        tip = b + axis * rng.uniform(0.2, stick_out) + bend
        tube(builder, [a, b, tip], [0.07, 0.07, 0.05], (1.0, 1.0, 1.0), 5, IRON)
    for fraction in (0.3, 0.75):
        ring = rings[max(0, min(count - 1, int(round(count - 1 - depth * (1 - fraction)))))]
        angle = rng.uniform(0, math.pi)
        tube(builder, [ring.point(angle, SHELL + 0.05), ring.point(angle + math.pi, SHELL + 0.05)], [0.06, 0.06],
             (1.0, 1.0, 1.0), 4, IRON)


def down_of(matrix):
    return (matrix.to_3x3().inverted() @ Vector((0.0, 0.0, -1.0))).normalized()


def ballast(builder, rings, rng, count, depth, down):
    end = rings[-1]
    start = rings[max(len(rings) - 1 - depth, 0)]
    axis = (end.centre - start.centre).normalized()
    floor = (down - axis * down.dot(axis)).normalized()
    lateral = axis.cross(floor).normalized()
    for k in range(count):
        t = rng.uniform(0.05, 0.92)
        centre = start.centre.lerp(end.centre, t)
        reach = 1e9
        for ring in (start, end):
            angle = math.atan2(floor.dot(ring.v), floor.dot(ring.u))
            reach = min(reach, (ring.point(angle, SHELL) - ring.centre).length)
        size = min(rng.uniform(0.5, 0.9), reach * 0.4) / 2
        side = rng.uniform(-0.35, 0.35) * reach
        drop = math.sqrt(max(reach * reach - side * side, 0.0)) - size * 0.8
        tone = rng.uniform(0.86, 1.1)
        boulder(builder, centre + floor * drop + lateral * side,
                (size * 1.2, size * rng.uniform(0.85, 1.1), size * rng.uniform(0.8, 1.0)),
                tuple(c * tone for c in BALLAST_TINT), rng, BALLAST, 10, 5)


def limb_rings(points, profile, hint, shape=None):
    rings = []
    for index, (point, radii) in enumerate(zip(points, profile)):
        prev = points[max(index - 1, 0)]
        nxt = points[min(index + 1, len(points) - 1)]
        u, v = frame_axes(Vector(nxt) - Vector(prev), hint)
        rings.append(Ring(point, u, v, radii[0], radii[1], shape, radii[2] if len(radii) > 2 else None))
    return rings


def torso_shape(h):
    def shape(angle):
        front = math.sin(angle)
        side = math.cos(angle)
        value = 1.0
        if 1.22 < h < 1.42:
            pec = (math.exp(-((angle - math.radians(58)) ** 2) / 0.1)
                   + math.exp(-((angle - math.radians(122)) ** 2) / 0.1))
            value += 0.08 * pec * math.sin(math.pi * (h - 1.22) / 0.2)
            value -= 0.03 * math.exp(-((angle - math.pi / 2) ** 2) / 0.02)
        if 1.0 < h < 1.2 and front > 0.7:
            value += 0.022 * math.cos((h - 1.0) * 95.0) * (front - 0.7) / 0.3
            value -= 0.02 * math.exp(-((angle - math.pi / 2) ** 2) / 0.01)
        if 0.96 < h < 1.1 and abs(front) < 0.5:
            value += 0.03 * math.exp(-((abs(side) - 0.95) ** 2) / 0.01) * math.sin(math.pi * (h - 0.96) / 0.14)
        if front < -0.9:
            value -= 0.06 * (-front - 0.9) / 0.1
        if 1.3 < h < 1.46 and front < -0.2:
            value += 0.05 * math.exp(-((abs(side) - 0.55) ** 2) / 0.04)
        if 1.4 < h < 1.49 and abs(side) > 0.7:
            value += 0.06 * math.sin(math.pi * (h - 1.4) / 0.09) * (abs(side) - 0.7) / 0.3
        return value
    return shape


TORSO = [(0.84, 0.12, 0.08, 0.09), (0.88, 0.16, 0.085, 0.112), (0.93, 0.178, 0.09, 0.122),
         (0.99, 0.17, 0.095, 0.104), (1.05, 0.153, 0.1, 0.086), (1.10, 0.146, 0.102, 0.08),
         (1.16, 0.152, 0.106, 0.085), (1.22, 0.162, 0.112, 0.09), (1.28, 0.172, 0.124, 0.096),
         (1.34, 0.18, 0.128, 0.1), (1.39, 0.192, 0.118, 0.1), (1.43, 0.207, 0.1, 0.094), (1.46, 0.2, 0.08, 0.084),
         (1.485, 0.15, 0.064, 0.07), (1.50, 0.09, 0.06, 0.06), (1.52, 0.062, 0.058, 0.055),
         (1.555, 0.058, 0.056, 0.054)]


def body_point(h, side=0.0, front=0.0):
    return Vector((side * S, front * S, h * S))


def doubled(stations):
    result = []
    for first, second in zip(stations[:-1], stations[1:]):
        result.append(first)
        result.append(tuple((p + q) / 2 for p, q in zip(first, second)))
    return result + [stations[-1]]


def torso(builder, rng, down):
    rings = []
    for h, a, b, back in doubled(TORSO):
        rings.append(Ring(body_point(h), Vector((1, 0, 0)), Vector((0, 1, 0)), a * S, b * S, torso_shape(h),
                          back * S))
    shell(builder, rings, 48, rng, open_start=False, open_end=True, amplitude=0.7)
    iron_cage(builder, rings, rng, depth=6, bars=5, stick_out=1.4)
    ballast(builder, rings, rng, 12, 6, down)
    return rings


def thigh_shape(h):
    def shape(angle):
        front = math.sin(angle)
        value = 1.0
        if h < 0.6 and front > 0.4:
            value += 0.07 * (front - 0.4) / 0.6 * (0.6 - h) / 0.1
        if h > 0.66 and front > 0.2:
            value += 0.04 * math.sin(math.pi * (h - 0.66) / 0.27) * (front - 0.2) / 0.8
        return value
    return shape


def thigh(builder, rng, side, down):
    heights = [0.93, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58, 0.53, 0.5]
    radii = [(0.08, 0.075, 0.08), (0.086, 0.082, 0.082), (0.083, 0.082, 0.076), (0.077, 0.078, 0.07),
             (0.07, 0.072, 0.064), (0.064, 0.066, 0.058), (0.058, 0.06, 0.052), (0.054, 0.05, 0.05),
             (0.05, 0.048, 0.05)]
    rings = []
    for h, a, b, c in doubled([(h, a, b, c) for h, (a, b, c) in zip(heights, radii)]):
        t = (h - 0.5) / 0.43
        x = side * (0.112 * (1 - t) + 0.096 * t)
        rings.append(Ring(body_point(h, x, 0.006 * math.sin(math.pi * t)), Vector((1, 0, 0)), Vector((0, 1, 0)),
                          a * S, b * S, thigh_shape(h), c * S))
    shell(builder, rings, 34, rng, open_start=False, open_end=True, amplitude=0.9)
    iron_cage(builder, rings, rng, depth=5, bars=6, stick_out=1.3)
    ballast(builder, rings, rng, 7, 5, down)
    return rings


ARM_PROFILE = [(0.058, 0.052), (0.053, 0.049), (0.043, 0.041), (0.037, 0.035), (0.04, 0.036), (0.037, 0.031),
               (0.031, 0.024), (0.028, 0.019)]


def arm_path(side):
    shoulder = Vector((side * 0.205, 0.0, 1.44))
    elbow = shoulder + Vector((side * 0.03, -0.01, -0.29))
    wrist = elbow + Vector((side * 0.01, 0.05, -0.25))
    path = [shoulder.lerp(elbow, t) for t in (0.0, 0.33, 0.66, 1.0)]
    path += [elbow.lerp(wrist, t) for t in (0.25, 0.5, 0.78, 1.0)]
    return [p * S for p in path], wrist * S


def digit(builder, rng, path, radius):
    profile = [radius * 1.04, radius, radius * 0.96, radius * 0.9, radius * 0.75, radius * 0.6]
    points = list(path) + [path[-1] + (path[-1] - path[-2]).normalized() * radius * 0.5]
    profile = profile[:len(points)] + [profile[-1]] * max(0, len(points) - len(profile))
    rings = limb_rings(points, [(r, r * 0.9) for r in profile], None)
    shell(builder, rings, 12, rng, round_end=True)


def hand(builder, wrist, forward, side_axis, palm_normal, rng, thumb_scale=1.0, curl_scale=1.0):
    forward = forward.normalized()
    side_axis = side_axis.normalized()
    palm_normal = palm_normal.normalized()
    length = 0.11 * S
    width = 0.085 * S
    depth = 0.032 * S
    rows = []
    for k in range(7):
        t = k / 6
        centre = wrist + forward * (length * t)
        half_w = width * (0.40 + 0.1 * math.sin(math.pi * t * 0.8))
        half_d = depth * (0.6 - 0.18 * t)
        rows.append(Ring(centre, side_axis, palm_normal, half_w, half_d))
    shell(builder, rows, 22, rng)
    knuckles = wrist + forward * (length * 0.97)
    finger_lengths = [0.083, 0.095, 0.09, 0.07]
    for index, finger_length in enumerate(finger_lengths):
        base = knuckles + side_axis * (width * (0.33 - index * 0.22))
        curl = (0.28 + 0.12 * index) * curl_scale
        segment = finger_length * S / 3
        direction = forward.copy()
        path = [base - forward * 0.4, base]
        point = base
        for k in range(3):
            direction = (direction * math.cos(curl) + palm_normal * math.sin(curl)).normalized()
            point = point + direction * segment
            path.append(point)
        digit(builder, rng, path, 0.0105 * S * (0.86 if index == 3 else 1.0))
    radius = 0.0145 * S * thumb_scale
    root = wrist + forward * (length * 0.28) + side_axis * (width * 0.36)
    out = (side_axis * 0.75 + forward * 0.45 - palm_normal * 0.35).normalized()
    first = root + out * 0.035 * S
    second = first + (out * 0.55 + forward * 0.8).normalized() * 0.032 * S
    tip = second + (out * 0.3 + forward * 0.9 - palm_normal * 0.2).normalized() * 0.028 * S
    digit(builder, rng, [root - out * 0.6, root, first, second, tip], radius)
    return root, second


def head_profile():
    return [(1.555, 0.052, 0.055, 0.055), (1.57, 0.055, 0.066, 0.058), (1.585, 0.058, 0.08, 0.062),
            (1.60, 0.063, 0.088, 0.068), (1.615, 0.067, 0.091, 0.075), (1.63, 0.071, 0.093, 0.083),
            (1.645, 0.073, 0.095, 0.089), (1.66, 0.075, 0.097, 0.094), (1.675, 0.076, 0.097, 0.098),
            (1.69, 0.077, 0.096, 0.101), (1.705, 0.078, 0.095, 0.103), (1.72, 0.078, 0.093, 0.104),
            (1.735, 0.077, 0.089, 0.103), (1.75, 0.074, 0.083, 0.099), (1.765, 0.068, 0.074, 0.091),
            (1.778, 0.06, 0.063, 0.079), (1.788, 0.049, 0.05, 0.064), (1.796, 0.034, 0.034, 0.045),
            (1.80, 0.016, 0.016, 0.022)]


def face_shape(h):
    def shape(angle):
        centred = math.atan2(math.sin(angle - math.pi / 2), math.cos(angle - math.pi / 2))
        front = math.cos(centred)
        value = 1.0
        if front > 0.3 and h < 1.64:
            jaw = (h - 1.555) / 0.085
            value -= 0.1 * (1 - jaw) * max(0.0, abs(math.sin(centred)) - 0.2)
        if abs(centred) < 0.32 and 1.635 < h < 1.715:
            ridge = math.exp(-(centred ** 2) / 0.006)
            tip = (1.715 - h) / 0.08
            value += 0.36 * ridge * (0.35 + 0.65 * tip) * min(1.0, (h - 1.635) / 0.012)
        if 1.69 < h < 1.71 and abs(abs(centred) - 0.5) < 0.2:
            value -= 0.1 * math.cos((abs(centred) - 0.5) / 0.2 * math.pi / 2)
        if 1.71 < h < 1.73 and abs(centred) < 0.85:
            value += 0.06 * math.cos(centred / 0.85 * math.pi / 2)
        if 1.618 < h < 1.632 and abs(centred) < 0.32:
            value -= 0.05 * math.cos(centred / 0.32 * math.pi / 2)
        if 1.6 < h < 1.618 and abs(centred) < 0.3:
            value += 0.03
        if 1.578 < h < 1.6 and abs(centred) < 0.4:
            value += 0.07 * math.cos(centred / 0.4 * math.pi / 2)
        if h > 1.735 or (front < 0.15 and h > 1.62):
            value += 0.03 * math.sin(angle * 13.0 + h * 260.0) * math.sin(h * 190.0 + angle * 3.0) + 0.02
        return value
    return shape


def head(builder, rng):
    rows = []
    for h, a, b, back in head_profile():
        rows.append(Ring(Vector((0.0, 0.0, h * S)), Vector((1, 0, 0)), Vector((0, 1, 0)), a * S, b * S, face_shape(h),
                         back * S))
    shell(builder, rows, 56, rng, open_start=True, amplitude=0.4)
    for side in (-1, 1):
        ear_rings = [Ring(Vector((side * (0.074 + d) * S, -0.012 * S, 1.665 * S)), Vector((0, side, 0)),
                          Vector((0, 0, 1)), 0.009 * S * s, 0.022 * S * s) for d, s in ((0.0, 0.8), (0.006, 1.0),
                                                                                     (0.012, 0.6))]
        shell(builder, ear_rings, 14, rng)
    first = len(builder.polygons)
    for k in range(11):
        angle = math.radians(-25 + 230 * k / 10)
        root = Vector((0.074 * S * math.cos(angle), 0.096 * S * math.sin(angle) - 0.006 * S, 1.748 * S))
        out = Vector((math.cos(angle), math.sin(angle), 0.1)).normalized()
        length = (0.1 if k % 2 == 0 else 0.07) * S
        if rng.random() < 0.3:
            length *= rng.uniform(0.35, 0.6)
        side = out.cross(UP).normalized()
        lift = side.cross(out).normalized()
        tip = root + out * length
        near = [root + side * (sx * 0.175) + lift * (sy * 0.04) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        far = [tip + side * (sx * 0.03) + lift * (sy * 0.04) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for k2 in range(4):
            j = (k2 + 1) % 4
            quad = [near[k2], near[j], far[j], far[k2]]
            middle = sum(quad, Vector()) / 4
            builder.oriented(quad, middle - (root + tip) / 2 - out * (middle - root).dot(out), BRONZE)
        builder.oriented(far, out, BRONZE)
    builder.tint(first, (0.92, 0.88, 0.8))
    circlet = []
    for k in range(40):
        angle = TAU * k / 40
        circlet.append(Vector((0.081 * S * math.cos(angle), 0.1 * S * math.sin(angle) - 0.004 * S, 1.742 * S)))
    tube(builder, circlet + [circlet[0]], [0.006 * S] * 41, (0.95, 0.9, 0.82), 6, BRONZE, cap=False)
    return rows


def foot(builder, rng, side, forward_shift):
    base = Vector((side * 0.11 * S, forward_shift * 1.2, 0.0))
    rows = []
    stations = [(-0.05, 0.026, 0.045), (-0.035, 0.031, 0.065), (-0.01, 0.034, 0.078), (0.03, 0.038, 0.065),
                (0.08, 0.044, 0.048), (0.13, 0.048, 0.035), (0.16, 0.047, 0.026)]
    for y, half_w, height in stations:
        centre = base + Vector((side * -0.004 * S, y * S, height * S * 0.5))
        rows.append(Ring(centre, Vector((1, 0, 0)), Vector((0, 0, -1)), half_w * S, height * S * 0.5))
    shell(builder, rows, 22, rng)
    for k in range(5):
        x = (-0.033 + k * 0.0165) * S * (-side)
        length = (0.04 - abs(k - 1) * 0.004) * S
        radius = (0.011 - k * 0.0011) * S
        start = base + Vector((x, 0.152 * S, radius * 0.95))
        digit(builder, rng, [start, start + Vector((0.0, length * 0.5, 0.0)),
                             start + Vector((0.0, length, -radius * 0.3))], radius)
    return base


def lower_leg(builder, rng, side, forward_shift):
    base = foot(builder, rng, side, forward_shift)
    heights = [0.045, 0.08, 0.12, 0.17, 0.22, 0.27, 0.32, 0.37, 0.42, KNEE - 0.02]
    radii = [(0.032, 0.036, 0.034), (0.031, 0.032, 0.036), (0.034, 0.033, 0.042), (0.04, 0.036, 0.05),
             (0.046, 0.038, 0.058), (0.05, 0.04, 0.062), (0.05, 0.04, 0.058), (0.047, 0.04, 0.05),
             (0.046, 0.042, 0.045), (0.05, 0.048, 0.046)]
    points = [base + Vector((0.0, 0.0, h * S)) for h in heights]
    rings = [Ring(p, Vector((1, 0, 0)), Vector((0, 1, 0)), a * S, b * S, knee_shape(h), c * S)
             for p, h, (a, b, c) in zip(points, heights, radii)]
    shell(builder, rings, 32, rng, open_start=False, open_end=True, amplitude=1.1)
    iron_cage(builder, rings, rng, depth=3, bars=6, stick_out=2.2)


def knee_shape(h):
    def shape(angle):
        front = math.sin(angle)
        value = 1.0
        if h > 0.36 and front > 0.3:
            value += 0.16 * (front - 0.3) / 0.7 * min(1.0, (h - 0.36) / 0.08)
        if 0.12 < h < 0.36 and front > 0.85:
            value += 0.05 * (front - 0.85) / 0.15
        return value
    return shape


def pedestal(builder):
    first = len(builder.polygons)
    for index, (size, z0, z1) in enumerate(PEDESTAL):
        half = size / 2
        builder.box((-half - 0.3, -half - 0.3, z0 - (1.2 if index == 0 else 0.0)), (half + 0.3, half + 0.3, z0 + 0.45),
                    STONE, bottom=False)
        builder.box((-half, -half, z0 + 0.45), (half, half, z1 - 0.6), STONE, bottom=False, top=False)
        for grow, z_low, z_high in ((0.12, z1 - 0.6, z1 - 0.45), (0.28, z1 - 0.45, z1 - 0.25), (0.42, z1 - 0.25, z1)):
            builder.box((-half - grow, -half - grow, z_low), (half + grow, half + grow, z_high), STONE, bottom=False)
    builder.tint(first, PEDESTAL_TINT)
    half = PEDESTAL[1][0] / 2 + 0.005
    rng = random.Random(29)
    start = len(builder.polygons)
    for line in range(9):
        z = 6.6 - line * 0.26
        width = 4.4 - (0.6 if line % 3 == 2 else 0.0) - (2.2 if line == 8 else 0.0)
        y = -width
        while y < width:
            stroke = rng.choice((0.035, 0.035, 0.05, 0.12))
            tall = 0.13 if stroke < 0.1 else 0.035
            lift = 0.0 if stroke < 0.1 else rng.choice((0.0, 0.05, 0.1))
            builder.oriented([(half, y, z + lift), (half, y + stroke, z + lift), (half, y + stroke, z + lift + tall),
                              (half, y, z + lift + tall)], (1, 0, 0), "matte")
            y += stroke + rng.choice((0.04, 0.06, 0.09, 0.09, 0.22))
    builder.tint(start, INSCRIPTION)


def standing_part(seed=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    pedestal(builder)
    legs = MeshBuilder()
    lower_leg(legs, rng, -1, 0.0)
    lower_leg(legs, rng, 1, 1.0)
    builder.merge(legs, Matrix.Translation((0.0, 0.0, TOP - 0.05)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    return builder


def fallen_body(down, seed=5):
    rng = random.Random(seed)
    body = MeshBuilder()
    torso(body, rng, down)
    thigh(body, rng, -1, down)
    thigh(body, rng, 1, down)
    path, wrist = arm_path(1)
    left = limb_rings(path, [(a * S, b * S) for a, b in ARM_PROFILE], Vector((0.0, 1.0, 0.0)))
    shell(body, left, 28, rng)
    hand(body, wrist, Vector((0.05, 0.2, -1.0)), Vector((0.0, 1.0, 0.0)), Vector((-1.0, 0.0, 0.0)), rng)
    path, _ = arm_path(-1)
    stump = limb_rings(path[:3], [(a * S, b * S) for a, b in ARM_PROFILE[:3]], Vector((0.0, 1.0, 0.0)))
    shell(body, stump, 28, rng, open_end=True, amplitude=0.6)
    iron_cage(body, stump, rng, depth=2, bars=4, stick_out=1.0)
    return body


def loose_arm(down, seed=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    path, wrist = arm_path(-1)
    rings = limb_rings(path[2:], [(a * S, b * S) for a, b in ARM_PROFILE[2:]], Vector((0.0, 1.0, 0.0)))
    rings.reverse()
    shell(builder, rings, 28, rng, open_start=False, open_end=True, amplitude=0.6)
    iron_cage(builder, rings, rng, depth=2, bars=4, stick_out=0.9)
    ballast(builder, rings, rng, 4, 3, down)
    thumb = hand(builder, wrist, Vector((0.0, 0.2, -1.0)), Vector((0.0, 1.0, 0.0)), Vector((1.0, 0.0, 0.0)), rng,
                 1.15, 0.2)
    return builder, thumb + (wrist,)


def fallen_head(down, seed=11):
    rng = random.Random(seed)
    builder = MeshBuilder()
    rings = head(builder, rng)
    neck = [Ring(r.centre, r.u, r.v, r.a, r.b, r.shape, r.back) for r in reversed(rings[:5])]
    ballast(builder, neck, rng, 3, 4, down)
    return builder


LYING = Matrix(((0.0, 0.0, 1.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def lay(builder, matrix, sink=0.35):
    low = min((matrix @ Vector(p)).z for p in builder.positions)
    final = Matrix.Translation((0.0, 0.0, -low - sink)) @ matrix
    result = MeshBuilder()
    result.merge(builder, final)
    return result, final


def lying_frame(x, y, h_origin, roll=0.0, yaw=0.0):
    return (Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(roll, 4, "X") @ LYING
            @ Matrix.Translation((0.0, 0.0, -h_origin * S)))


def plate(builder, frame, size, rng):
    sink = rng.choice((0.0, 0.0, 0.05))
    top = []
    for i in range(4):
        row = []
        for j in range(3):
            x = (i / 3 - 0.5) * size * 1.6
            y = (j / 2 - 0.5) * size
            z = 0.12 - sink + 0.3 * size * (1 - (2 * x / (size * 1.6)) ** 2) + rng.uniform(-0.03, 0.03)
            row.append(Vector((x, y, z)))
        top.append(row)
    bottom = [[p - Vector((0.0, 0.0, 0.12)) for p in row] for row in top]
    first = len(builder.polygons)
    builder.surface([[frame @ p for p in row] for row in top], BRONZE, smooth=True,
                    facing=tuple(frame.to_3x3() @ Vector((0.0, 0.0, 1.0))))
    builder.surface([[frame @ p for p in row] for row in bottom], BRONZE, smooth=True,
                    facing=tuple(frame.to_3x3() @ Vector((0.0, 0.0, -1.0))))
    centre = frame @ Vector((0.0, 0.0, 0.1))
    for upper, lower in ((top[0], bottom[0]), (top[-1], bottom[-1]), ([r[0] for r in top], [r[0] for r in bottom]),
                         ([r[-1] for r in top], [r[-1] for r in bottom])):
        for a, b, c, d in zip(upper[:-1], upper[1:], lower[1:], lower[:-1]):
            quad = [frame @ a, frame @ b, frame @ c, frame @ d]
            builder.oriented(quad, sum(quad, Vector()) / 4 - centre, BRONZE)
    builder.tint(first, (1.0, 1.0, 1.0))


def fragments(seed=13):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(26):
        size = rng.uniform(0.4, 1.3)
        centre = Vector((rng.uniform(-12.0, 42.0), rng.uniform(-15.0, 15.0), 0.0))
        if abs(centre.x) < 10.0 and abs(centre.y) < 10.0:
            continue
        frame = (Matrix.Translation(centre) @ Matrix.Rotation(rng.uniform(0, TAU), 4, "Z")
                 @ Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "X"))
        plate(builder, frame, size, rng)
    for k in range(22):
        size = rng.uniform(0.45, 1.1)
        centre = (rng.uniform(-11.0, 40.0), rng.uniform(-14.0, 14.0), size * 0.25)
        if abs(centre[0]) < 9.5 and abs(centre[1]) < 9.5:
            continue
        tone = rng.uniform(0.68, 0.86)
        boulder(builder, centre, (size * 1.25, size, size * 0.7), (tone, tone * 0.96, tone * 0.9), rng, STONE, 6, 3)
    return builder


ARM_ROLL = -90.0
ARM_SINK = 0.05
HEAD_ROLL = 60.0


def colossus():
    standing = standing_part()
    knee_x = PEDESTAL[0][0] / 2 + 1.4
    body_matrix = lying_frame(knee_x, 0.0, KNEE, math.radians(20.0))
    body, body_frame = lay(fallen_body(down_of(body_matrix)), body_matrix)
    arm_matrix = lying_frame(knee_x + 2.0, -12.5, 1.2, math.radians(ARM_ROLL), math.radians(-10.0))
    arm, (thumb_root, thumb_tip, wrist) = loose_arm(down_of(arm_matrix))
    arm_laid, arm_frame = lay(arm, arm_matrix, ARM_SINK)
    head_matrix = lying_frame(knee_x + 1.3 * S + 4.5, -3.0, 1.68, math.radians(HEAD_ROLL), math.radians(-14.0))
    head_laid, head_frame = lay(fallen_head(down_of(head_matrix)), head_matrix, 0.6)
    parts = {"standing": standing, "body": body, "arm": arm_laid, "head": head_laid, "debris": fragments()}
    root = arm_frame @ thumb_root
    tip = arm_frame @ thumb_tip
    marks = {"thumb": (root + tip) / 2, "thumb_root": root, "thumb_tip": tip, "wrist": arm_frame @ wrist,
             "face": head_frame @ Vector((0.0, 0.11 * S, 1.66 * S)),
             "face_out": head_frame @ Vector((0.0, 0.6 * S, 1.66 * S)),
             "knee": Vector((knee_x, 0.0, 2.0)), "neck": body_frame @ Vector((0.0, 0.0, 1.55 * S)),
             "feet": Vector((0.0, 0.0, TOP + 2.0))}
    return parts, marks
