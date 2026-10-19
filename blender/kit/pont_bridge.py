import math

import numpy as np
from mathutils import Matrix, Vector

from .geometry import MeshBuilder, newell_normal
from .pont_materials import COURSE, STONE_TILE

STONE = "molasse"
FOOT = 0.2957
TIER_HEIGHTS = (21.87, 19.50, 7.40)
TIER_WIDTHS = (6.36, 4.56, 3.06)
TIER_RINGS = (4, 3, 1)
TIER1_SPANS = (15.50, 24.52, 21.50, 19.20, 19.20, 15.75)
LARGE_ARCH = 1
PIER = 4.45
END = 2.2
TIER2_LENGTH = 242.55
TIER2_EXTRA = (3, 2)
TIER3_ARCHES = 47
TIER3_LENGTH = 360.0
TIER3_SPAN = 16 * FOOT
TIER3_END = 1.5
ABUTMENT_LENGTH = 130.0
SPECUS_WIDTH = 1.20
SPECUS_HEIGHT = 1.84
RAISED_COURSE = 0.46
SLAB_LENGTH = 3.61
SLAB_THICKNESS = 0.34
SLAB_WIDTH = 0.74
CUTWATER_DEPTH = 3.4
CUTWATER_TOP = 5.6
CUTWATER_CAP = 1.7
RING_DEPTH = (1.55, 1.3, 0.55)
CROWN_COVER = (1.6, 1.3, 0.0)


class Arch:
    def __init__(self, centre, span, springing, ring, base_left, base_right, pier_left, pier_right):
        self.centre = centre
        self.span = span
        self.radius = span / 2
        self.springing = springing
        self.ring = ring
        self.base_left = base_left
        self.base_right = base_right
        self.pier_left = pier_left
        self.pier_right = pier_right


class Layout:
    def __init__(self, base):
        self.base = base
        self.tops = [base + sum(TIER_HEIGHTS[:k + 1]) for k in range(3)]
        spans1 = list(TIER1_SPANS)
        before = END + sum(spans1[:LARGE_ARCH]) + PIER * LARGE_ARCH + spans1[LARGE_ARCH] / 2
        self.tier1_start = -before
        self.tier1_end = self.tier1_start + sum(spans1) + PIER * (len(spans1) - 1) + 2 * END
        extra_span = (TIER2_LENGTH - sum(spans1) - PIER * (len(spans1) + sum(TIER2_EXTRA) - 1) - 2 * END) / sum(
            TIER2_EXTRA)
        self.extra_span = extra_span
        self.spans2 = [extra_span] * TIER2_EXTRA[0] + spans1 + [extra_span] * TIER2_EXTRA[1]
        self.tier2_start = self.tier1_start - TIER2_EXTRA[0] * (extra_span + PIER)
        self.tier2_end = self.tier2_start + TIER2_LENGTH
        self.spans1 = spans1
        self.tier3_end = None
        self.tier3_start = None
        self.pier3 = (TIER3_LENGTH - TIER3_ARCHES * TIER3_SPAN - 2 * TIER3_END) / (TIER3_ARCHES - 1)

    def place_top(self, tier3_end):
        self.tier3_end = tier3_end
        self.tier3_start = tier3_end - TIER3_LENGTH
        self.abutment_start = self.tier3_start - ABUTMENT_LENGTH
        self.specus_floor = self.tops[2] - SLAB_THICKNESS - SPECUS_HEIGHT

    def centres(self, tier):
        if tier == 0:
            start, spans, pier, end = self.tier1_start, self.spans1, PIER, END
        elif tier == 1:
            start, spans, pier, end = self.tier2_start, self.spans2, PIER, END
        else:
            start, spans, pier, end = self.tier3_start, [TIER3_SPAN] * TIER3_ARCHES, self.pier3, TIER3_END
        result = []
        cursor = start + end
        for span in spans:
            result.append((cursor + span / 2, span))
            cursor += span + pier
        return result

    def springing(self, tier, span):
        if tier == 2:
            return self.tops[2] - SLAB_THICKNESS - SPECUS_HEIGHT - 0.45 - RING_DEPTH[2] - TIER3_SPAN / 2
        largest = max(self.spans1) / 2
        return self.tops[tier] - CROWN_COVER[tier] - RING_DEPTH[tier] - largest


def oriented(builder, points, normal, material=STONE, uvs=None, color=None):
    if newell_normal(points).dot(Vector(normal)) < 0:
        points = list(reversed(points))
        uvs = list(reversed(uvs)) if uvs is not None else None
    builder.face(builder.points(points), material, uvs=uvs, color=color)


def wall(builder, u0, u1, z0, z1, v, side, step=3.4, material=STONE, color=None):
    if z1 - z0 < 1e-3 or u1 - u0 < 1e-3:
        return
    rows = max(1, int(math.ceil((z1 - z0) / step)))
    columns = max(1, int(math.ceil((u1 - u0) / (step * 2.5))))
    for i in range(columns):
        a = u0 + (u1 - u0) * i / columns
        b = u0 + (u1 - u0) * (i + 1) / columns
        for k in range(rows):
            za = z0 + (z1 - z0) * k / rows
            zb = z0 + (z1 - z0) * (k + 1) / rows
            oriented(builder, [(a, v, za), (b, v, za), (b, v, zb), (a, v, zb)], (0, side, 0), material, color=color)


