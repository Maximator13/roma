import math
import random

from mathutils import Matrix, Vector

from .geometry import MeshBuilder
from .nimes_figures import POSES, Look, coarse, ellipsoid, person, tube
from .orders import column

STONE = "limestone"
MARBLE = "marble"
GILT = "bronze_gilt"
GRANITE = "granite"
VOID = "shadow_void"
PAVING = "paving"
TAU = 2 * math.pi
GROUND = 3.0
PLINTH = 4.0
SQUARE_TOP = 52.0
SQUARE_BASE_HALF = 15.2
SQUARE_TOP_HALF = 13.4
OCTAGON_TOP = 81.0
OCTAGON_BASE_HALF = 8.2
OCTAGON_TOP_HALF = 7.5
CYLINDER_TOP = 88.3
CYLINDER_RADIUS = 4.35
FOYER_TOP = CYLINDER_TOP + 6.6
CAP_RISE = 1.0
PEDESTAL = 1.0
STATUE_BASE = FOYER_TOP + 0.12 + CAP_RISE + PEDESTAL
BEACON_HEIGHT = CYLINDER_TOP + 1.7
STATUE_SCALE = 3.9
WHITE = (1.0, 0.97, 0.90)
TIER = 48.0 / 52.0
WARM = (0.98, 0.93, 0.84)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def ring(sides, half, z, rotation=0.0):
    if sides == 4:
        return [(half * sx, half * sy, z) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    radius = half / math.cos(math.pi / sides)
    return [(radius * math.cos(rotation + math.pi / sides + TAU * k / sides),
             radius * math.sin(rotation + math.pi / sides + TAU * k / sides), z) for k in range(sides)]


def frustum(builder, sides, half0, half1, z0, z1, material, top=False, bottom=False):
    lower = builder.points(ring(sides, half0, z0))
    upper = builder.points(ring(sides, half1, z1))
    for k in range(sides):
        j = (k + 1) % sides
        builder.face([lower[k], lower[j], upper[j], upper[k]], material)
    if top:
        builder.face(upper, material)
    if bottom:
        builder.face(list(reversed(lower)), material)


def band(builder, sides, half, z0, z1, material, projection):
    frustum(builder, sides, half + projection, half + projection, z0, z1, material, top=True, bottom=True)


def cornice(builder, sides, half, z, material, scale=1.0):
    rows = [(0.0, 0.0), (0.35, 0.25), (0.45, 0.55), (0.9, 0.85), (1.15, 1.25), (1.2, 1.55), (0.0, 1.55)]
    previous = None
    for offset, height in rows:
        current = builder.points(ring(sides, half + offset * scale, z + height * scale))
        if previous is not None:
            for k in range(sides):
                j = (k + 1) % sides
                builder.face([previous[k], previous[j], current[j], current[k]], material)
        previous = current
    builder.face(previous, material)


def parapet(builder, sides, half, z, height, thickness, material):
    outer_lower = builder.points(ring(sides, half, z))
    outer_upper = builder.points(ring(sides, half, z + height))
    inner_lower = builder.points(ring(sides, half - thickness, z))
    inner_upper = builder.points(ring(sides, half - thickness, z + height))
    for k in range(sides):
        j = (k + 1) % sides
        builder.face([outer_lower[k], outer_lower[j], outer_upper[j], outer_upper[k]], material)
        builder.face([inner_lower[j], inner_lower[k], inner_upper[k], inner_upper[j]], material)
        builder.face([outer_upper[k], outer_upper[j], inner_upper[j], inner_upper[k]], material)


def face_point(normal, side, half0, half1, z0, z1, u, z, push=0.04):
    half = half0 + (half1 - half0) * (z - z0) / (z1 - z0)
    return normal * (half + push) + side * u + Vector((0.0, 0.0, z))


def window(builder, normal, side, half0, half1, z0, z1, u, z, width, height, arched=False):
    corners = [face_point(normal, side, half0, half1, z0, z1, u + du, z + dz)
               for du, dz in ((-width / 2, 0.0), (width / 2, 0.0), (width / 2, height), (-width / 2, height))]
    builder.oriented(corners, normal, VOID)
    frame = [face_point(normal, side, half0, half1, z0, z1, u + du, z + dz, 0.12)
             for du, dz in ((-width / 2 - 0.25, -0.35), (width / 2 + 0.25, -0.35), (width / 2 + 0.25, -0.05),
                            (-width / 2 - 0.25, -0.05))]
    painted(builder, WARM, lambda: builder.oriented(frame, normal, STONE))
    if arched:
        top = [face_point(normal, side, half0, half1, z0, z1, u + width / 2 * math.cos(math.pi * k / 6),
                          z + height + width / 2 * math.sin(math.pi * k / 6)) for k in range(7)]
        builder.oriented(top, normal, VOID)


def square_tier(builder):
    z0, z1 = PLINTH, SQUARE_TOP
    painted(builder, WHITE, lambda: frustum(builder, 4, SQUARE_BASE_HALF, SQUARE_TOP_HALF, z0, z1, STONE))
    for z in (PLINTH + (value - PLINTH) * TIER for value in (17.0, 30.0, 43.0)):
        half = SQUARE_BASE_HALF + (SQUARE_TOP_HALF - SQUARE_BASE_HALF) * (z - z0) / (z1 - z0)
        painted(builder, WARM, lambda half=half, z=z: band(builder, 4, half, z, z + 0.55, STONE, 0.28))
    painted(builder, WARM, lambda: band(builder, 4, SQUARE_BASE_HALF, z0, z0 + 1.2, STONE, 0.45))
    normals = [Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((-1, 0, 0))]
    for normal in normals:
        side = Vector((-normal.y, normal.x, 0.0))
        for level, z in enumerate(PLINTH + (value - PLINTH) * TIER for value in (8.5, 13.0, 21.0, 25.5, 34.0, 38.5, 47.0,
                                                                                51.0)):
            for u in (-8.5, 0.0, 8.5):
                if normal.y < 0 and u == 0.0 and z < 18.0:
                    continue
                window(builder, normal, side, SQUARE_BASE_HALF, SQUARE_TOP_HALF, z0, z1, u, z, 0.9, 1.7,
                       arched=level % 2 == 0)
    door_normal = Vector((0, -1, 0))
    door_side = Vector((1, 0, 0))
    door = [face_point(door_normal, door_side, SQUARE_BASE_HALF, SQUARE_TOP_HALF, z0, z1, u, z, 0.05)
            for u, z in ((-1.6, 9.6), (1.6, 9.6), (1.6, 14.4), (-1.6, 14.4))]
    builder.oriented(door, door_normal, VOID)
    surround = [face_point(door_normal, door_side, SQUARE_BASE_HALF, SQUARE_TOP_HALF, z0, z1, u, z, 0.2)
                for u, z in ((-2.4, 9.4), (2.4, 9.4), (2.4, 15.4), (-2.4, 15.4))]
    painted(builder, (0.78, 0.52, 0.48), lambda: builder.oriented(surround, door_normal, GRANITE))
    painted(builder, WARM, lambda: cornice(builder, 4, SQUARE_TOP_HALF, SQUARE_TOP, STONE, 1.1))
    painted(builder, WHITE, lambda: frustum(builder, 4, SQUARE_TOP_HALF + 1.32, SQUARE_TOP_HALF + 1.32, SQUARE_TOP + 1.7,
                                            SQUARE_TOP + 2.0, STONE, top=True))
    painted(builder, WARM, lambda: parapet(builder, 4, SQUARE_TOP_HALF + 1.3, SQUARE_TOP + 2.0, 1.15, 0.5, STONE))


def octagon_tier(builder):
    z0, z1 = SQUARE_TOP + 2.0, OCTAGON_TOP
    painted(builder, WHITE, lambda: frustum(builder, 8, OCTAGON_BASE_HALF, OCTAGON_TOP_HALF, z0, z1, STONE))
    painted(builder, WARM, lambda: band(builder, 8, OCTAGON_BASE_HALF, z0, z0 + 0.9, STONE, 0.35))
    mid = (z0 + z1) / 2
    half_mid = (OCTAGON_BASE_HALF + OCTAGON_TOP_HALF) / 2
    painted(builder, WARM, lambda: band(builder, 8, half_mid, mid, mid + 0.45, STONE, 0.25))
    for k in range(8):
        angle = TAU * k / 8
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        for z in (z0 + 4.0, z0 + 15.0, z0 + 22.0):
            window(builder, normal, side, OCTAGON_BASE_HALF, OCTAGON_TOP_HALF, z0, z1, 0.0, z, 0.8, 1.8, True)
    painted(builder, WARM, lambda: cornice(builder, 8, OCTAGON_TOP_HALF, OCTAGON_TOP, STONE, 0.75))
    painted(builder, WARM, lambda: parapet(builder, 8, OCTAGON_TOP_HALF + 0.85, OCTAGON_TOP + 1.16, 0.95, 0.4, STONE))
    painted(builder, WHITE, lambda: frustum(builder, 8, OCTAGON_TOP_HALF + 0.9, OCTAGON_TOP_HALF + 0.9, OCTAGON_TOP + 1.0,
                                            OCTAGON_TOP + 1.16, STONE, top=True))


def cylinder_tier(builder):
    z0 = OCTAGON_TOP + 1.16
    profile = [(CYLINDER_RADIUS + 0.3, z0), (CYLINDER_RADIUS + 0.3, z0 + 0.6), (CYLINDER_RADIUS, z0 + 0.7),
               (CYLINDER_RADIUS, CYLINDER_TOP - 0.6), (CYLINDER_RADIUS + 0.5, CYLINDER_TOP - 0.3),
               (CYLINDER_RADIUS + 0.7, CYLINDER_TOP), (0.0, CYLINDER_TOP)]
    painted(builder, WHITE, lambda: builder.lathe(profile, 24, STONE, smooth=True))
    for k in range(6):
        angle = TAU * (k + 0.5) / 6
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-normal.y, normal.x, 0.0))
        corners = [normal * (CYLINDER_RADIUS + 0.03) + side * du + Vector((0, 0, z0 + 2.0 + dz))
                   for du, dz in ((-0.4, 0.0), (0.4, 0.0), (0.4, 1.6), (-0.4, 1.6))]
        builder.oriented(corners, normal, VOID)


