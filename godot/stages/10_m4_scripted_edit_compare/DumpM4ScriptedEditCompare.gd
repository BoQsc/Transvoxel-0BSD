# SPDX-License-Identifier: 0BSD
extends SceneTree

const DEFAULT_PATH: String = "res://generated/transition_tables.json"
const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/10_m4_scripted_edit_compare/m4_scripted_edit_compare.json"
const GRID_X: int = 8
const GRID_Y: int = 5

var _fields: Array = ["plane_x", "plane_y", "diagonal", "circle", "saddle", "hash_noise", "wavy"]

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed as Dictionary
	return {}

func _write_json(path: String, data: Dictionary) -> void:
	var dir_path: String = path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("cannot write " + path)
		return
	file.store_string(JSON.stringify(data, "\t"))
	file.close()

func _load_positions(table: Dictionary) -> Dictionary:
	var positions: Dictionary = {}
	var samples: Array = table.get("sample_positions", []) as Array
	if samples.is_empty():
		samples = table.get("samples", []) as Array
	for raw_sample in samples:
		var sample: Dictionary = raw_sample as Dictionary
		var pos: Array = sample.get("position", [0.0, 0.0, 0.0]) as Array
		positions[int(sample.get("id", -1))] = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	return positions

func _sample_position(positions: Dictionary, sample_id: int) -> Vector3:
	return positions.get(sample_id, Vector3.ZERO) as Vector3

func _edge_midpoint(positions: Dictionary, samples: Array, origin: Vector3, scale: float) -> Vector3:
	var a_id: int = int(samples[0])
	var b_id: int = int(samples[1])
	var a: Vector3 = origin + _sample_position(positions, a_id) * scale
	var b: Vector3 = origin + _sample_position(positions, b_id) * scale
	return (a + b) * 0.5

func _triangle_area2(vertices: PackedVector3Array, a_id: int, b_id: int, c_id: int) -> float:
	var a: Vector3 = vertices[a_id]
	var b: Vector3 = vertices[b_id]
	var c: Vector3 = vertices[c_id]
	return ((b - a).cross(c - a)).length_squared()

func _append_case_mesh(table: Dictionary, positions: Dictionary, case_index: int, origin: Vector3, scale: float, vertices: PackedVector3Array, indices: PackedInt32Array) -> Dictionary:
	var cases: Array = table.get("cases", []) as Array
	var result: Dictionary = {
		"case": case_index,
		"status": "PASS",
		"vertices": 0,
		"triangles": 0,
		"invalid_triangles": 0,
		"degenerate_triangles": 0
	}
	if case_index < 0 or case_index >= cases.size():
		result["status"] = "FAIL"
		result["invalid_triangles"] = 1
		return result
	var case_record: Dictionary = cases[case_index] as Dictionary
	var case_vertices: Array = case_record.get("vertices", []) as Array
	var base: int = vertices.size()
	for raw_vertex in case_vertices:
		var vertex: Dictionary = raw_vertex as Dictionary
		var samples: Array = vertex.get("samples", []) as Array
		if samples.size() < 2:
			result["status"] = "FAIL"
			result["invalid_triangles"] = int(result["invalid_triangles"]) + 1
			vertices.append(origin)
		else:
			vertices.append(_edge_midpoint(positions, samples, origin, scale))
	result["vertices"] = case_vertices.size()
	var triangles: Array = case_record.get("triangles", []) as Array
	for raw_triangle in triangles:
		var triangle: Dictionary = raw_triangle as Dictionary
		var ids: Array = triangle.get("vertices", []) as Array
		result["triangles"] = int(result["triangles"]) + 1
		if ids.size() != 3:
			result["status"] = "FAIL"
			result["invalid_triangles"] = int(result["invalid_triangles"]) + 1
			continue
		var a_local: int = int(ids[0])
		var b_local: int = int(ids[1])
		var c_local: int = int(ids[2])
		if a_local < 0 or b_local < 0 or c_local < 0 or a_local >= case_vertices.size() or b_local >= case_vertices.size() or c_local >= case_vertices.size():
			result["status"] = "FAIL"
			result["invalid_triangles"] = int(result["invalid_triangles"]) + 1
			continue
		if a_local == b_local or b_local == c_local or c_local == a_local:
			result["status"] = "FAIL"
			result["degenerate_triangles"] = int(result["degenerate_triangles"]) + 1
			continue
		var a_id: int = base + a_local
		var b_id: int = base + b_local
		var c_id: int = base + c_local
		if _triangle_area2(vertices, a_id, b_id, c_id) <= 0.0000001:
			result["status"] = "FAIL"
			result["degenerate_triangles"] = int(result["degenerate_triangles"]) + 1
			continue
		indices.append(a_id)
		indices.append(b_id)
		indices.append(c_id)
	return result