def end_wall(builder, u, v0, v1, z0, z1, facing, material=STONE):
    rows = max(1, int(math.ceil((z1 - z0) / 2.2)))
    for k in range(rows):
        za = z0 + (z1 - z0) * k / rows
        zb = z0 + (z1 - z0) * (k + 1) / rows
        oriented(builder, [(u, v0, za), (u, v1, za), (u, v1, zb), (u, v0, zb)], (facing, 0, 0), material)


def box(builder, u0, u1, v0, v1, z0, z1, material=STONE, bottom=False, color=None):
    builder.box((u0, v0, z0), (u1, v1, z1), material, bottom=bottom)
    if color is not None:
        builder.tint(len(builder.polygons) - (6 if bottom else 5), color)


def voussoir_count(radius):
    count = max(5, int(round(math.pi * radius / 0.82)))
    return count if count % 2 else count + 1


def pick_rect(rects, length, rng):
    fitting = [rect for rect in rects if abs((rect[2] - rect[0]) * STONE_TILE - length) < 0.45]
    pool = fitting or rects
    return pool[int(rng.integers(0, len(pool)))]


def arch_faces(builder, arch, top, width, rings, rects, rng):
    cu, r, t, zs = arch.centre, arch.radius, arch.ring, arch.springing
    big = r + t
    n = voussoir_count(r)
    angles = [math.pi - math.pi * i / n for i in range(n + 1)]
    for side in (-1, 1):
        v = side * width / 2
        wall(builder, cu - r - arch.pier_left, cu - r, arch.base_left, zs, v, side)
        wall(builder, cu + r, cu + r + arch.pier_right, arch.base_right, zs, v, side)
        if arch.pier_left > t + 1e-3:
            wall(builder, cu - r - arch.pier_left, cu - big, zs, top, v, side)
        if arch.pier_right > t + 1e-3:
            wall(builder, cu + big, cu + r + arch.pier_right, zs, top, v, side)
        for i in range(n):
            a0, a1 = angles[i], angles[i + 1]
            inner0 = (cu + r * math.cos(a0), v, zs + r * math.sin(a0))
            inner1 = (cu + r * math.cos(a1), v, zs + r * math.sin(a1))
            outer0 = (cu + big * math.cos(a0), v, zs + big * math.sin(a0))
            outer1 = (cu + big * math.cos(a1), v, zs + big * math.sin(a1))
            u0, v0, u1, v1 = pick_rect(rects, t, rng)
            inset = 0.0
            uvs = [((u0 + inset) * STONE_TILE, (v0 + inset) * STONE_TILE),
                   ((u1 - inset) * STONE_TILE, (v0 + inset) * STONE_TILE),
                   ((u1 - inset) * STONE_TILE, (v1 - inset) * STONE_TILE),
                   ((u0 + inset) * STONE_TILE, (v1 - inset) * STONE_TILE)]
            oriented(builder, [inner0, outer0, outer1, inner1], (0, side, 0), uvs=uvs)
            x0, z0 = outer0[0], outer0[2]
            x1, z1 = outer1[0], outer1[2]
            steps = max(1, int(math.ceil((top - min(z0, z1)) / 4.0)))
            for k in range(steps):
                fa = k / steps
                fb = (k + 1) / steps
                oriented(builder, [(x0, v, z0 + (top - z0) * fa), (x1, v, z1 + (top - z1) * fa),
                                   (x1, v, z1 + (top - z1) * fb), (x0, v, z0 + (top - z0) * fb)], (0, side, 0))
    for sign in (-1, 1):
        face_u = cu + sign * r
        base = arch.base_left if sign < 0 else arch.base_right
        rows = max(1, int(math.ceil((zs - base) / 2.2)))
        for k in range(rows):
            za = base + (zs - base) * k / rows
            zb = base + (zs - base) * (k + 1) / rows
            oriented(builder, [(face_u, -width / 2, za), (face_u, width / 2, za), (face_u, width / 2, zb),
                               (face_u, -width / 2, zb)], (-sign, 0, 0))
    gap = 0.05 if rings > 1 else 0.0
    ring_width = width / rings
    for k in range(rings):
        va = -width / 2 + k * ring_width + (gap / 2 if k else 0.0)
        vb = -width / 2 + (k + 1) * ring_width - (gap / 2 if k < rings - 1 else 0.0)
        offset_u = float(rng.uniform(0, STONE_TILE))
        offset_v = float(rng.uniform(0, STONE_TILE))
        for i in range(n):
            a0, a1 = angles[i], angles[i + 1]
            p0 = (cu + r * math.cos(a0), zs + r * math.sin(a0))
            p1 = (cu + r * math.cos(a1), zs + r * math.sin(a1))
            s0 = offset_v + i * COURSE
            s1 = s0 + COURSE
            points = [(p0[0], va, p0[1]), (p0[0], vb, p0[1]), (p1[0], vb, p1[1]), (p1[0], va, p1[1])]
            uvs = [(offset_u + va, s0), (offset_u + vb, s0), (offset_u + vb, s1), (offset_u + va, s1)]
            middle = (a0 + a1) / 2
            oriented(builder, points, (-math.cos(middle), 0, -math.sin(middle)), uvs=uvs)
        if k < rings - 1:
            groove_radius = r + 0.04
            for i in range(n):
                a0, a1 = angles[i], angles[i + 1]
                g0 = (cu + groove_radius * math.cos(a0), zs + groove_radius * math.sin(a0))
                g1 = (cu + groove_radius * math.cos(a1), zs + groove_radius * math.sin(a1))
                middle = (a0 + a1) / 2
                oriented(builder, [(g0[0], vb, g0[1]), (g0[0], vb + gap, g0[1]), (g1[0], vb + gap, g1[1]),
                                   (g1[0], vb, g1[1])], (-math.cos(middle), 0, -math.sin(middle)),
                         color=(0.32, 0.29, 0.25))
                for edge_v, facing in ((vb, 1), (vb + gap, -1)):
                    q0 = (cu + r * math.cos(a0), zs + r * math.sin(a0))
                    q1 = (cu + r * math.cos(a1), zs + r * math.sin(a1))
                    oriented(builder, [(q0[0], edge_v, q0[1]), (g0[0], edge_v, g0[1]), (g1[0], edge_v, g1[1]),
                                       (q1[0], edge_v, q1[1])], (0, facing, 0), color=(0.4, 0.36, 0.31))


