import math

import bpy
from mathutils import Matrix, Vector

UP = Vector((0.0, 0.0, 1.0))
VOID_MATERIAL = "shadow_void"
VOID_TINT = (0.16, 0.14, 0.12)
MATTE = "matte"
ALIASES = {
    "plaster": ("plaster", (0.97, 0.945, 0.9)),
    "plaster_white": ("plaster", (1.0, 1.0, 0.99)),
    "plaster_ochre": ("plaster", (0.93, 0.75, 0.54)),
    "plaster_rose": ("plaster", (0.96, 0.82, 0.74)),
    "plaster_cream": ("plaster", (0.99, 0.93, 0.8)),
    "plaster_grey": ("plaster", (0.86, 0.85, 0.82)),
    "plaster_red": ("plaster", (0.78, 0.42, 0.32)),
    "foliage_dark": (MATTE, (0.22, 0.29, 0.16)),
    "foliage_cypress": (MATTE, (0.17, 0.24, 0.13)),
    "foliage_olive": (MATTE, (0.45, 0.49, 0.36)),
    "foliage_plane": (MATTE, (0.36, 0.45, 0.2)),
    "foliage_vine": (MATTE, (0.38, 0.47, 0.2)),
    "foliage_shrub": (MATTE, (0.25, 0.34, 0.17)),
    "garrigue": (MATTE, (0.33, 0.36, 0.24)),
    "garden_green": (MATTE, (0.34, 0.4, 0.2)),
    "bark": (MATTE, (0.4, 0.33, 0.26)),
    "dark_wood": (MATTE, (0.36, 0.25, 0.17)),
    "painted_red": (MATTE, (0.62, 0.17, 0.12)),
}


def placement(x=0.0, y=0.0, z=0.0, rotation_z=0.0, scale=1.0):
    scale_vector = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    scale_matrix = Matrix.Diagonal((*scale_vector, 1.0))
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rotation_z, 4, "Z") @ scale_matrix


def rotation_toward(direction, up=UP):
    forward = Vector(direction).normalized()
    side = forward.cross(up)
    if side.length < 1e-6:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()
    true_up = side.cross(forward).normalized()
    return Matrix((side, forward, true_up)).transposed().to_4x4()


def arc_points(center_x, center_z, radius, start_angle, end_angle, steps):
    return [
        (center_x + radius * math.cos(start_angle + (end_angle - start_angle) * index / steps),
         center_z + radius * math.sin(start_angle + (end_angle - start_angle) * index / steps))
        for index in range(steps + 1)
    ]


def newell_normal(points):
    normal = Vector((0.0, 0.0, 0.0))
    for index, current in enumerate(points):
        following = points[(index + 1) % len(points)]
        normal.x += (current[1] - following[1]) * (current[2] + following[2])
        normal.y += (current[2] - following[2]) * (current[0] + following[0])
        normal.z += (current[0] - following[0]) * (current[1] + following[1])
    return normal.normalized() if normal.length > 1e-12 else UP.copy()


def projected_uv_axes(normal):
    if abs(normal.z) > 0.999:
        return Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))
    u_axis = UP.cross(normal).normalized()
    return u_axis, normal.cross(u_axis).normalized()


def occlusion(height, floor=0.74, reach=2.6):
    t = min(max(height / reach, 0.0), 1.0)
    return floor + (1.0 - floor) * t * t * (3 - 2 * t)


