import math
import random

import bpy
from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .nimes_figures import drape, ellipsoid, tube
from .orders import roman_font

STONE = "stone"
TILES = "terracotta_tiles"
VOID = "shadow_void"
WALLS = [("plaster", (0.98, 0.96, 0.92)), ("plaster", (0.97, 0.92, 0.82)), ("plaster", (0.95, 0.84, 0.64)),
         ("plaster", (0.96, 0.86, 0.80)), ("plaster", (0.93, 0.92, 0.89)), ("plaster", (0.90, 0.72, 0.52)),
         ("plaster", (0.99, 0.97, 0.94))]
DADOS = [(0.62, 0.16, 0.11), (0.70, 0.22, 0.14), (0.16, 0.14, 0.13), (0.78, 0.56, 0.26), (0.55, 0.20, 0.16),
         (0.74, 0.66, 0.56)]
WOODS = [(0.36, 0.25, 0.16), (0.42, 0.30, 0.20), (0.30, 0.22, 0.15), (0.46, 0.34, 0.22), (0.34, 0.28, 0.22)]
PROGRAMMES = ["C IVLIVM POLYBIVM AED OVF", "CN HELVIVM SABINVM AED OVF", "M HOLCONIVM PRISCVM IIVIR I D OVF",
              "A VETTIVM FIRMVM AED OVF", "L CEIVM SECVNDVM IIVIR OVF", "M CERRINIVM VATIAM AED OVF",
              "M EPIDIVM SABINVM IIVIR I D OVF", "CN HELVIVM SABINVM AED D R P OVF", "C CVSPIVM PANSAM AED OVF",
              "L POPIDIVM SECVNDVM AED OVF"]
RED_PAINT = (0.66, 0.10, 0.07)


def tinted(builder, color, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, color)


def quad(builder, corners, normal, material, color=None):
    first = len(builder.polygons)
    builder.oriented(corners, normal, material)
    if color is not None:
        builder.tint(first, color)


def front_panel(builder, x0, x1, z0, z1, y, material, color=None):
    quad(builder, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], (0, -1, 0), material, color)


def plank_shutter(builder, x0, x1, z0, z1, y, wood, rng, detail):
    if not detail:
        front_panel(builder, x0, x1, z0, z1, y, MATTE, wood)
        return
    count = max(int((x1 - x0) / 0.32), 2)
    step = (x1 - x0) / count
    for index in range(count):
        shade = tuple(c * rng.uniform(0.82, 1.08) for c in wood)
        front_panel(builder, x0 + index * step + 0.012, x0 + (index + 1) * step - 0.012, z0, z1, y, MATTE, shade)
    front_panel(builder, x0, x1, z0, z1, y + 0.01, MATTE, tuple(c * 0.4 for c in wood))
    for z in (z0 + 0.25, z1 - 0.3):
        tinted(builder, tuple(c * 0.75 for c in wood), lambda z=z: builder.box((x0, y - 0.05, z), (x1, y, z + 0.09),
                                                                              MATTE))


def shop_bay(builder, x, width, height, wood, rng, detail, state):
    x0, x1 = x - width / 2, x + width / 2
    tinted(builder, (0.30, 0.29, 0.27), lambda: builder.box((x0 - 0.05, -0.12, -0.02), (x1 + 0.05, 0.02, 0.06),
                                                            STONE, bottom=False))
    tinted(builder, tuple(c * 0.7 for c in wood), lambda: builder.box((x0 - 0.15, -0.1, height),
                                                                      (x1 + 0.15, 0.02, height + 0.28), MATTE))
    if state == "open":
        front_panel(builder, x0, x1, 0.0, height, -0.015, MATTE, (0.16, 0.12, 0.09))
        return
    if state == "half":
        cut = x0 + width * rng.uniform(0.45, 0.7)
        plank_shutter(builder, x0, cut, 0.06, height, -0.04, wood, rng, detail)
        front_panel(builder, cut, x1, 0.0, height, -0.015, MATTE, (0.15, 0.11, 0.08))
        return
    plank_shutter(builder, x0, x1, 0.06, height, -0.04, wood, rng, detail)