def foyer(builder):
    floor = CYLINDER_TOP
    count = 8
    radius = 3.35
    height = FOYER_TOP - floor - 0.7
    shaft = column("ionic", 0.7, height, "low", MARBLE)
    for k in range(count):
        angle = TAU * (k + 0.5) / count
        painted(builder, WHITE, lambda angle=angle: builder.merge(
            shaft, Matrix.Translation((radius * math.cos(angle), radius * math.sin(angle), floor))))
    painted(builder, (0.24, 0.20, 0.17), lambda: builder.lathe(
        [(0.0, floor + 0.05), (1.5, floor + 0.05), (1.7, floor + 0.6), (1.55, floor + 1.1), (1.2, floor + 1.15),
         (1.1, floor + 0.75), (0.0, floor + 0.7)], 14, GILT, smooth=True))
    under = FOYER_TOP - 0.7
    top = FOYER_TOP + 0.12
    painted(builder, WARM, lambda: builder.lathe([(0.0, under), (radius + 0.45, under), (radius + 0.45, FOYER_TOP - 0.25),
                                                  (radius + 0.75, FOYER_TOP), (radius + 0.75, top), (0.0, top)], 24,
                                                 MARBLE, smooth=False))
    eave = radius + 0.6
    apex = 1.1
    rise = CAP_RISE
    painted(builder, WHITE, lambda: builder.lathe([(eave, top), (eave, top + 0.15), (apex, top + rise), (0.0, top + rise)],
                                                  24, STONE, smooth=False))
    painted(builder, (1.0, 0.86, 0.6), lambda: builder.lathe([(eave + 0.12, top - 0.02), (eave + 0.12, top + 0.32),
                                                              (eave - 0.25, top + 0.32), (eave - 0.25, top + 0.1)], 24,
                                                             GILT, smooth=True, caps=False))
    painted(builder, WARM, lambda: builder.box((-0.95, -0.95, top + rise - 0.2), (0.95, 0.95, STATUE_BASE - 0.15),
                                               MARBLE, bottom=False))
    painted(builder, WHITE, lambda: builder.box((-1.1, -1.1, STATUE_BASE - 0.15), (1.1, 1.1, STATUE_BASE), MARBLE,
                                                bottom=False))


