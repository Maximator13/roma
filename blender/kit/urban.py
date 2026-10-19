import math
import random

from mathutils import Matrix

from .buildings import ASHLAR, TILES, VOID, WEATHERED, courtyard_house, garden_shrub, lobe, trunk, vine_row
from .geometry import MeshBuilder, placement
from .orders import gable_ends

PLASTERS = ["plaster", "plaster_white", "plaster_ochre", "plaster_rose", "plaster_cream", "plaster_white",
            "plaster_grey"]
ROOF_TINTS = [(1.0, 1.0, 1.0), (0.9, 0.84, 0.8), (0.96, 0.9, 0.78), (0.82, 0.74, 0.7), (1.0, 0.92, 0.86)]
WOODS = [(0.42, 0.30, 0.20), (0.36, 0.40, 0.32), (0.50, 0.36, 0.24), (0.30, 0.27, 0.24), (0.48, 0.25, 0.18)]
STONE_WHITE = (1.0, 1.0, 0.98)
CLOTH = [((0.95, 0.92, 0.84), (0.70, 0.30, 0.22)), ((0.92, 0.86, 0.72), (0.55, 0.50, 0.36)),
         ((0.95, 0.92, 0.84), (0.42, 0.48, 0.56))]


def tinted(builder, color, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, color)


def panel(builder, x0, x1, z0, z1, y, facing, material, color=None):
    corners = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    if color is None:
        builder.oriented(corners, (0, facing, 0), material)
    else:
        tinted(builder, color, lambda: builder.oriented(corners, (0, facing, 0), material))


def roof(builder, x0, x1, hd, height, top, kind, tint, wall):
    eave = height - 0.16
    overhang = 0.4
    if kind == "hip" and (x1 - x0) > 2 * hd + 0.5:
        ridge0, ridge1 = x0 + hd, x1 - hd
        corners = {"front": [(x0 - 0.15, -hd - overhang, eave), (x1 + 0.15, -hd - overhang, eave), (ridge1, 0.0, top),
                             (ridge0, 0.0, top)],
                   "back": [(x1 + 0.15, hd + overhang, eave), (x0 - 0.15, hd + overhang, eave), (ridge0, 0.0, top),
                            (ridge1, 0.0, top)]}
        normals = {"front": (0, -1, 1), "back": (0, 1, 1)}
        for key, quad in corners.items():
            tinted(builder, tint, lambda quad=quad, key=key: builder.oriented(quad, normals[key], TILES))
        tinted(builder, tint, lambda: builder.oriented([(x0 - 0.15, hd + overhang, eave), (x0 - 0.15, -hd - overhang,
                                                                                             eave), (ridge0, 0.0, top)],
                                                      (-1, 0, 1), TILES))
        tinted(builder, tint, lambda: builder.oriented([(x1 + 0.15, -hd - overhang, eave), (x1 + 0.15, hd + overhang,
                                                                                             eave), (ridge1, 0.0, top)],
                                                      (1, 0, 1), TILES))
        return
    for side in (-1, 1):
        quad = [(x0 - 0.15, side * (hd + overhang), eave), (x1 + 0.15, side * (hd + overhang), eave),
                (x1 + 0.15, 0.0, top), (x0 - 0.15, 0.0, top)]
        tinted(builder, tint, lambda quad=quad, side=side: builder.oriented(quad, (0, side, 1), TILES))
    gable_ends(builder, x0, x1, hd, height, top, wall, along_axis="x")


