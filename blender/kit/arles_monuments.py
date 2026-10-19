import math
import os
import random

import bpy
from mathutils import Matrix, Vector

from .arles_details import raking_cornice, side_antefixes
from .buildings import ASHLAR, TILES, VOID, WEATHERED, arched_wall, straight_moulding
from .geometry import MeshBuilder, newell_normal, placement
from .materials import linear_color, poly_haven_asset, principled_material, recolored
from .orders import (ENGAGED_HALF, STONE, column, frames_along, gable_roof, pilaster, podium,
                     simple_entablature_profile)

ROUGH = "arles_stone"
PLANK = "plank_wood"
MARBLE = "lens_smooth"
WOOD_DOOR = "dark_wood"
EXTRA_TEXTURES = {
    ROUGH: dict(asset="medieval_blocks_02", color=(0.77, 0.72, 0.62), contrast=0.6, roughness=0.88),
    PLANK: dict(asset="brown_planks_03", color=(0.62, 0.55, 0.45), contrast=0.6, roughness=0.85),
}
STONE_TONES = {ROUGH: 1.0, ASHLAR: 0.87, WEATHERED: 0.95, MARBLE: 0.93}
NORMAL_FREE = ("paving", "weathered_ashlar")


def strip_normals(name):
    material = bpy.data.materials.get(name)
    if material is None or not material.use_nodes:
        return
    nodes = material.node_tree.nodes
    for node in list(nodes):
        if node.type == "NORMAL_MAP":
            for link in list(node.inputs["Color"].links):
                nodes.remove(link.from_node)
            nodes.remove(node)


def arles_materials(cache_dir, tiles, credits):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    texture_dir = os.path.join(cache_dir, "textures")
    for name, spec in EXTRA_TEXTURES.items():
        diffuse, _, width_metres = poly_haven_asset(spec["asset"], source_dir, credits)
        signature = "".join(f"{round(value * 100):02d}" for value in (*spec["color"], spec["contrast"]))
        image = recolored(diffuse, spec["color"], spec["contrast"], os.path.join(texture_dir, f"{name}_{signature}.jpg"),
                          name)
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, image)
        tiles[name] = width_metres
    principled_material("river_water", linear_color((0.26, 0.24, 0.17)), 0.25)
    tiles["river_water"] = 8.0
    principled_material("reed", linear_color((0.55, 0.56, 0.33)), 0.9)
    tiles["reed"] = 2.0
    for name in NORMAL_FREE:
        strip_normals(name)


def weather(builder, seed=0, strength=0.14, low=1.6):
    rng = random.Random(seed)
    names = builder.materials
    for index, (polygon, material_index) in enumerate(zip(builder.polygons, builder.polygon_materials)):
        tone_factor = STONE_TONES.get(names[material_index])
        if tone_factor is None:
            continue
        corners = [builder.positions[point] for point in polygon]
        normal = newell_normal(corners)
        bottom = min(corner[2] for corner in corners)
        factor = tone_factor * (1.0 - strength * rng.random())
        if normal.z < -0.3:
            factor *= 0.78
        if bottom < low:
            factor *= 0.84 + 0.16 * min(max(bottom, 0.0) / max(low, 0.1), 1.0)
        streak = 0.5 + 0.5 * math.sin(sum(corner[0] + corner[1] for corner in corners) / len(corners) * 0.9 + seed)
        factor *= 0.95 + 0.05 * streak
        green, blue = 0.98, 0.94
        if bottom < low * 0.35 and abs(normal.z) < 0.5 and rng.random() < 0.6:
            factor *= 0.9
            green, blue = 1.02, 0.86
        current = builder.polygon_colors[index] or (1.0, 1.0, 1.0)
        builder.polygon_colors[index] = (current[0] * factor, current[1] * factor * green, current[2] * factor * blue)
    return builder


def tinted(builder, color, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, color)


def ring_frames(radius, start, sweep, count, z=0.0):
    frames = []
    for index in range(count):
        angle = start + sweep * (index + 0.5) / count
        frames.append(Matrix.Translation((radius * math.cos(angle), radius * math.sin(angle), z))
                      @ Matrix.Rotation(angle - math.pi / 2, 4, "Z"))
    return frames


ORCHESTRA = 15.3
CAVEA = 51.0
FACADE_TOP = 21.0
TREAD = 0.82
BLOCKS = ((19, 0.4, 1.5), (8, 0.42, 1.3), (6, 0.44, 0.0))
STAIRS = 7
STAIR_SWEEP = math.radians(2.2)
CUNEUS_SWEEP = (math.pi - STAIRS * STAIR_SWEEP) / (STAIRS - 1)
NICHE_MARBLES = [(0.62, 0.38, 0.32), (0.52, 0.58, 0.5), (0.78, 0.66, 0.46)]
LEVEL_MARBLES = [(0.96, 0.88, 0.88), (0.82, 0.88, 0.78), (0.98, 0.86, 0.64)]


def theatre_profile():
    points = [(ORCHESTRA, -0.6), (ORCHESTRA, 0.35), (ORCHESTRA + 1.4, 0.35), (ORCHESTRA + 1.4, 1.25)]
    r, z = ORCHESTRA + 1.4, 1.25
    for count, rise, gap in BLOCKS:
        for _ in range(count):
            z += rise
            points.append((r, z))
            r += TREAD
            points.append((r, z))
        if gap:
            points.append((r + gap, z))
            z += 1.1
            points.append((r + gap, z))
            r += gap
    return points, r, z


def theatre_rows():
    rows = []
    r, z = ORCHESTRA + 1.4, 1.25
    for count, rise, gap in BLOCKS:
        for index in range(count):
            z += rise
            rows.append((r, z, rise if index > 0 else None))
            r += TREAD
        if gap:
            r += gap
            z += 1.1
    return rows


