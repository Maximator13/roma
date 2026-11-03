import json
import os
import time

import bmesh
import bpy
import numpy as np

from .stage import export_glb

GLTF_OUTPUT = "glTF Material Output"
LIGHTMAP = "Lightmap"
WATER = ("water", "sea", "river")
NODE_LABEL = "baked_occlusion"


class Atlas:
    def __init__(self, name, objects, size, distance, unwrap="smart", samples=64, margin=0.004, strength=1.0):
        self.name = name
        self.objects = list(objects)
        self.size = size
        self.distance = distance
        self.unwrap = unwrap
        self.samples = samples
        self.margin = margin
        self.strength = strength


def gltf_output_group():
    group = bpy.data.node_groups.get(GLTF_OUTPUT)
    if group is None:
        group = bpy.data.node_groups.new(GLTF_OUTPUT, "ShaderNodeTree")
        group.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return group


def bakeable(material):
    return material is not None and not material.name.startswith(WATER)


def lightmap_layer(obj):
    layers = obj.data.uv_layers
    if LIGHTMAP in layers:
        layers.remove(layers[LIGHTMAP])
    render = next(layer for layer in layers if layer.active_render)
    layer = layers.new(name=LIGHTMAP)
    render.active_render = True
    layers.active = layer
    return layer


def planar_uvs(obj, layer):
    mesh = obj.data
    count = len(mesh.vertices)
    positions = np.empty(count * 3)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3) @ np.array(obj.matrix_world)[:3, :3].T + np.array(obj.matrix_world)[:3, 3]
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    layer.data.foreach_set("uv", (positions[loops, :2] / 1000.0).astype(np.float32).ravel())


def select_only(objects):
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def face_charts(obj):
    mesh = obj.data
    matrix = np.array(obj.matrix_world)
    count = len(mesh.polygons)
    normals = np.empty(count * 3)
    mesh.polygons.foreach_get("normal", normals)
    normals = normals.reshape(-1, 3) @ np.linalg.inv(matrix[:3, :3])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    starts = np.empty(count, dtype=np.int64)
    mesh.polygons.foreach_get("loop_start", starts)
    vertices = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", vertices)
    vertices = vertices.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    owner = np.repeat(np.arange(count), np.diff(np.append(starts, len(loops))))
    points = vertices[loops]
    direction = np.round(normals * 12.0)
    flat = np.abs(direction[:, 2]) >= 11.0
    local_x = matrix[:3, 0] * [1.0, 1.0, 0.0]
    axis_u = np.where(flat[:, None], local_x / max(np.linalg.norm(local_x), 1e-9),
                      np.cross([0.0, 0.0, 1.0], direction))
    axis_u /= np.maximum(np.linalg.norm(axis_u, axis=1, keepdims=True), 1e-9)
    axis_n = direction / np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-9)
    axis_v = np.cross(axis_n, axis_u)
    plane = np.round(np.einsum("ij,ij->i", points, axis_n[owner]) / 0.1)
    plane = np.maximum.reduceat(plane, starts)
    flat_uv = np.column_stack([np.einsum("ij,ij->i", points, axis_u[owner]),
                               np.einsum("ij,ij->i", points, axis_v[owner])])
    boxes = np.column_stack([np.minimum.reduceat(flat_uv, starts), np.maximum.reduceat(flat_uv, starts)])
    keys = np.column_stack([direction, plane])
    _, group = np.unique(keys, axis=0, return_inverse=True)
    charts = []
    for members in np.split(np.argsort(group.ravel(), kind="stable"),
                            np.cumsum(np.bincount(group.ravel()))[:-1]):
        for chart in split_gaps(boxes, members):
            charts.extend(split_long(boxes, chart))
    return flat_uv, owner, boxes, charts


def subdivide_long(obj, length):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    scale = max(obj.matrix_world.to_scale())
    cuts = {}
    for edge in mesh.edges:
        count = int(edge.calc_length() * scale / length)
        if count > 0:
            cuts.setdefault(count, []).append(edge)
    for count, edges in cuts.items():
        bmesh.ops.subdivide_edges(mesh, edges=[edge for edge in edges if edge.is_valid], cuts=count,
                                  use_grid_fill=True)
    mesh.to_mesh(obj.data)
    mesh.free()
    return sum(len(edges) for edges in cuts.values())