def trimmed(source, z_min):
    result = MeshBuilder()
    mapping = {}
    for indices, material_index, smooth, uvs, colour in zip(source.polygons, source.polygon_materials,
                                                             source.polygon_smooth, source.polygon_uvs,
                                                             source.polygon_colors):
        if max(source.positions[i][2] for i in indices) < z_min:
            continue
        points = []
        for i in indices:
            if i not in mapping:
                mapping[i] = result.point(source.positions[i])
            points.append(mapping[i])
        result.face(points, source.materials[material_index], smooth, uvs, colour, raw=True)
    return result


def slab(builder, points, normal, thickness, material):
    normal = Vector(normal).normalized()
    front = [Vector(p) + normal * thickness / 2 for p in points]
    back = [Vector(p) - normal * thickness / 2 for p in points]
    builder.oriented(front, normal, material, True)
    builder.oriented(back, -normal, material, True)
    centre = sum(front + back, Vector()) / (2 * len(points))
    for k in range(len(points)):
        j = (k + 1) % len(points)
        quad = [front[k], front[j], back[j], back[k]]
        middle = sum(quad, Vector()) / 4
        builder.oriented(quad, middle - centre, material, True)


def triton(seed=0):
    POSES["alex_conch"] = [((0.24, 0.16, 1.3), (0.07, 0.24, 1.5)), ((-0.24, 0.16, 1.3), (-0.06, 0.26, 1.48))]
    gold = (1.0, 1.0, 1.0)
    rng = random.Random(seed)
    body = trimmed(coarse(lambda: person(Look("white", hem=0.96, skin=0, hair=seed % 3, arms="alex_conch", mono=gold,
                                              seed=40 + seed)), 1.6), 0.92)
    builder = MeshBuilder()
    builder.merge(body)
    ellipsoid(builder, (0.0, 0.01, 1.3), (0.2, 0.15, 0.13), gold, 14, 6, GILT)
    path = [Vector((0.0, 0.0, 1.0)), Vector((0.0, -0.02, 0.78)), Vector((0.0, 0.06, 0.52)), Vector((0.0, 0.24, 0.3)),
            Vector((0.0, 0.48, 0.24)), Vector((0.0, 0.66, 0.36)), Vector((0.0, 0.72, 0.58)), Vector((0.0, 0.66, 0.76))]
    radii = [0.17, 0.165, 0.15, 0.13, 0.105, 0.08, 0.055, 0.03]
    tube(builder, path, radii, gold, 14, GILT, cap=False)
    for k in range(5):
        ring_z = path[k + 1]
        ellipsoid(builder, ring_z, (radii[k + 1] * 1.08, radii[k + 1] * 1.08, 0.025), gold, 12, 2, GILT)
    tip = path[-1]
    for side in (-1, 1):
        fluke = [tip, tip + Vector((side * 0.34, 0.06, 0.2)), tip + Vector((side * 0.3, -0.04, 0.32)),
                 tip + Vector((side * 0.1, -0.06, 0.12))]
        slab(builder, fluke, (0, -1, 0.2), 0.03, GILT)
    for side in (-1, 1):
        fin = [Vector((side * 0.16, 0.0, 0.95)), Vector((side * 0.34, -0.08, 0.86)), Vector((side * 0.2, 0.02, 0.8))]
        slab(builder, fin, (side, 0, 0), 0.03, GILT)
    conch = (Matrix.Translation((0.0, 0.17, 1.575)) @ Matrix.Rotation(math.radians(-35), 4, "X")
             @ Matrix.Rotation(math.radians(rng.uniform(-10, 10)), 4, "Y") @ Matrix.Diagonal((0.6, 0.6, 0.7, 1.0)))
    profile = [(0.0, 0.0), (0.022, 0.015), (0.04, 0.09), (0.068, 0.2), (0.095, 0.3), (0.11, 0.35), (0.075, 0.39),
               (0.0, 0.4)]
    painted(builder, gold, lambda: builder.lathe(profile, 12, GILT, smooth=True, matrix=conch))
    for k in range(3):
        ring = conch @ Matrix.Translation((0.0, 0.0, 0.11 + 0.08 * k))
        painted(builder, gold, lambda ring=ring, k=k: builder.lathe([(0.035 + 0.024 * k, -0.012),
                                                                     (0.046 + 0.024 * k, 0.0),
                                                                     (0.035 + 0.024 * k, 0.012)], 12, GILT,
                                                                    smooth=True, matrix=ring, caps=False))
    builder.materials = [GILT for _ in builder.materials]
    return builder


