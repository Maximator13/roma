import math
import random

import numpy as np
from mathutils import Matrix, Vector

from . import gizeh_plan as plan
from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import ellipsoid, tube

SAND = (0.93, 0.76, 0.52)
RUBBLE = (0.86, 0.78, 0.64)
TAU = 2 * math.pi


def frustum(builder, half0, half1, z0, z1, material, rows=1, cols=1, top=True, bands=None, color=None,
            centre1=(0.0, 0.0)):
    (hx0, hy0), (hx1, hy1) = half0, half1
    cx1, cy1 = centre1
    levels = list(np.linspace(z0, z1, rows + 1))
    if bands:
        levels = sorted(set(levels + [b for b, _ in bands if z0 < b < z1]))
    span = z1 - z0

    def corner(index, z):
        t = (z - z0) / span if span > 0 else 0.0
        hx = hx0 + (hx1 - hx0) * t
        hy = hy0 + (hy1 - hy0) * t
        sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[index]
        return Vector((cx1 * t + sx * hx, cy1 * t + sy * hy, z))

    for face in range(4):
        a, b = face, (face + 1) % 4
        direction = (corner(b, z0) - corner(a, z0)).normalized()
        run_bottom = abs(hy0 if face % 2 == 0 else hx0)
        run_top = abs(hy1 if face % 2 == 0 else hx1)
        slant = math.hypot(span, run_bottom - run_top) / span if span > 0 else 1.0
        for lower, upper in zip(levels[:-1], levels[1:]):
            middle = (lower + upper) / 2
            chosen = material
            if bands:
                for limit, band_material in bands:
                    if middle < limit:
                        chosen = band_material
                        break
            for column in range(cols):
                t0, t1 = column / cols, (column + 1) / cols
                points = [corner(a, lower).lerp(corner(b, lower), t0), corner(a, lower).lerp(corner(b, lower), t1),
                          corner(a, upper).lerp(corner(b, upper), t1), corner(a, upper).lerp(corner(b, upper), t0)]
                uvs = [(p.x * direction.x + p.y * direction.y, (p.z - z0) * slant) for p in points]
                builder.face(builder.points(points), chosen, uvs=uvs, color=color)
    if top and (hx1 > 1e-3 or hy1 > 1e-3):
        points = [corner(k, z1) for k in range(4)]
        builder.face(builder.points(points), material, color=color)
    return builder


def great_pyramid(item, rows=30, cols=22):
    builder = MeshBuilder()
    hx, hy, height = item["half_x"], item["half_y"], item["height"]
    top = item.get("top", 0.0) / 2
    granite = item.get("granite", 0.0)
    bands = []
    if granite:
        bands.append((granite, "granite_rough" if item["key"] == "menkaure" else "casing_granite"))
    if top > 0:
        z_top = height * (1 - top / hx)
        frustum(builder, (hx, hy), (top, top * hy / hx), 0.0, z_top, item["casing"], rows, cols, True, bands)
    else:
        z_cap = height * (1 - 1.0 / hx)
        frustum(builder, (hx, hy), (1.0, hy / hx), 0.0, z_cap, item["casing"], rows, cols, False, bands)
        frustum(builder, (1.0, hy / hx), (0.0, 0.0), z_cap, height, item["casing"], 1, 1, False)
    if item["key"] == "khufu":
        door_z = 16.9
        t = door_z / height
        y = hy * (1 - t)
        normal = Vector((0.0, hy, height)).normalized()
        slope = Vector((0.0, -hy, height)).normalized()
        centre = Vector((7.3, y, door_z)) + normal * 0.04
        corners = [centre + Vector((1.05, 0, 0)) * sx * 0.5 + slope * sy * 0.62 for sx, sy in
                   ((1, -1), (-1, -1), (-1, 1), (1, 1))]
        builder.polygon(corners, "casing", color=(0.82, 0.78, 0.70))
    base_apron(builder, hx, hy, sum(map(ord, item["key"])), int((hx + hy) * 0.55))
    return builder


