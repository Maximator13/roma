import numpy as np

from .nimes_detail import smooth_noise

WALLS = {"plaster", "limestone", "marble", "granite"}
ROOFS = {"terracotta_tiles"}
DUST = np.array([0.80, 0.70, 0.56])
SALT = np.array([0.66, 0.62, 0.54])
ALGAE = np.array([0.42, 0.46, 0.32])


def corner_data(mesh):
    count = len(mesh.loops)
    vertex = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex)
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    totals = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", totals)
    slots = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", slots)
    normals = np.empty(count * 3, dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", normals)
    names = [material.name if material else "" for material in mesh.materials]
    return vertex, positions, np.repeat(slots, totals), normals.reshape(-1, 3), names


def weather(mesh, heights=None, world_z=None, seed=0, foliage=False):
    attribute = mesh.color_attributes.get("Col")
    if attribute is None or len(mesh.loops) == 0:
        return
    vertex, positions, corner_slot, normals, names = corner_data(mesh)
    colours = np.empty(len(mesh.loops) * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    rgb = colours[:, :3]
    points = positions[vertex]
    height = heights[vertex] if heights is not None else points[:, 2]
    level = world_z[vertex] if world_z is not None else None
    walls = np.isin(corner_slot, [index for index, name in enumerate(names) if name in WALLS])
    upright = np.clip(1.0 - np.abs(normals[:, 2]) * 1.4, 0.0, 1.0)
    t = np.clip(height / 1.6, 0.0, 1.0)
    t = t * t * (3 - 2 * t)
    t = 1.0 - (1.0 - t) * upright
    stain = 1.0 + 0.1 * (smooth_noise(points, 0.45, seed) - 0.5) + 0.05 * (smooth_noise(points, 2.1, seed + 5) - 0.5)
    factor = (DUST[None, :] + (1 - DUST[None, :]) * t[:, None]) * stain[:, None]
    streak = np.clip((smooth_noise(points * np.array([4.0, 4.0, 0.25]), 1.0, seed + 9) - 0.6) * 3.0, 0.0, 1.0)
    factor *= (1.0 - 0.07 * streak * upright)[:, None]
    if level is not None:
        wet = np.clip(1.0 - (level - 0.1) / 0.9, 0.0, 1.0) * (level > -3.0) * upright
        factor *= (1.0 - wet[:, None] * (1.0 - ALGAE[None, :]))
        salt = np.clip(1.0 - np.abs(level - 1.2) / 0.5, 0.0, 1.0) * upright * 0.5
        factor = factor * (1 - salt[:, None]) + (factor * SALT[None, :] / SALT.max()) * salt[:, None]
    rgb[walls] *= factor[walls]
    roofs = np.isin(corner_slot, [index for index, name in enumerate(names) if name in ROOFS])
    n1 = smooth_noise(points, 0.3, seed + 3)
    n2 = smooth_noise(points, 0.85, seed + 7)
    tint = np.column_stack([0.92 + 0.18 * n1, 0.86 + 0.2 * n1 * n2 + 0.04, 0.82 + 0.18 * n2])
    rgb[roofs] *= tint[roofs]
    if foliage:
        green = (rgb[:, 1] > rgb[:, 0] * 1.02) & (rgb[:, 1] > rgb[:, 2])
        bottom, top = points[:, 2].min(), points[:, 2].max()
        relative = np.clip((points[:, 2] - bottom) / max(top - bottom, 1e-3), 0, 1)
        light = 0.6 + 0.46 * np.clip(normals[:, 2] * 0.5 + 0.5, 0, 1) * (0.55 + 0.45 * relative)
        light *= 0.9 + 0.2 * smooth_noise(points, 1.4, seed)
        warm = np.column_stack([light * (1.0 + 0.1 * relative), light * (1.0 + 0.04 * relative),
                                light * (1.02 - 0.14 * relative)])
        rgb[green] *= warm[green]
    colours[:, :3] = np.clip(rgb, 0.0, 1.0)
    attribute.data.foreach_set("color_srgb", colours.ravel())
    mesh.update()
