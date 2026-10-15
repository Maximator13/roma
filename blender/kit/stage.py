import math
import os
import time

import bpy
from mathutils import Vector

from .geometry import new_object


def sun_vector(azimuth_degrees, elevation_degrees):
    azimuth = math.radians(azimuth_degrees)
    elevation = math.radians(elevation_degrees)
    return Vector((math.sin(azimuth) * math.cos(elevation), math.cos(azimuth) * math.cos(elevation),
                   math.sin(elevation)))


def evening_world(azimuth_degrees, elevation_degrees, sky_strength, aerosol=0.4):
    world = bpy.data.worlds.new("EveningSky")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.sun_threshold = 0.0
    nodes = world.node_tree.nodes
    background = nodes["Background"]
    sky = nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(elevation_degrees)
    sky.sun_rotation = math.radians(azimuth_degrees) % math.tau
    sky.sun_disc = False
    sky.altitude = 60.0
    sky.aerosol_density = aerosol
    world.node_tree.links.new(sky.outputs["Color"], background.inputs["Color"])
    background.inputs["Strength"].default_value = sky_strength
    return world


def haze_volume(collection, half_extent, ceiling, density, color, glow):
    mesh = bpy.data.meshes.new("Haze")
    h = half_extent
    corners = [(-h, -h, -200.0), (h, -h, -200.0), (h, h, -200.0), (-h, h, -200.0),
               (-h, -h, ceiling), (h, -h, ceiling), (h, h, ceiling), (-h, h, ceiling)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(corners, [], faces)
    material = bpy.data.materials.new("Haze")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    absorption = nodes.new("ShaderNodeVolumeAbsorption")
    absorption.inputs["Density"].default_value = density
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1.0)
    emission.inputs["Strength"].default_value = density * glow
    total = nodes.new("ShaderNodeAddShader")
    links.new(absorption.outputs[0], total.inputs[0])
    links.new(emission.outputs[0], total.inputs[1])
    links.new(total.outputs[0], nodes["Material Output"].inputs["Volume"])
    mesh.materials.append(material)
    return new_object("Haze", mesh, collection)


def sun_lamp(collection, azimuth_degrees, elevation_degrees, strength, color, angle_degrees=0.6):
    data = bpy.data.lights.new("EveningSun", type="SUN")
    data.energy = strength
    data.color = color
    data.angle = math.radians(angle_degrees)
    lamp = new_object("EveningSun", data, collection)
    lamp.rotation_euler = sun_vector(azimuth_degrees, elevation_degrees).to_track_quat("Z", "Y").to_euler()
    return lamp


def configure_render(width, height, samples, exposure=0.0, volumetric_end=0.0):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    eevee = scene.eevee
    eevee.taa_render_samples = samples
    eevee.use_shadows = True
    eevee.shadow_resolution_scale = 1.0
    eevee.use_raytracing = False
    eevee.use_fast_gi = True
    eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
    if volumetric_end > 0:
        eevee.use_volume_custom_range = True
        eevee.volumetric_tile_size = "8"
        eevee.volumetric_samples = 48
        eevee.volumetric_start = 1.0
        eevee.volumetric_end = volumetric_end
        eevee.use_volumetric_shadows = True
        eevee.volumetric_shadow_samples = 16
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = exposure


def camera(collection, name, location, target, lens=35.0, clip_end=30000.0):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = max(0.3, Vector(location).z / 400.0)
    data.clip_end = clip_end
    rig = new_object(name, data, collection)
    rig.location = location
    rig.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return rig


def render_still(camera_object, path):
    scene = bpy.context.scene
    scene.camera = camera_object
    scene.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    return time.perf_counter() - start


def triangles_of(mesh):
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


def used_material_count(mesh):
    indices = [0] * len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", indices)
    return max(len(set(indices)), 1)


def mesh_groups(root):
    groups = {}
    stack = [root]
    while stack:
        current = stack.pop()
        stack.extend(current.children)
        if current.type != "MESH":
            continue
        key = (current.data.name, current.parent.name if current.parent else "", bool(current.children))
        groups.setdefault(key, []).append(current)
    return groups


def group_statistics(root_objects):
    statistics = {}
    total_draw_calls = 0
    total_triangles = 0
    for root in root_objects:
        unique = {}
        rendered = 0
        objects = 0
        draw_calls = 0
        for (mesh_name, _, has_children), members in mesh_groups(root).items():
            mesh = members[0].data
            if mesh_name not in unique:
                unique[mesh_name] = triangles_of(mesh)
            rendered += unique[mesh_name] * len(members)
            objects += len(members)
            batches = 1 if (len(members) > 1 and not has_children) else len(members)
            shadow_factor = 2 if members[0].get("cast_shadow", True) else 1
            draw_calls += batches * used_material_count(mesh) * shadow_factor
        statistics[root.name] = {"stored_triangles": sum(unique.values()), "rendered_triangles": rendered,
                                 "objects": objects, "unique_meshes": len(unique), "draw_calls": draw_calls}
        total_draw_calls += draw_calls
        total_triangles += rendered
    statistics["total"] = {"rendered_triangles": total_triangles, "draw_calls": total_draw_calls}
    return statistics


def export_glb(path, roots):
    bpy.ops.object.select_all(action="DESELECT")
    for root in roots:
        root.select_set(True)
        for child in root.children_recursive:
            child.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = time.perf_counter()
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_gpu_instances=True,
        export_extras=True,
        export_cameras=False,
        export_lights=False,
        export_yup=True,
        export_image_format="AUTO",
        export_materials="EXPORT",
        export_vertex_color="ACTIVE",
    )
    return time.perf_counter() - start