def doorway(builder, x, width, height, wood, wall):
    x0, x1 = x - width / 2, x + width / 2
    front_panel(builder, x0, x, 0.0, height, -0.03, MATTE, wood)
    front_panel(builder, x, x1, 0.0, height, -0.03, MATTE, tuple(c * 0.85 for c in wood))
    for side in (-1, 1):
        px = x + side * (width / 2 + 0.22)
        tinted(builder, (0.94, 0.92, 0.86), lambda px=px: builder.box((px - 0.22, -0.16, 0.0), (px + 0.22, 0.02, height),
                                                                      "plaster", bottom=False))
        tinted(builder, (0.90, 0.88, 0.82), lambda px=px: builder.box((px - 0.3, -0.22, height), (px + 0.3, 0.02,
                                                                                                  height + 0.32),
                                                                      "plaster", bottom=False))
    tinted(builder, (0.30, 0.29, 0.27), lambda: builder.box((x0, -0.2, -0.02), (x1, 0.18, 0.08), STONE, bottom=False))


def window(builder, x, z, wood, rng, detail):
    front_panel(builder, x - 0.28, x + 0.28, z, z + 0.62, -0.005, VOID)
    if detail and rng.random() < 0.6:
        front_panel(builder, x - 0.56, x - 0.28, z, z + 0.62, -0.012, MATTE, wood)
        front_panel(builder, x + 0.28, x + 0.56, z, z + 0.62, -0.012, MATTE, wood)
    elif detail:
        front_panel(builder, x - 0.28, x + 0.28, z, z + 0.62, -0.012, MATTE, tuple(c * 0.9 for c in wood))


def gable_roof(builder, x0, x1, depth, height, rise, wall, wall_colour, ends=True):
    top = height + rise
    for y_eave, y_ridge, normal in ((-0.45, depth / 2, (0, -1, 1)), (depth + 0.45, depth / 2, (0, 1, 1))):
        quad(builder, [(x0 - 0.25, y_eave, height - 0.12), (x1 + 0.25, y_eave, height - 0.12), (x1 + 0.25, y_ridge, top),
                       (x0 - 0.25, y_ridge, top)], normal, TILES)
    if ends:
        for x, normal in ((x0, (-1, 0, 0)), (x1, (1, 0, 0))):
            first = len(builder.polygons)
            builder.oriented([(x, 0.0, height), (x, depth, height), (x, depth / 2, top)], normal, wall)
            builder.tint(first, wall_colour)


def lean_roof(builder, x0, x1, depth, height, rise):
    quad(builder, [(x0 - 0.25, -0.55, height - 0.1), (x1 + 0.25, -0.55, height - 0.1), (x1 + 0.25, depth + 0.3,
                                                                                         height + rise),
                   (x0 - 0.25, depth + 0.3, height + rise)], (0, -1, 1), TILES)


def compluviate_roof(builder, x0, x1, y0, y1, height, opening=0.3):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    ox, oy = hx * opening, hy * opening
    inner = height - 0.7
    outer = [(x0 - 0.3, y0 - 0.45), (x1 + 0.3, y0 - 0.45), (x1 + 0.3, y1 + 0.2), (x0 - 0.3, y1 + 0.2)]
    hole = [(cx - ox, cy - oy), (cx + ox, cy - oy), (cx + ox, cy + oy), (cx - ox, cy + oy)]
    for index in range(4):
        a, b = outer[index], outer[(index + 1) % 4]
        c, d = hole[(index + 1) % 4], hole[index]
        quad(builder, [(a[0], a[1], height + 0.3), (b[0], b[1], height + 0.3), (c[0], c[1], inner), (d[0], d[1], inner)],
             (0, 0, 1), TILES)
    builder.box((cx - ox, cy - oy, inner - 4.0), (cx + ox, cy + oy, inner), VOID, top=False)
    tinted(builder, (0.82, 0.80, 0.74), lambda: builder.polygon(
        [(cx - ox * 0.7, cy - oy * 0.7, inner - 3.9), (cx + ox * 0.7, cy - oy * 0.7, inner - 3.9),
         (cx + ox * 0.7, cy + oy * 0.7, inner - 3.9), (cx - ox * 0.7, cy + oy * 0.7, inner - 3.9)], MATTE))