def split_long(boxes, chart, length=8.0):
    centres = (boxes[chart, :2] + boxes[chart, 2:]) / 2
    cells = np.floor((centres - centres.min(axis=0)) / length).astype(np.int64)
    _, piece = np.unique(cells, axis=0, return_inverse=True)
    piece = piece.ravel()
    return [chart[piece == number] for number in range(piece.max() + 1)]


def split_gaps(boxes, members, gap=0.25):
    pending = [(members, 0, False)]
    done = []
    while pending:
        indices, axis, tried = pending.pop()
        order = indices[np.argsort(boxes[indices, axis], kind="stable")]
        reach = np.maximum.accumulate(boxes[order, axis + 2])
        cuts = np.nonzero(boxes[order[1:], axis] > reach[:-1] + gap)[0] + 1
        if len(cuts) == 0:
            if tried:
                done.append(indices)
            else:
                pending.append((indices, 1 - axis, True))
            continue
        pending.extend((part, 1 - axis, False) for part in np.split(order, cuts))
    return done


def shelf_pack(sizes, scale, size, margin):
    widths = np.ceil(sizes[:, 0] * scale) + margin
    heights = np.ceil(sizes[:, 1] * scale) + margin
    order = np.argsort(-heights, kind="stable")
    origins = np.zeros((len(sizes), 2))
    x = y = shelf = 0.0
    for index in order:
        if widths[index] > size:
            return None
        if x + widths[index] > size:
            x, y, shelf = 0.0, y + shelf, 0.0
        if y + heights[index] > size:
            return None
        origins[index] = (x, y)
        x += widths[index]
        shelf = max(shelf, heights[index])
    return origins


def chart_unwrap(atlas):
    pixels = max(4, int(round(atlas.size * atlas.margin)))
    entries = [(obj, *face_charts(obj)) for obj in atlas.objects]
    sizes = []
    for _, _, _, boxes, charts in entries:
        for chart in charts:
            sizes.append(boxes[chart, 2:].max(axis=0) - boxes[chart, :2].min(axis=0))
    sizes = np.array(sizes)
    low, high = 0.0, atlas.size / max(float(sizes.max()), 1e-6)
    for _ in range(24):
        middle = (low + high) / 2
        if shelf_pack(sizes, middle, atlas.size, pixels) is None:
            high = middle
        else:
            low = middle
    origins = shelf_pack(sizes, low, atlas.size, pixels)
    index = 0
    for obj, flat_uv, owner, boxes, charts in entries:
        chart_of = np.zeros(len(boxes), dtype=np.int64)
        corners = np.zeros((len(charts), 2))
        for number, chart in enumerate(charts):
            chart_of[chart] = number
            corners[number] = boxes[chart, :2].min(axis=0)
        placed = origins[index:index + len(charts)]
        loop_chart = chart_of[owner]
        uv = (placed[loop_chart] + pixels / 2 + (flat_uv - corners[loop_chart]) * low) / atlas.size
        obj.data.uv_layers[LIGHTMAP].data.foreach_set("uv", uv.astype(np.float32).ravel())
        index += len(charts)
    return {"charts": index, "texels_per_metre": round(low, 1)}


def unwrap(atlas):
    for obj in atlas.objects:
        layer = lightmap_layer(obj)
        if atlas.unwrap == "planar":
            planar_uvs(obj, layer)
    if atlas.unwrap == "charts":
        cut = sum(subdivide_long(obj, 8.0) for obj in atlas.objects)
        report = chart_unwrap(atlas)
        report["long_edges_cut"] = cut
        return report
    select_only(atlas.objects)
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=atlas.margin)
    bpy.ops.object.mode_set(mode="OBJECT")
    return {}


def isolate_materials(atlases):
    owner = {obj.name: atlas.name for atlas in atlases for obj in atlas.objects}
    for atlas in atlases:
        for obj in atlas.objects:
            for slot in obj.material_slots:
                material = slot.material
                if not bakeable(material):
                    continue
                shared = any(other.type == "MESH" and owner.get(other.name) != atlas.name
                             and any(s.material == material for s in other.material_slots)
                             for other in bpy.data.objects)
                if shared:
                    copy = bpy.data.materials.get(f"{material.name}_{atlas.name}") or material.copy()
                    copy.name = f"{material.name}_{atlas.name}"
                    slot.material = copy


def atlas_materials(atlas):
    found = []
    for obj in atlas.objects:
        for slot in obj.material_slots:
            if bakeable(slot.material) and slot.material not in found:
                found.append(slot.material)
    return found