func _make_array_mesh(vertices: PackedVector3Array, indices: PackedInt32Array) -> ArrayMesh:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	if vertices.size() > 0 and indices.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh

func _mesh_summary(label: String, vertices: PackedVector3Array, indices: PackedInt32Array, invalid_triangles: int, degenerate_triangles: int) -> Dictionary:
	var mesh: ArrayMesh = _make_array_mesh(vertices, indices)
	var mdt_error: int = ERR_DOES_NOT_EXIST
	var mdt_vertices: int = 0
	var mdt_edges: int = 0
	var mdt_faces: int = 0
	if mesh.get_surface_count() > 0:
		var mdt: MeshDataTool = MeshDataTool.new()
		mdt_error = mdt.create_from_surface(mesh, 0)
		if mdt_error == OK:
			mdt_vertices = mdt.get_vertex_count()
			mdt_edges = mdt.get_edge_count()
			mdt_faces = mdt.get_face_count()
	var triangle_count: int = int(indices.size() / 3)
	var ok: bool = (
		mesh.get_surface_count() == 1
		and vertices.size() > 0
		and triangle_count > 0
		and mdt_error == OK
		and invalid_triangles == 0
		and degenerate_triangles == 0
	)
	return {
		"label": label,
		"status": "PASS" if ok else "FAIL",
		"surface_count": mesh.get_surface_count(),
		"array_vertex_count": vertices.size(),
		"index_count": indices.size(),
		"triangle_count": triangle_count,
		"mdt_create_error": mdt_error,
		"mdt_vertex_count": mdt_vertices,
		"mdt_edge_count": mdt_edges,
		"mdt_face_count": mdt_faces,
		"invalid_triangles": invalid_triangles,
		"degenerate_triangles": degenerate_triangles
	}

func _density_base(p: Vector3, field_id: int) -> float:
	if field_id == 0:
		return p.y - (1.35 + 0.15 * p.x - 0.07 * p.z)
	if field_id == 1:
		return (p - Vector3(6.0, 1.8, -0.5)).length() - 4.0
	if field_id == 2:
		var q: Vector2 = Vector2(p.x - 5.5, p.y - 0.8)
		return q.length() - (1.55 + 0.18 * sin(p.z * 1.25))
	if field_id == 3:
		return p.y - (1.2 + 0.04 * (p.x - 6.0) * (p.z + 1.5))
	if field_id == 4:
		return p.y - (1.45 + 0.35 * sin(p.x * 0.65) + 0.22 * cos(p.z * 1.1))
	if field_id == 5:
		var ground: float = p.y - (1.45 + 0.12 * p.x - 0.07 * p.z)
		var cave: float = 1.3 - (p - Vector3(5.2, 1.1, -0.7)).length()
		return min(ground, -cave)
	var ridge: float = p.y - (1.05 + 0.28 * abs(sin(p.x * 0.8)) - 0.12 * cos(p.z * 1.7))
	var pocket: float = 0.95 - (p - Vector3(7.5, 1.1, 1.5)).length()
	return min(ridge, -pocket)

func _density(p: Vector3, field_id: int, edits: Array) -> float:
	var value: float = _density_base(p, field_id)
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