def awning(builder, x0, x1, hd, kind, rng):
    front = -hd - 2.1
    if kind == "tile":
        top_quad = [(x0, -hd, 3.15), (x1, -hd, 3.15), (x1, front, 2.78), (x0, front, 2.78)]
        builder.oriented(top_quad, (0, -0.2, 1), TILES)
        tinted(builder, WOODS[0], lambda: builder.oriented(top_quad, (0, 0.2, -1), "plaster"))
        for x in (x0 + 0.3, (x0 + x1) / 2, x1 - 0.3):
            tinted(builder, WOODS[2], lambda x=x: builder.box((x - 0.1, front + 0.1, -0.2), (x + 0.1, front + 0.3, 2.78),
                                                              "plaster", bottom=False, top=False))
        return
    light, dark = CLOTH[rng.randrange(len(CLOTH))]
    stripes = 8
    for index in range(stripes):
        a = x0 + (x1 - x0) * index / stripes
        b = x0 + (x1 - x0) * (index + 1) / stripes
        tone = light if index % 2 else dark
        quad = [(a, -hd, 3.0), (b, -hd, 3.0), (b, front + 0.3, 2.55), (a, front + 0.3, 2.55)]
        tinted(builder, tone, lambda quad=quad: builder.oriented(quad, (0, -0.2, 1), "plaster"))
        tinted(builder, tone, lambda quad=quad: builder.oriented(quad, (0, 0.2, -1), "plaster"))
        panel(builder, a, b, 2.25, 2.55, front + 0.3, -1, "plaster", tone)
    for x in (x0 + 0.2, x1 - 0.2):
        tinted(builder, WOODS[1], lambda x=x: builder.box((x - 0.05, front + 0.25, -0.2), (x + 0.05, front + 0.35, 2.55),
                                                          "plaster", bottom=False, top=False))


def town_unit(builder, x0, width, depth, height, wall, roof_kind, shops, windows, awning_kind, balcony, roof_tint,
              rng):
    hd = depth / 2
    x1 = x0 + width
    builder.box((x0, -hd, -3.0), (x1, hd, height), wall, bottom=False, top=False)
    top = height + hd * 0.4
    roof(builder, x0, x1, hd, height, top, roof_kind, roof_tint, wall)
    front = -hd - 0.02
    shutter = WOODS[rng.randrange(len(WOODS))]
    if shops:
        spacing = width / shops
        for index in range(shops):
            x = x0 + spacing * (index + 0.5)
            opening = spacing * 0.64
            panel(builder, x - opening / 2, x + opening / 2, 0.0, 2.75, front, -1, VOID)
            panel(builder, x - opening / 2 - 0.12, x + opening / 2 + 0.12, 2.75, 3.0, front - 0.01, -1, wall,
                  STONE_WHITE)
            counter = opening * 0.55
            left = x - opening / 2 if index % 2 == 0 else x + opening / 2 - counter
            tinted(builder, STONE_WHITE, lambda left=left, counter=counter: builder.box(
                (left, -hd - 0.6, -0.3), (left + counter, -hd + 0.05, 1.0), wall, bottom=False))
        if awning_kind:
            awning(builder, x0 + 0.2, x1 - 0.2, hd, awning_kind, rng)
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
            if (index + floor) % 3 != 2:
                panel(builder, x - 0.62, x - 0.3, z, z + 0.9, front - 0.01, -1, wall, shutter)
                panel(builder, x + 0.3, x + 0.62, z, z + 0.9, front - 0.01, -1, wall, shutter)
    if balcony and floors >= 2:
        tinted(builder, WOODS[0], lambda: builder.box((x0 + 0.8, -hd - 1.0, 3.15), (x1 - 0.8, -hd, 3.3), wall))
        rail = [(x0 + 0.8, -hd - 1.0, 3.3), (x1 - 0.8, -hd - 1.0, 3.3), (x1 - 0.8, -hd - 1.0, 4.2),
                (x0 + 0.8, -hd - 1.0, 4.2)]
        tinted(builder, WOODS[0], lambda: builder.oriented(rail, (0, -1, 0), wall))
        tinted(builder, WOODS[3], lambda: builder.oriented(rail, (0, 1, 0), wall))
    back = hd + 0.02
    for index in range(2):
        x = x0 + width * (0.25 + 0.5 * index)
        panel(builder, x - 0.3, x + 0.3, height - 2.0, height - 1.2, back, 1, VOID)


