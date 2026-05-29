# SPDX-License-Identifier: 0BSD
extends SceneTree

func _write_json(path: String, data: Dictionary) -> void:
	var dir_path: String = path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("cannot write " + path)
		return
	file.store_string(JSON.stringify(data, "\t"))
	file.close()

func _init() -> void:
	var vertices: PackedVector3Array = PackedVector3Array()
	vertices.push_back(Vector3(0.0, 0.0, 0.0))
	vertices.push_back(Vector3(1.0, 0.0, 0.0))
	vertices.push_back(Vector3(1.0, 0.0, 1.0))
	vertices.push_back(Vector3(0.0, 0.0, 1.0))
	var indices: PackedInt32Array = PackedInt32Array()
	indices.push_back(0)
	indices.push_back(1)
	indices.push_back(2)
	indices.push_back(0)
	indices.push_back(2)
	indices.push_back(3)
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mdt: MeshDataTool = MeshDataTool.new()
	var err: int = mdt.create_from_surface(mesh, 0)
	var data: Dictionary = {}
	data["schema"] = "boqsc.transvoxel.godot_mesh_api_dump.v1"
	data["status"] = "PASS" if err == OK else "FAIL"
	data["mesh"] = {}
	data["mesh"]["surface_count"] = mesh.get_surface_count()
	data["mesh"]["aabb"] = str(mesh.get_aabb())
	data["mesh"]["array_vertex_count"] = vertices.size()
	data["mesh"]["index_count"] = indices.size()
	data["mesh"]["mdt_create_error"] = err
	data["mesh"]["mdt_vertex_count"] = mdt.get_vertex_count() if err == OK else 0
	data["mesh"]["mdt_edge_count"] = mdt.get_edge_count() if err == OK else 0
	data["mesh"]["mdt_face_count"] = mdt.get_face_count() if err == OK else 0
	_write_json("res://validation/02_mesh_api/mesh_api_dump.json", data)
	print("mesh_api_dump=", data["status"])
	print(ProjectSettings.globalize_path("res://validation/02_mesh_api/mesh_api_dump.json"))
	quit(0 if data["status"] == "PASS" else 1)
