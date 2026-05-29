# SPDX-License-Identifier: 0BSD
extends SceneTree

const TRANSITION_PATH: String = "res://generated/transition_tables.json"
const OUT_PATH: String = "res://validation/03_seam_metrics/seam_metrics.json"
const GRID_SIZE: int = 8
const SEED_COUNT: int = 12

var _table: Dictionary = {}
var _positions: Dictionary = {}
var _boundary_triangles: Array = []
var _face_ranges: Dictionary = {
	"high": [0, 1, 2, 3, 4, 5, 6, 7],
	"low": [8, 9],
	"y_min": [10, 11, 12],
	"x_max": [13, 14, 15],
	"y_max": [16, 17, 18],
	"x_min": [19, 20, 21]
}
var _fields: Array = ["plane_x", "plane_y", "diagonal", "circle", "saddle", "hash_noise", "wavy"]
var _directions: Array = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]

func _read_json(path: String) -> Dictionary:
	var text: String = FileAccess.get_file_as_string(path)
	if text.is_empty():
		return {}
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

func _sort_array(values: Array) -> Array:
	var copy: Array = []
	for item in values:
		copy.append(item)
	copy.sort()
	return copy

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

func _sign_for_sample(case_index: int, sample_id: int) -> bool:
	if sample_id >= 0 and sample_id <= 8:
		return (case_index & (1 << sample_id)) != 0
	if sample_id == 9:
		return _sign_for_sample(case_index, 0)
	if sample_id == 10:
		return _sign_for_sample(case_index, 2)
	if sample_id == 11:
		return _sign_for_sample(case_index, 6)
	if sample_id == 12:
		return _sign_for_sample(case_index, 8)
	if sample_id == 13:
		return _sign_for_sample(case_index, 4)
	return false

func _contour_for_boundary_triangle(case_index: int, tri: Array) -> Array:
	var crossings: Array = []
	var a0: int = int(tri[0])
	var a1: int = int(tri[1])
	var a2: int = int(tri[2])
	var edges: Array = [[a0, a1], [a1, a2], [a2, a0]]
	for e in edges:
		var a: int = int(e[0])
		var b: int = int(e[1])
		if _sign_for_sample(case_index, a) != _sign_for_sample(case_index, b):
			crossings.append(_edge_key(a, b))
	if crossings.size() == 0:
		return []
	if crossings.size() != 2:
		return ["ERROR"]
	return [_segment_key(str(crossings[0]), str(crossings[1]))]

func _expected_segments_by_face(case_index: int) -> Dictionary:
	var out: Dictionary = {}
	for face_name in _face_ranges.keys():
		var segments: Array = []
		var indexes: Array = _face_ranges[face_name]
		for idx in indexes:
			var tri: Array = _boundary_triangles[int(idx)]
			var tri_segments: Array = _contour_for_boundary_triangle(case_index, tri)
			for seg in tri_segments:
				segments.append(seg)
		out[face_name] = segments
	return out

func _actual_boundary_segments(case: Dictionary) -> Array:
	var vertex_keys: Array = []
	var verts: Array = case.get("vertices", []) as Array
	for v in verts:
		var vd: Dictionary = v as Dictionary
		var samples: Array = vd.get("samples", []) as Array
		if samples.size() >= 2:
			vertex_keys.append(_edge_key(int(samples[0]), int(samples[1])))
	var counts: Dictionary = {}
	var tris: Array = case.get("triangles", []) as Array
	for tri_item in tris:
		var td: Dictionary = tri_item as Dictionary
		var ids: Array = td.get("vertices", []) as Array
		if ids.size() < 3:
			continue
		var ia: int = int(ids[0])
		var ib: int = int(ids[1])
		var ic: int = int(ids[2])
		var tri_edges: Array = [[ia, ib], [ib, ic], [ic, ia]]
		for e in tri_edges:
			var a: int = int(e[0])
			var b: int = int(e[1])
			if a == b:
				continue
			var key: String = _edge_key(a, b)
			counts[key] = int(counts.get(key, 0)) + 1
	var out: Array = []
	for key in counts.keys():
		if int(counts[key]) == 1:
			var parts: PackedStringArray = String(key).split(":")
			var a_idx: int = int(parts[0])
			var b_idx: int = int(parts[1])
			if a_idx >= 0 and a_idx < vertex_keys.size() and b_idx >= 0 and b_idx < vertex_keys.size():
				out.append(_segment_key(str(vertex_keys[a_idx]), str(vertex_keys[b_idx])))
	return out

