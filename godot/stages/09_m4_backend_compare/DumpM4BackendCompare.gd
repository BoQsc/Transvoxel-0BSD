# SPDX-License-Identifier: 0BSD
extends SceneTree

const DEFAULT_PATH: String = "res://generated/transition_tables.json"
const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/09_m4_backend_compare/m4_backend_compare.json"
const GRID_SIZE: int = 8
const FIELD_ID: int = 6
const FIELD_SEED: int = 3

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

func _field_inside(field_id: int, x: int, y: int, seed: int) -> bool:
	if field_id == 0:
		return x < 5 + (seed % 3)
	if field_id == 1:
		return y < 4 + (seed % 4)
	if field_id == 2:
		return x + y < 8 + (seed % 5)
	if field_id == 3:
		var cx: int = 6 + (seed % 3)
		var cy: int = 6 + (int(seed / 2) % 3)
		var r: int = 5 + (seed % 2)
		return (x - cx) * (x - cx) + (y - cy) * (y - cy) < r * r
	if field_id == 4:
		return (x - 6) * (x - 6) - (y - 6) * (y - 6) + seed - 2 < 0
	if field_id == 5:
		var n: int = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
		n = (n ^ (n >> 13)) * 1274126177
		n = n ^ (n >> 16)
		return (n & 1) != 0
	return ((x + seed) % 7) + ((y * 3 + seed) % 11) < 8

func _case_for_cell(field_id: int, cx: int, cy: int, seed: int) -> int:
	var case_index: int = 0
	var sample_id: int = 0
	for sy in range(3):
		for sx in range(3):
			var gx: int = cx * 2 + sx
			var gy: int = cy * 2 + sy
			if _field_inside(field_id, gx, gy, seed):
				case_index = case_index | (1 << sample_id)
			sample_id += 1
	return case_index

func _sort_keys_as_int_strings(keys: Array) -> Array:
	var out: Array = []
	for raw_key in keys:
		out.append(int(String(raw_key)))
	out.sort()
	var text_out: Array = []
	for item in out:
		text_out.append(str(int(item)))
	return text_out

func _build_backend(label: String, table: Dictionary, z_offset: float) -> Dictionary:
	var positions: Dictionary = _load_positions(table)
	var vertices: PackedVector3Array = PackedVector3Array()
	var indices: PackedInt32Array = PackedInt32Array()
	var cell_reports: Array = []
	var case_sequence: Array = []
	var unique_cases: Dictionary = {}
	var non_empty_cells: int = 0
	var empty_cells: int = 0
	var invalid_triangles: int = 0
	var degenerate_triangles: int = 0
	var appended_vertices: int = 0
	var appended_triangles: int = 0
	for y in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var case_index: int = _case_for_cell(FIELD_ID, int(x), int(y), FIELD_SEED)
			case_sequence.append(case_index)
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
			if cell_reports.size() < 64:
				cell_reports.append(cell_report)
	var mesh: Dictionary = _mesh_summary(label + "_terrain_strip", vertices, indices, invalid_triangles, degenerate_triangles)
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
		"field": _fields[FIELD_ID],
		"seed": FIELD_SEED,
		"grid": GRID_SIZE,
		"cells": GRID_SIZE * GRID_SIZE,
		"non_empty_cells": non_empty_cells,
		"empty_or_full_cells": empty_cells,
		"case_sequence": case_sequence,
		"unique_cases": _sort_keys_as_int_strings(unique_cases.keys()),
		"cell_report_sample": cell_reports,
		"appended_vertices": appended_vertices,
		"appended_triangles": appended_triangles,
		"mesh": mesh
	}

func _arrays_equal(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in range(a.size()):
		if int(a[i]) != int(b[i]):
			return false
	return true

func _compare_backends(default_report: Dictionary, m4_report: Dictionary) -> Dictionary:
	var default_mesh: Dictionary = default_report.get("mesh", {}) as Dictionary
	var m4_mesh: Dictionary = m4_report.get("mesh", {}) as Dictionary
	var same_cases: bool = _arrays_equal(default_report.get("case_sequence", []) as Array, m4_report.get("case_sequence", []) as Array)
	var same_non_empty: bool = int(default_report.get("non_empty_cells", -1)) == int(m4_report.get("non_empty_cells", -2))
	var vertex_delta: int = int(m4_mesh.get("array_vertex_count", 0)) - int(default_mesh.get("array_vertex_count", 0))
	var triangle_delta: int = int(m4_mesh.get("triangle_count", 0)) - int(default_mesh.get("triangle_count", 0))
	var structurally_distinct: bool = vertex_delta != 0 or triangle_delta != 0
	return {
		"same_case_sequence": same_cases,
		"same_non_empty_cell_count": same_non_empty,
		"default_vertices": int(default_mesh.get("array_vertex_count", 0)),
		"m4_vertices": int(m4_mesh.get("array_vertex_count", 0)),
		"vertex_delta_m4_minus_default": vertex_delta,
		"default_triangles": int(default_mesh.get("triangle_count", 0)),
		"m4_triangles": int(m4_mesh.get("triangle_count", 0)),
		"triangle_delta_m4_minus_default": triangle_delta,
		"m4_structurally_distinct_from_default": structurally_distinct,
		"default_backend_by_default": true,
		"m4_requires_explicit_selection": true
	}

func _init() -> void:
	var default_table: Dictionary = _read_json(DEFAULT_PATH)
	var m4_table: Dictionary = _read_json(M4_PATH)
	var default_report: Dictionary = _build_backend("default_independent", default_table, 0.0)
	var m4_report: Dictionary = _build_backend("m4_candidate", m4_table, 6.0)
	var comparison: Dictionary = _compare_backends(default_report, m4_report)
	var ok: bool = (
		String(default_report.get("status", "FAIL")) == "PASS"
		and String(m4_report.get("status", "FAIL")) == "PASS"
		and bool(comparison.get("same_case_sequence", false))
		and bool(comparison.get("same_non_empty_cell_count", false))
		and bool(comparison.get("m4_structurally_distinct_from_default", false))
	)
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_backend_compare.v1",
		"status": "PASS" if ok else "FAIL",
		"meaning": "Godot-headless selectable-backend comparison between the default independent transition table and the optional M4 candidate table. This builds the same deterministic transition-strip-style mesh through both table paths and compares valid ArrayMesh/MeshDataTool outputs.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"selected_backends": ["default_independent", "m4_candidate"],
		"default_backend": default_report,
		"m4_backend": m4_report,
		"comparison": comparison,
		"outputs": {
			"default_table": DEFAULT_PATH,
			"m4_table": M4_PATH,
			"report": OUT_PATH,
			"mesh_path": "in_memory_array_mesh"
		}
	}
	_write_json(OUT_PATH, report)
	print("m4_backend_compare=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
