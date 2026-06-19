# SPDX-License-Identifier: 0BSD
extends SceneTree

const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/05_m4_candidate_metrics/m4_candidate_metrics.json"
const GRID_SIZE: int = 8
const SEED_COUNT: int = 12

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

func _edge_key(a: int, b: int) -> String:
	if a < b:
		return str(a) + ":" + str(b)
	return str(b) + ":" + str(a)

func _segment_key(a: String, b: String) -> String:
	if a < b:
		return a + "|" + b
	return b + "|" + a

func _parse_edge(edge: String) -> Array:
	var parts: PackedStringArray = edge.split(":")
	return [int(parts[0]), int(parts[1])]

func _sort_copy(values: Array) -> Array:
	var out: Array = []
	for item in values:
		out.append(item)
	out.sort()
	return out

func _load_positions() -> void:
	_positions.clear()
	var samples: Array = _table.get("samples", []) as Array
	for raw_sample in samples:
		var sample: Dictionary = raw_sample as Dictionary
		var pos: Array = sample.get("position", [0.0, 0.0, 0.0]) as Array
		_positions[int(sample.get("id", -1))] = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))

func _case_vertex_edges(case_record: Dictionary) -> Array:
	var out: Array = []
	var vertices: Array = case_record.get("vertices", []) as Array
	for raw_vertex in vertices:
		var vertex: Dictionary = raw_vertex as Dictionary
		var samples: Array = vertex.get("samples", []) as Array
		if samples.size() >= 2:
			out.append(_edge_key(int(samples[0]), int(samples[1])))
	return out

func _edge_midpoint(edge: String) -> Vector3:
	var ids: Array = _parse_edge(edge)
	var a: Vector3 = _positions.get(int(ids[0]), Vector3.ZERO) as Vector3
	var b: Vector3 = _positions.get(int(ids[1]), Vector3.ZERO) as Vector3
	return (a + b) * 0.5

func _boundary_segments(case_record: Dictionary) -> Array:
	var vertex_edges: Array = _case_vertex_edges(case_record)
	var counts: Dictionary = {}
	var triangles: Array = case_record.get("triangles", []) as Array
	for raw_triangle in triangles:
		var triangle: Dictionary = raw_triangle as Dictionary
		var ids: Array = triangle.get("vertices", []) as Array
		if ids.size() < 3:
			continue
		var tri_edges: Array = [[int(ids[0]), int(ids[1])], [int(ids[1]), int(ids[2])], [int(ids[2]), int(ids[0])]]
		for raw_edge in tri_edges:
			var edge: Array = raw_edge as Array
			var key: String = _edge_key(int(edge[0]), int(edge[1]))
			counts[key] = int(counts.get(key, 0)) + 1
	var out: Array = []
	for key in counts.keys():
		if int(counts[key]) == 1:
			var ids: Array = _parse_edge(String(key))
			var a: int = int(ids[0])
			var b: int = int(ids[1])
			if a >= 0 and a < vertex_edges.size() and b >= 0 and b < vertex_edges.size():
				out.append(_segment_key(String(vertex_edges[a]), String(vertex_edges[b])))
	return _sort_copy(out)

func _coord_equal(a: float, b: float) -> bool:
	return abs(a - b) <= 0.000001

func _point_on_face(point: Vector3, face: String) -> bool:
	if face == "x_min":
		return _coord_equal(point.x, 0.0)
	if face == "x_max":
		return _coord_equal(point.x, 2.0)
	if face == "y_min":
		return _coord_equal(point.y, 0.0)
	if face == "y_max":
		return _coord_equal(point.y, 2.0)
	return false

func _quantize(value: float) -> int:
	return int(round(value * 2.0))

func _project_point(point: Vector3, face: String) -> String:
	if face.begins_with("x_"):
		return str(_quantize(point.y)) + "," + str(_quantize(point.z))
	return str(_quantize(point.x)) + "," + str(_quantize(point.z))

func _face_fingerprint(case_record: Dictionary, face: String) -> Array:
	var out: Array = []
	var segments: Array = _boundary_segments(case_record)
	for raw_segment in segments:
		var parts: PackedStringArray = String(raw_segment).split("|")
		if parts.size() != 2:
			continue
		var a: Vector3 = _edge_midpoint(String(parts[0]))
		var b: Vector3 = _edge_midpoint(String(parts[1]))
		if _point_on_face(a, face) and _point_on_face(b, face):
			var pa: String = _project_point(a, face)
			var pb: String = _project_point(b, face)
			if pa < pb:
				out.append(pa + "|" + pb)
			else:
				out.append(pb + "|" + pa)
	return _sort_copy(out)

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

