# SPDX-License-Identifier: 0BSD
extends Node3D

# Runtime validation scene for the generated 0BSD Transvoxel tables.
# This script intentionally avoids external addons and does everything with core Godot APIs.
# It also avoids fragile type inference so Godot 4.6 does not fail on ambiguous numeric expressions.

const REGULAR_PATH: String = "res://generated/regular_tables.json"
const TRANSITION_PATH: String = "res://generated/transition_tables.json"
const TRANSVOXEL_PATH: String = "res://generated/transvoxel_tables.json"

@export var show_case_gallery: bool = true
@export var show_terrain_strip: bool = true
@export var show_sample_points: bool = false
@export_range(0, 511, 1) var single_transition_case: int = 85
@export_range(0, 5, 1) var field_mode: int = 0
@export var rebuild_now: bool = false:
	set(value):
		rebuild_now = false
		if value:
			call_deferred("build")

var regular_table: Dictionary = {}
var transition_table: Dictionary = {}
var transvoxel_table: Dictionary = {}
var wireframe: bool = false

var mat_regular: StandardMaterial3D
var mat_low: StandardMaterial3D
var mat_transition: StandardMaterial3D
var mat_debug: StandardMaterial3D
var mat_samples: StandardMaterial3D

func _ready() -> void:
	_make_materials()
	build()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		var key_event: InputEventKey = event as InputEventKey
		if key_event.pressed and not key_event.echo:
			match key_event.keycode:
				KEY_1:
					field_mode = 0
					build()
				KEY_2:
					field_mode = 1
					build()
				KEY_3:
					field_mode = 2
					build()
				KEY_4:
					field_mode = 3
					build()
				KEY_5:
					field_mode = 4
					build()
				KEY_6:
					field_mode = 5
					build()
				KEY_G:
					show_case_gallery = not show_case_gallery
					build()
				KEY_T:
					show_terrain_strip = not show_terrain_strip
					build()
				KEY_R:
					build()
				KEY_W:
					wireframe = not wireframe
					_make_materials()
					_apply_materials_recursive(self)

func _make_materials() -> void:
	mat_regular = _mat(Color(0.25, 0.55, 1.0, 1.0))
	mat_low = _mat(Color(0.55, 0.35, 1.0, 1.0))
	mat_transition = _mat(Color(1.0, 0.55, 0.15, 1.0))
	mat_debug = _mat(Color(1.0, 0.05, 0.05, 1.0))
	mat_samples = _mat(Color(1.0, 0.95, 0.25, 1.0))

func _mat(c: Color) -> StandardMaterial3D:
	var m: StandardMaterial3D = StandardMaterial3D.new()
	m.albedo_color = c
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	m.wireframe = wireframe
	return m

func _apply_materials_recursive(node: Node) -> void:
	for child in node.get_children():
		if child is MeshInstance3D:
			var mesh_instance: MeshInstance3D = child as MeshInstance3D
			var n: String = String(mesh_instance.name)
			if n.begins_with("high"):
				mesh_instance.material_override = mat_regular
			elif n.begins_with("low"):
				mesh_instance.material_override = mat_low
			elif n.begins_with("debug"):
				mesh_instance.material_override = mat_debug
			elif n.begins_with("sample"):
				mesh_instance.material_override = mat_samples
			else:
				mesh_instance.material_override = mat_transition
		_apply_materials_recursive(child)

func build() -> void:
	_clear()
	regular_table = _load_json(REGULAR_PATH)
	transition_table = _load_json(TRANSITION_PATH)
	transvoxel_table = _load_json(TRANSVOXEL_PATH)
	if regular_table.is_empty() or transition_table.is_empty():
		push_error("Missing generated table JSON files. See godot/README.md.")
		return

	_add_light_and_camera()
	if show_case_gallery:
		_build_case_gallery()
	if show_terrain_strip:
		_build_terrain_strip()
	_print_report()

func _clear() -> void:
	for child in get_children():
		child.queue_free()

func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Missing JSON: " + path)
		return {}
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Bad JSON: " + path)
		return {}
	return parsed as Dictionary

func _add_light_and_camera() -> void:
	var light: DirectionalLight3D = DirectionalLight3D.new()
	light.name = "DirectionalLight3D"
	light.rotation_degrees = Vector3(-55.0, -35.0, 0.0)
	light.light_energy = 2.5
	add_child(light)

	var cam: Camera3D = Camera3D.new()
	cam.name = "Camera3D"
	cam.position = Vector3(13.0, 11.0, 24.0)
	cam.rotation_degrees = Vector3(-30.0, 32.0, 0.0)
	cam.current = true
	add_child(cam)