def unit(width, depth, height, kind, seed, detail=True, shutters="closed"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    x0, x1 = -width / 2, width / 2
    wall, wall_colour = WALLS[rng.randrange(len(WALLS))]
    wood = WOODS[rng.randrange(len(WOODS))]
    tinted(builder, wall_colour, lambda: builder.box((x0, 0.0, -2.5), (x1, depth, height), wall, bottom=False,
                                                     top=False))
    dado = DADOS[rng.randrange(len(DADOS))]
    if rng.random() < 0.75:
        front_panel(builder, x0, x1, 0.0, rng.choice((0.9, 1.1, 1.3)), -0.01, "plaster", dado)
    tinted(builder, (0.42, 0.40, 0.37), lambda: builder.box((x0, -0.06, -0.4), (x1, 0.0, 0.1), STONE, bottom=False))
    upper = height > 5.6
    if kind == "shop":
        bays = max(1, min(3, int(width / 3.6)))
        step = width / bays
        for index in range(bays):
            state = shutters if shutters != "mixed" else rng.choice(("closed", "closed", "half", "open"))
            shop_bay(builder, x0 + step * (index + 0.5), min(step - 0.7, 3.1), 2.7, wood, rng, detail, state)
    elif kind == "house":
        door_x = rng.uniform(-0.15, 0.15) * width
        doorway(builder, door_x, 1.9, 3.3, wood, wall)
        for side in (-1, 1):
            room = (width / 2 - 1.6) if side > 0 else (width / 2 - 1.6)
            if room > 3.4:
                centre = door_x + side * (1.6 + room / 2)
                if abs(centre) + 1.5 < width / 2:
                    shop_bay(builder, centre, min(room - 0.8, 3.0), 2.6, wood, rng, detail,
                             shutters if shutters != "mixed" else rng.choice(("closed", "half")))
    else:
        front_panel(builder, -0.55, 0.55, 0.0, 2.4, -0.03, MATTE, wood)
    if upper:
        count = max(1, int(width / 4.0))
        for index in range(count):
            window(builder, x0 + width * (index + 0.5) / count, height - 1.9, wood, rng, detail)
    elif kind != "wall":
        for index in range(max(1, int(width / 6.0))):
            front_panel(builder, x0 + 1.0 + index * 6.0, x0 + 1.5 + index * 6.0, height - 1.2, height - 0.8, -0.005,
                        VOID)
    roof = "gable"
    if kind == "house" and width >= 10.0 and depth >= 12.0:
        roof = "atrium"
    elif kind == "shop" and rng.random() < 0.4:
        roof = "lean"
    elif kind == "wall":
        roof = "none"
    if roof == "atrium":
        front = min(depth * 0.62, width * 1.1)
        compluviate_roof(builder, x0, x1, 0.0, front, height, 0.28)
        if depth - front > 2.0:
            builder.merge(back_roof(x0, x1, front, depth, height + 0.4, wall, wall_colour))
    elif roof == "gable":
        gable_roof(builder, x0, x1, depth, height, min(depth * 0.18, 2.4), wall, wall_colour)
    elif roof == "lean":
        lean_roof(builder, x0, x1, depth, height, depth * 0.22)
        quad(builder, [(x0, depth, height), (x1, depth, height), (x1, depth, height + depth * 0.22),
                       (x0, depth, height + depth * 0.22)], (0, 1, 0), wall, wall_colour)
    else:
        tinted(builder, (0.85, 0.82, 0.76), lambda: builder.box((x0 - 0.05, -0.05, height), (x1 + 0.05, 0.4,
                                                                                            height + 0.15),
                                                                STONE, bottom=False))
    if detail and upper and kind == "shop" and rng.random() < 0.25:
        balcony(builder, x0 + 0.6, x1 - 0.6, height - 2.6, wood)
    return builder


def back_roof(x0, x1, y0, y1, height, wall, wall_colour):
    builder = MeshBuilder()
    rise = min((x1 - x0) * 0.16, 2.0)
    mid = (x0 + x1) / 2
    for xa, normal in ((x0 - 0.3, (-1, 0, 1)), (x1 + 0.3, (1, 0, 1))):
        quad(builder, [(xa, y0, height - 0.1), (xa, y1 + 0.4, height - 0.1), (mid, y1 + 0.4, height + rise),
                       (mid, y0, height + rise)], normal, TILES)
    first = len(builder.polygons)
    builder.oriented([(x0, y1, height - 0.4), (x1, y1, height - 0.4), (mid, y1, height + rise)], (0, 1, 0), wall)
    builder.oriented([(x0, y0, height - 0.4), (x1, y0, height - 0.4), (mid, y0, height + rise)], (0, -1, 0), wall)
    builder.tint(first, wall_colour)
    return builder


def balcony(builder, x0, x1, z, wood):
    tinted(builder, wood, lambda: builder.box((x0, -1.0, z), (x1, 0.0, z + 0.18), MATTE))
    quad(builder, [(x0, -1.0, z + 0.18), (x1, -1.0, z + 0.18), (x1, -1.0, z + 1.0), (x0, -1.0, z + 1.0)], (0, -1, 0),
         MATTE, tuple(c * 0.9 for c in wood))
    quad(builder, [(x0, -1.0, z + 0.18), (x1, -1.0, z + 0.18), (x1, -1.0, z + 1.0), (x0, -1.0, z + 1.0)], (0, 1, 0),
         MATTE, tuple(c * 0.7 for c in wood))
    quad(builder, [(x0 - 0.2, -1.3, z + 2.2), (x1 + 0.2, -1.3, z + 2.2), (x1 + 0.2, 0.0, z + 2.6),
                   (x0 - 0.2, 0.0, z + 2.6)], (0, -1, 1), TILES)
    for x in (x0 + 0.3, (x0 + x1) / 2, x1 - 0.3):
        first = len(builder.polygons)
        builder.box((x - 0.07, -1.0, z - 0.16), (x + 0.07, 0.0, z), MATTE)
        builder.tint(first, tuple(c * 0.75 for c in wood))


def flat_text(text, letter_height, color=RED_PAINT):
    curve = bpy.data.curves.new("programme_text", type="FONT")
    curve.font = roman_font()
    curve.body = text
    curve.size = letter_height * 1.45
    curve.resolution_u = 1
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.fill_mode = "FRONT"
    holder = bpy.data.objects.new("programme_text", curve)
    bpy.context.scene.collection.objects.link(holder)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(holder.evaluated_get(depsgraph))
    builder = MeshBuilder()
    for vertex in mesh.vertices:
        builder.point((vertex.co.x, 0.0, vertex.co.y))
    for polygon in mesh.polygons:
        builder.face(list(polygon.vertices), MATTE, color=color)
    width = max((v.co.x for v in mesh.vertices), default=0.0) - min((v.co.x for v in mesh.vertices), default=0.0)
    bpy.data.objects.remove(holder)
    bpy.data.curves.remove(curve)
    bpy.data.meshes.remove(mesh)
    for index, indices in enumerate(builder.polygons):
        corners = [Vector(builder.positions[i]) for i in indices]
        normal = (corners[1] - corners[0]).cross(corners[2] - corners[0])
        if normal.y > 0:
            builder.polygons[index] = tuple(reversed(indices))
    return builder, width


def programme(text, width_limit, seed):
    rng = random.Random(seed)
    words = text.split()
    split = max(1, len(words) - 1 if len(words) > 3 else len(words))
    lines = [" ".join(words[:split]), " ".join(words[split:])] if split < len(words) else [text]
    builder = MeshBuilder()
    slant = Matrix.Identity(4)
    slant[0][2] = math.tan(math.radians(rng.uniform(2.0, 4.0)))
    condense = Matrix.Diagonal((0.7, 1.0, 1.0, 1.0))
    z = 0.0
    widest = 0.0
    for index, line in enumerate(lines):
        size = 0.32 if index == 0 else 0.22
        text_builder, width = flat_text(line, size)
        scale = min(1.0, width_limit / max(width * 0.7, 1e-3))
        builder.merge(text_builder, Matrix.Translation((rng.uniform(-0.1, 0.1), 0.0, z)) @ slant
                      @ Matrix.Scale(scale * rng.uniform(0.92, 1.08), 4) @ condense)
        widest = max(widest, width * 0.7 * scale)
        z -= size * 1.4 * scale
    old = PROGRAMMES[rng.randrange(len(PROGRAMMES))].split()
    faded = tuple(0.93 * 0.7 + c * 0.3 for c in RED_PAINT)
    ghost, ghost_width = flat_text(" ".join(old[:3]), 0.2, faded)
    ghost_scale = min(1.0, widest / max(ghost_width * 0.7, 1e-3))
    builder.merge(ghost, Matrix.Translation((rng.uniform(-0.3, 0.3), 0.004, z + 0.02)) @ Matrix.Scale(ghost_scale, 4)
                  @ condense)
    half = widest / 2 + 0.25
    quad(builder, [(-half, 0.012, z - 0.2), (half, 0.012, z - 0.2), (half, 0.012, 0.32),
                   (-half, 0.012, 0.32)], (0, -1, 0), "plaster", (0.93, 0.91, 0.86))
    return builder


def street_mesh(street, others, ground, step=2.0):
    points = [Vector(point) for point in street["points"]]
    samples = []
    for a, b in zip(points[:-1], points[1:]):
        length = (b - a).length
        count = max(int(math.ceil(length / step)), 1)
        for k in range(count):
            samples.append(a.lerp(b, k / count))
    samples.append(points[-1])
    half = street["road"] / 2
    walk = street["walk"]
    kerb = street["kerb"]
    builder = MeshBuilder()
    rows = []
    distance = 0.0
    for index, point in enumerate(samples):
        before = samples[max(index - 1, 0)]
        after = samples[min(index + 1, len(samples) - 1)]
        tangent = (after - before).normalized()
        normal = Vector((-tangent.y, tangent.x))
        if index:
            distance += (point - samples[index - 1]).length
        z = ground(point.x, point.y)
        road_on = street["inside"](point)
        sink = 0.0
        walks = []
        for side in (-1, 1):
            q = point + normal * side * (half + walk / 2)
            walks.append(street["inside"](q))
        for other in others:
            if other is street:
                continue
            d_center = other["distance"](point)
            if other["rank"] > street["rank"] and d_center < other["road"] / 2 + 0.3:
                sink = 0.07
            for side_index, side in enumerate((-1, 1)):
                q = point + normal * side * (half + walk / 2)
                d = other["distance"](q)
                if d < other["road"] / 2 + 0.25:
                    walks[side_index] = False
                if other["rank"] > street["rank"] and d < other["road"] / 2 + other["walk"] + 0.15:
                    walks[side_index] = False
        rows.append((point, normal, z, road_on, walks, sink, distance))
    for (p0, n0, z0, r0, w0, s0, d0), (p1, n1, z1, r1, w1, s1, d1) in zip(rows[:-1], rows[1:]):
        if r0 and r1:
            za, zb = z0 - max(s0, s1), z1 - max(s0, s1)
            corners = [p0 - n0 * half, p1 - n1 * half, p1 + n1 * half, p0 + n0 * half]
            heights = [za, zb, zb, za]
            uvs = [(d0, 0.0), (d1, 0.0), (d1, 4.0), (d0, 4.0)]
            indices = builder.points([(c.x, c.y, h) for c, h in zip(corners, heights)])
            builder.face(indices, "basalt", uvs=uvs)
        for side_index, side in enumerate((-1, 1)):
            if not (w0[side_index] and w1[side_index]):
                continue
            inner0, inner1 = p0 + n0 * side * half, p1 + n1 * side * half
            outer0, outer1 = p0 + n0 * side * (half + walk), p1 + n1 * side * (half + walk)
            top0, top1 = z0 + kerb, z1 + kerb
            builder.oriented([(inner0.x, inner0.y, top0), (inner1.x, inner1.y, top1), (outer1.x, outer1.y, top1),
                              (outer0.x, outer0.y, top0)], (0, 0, 1), "sidewalk")
            first = len(builder.polygons)
            builder.oriented([(inner0.x, inner0.y, z0 - 0.1), (inner1.x, inner1.y, z1 - 0.1),
                              (inner1.x, inner1.y, top1), (inner0.x, inner0.y, top0)],
                             (-n0.x * side, -n0.y * side, 0.0), STONE)
            builder.tint(first, (0.55, 0.53, 0.50))
            builder.oriented([(outer0.x, outer0.y, z0 - 0.9), (outer1.x, outer1.y, z1 - 0.9),
                              (outer1.x, outer1.y, top1), (outer0.x, outer0.y, top0)],
                             (n0.x * side, n0.y * side, 0.0), STONE)
    for index, (point, normal, z, road_on, walks, sink, _) in enumerate(rows):
        for side_index, side in enumerate((-1, 1)):
            prev_on = index > 0 and rows[index - 1][4][side_index]
            next_on = index < len(rows) - 1 and rows[index + 1][4][side_index]
            if walks[side_index] and prev_on != next_on:
                inner = point + normal * side * half
                outer = point + normal * side * (half + walk)
                tangent = Vector((normal.y, -normal.x))
                facing = tangent if next_on else -tangent
                first = len(builder.polygons)
                builder.oriented([(inner.x, inner.y, z - 0.1), (outer.x, outer.y, z - 0.1),
                                  (outer.x, outer.y, z + kerb), (inner.x, inner.y, z + kerb)],
                                 (-facing.x, -facing.y, 0.0), STONE)
                builder.tint(first, (0.55, 0.53, 0.50))
    return builder, rows


def project(points, p):
    best = None
    for a, b in zip(points[:-1], points[1:]):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        q = a + ab * t
        d = (p - q).length
        if best is None or d < best[0]:
            best = (d, q, ab.normalized())
    return best


def crossings(specs):
    from mathutils.geometry import intersect_line_line_2d
    streets = [spec for spec in specs if spec["kind"] != "road"]
    found = []
    for index, a in enumerate(streets):
        for b in streets[index + 1:]:
            if (b["box"][2] < a["box"][0] or b["box"][0] > a["box"][2] or b["box"][3] < a["box"][1]
                    or b["box"][1] > a["box"][3]):
                continue
            for a0, a1 in zip(a["points"][:-1], a["points"][1:]):
                ta = (a1 - a0).normalized()
                for b0, b1 in zip(b["points"][:-1], b["points"][1:]):
                    tb = (b1 - b0).normalized()
                    sine = abs(ta.x * tb.y - ta.y * tb.x)
                    if sine < 0.3:
                        continue
                    hit = intersect_line_line_2d(a0 - ta * 2.0, a1 + ta * 2.0, b0 - tb * 2.0, b1 + tb * 2.0)
                    if hit is None:
                        continue
                    hit = Vector(hit)
                    if not (a["inside"](hit) and b["inside"](hit)):
                        continue
                    if any((hit - other[0]).length < 3.0 for other in found):
                        continue
                    found.append((hit, a, b, ta, tb, sine))
    return found


def crossing_patch(builder, crossing, ground, cell=2.5):
    centre, a, b, ta, tb, sine = crossing
    reach_s = (b["half"] + 2.3) / sine
    reach_t = (a["half"] + 2.3) / sine
    count_s = max(2, int(math.ceil(2 * reach_s / cell)))
    count_t = max(2, int(math.ceil(2 * reach_t / cell)))
    orientation = 1 if ta.x * tb.y - ta.y * tb.x > 0 else -1
    grid = []
    uvs = []
    for i in range(count_s + 1):
        s = -reach_s + 2 * reach_s * i / count_s
        row = []
        row_uv = []
        for j in range(count_t + 1):
            t = -reach_t + 2 * reach_t * j / count_t
            p = centre + ta * s + tb * t
            da, qa, _ = project(a["points"], p)
            db, qb, _ = project(b["points"], p)
            za, zb = ground(*qa), ground(*qb)
            first, second = ((da, a, za), (db, b, zb)) if a["rank"] >= b["rank"] else ((db, b, zb), (da, a, za))
            if first[0] <= first[1]["half"] + 0.2:
                z = first[2]
            elif second[0] <= second[1]["half"] + 0.2:
                z = second[2]
            else:
                z = min(za, zb)
            row.append(builder.point((p.x, p.y, z - 0.03)))
            across = t * sine * orientation
            row_uv.append((s, (across + a["road"] / 2) / a["road"] * 4.0))
        grid.append(row)
        uvs.append(row_uv)
    for i in range(count_s):
        for j in range(count_t):
            cells = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if orientation < 0:
                cells = list(reversed(cells))
            builder.face([grid[r][c] for r, c in cells], "basalt", uvs=[uvs[r][c] for r, c in cells])


def crossing_stones(crossing, ground):
    centre, a, b, ta, tb, sine = crossing
    stones = []
    for street, other, tangent in ((a, b, ta), (b, a, tb)):
        offset = (other["road"] / 2 + other["walk"] / 2) / sine
        normal = Vector((-tangent.y, tangent.x))
        for side in (-1, 1):
            position = centre + tangent * side * offset
            if not street["inside"](position) or not other["inside"](position):
                continue
            z = ground(*project(street["points"], position)[1])
            stones.append((position, math.atan2(normal.y, normal.x), z, 3 if street["kind"] == "main" else 2))
    return stones


def stepping_stones(count, spacing, height):
    builder = MeshBuilder()
    for index in range(count):
        x = (index - (count - 1) / 2) * spacing
        first = len(builder.polygons)
        builder.lathe([(0.0, -0.3), (0.42, -0.3), (0.44, height - 0.05), (0.38, height), (0.0, height)], 10, STONE,
                      smooth=False, matrix=Matrix.Translation((x, 0.0, 0.0)) @ Matrix.Diagonal((0.62, 1.0, 1.0, 1.0)))
        builder.tint(first, (0.48, 0.47, 0.45))
    return builder


def street_fountain(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    basalt = (0.42, 0.41, 0.39)
    tinted(builder, basalt, lambda: builder.box((-0.75, -0.55, -0.2), (0.75, 0.55, 0.78), STONE, bottom=False))
    tinted(builder, (0.10, 0.17, 0.18), lambda: builder.polygon(
        [(-0.62, -0.42, 0.66), (0.62, -0.42, 0.66), (0.62, 0.42, 0.66), (-0.62, 0.42, 0.66)], "water"))
    tinted(builder, basalt, lambda: builder.box((-0.3, 0.42, -0.2), (0.3, 0.75, 1.35), STONE, bottom=False))
    face = (0.50, 0.48, 0.44) if rng.random() < 0.5 else (0.62, 0.60, 0.56)
    ellipsoid(builder, (0.0, 0.41, 1.08), (0.16, 0.05, 0.18), face, 8, 5)
    tube(builder, [(0.0, 0.38, 1.0), (0.0, 0.2, 0.92), (0.0, 0.08, 0.7)], [0.02, 0.025, 0.03], (0.75, 0.82, 0.86), 5)
    return builder


def curtain(points, ground, height=8.0, thickness=3.2, step=6.0):
    builder = MeshBuilder()
    samples = []
    closed = points + [points[0]]
    for a, b in zip(closed[:-1], closed[1:]):
        a, b = Vector(a), Vector(b)
        count = max(int((b - a).length / step), 1)
        for k in range(count):
            samples.append(a.lerp(b, k / count))
    rows = []
    count = len(samples)
    for index, point in enumerate(samples):
        tangent = (samples[(index + 1) % count] - samples[index - 1]).normalized()
        normal = Vector((tangent.y, -tangent.x))
        z = ground(point.x, point.y)
        rows.append((point, normal, z))
    for index in range(count):
        p0, n0, z0 = rows[index]
        p1, n1, z1 = rows[(index + 1) % count]
        out0, out1 = p0 + n0 * thickness / 2, p1 + n1 * thickness / 2
        in0, in1 = p0 - n0 * thickness / 2, p1 - n1 * thickness / 2
        builder.oriented([(out0.x, out0.y, z0 - 6.0), (out1.x, out1.y, z1 - 6.0), (out1.x, out1.y, z1 + height),
                          (out0.x, out0.y, z0 + height)], (n0.x, n0.y, 0.0), STONE)
        builder.oriented([(in0.x, in0.y, z0 - 2.0), (in1.x, in1.y, z1 - 2.0), (in1.x, in1.y, z1 + height),
                          (in0.x, in0.y, z0 + height)], (-n0.x, -n0.y, 0.0), STONE)
        builder.oriented([(out0.x, out0.y, z0 + height), (out1.x, out1.y, z1 + height),
                          (in1.x, in1.y, z1 + height), (in0.x, in0.y, z0 + height)], (0, 0, 1), "sidewalk")
        tangent = (p1 - p0)
        length = tangent.length
        tangent.normalize()
        merlons = max(int(length / 2.4), 1)
        for k in range(merlons):
            s0 = (k + 0.15) / merlons
            s1 = (k + 0.65) / merlons
            a = out0.lerp(out1, s0)
            b = out0.lerp(out1, s1)
            za = z0 + (z1 - z0) * s0 + height
            zb = z0 + (z1 - z0) * s1 + height
            inner_a = a - n0 * 0.7
            inner_b = b - n0 * 0.7
            builder.oriented([(a.x, a.y, za), (b.x, b.y, zb), (b.x, b.y, zb + 1.5), (a.x, a.y, za + 1.5)],
                             (n0.x, n0.y, 0.0), STONE)
            builder.oriented([(inner_a.x, inner_a.y, za), (inner_b.x, inner_b.y, zb), (inner_b.x, inner_b.y, zb + 1.5),
                              (inner_a.x, inner_a.y, za + 1.5)], (-n0.x, -n0.y, 0.0), STONE)
            builder.oriented([(a.x, a.y, za + 1.5), (b.x, b.y, zb + 1.5), (inner_b.x, inner_b.y, zb + 1.5),
                              (inner_a.x, inner_a.y, za + 1.5)], (0, 0, 1), STONE)
    return builder, rows


def square_tower(width=8.5, depth=7.5, height=12.0):
    builder = MeshBuilder()
    hw = width / 2
    tinted(builder, (0.93, 0.90, 0.84), lambda: builder.box((-hw, -2.0, -6.0), (hw, depth, height), "plaster",
                                                            bottom=False, top=False))
    for z in (height - 3.4, height - 7.4):
        for x in (-hw * 0.45, hw * 0.45):
            quad(builder, [(x - 0.4, depth + 0.01, z), (x + 0.4, depth + 0.01, z), (x + 0.4, depth + 0.01, z + 1.4),
                           (x - 0.4, depth + 0.01, z + 1.4)], (0, 1, 0), VOID)
    apex = height + 2.2
    corners = [(-hw - 0.5, -2.5), (hw + 0.5, -2.5), (hw + 0.5, depth + 0.5), (-hw - 0.5, depth + 0.5)]
    centre = (0.0, (depth - 2.0) / 2)
    for index in range(4):
        a, b = corners[index], corners[(index + 1) % 4]
        normal = ((a[0] + b[0]) / 2 - centre[0], (a[1] + b[1]) / 2 - centre[1], 3.0)
        builder.oriented([(a[0], a[1], height), (b[0], b[1], height), (centre[0], centre[1], apex)], normal, TILES)
    return builder


def gate(width=11.0, depth=14.0, height=9.0, passages=((0.0, 3.6, 5.6),), material="plaster", tint=(0.94, 0.9, 0.84)):
    builder = MeshBuilder()
    hw = width / 2
    xs = sorted([-hw, hw] + [x - w / 2 for x, w, _ in passages] + [x + w / 2 for x, w, _ in passages])
    for a, b in zip(xs[0::2], xs[1::2]):
        tinted(builder, tint, lambda a=a, b=b: builder.box((a, 0.0, -5.0), (b, depth, height), material, bottom=False))
    for x, w, h in passages:
        steps = 8
        arch = [(x + w / 2 * math.cos(math.pi * k / steps), h - w / 2 + w / 2 * math.sin(math.pi * k / steps))
                for k in range(steps + 1)]
        for y, normal in ((0.0, (0, -1, 0)), (depth, (0, 1, 0))):
            for (ax, az), (bx, bz) in zip(arch[:-1], arch[1:]):
                tinted(builder, tint, lambda ax=ax, az=az, bx=bx, bz=bz, y=y, normal=normal: builder.oriented(
                    [(ax, y, az), (bx, y, bz), (bx, y, height), (ax, y, height)], normal, material))
        for (ax, az), (bx, bz) in zip(arch[:-1], arch[1:]):
            normal = (x - (ax + bx) / 2, 0.0, h - w / 2 - (az + bz) / 2)
            tinted(builder, (0.5, 0.48, 0.45), lambda ax=ax, az=az, bx=bx, bz=bz, normal=normal: builder.oriented(
                [(ax, 0.0, az), (bx, 0.0, bz), (bx, depth, bz), (ax, depth, az)], normal, STONE))
    tinted(builder, (0.88, 0.85, 0.79), lambda: builder.box((-hw - 0.2, -0.2, height), (hw + 0.2, depth + 0.2,
                                                                                        height + 0.5), STONE))
    return builder
