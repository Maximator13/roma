import math
import os

import bpy
import numpy as np
from mathutils import Vector

from .geometry import MeshBuilder
from .materials import principled_material

SIZE = 1024
INK = (0.30, 0.23, 0.17)
OPACITY = 0.6
ARC = [(math.cos(math.pi * k / 6), math.sin(math.pi * k / 6)) for k in range(13)]
RING = [(0.5 + 0.5 * x, 0.5 + 0.5 * y) for x, y in ARC] + [(0.5 + 0.5 * x, 0.5 - 0.5 * y) for x, y in ARC]
OPEN = [(1.0, 0.85), (0.7, 1.0), (0.3, 1.0), (0.0, 0.7), (0.0, 0.3), (0.3, 0.0), (0.7, 0.0), (1.0, 0.15)]
BOWL = [(0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (1.0, 0.8), (1.0, 0.62), (0.7, 0.45), (0.0, 0.45)]
GLYPHS = {
    "A": [[(0, 0), (0.5, 1), (1, 0)], [(0.25, 0.45), (0.75, 0.45)]],
    "B": [[(0, 0), (0, 1), (0.65, 1), (0.9, 0.85), (0.9, 0.65), (0.6, 0.5), (0, 0.5)],
          [(0.6, 0.5), (1, 0.35), (1, 0.15), (0.7, 0), (0, 0)]],
    "C": [OPEN],
    "D": [[(0, 0), (0, 1), (0.6, 1), (1, 0.7), (1, 0.3), (0.6, 0), (0, 0)]],
    "E": [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, 0.5), (0.7, 0.5)]],
    "F": [[(1, 1), (0, 1), (0, 0)], [(0, 0.5), (0.7, 0.5)]],
    "G": [OPEN, [(1, 0.15), (1, 0.45), (0.6, 0.45)]],
    "H": [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]],
    "I": [[(0.5, 0), (0.5, 1)]],
    "K": [[(0, 0), (0, 1)], [(1, 1), (0, 0.45), (1, 0)]],
    "L": [[(0, 1), (0, 0), (0.9, 0)]],
    "M": [[(0, 0), (0, 1), (0.5, 0.4), (1, 1), (1, 0)]],
    "N": [[(0, 0), (0, 1), (1, 0), (1, 1)]],
    "O": [RING],
    "P": [BOWL],
    "Q": [RING, [(0.6, 0.25), (1.0, -0.1)]],
    "R": [BOWL, [(0.4, 0.45), (1, 0)]],
    "S": [[(1, 0.9), (0.7, 1), (0.3, 1), (0, 0.8), (0.1, 0.55), (0.9, 0.45), (1, 0.2), (0.7, 0), (0.3, 0), (0, 0.1)]],
    "T": [[(0, 1), (1, 1)], [(0.5, 1), (0.5, 0)]],
    "V": [[(0, 1), (0.5, 0), (1, 1)]],
    "X": [[(0, 0), (1, 1)], [(0, 1), (1, 0)]],
    "Y": [[(0, 1), (0.5, 0.5), (1, 1)], [(0.5, 0.5), (0.5, 0)]],
    "Δ": [[(0, 0), (0.5, 1), (1, 0), (0, 0)]],
    "Σ": [[(1, 1), (0, 1), (0.5, 0.5), (0, 0), (1, 0)]],
    "Ω": [[(0, 0), (0.3, 0), (0.1, 0.4), (0.2, 0.85), (0.5, 1), (0.8, 0.85), (0.9, 0.4), (0.7, 0), (1, 0)]],
    "Λ": [[(0, 0), (0.5, 1), (1, 0)]],
    "Π": [[(0, 0), (0, 1), (1, 1), (1, 0)]],
    "Θ": [RING, [(0.3, 0.5), (0.7, 0.5)]],
}
for latin, greek in (("A", "Α"), ("E", "Ε"), ("H", "Η"), ("I", "Ι"), ("K", "Κ"), ("M", "Μ"), ("N", "Ν"), ("O", "Ο"),
                     ("P", "Ρ"), ("T", "Τ"), ("Y", "Υ")):
    GLYPHS[greek] = GLYPHS[latin]