func _sample_positions(table: Dictionary) -> Dictionary:
	var out: Dictionary = {}
	var items: Array = table.get("sample_positions", []) as Array
	for raw_item in items:
		var item: Dictionary = raw_item as Dictionary
		var p: Array = item.get("position", [0.0, 0.0, 0.0]) as Array
		var id: int = int(item.get("id", 0))
		out[id] = Vector3(float(p[0]), float(p[1]), float(p[2]))
	return out

func _case_from_signs(samples: Array) -> int:
	var index: int = 0
	for i in range(samples.size()):
		if float(samples[i]) < 0.0:
			index = index | (1 << i)
	return index

func _density(p: Vector3) -> float:
	match field_mode:
		0:
			return p.y - (1.3 + 0.18 * p.x - 0.08 * p.z)
		1:
			return (p - Vector3(5.0, 2.2, 0.5)).length() - 4.1
		2:
			var q: Vector2 = Vector2(p.x - 5.0, p.y - 1.2)
			return q.length() - (1.6 + 0.15 * sin(p.z * 1.4))
		3:
			return p.y - (1.7 + 0.03 * (p.x - 5.0) * (p.z + 3.0))
		4:
			return p.y - (1.5 + 0.35 * sin(p.x * 0.75) + 0.20 * cos(p.z * 1.2))
		5:
			var base: float = p.y - (1.4 + 0.15 * p.x - 0.08 * p.z)
			var cut: float = 1.2 - (p - Vector3(4.5, 1.5, 0.0)).length()
			return min(base, -cut)
	return p.y - 1.0

func _abs_float(v: float) -> float:
	if v < 0.0:
		return -v
	return v

func _interp_position(a: Vector3, b: Vector3, da: float, db: float) -> Vector3:
	var denom: float = _abs_float(da) + _abs_float(db)
	var t: float = 0.5
	if denom > 0.000001:
		t = _abs_float(da) / denom
	return a.lerp(b, clampf(t, 0.0, 1.0))

func _mesh_for_regular_cell(origin: Vector3, size: float, case_index: int, sample_densities: Array) -> ArrayMesh:
	var sample_pos: Dictionary = _sample_positions(regular_table)
	var cases: Array = regular_table.get("cases", []) as Array
	if case_index < 0 or case_index >= cases.size():
		return ArrayMesh.new()
	var case_data: Dictionary = cases[case_index] as Dictionary
	var vertices: PackedVector3Array = PackedVector3Array()
	var case_vertices: Array = case_data.get("vertices", []) as Array
	for raw_v in case_vertices:
		var v: Dictionary = raw_v as Dictionary
		var pair: Array = v.get("samples", [0, 0]) as Array
		var a_id: int = int(pair[0])
		var b_id: int = int(pair[1])
		var pa: Vector3 = origin + (sample_pos[a_id] as Vector3) * size
		var pb: Vector3 = origin + (sample_pos[b_id] as Vector3) * size
		vertices.append(_interp_position(pa, pb, float(sample_densities[a_id]), float(sample_densities[b_id])))
	return _mesh_from_case_vertices(case_data, vertices)

func _mesh_for_transition_cell(origin: Vector3, scale: float, case_index: int, sample_densities: Dictionary) -> ArrayMesh:
	var sample_pos: Dictionary = _sample_positions(transition_table)
	var cases: Array = transition_table.get("cases", []) as Array
	if case_index < 0 or case_index >= cases.size():
		return ArrayMesh.new()
	var case_data: Dictionary = cases[case_index] as Dictionary
	var vertices: PackedVector3Array = PackedVector3Array()
	var case_vertices: Array = case_data.get("vertices", []) as Array
	for raw_v in case_vertices:
		var v: Dictionary = raw_v as Dictionary
		var pair: Array = v.get("samples", [0, 0]) as Array
		var a_id: int = int(pair[0])
		var b_id: int = int(pair[1])
		var pa: Vector3 = origin + (sample_pos[a_id] as Vector3) * scale
		var pb: Vector3 = origin + (sample_pos[b_id] as Vector3) * scale
		vertices.append(_interp_position(pa, pb, float(sample_densities[a_id]), float(sample_densities[b_id])))
	return _mesh_from_case_vertices(case_data, vertices)