def cuneus_ranges():
    ranges = []
    angle = math.pi
    for index in range(2 * STAIRS - 1):
        sweep = STAIR_SWEEP if index % 2 == 0 else CUNEUS_SWEEP
        if index % 2:
            ranges.append((angle, angle + sweep))
        angle += sweep
    return ranges


def theatre_cavea():
    builder = MeshBuilder()
    profile, top_radius, top_z = theatre_profile()
    outline = profile + [(CAVEA - 1.0, top_z), (CAVEA - 1.0, -2.5)]
    angle = math.pi
    for index in range(2 * STAIRS - 1):
        is_stair = index % 2 == 0
        sweep = STAIR_SWEEP if is_stair else CUNEUS_SWEEP
        tinted(builder, (0.82, 0.79, 0.74) if is_stair else (1.0, 1.0, 1.0),
               lambda angle=angle, sweep=sweep, is_stair=is_stair: builder.lathe(
                   list(reversed(outline)), 1 if is_stair else 6, WEATHERED, smooth=False, start=angle, sweep=sweep,
                   caps=False))
        if is_stair:
            middle = angle + sweep / 2
            for r, z, _ in theatre_rows():
                radius = r + TREAD * 0.75
                width = 2 * radius * math.sin(sweep / 2) * 0.98
                frame = placement(radius * math.cos(middle), radius * math.sin(middle), 0.0, middle + math.pi / 2)
                tinted(builder, (0.8, 0.77, 0.72), lambda frame=frame, width=width, z=z: builder.centered_box(
                    (0.0, 0.0, z + 0.1), (width, TREAD * 0.5, 0.2), WEATHERED, matrix=frame, bottom=False))
        angle += sweep
    for outer, inner, colour in ((8.0, 0.0, (0.64, 0.7, 0.6)), (14.5, 8.0, (0.9, 0.7, 0.66)),
                                 (ORCHESTRA, 14.5, (0.97, 0.95, 0.9))):
        first = len(builder.polygons)
        for k in range(24):
            a0, a1 = math.pi + math.pi * k / 24, math.pi + math.pi * (k + 1) / 24
            quad = [(r * math.cos(a), r * math.sin(a), 0.03) for r, a in ((outer, a0), (outer, a1), (inner, a1),
                                                                          (inner, a0))]
            quad = quad if inner > 0 else quad[:3]
            builder.face(builder.points(quad), "paving", False, [(x, y) for x, y, _ in quad])
        builder.tint(first, colour)
    tinted(builder, (0.8, 0.58, 0.54), lambda: builder.box((-ORCHESTRA, 0.0, -0.6), (ORCHESTRA, 1.2, 0.0), "paving",
                                                             bottom=False))
    start = (ORCHESTRA, 1.6)
    slope = max((z + 0.6 - start[1]) / (r - start[0]) for r, z in profile if r > start[0] + 0.5)
    crest = (top_radius, start[1] + slope * (top_radius - start[0]))
    for side in (-1, 1):
        for outline_wall in ([start, crest, (top_radius, -2.5), (ORCHESTRA, -2.5)],
                             [(top_radius, top_z), (CAVEA - 1.0, top_z), (CAVEA - 1.0, -2.5), (top_radius, -2.5)]):
            wall = [(side * r, 0.0, z) for r, z in outline_wall]
            builder.oriented(wall, (0, 1, 0), ROUGH)
            builder.oriented(list(reversed(wall)), (0, -1, 0), ROUGH)
        (r0, z0), (r1, z1) = start, crest
        top = [(side * r0, 0.35, z0 + 0.3), (side * r1, 0.35, z1 + 0.3), (side * r1, -0.85, z1 + 0.3),
               (side * r0, -0.85, z0 + 0.3)]
        builder.oriented(top, (0, 0, 1), ASHLAR)
        for y in (0.35, -0.85):
            face = [(side * r0, y, z0 - 0.05), (side * r1, y, z1 - 0.05), (side * r1, y, z1 + 0.3),
                    (side * r0, y, z0 + 0.3)]
            builder.oriented(face, (0, 1 if y > 0 else -1, 0), ASHLAR)
        end = [(side * r1, 0.35, z1 + 0.3), (side * r1, -0.85, z1 + 0.3), (side * r1, -0.85, top_z),
               (side * r1, 0.35, top_z)]
        builder.oriented(end, (side, 0, 0), ROUGH)
    roof = [(top_radius - 0.2, top_z + 3.6), (CAVEA + 0.4, FACADE_TOP + 0.3)]
    for points in (roof, list(reversed(roof))):
        tinted(builder, (0.82, 0.74, 0.62), lambda points=points: builder.lathe(points, 28, TILES, smooth=False,
                                                                                start=math.pi, sweep=math.pi,
                                                                                caps=False))
    portico = ring_frames(top_radius + 0.5, math.pi, math.pi, 28, top_z)
    return weather(builder, 5), portico, top_z


def theatre_bay(width):
    builder = MeshBuilder()
    half = width / 2
    opening = min(1.65, half - 0.75)
    levels = [(0.0, 7.4, 4.6, "tuscan", 0.78), (7.4, 14.2, 11.6, "tuscan", 0.7), (14.2, FACADE_TOP, 17.6, None, 0.0)]
    for z0, z1, impost, order, diameter in levels:
        arched_wall(builder, -half, half, -1.3, 0.0, z0, z1 - 0.8, [(0.0, opening if order else 1.0, impost)], ROUGH,
                    segments=7, foundation=4.0 if z0 == 0 else 0.0, sill=z0 + 1.0 if z0 > 0 else None)
        builder.box((-half, -1.3, z1 - 0.8), (half, -0.3, z1), ROUGH, bottom=False)
        straight_moulding(builder, -half, half, z1 - 0.8, simple_entablature_profile(0.8, 0.32), ASHLAR)
        if order:
            builder.merge(column(order, diameter, z1 - z0 - 0.8, detail="low", material=ASHLAR, arc=ENGAGED_HALF),
                          placement(-half, 0.05, z0))
        builder.box((-opening, -0.95, z0), (opening, -0.92, z1 - 1.0), VOID, bottom=False)
    return weather(builder, 7)


