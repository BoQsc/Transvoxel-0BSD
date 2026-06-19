# SPDX-License-Identifier: 0BSD
extends SceneTree

const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/08_m4_candidate_viewer/m4_candidate_viewer.json"
const GRID_SIZE: int = 8
const FIELD_ID: int = 6
const FIELD_SEED: int = 3

var _table: Dictionary = {}
var _positions: Dictionary = {}
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

func _load_positions() -> void:
	_positions.clear()
	var samples: Array = _table.get("samples", []) as Array
	for raw_sample in samples:
		var sample: Dictionary = raw_sample as Dictionary
		var pos: Array = sample.get("position", [0.0, 0.0, 0.0]) as Array
		_positions[int(sample.get("id", -1))] = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))

func _sample_position(sample_id: int) -> Vector3:
	return _positions.get(sample_id, Vector3.ZERO) as Vector3

func _edge_midpoint(samples: Array, origin: Vector3, scale: float) -> Vector3:
	var a_id: int = int(samples[0])
	var b_id: int = int(samples[1])
	var a: Vector3 = origin + _sample_position(a_id) * scale
	var b: Vector3 = origin + _sample_position(b_id) * scale
	return (a + b) * 0.5

func _triangle_area2(vertices: PackedVector3Array, a_id: int, b_id: int, c_id: int) -> float:
	var a: Vector3 = vertices[a_id]
	var b: Vector3 = vertices[b_id]
	var c: Vector3 = vertices[c_id]
	return ((b - a).cross(c - a)).length_squared()

func _append_case_mesh(case_index: int, origin: Vector3, scale: float, vertices: PackedVector3Array, indices: PackedInt32Array) -> Dictionary:
	var cases: Array = _table.get("cases", []) as Array
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
			vertices.append(_edge_midpoint(samples, origin, scale))
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

func _count_open_edges(indices: PackedInt32Array) -> int:
	var counts: Dictionary = {}
	for i in range(0, indices.size(), 3):
		var edge_ids: Array = [
			[int(indices[i]), int(indices[i + 1])],
			[int(indices[i + 1]), int(indices[i + 2])],
			[int(indices[i + 2]), int(indices[i])]
		]
		for raw_edge in edge_ids:
			var edge: Array = raw_edge as Array
			var a: int = int(edge[0])
			var b: int = int(edge[1])
			var key: String = "%d:%d" % [min(a, b), max(a, b)]
			counts[key] = int(counts.get(key, 0)) + 1
	var open_edges: int = 0
	for raw_key in counts.keys():
		var key: String = String(raw_key)
		if int(counts[key]) == 1:
			open_edges += 1
	return open_edges

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
		"open_edges_total": _count_open_edges(indices),
		"mdt_create_error": mdt_error,
		"mdt_vertex_count": mdt_vertices,
		"mdt_edge_count": mdt_edges,
		"mdt_face_count": mdt_faces,
		"invalid_triangles": invalid_triangles,
		"degenerate_triangles": degenerate_triangles
	}