def statue():
    look = Look("white", hem=0.05, skin=0, hair=0, palla="white", arms="staff", mono=(1.0, 1.0, 1.0), seed=31)
    body = coarse(lambda: person(look), 1.6)
    body.materials = [GILT for _ in body.materials]
    merged = MeshBuilder()
    merged.merge(body, Matrix.Scale(STATUE_SCALE, 4))
    hand = Vector((0.25, 0.2, 1.0)) * STATUE_SCALE
    reach = 1.15 * 1.85 * STATUE_SCALE
    tube(merged, [(hand.x, hand.y, 0.1), (hand.x, hand.y, hand.z), (hand.x, hand.y, reach)], [0.08, 0.075, 0.06],
         (1.0, 1.0, 1.0), 8, GILT)
    ellipsoid(merged, (hand.x, hand.y, reach), (0.16, 0.16, 0.24), (1.0, 1.0, 1.0), 8, 4, GILT)
    return merged


def tower():
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-18.0, -18.0, -0.2), (18.0, 18.0, 1.6), STONE, bottom=False))
    painted(builder, WHITE, lambda: builder.box((-16.6, -16.6, 1.6), (16.6, 16.6, PLINTH), STONE, bottom=False))
    painted(builder, WARM, lambda: band(builder, 4, 16.6, PLINTH - 0.5, PLINTH, STONE, 0.3))
    square_tier(builder)
    octagon_tier(builder)
    cylinder_tier(builder)
    foyer(builder)
    return builder