def row_template(seed, tabernae=False, depth=11.0, units=2):
    rng = random.Random(seed)
    builder = MeshBuilder()
    width = 16.0
    for index in range(units):
        x0 = -width * units / 2 + width * index
        heights = [6.4, 7.0, 8.2, 9.8] if tabernae else [5.2, 6.4, 7.0, 8.2, 9.8]
        height = rng.choice(heights)
        shops = 3 if (tabernae or rng.random() < 0.35) else 0
        kind = rng.choice(["tile", "cloth", "tile"]) if shops else None
        town_unit(builder, x0, width, depth, height, rng.choice(PLASTERS), rng.choice(["gable", "hip", "hip"]), shops,
                  3 if height > 6.5 else 2, kind, height >= 8.0 and rng.random() < 0.6, rng.choice(ROOF_TINTS), rng)
    return builder


def single_house(seed, width=14.0, depth=9.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    height = rng.choice([4.2, 5.0, 5.6])
    town_unit(builder, -width / 2, width, depth, height, rng.choice(PLASTERS), rng.choice(["gable", "hip"]), 0, 2, None,
              False, rng.choice(ROOF_TINTS), rng)
    yard = (0.86, 0.8, 0.72)
    for x0, x1 in ((-width / 2, -width / 2 + 0.5), (width / 2 - 0.5, width / 2)):
        tinted(builder, yard, lambda x0=x0, x1=x1: builder.box((x0, depth / 2, -1.0), (x1, depth / 2 + 6.0, 1.8),
                                                               "plaster", bottom=False))
    tinted(builder, yard, lambda: builder.box((-width / 2, depth / 2 + 5.5, -1.0), (width / 2, depth / 2 + 6.0, 1.8),
                                              "plaster", bottom=False))
    for index in range(3):
        garden_shrub(builder, -width / 2 + 2.5 + index * 4.0, depth / 2 + 3.0, 1.6, seed + index)
    lobe(builder, (width / 2 - 3.0, depth / 2 + 3.0, 3.0), 2.2, 2.6, "foliage_olive", 6, seed)
    trunk(builder, 2.0, 0.15, at=(width / 2 - 3.0, depth / 2 + 3.0, 0.0))
    return builder


def peristyle(builder, cw, cd, wall_height, seed):
    rng = random.Random(seed)
    inset = 1.9
    px, py = cw - inset, cd - inset
    posts = []
    count_x = max(int(2 * px / 3.0), 2)
    count_y = max(int(2 * py / 3.0), 2)
    for index in range(count_x + 1):
        x = -px + 2 * px * index / count_x
        posts.extend([(x, -py), (x, py)])
    for index in range(1, count_y):
        y = -py + 2 * py * index / count_y
        posts.extend([(-px, y), (px, y)])
    square = [(-0.2, -0.2), (0.2, -0.2), (0.2, 0.2), (-0.2, 0.2)]
    for x, y in posts:
        outline = [(x + a, y + b) for a, b in square]
        tinted(builder, (0.78, 0.36, 0.28), lambda outline=outline: builder.prism(outline, 0.0, 1.0, "plaster",
                                                                                   top=False, bottom=False))
        tinted(builder, STONE_WHITE, lambda outline=outline: builder.prism(outline, 1.0, 3.2, "plaster", bottom=False))
    low = 3.3
    high = min(4.4, wall_height - 0.8)
    outer = [(-cw, -cd), (cw, -cd), (cw, cd), (-cw, cd)]
    inner = [(-px - 0.3, -py - 0.3), (px + 0.3, -py - 0.3), (px + 0.3, py + 0.3), (-px - 0.3, py + 0.3)]
    for index in range(4):
        a, b = outer[index], outer[(index + 1) % 4]
        c, d = inner[(index + 1) % 4], inner[index]
        quad = [(a[0], a[1], high), (b[0], b[1], high), (c[0], c[1], low), (d[0], d[1], low)]
        builder.oriented(quad, (0, 0, 1), TILES)
        tinted(builder, WOODS[0], lambda quad=quad: builder.oriented(quad, (0, 0, -1), "plaster"))
    tinted(builder, STONE_WHITE, lambda: builder.box((-1.6, -1.1, -0.2), (1.6, 1.1, 0.35), "plaster", bottom=False))
    builder.polygon([(-1.4, -0.9, 0.36), (1.4, -0.9, 0.36), (1.4, 0.9, 0.36), (-1.4, 0.9, 0.36)], "plaster",
                    color=(0.42, 0.52, 0.56))
    for index in range(4):
        angle = 2 * math.pi * index / 4 + math.pi / 4 + rng.uniform(-0.3, 0.3)
        garden_shrub(builder, math.cos(angle) * (px - 1.6), math.sin(angle) * (py - 1.6), rng.uniform(1.0, 1.6),
                     seed + index)
    lobe(builder, (px - 2.2, py - 2.0, 4.2), 2.4, 3.2, "foliage_plane", 6, seed)
    trunk(builder, 3.0, 0.16, at=(px - 2.2, py - 2.0, 0.0))


def domus(seed, width=32.0, depth=30.0, court_width=13.0, court_depth=12.0, height=6.5, wall="plaster_white"):
    builder = courtyard_house(width, depth, court_width, court_depth, height, wall)
    builder.paint(TILES, random.Random(seed).choice(ROOF_TINTS))
    peristyle(builder, court_width / 2, court_depth / 2, height, seed)
    return builder


def kitchen_garden(seed, width=28.0, depth=26.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    for (x0, y0), (x1, y1) in (((-hw, -hd), (hw, -hd + 0.6)), ((-hw, hd - 0.6), (hw, hd)),
                               ((-hw, -hd), (-hw + 0.6, hd)), ((hw - 0.6, -hd), (hw, hd))):
        tinted(builder, (0.86, 0.8, 0.72), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0, y0, -1.5), (x1, y1, 1.6), "plaster", bottom=False))
    row_template_unit = MeshBuilder()
    town_unit(row_template_unit, -4.0, 8.0, 6.0, 3.6, rng.choice(PLASTERS), "gable", 0, 1, None, False,
              rng.choice(ROOF_TINTS), rng)
    builder.merge(row_template_unit, placement(-hw + 5.0, hd - 4.0, 0.0))
    for index in range(5):
        y = -hd + 3.0 + index * 2.6
        tinted(builder, (0.9, 1.0, 0.85) if index % 2 else (1.0, 0.95, 0.9), lambda y=y: builder.box(
            (-hw + 2.0, y - 0.6, -0.2), (hw - 12.0, y + 0.6, 0.35), "garden_green", bottom=False))
    for index in range(3):
        x, y = hw - 4.0 - index * 3.5, -hd + 4.0 + index * 5.5
        trunk(builder, 1.6, 0.15, at=(x, y, 0.0))
        lobe(builder, (x, y, 2.8), 2.0, 2.6, "foliage_olive", 6, seed + index)
    for index in range(2):
        builder.merge(vine_row(8.0), placement(hw - 7.0, hd - 3.0 - index * 2.2, 0.0))
    return builder


