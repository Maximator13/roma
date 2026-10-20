import numpy as np

from .geometry import newell_normal
from .nimes_detail import smooth_noise, split_quad

STONES = {"stone", "marble"}


def split_front(builder, cuts=(0.1, 1.25), materials=("plaster", "stone"), min_width=1.0):
    slots = {index for index, name in enumerate(builder.materials) if name in materials}
    polygons, materials_out, smooth_out, uvs_out, colors_out = [], [], [], [], []
    for indices, material, smooth, uvs, color in zip(builder.polygons, builder.polygon_materials,
                                                     builder.polygon_smooth, builder.polygon_uvs,
                                                     builder.polygon_colors):
        replaced = None
        if material in slots and len(indices) == 4 and uvs is None:
            if newell_normal([builder.positions[index] for index in indices]).normalized().y < -0.7:
                replaced = split_quad(builder, indices, cuts, min_width)
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


def stone_wear(mesh, heights=None, seed=0):
    attribute = mesh.color_attributes.get("Col")
    names = [material.name if material else "" for material in mesh.materials]
    slots = [index for index, name in enumerate(names) if name in STONES]
    if attribute is None or not slots or len(mesh.loops) == 0:
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
    material = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", material)
    corner_slot = np.repeat(material, totals)
    normals = np.empty(count * 3, dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", normals)
    normals = normals.reshape(-1, 3)
    points = positions[vertex]
    height = heights[vertex] if heights is not None else points[:, 2]
    upright = np.clip(1.0 - np.abs(normals[:, 2]) * 1.4, 0.0, 1.0)
    t = np.clip(height / 1.2, 0.0, 1.0)
    t = t * t * (3 - 2 * t)
    ramp = 1.0 - 0.2 * (1.0 - t) * upright
    flat = points.copy()
    flat[:, 2] = 0.0
    streak = np.clip((smooth_noise(flat, 2.7, seed + 5) - 0.55) * 3.0, 0.0, 1.0) * upright
    factor = ramp * (1.0 - 0.1 * streak * np.clip(1.0 - height / 5.0, 0.3, 1.0))
    marble = np.isin(corner_slot, [index for index in slots if names[index] == "marble"])
    factor = np.where(marble, factor * 0.93, factor)
    mask = np.isin(corner_slot, slots)
    colours[mask, :3] *= factor[mask, None]
    attribute.data.foreach_set("color_srgb", np.clip(colours, 0.0, 1.0).ravel())
    mesh.update()