func _case_from_signs(samples: Array) -> int:
	var case_index: int = 0
	for i in range(samples.size()):
		if float(samples[i]) < 0.0:
			case_index = case_index | (1 << i)
	return case_index

func _case_for_cell(origin: Vector3, cell_x: int, cell_y: int, scale: float, field_id: int, edits: Array) -> int:
	var cell_origin: Vector3 = origin + Vector3(float(cell_x) * 2.0 * scale, float(cell_y) * 2.0 * scale, 0.0)
	var signs: Array = []
	for sy in range(3):
		for sx in range(3):
			var p: Vector3 = cell_origin + Vector3(float(sx), float(sy), 0.0) * scale
			signs.append(_density(p, field_id, edits))
	return _case_from_signs(signs)

func _case_sequence(origin: Vector3, scale: float, field_id: int, edits: Array) -> Array:
	var out: Array = []
	for y in range(GRID_Y):
		for x in range(GRID_X):
			out.append(_case_for_cell(origin, int(x), int(y), scale, field_id, edits))
	return out

func _arrays_equal(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in range(a.size()):
		if int(a[i]) != int(b[i]):
			return false
	return true

func _build_backend(label: String, table: Dictionary, case_sequence: Array, z_offset: float) -> Dictionary:
	var positions: Dictionary = _load_positions(table)
	var vertices: PackedVector3Array = PackedVector3Array()
	var indices: PackedInt32Array = PackedInt32Array()
	var unique_cases: Dictionary = {}
	var non_empty_cells: int = 0
	var empty_cells: int = 0
	var invalid_triangles: int = 0
	var degenerate_triangles: int = 0
	var appended_vertices: int = 0
	var appended_triangles: int = 0
	for y in range(GRID_Y):
		for x in range(GRID_X):
			var sequence_index: int = int(y) * GRID_X + int(x)
			var case_index: int = int(case_sequence[sequence_index])
			unique_cases[str(case_index)] = true
			if case_index == 0 or case_index == 511:
				empty_cells += 1
				continue
			var origin: Vector3 = Vector3(float(x) * 2.0, float(y) * 2.0, z_offset)
			var cell_report: Dictionary = _append_case_mesh(table, positions, case_index, origin, 1.0, vertices, indices)
			non_empty_cells += 1
			appended_vertices += int(cell_report.get("vertices", 0))
			appended_triangles += int(cell_report.get("triangles", 0))
			invalid_triangles += int(cell_report.get("invalid_triangles", 0))
			degenerate_triangles += int(cell_report.get("degenerate_triangles", 0))
	var mesh: Dictionary = _mesh_summary(label + "_scripted_edit_strip", vertices, indices, invalid_triangles, degenerate_triangles)
	var ok: bool = (
		String(mesh.get("status", "FAIL")) == "PASS"
		and non_empty_cells > 0
		and positions.size() > 0
	)
	return {
		"backend": label,
		"status": "PASS" if ok else "FAIL",
		"schema": table.get("schema", "missing"),
		"sample_count": positions.size(),
		"case_count": (table.get("cases", []) as Array).size(),
		"grid": [GRID_X, GRID_Y],
		"cells": GRID_X * GRID_Y,
		"non_empty_cells": non_empty_cells,
		"empty_or_full_cells": empty_cells,
		"appended_vertices": appended_vertices,
		"appended_triangles": appended_triangles,
		"unique_case_count": unique_cases.size(),
		"mesh": mesh
	}

func _compare_backend_summaries(default_report: Dictionary, m4_report: Dictionary) -> Dictionary:
	var default_mesh: Dictionary = default_report.get("mesh", {}) as Dictionary
	var m4_mesh: Dictionary = m4_report.get("mesh", {}) as Dictionary
	var vertex_delta: int = int(m4_mesh.get("array_vertex_count", 0)) - int(default_mesh.get("array_vertex_count", 0))
	var triangle_delta: int = int(m4_mesh.get("triangle_count", 0)) - int(default_mesh.get("triangle_count", 0))
	return {
		"default_vertices": int(default_mesh.get("array_vertex_count", 0)),
		"m4_vertices": int(m4_mesh.get("array_vertex_count", 0)),
		"vertex_delta_m4_minus_default": vertex_delta,
		"default_triangles": int(default_mesh.get("triangle_count", 0)),
		"m4_triangles": int(m4_mesh.get("triangle_count", 0)),
		"triangle_delta_m4_minus_default": triangle_delta,
		"m4_structurally_distinct_from_default": vertex_delta != 0 or triangle_delta != 0,
		"default_mesh_status": default_mesh.get("status", "FAIL"),
		"m4_mesh_status": m4_mesh.get("status", "FAIL")
	}

func _scripted_edits_for_field(field_id: int) -> Array:
	var out: Array = []
	var base_z: float = 0.10 + float(field_id % 3) * 0.28
	for i in range(6):
		var x: float = 1.0 + float((i * 2 + field_id) % 11)
		var y: float = 0.25 + float((i + field_id) % 5) * 0.82
		var z: float = base_z + float((i % 4) - 1) * 0.48
		var mode: String = "dig"
		if (i + field_id) % 2 == 1:
			mode = "add"
		out.append({"sequence": i + 1, "mode": mode, "position": [x, y, z], "radius": 0.72 + 0.18 * float(i % 3)})
	out.append({"sequence": 7, "mode": "dig", "position": [4.2 + float(field_id % 2), 1.2, 0.05], "radius": 1.35})
	out.append({"sequence": 8, "mode": "add", "position": [7.5 - float(field_id % 2), 2.0, -0.08], "radius": 1.20})
	return out

func _run_scenario(default_table: Dictionary, m4_table: Dictionary, field_id: int, origin: Vector3) -> Dictionary:
	var edits: Array = []
	var baseline_sequence: Array = _case_sequence(origin, 1.0, field_id, edits)
	var checks: Array = []
	var failed_checks: int = 0
	var changed_checks: int = 0
	var structurally_distinct_checks: int = 0
	var default_triangles_total: int = 0
	var m4_triangles_total: int = 0
	var scripted: Array = _scripted_edits_for_field(field_id)
	var check_inputs: Array = [{"sequence": 0, "mode": "baseline"}]
	for raw_edit in scripted:
		var edit: Dictionary = raw_edit as Dictionary
		edits.append(edit)
		check_inputs.append(edit)
	for raw_check in check_inputs:
		var check_input: Dictionary = raw_check as Dictionary
		var sequence: Array = _case_sequence(origin, 1.0, field_id, edits.slice(0, int(check_input.get("sequence", 0))))
		var changed: bool = not _arrays_equal(sequence, baseline_sequence)
		if changed:
			changed_checks += 1
		var default_report: Dictionary = _build_backend("default_independent", default_table, sequence, 0.0)
		var m4_report: Dictionary = _build_backend("m4_candidate", m4_table, sequence, 6.0)
		var comparison: Dictionary = _compare_backend_summaries(default_report, m4_report)
		if bool(comparison.get("m4_structurally_distinct_from_default", false)):
			structurally_distinct_checks += 1
		default_triangles_total += int(comparison.get("default_triangles", 0))
		m4_triangles_total += int(comparison.get("m4_triangles", 0))
		var check_status: String = "PASS"
		if (
			String(default_report.get("status", "FAIL")) != "PASS"
			or String(m4_report.get("status", "FAIL")) != "PASS"
			or not bool(comparison.get("m4_structurally_distinct_from_default", false))
		):
			check_status = "FAIL"
			failed_checks += 1
		checks.append({
			"sequence": int(check_input.get("sequence", 0)),
			"mode": check_input.get("mode", "baseline"),
			"case_sequence_changed_from_baseline": changed,
			"default_backend": default_report,
			"m4_backend": m4_report,
			"comparison": comparison,
			"status": check_status
		})
	var scenario_ok: bool = failed_checks == 0 and changed_checks > 0
	return {
		"status": "PASS" if scenario_ok else "FAIL",
		"field": _fields[field_id],
		"field_id": field_id,
		"origin": [origin.x, origin.y, origin.z],
		"edit_count": scripted.size(),
		"check_count": checks.size(),
		"failed_checks": failed_checks,
		"changed_after_edit_checks": changed_checks,
		"structurally_distinct_checks": structurally_distinct_checks,
		"default_triangles_total": default_triangles_total,
		"m4_triangles_total": m4_triangles_total,
		"checks": checks
	}

func _run_compare(default_table: Dictionary, m4_table: Dictionary) -> Dictionary:
	var fields: Array = [0, 1, 2, 3, 4, 5, 6]
	var origins: Array = [Vector3(0.0, -2.0, 0.0), Vector3(-1.0, -1.5, 0.0)]
	var scenarios: Array = []
	var failed_scenarios: int = 0
	var total_checks: int = 0
	var failed_checks: int = 0
	var total_edits: int = 0
	var changed_after_edit_checks: int = 0
	var scenarios_with_changes: int = 0
	var structurally_distinct_checks: int = 0
	var default_triangles_total: int = 0
	var m4_triangles_total: int = 0
	for raw_field in fields:
		for raw_origin in origins:
			var field_id: int = int(raw_field)
			var origin: Vector3 = raw_origin as Vector3
			var scenario: Dictionary = _run_scenario(default_table, m4_table, field_id, origin)
			scenarios.append(scenario)
			total_checks += int(scenario.get("check_count", 0))
			failed_checks += int(scenario.get("failed_checks", 0))
			total_edits += int(scenario.get("edit_count", 0))
			changed_after_edit_checks += int(scenario.get("changed_after_edit_checks", 0))
			structurally_distinct_checks += int(scenario.get("structurally_distinct_checks", 0))
			default_triangles_total += int(scenario.get("default_triangles_total", 0))
			m4_triangles_total += int(scenario.get("m4_triangles_total", 0))
			if int(scenario.get("changed_after_edit_checks", 0)) > 0:
				scenarios_with_changes += 1
			if String(scenario.get("status", "FAIL")) != "PASS":
				failed_scenarios += 1
	var ok: bool = (
		failed_scenarios == 0
		and failed_checks == 0
		and total_checks > 0
		and changed_after_edit_checks > 0
		and scenarios_with_changes == scenarios.size()
		and structurally_distinct_checks == total_checks
	)
	return {
		"status": "PASS" if ok else "FAIL",
		"field_count": fields.size(),
		"scenario_count": scenarios.size(),
		"failed_scenarios": failed_scenarios,
		"scripted_edits": total_edits,
		"check_count": total_checks,
		"failed_checks": failed_checks,
		"changed_after_edit_checks": changed_after_edit_checks,
		"scenarios_with_changes": scenarios_with_changes,
		"structurally_distinct_checks": structurally_distinct_checks,
		"default_triangles_total": default_triangles_total,
		"m4_triangles_total": m4_triangles_total,
		"triangle_delta_m4_minus_default_total": m4_triangles_total - default_triangles_total,
		"default_backend_by_default": true,
		"m4_requires_explicit_selection": true,
		"scenarios": scenarios
	}

func _init() -> void:
	var default_table: Dictionary = _read_json(DEFAULT_PATH)
	var m4_table: Dictionary = _read_json(M4_PATH)
	var comparison: Dictionary = _run_compare(default_table, m4_table)
	var ok: bool = String(comparison.get("status", "FAIL")) == "PASS"
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_scripted_edit_compare.v1",
		"status": "PASS" if ok else "FAIL",
		"meaning": "Godot-headless scripted edit comparison between the default independent transition table and optional M4 candidate table. Each check applies the same deterministic edit stack, builds both ArrayMesh outputs, and compares the explicit backend selections.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"selected_backends": ["default_independent", "m4_candidate"],
		"comparison": comparison,
		"outputs": {
			"default_table": DEFAULT_PATH,
			"m4_table": M4_PATH,
			"report": OUT_PATH,
			"mesh_path": "in_memory_array_mesh"
		}
	}
	_write_json(OUT_PATH, report)
	print("m4_scripted_edit_compare=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
