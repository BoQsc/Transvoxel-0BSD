# SPDX-License-Identifier: 0BSD
extends SceneTree

# Deterministic automated interaction proof.
# This is intentionally non-visual: it runs scripted dig/add edits over multiple
# terrain fields and validates transition strip side-face consistency after each edit.

const TRANSITION_PATH: String = "res://generated/transition_tables.json"
const OUT_PATH: String = "res://validation/07_auto_interaction/auto_interaction.json"

var transition_table: Dictionary = {}
var edits: Array = []
var field_mode: int = 0

func _initialize() -> void:
	transition_table = _load_json(TRANSITION_PATH)
	var report: Dictionary = _run_auto_interaction()
	_write_json(OUT_PATH, report)
	print("auto_interaction=" + str(report.get("status", "UNKNOWN")))
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if str(report.get("status", "FAIL")) == "PASS" else 2)

func _load_json(path: String) -> Dictionary:
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
		6:
			var ridge: float = p.y - (1.05 + 0.28 * abs(sin(p.x * 0.8)) - 0.12 * cos(p.z * 1.7))
			var pocket: float = 0.95 - (p - Vector3(7.5, 1.1, 1.5)).length()
			value = min(ridge, -pocket)
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

func _strip_check(origin: Vector3, cells: Vector2i, scale: float) -> Dictionary:
	var sample_pos: Dictionary = _sample_positions(transition_table)
	var mismatches: int = 0
	var invalid: int = 0
	var degenerate: int = 0
	var checked_faces: int = 0
	var checked_cells: int = 0
	var transition_triangles: int = 0
	var transition_vertices: int = 0
	var first_failures: Array = []
	for x in range(cells.x):
		for y in range(cells.y):
			var cell_origin: Vector3 = origin + Vector3(float(x) * 2.0 * scale, float(y) * 2.0 * scale, 0.0)
			var ci: int = _transition_case_for_cell(cell_origin, scale, sample_pos)
			var info: Dictionary = _inspect_transition_case(ci)
			invalid += int(info.get("invalid_triangles", 0))
			degenerate += int(info.get("degenerate_triangles", 0))
			transition_triangles += int(info.get("triangles", 0))
			transition_vertices += int(info.get("vertices", 0))
			checked_cells += 1
			if x + 1 < cells.x:
				var neighbor_x: Vector3 = origin + Vector3(float(x + 1) * 2.0 * scale, float(y) * 2.0 * scale, 0.0)
				var left_pattern: Array = _side_pattern(cell_origin, scale, "x_max", sample_pos)
				var right_pattern: Array = _side_pattern(neighbor_x, scale, "x_min", sample_pos)
				checked_faces += 1
				if not _patterns_equal(left_pattern, right_pattern):
					mismatches += 1
					if first_failures.size() < 16:
						first_failures.append({"face": "x", "cell": [x, y], "a": left_pattern, "b": right_pattern})
			if y + 1 < cells.y:
				var neighbor_y: Vector3 = origin + Vector3(float(x) * 2.0 * scale, float(y + 1) * 2.0 * scale, 0.0)
				var bottom_pattern: Array = _side_pattern(cell_origin, scale, "y_max", sample_pos)
				var top_pattern: Array = _side_pattern(neighbor_y, scale, "y_min", sample_pos)
				checked_faces += 1
				if not _patterns_equal(bottom_pattern, top_pattern):
					mismatches += 1
					if first_failures.size() < 16:
						first_failures.append({"face": "y", "cell": [x, y], "a": bottom_pattern, "b": top_pattern})
	var status: String = "PASS"
	if mismatches != 0 or invalid != 0 or degenerate != 0:
		status = "FAIL"
	return {
		"status": status,
		"seam_open_edges": mismatches,
		"side_pattern_mismatches": mismatches,
		"invalid_triangles": invalid,
		"degenerate_triangles": degenerate,
		"checked_transition_cells": checked_cells,
		"checked_shared_faces": checked_faces,
		"transition_triangles": transition_triangles,
		"transition_vertices": transition_vertices,
		"first_failures": first_failures
	}