def base_apron(builder, hx, hy, seed, count):
    rng = random.Random(seed)
    for k in range(count):
        side = rng.randrange(4)
        along = rng.uniform(-1.02, 1.02)
        out = rng.uniform(-0.6, 1.6)
        length = rng.uniform(2.5, 8.0) * min(1.0, hx / 60.0 + 0.3)
        width = rng.uniform(1.0, 2.6)
        high = rng.uniform(0.22, 0.6) * min(1.0, hx / 60.0 + 0.4)
        if side % 2 == 0:
            centre = (along * hx, (-1 if side == 0 else 1) * (hy + out), 0.15)
            radii = (length, width, high)
        else:
            centre = ((1 if side == 1 else -1) * (hx + out), along * hy, 0.15)
            radii = (width, length, high)
        shade = rng.uniform(0.96, 1.02)
        ellipsoid(builder, centre, radii, tuple(c * shade for c in (0.96, 0.87, 0.70)), 12, 4)
    for k in range(count // 2):
        side = rng.randrange(4)
        along = rng.uniform(-1.0, 1.0)
        out = rng.uniform(0.4, 5.0)
        size = rng.uniform(0.25, 0.9)
        if side % 2 == 0:
            x, y = along * hx, (-1 if side == 0 else 1) * (hy + out)
        else:
            x, y = (1 if side == 1 else -1) * (hx + out), along * hy
        frame = Matrix.Translation((x, y, 0.12)) @ Matrix.Rotation(rng.uniform(0, TAU), 4, "Z") @ Matrix.Rotation(
            rng.uniform(-0.3, 0.3), 4, "X")
        builder.box((-size, -size * 0.7, -size * 0.4), (size, size * 0.7, size * 0.5), "casing", matrix=frame)


def ruined_pyramid(item):
    rng = random.Random(item["seed"])
    builder = MeshBuilder()
    h = item["half_x"]
    height = item["height"]
    shell = 1.6
    tiers = 4
    core_top = height * 0.86
    dz = core_top / tiers
    profile = []
    for k in range(tiers):
        z0, z1 = dz * k, dz * (k + 1)
        bottom = (h - shell) * (1 - z1 / height) + 0.3
        top = bottom - dz * 0.3 if k < tiers - 1 else bottom * 0.55
        profile.append((z0, z1, bottom, top))
        frustum(builder, (bottom, bottom), (max(top, 0.8), max(top, 0.8)), z0, z1, "core_stone", 2, 4, True)
        builder.polygon_colors[-1] = SAND

    def core_half(z):
        for z0, z1, bottom, top in profile:
            if z <= z1:
                return bottom + (top - bottom) * (z - z0) / (z1 - z0)
        return profile[-1][3]

    for face in range(4):
        rotation = Matrix.Rotation(face * math.pi / 2, 4, "Z")
        cols = 9
        tops = [height * rng.uniform(0.08, 0.36) for _ in range(cols)]
        for c in range(cols):
            t0, t1 = c / cols, (c + 1) / cols
            hc = tops[c]
            s = 1 - hc / height
            outer = [Vector((-h + 2 * h * t0, -h, 0.0)), Vector((-h + 2 * h * t1, -h, 0.0)),
                     Vector(((-h + 2 * h * t1) * s, -h * s, hc)), Vector(((-h + 2 * h * t0) * s, -h * s, hc))]
            core = core_half(hc)
            inset = [Vector((p.x * core / max(h * s, 1e-3), -core, hc)) for p in outer[2:]]
            outer = [rotation @ p for p in outer]
            inset = [rotation @ p for p in inset]
            direction = (outer[1] - outer[0]).normalized()
            uvs = [(p.x * direction.x + p.y * direction.y, p.z * 1.27) for p in outer]
            builder.face(builder.points(outer), "casing", uvs=uvs, color=(0.90, 0.84, 0.72))
            builder.polygon([outer[3], outer[2], inset[0], inset[1]], "core_stone", color=SAND)
            for edge, side in ((0, -1), (1, 1)):
                neighbour = c + side
                if 0 <= neighbour < cols and tops[neighbour] < hc:
                    hn = tops[neighbour]
                    base = outer[0] if edge == 0 else outer[1]
                    p_low = Vector((base.x * (1 - hn / height), base.y * (1 - hn / height), hn))
                    p_top = Vector((base.x * (1 - hc / height), base.y * (1 - hc / height), hc))
                    q_low = Vector((base.x * core_half(hn) / h, base.y * core_half(hn) / h, hn))
                    q_top = Vector((base.x * core / h, base.y * core / h, hc))
                    builder.oriented([p_low, q_low, q_top, p_top],
                                     Vector((direction.x * side, direction.y * side, 0.0)), "core_stone")
    for k in range(int(h * 0.7)):
        angle = rng.uniform(0, TAU)
        side = rng.randrange(4)
        along = rng.uniform(-h, h)
        offset = h + rng.uniform(-1.0, 6.0)
        x, y = [(along, -offset), (offset, along), (along, offset), (-offset, along)][side]
        size = rng.uniform(0.5, 1.6)
        ellipsoid(builder, (x, y, 0.0), (size * 1.3, size, size * 0.55), RUBBLE, 6, 3, "core_stone")
    base_apron(builder, h, h, item["seed"] + 100, int(h * 1.2))
    return builder


def stepped_pyramid(item, tiers=4):
    builder = MeshBuilder()
    h = item["half_x"]
    height = item["height"]
    rng = random.Random(item["seed"])
    for k in range(tiers):
        z0 = height * k / tiers
        z1 = height * (k + 1) / tiers
        bottom = h * (1 - k / tiers) * 0.98
        top = bottom - (z1 - z0) * 0.25
        frustum(builder, (bottom, bottom), (top, top), z0, z1, "core_stone", 2, 3, True)
        builder.polygon_colors[-1] = SAND
    for k in range(int(h)):
        side = rng.randrange(4)
        along = rng.uniform(-h, h)
        offset = h + rng.uniform(-0.5, 4.0)
        x, y = [(along, -offset), (offset, along), (along, offset), (-offset, along)][side]
        size = rng.uniform(0.4, 1.3)
        ellipsoid(builder, (x, y, 0.0), (size * 1.3, size, size * 0.5), RUBBLE, 6, 3, "core_stone")
    base_apron(builder, h, h, item["seed"] + 200, int(h * 1.0))
    return builder


def cased_queen(item):
    data = dict(item, casing="casing", top=0.0)
    return great_pyramid(data, 10, 8)


def ruined_wall(builder, a, b, thickness, base, heights, material, rng, color=None, cap=None):
    a = Vector(a)
    b = Vector(b)
    length = (b - a).length
    direction = (b - a).normalized()
    normal = Vector((-direction.y, direction.x))
    count = max(int(length / 3.0), 1)
    for k in range(count):
        t0, t1 = k / count, (k + 1) / count
        top = rng.uniform(*heights)
        if top < 0.15:
            continue
        p0 = a + (b - a) * t0
        p1 = a + (b - a) * t1
        corners = [p0 - normal * thickness / 2, p1 - normal * thickness / 2, p1 + normal * thickness / 2,
                   p0 + normal * thickness / 2]
        z0 = base(p0.x, p0.y) - 0.8
        outline = [(c.x, c.y) for c in corners]
        first = len(builder.polygons)
        builder.prism(outline, z0, base(p0.x, p0.y) + top, material, bottom=False)
        if color is not None:
            builder.tint(first, color)
        if cap is not None and top > 1.0:
            builder.prism(outline, base(p0.x, p0.y) + top, base(p0.x, p0.y) + top + 0.12, cap, bottom=False)


def pillar(builder, x, y, z, height, size, material, broken=False, rng=None):
    builder.box((x - size / 2, y - size / 2, z - 0.4), (x + size / 2, y + size / 2, z + height), material)
    if broken and rng is not None:
        ellipsoid(builder, (x + rng.uniform(1.0, 2.0), y + rng.uniform(-1.0, 1.0), z + 0.3),
                  (size * 1.4, size * 0.6, size * 0.5), (0.8, 0.5, 0.45), 6, 3, material)


def khufu_temple(ground):
    rng = random.Random(41)
    builder = MeshBuilder()
    t = plan.KHUFU_TEMPLE
    z = ground((t["x0"] + t["x1"]) / 2, (t["y0"] + t["y1"]) / 2)
    builder.box((t["x0"], t["y0"], z - 0.6), (t["x1"], t["y1"], z + 0.35), "basalt")
    court = (t["x0"] + 9.0, t["x1"] - 7.0, t["y0"] + 8.0, t["y1"] - 8.0)
    for k in range(14):
        frac = k / 13
        for x, y in ((court[0] + (court[1] - court[0]) * frac, court[2]),
                     (court[0] + (court[1] - court[0]) * frac, court[3])):
            if rng.random() < 0.55:
                pillar(builder, x, y, z + 0.35, rng.uniform(0.6, 3.6), 1.05, "casing_granite", rng.random() < 0.3,
                       rng)
    for y in np.linspace(court[2], court[3], 9):
        if rng.random() < 0.5:
            pillar(builder, court[0], y, z + 0.35, rng.uniform(0.5, 3.0), 1.05, "casing_granite")
    level = lambda x, y: z + 0.3
    outline = [(t["x0"], t["y0"]), (t["x1"], t["y0"]), (t["x1"], t["y1"]), (t["x0"], t["y1"])]
    for a, b in zip(outline, outline[1:] + outline[:1]):
        ruined_wall(builder, a, b, 2.4, level, (0.0, 3.2), "limestone", rng)
    for k in range(18):
        x = rng.uniform(t["x0"], t["x1"])
        y = rng.uniform(t["y0"], t["y1"])
        ellipsoid(builder, (x, y, z + 0.3), (rng.uniform(1.5, 3.5), rng.uniform(1.0, 2.5), rng.uniform(0.3, 0.8)),
                  SAND, 7, 3)
    return builder


def khafre_temple(ground):
    rng = random.Random(43)
    builder = MeshBuilder()
    t = plan.KHAFRE_TEMPLE
    z = ground((t["x0"] + t["x1"]) / 2, 0.0)
    builder.box((t["x0"], t["y0"], z - 0.8), (t["x1"], t["y1"], z + 0.25), "paving")
    level = lambda x, y: z + 0.2
    outline = [(t["x0"], t["y0"]), (t["x1"], t["y0"]), (t["x1"], t["y1"]), (t["x0"], t["y1"])]
    for a, b in zip(outline, outline[1:] + outline[:1]):
        ruined_wall(builder, a, b, 5.5, level, (1.5, 7.5), "core_stone", rng)
    inner = [(t["x0"] + 14.0, -16.0), (t["x1"] - 12.0, -16.0), (t["x1"] - 12.0, 16.0), (t["x0"] + 14.0, 16.0)]
    for a, b in zip(inner, inner[1:] + inner[:1]):
        ruined_wall(builder, a, b, 3.0, level, (0.0, 5.0), "core_stone", rng)
    for x in np.linspace(t["x0"] + 18.0, t["x1"] - 16.0, 6):
        for y in (-11.0, 11.0):
            if rng.random() < 0.7:
                pillar(builder, x, y, z + 0.2, rng.uniform(1.2, 5.2), 1.3, "casing_granite", rng.random() < 0.25,
                       rng)
    builder.box((t["x1"] - 2.0, -4.0, z - 0.5), (t["x1"] + 6.0, 4.0, z + 0.6), "paving")
    for k in range(24):
        x = rng.uniform(t["x0"] - 4, t["x1"] + 4)
        y = rng.uniform(t["y0"] - 4, t["y1"] + 4)
        ellipsoid(builder, (x, y, z + 0.1), (rng.uniform(2.0, 4.0), rng.uniform(1.4, 3.0), rng.uniform(0.4, 1.2)),
                  SAND, 7, 3)
    return builder


def small_temple(ground, box, seed, material="mudbrick"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    z = ground((box["x0"] + box["x1"]) / 2, (box["y0"] + box["y1"]) / 2)
    level = lambda x, y: z
    outline = [(box["x0"], box["y0"]), (box["x1"], box["y0"]), (box["x1"], box["y1"]), (box["x0"], box["y1"])]
    for a, b in zip(outline, outline[1:] + outline[:1]):
        ruined_wall(builder, a, b, 3.0, level, (0.2, 2.6), material, rng)
    mid = (box["y0"] + box["y1"]) / 2
    ruined_wall(builder, (box["x0"] + 10, mid - 10), (box["x1"] - 8, mid - 10), 2.0, level, (0.0, 1.8), material,
                rng)
    ruined_wall(builder, (box["x0"] + 10, mid + 10), (box["x1"] - 8, mid + 10), 2.0, level, (0.0, 1.8), material,
                rng)
    return builder


def valley_temple(ground):
    rng = random.Random(47)
    builder = MeshBuilder()
    t = plan.KHAFRE_VALLEY
    base = plan.SPHINX["floor"] + 4.0
    level = lambda x, y: base
    outline = [(t["x0"], t["y0"]), (t["x1"], t["y0"]), (t["x1"], t["y1"]), (t["x0"], t["y1"])]
    for a, b in zip(outline, outline[1:] + outline[:1]):
        ruined_wall(builder, a, b, 4.0, level, (1.2, 3.4), "casing_granite", rng)
    for x in np.linspace(t["x0"] + 8, t["x1"] - 8, 4):
        pillar(builder, x, (t["y0"] + t["y1"]) / 2 + 6.0, base, rng.uniform(1.5, 2.6), 1.05, "casing_granite")
    return builder


def causeway(points, ground, width, wall, heights, material, seed, deck="paving", tint=None):
    rng = random.Random(seed)
    builder = MeshBuilder()
    path = plan.resample_line(points, 6.0)
    raw = [ground(x, y) for x, y in path]
    smooth = []
    for k in range(len(raw)):
        window = raw[max(0, k - 3):k + 4]
        smooth.append(max(sum(window) / len(window), raw[k]) + 0.7)
    profile_half = width / 2
    walk = {-1: rng.uniform(*heights), 1: rng.uniform(*heights)}
    first = len(builder.polygons)
    for k in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[k], path[k + 1]
        z0, z1 = smooth[k], smooth[k + 1]
        d = Vector((x1 - x0, y1 - y0)).normalized()
        n = Vector((-d.y, d.x))
        a = Vector((x0, y0))
        b = Vector((x1, y1))
        top = [Vector((*(a - n * profile_half), z0)), Vector((*(b - n * profile_half), z1)),
               Vector((*(b + n * profile_half), z1)), Vector((*(a + n * profile_half), z0))]
        builder.polygon(top, deck)
        for side in (-1, 1):
            edge_a = a + n * side * profile_half
            edge_b = b + n * side * profile_half
            low_a = min(raw[k], z0) - 1.5
            low_b = min(raw[k + 1], z1) - 1.5
            quad = [Vector((*edge_a, low_a)), Vector((*edge_b, low_b)), Vector((*edge_b, z1)), Vector((*edge_a, z0))]
            builder.oriented(quad, Vector((n.x * side, n.y * side, 0.0)), material)
            if wall <= 0:
                continue
            walk[side] = min(max(walk[side] + rng.uniform(-0.7, 0.7), heights[0]), heights[1])
            if rng.random() < 0.12:
                continue
            for part in range(3):
                t0, t1 = part / 3, (part + 1) / 3
                top_wall = walk[side] + rng.uniform(-0.6, 0.6)
                if top_wall < 0.25:
                    continue
                pa = edge_a.lerp(edge_b, t0)
                pb = edge_a.lerp(edge_b, t1)
                inner = pa - n * side * wall
                inner_b = pb - n * side * wall
                outline = [(pa.x, pa.y), (pb.x, pb.y), (inner_b.x, inner_b.y), (inner.x, inner.y)]
                if side < 0:
                    outline = list(reversed(outline))
                builder.prism(outline, min(z0, z1) - 0.1, min(z0, z1) + top_wall, material, bottom=False)
                if top_wall > 0.6 and rng.random() < 0.25:
                    fall = pa.lerp(pb, 0.5) + n * side * rng.uniform(1.0, 3.0)
                    size = rng.uniform(0.35, 0.7)
                    frame = Matrix.Translation((fall.x, fall.y, raw[k] + 0.1)) @ Matrix.Rotation(
                        rng.uniform(0, TAU), 4, "Z") @ Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "X")
                    builder.box((-size * 1.4, -size, -size * 0.5), (size * 1.4, size, size * 0.6), material,
                                matrix=frame)
        if rng.random() < 0.45:
            side = rng.choice((-1, 1))
            centre = a.lerp(b, rng.random()) + n * side * (profile_half - wall - rng.uniform(0.2, 1.0))
            ellipsoid(builder, (centre.x, centre.y, (z0 + z1) / 2 - 0.05),
                      (rng.uniform(1.5, 3.5), rng.uniform(0.8, 1.6), rng.uniform(0.25, 0.6)), SAND, 7, 3)
    if tint is not None:
        for index in range(first, len(builder.polygons)):
            if builder.polygon_colors[index] is None:
                builder.polygon_colors[index] = tint
    return builder, list(zip(path, smooth))


def mastaba(length, width, height, seed, material="limestone", bury=1.5):
    rng = random.Random(seed)
    builder = MeshBuilder()
    batter = 0.16
    frustum(builder, (width / 2, length / 2), (width / 2 - height * batter, length / 2 - height * batter), -bury,
            height - bury, material, 2, 3, True)
    for k, y in enumerate((-length * 0.32, length * 0.3)):
        x = width / 2 - (height * 0.4) * batter
        builder.box((x - 0.4, y - 0.7, -bury + 0.4), (x + 0.12, y + 0.7, -bury + 2.8 + k * 0.4), "shadow_void")
    for k in range(rng.randrange(2, 5)):
        side = rng.choice((-1, 1))
        y = rng.uniform(-length / 2, length / 2)
        ellipsoid(builder, (side * (width / 2 + rng.uniform(0.0, 2.0)), y, -0.3),
                  (rng.uniform(2.0, 4.0), rng.uniform(3.0, 6.0), rng.uniform(0.8, height * 0.6)), SAND, 7, 3)
    return builder


def khentkawes():
    builder = MeshBuilder()
    k = plan.KHENTKAWES
    frustum(builder, (k["half"], k["half"]), (k["half"] - 0.8, k["half"] - 0.8), -1.0, 10.0, "sphinx_rock", 2, 4,
            True)
    frustum(builder, (k["half"] - 8.0, k["half"] - 8.0), (k["half"] - 10.0, k["half"] - 10.0), 10.0, k["height"],
            "limestone", 2, 3, True)
    return builder


def crow_wall(ground):
    w = plan.CROW_WALL
    builder = MeshBuilder()
    gate_x, gate_w = w["gate"]
    z = ground((w["x0"] + w["x1"]) / 2, w["y"])
    half = w["thickness"] / 2
    for x0, x1 in ((w["x0"], gate_x - gate_w / 2), (gate_x + gate_w / 2, w["x1"])):
        builder.box((x0, w["y"] - half, z - 2.0), (x1, w["y"] + half, z + w["height"]), "core_stone")
    builder.box((gate_x - gate_w / 2, w["y"] - half, z + 6.8), (gate_x + gate_w / 2, w["y"] + half, z + w["height"]),
                "core_stone")
    return builder


def placed_distant(ground):
    builder = MeshBuilder()
    for x, y, half, height in plan.ABUSIR:
        local = MeshBuilder()
        frustum(local, (half, half), (half * 0.1, half * 0.1), -2.0, height * 0.9, "core_stone", 1, 1, True,
                color=(0.98, 0.92, 0.80))
        builder.merge(local, Matrix.Translation((x, y, ground(x, y))))
    s = plan.SAQQARA
    local = MeshBuilder()
    for k in range(s["steps"]):
        z0 = s["height"] * k / s["steps"]
        z1 = s["height"] * (k + 1) / s["steps"]
        f = 1 - k * 0.13
        g = f - 0.06
        frustum(local, (s["base_x"] * f, s["base_y"] * f), (s["base_x"] * g, s["base_y"] * g), z0 - (2.0 if k == 0
                                                                                                    else 0.0), z1,
                "casing", 1, 1, True, color=(0.96, 0.90, 0.78))
    builder.merge(local, Matrix.Translation((s["x"], s["y"], ground(s["x"], s["y"]))))
    return builder


def rock_shelf(builder, inner_a, inner_b, outward, depth, floor, ground, material="sphinx_rock"):
    a = Vector(inner_a)
    b = Vector(inner_b)
    out = Vector(outward).normalized()
    length = (b - a).length
    count = max(int(length / 3.0), 1)
    offsets = [0.0, 0.8, 3.0, 7.0, 11.0, depth]
    rows = []
    tops = []
    for k in range(count + 1):
        p = a + (b - a) * k / count
        heights = [ground(p.x + out.x * o, p.y + out.y * o) for o in offsets]
        rim = max(heights[2:]) + 0.15
        tops.append(rim)
        row = []
        for o, h in zip(offsets, heights):
            z = rim if o < 3.5 else max(h + 0.12, rim - (o - 3.0) * 0.12) if o < depth else h - 0.4
            row.append(Vector((p.x + out.x * o, p.y + out.y * o, z)))
        rows.append(row)
    builder.surface(rows, material, facing=(0.0, 0.0, 1.0))
    face_rows = []
    for k in range(count + 1):
        p = a + (b - a) * k / count
        face_rows.append([Vector((p.x, p.y, floor - 0.6)), Vector((p.x, p.y, tops[k]))])
    builder.surface(face_rows, material, facing=(-out.x, -out.y, 0.0))
    return tops


def enclosure(ground):
    builder = MeshBuilder()
    p = plan.PIT
    floor = plan.SPHINX["floor"]
    sides = [((p["x0"], p["y1"]), (p["x1"], p["y1"]), (0.0, 1.0)),
             ((p["x1"], p["y0"]), (p["x0"], p["y0"]), (0.0, -1.0)),
             ((p["x0"], p["y0"]), (p["x0"], p["y1"]), (-1.0, 0.0))]
    rims = []
    for a, b, out in sides:
        tops = rock_shelf(builder, a, b, out, 16.0, floor, ground)
        rims.append((a, b, out, tops))
    for (ax, ay), (bx, by) in (((p["x0"] - 16.0, p["y0"] - 16.0), (p["x0"], p["y0"])),
                               ((p["x0"] - 16.0, p["y1"]), (p["x0"], p["y1"] + 16.0))):
        z = max(ground(ax, ay), ground(bx, by), ground((ax + bx) / 2, (ay + by) / 2)) + 0.15
        builder.box((min(ax, bx), min(ay, by), floor - 0.6), (max(ax, bx), max(ay, by), z), "sphinx_rock")
    return builder, rims


def retaining_walls(rims):
    builder = MeshBuilder()
    for a, b, out, tops in rims:
        a = Vector(a)
        b = Vector(b)
        o = Vector(out)
        count = len(tops) - 1
        for k in range(count):
            p0 = a + (b - a) * k / count + o * 1.2
            p1 = a + (b - a) * (k + 1) / count + o * 1.2
            z = min(tops[k], tops[k + 1])
            outline = [(p0.x, p0.y), (p1.x, p1.y), (p1.x + o.x * 1.3, p1.y + o.y * 1.3),
                       (p0.x + o.x * 1.3, p0.y + o.y * 1.3)]
            if o.x * (p1.y - p0.y) - o.y * (p1.x - p0.x) > 0:
                outline = list(reversed(outline))
            builder.prism(outline, z - 0.6, z + 0.55, "limestone", bottom=False)
            builder.prism(outline, z + 0.55, z + 1.9, "mudbrick", bottom=False)
    return builder


def stairs_and_terrace(ground):
    rng = random.Random(71)
    builder = MeshBuilder()
    s = plan.SPHINX
    p = plan.PIT
    st = plan.STAIR
    floor = s["floor"]
    top = plan.TERRACE["top"]
    half = st["width"] / 2
    cy = s["y"]
    x = p["x1"]
    warm = (1.0, 0.95, 0.86)
    first = len(builder.polygons)
    builder.box((p["x0"] + 1.0, p["y0"] + 1.0, floor - 0.6), (p["x1"], p["y1"] - 1.0, floor + 0.12), "paving")
    builder.tint(first, warm)
    z = floor + 0.12
    for k in range(st["lower"]):
        z += st["rise"]
        step(builder, x, cy, half, floor, z, st["tread"])
        side_walls(builder, x, x + st["tread"], cy, half, floor, z)
        x += st["tread"]
    first = len(builder.polygons)
    builder.box((x, cy - half, floor - 0.6), (x + st["landing"], cy + half, z), "paving")
    builder.tint(first, warm)
    side_walls(builder, x, x + st["landing"], cy, half, floor, z)
    x += st["landing"]
    rise = (top - z) / st["upper"]
    for k in range(st["upper"]):
        z += rise
        step(builder, x, cy, half, floor, z, st["tread"])
        side_walls(builder, x, x + st["tread"], cy, half, floor, min(z, top - 0.2))
        x += st["tread"]
    stair_end = x
    first = len(builder.polygons)
    builder.box((x, cy - half - 4.0, floor - 0.6), (x + 12.0, cy + half + 4.0, top + 0.02), "paving")
    builder.tint(first, warm)
    for side in (-1, 1):
        fill_surface(builder, rng, p["x1"] + 1.0, plan.STAIR_END + 14.0, cy, side, half + 1.6, plan.FILL_REACH)
        dy = half + 1.6
        while dy < plan.FILL_REACH - 0.01:
            y0, y1 = cy + side * dy, cy + side * (dy + 1.0)
            h = float(plan.stair_fill(p["x1"] + 1.0, cy + side * (dy + 0.5))) + 0.5
            lo, hi = min(y0, y1), max(y0, y1)
            builder.box((p["x1"] - 0.3, lo, floor - 0.6), (p["x1"] + 1.2, hi, floor + 1.2), "limestone")
            builder.box((p["x1"] - 0.3, lo, floor + 1.2), (p["x1"] + 1.2, hi, h - 0.18), "mudbrick")
            builder.box((p["x1"] - 0.42, lo, h - 0.18), (p["x1"] + 1.3, hi, h), "limestone")
            dy += 1.0
    for y0, y1 in ((plan.TERRACE["y0"], cy - plan.FILL_REACH), (cy + plan.FILL_REACH, plan.TERRACE["y1"])):
        builder.box((p["x1"] - 0.3, y0, floor - 0.6), (p["x1"] + 14.5, y1, floor + 1.2), "limestone")
        builder.box((p["x1"] - 0.3, y0, floor + 1.2), (p["x1"] + 14.5, y1, top - 0.22), "mudbrick")
        builder.box((p["x1"] - 0.42, y0, top - 0.22), (p["x1"] + 14.5, y1, top - 0.04), "limestone")
        builder.box((p["x1"] - 0.42, y0, top - 0.04), (p["x1"] + 0.5, y1, top + 0.7), "limestone")
    drifts = ((p["x0"] + 3.0, p["y0"] + 3.0, 6.0, 3.0), (p["x0"] + 3.0, p["y1"] - 3.0, 6.0, 3.0),
              (p["x0"] + 2.5, cy, 2.5, 9.0), (p["x1"] - 4.0, p["y0"] + 2.5, 5.0, 2.2),
              (p["x1"] - 4.0, p["y1"] - 2.5, 5.0, 2.2), (s["x"] - 20.0, p["y0"] + 2.0, 9.0, 2.0),
              (s["x"] + 5.0, p["y1"] - 2.0, 10.0, 2.0))
    for dx, dy, ax, ay in drifts:
        ellipsoid(builder, (dx, dy, floor + 0.1), (ax, ay, rng.uniform(0.45, 0.9)), SAND, 10, 4)
    return builder, stair_end


def side_walls(builder, x0, x1, cy, half, floor, z):
    for side in (-1, 1):
        a, b = cy + side * half, cy + side * (half + 1.6)
        lo, hi = min(a, b), max(a, b)
        builder.box((x0, lo, floor - 0.6), (x1, hi, z + 0.25), "limestone")
        builder.box((x0, lo, z + 0.25), (x1, hi, z + 0.85), "mudbrick")
        builder.box((x0 - 0.01, lo - 0.08, z + 0.85), (x1 + 0.01, hi + 0.08, z + 1.0), "limestone")


def fill_surface(builder, rng, x0, x1, cy, side, d0, d1):
    xs = np.arange(x0, x1 + 0.01, 1.0)
    ds = np.arange(d0, d1 + 0.01, 1.0)
    rows = []
    for x in xs:
        row = []
        for d in ds:
            y = cy + side * d
            edge = min(d - d0, d1 - d, x - x0, x1 - x)
            jitter = rng.uniform(-0.04, 0.04) if edge > 0.5 else 0.0
            row.append(Vector((x, y, float(plan.stair_fill(x, y)) + 0.08 + jitter)))
        rows.append(row)
    first = len(builder.polygons)
    builder.surface(rows, MATTE, smooth=True, facing=(0.0, 0.0, 1.0))
    for index in range(first, len(builder.polygons)):
        builder.polygon_colors[index] = SAND
    for k in range(int((x1 - x0) * (d1 - d0) / 90)):
        x = rng.uniform(x0 + 1.0, x1 - 1.0)
        d = rng.uniform(d0 + 1.0, d1 - 1.0)
        y = cy + side * d
        size = rng.uniform(0.15, 0.45)
        shade = rng.uniform(0.9, 1.0)
        ellipsoid(builder, (x, y, float(plan.stair_fill(x, y)) + 0.02), (size * 1.4, size, size * 0.55),
                  (RUBBLE[0] * shade, RUBBLE[1] * shade, RUBBLE[2] * shade), 6, 3, "limestone")


def step(builder, x, cy, half, floor, z, tread):
    first = len(builder.polygons)
    builder.box((x, cy - half, floor - 0.6), (x + tread, cy + half, z), "limestone")
    shade = 1.0 if int(round(x / tread)) % 2 else 0.95
    for index in range(first, len(builder.polygons)):
        corners = [Vector(builder.positions[i]) for i in builder.polygons[index]]
        flat = max(c.z for c in corners) - min(c.z for c in corners) < 1e-3
        builder.polygon_colors[index] = (shade, shade * 0.96, shade * 0.88) if flat else (0.55, 0.48, 0.40)
    first = len(builder.polygons)
    builder.box((x - 0.03, cy - half, z - 0.06), (x + 0.02, cy + half, z - 0.03), MATTE, top=False)
    builder.tint(first, (0.30, 0.26, 0.21))


def altar():
    builder = MeshBuilder()
    builder.box((-0.75, -0.75, 0.0), (0.75, 0.75, 0.25), "limestone")
    builder.box((-0.6, -0.6, 0.25), (0.6, 0.6, 1.0), "plaster")
    builder.box((-0.7, -0.7, 1.0), (0.7, 0.7, 1.12), "limestone")
    for sx in (-1, 1):
        for sy in (-1, 1):
            builder.box((sx * 0.62 - 0.08, sy * 0.62 - 0.08, 1.12), (sx * 0.62 + 0.08, sy * 0.62 + 0.08, 1.3),
                        "limestone")
    ellipsoid(builder, (0.0, 0.0, 1.16), (0.3, 0.3, 0.06), (0.2, 0.16, 0.12), 8, 2)
    first = len(builder.polygons)
    builder.box((-0.61, -0.61, 0.6), (0.61, 0.61, 0.7), MATTE)
    builder.tint(first, (0.72, 0.18, 0.12))
    return builder


def stele(width, height, thickness, material, rounded=True, base=True):
    builder = MeshBuilder()
    if base:
        builder.box((-width * 0.6, -thickness * 1.2, 0.0), (width * 0.6, thickness * 1.2, 0.35), "limestone")
    z0 = 0.35 if base else 0.0
    shaft = height - (width / 2 if rounded else 0.0)
    outline = [(-width / 2, z0), (width / 2, z0), (width / 2, z0 + shaft)]
    if rounded:
        for k in range(1, 8):
            angle = math.pi * k / 8
            outline.append((width / 2 * math.cos(angle), z0 + shaft + width / 2 * math.sin(angle)))
    outline.append((-width / 2, z0 + shaft))
    front = [(x, -thickness / 2, z) for x, z in outline]
    back = [(x, thickness / 2, z) for x, z in reversed(outline)]
    tone = (0.62, 0.62, 0.62) if material == "granite_glyphs" else None
    builder.face(builder.points(front), material, uvs=[(x / width * 1.0 + 0.5, (z - z0) / height) for x, _, z in front],
                 color=tone)
    builder.face(builder.points(back), material, uvs=[(0.5 - x / width, (z - z0) / height) for x, _, z in back],
                 color=tone)
    count = len(outline)
    for k in range(count):
        a, b = outline[k], outline[(k + 1) % count]
        quad = [(a[0], -thickness / 2, a[1]), (a[0], thickness / 2, a[1]), (b[0], thickness / 2, b[1]),
                (b[0], -thickness / 2, b[1])]
        builder.polygon(quad, "limestone" if material != "granite_glyphs" else "casing_granite",
                        color=(0.66, 0.60, 0.58) if material == "granite_glyphs" else None)
    return builder


def dream_stele():
    builder = stele(2.2, 3.6, 0.7, "granite_glyphs")
    front = -0.38
    lunette = 0.35 + 3.6 - 1.1
    relief = (0.40, 0.27, 0.24)
    ellipsoid(builder, (0.0, front, lunette + 0.55), (0.16, 0.06, 0.16), (0.70, 0.46, 0.22), 10, 4, "bronze_gilt")
    for side in (-1, 1):
        wing = [Vector((side * 0.14, front, lunette + 0.62)), Vector((side * 0.85, front, lunette + 0.66)),
                Vector((side * 0.8, front, lunette + 0.5)), Vector((side * 0.14, front, lunette + 0.48))]
        builder.oriented(wing, Vector((0.0, -1.0, 0.0)), MATTE)
        builder.polygon_colors[-1] = relief
        ellipsoid(builder, (side * 0.48, front - 0.02, lunette + 0.08), (0.26, 0.05, 0.09), relief, 8, 3)
        ellipsoid(builder, (side * 0.24, front - 0.02, lunette + 0.2), (0.06, 0.05, 0.1), relief, 6, 3)
        ellipsoid(builder, (side * 0.72, front - 0.02, lunette + 0.03), (0.08, 0.05, 0.05), relief, 6, 3)
    return builder


def dream_chapel(x, y, floor):
    builder = MeshBuilder()
    for side in (-1, 1):
        wy = y + side * 3.4
        builder.box((x - 2.6, wy - 0.45, floor - 0.2), (x + 3.2, wy + 0.45, floor + 1.55), "mudbrick")
        builder.box((x - 2.7, wy - 0.55, floor + 1.55), (x + 3.3, wy + 0.55, floor + 1.7), "limestone")
        builder.box((x + 3.2, wy - 0.5, floor - 0.2), (x + 3.7, wy + 0.5, floor + 1.25), "mudbrick")
    builder.box((x - 2.6, y - 2.95, floor + 0.08), (x + 3.2, y + 2.95, floor + 0.16), "paving")
    return builder



def isis_temple(ground):
    rng = random.Random(53)
    builder = MeshBuilder()
    c = plan.ISIS
    x0 = 564.4
    z = ground(c["x"], c["y"])
    builder.box((x0, c["y"] - 13.0, z - 0.5), (x0 + 22.0, c["y"] + 13.0, z + 0.2), "paving")
    for (ax, ay), (bx, by) in (((x0, c["y"] - 12.0), (x0 + 20.0, c["y"] - 12.0)),
                               ((x0, c["y"] + 12.0), (x0 + 20.0, c["y"] + 12.0)),
                               ((x0 + 8.0, c["y"] - 12.0), (x0 + 8.0, c["y"] + 12.0))):
        ruined_wall(builder, (ax, ay), (bx, by), 1.4, lambda x, y: z + 0.2, (2.6, 3.6), "plaster", rng)
    builder.box((x0, c["y"] - 6.0, z + 0.2), (x0 + 7.6, c["y"] + 6.0, z + 4.2), "limestone")
    builder.box((x0 + 7.6, c["y"] - 2.0, z + 0.2), (x0 + 7.9, c["y"] + 2.0, z + 3.0), "shadow_void")
    builder.box((x0 - 0.2, c["y"] - 6.4, z + 4.2), (x0 + 8.0, c["y"] + 6.4, z + 4.6), "limestone")
    first = len(builder.polygons)
    builder.box((x0 + 7.62, c["y"] - 6.0, z + 3.4), (x0 + 7.7, c["y"] + 6.0, z + 3.9), MATTE)
    builder.tint(first, (0.16, 0.38, 0.62))
    for side in (-1, 1):
        tower = MeshBuilder()
        frustum(tower, (1.3, 2.4), (1.0, 2.1), 0.0, 5.2, "limestone", 1, 1, True)
        builder.merge(tower, Matrix.Translation((x0 + 20.0, c["y"] + side * 4.6, z + 0.2)))
    first = len(builder.polygons)
    builder.box((x0 + 18.8, c["y"] - 7.0, z + 4.9), (x0 + 21.2, c["y"] + 7.0, z + 5.2), MATTE)
    builder.tint(first, (0.78, 0.22, 0.14))
    for y in (-2.6, 2.6):
        tube(builder, [(x0 + 13.0, c["y"] + y, z + 0.2), (x0 + 13.0, c["y"] + y, z + 4.4)], [0.42, 0.36],
             (0.96, 0.92, 0.84), 10)
        ellipsoid(builder, (x0 + 13.0, c["y"] + y, z + 4.5), (0.6, 0.6, 0.35), (0.40, 0.62, 0.42), 10, 4)
    builder.box((x0 + 10.0, c["y"] - 0.7, z + 0.2), (x0 + 11.2, c["y"] + 0.7, z + 1.0), "limestone")
    return builder


def nile_x(y):
    ys = [p[1] for p in plan.NILE]
    xs = [p[0] for p in plan.NILE]
    return float(np.interp(y, ys, xs))


def cylinder(builder, x, y, z0, z1, radius, material, color, sides=8):
    ring = [(x + radius * math.cos(TAU * k / sides), y + radius * math.sin(TAU * k / sides)) for k in range(sides)]
    first = len(builder.polygons)
    builder.prism(ring, z0, z1, material, bottom=False)
    builder.tint(first, color)


def far_landscape(ground):
    rng = random.Random(97)
    builder = MeshBuilder()
    water = plan.LEVELS["water"]
    mud = (0.46, 0.40, 0.26)
    grove = (0.17, 0.30, 0.12)
    for y in np.arange(-24000.0, 14000.0, 500.0):
        x0 = nile_x(y) + plan.NILE_HALF + 30.0
        x1 = nile_x(y + 500.0) + plan.NILE_HALF + 30.0
        builder.polygon([Vector((x0, y, water + 0.9)), Vector((x0 + 160.0, y, water + 0.9)),
                         Vector((x1 + 160.0, y + 500.0, water + 0.9)), Vector((x1, y + 500.0, water + 0.9))], MATTE,
                        color=mud)
        builder.oriented([Vector((x0 - 2.0, y, water - 0.5)), Vector((x1 - 2.0, y + 500.0, water - 0.5)),
                          Vector((x1, y + 500.0, water + 0.9)), Vector((x0, y, water + 0.9))],
                         Vector((-1.0, 0.0, 0.0)), MATTE)
        builder.polygon_colors[-1] = mud
        if rng.random() < 0.3:
            continue
        for k in range(4):
            t0, t1 = k / 4, (k + 1) / 4
            ya, yb = y + 500.0 * t0, y + 500.0 * t1
            xa, xb = x0 + (x1 - x0) * t0 + 70.0, x0 + (x1 - x0) * t1 + 70.0
            ha, hb = rng.uniform(9.0, 15.0), rng.uniform(9.0, 15.0)
            builder.oriented([Vector((xa, ya, water + 0.9)), Vector((xb, yb, water + 0.9)),
                              Vector((xb, yb, water + 0.9 + hb)), Vector((xa, ya, water + 0.9 + ha))],
                             Vector((-1.0, 0.0, 0.0)), MATTE)
            shade = rng.uniform(0.85, 1.1)
            builder.polygon_colors[-1] = tuple(c * shade for c in grove)
    cliff = []
    for y in np.arange(-17000.0, 9001.0, 400.0):
        x = 13800.0 + 900.0 * math.sin(y / 5200.0) + rng.uniform(-150.0, 150.0)
        if y > 2000.0:
            x -= (y - 2000.0) * 0.12
        top = rng.uniform(150.0, 180.0) - max(0.0, -y - 9000.0) * 0.006
        cliff.append((x, y, top))
    strata = [(0.90, 0.78, 0.62), (0.84, 0.70, 0.54), (0.93, 0.83, 0.68)]
    for (xa, ya, ta), (xb, yb, tb) in zip(cliff[:-1], cliff[1:]):
        levels = [28.0, 0.45, 0.7, 0.88, 1.0]
        for k in range(4):
            za0 = 28.0 + (ta - 28.0) * (levels[k] if k else 0.0)
            za1 = 28.0 + (ta - 28.0) * levels[k + 1]
            zb0 = 28.0 + (tb - 28.0) * (levels[k] if k else 0.0)
            zb1 = 28.0 + (tb - 28.0) * levels[k + 1]
            inset = 40.0 * (1 - levels[k + 1])
            builder.oriented([Vector((xa + 60.0 - inset * 1.5, ya, za0)), Vector((xb + 60.0 - inset * 1.5, yb, zb0)),
                              Vector((xb + 60.0 - inset, yb, zb1)), Vector((xa + 60.0 - inset, ya, za1))],
                             Vector((-1.0, 0.0, 0.0)), MATTE)
            builder.polygon_colors[-1] = strata[k % 3]
        builder.polygon([Vector((xa + 60.0, ya, ta)), Vector((xa + 1600.0, ya, ta - 30.0)),
                         Vector((xb + 1600.0, yb, tb - 30.0)), Vector((xb + 60.0, yb, tb))], MATTE,
                        color=(0.88, 0.76, 0.58))
    bx, by = 9560.0, 3320.0
    builder.polygon([Vector((bx - 260.0, by - 200.0, water + 1.2)), Vector((bx + 260.0, by - 200.0, water + 1.2)),
                     Vector((bx + 260.0, by + 200.0, water + 1.2)), Vector((bx - 260.0, by + 200.0, water + 1.2))],
                    MATTE, color=mud)
    wall = (0.80, 0.66, 0.52)
    for (ax, ay), (cx, cy) in (((-150.0, -90.0), (150.0, -80.0)), ((150.0, -80.0), (150.0, 90.0)),
                               ((150.0, 90.0), (-150.0, 90.0)), ((-150.0, 90.0), (-150.0, -90.0))):
        first = len(builder.polygons)
        x0, x1 = sorted((bx + ax, bx + cx))
        y0, y1 = sorted((by + ay, by + cy))
        builder.box((x0 - 3.0, y0 - 3.0, water), (x1 + 3.0, y1 + 3.0, water + 11.0), "mudbrick", top=True,
                    bottom=False)
        builder.tint(first, wall)
        for t in (0.0, 0.5):
            cylinder(builder, bx + ax + (cx - ax) * t, by + ay + (cy - ay) * t, water, water + 15.0, 9.0,
                     "mudbrick", wall)
    mx, my = nile_x(-14500.0) + 4800.0, -14500.0
    mound = []
    for k in range(16):
        angle = TAU * k / 16
        mound.append((mx + 900.0 * math.cos(angle), my + 650.0 * math.sin(angle)))
    builder.prism(mound, water - 1.0, water + 5.0, MATTE, bottom=False)
    builder.tint(len(builder.polygons) - 17, mud)
    first = len(builder.polygons)
    builder.box((mx - 300.0, my - 220.0, water + 5.0), (mx + 300.0, my + 220.0, water + 13.0), "mudbrick",
                bottom=False)
    builder.tint(first, wall)
    temple = (0.94, 0.86, 0.72)
    for side in (-1, 1):
        tower = MeshBuilder()
        frustum(tower, (9.0, 22.0), (6.5, 18.0), 0.0, 26.0, "limestone", 1, 1, True, color=temple)
        builder.merge(tower, Matrix.Translation((mx + 300.0, my + side * 26.0, water + 5.0)))
    first = len(builder.polygons)
    builder.box((mx + 160.0, my - 60.0, water + 5.0), (mx + 290.0, my + 60.0, water + 19.0), "limestone",
                bottom=False)
    builder.tint(first, temple)
    for k in range(40):
        hx, hy = mx + rng.uniform(-800.0, 700.0), my + rng.uniform(-520.0, 520.0)
        if abs(hx - mx) < 320.0 and abs(hy - my) < 240.0:
            continue
        if ((hx - mx) / 900.0) ** 2 + ((hy - my) / 650.0) ** 2 > 0.8:
            continue
        size = rng.uniform(12.0, 30.0)
        first = len(builder.polygons)
        builder.box((hx - size, hy - size * 0.7, water + 5.0), (hx + size, hy + size * 0.7,
                                                                  water + 5.0 + rng.uniform(4.0, 9.0)), "mudbrick",
                    bottom=False)
        builder.tint(first, (0.78, 0.68, 0.54) if k % 3 else (0.92, 0.88, 0.80))
    return builder