def impost(builder, u0, u1, z, width, projection=0.2, height=0.48):
    box(builder, u0 - projection, u1 + projection, -width / 2 - projection, width / 2 + projection, z - height, z)
    box(builder, u0 - projection * 0.5, u1 + projection * 0.5, -width / 2 - projection * 0.5,
        width / 2 + projection * 0.5, z - height - 0.22, z - height)


def corbels(builder, arch, width, rings, rng):
    cu, r, zs = arch.centre, arch.radius, arch.springing
    ring_width = width / rings
    for angle in (math.radians(9.0), math.radians(171.0)):
        x = cu + r * math.cos(angle)
        z = zs + r * math.sin(angle)
        inward = -1 if math.cos(angle) > 0 else 1
        for k in range(rings):
            va = -width / 2 + k * ring_width + 0.18
            vb = va + ring_width - 0.36
            depth = 0.42 + 0.08 * float(rng.random())
            if inward > 0:
                box(builder, x - 0.02, x + depth, va, vb, z - 0.3, z + 0.32)
            else:
                box(builder, x - depth, x + 0.02, va, vb, z - 0.3, z + 0.32)


def bosses(builder, u_centre, half, z, width, rng, count=2, projection=0.48):
    for side in (-1, 1):
        for k in range(count):
            offset = (k - (count - 1) / 2) * (2 * half / max(count, 1)) * 0.75
            jitter = float(rng.uniform(-0.15, 0.15))
            u = u_centre + offset + jitter
            size = float(rng.uniform(0.55, 0.8))
            v_face = side * width / 2
            v_out = v_face + side * (projection + float(rng.uniform(-0.06, 0.06)))
            box(builder, u - size / 2, u + size / 2, min(v_face, v_out), max(v_face, v_out), z, z + 0.55)


def cutwater(builder, u_centre, half, width, base, top, cap):
    face_v = -width / 2
    tip = (u_centre, face_v - CUTWATER_DEPTH)
    left = (u_centre - half, face_v)
    right = (u_centre + half, face_v)
    rows = max(1, int(math.ceil((top - base) / 2.2)))
    for k in range(rows):
        za = base + (top - base) * k / rows
        zb = base + (top - base) * (k + 1) / rows
        for a, b in ((left, tip), (tip, right)):
            normal = (-(b[1] - a[1]), b[0] - a[0], 0.0)
            centre = Vector(((a[0] + b[0]) / 2 - u_centre, (a[1] + b[1]) / 2 - face_v + CUTWATER_DEPTH / 2, 0))
            if Vector(normal).dot(centre) < 0:
                normal = tuple(-c for c in normal)
            oriented(builder, [(a[0], a[1], za), (b[0], b[1], za), (b[0], b[1], zb), (a[0], a[1], zb)], normal)
    apex = (u_centre, face_v - 0.15, top + cap)
    for a, b in ((left, tip), (tip, right)):
        points = [(a[0], a[1], top), (b[0], b[1], top), apex]
        oriented(builder, points, (0, -0.6, 0.8))