func _validate_strips() -> Dictionary:
	var cases: Array = _table.get("cases", []) as Array
	var failures: Array = []
	var builds: int = 0
	var shared_faces: int = 0
	var total_vertices: int = 0
	var total_triangles: int = 0
	for field_id in range(_fields.size()):
		for seed in range(SEED_COUNT):
			var grid: Array = []
			for y in range(GRID_SIZE):
				var row: Array = []
				for x in range(GRID_SIZE):
					var case_index: int = _case_for_cell(int(field_id), int(x), int(y), int(seed))
					row.append(case_index)
					var case_record: Dictionary = cases[case_index] as Dictionary
					total_vertices += int(case_record.get("vertex_count", 0))
					total_triangles += int(case_record.get("triangle_count", 0))
					builds += 1
				grid.append(row)
			for y in range(GRID_SIZE):
				for x in range(GRID_SIZE - 1):
					var left: Dictionary = cases[int((grid[y] as Array)[x])] as Dictionary
					var right: Dictionary = cases[int((grid[y] as Array)[x + 1])] as Dictionary
					shared_faces += 1
					if _face_fingerprint(left, "x_max") != _face_fingerprint(right, "x_min"):
						if failures.size() < 100:
							failures.append({"field": _fields[field_id], "seed": seed, "cell_a": [x, y], "cell_b": [x + 1, y], "face_a": "x_max", "face_b": "x_min"})
			for y in range(GRID_SIZE - 1):
				for x in range(GRID_SIZE):
					var lower: Dictionary = cases[int((grid[y] as Array)[x])] as Dictionary
					var upper: Dictionary = cases[int((grid[y + 1] as Array)[x])] as Dictionary
					shared_faces += 1
					if _face_fingerprint(lower, "y_max") != _face_fingerprint(upper, "y_min"):
						if failures.size() < 100:
							failures.append({"field": _fields[field_id], "seed": seed, "cell_a": [x, y], "cell_b": [x, y + 1], "face_a": "y_max", "face_b": "y_min"})
	return {
		"status": "PASS" if failures.is_empty() else "FAIL",
		"fields": _fields.size(),
		"field_names": _fields,
		"seeds": SEED_COUNT,
		"grid": GRID_SIZE,
		"builds": builds,
		"shared_faces": shared_faces,
		"failures": failures.size(),
		"failure_examples": failures,
		"total_vertices": total_vertices,
		"total_triangles": total_triangles
	}

func _validate_triangles() -> Dictionary:
	var cases: Array = _table.get("cases", []) as Array
	var invalid: int = 0
	var degenerate: int = 0
	var total: int = 0
	for raw_case in cases:
		var case_record: Dictionary = raw_case as Dictionary
		var vertex_edges: Array = _case_vertex_edges(case_record)
		var triangles: Array = case_record.get("triangles", []) as Array
		for raw_triangle in triangles:
			var triangle: Dictionary = raw_triangle as Dictionary
			var ids: Array = triangle.get("vertices", []) as Array
			total += 1
			if ids.size() != 3:
				invalid += 1
				continue
			var a_id: int = int(ids[0])
			var b_id: int = int(ids[1])
			var c_id: int = int(ids[2])
			if a_id < 0 or b_id < 0 or c_id < 0 or a_id >= vertex_edges.size() or b_id >= vertex_edges.size() or c_id >= vertex_edges.size():
				invalid += 1
				continue
			if a_id == b_id or b_id == c_id or c_id == a_id:
				degenerate += 1
				continue
			var a: Vector3 = _edge_midpoint(String(vertex_edges[a_id]))
			var b: Vector3 = _edge_midpoint(String(vertex_edges[b_id]))
			var c: Vector3 = _edge_midpoint(String(vertex_edges[c_id]))
			var area2: float = ((b - a).cross(c - a)).length_squared()
			if area2 <= 0.0000001:
				degenerate += 1
	return {
		"status": "PASS" if invalid == 0 and degenerate == 0 else "FAIL",
		"invalid_triangles": invalid,
		"degenerate_triangles": degenerate,
		"total_triangles": total
	}

func _validate_m4_candidate() -> Dictionary:
	_load_positions()
	var cases: Array = _table.get("cases", []) as Array
	var stats: Dictionary = _table.get("statistics", {}) as Dictionary
	var issues: Array = []
	if String(_table.get("schema", "")) != "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1":
		issues.append("unexpected schema")
	if cases.size() != 512:
		issues.append("case count is not 512")
	if int(stats.get("research_class_count", 0)) != 73:
		issues.append("research class count is not 73")
	if _positions.size() != 13:
		issues.append("sample count is not 13")
	if int(stats.get("total_triangles", 0)) != 2640:
		issues.append("total triangle count is not 2640")
	if int(stats.get("total_vertex_pairs", 0)) != 4096:
		issues.append("total vertex-pair count is not 4096")
	var triangles: Dictionary = _validate_triangles()
	var strips: Dictionary = _validate_strips()
	if String(triangles.get("status", "FAIL")) != "PASS":
		issues.append("triangle validation failed")
	if String(strips.get("status", "FAIL")) != "PASS":
		issues.append("strip seam validation failed")
	return {
		"status": "PASS" if issues.is_empty() else "FAIL",
		"issues": issues,
		"case_count": cases.size(),
		"sample_count": _positions.size(),
		"statistics": stats,
		"triangles": triangles,
		"strips": strips,
		"seam_open_edges": int(strips.get("failures", -1)),
		"invalid_triangles": int(triangles.get("invalid_triangles", -1)),
		"degenerate_triangles": int(triangles.get("degenerate_triangles", -1))
	}

func _init() -> void:
	_table = _read_json(M4_PATH)
	var validation: Dictionary = _validate_m4_candidate()
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_candidate_metrics.v1",
		"status": validation.get("status", "FAIL"),
		"meaning": "Godot-headless non-visual M4 candidate metrics. This validates the synced M4 candidate table in the Godot data path and does not claim official Transvoxel.cpp equivalence.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"validation": validation
	}
	_write_json(OUT_PATH, report)
	print("m4_candidate_metrics=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