func _build_case_gallery() -> Dictionary:
	var selected_cases: Array = [1, 2, 3, 7, 15, 31, 63, 85, 127, 170, 255, 341, 383, 447, 510, 511]
	var vertices: PackedVector3Array = PackedVector3Array()
	var indices: PackedInt32Array = PackedInt32Array()
	var case_reports: Array = []
	var invalid_triangles: int = 0
	var degenerate_triangles: int = 0
	var non_empty_cases: int = 0
	var i: int = 0
	for raw_case in selected_cases:
		var case_index: int = int(raw_case)
		var origin: Vector3 = Vector3(float(i % 8) * 3.0, 0.0, float(int(i / 8)) * 3.0)
		var case_report: Dictionary = _append_case_mesh(case_index, origin, 1.0, vertices, indices)
		if int(case_report.get("triangles", 0)) > 0:
			non_empty_cases += 1
		invalid_triangles += int(case_report.get("invalid_triangles", 0))
		degenerate_triangles += int(case_report.get("degenerate_triangles", 0))
		case_reports.append(case_report)
		i += 1
	var mesh: Dictionary = _mesh_summary("m4_case_gallery", vertices, indices, invalid_triangles, degenerate_triangles)
	var ok: bool = String(mesh.get("status", "FAIL")) == "PASS" and non_empty_cases >= 12
	return {
		"status": "PASS" if ok else "FAIL",
		"selected_cases": selected_cases,
		"non_empty_cases": non_empty_cases,
		"case_reports": case_reports,
		"mesh": mesh
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

func _build_terrain_strip() -> Dictionary:
	var vertices: PackedVector3Array = PackedVector3Array()
	var indices: PackedInt32Array = PackedInt32Array()
	var cell_reports: Array = []
	var unique_cases: Dictionary = {}
	var non_empty_cells: int = 0
	var empty_cells: int = 0
	var invalid_triangles: int = 0
	var degenerate_triangles: int = 0
	for y in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var case_index: int = _case_for_cell(FIELD_ID, int(x), int(y), FIELD_SEED)
			unique_cases[str(case_index)] = true
			if case_index == 0 or case_index == 511:
				empty_cells += 1
				continue
			var origin: Vector3 = Vector3(float(x) * 2.0, float(y) * 2.0, 6.0)
			var cell_report: Dictionary = _append_case_mesh(case_index, origin, 1.0, vertices, indices)
			non_empty_cells += 1
			invalid_triangles += int(cell_report.get("invalid_triangles", 0))
			degenerate_triangles += int(cell_report.get("degenerate_triangles", 0))
			if cell_reports.size() < 64:
				cell_reports.append(cell_report)
	var mesh: Dictionary = _mesh_summary("m4_terrain_strip", vertices, indices, invalid_triangles, degenerate_triangles)
	var unique_case_list: Array = unique_cases.keys()
	unique_case_list.sort()
	var ok: bool = String(mesh.get("status", "FAIL")) == "PASS" and non_empty_cells > 0
	return {
		"status": "PASS" if ok else "FAIL",
		"field": _fields[FIELD_ID],
		"seed": FIELD_SEED,
		"grid": GRID_SIZE,
		"cells": GRID_SIZE * GRID_SIZE,
		"non_empty_cells": non_empty_cells,
		"empty_or_full_cells": empty_cells,
		"unique_cases": unique_case_list,
		"cell_report_sample": cell_reports,
		"mesh": mesh
	}

func _validate_table_contract() -> Dictionary:
	var cases: Array = _table.get("cases", []) as Array
	var stats: Dictionary = _table.get("statistics", {}) as Dictionary
	var issues: Array = []
	if String(_table.get("schema", "")) != "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1":
		issues.append("unexpected schema")
	if cases.size() != 512:
		issues.append("case count is not 512")
	if _positions.size() != 13:
		issues.append("sample count is not 13")
	if int(stats.get("research_class_count", 0)) != 73:
		issues.append("research class count is not 73")
	return {
		"status": "PASS" if issues.is_empty() else "FAIL",
		"issues": issues,
		"case_count": cases.size(),
		"sample_count": _positions.size(),
		"research_class_count": int(stats.get("research_class_count", 0)),
		"total_vertex_pairs": int(stats.get("total_vertex_pairs", 0)),
		"total_triangles": int(stats.get("total_triangles", 0))
	}

func _init() -> void:
	_table = _read_json(M4_PATH)
	_load_positions()
	var table_contract: Dictionary = _validate_table_contract()
	var gallery: Dictionary = _build_case_gallery()
	var strip: Dictionary = _build_terrain_strip()
	var ok: bool = (
		String(table_contract.get("status", "FAIL")) == "PASS"
		and String(gallery.get("status", "FAIL")) == "PASS"
		and String(strip.get("status", "FAIL")) == "PASS"
	)
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_candidate_viewer.v1",
		"status": "PASS" if ok else "FAIL",
		"meaning": "Godot-headless M4 candidate viewer/export path. This builds real ArrayMesh objects from the synced M4 candidate table and validates MeshDataTool readback. It does not claim official Transvoxel.cpp equivalence.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"table": table_contract,
		"case_gallery": gallery,
		"terrain_strip": strip,
		"outputs": {
			"m4_table": M4_PATH,
			"report": OUT_PATH,
			"mesh_path": "in_memory_array_mesh"
		}
	}
	_write_json(OUT_PATH, report)
	print("m4_candidate_viewer=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