def shifted_roof(builder, offset, *args, **kwargs):
    roof = MeshBuilder()
    gable_roof(roof, *args, **kwargs)
    builder.merge(roof, Matrix.Translation(offset))


def framed_niche(builder, x, wall_front, z0, z1, width, colour):
    half = width / 2
    tinted(builder, colour, lambda: builder.box((x - half, wall_front - 0.05, z0), (x + half, wall_front - 0.02, z1),
                                                MARBLE, bottom=False))
    for side in (-1, 1):
        edge = x + side * half
        builder.box((min(edge, edge + side * 0.25), wall_front - 0.6, z0 - 0.15),
                    (max(edge, edge + side * 0.25), wall_front, z1 + 0.3), MARBLE, bottom=False)
    builder.box((x - half - 0.25, wall_front - 0.6, z1), (x + half + 0.25, wall_front, z1 + 0.3), MARBLE)
    builder.box((x - half - 0.25, wall_front - 0.6, z0 - 0.15), (x + half + 0.25, wall_front, z0), MARBLE,
                bottom=False)


def wooden_door(builder, x, y, z0, width, height, facing=-1):
    half = width / 2
    depth = 0.06 * facing
    tinted(builder, (0.78, 0.62, 0.46), lambda: builder.box((x - half, min(y, y + depth), z0),
                                                            (x + half, max(y, y + depth), z0 + height), WOOD_DOOR,
                                                            bottom=False))
    for side in (-1, 1):
        builder.box((x + side * half - 0.2, min(y, y + 0.25 * facing), z0),
                    (x + side * half + 0.2, max(y, y + 0.25 * facing), z0 + height + 0.3), ASHLAR, bottom=False)
    builder.box((x - half - 0.35, min(y, y + 0.3 * facing), z0 + height), (x + half + 0.35, max(y, y + 0.3 * facing),
                                                                           z0 + height + 0.5), ASHLAR)