LINES = [
    ["ΔΙΟΝΥΣΙΟΣ ΙΣΤΟΡΗΣΑ"],
    ["VIDI ET MIRATVS SVM", "C IVLIVS FELIX"],
    ["ΑΠΟΛΛΩΝΙΟΣ ΗΚΩ ΚΑΙ ΕΘΑΥΜΑΣΑ"],
    ["L MARCIVS HIC FVIT"],
    ["VIDI PYRAMIDAS SINE TE DVLCISSIME FRATER", "ET TIBI QVOD POTVI LACRIMAS HIC MAESTA PROFVDI",
     "ET NOSTRI MEMOREM LVCTVS HANC SCVLPO QVERELLAM", "SIT NOMEN DECIMI GENTIANI PYRAMIDE ALTA",
     "PONTIFICIS COMITISQVE TVIS TRAIANE TRIVMPHIS", "LVSTRA SEX INTRA CENSORIS CONSVLIS ESSE"],
]
ROWS = [(0, 128, 30), (128, 256, 28), (256, 384, 26), (384, 512, 30), (512, 768, 22)]


def stamp(mask, x, y, radius):
    x0, x1 = int(max(x - radius, 0)), int(min(x + radius + 1, mask.shape[1]))
    y0, y1 = int(max(y - radius, 0)), int(min(y + radius + 1, mask.shape[0]))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], np.clip(radius + 0.5 - np.hypot(xx - x, yy - y), 0, 1))


def write(mask, text, left, baseline, height, rng):
    width = height * 0.72
    x = left
    for character in text:
        if character == " ":
            x += width * 0.8
            continue
        lean = rng.uniform(-0.08, 0.08)
        scale = height * rng.uniform(0.9, 1.08)
        for stroke in GLYPHS[character]:
            for (ax, ay), (bx, by) in zip(stroke[:-1], stroke[1:]):
                steps = int(max(abs(bx - ax) * width, abs(by - ay) * scale) * 1.5) + 2
                for t in np.linspace(0.0, 1.0, steps):
                    px = x + (ax + (bx - ax) * t) * width + lean * (ay + (by - ay) * t) * scale
                    py = baseline + (ay + (by - ay) * t) * scale
                    stamp(mask, px, py, 1.1)
        x += width * 1.28
    return x


def atlas_pixels(seed=5):
    rng = np.random.default_rng(seed)
    mask = np.zeros((SIZE, SIZE))
    for (y0, y1, height), lines in zip(ROWS, LINES):
        gap = height * 1.45
        baseline = y1 - 18 - height
        for line in lines:
            write(mask, line, 18 + rng.uniform(0, 30), baseline, height, rng)
            baseline -= gap
    pixels = np.zeros((SIZE, SIZE, 4), dtype=np.float32)
    pixels[..., :3] = INK
    pixels[..., 3] = mask * OPACITY
    return pixels


def graffiti_material(cache_dir):
    path = os.path.join(cache_dir, "textures", "graffiti_v1.png")
    if not os.path.exists(path):
        image = bpy.data.images.new("graffiti", SIZE, SIZE, alpha=True)
        image.pixels.foreach_set(atlas_pixels().ravel())
        image.filepath_raw = path
        image.file_format = "PNG"
        image.save()
        bpy.data.images.remove(image)
    image = bpy.data.images.load(path, check_existing=True)
    image.alpha_mode = "STRAIGHT"
    material = principled_material("graffiti", (1.0, 1.0, 1.0), 0.9, 0.0, image, vertex_color=False)
    nodes = material.node_tree.nodes
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    material.node_tree.links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    material.surface_render_method = "BLENDED"
    return material


def graffiti(item, base):
    builder = MeshBuilder()
    hx, hy, height = item["half_x"], item["half_y"], item["height"]
    normal = Vector((height, 0.0, hx)).normalized()
    up = Vector((-hx, 0.0, height)).normalized()
    along = Vector((0.0, 1.0, 0.0))
    spots = [(0, 1.05, -5.5), (1, 1.55, -9.0), (2, 0.75, -12.5), (3, 2.05, -15.0), (4, 1.35, -19.0)]
    for row, z, offset in spots:
        y0, y1, _ = ROWS[row]
        width = 1.0
        tall = (y1 - y0) / SIZE * width
        centre = Vector((item["x"] + hx * (1 - z / height), item["y"] + hy + offset, base + z)) + normal * 0.02
        corners = [centre - along * width / 2 - up * tall / 2, centre + along * width / 2 - up * tall / 2,
                   centre + along * width / 2 + up * tall / 2, centre - along * width / 2 + up * tall / 2]
        v0, v1 = y0 / SIZE, y1 / SIZE
        builder.face(builder.points(corners), "graffiti", uvs=[(0.0, v0), (1.0, v0), (1.0, v1), (0.0, v1)])
    return builder