def tier_body(builder, layout, tier, ground, rects, rng):
    width = TIER_WIDTHS[tier]
    top = layout.tops[tier] - (SLAB_THICKNESS if tier == 2 else 0.0)
    rings = TIER_RINGS[tier]
    centres = layout.centres(tier)
    if tier == 0:
        start, end, pier = layout.tier1_start, layout.tier1_end, PIER
    elif tier == 1:
        start, end, pier = layout.tier2_start, layout.tier2_end, PIER
    else:
        start, end, pier = layout.tier3_start, layout.tier3_end, layout.pier3
    lower_start = [None, layout.tier1_start, layout.tier2_start][tier]
    lower_end = [None, layout.tier1_end, layout.tier2_end][tier]

    def base_at(u0, u1):
        if tier == 0:
            return min(layout.base - 3.0, ground(u0, u1) - 1.2)
        if lower_start - 0.05 <= u0 and u1 <= lower_end + 0.05:
            return layout.tops[tier - 1]
        return min(layout.tops[tier - 1], ground(u0, u1) - 1.0)

    arches = []
    for index, (centre, span) in enumerate(centres):
        left_half = END if index == 0 else pier / 2
        right_half = END if index == len(centres) - 1 else pier / 2
        r = span / 2
        springing = layout.springing(tier, span)
        bl = base_at(centre - r - left_half, centre - r)
        br = base_at(centre + r, centre + r + right_half)
        arches.append(Arch(centre, span, springing, RING_DEPTH[tier], bl, br, left_half, right_half))
    for arch in arches:
        arch_faces(builder, arch, top, width, rings, rects, rng)
    for u, facing in ((start, -1), (end, 1)):
        base = base_at(u - 0.1, u + 0.1) if tier else min(layout.base - 3.0, ground(u - 0.1, u + 0.1) - 1.2)
        end_wall(builder, u, -width / 2, width / 2, base, top, facing)
    pieces = max(1, int(math.ceil((end - start) / 12.0))) if tier < 2 else 0
    for k in range(pieces):
        a = start + (end - start) * k / pieces
        b = start + (end - start) * (k + 1) / pieces
        oriented(builder, [(a, -width / 2, top), (b, -width / 2, top), (b, width / 2, top), (a, width / 2, top)],
                 (0, 0, 1))
    return arches


def tier_details(builder, layout, tier, arches, rng):
    width = TIER_WIDTHS[tier]
    rings = TIER_RINGS[tier]
    top = layout.tops[tier]
    for index, arch in enumerate(arches):
        corbels(builder, arch, width, rings, rng)
        if index == len(arches) - 1:
            continue
        nxt = arches[index + 1]
        u0 = arch.centre + arch.radius
        u1 = nxt.centre - nxt.radius
        middle = (u0 + u1) / 2
        half = (u1 - u0) / 2
        impost(builder, u0, u1, arch.springing, width)
        if tier == 0:
            base = max(arch.base_right, layout.base - 1.5)
            cutwater(builder, middle, half, width, base, layout.base + CUTWATER_TOP, CUTWATER_CAP)
            bosses(builder, middle, half, arch.springing + 0.75, width, rng, 2)
            bosses(builder, middle, half, arch.springing + 4.6, width, rng, 2, 0.4)
        elif tier == 1:
            bosses(builder, middle, half, arch.springing - 3.2, width, rng, 2)
            bosses(builder, middle, half, arch.springing + 0.7, width, rng, 2)
            bosses(builder, middle, half, arch.springing + 5.4, width, rng, 1, 0.42)
    if tier < 2:
        start = layout.tier1_start if tier == 0 else layout.tier2_start
        end = layout.tier1_end if tier == 0 else layout.tier2_end
        for side in (-1, 1):
            v_face = side * width / 2
            v_out = v_face + side * 0.16
            box(builder, start, end, min(v_face, v_out), max(v_face, v_out), top - 0.42, top)


def specus(builder, layout, start, end, pieces_length=15.0):
    floor = layout.specus_floor
    top = layout.tops[2] - SLAB_THICKNESS
    course = top - RAISED_COURSE
    half = SPECUS_WIDTH / 2
    water = floor + 1.02
    pieces = max(1, int(math.ceil((end - start) / pieces_length)))
    red = (0.58, 0.37, 0.30)
    for k in range(pieces):
        a = start + (end - start) * k / pieces
        b = start + (end - start) * (k + 1) / pieces
        for side in (-1, 1):
            v = side * half
            oriented(builder, [(a, v, floor), (b, v, floor), (b, v, course), (a, v, course)], (0, -side, 0),
                     material="lime_wash", color=red)
            oriented(builder, [(a, v, water - 0.04), (b, v, water - 0.04), (b, v, water + 0.035),
                               (a, v, water + 0.035)], (0, -side, 0), material="lime_wash", color=(0.9, 0.88, 0.82))
            oriented(builder, [(a, v, course + 0.025), (b, v, course + 0.025), (b, v, top), (a, v, top)],
                     (0, -side, 0), color=(0.86, 0.82, 0.74))
            oriented(builder, [(a, v, course), (b, v, course), (b, v, course + 0.025), (a, v, course + 0.025)],
                     (0, -side, 0), material="lime_wash", color=(0.3, 0.26, 0.22))
            oriented(builder, [(a, side * (TIER_WIDTHS[2] / 2), top), (b, side * (TIER_WIDTHS[2] / 2), top),
                               (b, v, top), (a, v, top)], (0, 0, 1))
        oriented(builder, [(a, -half, water), (b, -half, water), (b, half, water), (a, half, water)], (0, 0, 1),
                 material="river", color=(0.2, 0.3, 0.27))


def slab_uvs(rect, corners_uv):
    u0, v0, u1, v1 = rect
    return [((u0 + (u1 - u0) * s) * STONE_TILE, (v0 + (v1 - v0) * t) * STONE_TILE) for s, t in corners_uv]