class MeshBuilder:
    def __init__(self):
        self.positions = []
        self.polygons = []
        self.polygon_materials = []
        self.polygon_smooth = []
        self.polygon_uvs = []
        self.polygon_colors = []
        self.materials = []
        self.heights = []

    def slot(self, material):
        if material not in self.materials:
            self.materials.append(material)
        return self.materials.index(material)

    def point(self, position, height=None):
        self.positions.append((float(position[0]), float(position[1]), float(position[2])))
        self.heights.append(float(position[2]) if height is None else height)
        return len(self.positions) - 1

    def points(self, positions):
        return [self.point(position) for position in positions]

    def face(self, indices, material, smooth=False, uvs=None, color=None, raw=False):
        if material in ALIASES and not raw:
            material, tint = ALIASES[material]
            color = tint if color is None else tuple(a * b for a, b in zip(color, tint))
        cleaned = []
        cleaned_uvs = []
        for position_in_face, index in enumerate(indices):
            if cleaned and cleaned[-1] == index:
                continue
            cleaned.append(index)
            if uvs is not None:
                cleaned_uvs.append(uvs[position_in_face])
        if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
            cleaned.pop()
            if uvs is not None:
                cleaned_uvs.pop()
        if len(set(cleaned)) < 3:
            return
        self.polygons.append(tuple(cleaned))
        self.polygon_materials.append(self.slot(material))
        self.polygon_smooth.append(smooth)
        self.polygon_uvs.append(cleaned_uvs if uvs is not None else None)
        self.polygon_colors.append(color)

    def tint(self, first_polygon, color):
        for index in range(first_polygon, len(self.polygons)):
            current = self.polygon_colors[index]
            self.polygon_colors[index] = color if current is None else tuple(a * b for a, b in zip(current, color))
        return self

    def paint(self, material, color):
        if material not in self.materials:
            return self
        slot = self.materials.index(material)
        for index, material_index in enumerate(self.polygon_materials):
            if material_index == slot:
                current = self.polygon_colors[index]
                self.polygon_colors[index] = color if current is None else tuple(a * b for a, b in zip(current, color))
        return self

    def local_uvs(self, indices):
        corners = [self.positions[index] for index in indices]
        u_axis, v_axis = projected_uv_axes(newell_normal(corners))
        return [(corner[0] * u_axis.x + corner[1] * u_axis.y + corner[2] * u_axis.z,
                 corner[0] * v_axis.x + corner[1] * v_axis.y + corner[2] * v_axis.z) for corner in corners]

    def polygon(self, positions, material, smooth=False, uvs=None, color=None):
        self.face(self.points(positions), material, smooth, uvs, color)

    def oriented(self, positions, normal, material, smooth=False):
        if newell_normal(positions).dot(Vector(normal)) < 0:
            positions = list(reversed(positions))
        self.polygon(positions, material, smooth)

    def triangle_count(self):
        return sum(len(indices) - 2 for indices in self.polygons)

    def merge(self, other, matrix=None, keep_local=False):
        transform = matrix if matrix is not None else Matrix.Identity(4)
        mirrored = transform.determinant() < 0
        offset = len(self.positions)
        for position, height in zip(other.positions, other.heights):
            self.point(transform @ Vector(position), height if keep_local else None)
        for indices, material_index, smooth, uvs, color in zip(
            other.polygons, other.polygon_materials, other.polygon_smooth, other.polygon_uvs, other.polygon_colors
        ):
            if keep_local and uvs is None:
                uvs = other.local_uvs(indices)
            shifted = [index + offset for index in indices]
            if mirrored:
                shifted.reverse()
                uvs = list(reversed(uvs)) if uvs is not None else None
            self.face(shifted, other.materials[material_index], smooth, uvs, color, raw=True)
        return self

    def box(self, minimum, maximum, material, matrix=None, bottom=True, top=True):
        x0, y0, z0 = minimum
        x1, y1, z1 = maximum
        corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if matrix is not None:
            corners = [matrix @ Vector(corner) for corner in corners]
        indices = self.points(corners)
        faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        if bottom:
            faces.append((0, 3, 2, 1))
        if top:
            faces.append((4, 5, 6, 7))
        for face in faces:
            self.face([indices[corner] for corner in face], material)
        return self

    def centered_box(self, center, size, material, matrix=None, bottom=True, top=True):
        half = [component / 2 for component in size]
        return self.box(
            (center[0] - half[0], center[1] - half[1], center[2] - half[2]),
            (center[0] + half[0], center[1] + half[1], center[2] + half[2]),
            material, matrix, bottom, top,
        )

    def prism(self, outline, z0, z1, material, matrix=None, top=True, bottom=True, smooth=False):
        transform = matrix if matrix is not None else Matrix.Identity(4)
        lower = self.points([transform @ Vector((x, y, z0)) for x, y in outline])
        upper = self.points([transform @ Vector((x, y, z1)) for x, y in outline])
        count = len(outline)
        for index in range(count):
            following = (index + 1) % count
            self.face([lower[index], lower[following], upper[following], upper[index]], material, smooth)
        if top:
            self.face(upper, material)
        if bottom:
            self.face(list(reversed(lower)), material)
        return self

    def lathe(self, profile, segments, material, smooth=True, matrix=None, radius_scale=None,
              start=0.0, sweep=2 * math.pi, caps=True):
        transform = matrix if matrix is not None else Matrix.Identity(4)
        full_circle = abs(sweep - 2 * math.pi) < 1e-6
        angle_count = segments if full_circle else segments + 1
        angles = [start + sweep * step / segments for step in range(angle_count)]
        rings = []
        for radius, height in profile:
            if radius < 1e-6:
                rings.append([self.point(transform @ Vector((0.0, 0.0, height)))] * angle_count)
                continue
            ring = []
            for angle in angles:
                local_radius = radius * (radius_scale(angle) if radius_scale else 1.0)
                ring.append(self.point(transform @ Vector((local_radius * math.cos(angle),
                                                           local_radius * math.sin(angle), height))))
            rings.append(ring)
        mean_radius = max(sum(radius for radius, _ in profile) / len(profile), 1e-3)
        for ring_index in range(len(rings) - 1):
            lower_height = profile[ring_index][1]
            upper_height = profile[ring_index + 1][1]
            for step in range(segments):
                following = (step + 1) % angle_count if full_circle else step + 1
                u0 = mean_radius * sweep * step / segments
                u1 = mean_radius * sweep * (step + 1) / segments
                self.face(
                    [rings[ring_index][step], rings[ring_index][following],
                     rings[ring_index + 1][following], rings[ring_index + 1][step]],
                    material, smooth,
                    [(u0, lower_height), (u1, lower_height), (u1, upper_height), (u0, upper_height)],
                )
        if caps and full_circle:
            if profile[0][0] > 1e-6:
                self.face(list(reversed(rings[0])), material)
            if profile[-1][0] > 1e-6:
                self.face(list(rings[-1]), material)
        return self

    def sweep(self, path, profile, material, closed=False, facade_normal=None, caps=True,
              smooth=False, matrix=None):
        transform = matrix if matrix is not None else Matrix.Identity(4)
        path = [Vector(point) for point in path]
        count = len(path)
        segment_count = count if closed else count - 1
        tangents = [(path[(index + 1) % count] - path[index]).normalized() for index in range(segment_count)]

        def frame_of(tangent):
            if facade_normal is None:
                outward = Vector((tangent.y, -tangent.x, 0.0)).normalized()
                return outward, UP.copy()
            normal = Vector(facade_normal).normalized()
            return normal, tangent.cross(normal).normalized()

        frames = []
        for index in range(count):
            previous_index = index - 1 if (closed or index > 0) else None
            next_index = index if (closed or index < count - 1) else None
            if previous_index is not None:
                previous_index %= segment_count
            candidates = [frame_of(tangents[i]) for i in (previous_index, next_index) if i is not None]
            if len(candidates) == 1:
                outward, upward = candidates[0]
                frames.append((outward, upward, 1.0, 1.0))
                continue
            if facade_normal is None:
                outward = (candidates[0][0] + candidates[1][0]).normalized()
                frames.append((outward, UP.copy(), 1.0 / max(outward.dot(candidates[1][0]), 0.2), 1.0))
            else:
                upward = (candidates[0][1] + candidates[1][1]).normalized()
                frames.append((candidates[0][0], upward, 1.0, 1.0 / max(upward.dot(candidates[1][1]), 0.2)))
        rings = []
        for point, (outward, upward, outward_scale, upward_scale) in zip(path, frames):
            rings.append(self.points([
                transform @ (point + outward * offset * outward_scale + upward * height * upward_scale)
                for offset, height in profile
            ]))
        outward0, upward0, _, _ = frames[0]
        handedness = outward0.cross(upward0).dot(tangents[0])
        profile_count = len(profile)
        for index in range(segment_count):
            following = (index + 1) % count
            for corner in range(profile_count - 1):
                quad = [rings[index][corner], rings[following][corner],
                        rings[following][corner + 1], rings[index][corner + 1]]
                if handedness > 0:
                    quad.reverse()
                self.face(quad, material, smooth)
            if profile[0] != profile[-1]:
                quad = [rings[index][profile_count - 1], rings[following][profile_count - 1],
                        rings[following][0], rings[index][0]]
                if handedness > 0:
                    quad.reverse()
                self.face(quad, material, smooth)
        if caps and not closed:
            start_cap = list(reversed(rings[0])) if handedness < 0 else list(rings[0])
            end_cap = list(rings[-1]) if handedness < 0 else list(reversed(rings[-1]))
            self.face(start_cap, material)
            self.face(end_cap, material)
        return self

    def surface(self, rows, material, smooth=False, closed=False, matrix=None, facing=None):
        transform = matrix if matrix is not None else Matrix.Identity(4)
        if facing is not None:
            first = [Vector(rows[0][0]), Vector(rows[0][1]), Vector(rows[1][1]), Vector(rows[1][0])]
            if newell_normal(first).dot(Vector(facing)) < 0:
                rows = list(reversed(rows))
        indexed = [self.points([transform @ Vector(point) for point in row]) for row in rows]
        width = len(rows[0])
        columns = width if closed else width - 1
        for row_index in range(len(rows) - 1):
            for column in range(columns):
                following = (column + 1) % width
                self.face([indexed[row_index][column], indexed[row_index][following],
                           indexed[row_index + 1][following], indexed[row_index + 1][column]], material, smooth)
        return self

    def absorb_voids(self):
        if VOID_MATERIAL not in self.materials or len(self.materials) < 2:
            return
        void = self.materials.index(VOID_MATERIAL)
        counts = {}
        for material_index in self.polygon_materials:
            if material_index != void and self.materials[material_index] not in ("water", "bronze_gilt"):
                counts[material_index] = counts.get(material_index, 0) + 1
        if not counts:
            return
        host = max(counts, key=counts.get)
        for index, material_index in enumerate(self.polygon_materials):
            if material_index == void:
                self.polygon_materials[index] = host
                self.polygon_colors[index] = VOID_TINT
        remap = {old: new for new, old in enumerate(i for i in range(len(self.materials)) if i != void)}
        self.polygon_materials = [remap[index] for index in self.polygon_materials]
        self.materials = [material for index, material in enumerate(self.materials) if index != void]

    def to_mesh(self, name, tile_sizes, ground_occlusion=True):
        self.absorb_voids()
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.positions, [], self.polygons)
        for material_name in self.materials:
            mesh.materials.append(bpy.data.materials[material_name])
        mesh.polygons.foreach_set("material_index", self.polygon_materials)
        mesh.polygons.foreach_set("use_smooth", self.polygon_smooth)
        uv_values = []
        for indices, material_index, explicit in zip(self.polygons, self.polygon_materials, self.polygon_uvs):
            tile = tile_sizes.get(self.materials[material_index], 2.0)
            if explicit is not None:
                uv_values.extend(component / tile for uv in explicit for component in uv)
                continue
            corners = [self.positions[index] for index in indices]
            u_axis, v_axis = projected_uv_axes(newell_normal(corners))
            for corner in corners:
                uv_values.append((corner[0] * u_axis.x + corner[1] * u_axis.y + corner[2] * u_axis.z) / tile)
                uv_values.append((corner[0] * v_axis.x + corner[1] * v_axis.y + corner[2] * v_axis.z) / tile)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        uv_layer.data.foreach_set("uv", uv_values)
        colors = []
        for indices, color in zip(self.polygons, self.polygon_colors):
            base = color or (1.0, 1.0, 1.0)
            for index in indices:
                shade = occlusion(self.heights[index]) if ground_occlusion else 1.0
                colors.extend((base[0] * shade, base[1] * shade, base[2] * shade, 1.0))
        attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        attribute.data.foreach_set("color_srgb", colors)
        mesh.color_attributes.active_color = attribute
        mesh.update()
        return mesh