func _validate_all_case_boundaries() -> Dictionary:
	var failures: Array = []
	var total_expected: int = 0
	var total_actual: int = 0
	var cases: Array = _table.get("cases", []) as Array
	for case_item in cases:
		var case: Dictionary = case_item as Dictionary
		var case_index: int = int(case.get("case", -1))
		var by_face: Dictionary = _expected_segments_by_face(case_index)
		var expected: Array = []
		for face_name in by_face.keys():
			var face_segments: Array = by_face[face_name]
			for seg in face_segments:
				expected.append(seg)
		var actual: Array = _actual_boundary_segments(case)
		total_expected += expected.size()
		total_actual += actual.size()
		var expected_sorted: Array = _sort_array(expected)
		var actual_sorted: Array = _sort_array(actual)
		if expected_sorted != actual_sorted:
			if failures.size() < 50:
				failures.append({"case": case_index, "expected": expected_sorted.size(), "actual": actual_sorted.size()})
	return {
		"status": "PASS" if failures.is_empty() else "FAIL",
		"case_count": cases.size(),
		"failure_count": failures.size(),
		"failures": failures,
		"total_expected_boundary_segments": total_expected,
		"total_actual_boundary_segments": total_actual
	}

func _load_positions() -> void:
	_positions.clear()
	var items: Array = _table.get("sample_positions", []) as Array
	for item in items:
		var d: Dictionary = item as Dictionary
		var pos: Array = d.get("position", []) as Array
		if pos.size() >= 3:
			_positions[int(d.get("id", -1))] = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))

func _edge_midpoint(edge: String) -> Vector3:
	var ids: Array = _parse_edge(edge)
	var a: int = int(ids[0])
	var b: int = int(ids[1])
	var pa: Vector3 = _positions.get(a, Vector3.ZERO)
	var pb: Vector3 = _positions.get(b, Vector3.ZERO)
	return (pa + pb) * 0.5

func _coord_text(v: float) -> String:
	var rounded: float = round(v * 1000000.0) / 1000000.0
	return str(rounded)

func _project_point(face: String, p: Vector3) -> String:
	if face == "y_min" or face == "y_max":
		return _coord_text(p.x) + "," + _coord_text(p.z)
	return _coord_text(p.y) + "," + _coord_text(p.z)

func _fingerprint(face: String, segments: Array) -> Array:
	var out: Array = []
	for seg in segments:
		var parts: PackedStringArray = String(seg).split("|")
		if parts.size() != 2:
			continue
		var p0: String = _project_point(face, _edge_midpoint(parts[0]))
		var p1: String = _project_point(face, _edge_midpoint(parts[1]))
		if p0 < p1:
			out.append(p0 + "|" + p1)
		else:
			out.append(p1 + "|" + p0)
	out.sort()
	return out

func _field_value(field_name: String, x: int, y: int, seed: int) -> float:
	if field_name == "plane_x":
		return float(x - (5 + seed % 3))
	if field_name == "plane_y":
		return float(y - (4 + seed % 4))
	if field_name == "diagonal":
		return float(x + y - (8 + seed % 5))
	if field_name == "circle":
		var cx: int = 6 + (seed % 3)
		var cy: int = 6 + (int(seed / 2) % 3)
		var r: int = 5 + (seed % 2)
		return float((x - cx) * (x - cx) + (y - cy) * (y - cy) - r * r)
	if field_name == "saddle":
		return float((x - 6) * (x - 6) - (y - 6) * (y - 6) + seed - 2)
	if field_name == "hash_noise":
		var n: int = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
		n = (n ^ (n >> 13)) * 1274126177
		n = n ^ (n >> 16)
		return -1.0 if (n & 1) != 0 else 1.0
	if field_name == "wavy":
		return sin(float(x + seed) * 0.7) + cos(float(y - seed) * 0.55)
	return 1.0

func _case_for_cell(field_name: String, cx: int, cy: int, seed: int) -> int:
	var case_index: int = 0
	var sample_id: int = 0
	for sy in range(3):
		for sx in range(3):
			var gx: int = cx * 2 + sx
			var gy: int = cy * 2 + sy
			if _field_value(field_name, gx, gy, seed) < 0.0:
				case_index = case_index | (1 << sample_id)
			sample_id += 1
	return case_index

func _face_fingerprint(case_index: int, face: String) -> Array:
	var by_face: Dictionary = _expected_segments_by_face(case_index)
	return _fingerprint(face, by_face.get(face, []) as Array)