SLAB_RECTS = []


def slab_rect(rng):
    return SLAB_RECTS[int(rng.integers(0, len(SLAB_RECTS)))] if SLAB_RECTS else None


def slabs(builder, layout, start, end, rng, gap_at=None):
    top = layout.tops[2]
    lifted = []
    cursor = start
    while cursor < end - 0.3:
        width = min(float(rng.uniform(0.55, 1.05)), end - cursor)
        a = cursor + 0.008
        b = cursor + width - 0.008
        cursor += width
        middle = (a + b) / 2
        if gap_at is not None and abs(middle - gap_at) < 1.25:
            lifted.append((a, b))
            continue
        tilt = float(rng.uniform(-0.012, 0.012))
        drop = float(rng.uniform(-0.02, 0.01))
        half = SLAB_LENGTH / 2 + float(rng.uniform(-0.04, 0.04))
        z0 = top - SLAB_THICKNESS + drop
        z1 = top + drop
        corners = [(a, -half, z0), (b, -half, z0), (b, half, z0), (a, half, z0),
                   (a, -half, z1 - tilt), (b, -half, z1 - tilt), (b, half, z1 + tilt), (a, half, z1 + tilt)]
        tone = float(rng.normal(0.8, 0.08))
        warm = float(rng.normal(0.0, 0.025))
        colour = (tone * (0.97 + warm), tone * 0.95, tone * (0.9 - warm))
        rect = slab_rect(rng)
        top_uvs = slab_uvs(rect, [(0, 0), (0, 1), (1, 1), (1, 0)]) if rect else None
        quads = [((4, 5, 6, 7), (0, 0, 1), top_uvs), ((0, 1, 5, 4), (0, -1, 0), None),
                 ((1, 2, 6, 5), (1, 0, 0), None), ((2, 3, 7, 6), (0, 1, 0), None), ((3, 0, 4, 7), (-1, 0, 0), None),
                 ((0, 3, 2, 1), (0, 0, -1), None)]
        for indices, normal, uvs in quads:
            oriented(builder, [corners[i] for i in indices], normal, uvs=uvs, color=colour)
    return lifted


def stick(builder, start, end, radius, colour):
    start = Vector(start)
    direction = Vector(end) - start
    rotation = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    piece = MeshBuilder()
    piece.lathe([(0.0, 0.0), (radius, 0.0), (radius, direction.length), (0.0, direction.length)], 5, "matte",
                smooth=True, matrix=Matrix.Translation(start) @ rotation)
    piece.tint(0, colour)
    builder.merge(piece)