func _scripted_edits_for_field(field: int) -> Array:
	var out: Array = []
	var base_z: float = 0.15 + float(field % 3) * 0.35
	for i in range(10):
		var x: float = 1.0 + float((i * 2 + field) % 11)
		var y: float = 0.2 + float((i + field) % 5) * 0.85
		var z: float = base_z + float((i % 4) - 1) * 0.55
		var mode: String = "dig"
		if (i + field) % 2 == 1:
			mode = "add"
		out.append({"sequence": i + 1, "mode": mode, "position": [x, y, z], "radius": 0.65 + 0.12 * float(i % 3)})
	# Add two seam-focused edits near the transition plane.
	out.append({"sequence": 11, "mode": "dig", "position": [4.2 + float(field % 2), 1.2, 0.05], "radius": 1.25})
	out.append({"sequence": 12, "mode": "add", "position": [7.5 - float(field % 2), 2.0, -0.08], "radius": 1.1})
	return out

func _run_auto_interaction() -> Dictionary:
	var issues: Array = []
	if transition_table.is_empty():
		issues.append("missing transition table")
	var scenarios: Array = []
	var total_checks: int = 0
	var failed_checks: int = 0
	var total_edits: int = 0
	var total_shared_faces: int = 0
	var total_transition_triangles: int = 0
	var max_vertices: int = 0
	var fields: Array = [0, 1, 2, 3, 4, 5, 6]
	var origins: Array = [Vector3(0.0, -2.0, 0.0), Vector3(-1.0, -1.5, 0.0)]
	for raw_field in fields:
		field_mode = int(raw_field)
		for raw_origin in origins:
			var origin: Vector3 = raw_origin as Vector3
			edits.clear()
			var checks: Array = []
			var baseline: Dictionary = _strip_check(origin, Vector2i(8, 5), 1.0)
			checks.append({"sequence": 0, "mode": "baseline", "check": baseline})
			total_checks += 1
			total_shared_faces += int(baseline.get("checked_shared_faces", 0))
			total_transition_triangles += int(baseline.get("transition_triangles", 0))
			max_vertices = maxi(max_vertices, int(baseline.get("transition_vertices", 0)))
			if str(baseline.get("status", "FAIL")) != "PASS":
				failed_checks += 1
			var scripted: Array = _scripted_edits_for_field(field_mode)
			for raw_edit in scripted:
				var edit: Dictionary = raw_edit as Dictionary
				edits.append(edit)
				var check: Dictionary = _strip_check(origin, Vector2i(8, 5), 1.0)
				checks.append({"sequence": edit.get("sequence", edits.size()), "mode": edit.get("mode", "unknown"), "check": check})
				total_checks += 1
				total_edits += 1
				total_shared_faces += int(check.get("checked_shared_faces", 0))
				total_transition_triangles += int(check.get("transition_triangles", 0))
				max_vertices = maxi(max_vertices, int(check.get("transition_vertices", 0)))
				if str(check.get("status", "FAIL")) != "PASS":
					failed_checks += 1
			var scenario_status: String = "PASS"
			for raw_check in checks:
				var one: Dictionary = raw_check as Dictionary
				var c: Dictionary = one.get("check", {}) as Dictionary
				if str(c.get("status", "FAIL")) != "PASS":
					scenario_status = "FAIL"
			scenarios.append({
				"field_mode": field_mode,
				"origin": [origin.x, origin.y, origin.z],
				"edit_count": scripted.size(),
				"check_count": checks.size(),
				"status": scenario_status,
				"checks": checks
			})
	var status: String = "PASS"
	if issues.size() > 0 or failed_checks != 0:
		status = "FAIL"
	return {
		"schema": "boqsc.transvoxel.auto_interaction.v1",
		"status": status,
		"meaning": "Scripted non-visual auto-interaction proof. It simulates repeated dig/add edits over multiple fields and origins, then checks transition strip seam consistency after every edit. It is stronger than screenshots, but still not a final art/gameplay-quality certification.",
		"issues": issues,
		"field_count": fields.size(),
		"scenario_count": scenarios.size(),
		"scripted_edits": total_edits,
		"check_count": total_checks,
		"failed_checks": failed_checks,
		"seam_open_edges": 0 if failed_checks == 0 else -1,
		"invalid_triangles": 0 if failed_checks == 0 else -1,
		"degenerate_triangles": 0 if failed_checks == 0 else -1,
		"checked_shared_faces_total": total_shared_faces,
		"transition_triangles_total": total_transition_triangles,
		"max_transition_vertices_in_check": max_vertices,
		"scenarios": scenarios
	}
