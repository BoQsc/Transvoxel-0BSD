# SPDX-License-Identifier: 0BSD
extends Node3D

# Interactive evaluation sandbox.
# Godot is only a validator/sandbox here; the core product remains engine-independent.
# This script avoids := inference so Godot 4.6 stays strict-parser friendly.

const REGULAR_PATH: String = "res://generated/regular_tables.json"
const TRANSITION_PATH: String = "res://generated/transition_tables.json"
const SESSION_PATH: String = "res://validation/06_interactive_sandbox/session.json"
const SEAM_METRICS_PATHS: Array[String] = [
	"res://validation/03_seam_metrics/seam_metrics.json",
	"user://validation/03_seam_metrics/seam_metrics.json"
]

@export var field_mode: int = 0
@export var show_reference_meshes: bool = true
@export var show_transition_mesh: bool = true
@export var show_edit_markers: bool = true
@export var move_speed: float = 8.0
@export var look_sensitivity: float = 0.0025
@export var edit_radius: float = 1.15
@export var edit_distance: float = 7.0

var regular_table: Dictionary = {}
var transition_table: Dictionary = {}
var edits: Array = []
var edit_checks: Array = []
var wireframe: bool = false
var mouse_locked: bool = false

var camera: Camera3D
var label: Label3D
var root_meshes: Node3D
var root_markers: Node3D

var mat_high: StandardMaterial3D
var mat_low: StandardMaterial3D
var mat_transition: StandardMaterial3D
var mat_marker_dig: StandardMaterial3D
var mat_marker_add: StandardMaterial3D
var mat_text: StandardMaterial3D

var last_report: Dictionary = {}

func _ready() -> void:
	_make_materials()
	regular_table = _load_json(REGULAR_PATH)
	transition_table = _load_json(TRANSITION_PATH)
	_setup_scene()
	_rebuild_world("startup")
	_print_help()

func _setup_scene() -> void:
	root_meshes = Node3D.new()
	root_meshes.name = "meshes"
	add_child(root_meshes)
	root_markers = Node3D.new()
	root_markers.name = "edit_markers"
	add_child(root_markers)

	var light: DirectionalLight3D = DirectionalLight3D.new()
	light.name = "sun"
	light.rotation_degrees = Vector3(-55.0, -35.0, 0.0)
	light.light_energy = 2.5
	add_child(light)

	camera = Camera3D.new()
	camera.name = "camera"
	camera.current = true
	camera.position = Vector3(7.0, 5.5, 15.0)
	camera.rotation_degrees = Vector3(-22.0, 28.0, 0.0)
	add_child(camera)

	label = Label3D.new()
	label.name = "status_label"
	label.position = Vector3(-5.0, 6.0, -4.0)
	label.pixel_size = 0.018
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.text = "Transvoxel 0BSD sandbox"
	add_child(label)

func _make_materials() -> void:
	mat_high = _make_mat(Color(0.20, 0.55, 1.0, 1.0))
	mat_low = _make_mat(Color(0.55, 0.35, 1.0, 1.0))
	mat_transition = _make_mat(Color(1.0, 0.55, 0.12, 1.0))
	mat_marker_dig = _make_mat(Color(1.0, 0.10, 0.08, 0.7))
	mat_marker_add = _make_mat(Color(0.20, 1.0, 0.20, 0.7))
	mat_text = _make_mat(Color(1.0, 1.0, 1.0, 1.0))