func _mesh_from_case_vertices(case_data: Dictionary, vertices: PackedVector3Array) -> ArrayMesh:
	var indices: PackedInt32Array = PackedInt32Array()
	var triangles: Array = case_data.get("triangles", []) as Array
	for raw_tri in triangles:
		var tri: Dictionary = raw_tri as Dictionary
		var ids: Array = tri.get("vertices", []) as Array
		if ids.size() == 3:
			indices.append(int(ids[0]))
			indices.append(int(ids[1]))
			indices.append(int(ids[2]))
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	if vertices.size() > 0 and indices.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh

func _add_mesh(mesh_name: String, mesh: ArrayMesh, material: StandardMaterial3D) -> void:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = mesh_name
	mi.mesh = mesh
	mi.material_override = material
	add_child(mi)

func _build_case_gallery() -> void:
	var cases: Array = [1, 2, 3, 7, 15, 31, 63, 85, 127, 170, 255, 341, 383, 447, 510, single_transition_case]
	var i: int = 0
	for raw_ci in cases:
		var ci: int = int(raw_ci)
		var origin: Vector3 = Vector3(float(i % 8) * 3.0, 0.0, float(i / 8) * 3.0 + 9.0)
		var mesh: ArrayMesh = _transition_case_mesh_flat(ci, origin, 1.0)
		_add_mesh("transition_case_%03d" % ci, mesh, mat_transition)
		i += 1

func _transition_case_mesh_flat(case_index: int, origin: Vector3, scale: float) -> ArrayMesh:
	var sample_pos: Dictionary = _sample_positions(transition_table)
	var densities: Dictionary = {}
	for raw_id in sample_pos.keys():
		var sid: int = int(raw_id)
		var source: int = sid
		if sid == 9:
			source = 0
		elif sid == 10:
			source = 2
		elif sid == 11:
			source = 6
		elif sid == 12:
			source = 8
		elif sid == 13:
			source = 4
		if source >= 0 and source <= 8:
			densities[sid] = -1.0 if ((case_index & (1 << source)) != 0) else 1.0
		else:
			densities[sid] = 1.0
	return _mesh_for_transition_cell(origin, scale, case_index, densities)

func _build_terrain_strip() -> void:
	_build_regular_chunk("high_lod_regular", Vector3(0.0, -1.0, -4.0), Vector3i(10, 5, 4), 1.0, mat_regular)
	_build_regular_chunk("low_lod_regular", Vector3(0.0, -1.0, 1.0), Vector3i(5, 3, 3), 2.0, mat_low)
	_build_transition_strip(Vector3(0.0, -1.0, 0.0), Vector2i(5, 3), 1.0)

func _build_regular_chunk(prefix: String, origin: Vector3, cells: Vector3i, size: float, material: StandardMaterial3D) -> void:
	var surface_vertices: PackedVector3Array = PackedVector3Array()
	var surface_indices: PackedInt32Array = PackedInt32Array()
	var sample_pos: Dictionary = _sample_positions(regular_table)
	for x in range(cells.x):
		for y in range(cells.y):
			for z in range(cells.z):
				var cell_origin: Vector3 = origin + Vector3(float(x), float(y), float(z)) * size
				var dens: Array = []
				for i in range(8):
					var p: Vector3 = cell_origin + (sample_pos[i] as Vector3) * size
					dens.append(_density(p))
				var ci: int = _case_from_signs(dens)
				if ci == 0 or ci == 255:
					continue
				var mesh: ArrayMesh = _mesh_for_regular_cell(cell_origin, size, ci, dens)
				_append_mesh(mesh, surface_vertices, surface_indices)
	var final_mesh: ArrayMesh = _mesh_from_arrays(surface_vertices, surface_indices)
	_add_mesh(prefix, final_mesh, material)