def theatre_stage():
    builder = MeshBuilder()
    stage_z = 1.35
    front = 1.2
    wall_front = 8.4
    exedra = 4.5
    exedra_top = stage_z + 7.9
    builder.box((-25.0, front, -0.6), (25.0, front + 0.6, stage_z), ASHLAR, bottom=False)
    for x in range(-24, 25, 4):
        tinted(builder, (0.62, 0.56, 0.5), lambda x=x: builder.box((x - 0.8, front - 0.05, 0.25), (x + 0.8, front, 1.1),
                                                                    MARBLE, bottom=False))
    tinted(builder, (0.78, 0.64, 0.5), lambda: builder.box((-25.0, front + 0.6, stage_z - 0.2), (25.0, wall_front,
                                                                                                 stage_z), PLANK,
                                                           bottom=False))
    floor = [(exedra * math.cos(math.pi * i / 10), wall_front + exedra * math.sin(math.pi * i / 10), stage_z)
             for i in range(11)]
    tinted(builder, (0.78, 0.64, 0.5), lambda: builder.oriented(list(reversed(floor)), (0, 0, 1), PLANK))
    face = (0.96, 0.92, 0.85)
    for x0, x1 in ((-27.0, -exedra), (exedra, 27.0)):
        builder.box((x0, wall_front, -0.6), (x1, 17.0, FACADE_TOP - 0.6), ROUGH, bottom=False, top=False)
        tinted(builder, face, lambda x0=x0, x1=x1: builder.box((x0, wall_front - 0.02, stage_z),
                                                                (x1, wall_front, FACADE_TOP - 0.6), MARBLE,
                                                                bottom=False, top=False))
    builder.box((-exedra, wall_front + exedra, -0.6), (exedra, 17.0, FACADE_TOP - 0.6), ROUGH, bottom=False, top=False)
    builder.box((-exedra, wall_front, exedra_top), (exedra, wall_front + exedra, FACADE_TOP - 0.6), ROUGH, top=False)
    tinted(builder, face, lambda: builder.box((-exedra, wall_front - 0.02, exedra_top), (exedra, wall_front,
                                                                                          FACADE_TOP - 0.6), MARBLE,
                                              bottom=False, top=False))
    shell = Matrix.Translation((0.0, wall_front, 0.0))
    tinted(builder, NICHE_MARBLES[1], lambda: builder.lathe([(exedra, exedra_top), (exedra, stage_z - 0.2)], 12, MARBLE,
                                                            smooth=True, matrix=shell, start=0.0, sweep=math.pi,
                                                            caps=False))
    wooden_door(builder, 0.0, wall_front + 3.95, stage_z, 3.4, 6.0)
    for x in (-13.0, 13.0):
        wooden_door(builder, x, wall_front - 0.02, stage_z, 2.4, 4.6)
    level_heights = [(stage_z + 1.0, 6.4, 1.2), (stage_z + 8.6, 5.0, 1.0), (stage_z + 14.6, 3.8, 0.9)]
    column_frames = {0: [], 1: [], 2: []}
    statue_frames = []
    xs = [-25.0, -22.0, -17.6, -15.4, -10.6, -8.4, -6.8, -2.6, 2.6, 6.8, 8.4, 10.6, 15.4, 17.6, 22.0, 25.0]
    kinds = ["marble", "toga", "marble", "toga", "venus", "toga", "marble", "toga", "marble", "toga"]
    for level, (base, height, beam) in enumerate(level_heights):
        positions = [(-4.9 if x == -2.6 else 4.9 if x == 2.6 else x) for x in xs] if level == 0 else xs
        for x0, x1 in ((-26.0, -exedra), (exedra, 26.0)) if level == 0 else ((-26.0, 26.0),):
            builder.box((x0, wall_front - 2.2, base - (1.0 if level == 0 else 0.0)), (x1, wall_front, base), ASHLAR,
                        bottom=False)
        top = base + height
        for a, b in zip(positions[0::2], positions[1::2]):
            builder.box((a - 0.6, wall_front - 3.7, base - (1.0 if level == 0 else 0.5)), (b + 0.6, wall_front - 2.2,
                                                                                        base), ASHLAR, bottom=False)
            builder.box((a - 0.6, wall_front - 3.7, top), (b + 0.6, wall_front - 2.0, top + beam * 0.7), STONE)
            straight_moulding(builder, a - 0.6, b + 0.6, top + beam * 0.7, simple_entablature_profile(beam * 0.3, 0.3),
                              STONE, y=wall_front - 3.7)
        for x in positions:
            column_frames[level].append(placement(x, wall_front - 1.4, base))
            column_frames[level].append(placement(x, wall_front - 3.0, base))
        builder.box((-26.0, wall_front - 2.0, top), (26.0, wall_front, top + beam * 0.7), STONE)
        straight_moulding(builder, -26.0, 26.0, top + beam * 0.7, simple_entablature_profile(beam * 0.3, 0.4), STONE,
                          y=wall_front - 2.0)
        for a, b in zip(positions[1::2], positions[2::2]):
            middle = (a + b) / 2
            if abs(middle) < 0.1 or b - a < 3.0 or (level == 0 and abs(abs(middle) - 13.0) < 0.5):
                continue
            z0, z1 = base + 0.15, base + height * 0.78
            framed_niche(builder, middle, wall_front, z0, z1, 1.8, NICHE_MARBLES[(level + int(middle)) % 3])
            statue_frames.append((kinds[len(statue_frames) % len(kinds)],
                                  placement(middle, wall_front - 0.35, z0, math.pi)))
    augustus_base = level_heights[1][0]
    framed_niche(builder, 0.0, wall_front, augustus_base + 0.15, augustus_base + 4.6, 3.4, NICHE_MARBLES[0])
    statue_frames.append(("augustus", placement(0.0, wall_front - 1.0, augustus_base, math.pi)))
    for side in (-1, 1):
        x0, x1 = sorted((side * 27.0, side * 51.0))
        outer = x1 if side > 0 else x0
        builder.box((x0, 4.0, -0.6), (x1, 18.0, 17.0), ROUGH, bottom=False, top=False)
        for z in (2.0, 8.5):
            for y in (7.0, 11.0, 15.0):
                builder.box((outer - 0.03, y - 0.8, z), (outer + 0.03, y + 0.8, z + 3.0), VOID, bottom=False)
        wooden_door(builder, (x0 + x1) / 2, 4.0, 0.0, 3.0, 4.6)
        shifted_roof(builder, (0.0, 11.0, 0.0), x0 - 0.3, x1 + 0.3, 7.4, 17.0, 19.8, TILES, along_axis="x",
                     imbrex=False)
        builder.oriented([(outer + side * 0.3, 3.6, 17.0), (outer + side * 0.3, 18.4, 17.0),
                          (outer + side * 0.3, 11.0, 19.8)], (side, 0, 0), ROUGH)
    shifted_roof(builder, (0.0, 12.7, 0.0), -27.3, 27.3, 4.8, FACADE_TOP - 0.6, FACADE_TOP + 1.8, TILES,
                 along_axis="x", imbrex=False)
    for side in (-1, 1):
        builder.oriented([(side * 27.3, 7.9, FACADE_TOP - 0.6), (side * 27.3, 17.5, FACADE_TOP - 0.6),
                          (side * 27.3, 12.7, FACADE_TOP + 1.8)], (side, 0, 0), ROUGH)
    tinted(builder, (0.7, 0.55, 0.42), lambda: builder.oriented(
        [(-26.0, wall_front - 2.2, FACADE_TOP - 1.2), (26.0, wall_front - 2.2, FACADE_TOP - 1.2),
         (26.0, 1.4, FACADE_TOP - 2.6), (-26.0, 1.4, FACADE_TOP - 2.6)], (0, 0, -1), PLANK))
    builder.oriented([(-26.4, wall_front - 2.2, FACADE_TOP - 1.0), (26.4, wall_front - 2.2, FACADE_TOP - 1.0),
                      (26.4, 1.0, FACADE_TOP - 2.45), (-26.4, 1.0, FACADE_TOP - 2.45)], (0, 0, 1), TILES)
    for x in range(-24, 25, 6):
        wooden_door(builder, float(x), 17.0, 0.0, 1.0, 3.0, facing=1)
    return weather(builder, 3), column_frames, statue_frames, level_heights


ARENA_STOREY = 10.5
ARENA_TOP = 20.9
ATTIC_TOP = 24.5
MAST_TOP = 29.0