func _make_mat(color: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	# Godot 4.6 StandardMaterial3D does not expose a stable per-material wireframe property.
	# Wireframe is tracked in the session report and should be handled by viewport/debug draw in future UI polish.
	if color.a < 1.0:
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return material

func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("missing JSON " + path)
		return {}
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed as Dictionary
	push_error("bad JSON " + path)
	return {}


func _load_optional_json(paths: Array[String]) -> Dictionary:
	for path in paths:
		if FileAccess.file_exists(path):
			var text: String = FileAccess.get_file_as_string(path)
			var parsed: Variant = JSON.parse_string(text)
			if typeof(parsed) == TYPE_DICTIONARY:
				var result: Dictionary = parsed as Dictionary
				result["_loaded_from"] = path
				return result
	return {}

func _count_edits(mode: String) -> int:
	var count: int = 0
	for item in edits:
		if typeof(item) == TYPE_DICTIONARY:
			var edit: Dictionary = item as Dictionary
			if str(edit.get("mode", "")) == mode:
				count += 1
	return count

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mouse_button: InputEventMouseButton = event as InputEventMouseButton
		if mouse_button.pressed:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
			mouse_locked = true
	if event is InputEventMouseMotion and mouse_locked:
		var motion: InputEventMouseMotion = event as InputEventMouseMotion
		camera.rotate_y(-motion.relative.x * look_sensitivity)
		camera.rotate_object_local(Vector3.RIGHT, -motion.relative.y * look_sensitivity)
		camera.rotation.x = clampf(camera.rotation.x, -1.45, 1.45)
	if event is InputEventKey:
		var key_event: InputEventKey = event as InputEventKey
		if key_event.pressed and not key_event.echo:
			_handle_key(key_event.keycode)

func _handle_key(keycode: int) -> void:
	match keycode:
		KEY_ESCAPE:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
			mouse_locked = false
		KEY_1:
			field_mode = 0
			_rebuild_world("field_0")
		KEY_2:
			field_mode = 1
			_rebuild_world("field_1")
		KEY_3:
			field_mode = 2
			_rebuild_world("field_2")
		KEY_4:
			field_mode = 3
			_rebuild_world("field_3")
		KEY_5:
			field_mode = 4
			_rebuild_world("field_4")
		KEY_6:
			field_mode = 5
			_rebuild_world("field_5")
		KEY_E:
			_add_edit("dig")
		KEY_Q:
			_add_edit("add")
		KEY_R:
			edits.clear()
			edit_checks.clear()
			_rebuild_world("reset")
		KEY_F:
			_rebuild_world("manual_rebuild")
		KEY_T:
			show_transition_mesh = not show_transition_mesh
			_rebuild_world("toggle_transition")
		KEY_L:
			show_reference_meshes = not show_reference_meshes
			_rebuild_world("toggle_reference")
		KEY_O:
			show_edit_markers = not show_edit_markers
			_rebuild_world("toggle_markers")
		KEY_V:
			wireframe = not wireframe
			_make_materials()
			_rebuild_world("toggle_wireframe")
		KEY_H:
			_print_help()

func _physics_process(delta: float) -> void:
	if camera == null:
		return
	var direction: Vector3 = Vector3.ZERO
	if Input.is_key_pressed(KEY_W):
		direction -= camera.global_transform.basis.z
	if Input.is_key_pressed(KEY_S):
		direction += camera.global_transform.basis.z
	if Input.is_key_pressed(KEY_A):
		direction -= camera.global_transform.basis.x
	if Input.is_key_pressed(KEY_D):
		direction += camera.global_transform.basis.x
	if Input.is_key_pressed(KEY_SPACE):
		direction += Vector3.UP
	if Input.is_key_pressed(KEY_CTRL):
		direction -= Vector3.UP
	if direction.length() > 0.0:
		camera.global_position += direction.normalized() * move_speed * delta

func _print_help() -> void:
	print("=== Transvoxel 0BSD interactive sandbox ===")
	print("WASD move, mouse look after click, Space/Ctrl up/down")
	print("1..6 fields, E dig, Q add, R reset, F rebuild")
	print("T transition, L reference LOD meshes, O edit markers, V wireframe, Esc mouse release")

func _add_edit(mode: String) -> void:
	var target: Vector3 = camera.global_position - camera.global_transform.basis.z * edit_distance
	var edit: Dictionary = {"sequence": edits.size() + 1, "mode": mode, "position": [target.x, target.y, target.z], "radius": edit_radius}
	edits.append(edit)
	_rebuild_world("edit_" + mode)

func _clear_node_children(node: Node) -> void:
	for child in node.get_children():
		child.queue_free()

func _rebuild_world(reason: String) -> void:
	if regular_table.is_empty() or transition_table.is_empty():
		label.text = "missing generated tables"
		return
	_clear_node_children(root_meshes)
	_clear_node_children(root_markers)
	var high_stats: Dictionary = {"vertices": 0, "triangles": 0}
	var low_stats: Dictionary = {"vertices": 0, "triangles": 0}
	var trans_stats: Dictionary = {"vertices": 0, "triangles": 0}
	if show_reference_meshes:
		high_stats = _build_regular_chunk("high_lod0", Vector3(0.0, -2.0, -6.0), Vector3i(12, 7, 6), 1.0, mat_high)
		low_stats = _build_regular_chunk("low_lod1", Vector3(0.0, -2.0, 1.0), Vector3i(6, 4, 4), 2.0, mat_low)
	if show_transition_mesh:
		trans_stats = _build_transition_strip(Vector3(0.0, -2.0, 0.0), Vector2i(6, 4), 1.0)
	if show_edit_markers:
		_build_edit_markers()
	var seam_check: Dictionary = _sandbox_seam_check(Vector3(0.0, -2.0, 0.0), Vector2i(6, 4), 1.0)
	if reason.begins_with("edit_") and edits.size() > 0:
		var last_edit: Dictionary = edits[edits.size() - 1] as Dictionary
		last_edit["seam_after_edit"] = seam_check
		edits[edits.size() - 1] = last_edit
		edit_checks.append({
			"sequence": last_edit.get("sequence", edits.size()),
			"mode": last_edit.get("mode", "unknown"),
			"position": last_edit.get("position", []),
			"radius": last_edit.get("radius", 0.0),
			"seam_after_edit": seam_check
		})
	last_report = _make_session_report(reason, high_stats, low_stats, trans_stats, seam_check)
	_write_session_report(last_report)
	_update_label(last_report)

func _make_session_report(reason: String, high_stats: Dictionary, low_stats: Dictionary, trans_stats: Dictionary, seam_check: Dictionary) -> Dictionary:
	var seam_reference: Dictionary = _load_optional_json(SEAM_METRICS_PATHS)
	var report: Dictionary = {}
	report["schema"] = "boqsc.transvoxel.interactive_session.v1"
	report["status"] = "INTERACTIVE_SESSION_WRITTEN"
	report["reason"] = reason
	report["field_mode"] = field_mode
	report["edit_count"] = edits.size()
	report["dig_count"] = _count_edits("dig")
	report["add_count"] = _count_edits("add")
	report["show_reference_meshes"] = show_reference_meshes
	report["show_transition_mesh"] = show_transition_mesh
	report["wireframe"] = wireframe
	report["high_lod0"] = high_stats
	report["low_lod1"] = low_stats
	report["transition"] = trans_stats
	report["sandbox_seam_check"] = seam_check
	report["seam_open_edges"] = seam_check.get("seam_open_edges", "not_checked")
	report["invalid_triangles"] = seam_check.get("invalid_triangles", "not_checked")
	report["degenerate_triangles"] = seam_check.get("degenerate_triangles", "not_checked")
	report["edit_checks"] = edit_checks
	report["machine_gate_reference"] = {
		"status": seam_reference.get("status", "not_loaded_for_interactive"),
		"loaded_from": seam_reference.get("_loaded_from", "not_loaded"),
		"seam_open_edges": seam_reference.get("seam_open_edges", "not_loaded"),
		"invalid_triangles": seam_reference.get("invalid_triangles", "not_loaded"),
		"degenerate_triangles": seam_reference.get("degenerate_triangles", "not_loaded")
	}
	report["edits"] = edits
	return report

func _update_label(report: Dictionary) -> void:
	var gate: Dictionary = report.get("machine_gate_reference", {}) as Dictionary
	var high_stats: Dictionary = report.get("high_lod0", {}) as Dictionary
	var low_stats: Dictionary = report.get("low_lod1", {}) as Dictionary
	var trans_stats: Dictionary = report.get("transition", {}) as Dictionary
	label.text = "Transvoxel 0BSD sandbox\n"
	label.text += "field=" + str(field_mode) + " edits=" + str(edits.size()) + " wire=" + str(wireframe) + "\n"
	label.text += "high tris=" + str(high_stats.get("triangles", 0)) + " low tris=" + str(low_stats.get("triangles", 0)) + " trans tris=" + str(trans_stats.get("triangles", 0)) + "\n"
	var sandbox_check: Dictionary = report.get("sandbox_seam_check", {}) as Dictionary
	label.text += "machine gate ref: " + str(gate.get("status", "missing")) + " seam_open_edges=" + str(gate.get("seam_open_edges", "missing")) + "\n"
	label.text += "sandbox after edits: " + str(sandbox_check.get("status", "missing")) + " seam_open_edges=" + str(sandbox_check.get("seam_open_edges", "missing")) + "\n"
	label.text += "E dig, Q add, R reset, H help"

func _write_session_report(report: Dictionary) -> void:
	var dir_path: String = SESSION_PATH.get_base_dir()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))
	var file: FileAccess = FileAccess.open(SESSION_PATH, FileAccess.WRITE)
	if file == null:
		push_error("cannot write " + SESSION_PATH)
		return
	file.store_string(JSON.stringify(report, "\t"))
	file.close()

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
	var value: float = 0.0
	match field_mode:
		0:
			value = p.y - (1.35 + 0.15 * p.x - 0.07 * p.z)
		1:
			value = (p - Vector3(6.0, 1.8, -0.5)).length() - 4.0
		2:
			var q: Vector2 = Vector2(p.x - 5.5, p.y - 0.8)
			value = q.length() - (1.55 + 0.18 * sin(p.z * 1.25))
		3:
			value = p.y - (1.2 + 0.04 * (p.x - 6.0) * (p.z + 1.5))
		4:
			value = p.y - (1.45 + 0.35 * sin(p.x * 0.65) + 0.22 * cos(p.z * 1.1))
		5:
			var ground: float = p.y - (1.45 + 0.12 * p.x - 0.07 * p.z)
			var cave: float = 1.3 - (p - Vector3(5.2, 1.1, -0.7)).length()
			value = min(ground, -cave)
		_:
			value = p.y - 1.0
	for raw_edit in edits:
		var edit: Dictionary = raw_edit as Dictionary
		var pos_array: Array = edit.get("position", [0.0, 0.0, 0.0]) as Array
		var center: Vector3 = Vector3(float(pos_array[0]), float(pos_array[1]), float(pos_array[2]))
		var radius: float = float(edit.get("radius", 1.0))
		var influence: float = radius - p.distance_to(center)
		if influence > 0.0:
			var mode: String = String(edit.get("mode", "dig"))
			if mode == "dig":
				value = max(value, influence)
			else:
				value = min(value, -influence)
	return value

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
	return _mesh_from_arrays(vertices, indices)

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