def terrace(seed, length=18.0, depth=7.0, height=1.8):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.box((-length / 2, -0.6, -2.5), (length / 2, 0.0, height), WEATHERED, bottom=False)
    tinted(builder, (0.56, 0.47, 0.35), lambda: builder.box((-length / 2, 0.0, height - 0.6),
                                                            (length / 2, depth, height - 0.05), "matte", bottom=False))
    if rng.random() < 0.6:
        for index in range(3):
            builder.merge(vine_row(length - 2.0), placement(0.0, 1.3 + index * 2.0, height - 0.05))
    else:
        for index in range(3):
            x = -length / 2 + 3.0 + index * 6.0
            lobe(builder, (x, 3.5, height + 2.6), 1.9, 2.4, "foliage_olive", 6, seed + index)
    return builder


def street_segment(paved=True, length=16.0, width=8.0):
    builder = MeshBuilder()
    half = length / 2
    road = 2.6
    walk = width / 2 + 0.3
    surface = "paving" if paved else "arena_sand"
    tone = (1.0, 1.0, 1.0) if paved else (0.86, 0.8, 0.72)
    tinted(builder, tone, lambda: builder.box((-half, -road, -0.6), (half, road, 0.12), surface, bottom=False))
    for side in (-1, 1):
        y0, y1 = sorted((side * 0.65, side * 0.75))
        tinted(builder, (0.8, 0.77, 0.74), lambda y0=y0, y1=y1: builder.polygon(
            [(-half, y0, 0.125), (half, y0, 0.125), (half, y1, 0.125), (-half, y1, 0.125)], surface))
        y0, y1 = sorted((side * road, side * walk))
        builder.box((-half, y0, -0.6), (half, y1, 0.36 if paved else 0.28), WEATHERED, bottom=False)
        if paved:
            panel(builder, 2.5, 2.85, 0.14, 0.27, side * (road + 0.01), -side, VOID)
    return builder