def tritons_and_statue():
    builder = MeshBuilder()
    corner = SQUARE_TOP_HALF + 1.3 - 0.25
    seat = SQUARE_TOP + 2.0 + 1.15
    for k in range(4):
        angle = math.radians(45 + 90 * k)
        cx = corner * math.copysign(1, math.cos(angle))
        cy = corner * math.copysign(1, math.sin(angle))
        painted(builder, WARM, lambda cx=cx, cy=cy: builder.box((cx - 0.9, cy - 0.9, seat - 0.05),
                                                                (cx + 0.9, cy + 0.9, seat + 0.55), STONE, bottom=False))
        frame = (Matrix.Translation((cx, cy, seat + 0.55)) @ Matrix.Rotation(angle - math.pi / 2, 4, "Z")
                 @ Matrix.Scale(2.5, 4))
        builder.merge(triton(k), frame)
    builder.merge(statue(), Matrix.Translation((0.0, 0.0, STATUE_BASE)) @ Matrix.Rotation(math.radians(-60), 4, "Z"))
    return builder


def arcade(builder, start, end, width, z_start, z_end, spans, material, colour, foot=-0.5, parapet_height=1.0):
    direction = (end - start).normalized()
    length = (end - start).length
    side = Vector((-direction.y, direction.x, 0.0))
    pier = 1.8
    span = (length - pier) / spans

    def at(s, offset, z):
        p = start + direction * s + side * offset
        return Vector((p.x, p.y, z))

    def deck(s):
        return z_start + (z_end - z_start) * s / length

    first = len(builder.polygons)
    for k in range(spans + 1):
        s0 = k * span
        s1 = s0 + pier
        corners = [at(s0, -width / 2, foot), at(s1, -width / 2, foot), at(s1, width / 2, foot), at(s0, width / 2, foot),
                   at(s0, -width / 2, deck(s0)), at(s1, -width / 2, deck(s1)), at(s1, width / 2, deck(s1)),
                   at(s0, width / 2, deck(s0))]
        indices = builder.points(corners)
        for quad in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            builder.face([indices[q] for q in quad], material)
    for k in range(spans):
        a = k * span + pier
        b = (k + 1) * span
        half = (b - a) / 2
        middle = a + half
        spring = max(min(deck(a), deck(b)) - 0.9 - half, foot + 0.5)
        arc = [(middle - half * math.cos(math.pi * i / 10), spring + half * math.sin(math.pi * i / 10))
               for i in range(11)]
        for offset, normal in ((-width / 2, -side), (width / 2, side)):
            for (sa, za), (sb, zb) in zip(arc[:-1], arc[1:]):
                builder.oriented([at(sa, offset, za), at(sb, offset, zb), at(sb, offset, deck(sb)),
                                  at(sa, offset, deck(sa))], normal, material)
        for (sa, za), (sb, zb) in zip(arc[:-1], arc[1:]):
            builder.oriented([at(sa, -width / 2, za), at(sb, -width / 2, zb), at(sb, width / 2, zb),
                              at(sa, width / 2, za)], Vector((0, 0, -1)), material)
    builder.tint(first, colour)
    first = len(builder.polygons)
    top_quad = [at(0.0, -width / 2, deck(0.0)), at(length, -width / 2, deck(length)), at(length, width / 2, deck(length)),
                at(0.0, width / 2, deck(0.0))]
    builder.oriented(top_quad, Vector((0, 0, 1)), PAVING)
    if parapet_height > 0:
        for offset in (-width / 2 + 0.25, width / 2 - 0.25):
            builder.sweep([at(0.0, offset, deck(0.0)), at(length, offset, deck(length))],
                          [(-0.25, 0.0), (0.25, 0.0), (0.25, parapet_height), (-0.25, parapet_height)], material,
                          caps=True)
    builder.tint(first, colour)