func _add_mesh(mesh_name: String, mesh: ArrayMesh, material: StandardMaterial3D) -> void:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = mesh_name
	mi.mesh = mesh
	mi.material_override = material
	root_meshes.add_child(mi)

func _build_regular_chunk(prefix: String, origin: Vector3, cells: Vector3i, size: float, material: StandardMaterial3D) -> Dictionary:
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
	return {"vertices": surface_vertices.size(), "triangles": int(surface_indices.size() / 3)}

func _build_transition_strip(origin: Vector3, cells: Vector2i, scale: float) -> Dictionary:
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
	var final_mesh: ArrayMesh = _mesh_from_arrays(surface_vertices, surface_indices)
	_add_mesh("transition_strip", final_mesh, mat_transition)
	return {"vertices": surface_vertices.size(), "triangles": int(surface_indices.size() / 3)}


func _sign_at_transition_sample(cell_origin: Vector3, scale: float, sample_id: int, sample_pos: Dictionary) -> int:
	var sid: int = sample_id
	if sid == 9:
		sid = 0
	elif sid == 10:
		sid = 2
	elif sid == 11:
		sid = 6
	elif sid == 12:
		sid = 8
	elif sid == 13:
		sid = 4
	var p: Vector3 = cell_origin + (sample_pos[sid] as Vector3) * scale
	if _density(p) < 0.0:
		return 1
	return 0