def street_node(paved=True, width=8.0):
    builder = MeshBuilder()
    half = width / 2 + 0.3
    surface = "street_paving" if paved else "arena_sand"
    tone = (1.0, 1.0, 1.0) if paved else (0.86, 0.8, 0.72)
    tinted(builder, tone, lambda: builder.box((-half, -half, -0.6), (half, half, 0.12), surface, bottom=False))
    if paved:
        for angle in range(4):
            frame = Matrix.Rotation(angle * math.pi / 2, 4, "Z")
            for y in (-1.45, 0.0, 1.45):
                builder.box((half + 0.4, y - 0.45, -0.2), (half + 1.05, y + 0.45, 0.4), ASHLAR, matrix=frame,
                            bottom=False)
    return builder


def street_fountain():
    builder = MeshBuilder()
    for (x0, y0), (x1, y1) in (((-0.95, -0.65), (0.95, -0.47)), ((-0.95, 0.47), (0.95, 0.65)),
                               ((-0.95, -0.47), (-0.77, 0.47)), ((0.77, -0.47), (0.95, 0.47))):
        builder.box((x0, y0, -0.3), (x1, y1, 0.85), ASHLAR, bottom=False)
    builder.polygon([(-0.77, -0.47, 0.72), (0.77, -0.47, 0.72), (0.77, 0.47, 0.72), (-0.77, 0.47, 0.72)], "water")
    builder.box((-0.28, 0.65, -0.3), (0.28, 1.0, 1.45), ASHLAR, bottom=False)
    builder.box((-0.34, 0.6, 1.45), (0.34, 1.05, 1.6), ASHLAR, bottom=False)
    panel(builder, -0.12, 0.12, 1.0, 1.24, 0.64, -1, ASHLAR, (0.55, 0.52, 0.48))
    builder.polygon([(-0.03, 0.62, 1.04), (0.03, 0.62, 1.04), (0.03, 0.2, 0.73), (-0.03, 0.2, 0.73)], "water")
    return builder


def velum(outer_a, outer_b, inner_a, inner_b, outer_z, inner_z, angles, extent=0.55, sag=1.1):
    builder = MeshBuilder()
    count = len(angles)
    rows = 4
    for index in range(count):
        t0 = angles[index]
        t1 = angles[(index + 1) % count] + (2 * math.pi if index == count - 1 else 0.0)
        columns = []
        for t in (t0, t1):
            column = []
            for row in range(rows + 1):
                s = extent * row / rows
                ax = outer_a * math.cos(t) * (1 - s) + inner_a * math.cos(t) * s
                ay = outer_b * math.sin(t) * (1 - s) + inner_b * math.sin(t) * s
                z = outer_z + (inner_z - outer_z) * s - sag * math.sin(math.pi * row / rows) * 0.5
                column.append((ax, ay, z))
            columns.append(column)
        first = len(builder.polygons)
        builder.surface([[columns[0][row], columns[1][row]] for row in range(rows + 1)], "velum_linen",
                        facing=(0, 0, 1))
        builder.tint(first, (1.0, 1.0, 1.0) if index % 2 else (0.93, 0.86, 0.74))
    return builder