def arena_bay(width):
    builder = MeshBuilder()
    half = width / 2
    opening = (width - 2.2) / 2
    lower, upper = ARENA_STOREY, ARENA_TOP
    arched_wall(builder, -half, half, -1.2, 0.0, 0.0, lower - 1.1, [(0.0, opening, 6.6)], ROUGH, segments=12,
                foundation=3.0)
    builder.merge(pilaster(1.1, lower - 1.4, 0.22, ASHLAR), placement(-half, 0.0, 0.3))
    builder.box((-half, -1.2, lower - 1.1), (half, -0.4, lower), WEATHERED, bottom=False)
    straight_moulding(builder, -half, half, lower - 1.1, simple_entablature_profile(1.1, 0.4), ASHLAR)
    arched_wall(builder, -half, half, -1.2, 0.0, lower, upper - 1.1, [(0.0, opening, lower + 6.4)], ROUGH,
                segments=12, sill=lower + 1.0)
    builder.merge(column("corinthian", 0.85, upper - lower - 2.2, detail="low", material=ASHLAR, arc=ENGAGED_HALF),
                  placement(-half, 0.05, lower + 1.0))
    builder.box((-half, -1.2, upper - 1.1), (half, -0.4, upper), WEATHERED, bottom=False)
    straight_moulding(builder, -half, half, upper - 1.1, simple_entablature_profile(1.1, 0.42), ASHLAR)
    builder.box((-half, -1.0, upper), (half, 0.0, ATTIC_TOP), WEATHERED, bottom=False)
    straight_moulding(builder, -half, half, ATTIC_TOP, simple_entablature_profile(0.6, 0.32), ASHLAR)
    for x in (-width / 4, width / 4):
        builder.box((x - 0.22, 0.0, ATTIC_TOP - 1.05), (x + 0.22, 0.6, ATTIC_TOP - 0.45), ASHLAR)
        builder.box((x - 0.18, 0.0, upper + 0.15), (x + 0.18, 0.42, upper + 0.45), ASHLAR)
        tinted(builder, (0.5, 0.36, 0.25), lambda x=x: builder.lathe([(0.09, upper + 0.45), (0.07, MAST_TOP)], 5,
                                                                      WEATHERED, smooth=True,
                                                                      matrix=placement(x, 0.34, 0.0)))
    vault = [(-3.2 + 2.0 * math.cos(math.pi * i / 8), 7.0 + 2.0 * math.sin(math.pi * i / 8)) for i in range(9)]
    builder.surface([[(x, y, z) for y, z in vault] for x in (-half, half)], WEATHERED)
    builder.box((-half, -5.2, -0.2), (half, -1.2, 0.0), WEATHERED, bottom=False)
    builder.box((-half, -5.2, lower - 0.3), (half, -1.2, lower), WEATHERED, bottom=False)
    builder.box((-half, -5.2, upper - 0.6), (half, -1.2, upper), WEATHERED)
    arched_wall(builder, -half, half, -6.4, -5.2, 0.0, lower - 0.3, [(0.0, 1.3, 3.4)], WEATHERED, segments=4)
    arched_wall(builder, -half, half, -6.4, -5.2, lower - 0.3, upper, [(0.0, 1.2, lower + 3.0)], WEATHERED, segments=4)
    builder.box((-1.4, -7.0, 0.0), (1.4, -6.3, 4.7), VOID, bottom=False)
    builder.box((-1.3, -7.0, lower), (1.3, -6.3, lower + 4.2), VOID, bottom=False)
    builder.box((-half, -6.4, ATTIC_TOP - 1.3), (half, -1.0, ATTIC_TOP - 1.0), WEATHERED, bottom=False)
    builder.box((-half, -6.4, upper), (half, -5.2, ATTIC_TOP - 1.3), WEATHERED, bottom=False, top=False)
    return weather(builder, 11)


CIRCUS_LENGTH = 450.0
CIRCUS_HALF_WIDTH = 50.5
CIRCUS_DEPTH = 18.0
CARCERES = 20.0


def circus_outline(offset, steps=24):
    inner = CIRCUS_HALF_WIDTH - CIRCUS_DEPTH
    radius = inner + offset
    center_y = -CIRCUS_LENGTH / 2 + CIRCUS_HALF_WIDTH
    top = CIRCUS_LENGTH / 2 - CARCERES
    path = [(-radius, top), (-radius, center_y)]
    for index in range(1, steps):
        angle = math.pi + math.pi * index / steps
        path.append((radius * math.cos(angle), center_y + radius * math.sin(angle)))
    path += [(radius, center_y), (radius, top)]
    return [(x, y, 0.0) for x, y in path]


def circus_profile():
    points = [(0.0, 0.0), (0.0, 2.4), (0.9, 2.4)]
    offset, height = 0.9, 2.4
    for _ in range(14):
        height += 0.5
        points.append((offset, height))
        offset += 0.86
        points.append((offset, height))
    points += [(CIRCUS_DEPTH - 2.0, height), (CIRCUS_DEPTH - 2.0, height + 1.1), (CIRCUS_DEPTH - 1.0, height + 1.1),
               (CIRCUS_DEPTH - 1.0, -1.5), (0.0, -1.5)]
    return points, height + 1.1


def circus_bay(width, top):
    builder = MeshBuilder()
    half = width / 2
    arched_wall(builder, -half, half, -1.0, 0.0, 0.0, top, [(0.0, min(1.5, half - 0.6), 4.0)], ASHLAR,
                segments=6, foundation=1.5)
    builder.merge(pilaster(0.8, 6.0, 0.15, ASHLAR), placement(-half, 0.0, 0.0))
    straight_moulding(builder, -half, half, 6.0, simple_entablature_profile(0.6, 0.25), ASHLAR)
    builder.box((-0.45, -0.03, 7.2), (0.45, 0.0, 8.2), VOID, bottom=False)
    straight_moulding(builder, -half, half, top - 1.0, simple_entablature_profile(1.0, 0.3), ASHLAR)
    builder.box((-min(1.5, half - 0.6), -0.95, 0.0), (min(1.5, half - 0.6), -0.92, 4.0), VOID, bottom=False)
    return builder


