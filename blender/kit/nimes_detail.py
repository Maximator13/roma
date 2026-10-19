import math
import random

import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from .buildings import ASHLAR, TILES, VOID, lobe, trunk
from .geometry import MATTE, MeshBuilder, newell_normal
from .nimes_figures import Look, drape, person, tube
from .orders import gable_ends
from .urban import CLOTH, PLASTERS, ROOF_TINTS, STONE_WHITE, WOODS, panel, tinted

WALL_MATERIALS = {"plaster", "weathered_ashlar", "lens_ashlar", "lens_smooth", "lens_fluted"}
ROOF_MATERIALS = {"terracotta_tiles", "roof_flat", "roof_tiles"}
CUTS = (0.1, 1.25)
DIRT = np.array([0.66, 0.58, 0.48])
MOSS = np.array([0.70, 0.78, 0.56])
WET = np.array([0.66, 0.66, 0.64])
TERRACOTTA_POT = (0.70, 0.42, 0.28)
LEAF = (0.36, 0.46, 0.22)
SHOP_INSIDE = (0.22, 0.17, 0.12)
SHOP_SHELF = (0.42, 0.32, 0.22)
ROPE = (0.45, 0.38, 0.28)
EARTH = (0.82, 0.76, 0.66)
HEMISPHERE = np.array([(0.0, 0.0, 1.0)] + [(math.cos(a) * 0.82, math.sin(a) * 0.82, 0.57)
                                          for a in np.linspace(0, 2 * math.pi, 5, endpoint=False)])
SKIP_OCCLUSION = {"water", "shadow_void", "velum_linen"}


def split_vertical(builder, cuts=CUTS, materials=WALL_MATERIALS, min_width=1.6, spacing=None):
    slots = {index for index, name in enumerate(builder.materials) if name in materials}
    polygons, materials_out, smooth_out, uvs_out, colors_out = [], [], [], [], []
    for indices, material, smooth, uvs, color in zip(builder.polygons, builder.polygon_materials,
                                                     builder.polygon_smooth, builder.polygon_uvs,
                                                     builder.polygon_colors):
        replaced = None
        if material in slots and len(indices) == 4 and uvs is None:
            corners = [builder.positions[index] for index in indices]
            if abs(newell_normal(corners).z) < 0.05:
                replaced = split_quad(builder, indices, cuts, min_width, spacing)
        for piece in replaced or [indices]:
            polygons.append(piece)
            materials_out.append(material)
            smooth_out.append(smooth)
            uvs_out.append(uvs)
            colors_out.append(color)
    builder.polygons = polygons
    builder.polygon_materials = materials_out
    builder.polygon_smooth = smooth_out
    builder.polygon_uvs = uvs_out
    builder.polygon_colors = colors_out
    return builder


def split_quad(builder, indices, cuts, min_width, spacing=None):
    zs = [builder.positions[index][2] for index in indices]
    low, high = min(zs), max(zs)
    inner = [cut for cut in cuts if low + 0.05 < cut < high - 0.05]
    if not inner and spacing is None:
        return None
    for shift in range(4):
        order = [indices[(shift + k) % 4] for k in range(4)]
        z = [builder.positions[index][2] for index in order]
        if abs(z[0] - low) < 1e-4 and abs(z[1] - low) < 1e-4 and abs(z[2] - high) < 1e-4 and abs(z[3] - high) < 1e-4:
            break
    else:
        return None
    a, b, c, d = (Vector(builder.positions[index]) for index in order)
    if (b - a).length < min_width:
        return None
    lefts = [order[0]]
    rights = [order[1]]
    for cut in inner:
        t = (cut - low) / (high - low)
        lefts.append(builder.point(a.lerp(d, t)))
        rights.append(builder.point(b.lerp(c, t)))
    lefts.append(order[3])
    rights.append(order[2])
    columns = max(int(math.ceil((b - a).length / spacing)), 1) if spacing else 1
    if columns == 1:
        if not inner:
            return None
        return [(lefts[k], rights[k], rights[k + 1], lefts[k + 1]) for k in range(len(lefts) - 1)]
    rows = []
    for left, right in zip(lefts, rights):
        start, end = Vector(builder.positions[left]), Vector(builder.positions[right])
        rows.append([left] + [builder.point(start.lerp(end, j / columns)) for j in range(1, columns)] + [right])
    return [(rows[k][j], rows[k][j + 1], rows[k + 1][j + 1], rows[k + 1][j]) for k in range(len(rows) - 1)
            for j in range(columns)]


def smooth_noise(points, scale, seed):
    x, y, z = points[:, 0] * scale, points[:, 1] * scale, points[:, 2] * scale
    value = (np.sin(x * 1.7 + seed) * np.sin(y * 1.3 + 2.1 * seed) + np.sin(z * 2.3 + x * 0.7 + seed * 0.5)
             + 0.5 * np.sin((x - y) * 3.1 + seed * 1.7))
    return 0.5 + value / 5.0