def ensure_collection(name, parent=None):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(collection)
    return collection


def new_object(name, data, collection, parent=None, matrix=None):
    created = bpy.data.objects.new(name, data)
    collection.objects.link(created)
    if parent is not None:
        created.parent = parent
    if matrix is not None:
        created.matrix_basis = matrix
    return created


def new_empty(name, collection, parent=None, matrix=None, kind=None):
    empty = new_object(name, None, collection, parent, matrix)
    empty.empty_display_type = "PLAIN_AXES"
    if kind is not None:
        empty["kind"] = kind
    return empty


class TemplateLibrary:
    def __init__(self, tile_sizes):
        self.tile_sizes = tile_sizes
        self.meshes = {}
        self.builders = {}

    def mesh(self, key, build, ground_occlusion=True):
        if key not in self.meshes:
            builder = build()
            self.builders[key] = builder
            self.meshes[key] = builder.to_mesh(key, self.tile_sizes, ground_occlusion)
        return self.meshes[key]

    def place(self, key, build, collection, parent, matrices, cast_shadow=True, ground_occlusion=True):
        mesh = self.mesh(key, build, ground_occlusion)
        group = new_empty(f"group_{key}", collection, parent)
        group["cast_shadow"] = cast_shadow
        for index, matrix in enumerate(matrices):
            instance = new_object(f"{key}.{index:05d}", mesh, collection, group, matrix)
            instance["cast_shadow"] = cast_shadow
        return group


def unique_object(name, builder, collection, parent, tile_sizes, matrix=None, cast_shadow=True,
                  ground_occlusion=True):
    created = new_object(name, builder.to_mesh(name, tile_sizes, ground_occlusion), collection, parent, matrix)
    created["cast_shadow"] = cast_shadow
    return created