func _validate_strips() -> Dictionary:
	var failures: Array = []
	var shared_faces_checked: int = 0
	var strips_checked: int = 0
	var per_direction: Dictionary = {}
	for direction in _directions:
		var direction_failures: int = 0
		var direction_shared: int = 0
		for field_name in _fields:
			for seed in range(SEED_COUNT):
				var grid: Array = []
				for y in range(GRID_SIZE):
					var row: Array = []
					for x in range(GRID_SIZE):
						row.append(_case_for_cell(str(field_name), x, y, seed))
					grid.append(row)
				strips_checked += 1
				for y in range(GRID_SIZE):
					for x in range(GRID_SIZE - 1):
						var left: int = int((grid[y] as Array)[x])
						var right: int = int((grid[y] as Array)[x + 1])
						var a: Array = _face_fingerprint(left, "x_max")
						var b: Array = _face_fingerprint(right, "x_min")
						shared_faces_checked += 1
						direction_shared += 1
						if a != b:
							direction_failures += 1
							if failures.size() < 100:
								failures.append({"direction": direction, "field": field_name, "seed": seed, "cell_a": [x, y], "cell_b": [x + 1, y], "face_a": "x_max", "face_b": "x_min"})
				for y in range(GRID_SIZE - 1):
					for x in range(GRID_SIZE):
						var lower: int = int((grid[y] as Array)[x])
						var upper: int = int((grid[y + 1] as Array)[x])
						var c: Array = _face_fingerprint(lower, "y_max")
						var d: Array = _face_fingerprint(upper, "y_min")
						shared_faces_checked += 1
						direction_shared += 1
						if c != d:
							direction_failures += 1
							if failures.size() < 100:
								failures.append({"direction": direction, "field": field_name, "seed": seed, "cell_a": [x, y], "cell_b": [x, y + 1], "face_a": "y_max", "face_b": "y_min"})
		per_direction[str(direction)] = {"shared_faces_checked": direction_shared, "failure_count": direction_failures}
	return {
		"status": "PASS" if failures.is_empty() else "FAIL",
		"grid_size": GRID_SIZE,
		"seed_count": SEED_COUNT,
		"tested_fields": _fields.size(),
		"tested_field_names": _fields,
		"tested_face_directions": _directions.size(),
		"tested_face_direction_names": _directions,
		"strips_checked": strips_checked,
		"shared_faces_checked": shared_faces_checked,
		"failure_count": failures.size(),
		"failures": failures,
		"per_direction": per_direction
	}

func _validate_triangles() -> Dictionary:
	var invalid: int = 0
	var degenerate: int = 0
	var total_triangles: int = 0
	var cases: Array = _table.get("cases", []) as Array
	for case_item in cases:
		var case: Dictionary = case_item as Dictionary
		var vertex_count: int = (case.get("vertices", []) as Array).size()
		var tris: Array = case.get("triangles", []) as Array
		for tri_item in tris:
			var tri: Dictionary = tri_item as Dictionary
			var ids: Array = tri.get("vertices", []) as Array
			total_triangles += 1
			if ids.size() != 3:
				invalid += 1
				continue
			var a: int = int(ids[0])
			var b: int = int(ids[1])
			var c: int = int(ids[2])
			if a < 0 or b < 0 or c < 0 or a >= vertex_count or b >= vertex_count or c >= vertex_count:
				invalid += 1
			if a == b or b == c or c == a:
				degenerate += 1
	return {"invalid_triangles": invalid, "degenerate_triangles": degenerate, "total_triangles": total_triangles}

func _init() -> void:
	_table = _read_json(TRANSITION_PATH)
	_boundary_triangles = _table.get("boundary_triangles", []) as Array
	_load_positions()
	var boundary: Dictionary = _validate_all_case_boundaries()
	var strips: Dictionary = _validate_strips()
	var tri_stats: Dictionary = _validate_triangles()
	var seam_open_edges: int = int(strips.get("failure_count", 0))
	var invalid_triangles: int = int(tri_stats.get("invalid_triangles", 0))
	var degenerate_triangles: int = int(tri_stats.get("degenerate_triangles", 0))
	var status: String = "PASS"
	if str(boundary.get("status", "FAIL")) != "PASS":
		status = "FAIL"
	if str(strips.get("status", "FAIL")) != "PASS":
		status = "FAIL"
	if invalid_triangles != 0 or degenerate_triangles != 0:
		status = "FAIL"
	var result: Dictionary = {}
	result["schema"] = "boqsc.transvoxel.godot_seam_metrics.v1"
	result["status"] = status
	result["meaning"] = "Godot-headless non-visual seam metrics. This validates transition-cell boundary and neighboring-strip seam contracts in Godot. It is stronger than screenshots, but it is still not gameplay performance certification."
	result["seam_open_edges"] = seam_open_edges
	result["invalid_triangles"] = invalid_triangles
	result["degenerate_triangles"] = degenerate_triangles
	result["tested_face_directions"] = int(strips.get("tested_face_directions", 0))
	result["tested_fields"] = int(strips.get("tested_fields", 0))
	result["boundary"] = boundary
	result["strips"] = strips
	result["triangles"] = tri_stats
	result["limitations"] = [
		"This script validates the generated table seam contract in Godot headless mode.",
		"It does not claim byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp tables.",
		"It does not measure frame time, streaming, collision, or full gameplay chunk editing."
	]
	_write_json(OUT_PATH, result)
	print("seam_metrics=", status)
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if status == "PASS" else 1)