def weather(mesh, heights=None, seed=0, walls=True, roofs=True, foliage=False):
    attribute = mesh.color_attributes.get("Col")
    if attribute is None or len(mesh.loops) == 0:
        return
    count = len(mesh.loops)
    colours = np.empty(count * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    vertex = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex)
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    totals = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", totals)
    slots = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", slots)
    corner_slot = np.repeat(slots, totals)
    names = [material.name if material else "" for material in mesh.materials]
    points = positions[vertex]
    height = heights[vertex] if heights is not None else points[:, 2]
    rgb = colours[:, :3]
    normals = np.empty(count * 3, dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", normals)
    normals = normals.reshape(-1, 3)
    if walls:
        mask = np.isin(corner_slot, [index for index, name in enumerate(names) if name in WALL_MATERIALS])
        t = np.clip(height / 1.25, 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        upright = np.clip(1.0 - np.abs(normals[:, 2]) * 1.4, 0.0, 1.0)
        t = 1.0 - (1.0 - t) * upright
        stain = 1.0 + 0.09 * (smooth_noise(points, 0.6, seed) - 0.5)
        factor = (DIRT[None, :] + (1 - DIRT[None, :]) * t[:, None]) * stain[:, None]
        damp = np.clip(1.0 - height / 0.7, 0.0, 1.0) * upright
        patch = np.clip((smooth_noise(points, 1.3, seed + 11) - 0.42) * 5.0, 0.0, 1.0)
        moss = (damp * patch * 0.6)[:, None]
        factor *= 1.0 - moss * (1.0 - MOSS[None, :])
        rgb[mask] *= factor[mask]
    if roofs:
        mask = np.isin(corner_slot, [index for index, name in enumerate(names) if name in ROOF_MATERIALS])
        n1 = smooth_noise(points, 0.35, seed + 3)
        n2 = smooth_noise(points, 0.9, seed + 7)
        tint = np.column_stack([0.9 + 0.2 * n1, 0.86 + 0.22 * n1 * n2 + 0.04, 0.84 + 0.2 * n2])
        rgb[mask] *= tint[mask]
    if foliage:
        green = (rgb[:, 1] > rgb[:, 0] * 1.02) & (rgb[:, 1] > rgb[:, 2])
        bottom, top = points[:, 2].min(), points[:, 2].max()
        relative = np.clip((points[:, 2] - bottom) / max(top - bottom, 1e-3), 0, 1)
        light = 0.62 + 0.42 * np.clip(normals[:, 2] * 0.5 + 0.5, 0, 1) * (0.55 + 0.45 * relative)
        light *= 0.9 + 0.2 * smooth_noise(points, 1.4, seed)
        warm = np.column_stack([light * (1.0 + 0.08 * relative), light * (1.0 + 0.03 * relative),
                                light * (1.05 - 0.12 * relative)])
        rgb[green] *= warm[green]
    colours[:, :3] = np.clip(rgb, 0.0, 1.0)
    attribute.data.foreach_set("color_srgb", colours.ravel())
    mesh.update()


def wet_edges(mesh, reach=0.8, above=0.5, below=0.8):
    attribute = mesh.color_attributes.get("Col")
    names = [material.name if material else "" for material in mesh.materials]
    if attribute is None or "water" not in names or len(mesh.loops) == 0:
        return
    water = names.index("water")
    count = len(mesh.loops)
    vertex = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex)
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    totals = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", totals)
    slots = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", slots)
    corner_slot = np.repeat(slots, totals)
    points = positions[vertex]
    shade = np.ones(count)
    for polygon in mesh.polygons:
        if polygon.material_index != water or polygon.area < 1.0 or abs(polygon.normal.z) < 0.9:
            continue
        corners = positions[list(polygon.vertices)]
        low = corners.min(axis=0) - reach
        high = corners.max(axis=0) + reach
        level = corners[:, 2].mean()
        inside = ((points[:, 0] > low[0]) & (points[:, 0] < high[0]) & (points[:, 1] > low[1]) & (points[:, 1] < high[1])
                  & (points[:, 2] > level - below) & (points[:, 2] < level + above))
        t = np.clip((points[:, 2] - level) / above, 0.0, 1.0)
        shade = np.where(inside, np.minimum(shade, 0.68 + 0.32 * t), shade)
    keep = corner_slot != water
    colours = np.empty(count * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    wet = (1.0 - shade)[:, None] / 0.32
    factor = shade[:, None] * (1.0 - wet * (1.0 - WET[None, :] / WET.max()))
    colours[keep, :3] = np.clip(colours[keep, :3] * factor[keep], 0.0, 1.0)
    attribute.data.foreach_set("color_srgb", colours.ravel())
    mesh.update()


def occlusion(mesh, seed=0, reach=2.0, strength=0.35, drip=3.0):
    attribute = mesh.color_attributes.get("Col")
    if attribute is None or len(mesh.loops) == 0 or len(mesh.vertices) > 400000:
        return
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    normals = np.empty(count * 3, dtype=np.float64)
    mesh.vertex_normals.foreach_get("vector", normals)
    normals = normals.reshape(-1, 3)
    mesh.calc_loop_triangles()
    tris = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get("vertices", tris)
    tree = BVHTree.FromPolygons(co.tolist(), tris.reshape(-1, 3).tolist(), all_triangles=True)
    helper = np.where(np.abs(normals[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
    tangent = np.cross(normals, helper)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1, keepdims=True), 1e-9)
    bitangent = np.cross(normals, tangent)
    directions = (HEMISPHERE[None, :, 0:1] * tangent[:, None, :] + HEMISPHERE[None, :, 1:2] * bitangent[:, None, :]
                  + HEMISPHERE[None, :, 2:3] * normals[:, None, :])
    origins = co + normals * 0.03
    ray = tree.ray_cast
    hits = np.zeros(count)
    above = np.zeros(count, dtype=bool)
    up = Vector((0.0, 0.0, 1.0))
    wall = np.abs(normals[:, 2]) < 0.5
    for index in range(count):
        origin = Vector(origins[index])
        hits[index] = sum(ray(origin, Vector(direction), reach)[0] is not None for direction in directions[index])
        if wall[index]:
            above[index] = ray(origin, up, drip)[0] is not None
    shade = 1.0 - strength * (hits / len(HEMISPHERE)) ** 0.8
    streak = smooth_noise(np.column_stack([co[:, 0] * 3.0, co[:, 1] * 3.0, np.zeros(count)]), 1.0, seed)
    shade *= np.where(above, 1.0 - (0.08 + 0.04 * streak), 1.0)
    rng = np.random.default_rng(seed)
    hue = 1.0 + 0.03 * (rng.random(3) * 2.0 - 1.0)
    loops = len(mesh.loops)
    colours = np.empty(loops * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    vertex = np.empty(loops, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex)
    totals = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", totals)
    slots = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", slots)
    names = [material.name if material else "" for material in mesh.materials]
    keep = ~np.isin(np.repeat(slots, totals), [index for index, name in enumerate(names) if name in SKIP_OCCLUSION])
    factor = shade[vertex][:, None] * hue[None, :]
    colours[keep, :3] = np.clip(colours[keep, :3] * factor[keep], 0.0, 1.0)
    attribute.data.foreach_set("color_srgb", colours.ravel())
    mesh.update()


def velum_ropes(masts, origin, angle, edge_a, edge_b, edge_z, width=0.05):
    builder = MeshBuilder()
    cx, cy, base = origin
    cosine, sine = math.cos(angle), math.sin(angle)
    for top in masts:
        lx = (top.x - cx) * cosine + (top.y - cy) * sine
        ly = -(top.x - cx) * sine + (top.y - cy) * cosine
        t = math.atan2(ly / edge_b, lx / edge_a)
        ex, ey = edge_a * math.cos(t), edge_b * math.sin(t)
        end = Vector((cx + ex * cosine - ey * sine, cy + ex * sine + ey * cosine, base + edge_z))
        along = (end - top).to_2d()
        side = Vector((-along.y, along.x, 0.0)).normalized() * width / 2
        quad = [top - side, top + side, end + side, end - side]
        first = len(builder.polygons)
        builder.polygon(quad, MATTE)
        builder.polygon(list(reversed(quad)), MATTE)
        builder.tint(first, ROPE)
    return builder


def column_statue():
    builder = MeshBuilder()
    builder.box((-0.34, -0.34, 0.0), (0.34, 0.34, 0.28), "lens_smooth", bottom=False)
    spec = Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=(1.0, 1.0, 1.0), material="bronze", seed=33)
    builder.merge(person(spec), Matrix.Translation((0.0, 0.0, 0.28)) @ Matrix.Scale(0.9, 4))
    return builder


def rough_lobe(builder, center, radius, height, material, segments=6, seed=0, flat=0.0, amount=0.18):
    first = len(builder.positions)
    lobe(builder, center, radius, height, material, segments, seed, flat)
    points = np.array(builder.positions[first:])
    if len(points) == 0:
        return
    middle = np.array(center)
    noise = smooth_noise(points / 1.2, 1.0, seed)
    moved = middle + (points - middle) * (1.0 + amount * (2.0 * noise - 1.0))[:, None]
    builder.positions[first:] = [tuple(map(float, point)) for point in moved]


def cloth_awning(builder, x0, x1, hd, rng, rows=2):
    light, dark = CLOTH[rng.randrange(len(CLOTH))]
    light = tuple(min(1.0, 0.35 + 0.65 * value) for value in light)
    front = -hd - 2.1
    columns = 8
    grid = []
    for row in range(rows + 1):
        t = row / rows
        y = -hd + (front + 0.3 + hd) * t
        line = []
        for column in range(columns + 1):
            s = column / columns
            x = x0 + (x1 - x0) * s
            sag = 0.14 * math.sin(math.pi * t) * (0.6 + 0.4 * abs(math.sin(math.pi * s * 2)))
            fold = 0.05 * t * (1 if column % 2 else -1)
            line.append((x, y, 3.0 - 0.45 * t - sag + fold))
        grid.append(line)
    for row in range(rows):
        for column in range(columns):
            color = light
            quad = [grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]]
            tinted(builder, color, lambda quad=quad: builder.oriented(quad, (0, -0.2, 1), "plaster", True))
            tinted(builder, tuple(v * 0.8 for v in color),
                   lambda quad=quad: builder.oriented(quad, (0, 0.2, -1), "plaster", True))
    edge = grid[-1]
    for column in range(columns):
        a, b = edge[column], edge[column + 1]
        drop = 0.15
        quad = [a, b, (b[0], b[1], b[2] - drop), (a[0], a[1], a[2] - drop)]
        color = dark
        tinted(builder, color, lambda quad=quad: builder.oriented(quad, (0, -1, 0), "plaster"))
        tinted(builder, color, lambda quad=quad: builder.oriented(quad, (0, 1, 0), "plaster"))
    for x in (x0 + 0.2, x1 - 0.2):
        tinted(builder, (0.55, 0.42, 0.28), lambda x=x: builder.box((x - 0.05, front + 0.25, -0.2), (x + 0.05, front + 0.35, 2.55),
                                                          "plaster", bottom=False, top=False))


def tile_awning(builder, x0, x1, hd):
    front = -hd - 2.1
    top_quad = [(x0, -hd, 3.15), (x1, -hd, 3.15), (x1, front, 2.78), (x0, front, 2.78)]
    builder.oriented(top_quad, (0, -0.2, 1), TILES)
    tinted(builder, WOODS[0], lambda: builder.oriented(top_quad, (0, 0.2, -1), "plaster"))
    for x in (x0 + 0.3, (x0 + x1) / 2, x1 - 0.3):
        tinted(builder, WOODS[2], lambda x=x: builder.box((x - 0.1, front + 0.1, -0.2), (x + 0.1, front + 0.3, 2.78),
                                                          "plaster", bottom=False, top=False))


def ajar(builder, x, z, front, shutter, rng):
    for side in (-1, 1):
        hinge = x + side * 0.3
        angle = math.radians(rng.uniform(25, 70))
        tip = (hinge + side * 0.32 * math.cos(angle), front - 0.32 * math.sin(angle))
        quad = [(hinge, front, z), (tip[0], tip[1], z), (tip[0], tip[1], z + 0.9), (hinge, front, z + 0.9)]
        tinted(builder, shutter, lambda quad=quad: builder.polygon(quad, "plaster"))
        tinted(builder, tuple(v * 0.8 for v in shutter), lambda quad=quad: builder.polygon(list(reversed(quad)),
                                                                                           "plaster"))


def laundry(builder, x0, x1, z, front, rng):
    tinted(builder, (0.4, 0.33, 0.25), lambda: builder.box((x0, front - 0.42, z - 0.01), (x1, front - 0.4, z + 0.01),
                                                           "plaster", bottom=False, top=False))
    x = x0 + 0.3
    colours = [(0.93, 0.91, 0.86), (0.80, 0.75, 0.64), (0.64, 0.28, 0.20), (0.42, 0.49, 0.58), (0.80, 0.71, 0.42)]
    while x < x1 - 0.7:
        width = rng.uniform(0.45, 0.8)
        drop = rng.uniform(0.5, 0.9)
        y = front - 0.41
        quad = [(x, y, z), (x + width, y, z), (x + width, y + 0.04, z - drop), (x, y - 0.03, z - drop * 0.95)]
        color = colours[rng.randrange(len(colours))]
        tinted(builder, color, lambda quad=quad: builder.polygon(quad, "plaster"))
        tinted(builder, tuple(v * 0.85 for v in color),
               lambda quad=quad: builder.polygon(list(reversed(quad)), "plaster"))
        x += width + rng.uniform(0.1, 0.4)


def roof(builder, x0, x1, hd, height, top, kind, tint, wall, detail=True):
    eave = height - 0.16
    overhang = 0.4
    if kind == "hip" and (x1 - x0) > 2 * hd + 0.5:
        ridge0, ridge1 = x0 + hd, x1 - hd
        quads = {(0, -1, 1): [(x0 - 0.15, -hd - overhang, eave), (x1 + 0.15, -hd - overhang, eave), (ridge1, 0.0, top),
                              (ridge0, 0.0, top)],
                 (0, 1, 1): [(x1 + 0.15, hd + overhang, eave), (x0 - 0.15, hd + overhang, eave), (ridge0, 0.0, top),
                             (ridge1, 0.0, top)],
                 (-1, 0, 1): [(x0 - 0.15, hd + overhang, eave), (x0 - 0.15, -hd - overhang, eave), (ridge0, 0.0, top)],
                 (1, 0, 1): [(x1 + 0.15, -hd - overhang, eave), (x1 + 0.15, hd + overhang, eave), (ridge1, 0.0, top)]}
        for normal, quad in quads.items():
            tinted(builder, tint, lambda quad=quad, normal=normal: builder.oriented(quad, normal, TILES))
        ridge = tuple(v * 0.8 for v in tint)
        if not detail:
            return
        tube(builder, [(ridge0, 0.0, top + 0.04), (ridge1, 0.0, top + 0.04)], [0.11, 0.11], ridge, 4, TILES,
             cap=False)
        for corner, end in (((x0 - 0.15, -hd - overhang), ridge0), ((x0 - 0.15, hd + overhang), ridge0),
                            ((x1 + 0.15, -hd - overhang), ridge1), ((x1 + 0.15, hd + overhang), ridge1)):
            tube(builder, [(corner[0], corner[1], eave + 0.05), (end, 0.0, top + 0.04)], [0.08, 0.09], ridge, 4,
                 TILES, cap=False)
        return
    for side in (-1, 1):
        quad = [(x0 - 0.15, side * (hd + overhang), eave), (x1 + 0.15, side * (hd + overhang), eave),
                (x1 + 0.15, 0.0, top), (x0 - 0.15, 0.0, top)]
        tinted(builder, tint, lambda quad=quad, side=side: builder.oriented(quad, (0, side, 1), TILES))
    if detail:
        tube(builder, [(x0 - 0.2, 0.0, top + 0.04), (x1 + 0.2, 0.0, top + 0.04)], [0.11, 0.11],
             tuple(v * 0.8 for v in tint), 4, TILES, start_cap=True)
    gable_ends(builder, x0, x1, hd, height, top, wall, along_axis="x")


def town_unit(builder, x0, width, depth, height, wall, roof_kind, shops, windows, awning_kind, balcony, roof_tint,
              rng, detail=True, plain=False):
    hd = depth / 2
    x1 = x0 + width
    builder.box((x0, -hd, -3.0), (x1, hd, height), wall, bottom=False, top=False)
    for side in ((-1, 1) if not plain else ()):
        tinted(builder, tuple(v * 0.93 for v in STONE_WHITE), lambda side=side: builder.box(
            (x0, side * hd - 0.14 if side < 0 else hd, height - 0.36), (x1, -hd if side < 0 else hd + 0.14, height - 0.16),
            wall, top=False))
    top = height + hd * 0.4
    roof(builder, x0, x1, hd, height, top, roof_kind, roof_tint, wall, not plain)
    front = -hd - 0.02
    shutter = WOODS[rng.randrange(len(WOODS))]
    if shops:
        spacing = width / shops
        for index in range(shops):
            x = x0 + spacing * (index + 0.5)
            opening = spacing * 0.64
            panel(builder, x - opening / 2, x + opening / 2, 0.0, 2.2, front, -1, "plaster", SHOP_INSIDE)
            panel(builder, x - opening / 2, x + opening / 2, 2.2, 2.75, front, -1, VOID)
            panel(builder, x - opening / 2 + 0.1, x + opening / 2 - 0.1, 1.3, 1.37, front - 0.005, -1, "plaster",
                  SHOP_SHELF)
            panel(builder, x - opening / 2 - 0.12, x + opening / 2 + 0.12, 2.75, 3.0, front - 0.01, -1, wall,
                  STONE_WHITE)
            counter = opening * 0.55
            left = x - opening / 2 if index % 2 == 0 else x + opening / 2 - counter
            tinted(builder, STONE_WHITE, lambda left=left, counter=counter: builder.box(
                (left, -hd - 0.6, -0.3), (left + counter, -hd + 0.05, 1.0), wall, bottom=False))
            if detail and rng.random() < 0.5:
                drape(builder, (0.72, 0.45, 0.30), [(0.11, 1.0), (0.12, 1.2), (0.06, 1.32), (0.07, 1.36)], 5,
                      folds=(0, 0.0, 0.0), squash=1.0, center=(left + counter * rng.uniform(0.25, 0.75), -hd - 0.3),
                      material="plaster")
        if awning_kind == "tile":
            tile_awning(builder, x0 + 0.2, x1 - 0.2, hd)
        elif awning_kind:
            cloth_awning(builder, x0 + 0.2, x1 - 0.2, hd, rng, 2 if detail else 1)
    else:
        middle = x0 + width * (0.3 + 0.4 * rng.random())
        panel(builder, middle - 0.75, middle + 0.75, 0.0, 2.5, front, -1, wall, shutter)
        panel(builder, middle - 0.95, middle + 0.95, 2.5, 2.75, front - 0.01, -1, wall, STONE_WHITE)
        panel(builder, middle - 0.95, middle - 0.75, 0.0, 2.5, front - 0.01, -1, wall, STONE_WHITE)
        panel(builder, middle + 0.75, middle + 0.95, 0.0, 2.5, front - 0.01, -1, wall, STONE_WHITE)
        if width > 10:
            other = x0 + width * 0.82 if middle < x0 + width / 2 else x0 + width * 0.18
            panel(builder, other - 0.35, other + 0.35, 1.5, 2.3, front, -1, VOID)
            panel(builder, other - 0.7, other - 0.35, 1.5, 2.3, front - 0.01, -1, wall, shutter)
            panel(builder, other + 0.35, other + 0.7, 1.5, 2.3, front - 0.01, -1, wall, shutter)
    floors = max(int(height / 3.2), 1)
    for floor in range(1, floors):
        z = floor * 3.2 + 0.7
        for index in range(windows):
            x = x0 + width * (index + 0.5) / windows
            panel(builder, x - 0.3, x + 0.3, z, z + 0.9, front, -1, VOID)
            sill = [(x - 0.4, front, z), (x + 0.4, front, z), (x + 0.4, front - 0.09, z - 0.02),
                    (x - 0.4, front - 0.09, z - 0.02)]
            if not plain:
                tinted(builder, STONE_WHITE, lambda sill=sill: builder.oriented(sill, (0, -0.3, 1), wall))
                panel(builder, x - 0.4, x + 0.4, z - 0.12, z - 0.02, front - 0.09, -1, wall, (0.9, 0.88, 0.84))
                panel(builder, x - 0.36, x + 0.36, z + 0.9, z + 1.02, front - 0.012, -1, wall, (0.92, 0.9, 0.86))
            state = (index + floor + rng.randrange(2)) % 3
            if state == 0:
                panel(builder, x - 0.62, x - 0.3, z, z + 0.9, front - 0.01, -1, wall, shutter)
                panel(builder, x + 0.3, x + 0.62, z, z + 0.9, front - 0.01, -1, wall, shutter)
            elif state == 1 and detail:
                ajar(builder, x, z, front - 0.01, shutter, rng)
            elif state == 1:
                panel(builder, x - 0.62, x - 0.3, z, z + 0.9, front - 0.01, -1, wall, shutter)
                panel(builder, x + 0.3, x + 0.62, z, z + 0.9, front - 0.01, -1, wall, shutter)
            else:
                panel(builder, x - 0.3, x + 0.3, z, z + 0.9, front - 0.015, -1, wall,
                      tuple(v * 0.9 for v in shutter))
    if balcony and floors >= 2:
        tinted(builder, WOODS[0], lambda: builder.box((x0 + 0.8, -hd - 1.0, 3.15), (x1 - 0.8, -hd, 3.3), wall))
        rail = [(x0 + 0.8, -hd - 1.0, 3.3), (x1 - 0.8, -hd - 1.0, 3.3), (x1 - 0.8, -hd - 1.0, 4.2),
                (x0 + 0.8, -hd - 1.0, 4.2)]
        tinted(builder, WOODS[0], lambda: builder.oriented(rail, (0, -1, 0), wall))
        tinted(builder, WOODS[3], lambda: builder.oriented(rail, (0, 1, 0), wall))
        for k in range(2 if detail else 0):
            px = x0 + 1.3 + k * (width - 2.6)
            drape(builder, TERRACOTTA_POT, [(0.12, 3.3), (0.16, 3.55)], 4, folds=(0, 0.0, 0.0), squash=1.0,
                  center=(px, -hd - 0.7), material="plaster")
            drape(builder, LEAF, [(0.16, 3.52), (0.24, 3.72), (0.0, 3.95)], 5, folds=(2, 0.15, k), squash=1.0,
                  center=(px, -hd - 0.7), material="plaster")
        if detail and rng.random() < 0.5:
            laundry(builder, x0 + 1.0, x1 - 1.0, 5.2, -hd - 0.49, rng)
    elif detail and floors >= 2 and rng.random() < 0.35:
        laundry(builder, x0 + 1.5, x0 + width * 0.7, 3.2 + 2.0, front, rng)
    back = hd + 0.02
    for index in range(2):
        x = x0 + width * (0.25 + 0.5 * index)
        panel(builder, x - 0.3, x + 0.3, height - 2.0, height - 1.2, back, 1, VOID)


def row_template(seed, tabernae=False, depth=11.0, units=2, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    width = 16.0
    for index in range(units):
        x0 = -width * units / 2 + width * index
        heights = [6.4, 7.0, 8.2, 9.8] if tabernae else [5.2, 6.4, 7.0, 8.2, 9.8]
        height = rng.choice(heights)
        shops = 3 if (tabernae or rng.random() < 0.35) else 0
        kind = rng.choice(["tile", "cloth", "cloth"]) if shops else None
        town_unit(builder, x0, width, depth, height, rng.choice(PLASTERS), rng.choice(["gable", "hip", "hip"]), shops,
                  3 if height > 6.5 else 2, kind, height >= 8.0 and rng.random() < 0.6, rng.choice(ROOF_TINTS), rng,
                  tabernae and detail, not detail)
    return split_vertical(builder) if tabernae else builder


def street_fountain():
    builder = MeshBuilder()
    for (x0, y0), (x1, y1) in (((-0.95, -0.65), (0.95, -0.47)), ((-0.95, 0.47), (0.95, 0.65)),
                               ((-0.95, -0.47), (-0.77, 0.47)), ((0.77, -0.47), (0.95, 0.47))):
        builder.box((x0, y0, -0.3), (x1, y1, 0.75), ASHLAR, bottom=False)
    builder.polygon([(-0.77, -0.47, 0.64), (0.77, -0.47, 0.64), (0.77, 0.47, 0.64), (-0.77, 0.47, 0.64)], "water")
    builder.box((-0.28, 0.65, -0.3), (0.28, 1.0, 1.35), ASHLAR, bottom=False)
    builder.box((-0.34, 0.6, 1.35), (0.34, 1.05, 1.5), ASHLAR, bottom=False)
    panel(builder, -0.12, 0.12, 0.9, 1.14, 0.64, -1, ASHLAR, (0.55, 0.52, 0.48))
    builder.polygon([(-0.03, 0.62, 0.94), (0.03, 0.62, 0.94), (0.03, 0.2, 0.65), (-0.03, 0.2, 0.65)], "water")
    rng = random.Random(4)
    for cx, cy, radius in ((1.45, -0.1, 0.42), (-1.35, 0.05, 0.3), (0.2, -0.78, 0.16)):
        outline = []
        for k in range(9):
            angle = 2 * math.pi * k / 9
            r = radius * rng.uniform(0.7, 1.15)
            outline.append((cx + r * math.cos(angle), cy + r * 0.75 * math.sin(angle), 0.012))
        first = len(builder.polygons)
        builder.polygon(outline, "water")
        builder.tint(first, (0.62, 0.6, 0.56))
    return builder


def shop_goods(seed):
    rng = random.Random(seed)
    builder = MeshBuilder()
    produce = [(0.45, 0.55, 0.25), (0.70, 0.30, 0.18), (0.85, 0.72, 0.40), (0.42, 0.22, 0.30), (0.62, 0.48, 0.26)]
    for k in range(3):
        frame = (Matrix.Translation((-0.62 + k * 0.33, 0.12 + 0.05 * (k % 2), 0.0))
                 @ Matrix.Rotation(math.radians(rng.uniform(-10, 4)), 4, "X"))
        drape(builder, (0.70 + 0.04 * (k % 3), 0.42 + 0.03 * k, 0.28),
              [(0.0, -0.03), (0.15, 0.22), (0.16, 0.5), (0.06, 0.74), (0.05, 0.9)], 6, folds=(0, 0.0, 0.0),
              squash=1.0, matrix=frame)
    for k in range(2):
        x, y = 0.25 + k * 0.42, -0.15
        drape(builder, (0.62, 0.50, 0.32), [(0.16, 0.0), (0.2, 0.18)], 6, folds=(0, 0.0, 0.0), squash=1.0, center=(x, y))
        drape(builder, produce[(k + seed) % 5], [(0.2, 0.17), (0.12, 0.25), (0.0, 0.27)], 6, folds=(3, 0.12, k),
              squash=1.0, center=(x, y))
    for k, color in enumerate(((0.64, 0.28, 0.20), (0.42, 0.49, 0.58), (0.80, 0.71, 0.42))):
        x = 0.2 + k * 0.19
        tube(builder, [(x, 0.05, 0.08), (x, 0.5, 0.08)], [0.08, 0.08], color, 5, start_cap=True)
    return builder


def potted_plant(seed=0):
    builder = MeshBuilder()
    drape(builder, TERRACOTTA_POT, [(0.0, 0.0), (0.18, 0.02), (0.24, 0.42), (0.27, 0.46), (0.22, 0.47)], 8,
          folds=(0, 0.0, 0.0), squash=1.0)
    trunk(builder, 0.9, 0.04, at=(0.0, 0.0, 0.4))
    lobe(builder, (0.0, 0.0, 1.25), 0.42, 0.85, "foliage_shrub", 7, seed)
    lobe(builder, (0.15, 0.1, 0.85), 0.28, 0.45, "foliage_olive", 6, seed + 1)
    return builder


def weeds(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for _ in range(5):
        x, y = rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1)
        dry = rng.random()
        for blade in range(7):
            angle = rng.uniform(0, 2 * math.pi)
            height = rng.uniform(0.18, 0.5)
            reach = rng.uniform(0.05, 0.22)
            width = rng.uniform(0.015, 0.03)
            tip = (x + math.cos(angle) * reach, y + math.sin(angle) * reach, height)
            side = (-math.sin(angle) * width, math.cos(angle) * width)
            triangle = [(x - side[0], y - side[1], -0.02), (x + side[0], y + side[1], -0.02), tip]
            tone = rng.uniform(0.85, 1.1)
            color = ((0.58 + 0.2 * dry) * tone, (0.56 + 0.06 * dry) * tone, (0.26 + 0.06 * dry) * tone)
            for points in (triangle, list(reversed(triangle))):
                first = len(builder.polygons)
                builder.polygon(points, MATTE)
                builder.tint(first, color)
    return builder


def plane_tree(height=16.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    first = len(builder.polygons)
    trunk(builder, height * 0.5, 0.42, (0.4, 0.2), MATTE)
    builder.tint(first, (0.74, 0.72, 0.64))
    r = height * 0.24
    centres = [(0.4, 0.2, height * 0.72, 1.0)]
    for k in range(7):
        angle = 2 * math.pi * k / 7 + rng.uniform(-0.3, 0.3)
        reach = r * rng.uniform(0.75, 1.05)
        centres.append((0.4 + math.cos(angle) * reach, 0.2 + math.sin(angle) * reach,
                        height * rng.uniform(0.52, 0.7), rng.uniform(0.55, 0.75)))
    for k in range(3):
        angle = 2 * math.pi * k / 3 + 0.9
        centres.append((0.4 + math.cos(angle) * r * 1.35, 0.2 + math.sin(angle) * r * 1.35, height * 0.6, 0.32))
    for index, (x, y, z, size) in enumerate(centres):
        rough_lobe(builder, (x, y, z), r * size, height * 0.36 * size, "foliage_plane", 7 if size > 0.4 else 5,
                   seed + index)
    for k in range(4):
        angle = 2 * math.pi * k / 4 + 0.4
        tube(builder, [(0.4 + 0.1 * math.cos(angle), 0.2, height * 0.42),
                       (0.4 + math.cos(angle) * r * 0.7, 0.2 + math.sin(angle) * r * 0.7, height * 0.58)],
             [0.16, 0.08], (0.78, 0.76, 0.68), 4)
    return builder


def litter(builder, points, rng):
    for x, y, z, heading in points:
        kind = rng.random()
        if kind < 0.45:
            for _ in range(rng.randrange(3, 7)):
                cx, cy = x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6)
                angle = rng.uniform(0, math.pi)
                dx, dy = math.cos(angle) * 0.18, math.sin(angle) * 0.18
                nx, ny = -dy * 0.12, dx * 0.12
                first = len(builder.polygons)
                builder.polygon([(cx - dx - nx, cy - dy - ny, z + 0.025), (cx + dx - nx, cy + dy - ny, z + 0.025),
                                 (cx + dx + nx, cy + dy + ny, z + 0.03), (cx - dx + nx, cy - dy + ny, z + 0.03)],
                                "arena_sand")
                builder.tint(first, (1.15, 1.02, 0.62))
        elif kind < 0.7:
            outline = []
            radius = rng.uniform(0.12, 0.22)
            for k in range(6):
                angle = 2 * math.pi * k / 6
                outline.append((x + radius * math.cos(angle), y + radius * math.sin(angle), z + 0.035))
            first = len(builder.polygons)
            builder.polygon(outline, "arena_sand")
            builder.tint(first, (0.42, 0.34, 0.24))
        else:
            dx, dy = math.cos(heading), math.sin(heading)
            for offset in (-0.65, 0.65):
                ox, oy = -dy * offset, dx * offset
                length = rng.uniform(3.0, 6.0)
                first = len(builder.polygons)
                builder.polygon([(x + ox - dx * length / 2 + dy * 0.06, y + oy - dy * length / 2 - dx * 0.06, z + 0.02),
                                 (x + ox + dx * length / 2 + dy * 0.06, y + oy + dy * length / 2 - dx * 0.06, z + 0.02),
                                 (x + ox + dx * length / 2 - dy * 0.06, y + oy + dy * length / 2 + dx * 0.06, z + 0.02),
                                 (x + ox - dx * length / 2 - dy * 0.06, y + oy - dy * length / 2 + dx * 0.06, z + 0.02)],
                                "arena_sand")
                builder.tint(first, (0.72, 0.66, 0.56))
    return builder


def street_segment(paved=True, length=16.0, width=8.0):
    builder = MeshBuilder()
    half = length / 2
    road = 2.6
    walk = width / 2 + 0.3
    surface = "street_paving" if paved else "arena_sand"
    tone = (0.84, 0.81, 0.76) if paved else (0.86, 0.8, 0.72)
    top = 0.36 if paved else 0.28
    tinted(builder, tone, lambda: builder.polygon([(-half, -road, 0.12), (half, -road, 0.12), (half, road, 0.12),
                                                   (-half, road, 0.12)], surface))
    for side in (-1, 1):
        y0, y1 = sorted((side * 0.65, side * 0.75))
        tinted(builder, (0.8, 0.77, 0.74), lambda y0=y0, y1=y1: builder.polygon(
            [(-half, y0, 0.125), (half, y0, 0.125), (half, y1, 0.125), (-half, y1, 0.125)], surface))
        inner, outer = side * road, side * walk
        builder.oriented([(-half, inner, -0.6), (half, inner, -0.6), (half, inner, top), (-half, inner, top)],
                         (0, -side, 0), "weathered_ashlar")
        kerb = side * (road + 0.35)
        builder.oriented([(-half, inner, top), (half, inner, top), (half, kerb, top), (-half, kerb, top)],
                         (0, 0, 1), "weathered_ashlar")
        tinted(builder, EARTH, lambda kerb=kerb, outer=outer: builder.oriented(
            [(-half, kerb, top), (half, kerb, top), (half, outer, top), (-half, outer, top)], (0, 0, 1),
            "arena_sand"))
        builder.oriented([(-half, outer, -0.6), (half, outer, -0.6), (half, outer, top), (-half, outer, top)],
                         (0, side, 0), "weathered_ashlar")
        if paved:
            panel(builder, 2.5, 2.85, 0.14, 0.27, side * (road + 0.01), -side, VOID)
    return builder


def holm_oak(height=8.0, seed=0):
    builder = MeshBuilder()
    trunk_lean(builder, height * 0.38, 0.2, (0.3, 0.0))
    r = height * 0.32
    rough_lobe(builder, (0.4, 0.2, height * 0.62), r, height * 0.55, "foliage_dark", 6, seed)
    rough_lobe(builder, (-r * 0.75, -r * 0.2, height * 0.5), r * 0.72, height * 0.42, "foliage_dark", 4, seed + 1)
    return builder


def olive_tree(height=4.5, seed=0):
    builder = MeshBuilder()
    trunk_lean(builder, 1.5, 0.17, (0.35, 0.1))
    r = height * 0.33
    rough_lobe(builder, (0.6, 0.3, height * 0.66), r, height * 0.5, "foliage_olive", 6, seed, 0.1)
    rough_lobe(builder, (-0.6, -0.4, height * 0.55), r * 0.8, height * 0.4, "foliage_olive", 4, seed + 3, 0.1)
    return builder


def trunk_lean(builder, top, radius, lean):
    shear = Matrix(((1, 0, lean[0] / max(top, 0.1), 0.0), (0, 1, lean[1] / max(top, 0.1), 0.0), (0, 0, 1, 0.0),
                    (0, 0, 0, 1)))
    builder.lathe([(radius * 1.15, -0.5), (radius * 0.75, top)], 3, "bark", smooth=True, caps=False, matrix=shear)


def vine_row(length=10.0):
    builder = MeshBuilder()
    half = length / 2
    builder.prism([(-half, -0.3), (half, -0.3), (half, 0.3), (-half, 0.3)], 0.55, 1.25, "foliage_vine", bottom=False)
    return builder


def terrace(seed, length=18.0, depth=7.0, height=1.8):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.box((-length / 2, -0.6, -2.5), (length / 2, 0.0, height), "weathered_ashlar", bottom=False)
    tinted(builder, (0.56, 0.47, 0.35), lambda: builder.box((-length / 2, 0.0, height - 0.6),
                                                            (length / 2, depth, height - 0.05), MATTE, bottom=False))
    if rng.random() < 0.6:
        for index in range(3):
            builder.merge(vine_row(length - 2.0), Matrix.Translation((0.0, 1.3 + index * 2.0, height - 0.05)))
    else:
        for index in range(3):
            x = -length / 2 + 3.0 + index * 6.0
            lobe(builder, (x, 3.5, height + 2.6), 1.9, 2.4, "foliage_olive", 6, seed + index)
    return builder