func _build_transition_strip(origin: Vector3, cells: Vector2i, scale: float) -> void:
	var surface_vertices: PackedVector3Array = PackedVector3Array()
	var surface_indices: PackedInt32Array = PackedInt32Array()
	var sample_pos: Dictionary = _sample_positions(transition_table)
	for x in range(cells.x):
		for y in range(cells.y):
			var cell_origin: Vector3 = origin + Vector3(float(x) * 2.0 * scale, float(y) * 2.0 * scale, 0.0)
			var full_dens: Array = []
			var dens: Dictionary = {}
			for raw_sid in sample_pos.keys():
				var sid: int = int(raw_sid)
				var p: Vector3 = cell_origin + (sample_pos[sid] as Vector3) * scale
				dens[sid] = _density(p)
			for i in range(9):
				full_dens.append(float(dens[i]))
			# Match generator sign-source rules for derived samples.
			dens[9] = dens[0]
			dens[10] = dens[2]
			dens[11] = dens[6]
			dens[12] = dens[8]
			dens[13] = dens[4]
			var ci: int = _case_from_signs(full_dens)
			if ci == 0 or ci == 511:
				continue
			var mesh: ArrayMesh = _mesh_for_transition_cell(cell_origin, scale, ci, dens)
			_append_mesh(mesh, surface_vertices, surface_indices)
			if show_sample_points:
				_add_sample_points(cell_origin, sample_pos, scale)
	var final_mesh: ArrayMesh = _mesh_from_arrays(surface_vertices, surface_indices)
	_add_mesh("transition_strip", final_mesh, mat_transition)
	var seam: int = _count_open_edges(surface_vertices, surface_indices)
	print("transition_strip vertices=", surface_vertices.size(), " triangles=", surface_indices.size() / 3, " open_edges_total=", seam)

func _append_mesh(mesh: ArrayMesh, vertices: PackedVector3Array, indices: PackedInt32Array) -> void:
	if mesh.get_surface_count() == 0:
		return
	var arrays: Array = mesh.surface_get_arrays(0)
	var v: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var ind: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var base: int = vertices.size()
	for p in v:
		vertices.append(p)
	for i in ind:
		indices.append(base + int(i))

func _mesh_from_arrays(vertices: PackedVector3Array, indices: PackedInt32Array) -> ArrayMesh:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	if vertices.size() > 0 and indices.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh

func _edge_key(a: Vector3, b: Vector3) -> String:
	var ia: Vector3i = Vector3i(roundi(a.x * 10000.0), roundi(a.y * 10000.0), roundi(a.z * 10000.0))
	var ib: Vector3i = Vector3i(roundi(b.x * 10000.0), roundi(b.y * 10000.0), roundi(b.z * 10000.0))
	var sa: String = "%d,%d,%d" % [ia.x, ia.y, ia.z]
	var sb: String = "%d,%d,%d" % [ib.x, ib.y, ib.z]
	if sa < sb:
		return sa + "|" + sb
	return sb + "|" + sa

func _count_open_edges(vertices: PackedVector3Array, indices: PackedInt32Array) -> int:
	var counts: Dictionary = {}
	for i in range(0, indices.size(), 3):
		var a: Vector3 = vertices[int(indices[i])]
		var b: Vector3 = vertices[int(indices[i + 1])]
		var c: Vector3 = vertices[int(indices[i + 2])]
		var edge_keys: Array = [_edge_key(a, b), _edge_key(b, c), _edge_key(c, a)]
		for raw_key in edge_keys:
			var key: String = String(raw_key)
			counts[key] = int(counts.get(key, 0)) + 1
	var open: int = 0
	for raw_key in counts.keys():
		var key: String = String(raw_key)
		if int(counts[key]) == 1:
			open += 1
	return open

func _add_sample_points(origin: Vector3, sample_pos: Dictionary, scale: float) -> void:
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = 0.045
	mesh.height = 0.09
	for raw_sid in sample_pos.keys():
		var sid: int = int(raw_sid)
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = "sample_%s" % str(sid)
		mi.mesh = mesh
		mi.material_override = mat_samples
		mi.position = origin + (sample_pos[sid] as Vector3) * scale
		add_child(mi)

func _print_report() -> void:
	var regular_cases: int = 0
	var transition_cases: int = 0
	if regular_table.has("cases"):
		regular_cases = (regular_table["cases"] as Array).size()
	if transition_table.has("cases"):
		transition_cases = (transition_table["cases"] as Array).size()
	print("=== Transvoxel 0BSD Godot validation ===")
	print("field_mode=", field_mode, " wireframe=", wireframe)
	print("regular_cases=", regular_cases, " transition_cases=", transition_cases)
	print("transvoxel_schema=", transvoxel_table.get("schema", "missing"))
	print("NOTE: Python proof suite remains authoritative for exhaustive case validation.")