def circus():
    track = MeshBuilder()
    outline = circus_outline(0.0, 24)
    tinted(track, (0.98, 0.9, 0.78), lambda: track.oriented([(x, y, 0.03) for x, y, _ in outline], (0, 0, 1),
                                                             "arena_sand"))
    profile, top = circus_profile()
    cavea = MeshBuilder()
    cavea.sweep(outline, list(reversed(profile)), ASHLAR, closed=False)
    outer = circus_outline(CIRCUS_DEPTH, 24)
    bay_frames = frames_along([Vector(point) for point in outer], 4.6, False, 0.0)
    spina = MeshBuilder()
    half_spina = 115.0
    spina.box((-3.4, -half_spina, -0.5), (3.4, half_spina, 1.3), ASHLAR, bottom=False)
    for y0, y1 in ((-100.0, -42.0), (-30.0, 30.0), (42.0, 100.0)):
        spina.box((-2.6, y0, 1.3), (2.6, y1, 1.35), "river_water", bottom=False)
        spina.box((-3.0, y0 - 0.4, 1.3), (3.0, y0, 1.7), ASHLAR, bottom=False)
        spina.box((-3.0, y1, 1.3), (3.0, y1 + 0.4, 1.7), ASHLAR, bottom=False)
    statue_frames = []
    for y in (-36.0, 36.0, -106.0, 106.0):
        statue_frames.append(placement(0.0, y, 1.3, 0.0 if y > 0 else math.pi))
    for y in (-71.0, 71.0):
        spina.box((-1.6, y - 1.6, 1.3), (1.6, y + 1.6, 2.0), ASHLAR, bottom=False)
        for x in (-1.2, 1.2):
            for yy in (y - 1.2, y + 1.2):
                spina.lathe([(0.18, 2.0), (0.15, 5.8)], 6, MARBLE, smooth=True, matrix=Matrix.Translation((x, yy, 0.0)))
        spina.box((-1.6, y - 1.6, 5.8), (1.6, y + 1.6, 6.3), MARBLE)
        for k in range(7):
            spina.lathe([(0.0, 6.3), (0.13, 6.42), (0.1, 6.62), (0.0, 6.7)], 6, MARBLE, smooth=True,
                        matrix=Matrix.Translation((-1.2 + k * 0.4, y, 0.0)))
    for sign in (-1, 1):
        cy = sign * (half_spina + 6.0)
        spina.lathe([(3.4, -0.4), (3.4, 1.8), (0.0, 1.8)], 12, ASHLAR, smooth=False,
                    matrix=Matrix.Translation((0.0, cy, 0.0)), start=0.0 if sign > 0 else math.pi, sweep=math.pi)
        spina.oriented([(-3.4, cy, -0.4), (3.4, cy, -0.4), (3.4, cy, 1.8), (-3.4, cy, 1.8)], (0, -sign, 0), ASHLAR)
        for x in (-2.0, 0.0, 2.0):
            spina.lathe([(0.75, 1.8), (0.6, 2.4), (0.25, 6.4), (0.0, 7.0)], 8, "bronze_gilt", smooth=True,
                        matrix=Matrix.Translation((x, cy + sign * 0.8, 0.0)))
    carceres = MeshBuilder()
    y_front = CIRCUS_LENGTH / 2 - CARCERES
    y_back = CIRCUS_LENGTH / 2
    stalls = 12
    span = 2 * (CIRCUS_HALF_WIDTH - 8.0)
    openings = [(-span / 2 + span * (index + 0.5) / stalls, span / stalls / 2 - 0.55, 3.6) for index in range(stalls)]
    arched_wall(carceres, -CIRCUS_HALF_WIDTH + 8.0, CIRCUS_HALF_WIDTH - 8.0, y_front, y_front + 1.2, 0.0, 8.0,
                openings, ASHLAR, segments=6, foundation=1.5)
    carceres.box((-CIRCUS_HALF_WIDTH + 8.0, y_front + 1.2, -1.5), (CIRCUS_HALF_WIDTH - 8.0, y_back, 8.0), ASHLAR,
                 bottom=False)
    for x, _, _ in openings:
        carceres.box((x - 1.0, y_front + 1.17, 0.0), (x + 1.0, y_front + 1.2, 3.4), VOID, bottom=False)
    straight_moulding(carceres, -CIRCUS_HALF_WIDTH + 8.0, CIRCUS_HALF_WIDTH - 8.0, 8.0,
                      simple_entablature_profile(0.8, 0.35), ASHLAR, y=y_front)
    shifted_roof(carceres, (0.0, (y_front + y_back) / 2, 0.0), -CIRCUS_HALF_WIDTH + 8.0, CIRCUS_HALF_WIDTH - 8.0,
                 (y_back - y_front) / 2 + 0.3, 8.8, 11.2, TILES, along_axis="x", imbrex=False)
    carceres.box((-CIRCUS_HALF_WIDTH + 8.0, y_front - 0.3, 8.0), (CIRCUS_HALF_WIDTH - 8.0, y_back + 0.3, 8.8), ASHLAR)
    for side in (-1, 1):
        cx = side * (CIRCUS_HALF_WIDTH - 4.0)
        carceres.box((cx - 4.0, y_front - 2.0, -1.5), (cx + 4.0, y_back, 13.0), ASHLAR, bottom=False)
        straight_moulding(carceres, cx - 4.0, cx + 4.0, 13.0, simple_entablature_profile(0.8, 0.35), ASHLAR,
                          y=y_front - 2.0)
        carceres.lathe([(5.8, 13.0), (0.0, 15.6)], 4, TILES, smooth=False, start=math.pi / 4,
                       matrix=Matrix.Translation((cx, (y_front + y_back) / 2 - 1.0, 0.0)))
        for z in (4.0, 9.0):
            carceres.box((cx - 0.6, y_front - 2.03, z), (cx + 0.6, y_front - 2.0, z + 1.8), VOID, bottom=False)
    carceres.box((-2.8, y_front - 0.03, 0.0), (2.8, y_front, 6.4), VOID, bottom=False)
    return {"track": track, "cavea": cavea, "spina": spina, "carceres": carceres}, bay_frames, statue_frames, top


FORUM_HALF_X = 39.0
FORUM_HALF_Y = 30.0
GALLERY = 8.0


