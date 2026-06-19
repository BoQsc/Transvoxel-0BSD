# SPDX-License-Identifier: 0BSD
extends SceneTree

const M4_PATH: String = "res://generated/official_topology_candidate_tables.json"
const OUT_PATH: String = "res://validation/11_m4_six_face_orientation/m4_six_face_orientation.json"
const GRID_SIZE: int = 4
const SEED_COUNT: int = 4
const FIELD_COUNT: int = 7
const SIDE_U_MIN: int = 0
const SIDE_U_MAX: int = 1
const SIDE_V_MIN: int = 2
const SIDE_V_MAX: int = 3

var _face_specs: Array = [
	{"id": 0, "name": "positive_x", "u": Vector3(0.0, 1.0, 0.0), "v": Vector3(0.0, 0.0, 1.0), "w": Vector3(1.0, 0.0, 0.0)},
	{"id": 1, "name": "negative_x", "u": Vector3(0.0, -1.0, 0.0), "v": Vector3(0.0, 0.0, 1.0), "w": Vector3(-1.0, 0.0, 0.0)},
	{"id": 2, "name": "positive_y", "u": Vector3(0.0, 0.0, 1.0), "v": Vector3(1.0, 0.0, 0.0), "w": Vector3(0.0, 1.0, 0.0)},
	{"id": 3, "name": "negative_y", "u": Vector3(0.0, 0.0, -1.0), "v": Vector3(1.0, 0.0, 0.0), "w": Vector3(0.0, -1.0, 0.0)},
	{"id": 4, "name": "positive_z", "u": Vector3(1.0, 0.0, 0.0), "v": Vector3(0.0, 1.0, 0.0), "w": Vector3(0.0, 0.0, 1.0)},
	{"id": 5, "name": "negative_z", "u": Vector3(-1.0, 0.0, 0.0), "v": Vector3(0.0, 1.0, 0.0), "w": Vector3(0.0, 0.0, -1.0)}
]

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

