# SPDX-License-Identifier: 0BSD
extends SceneTree

const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/12_m4_corner_junctions/m4_corner_junctions.json"
const FIELD_COUNT: int = 7
const SEED_COUNT: int = 8
const SIDE_U_MIN: int = 0
const SIDE_V_MIN: int = 1

var _u_min_samples: Array = [0, 3, 6, 9, 11]
var _v_min_samples: Array = [0, 1, 2, 9, 10]

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed as Dictionary
	return {}

func _write_json(path: String, data: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("cannot write " + path)
		return
	file.store_string(JSON.stringify(data, "\t"))
	file.close()

func _near(a: float, b: float) -> bool:
	return abs(a - b) <= 0.00002

func _vector_near(a: Vector3, b: Vector3) -> bool:
	return _near(a.x, b.x) and _near(a.y, b.y) and _near(a.z, b.z)

func _load_local_positions(table: Dictionary) -> Dictionary:
	var positions: Dictionary = {}
	for raw_sample in table.get("samples", []) as Array:
		var sample: Dictionary = raw_sample as Dictionary
		var raw_position: Array = sample.get("position", [0.0, 0.0, 0.0]) as Array
		positions[int(sample.get("id", -1))] = Vector3(
			float(raw_position[0]),
			float(raw_position[1]),
			float(raw_position[2])
		)
	return positions

func _frame_position(frame: Dictionary, local: Vector3) -> Vector3:
	return (
		(frame.get("origin", Vector3.ZERO) as Vector3)
		+ (frame.get("axis_u", Vector3.ZERO) as Vector3) * local.x
		+ (frame.get("axis_v", Vector3.ZERO) as Vector3) * local.y
		+ (frame.get("axis_w", Vector3.ZERO) as Vector3) * local.z
	)

func _mapped_sample_positions(local_positions: Dictionary, frame: Dictionary) -> Array:
	var out: Array = []
	for sample_id in range(13):
		var local: Vector3 = local_positions.get(int(sample_id), Vector3.ZERO) as Vector3
		if int(sample_id) >= 9:
			if _near(local.x, 0.0):
				local.x += 0.5
			if _near(local.y, 0.0):
				local.y += 0.5
		out.append(_frame_position(frame, local))
	return out

func _density(p: Vector3, field_id: int, seed: int) -> float:
	var x: float = p.x
	var y: float = p.y
	var z: float = p.z
	var epsilon: float = 0.037 * float(seed + 1) + 0.013
	if field_id == 0:
		return x + y + z - (0.75 + 0.25 * float(seed % 5)) + epsilon
	if field_id == 1:
		var delta: Vector3 = p - Vector3(0.7, 0.9, 1.1)
		var radius: float = 0.8 + 0.1 * float(seed % 4)
		return delta.length_squared() - radius * radius + epsilon
	if field_id == 2:
		return x * y + y * z + z * x - 0.2 * float(seed - 3) + epsilon
	if field_id == 3:
		return x * x + 0.5 * y - 0.75 * z - (0.6 + 0.15 * float(seed)) + epsilon
	if field_id == 4:
		return (x - 0.8) * (y - 1.1) - (z - 0.6) * (0.5 + 0.1 * float(seed)) + epsilon
	if field_id == 5:
		return x * x + y * y - z * z - (0.5 + 0.2 * float(seed)) + epsilon
	return x + 2.0 * y - 1.5 * z + 0.2 * x * y - 0.1 * y * z + epsilon

func _sample_values(samples: Array, field_id: int, seed: int) -> Array:
	var values: Array = []
	values.resize(13)
	for sample_id in range(9):
		values[sample_id] = _density(samples[sample_id] as Vector3, field_id, seed)
	values[9] = values[0]
	values[10] = values[2]
	values[11] = values[6]
	values[12] = values[8]
	return values

func _case_index(values: Array) -> int:
	var result: int = 0
	for sample_id in range(9):
		if float(values[sample_id]) < 0.0:
			result = result | (1 << int(sample_id))
	return result

func _sample_in_list(sample_id: int, samples: Array) -> bool:
	for raw_sample in samples:
		if int(raw_sample) == sample_id:
			return true
	return false

func _vertex_side_mask(sample_a: int, sample_b: int) -> int:
	var mask: int = 0
	if _sample_in_list(sample_a, _u_min_samples) and _sample_in_list(sample_b, _u_min_samples):
		mask = mask | (1 << SIDE_U_MIN)
	if _sample_in_list(sample_a, _v_min_samples) and _sample_in_list(sample_b, _v_min_samples):
		mask = mask | (1 << SIDE_V_MIN)
	return mask

func _edge_key(a: int, b: int) -> String:
	if b < a:
		return "%d:%d" % [b, a]
	return "%d:%d" % [a, b]

func _add_edge(edges: Dictionary, a: int, b: int) -> void:
	var key: String = _edge_key(a, b)
	var record: Array = edges.get(key, [0, a, b]) as Array
	record[0] = int(record[0]) + 1
	edges[key] = record

func _build_cell(table: Dictionary, local_positions: Dictionary, frame: Dictionary, field_id: int, seed: int) -> Dictionary:
	var samples: Array = _mapped_sample_positions(local_positions, frame)
	var values: Array = _sample_values(samples, field_id, seed)
	var case_index: int = _case_index(values)
	var case_record: Dictionary = (table.get("cases", []) as Array)[case_index] as Dictionary
	var vertices: PackedVector3Array = PackedVector3Array()
	var masks: PackedInt32Array = PackedInt32Array()
	for raw_vertex in case_record.get("vertices", []) as Array:
		var vertex: Dictionary = raw_vertex as Dictionary
		var sample_ids: Array = vertex.get("samples", []) as Array
		var sample_a: int = int(sample_ids[0])
		var sample_b: int = int(sample_ids[1])
		var value_a: float = float(values[sample_a])
		var value_b: float = float(values[sample_b])
		var denominator: float = abs(value_a) + abs(value_b)
		var t: float = 0.5
		if denominator > 0.000001:
			t = abs(value_a) / denominator
		vertices.append((samples[sample_a] as Vector3).lerp(samples[sample_b] as Vector3, clamp(t, 0.0, 1.0)))
		masks.append(_vertex_side_mask(sample_a, sample_b))
	var triangles: Array = []
	var determinant: float = (
		((frame.get("axis_u", Vector3.ZERO) as Vector3).cross(frame.get("axis_v", Vector3.ZERO) as Vector3))
		.dot(frame.get("axis_w", Vector3.ZERO) as Vector3)
	)
	for raw_triangle in case_record.get("triangles", []) as Array:
		var triangle: Dictionary = raw_triangle as Dictionary
		var ids: Array = triangle.get("vertices", []) as Array
		var oriented: Array = [int(ids[0]), int(ids[1]), int(ids[2])]
		if determinant < 0.0:
			oriented = [int(ids[0]), int(ids[2]), int(ids[1])]
		triangles.append(oriented)
	return {
		"case": case_index,
		"samples": samples,
		"values": values,
		"vertices": vertices,
		"masks": masks,
		"triangles": triangles
	}

func _validate_cell(cell: Dictionary) -> Dictionary:
	var vertices: PackedVector3Array = cell.get("vertices", PackedVector3Array()) as PackedVector3Array
	var triangles: Array = cell.get("triangles", []) as Array
	var edges: Dictionary = {}
	var result: Dictionary = {
		"vertices": vertices.size(),
		"triangles": triangles.size(),
		"invalid_triangles": 0,
		"degenerate_triangles": 0,
		"internal_winding_failures": 0
	}
	for raw_triangle in triangles:
		var ids: Array = raw_triangle as Array
		var a: int = int(ids[0])
		var b: int = int(ids[1])
		var c: int = int(ids[2])
		if a < 0 or b < 0 or c < 0 or a >= vertices.size() or b >= vertices.size() or c >= vertices.size() or a == b or b == c or c == a:
			result["invalid_triangles"] = int(result["invalid_triangles"]) + 1
			continue
		if (vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length_squared() <= 0.0000001:
			result["degenerate_triangles"] = int(result["degenerate_triangles"]) + 1
		_add_edge(edges, a, b)
		_add_edge(edges, b, c)
		_add_edge(edges, c, a)
	for raw_record in edges.values():
		var record: Array = raw_record as Array
		if int(record[0]) == 2:
			var reverse_key: String = "%d>%d" % [int(record[2]), int(record[1])]
			var forward_count: int = 0
			var reverse_count: int = 0
			for raw_triangle in triangles:
				var ids: Array = raw_triangle as Array
				var directed: Array = [
					"%d>%d" % [int(ids[0]), int(ids[1])],
					"%d>%d" % [int(ids[1]), int(ids[2])],
					"%d>%d" % [int(ids[2]), int(ids[0])]
				]
				for raw_direction in directed:
					if String(raw_direction) == "%d>%d" % [int(record[1]), int(record[2])]:
						forward_count += 1
					if String(raw_direction) == reverse_key:
						reverse_count += 1
			if forward_count != 1 or reverse_count != 1:
				result["internal_winding_failures"] = int(result["internal_winding_failures"]) + 1
	return result

func _quantize(value: float) -> int:
	if value >= 0.0:
		return int(value * 100000.0 + 0.5)
	return int(value * 100000.0 - 0.5)

func _quantized_point(value: Vector3) -> Array:
	return [_quantize(value.x), _quantize(value.y), _quantize(value.z)]

func _point_less(a: Array, b: Array) -> bool:
	if int(a[0]) != int(b[0]):
		return int(a[0]) < int(b[0])
	if int(a[1]) != int(b[1]):
		return int(a[1]) < int(b[1])
	return int(a[2]) < int(b[2])

func _point_text(point: Array) -> String:
	return "%d,%d,%d" % [int(point[0]), int(point[1]), int(point[2])]

func _fingerprint(cell: Dictionary, side: int) -> Dictionary:
	var vertices: PackedVector3Array = cell.get("vertices", PackedVector3Array()) as PackedVector3Array
	var masks: PackedInt32Array = cell.get("masks", PackedInt32Array()) as PackedInt32Array
	var triangles: Array = cell.get("triangles", []) as Array
	var edges: Dictionary = {}
	for raw_triangle in triangles:
		var ids: Array = raw_triangle as Array
		_add_edge(edges, int(ids[0]), int(ids[1]))
		_add_edge(edges, int(ids[1]), int(ids[2]))
		_add_edge(edges, int(ids[2]), int(ids[0]))
	var fingerprint: Dictionary = {}
	for raw_record in edges.values():
		var record: Array = raw_record as Array
		var a_id: int = int(record[1])
		var b_id: int = int(record[2])
		if int(record[0]) != 1 or (int(masks[a_id]) & (1 << side)) == 0 or (int(masks[b_id]) & (1 << side)) == 0:
			continue
		var a: Array = _quantized_point(vertices[a_id])
		var b: Array = _quantized_point(vertices[b_id])
		var direction: int = 1
		if _point_less(b, a):
			var swap: Array = a
			a = b
			b = swap
			direction = -1
		fingerprint[_point_text(a) + "|" + _point_text(b)] = direction
	return fingerprint

func _compare_fingerprints(a: Dictionary, b: Dictionary, totals: Dictionary) -> void:
	totals["shared_faces"] = int(totals["shared_faces"]) + 1
	if not a.is_empty() or not b.is_empty():
		totals["nonempty_shared_faces"] = int(totals["nonempty_shared_faces"]) + 1
	if a.size() != b.size():
		totals["lateral_geometry_failures"] = int(totals["lateral_geometry_failures"]) + 1
		return
	for raw_key in a.keys():
		var key: String = String(raw_key)
		if not b.has(key):
			totals["lateral_geometry_failures"] = int(totals["lateral_geometry_failures"]) + 1
		elif int(a[key]) + int(b[key]) != 0:
			totals["lateral_winding_failures"] = int(totals["lateral_winding_failures"]) + 1

func _compare_shared_samples(a: Dictionary, a_ids: Array, b: Dictionary, b_ids: Array, totals: Dictionary) -> void:
	var a_samples: Array = a.get("samples", []) as Array
	var b_samples: Array = b.get("samples", []) as Array
	var a_values: Array = a.get("values", []) as Array
	var b_values: Array = b.get("values", []) as Array
	for i in range(5):
		var a_id: int = int(a_ids[i])
		var b_id: int = int(b_ids[i])
		totals["shared_samples"] = int(totals["shared_samples"]) + 1
		if not _vector_near(a_samples[a_id] as Vector3, b_samples[b_id] as Vector3):
			totals["sample_position_failures"] = int(totals["sample_position_failures"]) + 1
		if not _near(float(a_values[a_id]), float(b_values[b_id])):
			totals["sample_value_failures"] = int(totals["sample_value_failures"]) + 1

func _corner_frames(sign_x: int, sign_y: int, sign_z: int) -> Array:
	return [
		{"origin": Vector3.ZERO, "axis_u": Vector3(0.0, float(sign_y), 0.0), "axis_v": Vector3(0.0, 0.0, float(sign_z)), "axis_w": Vector3(0.5 * float(sign_x), 0.0, 0.0)},
		{"origin": Vector3.ZERO, "axis_u": Vector3(0.0, 0.0, float(sign_z)), "axis_v": Vector3(float(sign_x), 0.0, 0.0), "axis_w": Vector3(0.0, 0.5 * float(sign_y), 0.0)},
		{"origin": Vector3.ZERO, "axis_u": Vector3(float(sign_x), 0.0, 0.0), "axis_v": Vector3(0.0, float(sign_y), 0.0), "axis_w": Vector3(0.0, 0.0, 0.5 * float(sign_z))}
	]

func _make_array_mesh(vertices: PackedVector3Array, indices: PackedInt32Array) -> Dictionary:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	if vertices.size() > 0 and indices.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mdt_error: int = ERR_DOES_NOT_EXIST
	var mdt_faces: int = 0
	var mdt_vertices: int = 0
	var mdt_edges: int = 0
	if mesh.get_surface_count() == 1:
		var mdt: MeshDataTool = MeshDataTool.new()
		mdt_error = mdt.create_from_surface(mesh, 0)
		if mdt_error == OK:
			mdt_faces = mdt.get_face_count()
			mdt_vertices = mdt.get_vertex_count()
			mdt_edges = mdt.get_edge_count()
	return {
		"status": "PASS" if mesh.get_surface_count() == 1 and mdt_error == OK else "FAIL",
		"surface_count": mesh.get_surface_count(),
		"mdt_error": mdt_error,
		"mdt_faces": mdt_faces,
		"mdt_vertices": mdt_vertices,
		"mdt_edges": mdt_edges
	}

func _run_validation(table: Dictionary) -> Dictionary:
	var local_positions: Dictionary = _load_local_positions(table)
	var totals: Dictionary = {
		"octants": 0,
		"fields": FIELD_COUNT,
		"seeds": SEED_COUNT,
		"junctions": 0,
		"builds": 0,
		"vertices": 0,
		"triangles": 0,
		"invalid_triangles": 0,
		"degenerate_triangles": 0,
		"internal_winding_failures": 0,
		"shared_faces": 0,
		"nonempty_shared_faces": 0,
		"shared_samples": 0,
		"sample_position_failures": 0,
		"sample_value_failures": 0,
		"lateral_geometry_failures": 0,
		"lateral_winding_failures": 0,
		"corner_position_failures": 0,
		"corner_value_failures": 0
	}
	var gallery_vertices: PackedVector3Array = PackedVector3Array()
	var gallery_indices: PackedInt32Array = PackedInt32Array()
	for sign_x in [-1, 1]:
		for sign_y in [-1, 1]:
			for sign_z in [-1, 1]:
				totals["octants"] = int(totals["octants"]) + 1
				var frames: Array = _corner_frames(int(sign_x), int(sign_y), int(sign_z))
				for field_id in range(FIELD_COUNT):
					for seed in range(SEED_COUNT):
						var cells: Array = []
						for raw_frame in frames:
							var cell: Dictionary = _build_cell(table, local_positions, raw_frame as Dictionary, int(field_id), int(seed))
							var validation: Dictionary = _validate_cell(cell)
							totals["builds"] = int(totals["builds"]) + 1
							for key in ["vertices", "triangles", "invalid_triangles", "degenerate_triangles", "internal_winding_failures"]:
								totals[key] = int(totals[key]) + int(validation.get(key, 0))
							var base: int = gallery_vertices.size()
							var vertices: PackedVector3Array = cell.get("vertices", PackedVector3Array()) as PackedVector3Array
							for vertex in vertices:
								gallery_vertices.append(vertex as Vector3)
							for raw_triangle in cell.get("triangles", []) as Array:
								var ids: Array = raw_triangle as Array
								gallery_indices.append(base + int(ids[0]))
								gallery_indices.append(base + int(ids[1]))
								gallery_indices.append(base + int(ids[2]))
							cells.append(cell)
						totals["junctions"] = int(totals["junctions"]) + 1
						_compare_shared_samples(cells[0] as Dictionary, _u_min_samples, cells[1] as Dictionary, _v_min_samples, totals)
						_compare_shared_samples(cells[1] as Dictionary, _u_min_samples, cells[2] as Dictionary, _v_min_samples, totals)
						_compare_shared_samples(cells[2] as Dictionary, _u_min_samples, cells[0] as Dictionary, _v_min_samples, totals)
						var expected_inner: Vector3 = Vector3(0.5 * float(sign_x), 0.5 * float(sign_y), 0.5 * float(sign_z))
						var samples_x: Array = (cells[0] as Dictionary).get("samples", []) as Array
						var samples_y: Array = (cells[1] as Dictionary).get("samples", []) as Array
						var samples_z: Array = (cells[2] as Dictionary).get("samples", []) as Array
						if not _vector_near(samples_x[0] as Vector3, samples_y[0] as Vector3) or not _vector_near(samples_y[0] as Vector3, samples_z[0] as Vector3) or not _vector_near(samples_x[9] as Vector3, expected_inner) or not _vector_near(samples_y[9] as Vector3, expected_inner) or not _vector_near(samples_z[9] as Vector3, expected_inner):
							totals["corner_position_failures"] = int(totals["corner_position_failures"]) + 1
						var values_x: Array = (cells[0] as Dictionary).get("values", []) as Array
						var values_y: Array = (cells[1] as Dictionary).get("values", []) as Array
						var values_z: Array = (cells[2] as Dictionary).get("values", []) as Array
						if not _near(float(values_x[0]), float(values_y[0])) or not _near(float(values_y[0]), float(values_z[0])) or not _near(float(values_x[9]), float(values_y[9])) or not _near(float(values_y[9]), float(values_z[9])):
							totals["corner_value_failures"] = int(totals["corner_value_failures"]) + 1
						_compare_fingerprints(_fingerprint(cells[0] as Dictionary, SIDE_U_MIN), _fingerprint(cells[1] as Dictionary, SIDE_V_MIN), totals)
						_compare_fingerprints(_fingerprint(cells[1] as Dictionary, SIDE_U_MIN), _fingerprint(cells[2] as Dictionary, SIDE_V_MIN), totals)
						_compare_fingerprints(_fingerprint(cells[2] as Dictionary, SIDE_U_MIN), _fingerprint(cells[0] as Dictionary, SIDE_V_MIN), totals)
	var mesh: Dictionary = _make_array_mesh(gallery_vertices, gallery_indices)
	var ok: bool = (
		int(totals["octants"]) == 8
		and int(totals["junctions"]) == 448
		and int(totals["builds"]) == 1344
		and int(totals["vertices"]) == 4680
		and int(totals["triangles"]) == 2896
		and int(totals["shared_faces"]) == 1344
		and int(totals["nonempty_shared_faces"]) == 500
		and int(totals["shared_samples"]) == 6720
		and int(totals["invalid_triangles"]) == 0
		and int(totals["degenerate_triangles"]) == 0
		and int(totals["internal_winding_failures"]) == 0
		and int(totals["sample_position_failures"]) == 0
		and int(totals["sample_value_failures"]) == 0
		and int(totals["lateral_geometry_failures"]) == 0
		and int(totals["lateral_winding_failures"]) == 0
		and int(totals["corner_position_failures"]) == 0
		and int(totals["corner_value_failures"]) == 0
		and String(mesh.get("status", "FAIL")) == "PASS"
		and int(mesh.get("mdt_faces", 0)) == 2896
	)
	return {
		"status": "PASS" if ok else "FAIL",
		"totals": totals,
		"mesh": mesh
	}

func _init() -> void:
	var table: Dictionary = _read_json(M4_PATH)
	var validation: Dictionary = _run_validation(table)
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_corner_junctions.v1",
		"status": validation.get("status", "FAIL"),
		"meaning": "Godot runtime validation of three mapped M4 transition cells meeting at every signed block-corner octant. Half-resolution faces are inset so coincident lateral faces share sample positions, values, boundary geometry, and opposite edge winding.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_reference_convention_equivalence": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"source_basis": "Clean-room transition-cell deformation and lateral-face rules derived from the public dissertation description; no official table arrays are read.",
		"validation": validation,
		"outputs": {"m4_table": M4_PATH, "report": OUT_PATH}
	}
	_write_json(OUT_PATH, report)
	print("m4_corner_junctions=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