def forum_base():
    builder = MeshBuilder()
    x0, x1 = -FORUM_HALF_X + GALLERY, FORUM_HALF_X
    y0, y1 = -FORUM_HALF_Y + GALLERY, FORUM_HALF_Y - GALLERY
    tinted(builder, (0.98, 0.95, 0.9), lambda: builder.box((x0, y0, -1.0), (x1 + 6.0, y1, 0.02), "paving",
                                                           bottom=False))
    walls = [((-FORUM_HALF_X - 1.2, -FORUM_HALF_Y - 1.2), (FORUM_HALF_X, -FORUM_HALF_Y)),
             ((-FORUM_HALF_X - 1.2, FORUM_HALF_Y), (FORUM_HALF_X, FORUM_HALF_Y + 1.2)),
             ((-FORUM_HALF_X - 1.2, -FORUM_HALF_Y), (-FORUM_HALF_X, FORUM_HALF_Y))]
    for (ax, ay), (bx, by) in walls:
        builder.box((ax, ay, -9.0), (bx, by, 0.4), ROUGH, bottom=False)
    weather(builder, 19, low=-4.0)
    for x in range(-34, 38, 6):
        for y, facing in ((-FORUM_HALF_Y - 1.2, -1), (FORUM_HALF_Y + 1.2, 1)):
            builder.box((x - 0.3, y - 0.04 if facing < 0 else y, -3.4), (x + 0.3, y if facing < 0 else y + 0.04, -1.6),
                        VOID, bottom=False)
    for y in range(-26, 28, 6):
        builder.box((-FORUM_HALF_X - 1.24, y - 0.3, -3.4), (-FORUM_HALF_X - 1.2, y + 0.3, -1.6), VOID, bottom=False)
    return builder


def forum_wings():
    wings = []
    length_x = 2 * FORUM_HALF_X - GALLERY
    wings.append((length_x, placement(GALLERY / 2, FORUM_HALF_Y - GALLERY, 0.0, math.pi)))
    wings.append((length_x, placement(GALLERY / 2, -FORUM_HALF_Y + GALLERY, 0.0, 0.0)))
    wings.append((2 * FORUM_HALF_Y, placement(-FORUM_HALF_X + GALLERY, 0.0, 0.0, -math.pi / 2)))
    return wings


def temple(width=15.0, length=27.0, column_height=9.6, podium_height=3.0):
    builder = MeshBuilder()
    hw = width / 2
    back = -length / 2
    front = length / 2
    stair = 5.0
    podium(builder, hw, back, front, podium_height, stair, 1.4, material=ASHLAR)
    floor = podium_height
    column_d = 0.95
    frames = []
    front_row = front - stair - 1.0
    for index in range(6):
        frames.append(placement(-hw + 1.0 + (width - 2.0) * index / 5, front_row, floor))
    for y in (front_row - 3.2, front_row - 6.4):
        for x in (-hw + 1.0, hw - 1.0):
            frames.append(placement(x, y, floor))
    cella_front = front_row - 7.6
    builder.box((-hw + 0.6, back + 0.6, floor), (hw - 0.6, cella_front, floor + column_height + 0.4), ASHLAR,
                bottom=False, top=False)
    wooden_door(builder, 0.0, cella_front + 0.02, floor, 3.6, 6.0, facing=1)
    top = floor + column_height
    builder.box((-hw - 0.1, back + 0.4, top), (hw + 0.1, front_row + 0.7, top + 1.6), STONE)
    straight_moulding(builder, -hw - 0.1, hw + 0.1, top + 1.2, simple_entablature_profile(0.5, 0.35), STONE,
                      y=front_row + 0.7)
    rise = hw * math.tan(math.radians(15))
    gable_roof(builder, back + 0.2, front_row + 1.0, hw + 0.5, top + 1.6, top + 1.6 + rise, TILES, along_axis="y",
               imbrex=True)
    for y, facing in ((front_row + 1.0, 1), (back + 0.2, -1)):
        tri = [(-hw - 0.3, y, top + 1.6), (hw + 0.3, y, top + 1.6), (0.0, y, top + 1.6 + rise)]
        builder.oriented(tri, (0, facing, 0), STONE)
        inner = [(-hw + 0.6, y + facing * 0.02, top + 1.85), (hw - 0.6, y + facing * 0.02, top + 1.85),
                 (0.0, y + facing * 0.02, top + 1.45 + rise)]
        tinted(builder, (0.82, 0.8, 0.76), lambda inner=inner, facing=facing: builder.oriented(inner, (0, facing, 0),
                                                                                              STONE))
        raking_cornice(builder, hw + 0.45, y + facing * 0.05, top + 1.55, top + 1.75 + rise, facing)
    for side in (-1, 1):
        side_antefixes(builder, side * (hw + 0.5), back + 0.2, front_row + 1.0, top + 1.6, side)
    for z in (top + 0.35, top + 0.7):
        builder.box((-hw - 0.1, front_row + 0.7, z), (hw + 0.1, front_row + 0.74, z + 0.04), STONE, bottom=False)
    return weather(builder, 13), frames, column_height, column_d


def augustus_gate():
    builder = MeshBuilder()
    radius = 16.5
    center = Vector((0.0, radius, 0.0))
    gap = 0.46
    for start, end in ((math.pi, 1.5 * math.pi - gap), (1.5 * math.pi + gap, 2.0 * math.pi)):
        steps = 8
        path = [center + Vector((radius * math.cos(start + (end - start) * i / steps),
                                 radius * math.sin(start + (end - start) * i / steps), 0.0)) for i in range(steps + 1)]
        builder.sweep(path, [(-1.2, -3.0), (-1.2, 9.5), (1.2, 9.5), (1.2, -3.0)], ROUGH, caps=True)
        builder.sweep(path, [(-1.3, 9.5), (-1.3, 10.1), (1.3, 10.1), (1.3, 9.5)], ASHLAR, caps=True)
    gate_half = radius * math.sin(gap) + 1.2
    openings = [(0.0, 2.4, 5.4), (-gate_half + 1.9, 0.85, 2.7), (gate_half - 1.9, 0.85, 2.7)]
    arched_wall(builder, -gate_half, gate_half, -4.2, 0.4, 0.0, 12.0, openings, ASHLAR, segments=10, foundation=3.0)
    for x in (-gate_half + 3.4, -2.9, 2.9, gate_half - 3.4):
        builder.merge(pilaster(0.6, 9.2, 0.16, ASHLAR), placement(x, 0.4, 0.4))
    straight_moulding(builder, -gate_half, gate_half, 9.8, simple_entablature_profile(0.8, 0.45), ASHLAR, y=0.4)
    builder.box((-gate_half, -4.2, 12.0), (gate_half, 0.4, 12.6), ASHLAR)
    builder.box((-2.4, -4.2, -0.05), (2.4, 0.4, 0.02), "paving", bottom=False)
    for side in (-1, 1):
        tower = Matrix.Translation((side * radius, radius + 1.8, 0.0))
        builder.lathe([(5.6, -3.0), (5.6, 15.0)], 18, ROUGH, smooth=True, matrix=tower, caps=False)
        builder.lathe([(5.6, 15.0), (5.9, 15.3), (5.9, 15.8), (5.4, 15.8)], 18, ASHLAR, smooth=False, matrix=tower,
                      caps=False)
        builder.lathe([(6.1, 15.8), (0.0, 19.6)], 18, TILES, smooth=False, matrix=tower)
        for angle in (45, 90, 135, 200, 260, 320):
            a = math.radians(angle)
            frame = Matrix.Translation((side * radius + 5.55 * math.cos(a), radius + 1.8 + 5.55 * math.sin(a), 11.0))
            frame = frame @ Matrix.Rotation(a - math.pi / 2, 4, "Z")
            builder.centered_box((0.0, 0.0, 0.0), (0.6, 0.3, 1.4), VOID, matrix=frame)
    return weather(builder, 17)