func _vector_array(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func _near(a: float, b: float) -> bool:
	return abs(a - b) <= 0.0001

func _vector_near(a: Vector3, b: Vector3) -> bool:
	return _near(a.x, b.x) and _near(a.y, b.y) and _near(a.z, b.z)

func _frame(spec: Dictionary, origin: Vector3, local_scale: Vector3) -> Dictionary:
	var axis_u: Vector3 = (spec.get("u", Vector3.ZERO) as Vector3) * local_scale.x
	var axis_v: Vector3 = (spec.get("v", Vector3.ZERO) as Vector3) * local_scale.y
	var axis_w: Vector3 = (spec.get("w", Vector3.ZERO) as Vector3) * local_scale.z
	return {
		"origin": origin,
		"axis_u": axis_u,
		"axis_v": axis_v,
		"axis_w": axis_w,
		"determinant": axis_u.cross(axis_v).dot(axis_w)
	}

func _frame_position(frame: Dictionary, local: Vector3) -> Vector3:
	var origin: Vector3 = frame.get("origin", Vector3.ZERO) as Vector3
	var axis_u: Vector3 = frame.get("axis_u", Vector3.ZERO) as Vector3
	var axis_v: Vector3 = frame.get("axis_v", Vector3.ZERO) as Vector3
	var axis_w: Vector3 = frame.get("axis_w", Vector3.ZERO) as Vector3
	return origin + axis_u * local.x + axis_v * local.y + axis_w * local.z

func _frame_to_local(frame: Dictionary, world: Vector3) -> Vector3:
	var origin: Vector3 = frame.get("origin", Vector3.ZERO) as Vector3
	var axis_u: Vector3 = frame.get("axis_u", Vector3.ZERO) as Vector3
	var axis_v: Vector3 = frame.get("axis_v", Vector3.ZERO) as Vector3
	var axis_w: Vector3 = frame.get("axis_w", Vector3.ZERO) as Vector3
	var delta: Vector3 = world - origin
	return Vector3(
		delta.dot(axis_u) / axis_u.length_squared(),
		delta.dot(axis_v) / axis_v.length_squared(),
		delta.dot(axis_w) / axis_w.length_squared()
	)

func _expected_transformed_cross(frame: Dictionary, local_cross: Vector3) -> Vector3:
	var axis_u: Vector3 = frame.get("axis_u", Vector3.ZERO) as Vector3
	var axis_v: Vector3 = frame.get("axis_v", Vector3.ZERO) as Vector3
	var axis_w: Vector3 = frame.get("axis_w", Vector3.ZERO) as Vector3
	var determinant: float = float(frame.get("determinant", 0.0))
	return (
		axis_u * (determinant * local_cross.x / axis_u.length_squared())
		+ axis_v * (determinant * local_cross.y / axis_v.length_squared())
		+ axis_w * (determinant * local_cross.z / axis_w.length_squared())
	)

func _load_positions(table: Dictionary) -> Dictionary:
	var positions: Dictionary = {}
	var samples: Array = table.get("samples", []) as Array
	for raw_sample in samples:
		var sample: Dictionary = raw_sample as Dictionary
		var raw_position: Array = sample.get("position", [0.0, 0.0, 0.0]) as Array
		positions[int(sample.get("id", -1))] = Vector3(
			float(raw_position[0]),
			float(raw_position[1]),
			float(raw_position[2])
		)
	return positions

func _local_vertices(case_record: Dictionary, positions: Dictionary) -> PackedVector3Array:
	var vertices: PackedVector3Array = PackedVector3Array()
	var case_vertices: Array = case_record.get("vertices", []) as Array
	for raw_vertex in case_vertices:
		var vertex: Dictionary = raw_vertex as Dictionary
		var sample_ids: Array = vertex.get("samples", []) as Array
		if sample_ids.size() != 2:
			vertices.append(Vector3.ZERO)
			continue
		var a: Vector3 = positions.get(int(sample_ids[0]), Vector3.ZERO) as Vector3
		var b: Vector3 = positions.get(int(sample_ids[1]), Vector3.ZERO) as Vector3
		vertices.append((a + b) * 0.5)
	return vertices

func _make_array_mesh(vertices: PackedVector3Array, indices: PackedInt32Array) -> Dictionary:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	if vertices.size() > 0 and indices.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mdt_error: int = ERR_DOES_NOT_EXIST
	var mdt_vertices: int = 0
	var mdt_edges: int = 0
	var mdt_faces: int = 0
	if mesh.get_surface_count() == 1:
		var mdt: MeshDataTool = MeshDataTool.new()
		mdt_error = mdt.create_from_surface(mesh, 0)
		if mdt_error == OK:
			mdt_vertices = mdt.get_vertex_count()
			mdt_edges = mdt.get_edge_count()
			mdt_faces = mdt.get_face_count()
	return {
		"status": "PASS" if mesh.get_surface_count() == 1 and mdt_error == OK else "FAIL",
		"surface_count": mesh.get_surface_count(),
		"array_vertices": vertices.size(),
		"array_indices": indices.size(),
		"mdt_error": mdt_error,
		"mdt_vertices": mdt_vertices,
		"mdt_edges": mdt_edges,
		"mdt_faces": mdt_faces
	}

func _validate_face_cases(table: Dictionary, positions: Dictionary, spec: Dictionary) -> Dictionary:
	var cases: Array = table.get("cases", []) as Array
	var frame: Dictionary = _frame(spec, Vector3(11.0, -7.0, 3.0), Vector3(0.75, 1.25, 1.5))
	var gallery_vertices: PackedVector3Array = PackedVector3Array()
	var gallery_indices: PackedInt32Array = PackedInt32Array()
	var totals: Dictionary = {
		"cases": 0,
		"vertices": 0,
		"triangles": 0,
		"invalid_triangles": 0,
		"degenerate_triangles": 0,
		"transform_failures": 0,
		"orientation_failures": 0,
		"frame_failures": 0
	}
	var unit_frame: Dictionary = _frame(spec, Vector3(3.0, -5.0, 7.0), Vector3.ONE)
	if not _near(float(unit_frame.get("determinant", 0.0)), 1.0):
		totals["frame_failures"] = int(totals["frame_failures"]) + 1
	var unit_u: Vector3 = unit_frame.get("axis_u", Vector3.ZERO) as Vector3
	var unit_v: Vector3 = unit_frame.get("axis_v", Vector3.ZERO) as Vector3
	var unit_w: Vector3 = unit_frame.get("axis_w", Vector3.ZERO) as Vector3
	if not _near(unit_u.dot(unit_v), 0.0) or not _near(unit_u.dot(unit_w), 0.0) or not _near(unit_v.dot(unit_w), 0.0):
		totals["frame_failures"] = int(totals["frame_failures"]) + 1
	for raw_local_sample in positions.values():
		var local_sample: Vector3 = raw_local_sample as Vector3
		var world_sample: Vector3 = _frame_position(frame, local_sample)
		if not _vector_near(_frame_to_local(frame, world_sample), local_sample):
			totals["frame_failures"] = int(totals["frame_failures"]) + 1

	for case_index in range(cases.size()):
		var case_record: Dictionary = cases[case_index] as Dictionary
		var local_vertices: PackedVector3Array = _local_vertices(case_record, positions)
		var world_vertices: PackedVector3Array = PackedVector3Array()
		var base: int = gallery_vertices.size()
		totals["cases"] = int(totals["cases"]) + 1
		totals["vertices"] = int(totals["vertices"]) + local_vertices.size()
		for local in local_vertices:
			var local_position: Vector3 = local as Vector3
			var world: Vector3 = _frame_position(frame, local_position)
			var recovered: Vector3 = _frame_to_local(frame, world)
			if not _vector_near(recovered, local_position):
				totals["transform_failures"] = int(totals["transform_failures"]) + 1
			world_vertices.append(world)
			gallery_vertices.append(world)
		var triangles: Array = case_record.get("triangles", []) as Array
		for raw_triangle in triangles:
			var triangle: Dictionary = raw_triangle as Dictionary
			var ids: Array = triangle.get("vertices", []) as Array
			totals["triangles"] = int(totals["triangles"]) + 1
			if ids.size() != 3:
				totals["invalid_triangles"] = int(totals["invalid_triangles"]) + 1
				continue
			var a_id: int = int(ids[0])
			var b_id: int = int(ids[1])
			var c_id: int = int(ids[2])
			if a_id < 0 or b_id < 0 or c_id < 0 or a_id >= local_vertices.size() or b_id >= local_vertices.size() or c_id >= local_vertices.size() or a_id == b_id or b_id == c_id or c_id == a_id:
				totals["invalid_triangles"] = int(totals["invalid_triangles"]) + 1
				continue
			var local_cross: Vector3 = (local_vertices[b_id] - local_vertices[a_id]).cross(local_vertices[c_id] - local_vertices[a_id])
			var world_cross: Vector3 = (world_vertices[b_id] - world_vertices[a_id]).cross(world_vertices[c_id] - world_vertices[a_id])
			if world_cross.length_squared() <= 0.0000001:
				totals["degenerate_triangles"] = int(totals["degenerate_triangles"]) + 1
				continue
			var expected_cross: Vector3 = _expected_transformed_cross(frame, local_cross)
			if not _vector_near(world_cross, expected_cross):
				totals["orientation_failures"] = int(totals["orientation_failures"]) + 1
			gallery_indices.append(base + a_id)
			gallery_indices.append(base + b_id)
			gallery_indices.append(base + c_id)
	var mesh: Dictionary = _make_array_mesh(gallery_vertices, gallery_indices)
	totals["mesh"] = mesh
	return totals

func _field_inside(field_id: int, x: int, y: int, seed: int) -> bool:
	if field_id == 0:
		return x < 3 + seed % 3
	if field_id == 1:
		return y < 3 + seed % 3
	if field_id == 2:
		return x + y < 6 + seed % 4
	if field_id == 3:
		var cx: int = 3 + seed % 2
		var cy: int = 3 + int(seed / 2) % 2
		var radius: int = 3 + seed % 2
		return (x - cx) * (x - cx) + (y - cy) * (y - cy) < radius * radius
	if field_id == 4:
		return (x - 3) * (x - 3) - (y - 3) * (y - 3) + seed - 1 < 0
	if field_id == 5:
		var noise: int = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xffffffff
		noise = ((noise ^ (noise >> 13)) * 1274126177) & 0xffffffff
		noise = (noise ^ (noise >> 16)) & 0xffffffff
		return (noise & 1) != 0
	return ((x + seed) % 7) + ((y * 3 + seed) % 11) < 8

func _case_for_cell(field_id: int, cell_x: int, cell_y: int, seed: int) -> int:
	var case_index: int = 0
	var sample_id: int = 0
	for sy in range(3):
		for sx in range(3):
			if _field_inside(field_id, cell_x * 2 + int(sx), cell_y * 2 + int(sy), seed):
				case_index = case_index | (1 << sample_id)
			sample_id += 1
	return case_index

func _quantize2(value: float) -> int:
	if value >= 0.0:
		return int(value * 2.0 + 0.5)
	return int(value * 2.0 - 0.5)

func _segment_key(a: Vector3, b: Vector3, side: int) -> String:
	var ax: int
	var ay: int
	var bx: int
	var by: int
	if side == SIDE_U_MIN or side == SIDE_U_MAX:
		ax = _quantize2(a.y)
		ay = _quantize2(a.z)
		bx = _quantize2(b.y)
		by = _quantize2(b.z)
	else:
		ax = _quantize2(a.x)
		ay = _quantize2(a.z)
		bx = _quantize2(b.x)
		by = _quantize2(b.z)
	if bx < ax or (bx == ax and by < ay):
		var swap_x: int = ax
		var swap_y: int = ay
		ax = bx
		ay = by
		bx = swap_x
		by = swap_y
	return "%d,%d,%d,%d" % [ax, ay, bx, by]

func _point_on_side(local: Vector3, side: int) -> bool:
	if side == SIDE_U_MIN:
		return _near(local.x, 0.0)
	if side == SIDE_U_MAX:
		return _near(local.x, 2.0)
	if side == SIDE_V_MIN:
		return _near(local.y, 0.0)
	return _near(local.y, 2.0)

func _edge_key(a: int, b: int) -> String:
	if b < a:
		return "%d:%d" % [b, a]
	return "%d:%d" % [a, b]

func _build_fingerprints(case_record: Dictionary, positions: Dictionary, frame: Dictionary) -> Dictionary:
	var local_vertices: PackedVector3Array = _local_vertices(case_record, positions)
	var world_vertices: PackedVector3Array = PackedVector3Array()
	for local in local_vertices:
		world_vertices.append(_frame_position(frame, local as Vector3))
	var edges: Dictionary = {}
	var triangles: Array = case_record.get("triangles", []) as Array
	for raw_triangle in triangles:
		var triangle: Dictionary = raw_triangle as Dictionary
		var ids: Array = triangle.get("vertices", []) as Array
		if ids.size() != 3:
			continue
		var edge_pairs: Array = [[int(ids[0]), int(ids[1])], [int(ids[1]), int(ids[2])], [int(ids[2]), int(ids[0])]]
		for raw_pair in edge_pairs:
			var pair: Array = raw_pair as Array
			var key: String = _edge_key(int(pair[0]), int(pair[1]))
			edges[key] = int(edges.get(key, 0)) + 1
	var fingerprints: Array = [[], [], [], []]
	var failures: int = 0
	for raw_key in edges.keys():
		var key: String = String(raw_key)
		var count: int = int(edges[key])
		if count > 2:
			failures += 1
			continue
		if count != 1:
			continue
		var parts: PackedStringArray = key.split(":")
		var a_id: int = int(parts[0])
		var b_id: int = int(parts[1])
		var a: Vector3 = _frame_to_local(frame, world_vertices[a_id])
		var b: Vector3 = _frame_to_local(frame, world_vertices[b_id])
		for side in range(4):
			if _point_on_side(a, int(side)) and _point_on_side(b, int(side)):
				(fingerprints[side] as Array).append(_segment_key(a, b, int(side)))
	for side in range(4):
		(fingerprints[side] as Array).sort()
	return {
		"fingerprints": fingerprints,
		"failures": failures,
		"vertices": local_vertices.size(),
		"triangles": triangles.size()
	}

func _fingerprints_equal(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in range(a.size()):
		if String(a[i]) != String(b[i]):
			return false
	return true

func _validate_face_seams(table: Dictionary, positions: Dictionary, spec: Dictionary) -> Dictionary:
	var cases: Array = table.get("cases", []) as Array
	var root: Vector3 = Vector3(-13.0, 17.0, 5.0)
	var root_frame: Dictionary = _frame(spec, root, Vector3.ONE)
	var axis_u: Vector3 = root_frame.get("axis_u", Vector3.ZERO) as Vector3
	var axis_v: Vector3 = root_frame.get("axis_v", Vector3.ZERO) as Vector3
	var result: Dictionary = {
		"seam_builds": 0,
		"shared_faces": 0,
		"seam_failures": 0,
		"seam_vertices": 0,
		"seam_triangles": 0
	}
	for field_id in range(FIELD_COUNT):
		for seed in range(SEED_COUNT):
			var grid: Array = []
			for y in range(GRID_SIZE):
				var row: Array = []
				for x in range(GRID_SIZE):
					var case_index: int = _case_for_cell(int(field_id), int(x), int(y), int(seed))
					var origin: Vector3 = root + axis_u * float(int(x) * 2) + axis_v * float(int(y) * 2)
					var cell_frame: Dictionary = _frame(spec, origin, Vector3.ONE)
					var built: Dictionary = _build_fingerprints(cases[case_index] as Dictionary, positions, cell_frame)
					row.append(built.get("fingerprints", [[], [], [], []]))
					result["seam_builds"] = int(result["seam_builds"]) + 1
					result["seam_failures"] = int(result["seam_failures"]) + int(built.get("failures", 0))
					result["seam_vertices"] = int(result["seam_vertices"]) + int(built.get("vertices", 0))
					result["seam_triangles"] = int(result["seam_triangles"]) + int(built.get("triangles", 0))
				grid.append(row)
			for y in range(GRID_SIZE):
				for x in range(GRID_SIZE - 1):
					result["shared_faces"] = int(result["shared_faces"]) + 1
					var left: Array = grid[y][x] as Array
					var right: Array = grid[y][x + 1] as Array
					if not _fingerprints_equal(left[SIDE_U_MAX] as Array, right[SIDE_U_MIN] as Array):
						result["seam_failures"] = int(result["seam_failures"]) + 1
			for y in range(GRID_SIZE - 1):
				for x in range(GRID_SIZE):
					result["shared_faces"] = int(result["shared_faces"]) + 1
					var lower: Array = grid[y][x] as Array
					var upper: Array = grid[y + 1][x] as Array
					if not _fingerprints_equal(lower[SIDE_V_MAX] as Array, upper[SIDE_V_MIN] as Array):
						result["seam_failures"] = int(result["seam_failures"]) + 1
	return result

func _face_status(face: Dictionary) -> String:
	var mesh: Dictionary = face.get("mesh", {}) as Dictionary
	var ok: bool = (
		int(face.get("cases", 0)) == 512
		and int(face.get("vertices", 0)) == 4096
		and int(face.get("triangles", 0)) == 2640
		and int(face.get("invalid_triangles", -1)) == 0
		and int(face.get("degenerate_triangles", -1)) == 0
		and int(face.get("transform_failures", -1)) == 0
		and int(face.get("orientation_failures", -1)) == 0
		and int(face.get("frame_failures", -1)) == 0
		and int(face.get("seam_builds", 0)) == 448
		and int(face.get("shared_faces", 0)) == 672
		and int(face.get("seam_failures", -1)) == 0
		and int(face.get("seam_vertices", 0)) == 1616
		and int(face.get("seam_triangles", 0)) == 1020
		and String(mesh.get("status", "FAIL")) == "PASS"
		and int(mesh.get("mdt_faces", 0)) == 2640
	)
	return "PASS" if ok else "FAIL"

func _run_validation(table: Dictionary) -> Dictionary:
	var positions: Dictionary = _load_positions(table)
	var faces: Array = []
	var totals: Dictionary = {
		"faces": 0,
		"failed_faces": 0,
		"cases": 0,
		"vertices": 0,
		"triangles": 0,
		"invalid_triangles": 0,
		"degenerate_triangles": 0,
		"transform_failures": 0,
		"orientation_failures": 0,
		"frame_failures": 0,
		"seam_builds": 0,
		"shared_faces": 0,
		"seam_failures": 0,
		"seam_vertices": 0,
		"seam_triangles": 0
	}
	for raw_spec in _face_specs:
		var spec: Dictionary = raw_spec as Dictionary
		var face: Dictionary = _validate_face_cases(table, positions, spec)
		var seams: Dictionary = _validate_face_seams(table, positions, spec)
		for key in ["seam_builds", "shared_faces", "seam_failures", "seam_vertices", "seam_triangles"]:
			face[key] = seams.get(key, 0)
		face["id"] = spec.get("id")
		face["name"] = spec.get("name")
		face["axis_u"] = _vector_array(spec.get("u", Vector3.ZERO) as Vector3)
		face["axis_v"] = _vector_array(spec.get("v", Vector3.ZERO) as Vector3)
		face["axis_w"] = _vector_array(spec.get("w", Vector3.ZERO) as Vector3)
		face["determinant"] = (spec.get("u", Vector3.ZERO) as Vector3).cross(spec.get("v", Vector3.ZERO) as Vector3).dot(spec.get("w", Vector3.ZERO) as Vector3)
		face["status"] = _face_status(face)
		totals["faces"] = int(totals["faces"]) + 1
		if String(face["status"]) != "PASS":
			totals["failed_faces"] = int(totals["failed_faces"]) + 1
		for key in ["cases", "vertices", "triangles", "invalid_triangles", "degenerate_triangles", "transform_failures", "orientation_failures", "frame_failures", "seam_builds", "shared_faces", "seam_failures", "seam_vertices", "seam_triangles"]:
			totals[key] = int(totals[key]) + int(face.get(key, 0))
		faces.append(face)
	var ok: bool = (
		int(totals["faces"]) == 6
		and int(totals["failed_faces"]) == 0
		and int(totals["cases"]) == 3072
		and int(totals["triangles"]) == 15840
		and int(totals["shared_faces"]) == 4032
		and int(totals["seam_failures"]) == 0
	)
	return {
		"status": "PASS" if ok else "FAIL",
		"faces": faces,
		"totals": totals
	}

func _init() -> void:
	var table: Dictionary = _read_json(M4_PATH)
	var validation: Dictionary = _run_validation(table)
	var report: Dictionary = {
		"schema": "boqsc.transvoxel.godot_m4_six_face_orientation.v1",
		"status": validation.get("status", "FAIL"),
		"meaning": "Godot runtime validation of the clean-room M4 candidate across explicit right-handed +X/-X/+Y/-Y/+Z/-Z transition frames. It checks all cases, ArrayMesh/MeshDataTool output, transformed winding, and deterministic side seams.",
		"official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
		"official_reference_convention_equivalence": "NOT_PROVEN",
		"official_triangle_topology_equivalence": "NOT_PROVEN",
		"default_core_replaced": false,
		"frame_contract": "local u/v span the 3x3 full-resolution face at w=0; local +w points toward the four half-resolution samples at w=1",
		"validation": validation,
		"outputs": {
			"m4_table": M4_PATH,
			"report": OUT_PATH
		}
	}
	_write_json(OUT_PATH, report)
	print("m4_six_face_orientation=", report["status"])
	print(ProjectSettings.globalize_path(OUT_PATH))
	quit(0 if String(report.get("status", "FAIL")) == "PASS" else 1)