def lifted_slabs(builder, layout, gaps):
    top = layout.tops[2]
    wood = (0.42, 0.31, 0.21)
    edge = min(a for a, _ in gaps)
    for index, (a, b) in enumerate(gaps):
        width = b - a
        lean = math.radians(-16.0 - 5.0 * index)
        piece = MeshBuilder()
        half = SLAB_LENGTH / 2
        corners = [(0.0, -half, 0.0), (SLAB_THICKNESS, -half, 0.0), (SLAB_THICKNESS, half, 0.0), (0.0, half, 0.0),
                   (0.0, -half, width), (SLAB_THICKNESS, -half, width), (SLAB_THICKNESS, half, width),
                   (0.0, half, width)]
        rect = SLAB_RECTS[index % len(SLAB_RECTS)] if SLAB_RECTS else None
        face_uvs = slab_uvs(rect, [(0, 0), (1, 0), (1, 1), (0, 1)]) if rect else None
        for indices, normal, uvs in (((1, 2, 6, 5), (1, 0, 0), face_uvs), ((0, 3, 7, 4), (-1, 0, 0), face_uvs),
                                     ((0, 1, 5, 4), (0, -1, 0), None), ((3, 7, 6, 2), (0, 1, 0), None),
                                     ((4, 5, 6, 7), (0, 0, 1), None), ((0, 3, 2, 1), (0, 0, -1), None)):
            oriented(piece, [corners[i] for i in indices], normal, uvs=uvs, color=(0.84, 0.79, 0.7))
        u = edge - 0.75 - index * 0.75
        rotation = Matrix.Rotation(lean, 4, "Y")
        builder.merge(piece, Matrix.Translation((u, 0.05 * index, top + 0.002)) @ rotation)
        tip = Vector((u, 0.0, top + 0.002)) + rotation.to_3x3() @ Vector((0.0, 0.0, width))
        for v in (-1.1, 1.1):
            stick(builder, (tip.x - 0.8, v, top), (tip.x - 0.03, v, tip.z - 0.05), 0.045, wood)
    stick(builder, (edge - 0.3, -1.3, top + 0.06), (edge - 2.5, -0.85, top + 0.06), 0.05, wood)
    roller = MeshBuilder()
    roller.lathe([(0.0, -0.75), (0.11, -0.75), (0.11, 0.75), (0.0, 0.75)], 8, "matte", smooth=True,
                 matrix=Matrix.Translation((edge - 2.9, 0.2, top + 0.11)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    roller.tint(0, (0.5, 0.38, 0.26))
    builder.merge(roller)


class Segment:
    def __init__(self, near, far):
        self.near = Vector(near)
        self.far = Vector(far)
        self.length = (self.near - self.far).length
        self.direction = (self.near - self.far).normalized()
        self.angle = math.atan2(self.direction.y, self.direction.x)
        self.matrix = Matrix.Translation((self.far.x, self.far.y, 0.0)) @ Matrix.Rotation(self.angle, 4, "Z")

    def to_bridge(self, u, v):
        cos, sin = math.cos(self.angle), math.sin(self.angle)
        u = np.asarray(u, dtype=float)
        v = np.asarray(v, dtype=float)
        return self.far.x + u * cos - v * sin, self.far.y + u * sin + v * cos


BASIN_INNER = (5.2, 6.4)
BASIN_WALL = 0.63
BASIN_RIM = 0.8


def bezier(p0, control, end, t):
    t = float(t)
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * control + t * t * end


def abutment_path(layout, basin_centre, spacing=6.0):
    p0 = Vector((layout.tier3_start, 0.0))
    centre = Vector(basin_centre)
    control = p0 + Vector((-1.0, 0.0)) * ((centre - p0).length * 0.42)
    toward = (control - centre).normalized()
    end = centre + toward * (BASIN_INNER[0] / 2 + BASIN_WALL + BASIN_RIM)
    samples = [bezier(p0, control, end, t) for t in np.linspace(0.0, 1.0, 201)]
    length = sum((b - a).length for a, b in zip(samples[:-1], samples[1:]))
    count = max(2, int(math.ceil(length / spacing)))
    points = [bezier(p0, control, end, t) for t in np.linspace(0.0, 1.0, count + 1)]
    return points, centre, toward, length


def footprint_of(segment, height, u0, u1, half):
    gu, gv = np.meshgrid(np.linspace(u0, u1, 5), np.linspace(-half, half, 5))
    bu, bv = segment.to_bridge(gu, gv)
    return float(np.min(height(bu, bv)))


def abutment(builder, layout, height, points, rng):
    width = TIER_WIDTHS[2]
    top = layout.tops[2] - SLAB_THICKNESS
    for near, far in zip(points[:-1], points[1:]):
        segment = Segment(near, far)
        piece = MeshBuilder()
        length = segment.length + 0.06
        base = footprint_of(segment, height, -0.03, length, width / 2) - 1.0
        for side in (-1, 1):
            wall(piece, -0.03, length, base, top, side * width / 2, side, step=2.0)
        specus(piece, layout, -0.03, length)
        slabs(piece, layout, -0.03, length, rng)
        builder.merge(piece, segment.matrix)


def split_box(builder, u0, u1, v0, v1, z0, z1, gap_axis, gap_centre, gap_width):
    if gap_axis == "u":
        for a, b in ((u0, gap_centre - gap_width / 2), (gap_centre + gap_width / 2, u1)):
            if b - a > 1e-3:
                box(builder, a, b, v0, v1, z0, z1)
    else:
        for a, b in ((v0, gap_centre - gap_width / 2), (gap_centre + gap_width / 2, v1)):
            if b - a > 1e-3:
                box(builder, u0, u1, a, b, z0, z1)


def gate(builder, axis, position, width, bottom, height, thickness=0.28):
    wood = (0.40, 0.29, 0.19)
    if axis == "u":
        box(builder, position - thickness / 2, position + thickness / 2, -width / 2 - 0.1, width / 2 + 0.1, bottom,
            bottom + height, material="matte", color=wood)
        box(builder, position - 0.04, position + 0.04, -0.06, 0.06, bottom + height, bottom + height + 0.45,
            material="matte", color=wood)
    else:
        box(builder, -width / 2 - 0.1, width / 2 + 0.1, position - thickness / 2, position + thickness / 2, bottom,
            bottom + height, material="matte", color=wood)
        box(builder, -0.06, 0.06, position - 0.04, position + 0.04, bottom + height, bottom + height + 0.45,
            material="matte", color=wood)


def jambs(builder, wall_start, wall_end, width, z0, z1):
    for side in (-1, 1):
        inner = side * width / 2
        outer = side * (width / 2 + 0.24)
        box(builder, wall_start, wall_end, min(inner, outer), max(inner, outer), z0, z1, color=(0.94, 0.9, 0.82))
        for groove in (0.3, 0.68):
            g = wall_start + (wall_end - wall_start) * groove
            oriented(builder, [(g - 0.07, inner - side * 0.003, z0), (g + 0.07, inner - side * 0.003, z0),
                               (g + 0.07, inner - side * 0.003, z1), (g - 0.07, inner - side * 0.003, z1)],
                     (0, -side, 0), material="lime_wash", color=(0.36, 0.31, 0.26))


def discharge_channel(height, frame, start_v, side, rng):
    channel = MeshBuilder()
    half = 0.8
    previous = None
    for k in range(11):
        v = start_v + 2.0 * k
        bu, bv = frame.to_bridge(0.0, side * v)
        ground = float(np.asarray(height(np.array([float(bu)]), np.array([float(bv)])))[0])
        if previous is not None:
            a, b = side * (v - 2.0), side * v
            z0, z1 = previous + 0.16, ground + 0.16
            tone = float(rng.normal(0.8, 0.06))
            colour = (tone * 0.98, tone * 0.94, tone * 0.88)
            corners = [(-half, a, z0 - 0.4), (half, a, z0 - 0.4), (half, b, z1 - 0.4), (-half, b, z1 - 0.4),
                       (-half, a, z0), (half, a, z0), (half, b, z1), (-half, b, z1)]
            for indices, normal in (((4, 5, 6, 7), (0, 0, 1)), ((0, 1, 5, 4), (0, -side, 0)),
                                    ((1, 2, 6, 5), (1, 0, 0)), ((2, 3, 7, 6), (0, side, 0)),
                                    ((3, 0, 4, 7), (-1, 0, 0))):
                oriented(channel, [corners[i] for i in indices], normal, color=colour)
        previous = ground
    return channel


def basin(builder, layout, height, centre, toward, discharge_side, rng):
    floor = layout.specus_floor
    inner_u, inner_v = BASIN_INNER
    outer = BASIN_WALL + BASIN_RIM
    top = layout.tops[2] - SLAB_THICKNESS + 0.25
    frame = Segment(centre + toward, centre)
    piece = MeshBuilder()
    u0, u1 = -inner_u / 2, inner_u / 2
    v0, v1 = -inner_v / 2, inner_v / 2
    base = footprint_of(frame, height, u0 - outer, u1 + outer, v1 + outer) - 1.2
    split_box(piece, u0 - outer, u0, v0 - outer, v1 + outer, base, top, "v", 0.0, SPECUS_WIDTH + 0.48)
    split_box(piece, u1, u1 + outer, v0 - outer, v1 + outer, base, top, "v", 0.0, SPECUS_WIDTH + 0.48)
    for sign, (a, b) in ((-1, (v0 - outer, v0)), (1, (v1, v1 + outer))):
        if sign == discharge_side:
            split_box(piece, u0, u1, a, b, base, top, "u", 0.0, 1.0)
        else:
            box(piece, u0, u1, a, b, base, top)
    oriented(piece, [(u0, v0, floor), (u1, v0, floor), (u1, v1, floor), (u0, v1, floor)], (0, 0, 1),
             material="lime_wash", color=(0.6, 0.4, 0.33))
    lining = (0.58, 0.38, 0.31)
    for v, normal, open_side in ((v0, (0, 1, 0), discharge_side < 0), (v1, (0, -1, 0), discharge_side > 0)):
        for p, q in ([(u0, -0.5), (0.5, u1)] if open_side else [(u0, u1)]):
            oriented(piece, [(p, v, floor), (q, v, floor), (q, v, top), (p, v, top)], normal, material="lime_wash",
                     color=lining)
    for u, normal in ((u0, (1, 0, 0)), (u1, (-1, 0, 0))):
        for p, q in ((v0, -SPECUS_WIDTH / 2), (SPECUS_WIDTH / 2, v1)):
            oriented(piece, [(u, p, floor), (u, q, floor), (u, q, top), (u, p, top)], normal, material="lime_wash",
                     color=lining)
    water = floor + 1.02
    oriented(piece, [(u0, v0, water), (u1, v0, water), (u1, v1, water), (u0, v1, water)], (0, 0, 1),
             material="river", color=(0.42, 0.6, 0.56))
    for a, b in ((u0 - outer, u0), (u1, u1 + outer)):
        jambs(piece, a, b, SPECUS_WIDTH, floor, top + 0.06)
        oriented(piece, [(a, -SPECUS_WIDTH / 2, floor), (b, -SPECUS_WIDTH / 2, floor), (b, SPECUS_WIDTH / 2, floor),
                         (a, SPECUS_WIDTH / 2, floor)], (0, 0, 1), material="lime_wash", color=lining)
        oriented(piece, [(a, -SPECUS_WIDTH / 2, water), (b, -SPECUS_WIDTH / 2, water),
                         (b, SPECUS_WIDTH / 2, water), (a, SPECUS_WIDTH / 2, water)], (0, 0, 1), material="river",
                 color=(0.42, 0.6, 0.56))
    gate(piece, "u", u0 - outer * 0.7, SPECUS_WIDTH, floor + 1.15, 1.3)
    gate(piece, "u", u1 + outer * 0.3, SPECUS_WIDTH, floor + 0.4, 1.3)
    gate(piece, "v", discharge_side * (v1 + outer * 0.35), 1.0, floor, 1.75)
    stub_length = 15.0
    stub_frame = Segment(centre - toward * (inner_u / 2 + outer), centre - toward * (inner_u / 2 + outer + stub_length))
    stub_base = footprint_of(stub_frame, height, 0.0, stub_length, TIER_WIDTHS[2] / 2) - 1.0
    stub = MeshBuilder()
    for side in (-1, 1):
        wall(stub, 0.0, stub_length, stub_base, layout.tops[2] - SLAB_THICKNESS, side * TIER_WIDTHS[2] / 2, side,
             step=2.0)
    specus(stub, layout, 0.0, stub_length)
    slabs(stub, layout, 0.0, stub_length, rng)
    piece.merge(stub, Matrix.Translation((u0 - outer - stub_length, 0.0, 0.0)))
    piece.merge(discharge_channel(height, frame, v1 + outer, discharge_side, rng))
    builder.merge(piece, frame.matrix)
    keeper_v = discharge_side * (v1 + outer * 0.4)
    return {"frame": frame, "centre": centre, "toward": toward, "top": top, "floor": floor,
            "keeper": frame.matrix @ Vector((0.95, keeper_v, top)),
            "keeper_angle": frame.angle + math.pi / 2,
            "discharge_side": discharge_side, "half": (inner_u / 2 + outer, inner_v / 2 + outer),
            "stub_length": stub_length}


def weathering(mesh, layout, ground_local, seed=3):
    count = len(mesh.loops)
    if count == 0:
        return
    vertex_index = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex_index)
    positions = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)[vertex_index]
    normals = np.empty(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get("normal", normals)
    normals = normals.reshape(-1, 3)
    totals = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", totals)
    loop_polygon = np.repeat(np.arange(len(mesh.polygons)), totals)
    normal = normals[loop_polygon]
    u, v, z = positions[:, 0], positions[:, 1], positions[:, 2]
    base = layout.base
    rng = np.random.default_rng(seed)
    phases = rng.uniform(0, 6.28, 8)
    broad = (np.sin(u / 23.0 + phases[0]) * 0.5 + np.sin(u / 9.0 + z / 7.0 + phases[1]) * 0.3
             + np.sin(u / 3.7 - z / 5.1 + phases[2]) * 0.2)
    shade = 1.0 + 0.055 * broad
    flood = np.clip(1.0 - (z - base) / 9.0, 0.0, 1.0)
    water_line = np.exp(-((z - (base + 1.6)) / 0.9) ** 2)
    tint = np.ones((count, 3))
    tint *= shade[:, None]
    tint *= (1.0 - 0.18 * flood)[:, None]
    tint *= (1.0 - np.array([0.20, 0.17, 0.12]) * water_line[:, None])
    tint = np.where((z < base + 0.6)[:, None], tint * np.array([0.6, 0.66, 0.6]), tint)
    downward = np.clip(-normal[:, 2], 0, 1)
    tint *= (1.0 - 0.28 * downward)[:, None]
    upward = np.clip(normal[:, 2], 0, 1)
    tint = tint * (1 - 0.25 * upward[:, None]) + np.array([0.86, 0.8, 0.7]) * 0.25 * upward[:, None]
    downstream = np.clip(normal[:, 1], 0, 1)
    tint *= (1.0 - np.array([0.08, 0.06, 0.04]) * downstream[:, None])
    upstream = np.clip(-normal[:, 1], 0, 1)
    tint *= (1.0 + np.array([0.04, 0.02, -0.01]) * upstream[:, None])
    for top in layout.tops:
        below = top - z
        drip = np.clip(1.0 - below / 3.2, 0, 1) * (below > 0)
        streak = 0.5 + 0.5 * np.sin(u * 3.1 + phases[3]) * np.sin(u * 1.3 + phases[4])
        tint *= (1.0 - 0.14 * drip * streak)[:, None]
    if ground_local is not None:
        contact = ground_local(u, v)
        near = np.clip(1.0 - (z - contact) / 1.8, 0, 1)
        tint *= (1.0 - 0.3 * near)[:, None]
        patches = 0.5 + 0.5 * np.sin(u * 0.9 + phases[5]) * np.sin(u * 0.37 + z * 0.8 + phases[6])
        moss = np.clip(1.0 - (z - contact) / 1.4, 0, 1) * patches * (normal[:, 2] > -0.3)
        tint = tint * (1 - 0.4 * moss[:, None]) + np.array([0.46, 0.5, 0.32]) * 0.4 * moss[:, None]
    attribute = mesh.color_attributes.get("Col")
    colours = np.empty(count * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    colours[:, :3] = np.clip(colours[:, :3] * tint, 0, 1)
    attribute.data.foreach_set("color_srgb", colours.ravel())


def build_bridge(layout, ground, height, rects, basin_centre, discharge_side, seed=11, gap_at=None):
    rng = np.random.default_rng(seed)
    SLAB_RECTS[:] = [rect for rect in rects if (rect[2] - rect[0]) * STONE_TILE > 1.5]
    builder = MeshBuilder()
    arches = []
    for tier in range(3):
        tier_arches = tier_body(builder, layout, tier, ground, rects, rng)
        tier_details(builder, layout, tier, tier_arches, rng)
        arches.append(tier_arches)
    points, centre, toward, _ = abutment_path(layout, basin_centre)
    abutment(builder, layout, height, points, rng)
    info = basin(builder, layout, height, centre, toward, discharge_side, rng)
    specus(builder, layout, layout.tier3_start, layout.tier3_end)
    lifted = slabs(builder, layout, layout.tier3_start, layout.tier3_end, rng, gap_at)
    if lifted:
        lifted_slabs(builder, layout, lifted)
        info["gap"] = (min(a for a, _ in lifted), max(b for _, b in lifted))
    info["path"] = points
    return builder, arches, info