def target_node(material, image):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    for node in [node for node in nodes if node.label == NODE_LABEL]:
        nodes.remove(node)
    texture = nodes.new("ShaderNodeTexImage")
    texture.label = NODE_LABEL
    texture.image = image
    texture.interpolation = "Linear"
    coordinates = nodes.new("ShaderNodeUVMap")
    coordinates.label = NODE_LABEL
    coordinates.uv_map = LIGHTMAP
    links.new(coordinates.outputs["UV"], texture.inputs["Vector"])
    nodes.active = texture
    return texture


def wire_occlusion(material, texture):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    separate = nodes.new("ShaderNodeSeparateColor")
    separate.label = NODE_LABEL
    output = nodes.new("ShaderNodeGroup")
    output.label = NODE_LABEL
    output.node_tree = gltf_output_group()
    links.new(texture.outputs["Color"], separate.inputs["Color"])
    links.new(separate.outputs["Red"], output.inputs["Occlusion"])


def smooth(pixels, passes):
    for _ in range(passes):
        padded = np.pad(pixels, 1, mode="edge")
        pixels = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] + 4 * pixels) / 8
    return pixels


def bake_atlas(atlas, folder):
    image = bpy.data.images.get(f"ao_{atlas.name}")
    if image is not None:
        bpy.data.images.remove(image)
    image = bpy.data.images.new(f"ao_{atlas.name}", atlas.size, atlas.size, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(np.ones(atlas.size * atlas.size * 4, dtype=np.float32))
    textures = {material.name: target_node(material, image) for material in atlas_materials(atlas)}
    scene = bpy.context.scene
    scene.cycles.samples = atlas.samples
    scene.world.light_settings.distance = atlas.distance
    select_only(atlas.objects)
    start = time.perf_counter()
    bpy.ops.object.bake(type="AO", uv_layer=LIGHTMAP, margin=max(2, int(atlas.size * atlas.margin / 2)),
                        margin_type="EXTEND", use_clear=False)
    seconds = time.perf_counter() - start
    pixels = np.empty(atlas.size * atlas.size * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(atlas.size, atlas.size, 4)
    grey = 1.0 - atlas.strength * (1.0 - smooth(pixels[..., 0], 1))
    pixels[..., :3] = grey[..., None]
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = os.path.join(folder, f"ao_{atlas.name}.png")
    image.file_format = "PNG"
    os.makedirs(folder, exist_ok=True)
    image.save()
    for material in atlas_materials(atlas):
        wire_occlusion(material, textures[material.name])
    return {"seconds": round(seconds, 1), "size": atlas.size, "materials": sorted(textures),
            "mean": round(float(grey.mean()), 3), "p01": round(float(np.percentile(grey, 1)), 3)}


def bake_occlusion(atlases, occluders, folder):
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BakeWorld")
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    casting = {obj.name for atlas in atlases for obj in atlas.objects} | {obj.name for obj in occluders}
    hidden = [obj for obj in scene.objects if obj.type == "MESH" and obj.name not in casting and not obj.hide_render]
    for obj in hidden:
        obj.hide_render = True
    isolate_materials(atlases)
    report = {}
    start = time.perf_counter()
    for atlas in atlases:
        unwrap_start = time.perf_counter()
        report[atlas.name] = unwrap(atlas)
        report[atlas.name]["unwrap_seconds"] = round(time.perf_counter() - unwrap_start, 1)
        report[atlas.name].update(bake_atlas(atlas, folder))
    for obj in hidden:
        obj.hide_render = False
    scene.render.engine = engine
    report["total_seconds"] = round(time.perf_counter() - start, 1)
    return report


def bake_scene(options, atlases, occluders, folder):
    if options.get("bake") != "1":
        return None
    samples = int(options.get("bake_samples", 64))
    chosen = [Atlas(name, [bpy.data.objects[key] for key in keys], size, distance, unwrap, samples, *margin)
              for name, keys, size, distance, unwrap, *margin in atlases]
    report = bake_occlusion(chosen, [bpy.data.objects[key] for key in occluders], folder)
    print("BAKE", json.dumps(report), flush=True)
    return report


def rebake_scene(options, blend, glb, atlases, occluders, folder):
    started = time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=blend)
    report = bake_scene(options, atlases, occluders, folder)
    roots = [obj for obj in bpy.context.scene.objects if obj.parent is None]
    export_seconds = export_glb(glb, roots)
    print("REBAKE", json.dumps({"bake": report, "export_seconds": round(export_seconds, 1),
                                "glb_bytes": os.path.getsize(glb),
                                "total_seconds": round(time.perf_counter() - started, 1)}), flush=True)