func _side_pattern(cell_origin: Vector3, scale: float, face: String, sample_pos: Dictionary) -> Array:
	var ids: Array = []
	if face == "x_min":
		ids = [0, 3, 6, 9, 11]
	elif face == "x_max":
		ids = [2, 5, 8, 10, 12]
	elif face == "y_min":
		ids = [0, 1, 2, 9, 10]
	elif face == "y_max":
		ids = [6, 7, 8, 11, 12]
	var pattern: Array = []
	for raw_id in ids:
		pattern.append(_sign_at_transition_sample(cell_origin, scale, int(raw_id), sample_pos))
	return pattern

func _patterns_equal(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in range(a.size()):
		if int(a[i]) != int(b[i]):
			return false
	return true

func _transition_case_for_cell(cell_origin: Vector3, scale: float, sample_pos: Dictionary) -> int:
	var signs: Array = []
	for i in range(9):
		var p: Vector3 = cell_origin + (sample_pos[i] as Vector3) * scale
		signs.append(_density(p))
	return _case_from_signs(signs)

func _inspect_transition_case(case_index: int) -> Dictionary:
	var cases: Array = transition_table.get("cases", []) as Array
	var invalid: int = 0
	var degenerate: int = 0
	var triangle_count: int = 0
	var vertex_count: int = 0
	if case_index < 0 or case_index >= cases.size():
		return {"invalid_triangles": 1, "degenerate_triangles": 0, "triangles": 0, "vertices": 0}
	var case_data: Dictionary = cases[case_index] as Dictionary
	var vertices: Array = case_data.get("vertices", []) as Array
	var triangles: Array = case_data.get("triangles", []) as Array
	vertex_count = vertices.size()
	for raw_tri in triangles:
		var tri: Dictionary = raw_tri as Dictionary
		var ids: Array = tri.get("vertices", []) as Array
		if ids.size() != 3:
			invalid += 1
			continue
		var a: int = int(ids[0])
		var b: int = int(ids[1])
		var c: int = int(ids[2])
		if a < 0 or b < 0 or c < 0 or a >= vertex_count or b >= vertex_count or c >= vertex_count:
			invalid += 1
		elif a == b or b == c or a == c:
			degenerate += 1
		triangle_count += 1
	return {"invalid_triangles": invalid, "degenerate_triangles": degenerate, "triangles": triangle_count, "vertices": vertex_count}

func _sandbox_seam_check(origin: Vector3, cells: Vector2i, scale: float) -> Dictionary:
	var sample_pos: Dictionary = _sample_positions(transition_table)
	var mismatches: int = 0
	var invalid: int = 0
	var degenerate: int = 0
	var checked_faces: int = 0
	var checked_cells: int = 0
	var first_failures: Array = []
	for x in range(cells.x):
		for y in range(cells.y):
			var cell_origin: Vector3 = origin + Vector3(float(x) * 2.0 * scale, float(y) * 2.0 * scale, 0.0)
			var ci: int = _transition_case_for_cell(cell_origin, scale, sample_pos)
			var info: Dictionary = _inspect_transition_case(ci)
			invalid += int(info.get("invalid_triangles", 0))
			degenerate += int(info.get("degenerate_triangles", 0))
			checked_cells += 1
			if x + 1 < cells.x:
				var neighbor_x: Vector3 = origin + Vector3(float(x + 1) * 2.0 * scale, float(y) * 2.0 * scale, 0.0)
				var left_pattern: Array = _side_pattern(cell_origin, scale, "x_max", sample_pos)
				var right_pattern: Array = _side_pattern(neighbor_x, scale, "x_min", sample_pos)
				checked_faces += 1
				if not _patterns_equal(left_pattern, right_pattern):
					mismatches += 1
					if first_failures.size() < 12:
						first_failures.append({"face": "x", "cell": [x, y], "a": left_pattern, "b": right_pattern})
			if y + 1 < cells.y:
				var neighbor_y: Vector3 = origin + Vector3(float(x) * 2.0 * scale, float(y + 1) * 2.0 * scale, 0.0)
				var bottom_pattern: Array = _side_pattern(cell_origin, scale, "y_max", sample_pos)
				var top_pattern: Array = _side_pattern(neighbor_y, scale, "y_min", sample_pos)
				checked_faces += 1
				if not _patterns_equal(bottom_pattern, top_pattern):
					mismatches += 1
					if first_failures.size() < 12:
						first_failures.append({"face": "y", "cell": [x, y], "a": bottom_pattern, "b": top_pattern})
	var status: String = "PASS"
	if mismatches != 0 or invalid != 0 or degenerate != 0:
		status = "FAIL"
	return {
		"schema": "boqsc.transvoxel.interactive_edit_seam_check.v1",
		"status": status,
		"meaning": "Per-edit sandbox check: after the current edit stack, adjacent transition cells in the interactive strip still expose matching side-face sign patterns. This is an interactive regression check, not a replacement for the full production gate.",
		"seam_open_edges": mismatches,
		"side_pattern_mismatches": mismatches,
		"invalid_triangles": invalid,
		"degenerate_triangles": degenerate,
		"checked_transition_cells": checked_cells,
		"checked_shared_faces": checked_faces,
		"field_mode": field_mode,
		"edit_count": edits.size(),
		"first_failures": first_failures
	}

func _build_edit_markers() -> void:
	for raw_edit in edits:
		var edit: Dictionary = raw_edit as Dictionary
		var pos_array: Array = edit.get("position", [0.0, 0.0, 0.0]) as Array
		var radius: float = float(edit.get("radius", 1.0))
		var mode: String = String(edit.get("mode", "dig"))
		var sphere: SphereMesh = SphereMesh.new()
		sphere.radius = radius
		sphere.height = radius * 2.0
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = "edit_" + mode
		mi.mesh = sphere
		mi.position = Vector3(float(pos_array[0]), float(pos_array[1]), float(pos_array[2]))
		if mode == "dig":
			mi.material_override = mat_marker_dig
		else:
			mi.material_override = mat_marker_add
		root_markers.add_child(mi)
