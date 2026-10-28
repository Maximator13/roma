import numpy as np

from .alexandrie_weather import corner_data
from .nimes_detail import smooth_noise

STONE = {"casing", "casing_granite", "granite_rough", "core_stone", "limestone", "restoration", "sphinx_rock",
         "mudbrick", "plaster", "paving", "basalt"}
DUST = np.array([0.86, 0.70, 0.50])


def weather(mesh, heights=None, seed=0, reach=1.8, patina=0.0):
    attribute = mesh.color_attributes.get("Col")
    if attribute is None or len(mesh.loops) == 0:
        return
    vertex, positions, corner_slot, normals, names = corner_data(mesh)
    colours = np.empty(len(mesh.loops) * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    rgb = colours[:, :3]
    points = positions[vertex]
    height = heights[vertex] if heights is not None else points[:, 2] - points[:, 2].min()
    stone = np.isin(corner_slot, [index for index, name in enumerate(names) if name in STONE])
    upright = np.clip(1.0 - np.abs(normals[:, 2]) * 1.2, 0.0, 1.0)
    t = np.clip(height / reach, 0.0, 1.0)
    t = t * t * (3 - 2 * t)
    t = 1.0 - (1.0 - t) * (0.4 + 0.6 * upright)
    factor = DUST[None, :] + (1 - DUST[None, :]) * t[:, None]
    stain = 1.0 + 0.08 * (smooth_noise(points, 0.35, seed) - 0.5) + 0.05 * (smooth_noise(points, 1.7, seed + 5) - 0.5)
    factor *= stain[:, None]
    streak = np.clip((smooth_noise(points * np.array([3.0, 3.0, 0.2]), 1.0, seed + 9) - 0.58) * 3.0, 0.0, 1.0)
    factor *= (1.0 - 0.08 * streak * upright)[:, None]
    if patina > 0:
        large = smooth_noise(points, 0.02, seed + 11) - 0.5
        middle = smooth_noise(points * np.array([1.0, 1.0, 0.35]), 0.09, seed + 13) - 0.5
        varnish = np.clip((smooth_noise(points * np.array([2.5, 2.5, 0.12]), 0.25, seed + 17) - 0.62) * 2.5, 0, 1)
        tone = 1.0 + patina * (0.22 * large + 0.12 * middle)
        warm = np.column_stack([tone, tone * (1.0 - 0.015 * patina), tone * (1.0 - 0.05 * patina * (0.5 + large))])
        factor *= warm
        factor *= (1.0 - 0.12 * patina * varnish * upright)[:, None]
        broad = (smooth_noise(points, 1.0 / 37.0, seed + 19) - 0.5) * 0.10 + (smooth_noise(points, 1.0 / 140.0,
                                                                                      seed + 23) - 0.5) * 0.12
        rain = np.clip((smooth_noise(points * np.array([4.0, 4.0, 0.08]), 0.5, seed + 29) - 0.45) * 2.0, 0, 1)
        foot = np.exp(-np.clip(height, 0.0, None) / 18.0)
        factor *= (1.0 + patina * broad - patina * upright * rain * (0.04 + 0.05 * foot))[:, None]
    rgb[stone] *= factor[stone]
    colours[:, :3] = np.clip(rgb, 0.0, 1.0)
    attribute.data.foreach_set("color_srgb", colours.ravel())
    mesh.update()