def horreum(length=42.0, depth=14.0, height=7.0, seed=0, doors_both=False, portico=False, wall=None):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hl, hd = length / 2, depth / 2
    builder.box((-hl, -hd, -2.5), (hl, hd, 1.2), ROUGH, bottom=False, top=False)
    wall = wall or rng.choice(["plaster", "plaster_cream", "plaster_ochre"])
    builder.box((-hl, -hd, 1.2), (hl, hd, height), wall, bottom=False, top=False)
    rise = hd * 0.42
    gable_roof(builder, -hl - 0.4, hl + 0.4, hd + 0.6, height, height + rise, TILES, along_axis="x", imbrex=False)
    if portico:
        front = -hd - 3.6
        slope = [(-hl, -hd, 4.7), (hl, -hd, 4.7), (hl, front - 0.4, 3.75), (-hl, front - 0.4, 3.75)]
        builder.oriented(slope, (0, -0.3, 1), TILES)
        first = len(builder.polygons)
        builder.oriented(list(reversed(slope)), (0, 0.3, -1), TILES)
        builder.tint(first, (0.5, 0.42, 0.36))
        builder.box((-hl, front - 0.25, 3.4), (hl, front + 0.25, 3.8), ROUGH, bottom=True)
        builder.box((-hl, front - 0.3, -0.6), (hl, -hd, 0.12), ROUGH, bottom=False)
        count = int(length / 4.2)
        for index in range(count + 1):
            x = -hl + 0.25 + (length - 0.5) * index / count
            builder.box((x - 0.25, front - 0.25, 0.12), (x + 0.25, front + 0.25, 3.4), ROUGH, bottom=False, top=False)
    builder.paint(TILES, rng.choice([(1.0, 1.0, 1.0), (0.92, 0.86, 0.8), (0.86, 0.78, 0.72)]))
    for x in (-hl, hl):
        tri = [(x, -hd, height), (x, hd, height), (x, 0.0, height + rise)]
        builder.oriented(tri, (1 if x > 0 else -1, 0, 0), wall)
    count = int(length / 5.0)
    for index in range(count):
        x = -hl + length * (index + 0.5) / count
        builder.box((x - 1.1, -hd - 0.04, 0.0), (x + 1.1, -hd, 3.0), VOID, bottom=False)
        builder.box((x - 1.35, -hd - 0.08, 3.0), (x + 1.35, -hd - 0.02, 3.3), ROUGH, bottom=False)
        builder.box((x - 0.35, hd, height - 2.0), (x + 0.35, hd + 0.04, height - 1.2), VOID, bottom=False)
        if doors_both and index % 2 == 0:
            builder.box((x - 1.1, hd, 0.0), (x + 1.1, hd + 0.04, 3.0), VOID, bottom=False)
        if index < count - 1:
            bx = x + length / count / 2
            builder.box((bx - 0.35, -hd - 0.45, -0.5), (bx + 0.35, -hd, height - 0.3), ROUGH, bottom=False)
    return builder


def jetty(length=18.0, width=4.0):
    builder = MeshBuilder()
    hw = width / 2
    tinted(builder, (0.72, 0.6, 0.46), lambda: builder.box((-hw, 0.0, -0.25), (hw, length, 0.0), PLANK))
    for y in range(2, int(length) + 1, 3):
        for x in (-hw + 0.2, hw - 0.2):
            tinted(builder, (0.42, 0.32, 0.22), lambda x=x, y=y: builder.lathe(
                [(0.16, -6.0), (0.15, 0.35)], 6, PLANK, smooth=True, matrix=Matrix.Translation((x, y, 0.0))))
    return builder


def pile(height=6.0):
    builder = MeshBuilder()
    tinted(builder, (0.42, 0.32, 0.22), lambda: builder.lathe([(0.17, -height), (0.15, 0.4), (0.0, 0.5)], 6, PLANK,
                                                              smooth=True))
    return builder


def reeds(seed=0, count=26, height=2.2):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for _ in range(count):
        x, y = rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4)
        h = height * rng.uniform(0.6, 1.1)
        lean = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0.0))
        base = Vector((x, y, -0.2))
        tip = base + lean * h * 0.4 + Vector((0.0, 0.0, h))
        side = Vector((0.03, 0.0, 0.0)) if rng.random() < 0.5 else Vector((0.0, 0.03, 0.0))
        shade = rng.uniform(0.82, 1.12)
        tinted(builder, (shade, shade, shade * 0.95), lambda base=base, tip=tip, side=side: builder.polygon(
            [base - side, base + side, tip], "reed"))
        tinted(builder, (shade, shade, shade * 0.95), lambda base=base, tip=tip, side=side: builder.polygon(
            [base + side, base - side, tip], "reed"))
    return builder