def ramp():
    builder = MeshBuilder()
    start = Vector((0.0, -50.0, 0.0))
    end = Vector((0.0, -SQUARE_BASE_HALF - 0.45, 0.0))
    arcade(builder, start, end, 4.6, 0.3, 9.6, 6, STONE, WARM, foot=-0.2)
    return builder


def rotation_of(direction):
    return Matrix.Rotation(math.atan2(direction.y, direction.x), 4, "Z")


def enclosure(half=58.0, height=9.0):
    builder = MeshBuilder()
    corners = [Vector((-half, -half, 0.0)), Vector((half, -half, 0.0)), Vector((half, half, 0.0)),
               Vector((-half, half, 0.0))]
    thick = 3.2
    first = len(builder.polygons)
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        direction = (b - a).normalized()
        frame = Matrix.Translation((a.x, a.y, 0.0)) @ rotation_of(direction)
        length = (b - a).length
        runs = [(0.0, length)]
        if k == 0:
            gate = length / 2 - 2.2
            left, right = gate - 2.4, gate + 6.8
            runs = [(0.0, left), (right, length)]
            builder.box((0.0, -thick / 2, -6.0), (left, thick / 2, height), STONE, matrix=frame, bottom=False)
            builder.box((right, -thick / 2, -6.0), (length, thick / 2, height), STONE, matrix=frame, bottom=False)
            for x in (left - 4.0, right):
                builder.box((x, -thick, -6.0), (x + 4.0, thick, height + 2.5), STONE, matrix=frame, bottom=False)
                builder.box((x - 0.3, -thick - 0.3, height + 2.5), (x + 4.3, thick + 0.3, height + 3.1), STONE,
                            matrix=frame)
            builder.box((left, -thick / 2, 6.0), (right, thick / 2, height + 1.0), STONE, matrix=frame)
            for hinge, sign in ((left, 1.0), (right, -1.0)):
                leaf = (frame @ Matrix.Translation((hinge, thick / 2 - 0.1, 0.0))
                        @ Matrix.Rotation(sign * math.radians(80.0), 4, "Z"))
                painted(builder, (0.42, 0.26, 0.14), lambda leaf=leaf, sign=sign: builder.box(
                    (min(0.0, sign * 4.5), 0.0, 0.0), (max(0.0, sign * 4.5), 0.2, 5.8), "matte", matrix=leaf,
                    bottom=False))
            painted(builder, (0.98, 0.92, 0.8), lambda: builder.box((left - 0.8, -thick / 2 - 0.3, 6.0),
                                                                     (right + 0.8, -thick / 2 + 0.1, 6.8), STONE,
                                                                     matrix=frame))
            painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((left - 0.6, -thick / 2 - 1.2, -0.6),
                                                                      (right + 0.6, thick / 2 + 0.6, 0.0), PAVING,
                                                                      matrix=frame, bottom=False))
        else:
            builder.box((0.0, -thick / 2, -6.0), (length, thick / 2, height), STONE, matrix=frame, bottom=False)
        builder.box((0.0, -thick / 2 - 0.3, height), (length, thick / 2 + 0.3, height + 0.6), STONE, matrix=frame)
        builder.box((0.0, -thick / 2 - 0.25, height - 1.4), (length, thick / 2 + 0.25, height - 0.9), STONE,
                    matrix=frame)
        for x0, x1 in runs:
            builder.box((x0, -thick / 2 - 0.4, -6.0), (x1, thick / 2 + 0.4, 0.6), STONE, matrix=frame, bottom=False)
    for corner in corners:
        builder.box((corner.x - 3.5, corner.y - 3.5, -6.0), (corner.x + 3.5, corner.y + 3.5, height + 3.0), STONE,
                    bottom=False)
        builder.box((corner.x - 3.85, corner.y - 3.85, height + 3.0), (corner.x + 3.85, corner.y + 3.85, height + 3.6),
                    STONE)
        builder.box((corner.x - 3.6, corner.y - 3.6, height + 0.8), (corner.x + 3.6, corner.y + 3.6, height + 1.2),
                    STONE, bottom=False, top=False)
    builder.tint(first, WARM)
    first = len(builder.polygons)
    builder.box((-half + thick / 2, -half + thick / 2, -0.4), (half - thick / 2, half - thick / 2, 0.0), PAVING,
                bottom=False)
    builder.tint(first, (0.98, 0.94, 0.86))
    for x0, y0, x1, y1 in ((-half + 1.6, half - 12.0, -half + 30.0, half - 1.6), (half - 26.0, half - 12.0,
                                                                                   half - 1.6, half - 1.6),
                           (half - 12.0, -half + 12.0, half - 1.6, -half + 40.0)):
        first = len(builder.polygons)
        builder.box((x0, y0, 0.0), (x1, y1, 5.5), "plaster", bottom=False)
        builder.tint(first, (0.98, 0.9, 0.76))
        builder.box((x0 - 0.3, y0 - 0.3, 5.5), (x1 + 0.3, y1 + 0.3, 5.9), "plaster", bottom=False)
    return builder


def platform(half=62.0):
    builder = MeshBuilder()
    outline = []
    for k in range(16):
        angle = TAU * k / 16
        r = half * 1.06 / max(abs(math.cos(angle)), abs(math.sin(angle))) ** 0.25
        outline.append((r * math.cos(angle), r * math.sin(angle)))
    first = len(builder.polygons)
    builder.prism(outline, -7.0, -0.3, STONE, top=True, bottom=False)
    builder.tint(first, (0.82, 0.78, 0.70))
    return builder


def beacon_position():
    return Vector((0.0, 0.0, BEACON_HEIGHT))


def total_height():
    return GROUND + STATUE_BASE + STATUE_SCALE * 1.85
