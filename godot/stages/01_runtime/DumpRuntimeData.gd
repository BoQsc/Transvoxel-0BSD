# SPDX-License-Identifier: 0BSD
extends SceneTree

func _read_json(path: String) -> Dictionary:
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed as Dictionary
	return {}

func _safe_singleton_call(singleton_name: String, method_name: String) -> Variant:
	if not Engine.has_singleton(singleton_name):
		return null
	var obj: Object = Engine.get_singleton(singleton_name)
	if obj == null:
		return null
	if not obj.has_method(method_name):
		return null
	return obj.call(method_name)

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
	var regular: Dictionary = _read_json("res://generated/regular_tables.json")
	var transition: Dictionary = _read_json("res://generated/transition_tables.json")
	var transvoxel: Dictionary = _read_json("res://generated/transvoxel_tables.json")

	var data: Dictionary = {}
	data["schema"] = "boqsc.transvoxel.godot_runtime_dump.v1"
	data["status"] = "PASS"
	data["engine"] = {}
	data["engine"]["version_info"] = Engine.get_version_info()
	data["engine"]["architecture_name"] = Engine.get_architecture_name()
	data["engine"]["is_editor_hint"] = Engine.is_editor_hint()
	data["engine"]["is_embedded_in_editor"] = Engine.is_embedded_in_editor()
	data["os"] = {}
	data["os"]["name"] = OS.get_name()
	data["os"]["processor_name"] = OS.get_processor_name()
	data["os"]["processor_count"] = OS.get_processor_count()
	data["features"] = {}
	data["features"]["editor"] = OS.has_feature("editor")
	data["features"]["debug"] = OS.has_feature("debug")
	data["features"]["64"] = OS.has_feature("64")
	data["rendering"] = {}
	data["rendering"]["method"] = ProjectSettings.get_setting("rendering/renderer/rendering_method", "unknown")
	data["rendering"]["video_adapter_name"] = _safe_singleton_call("RenderingServer", "get_video_adapter_name")
	data["rendering"]["video_adapter_vendor"] = _safe_singleton_call("RenderingServer", "get_video_adapter_vendor")
	data["tables"] = {}
	data["tables"]["regular_schema"] = regular.get("schema", "missing")
	data["tables"]["transition_schema"] = transition.get("schema", "missing")
	data["tables"]["transvoxel_schema"] = transvoxel.get("schema", "missing")
	data["tables"]["regular_cases"] = (regular.get("cases", []) as Array).size() if regular.has("cases") else 0
	data["tables"]["transition_cases"] = (transition.get("cases", []) as Array).size() if transition.has("cases") else 0
	data["tables"]["transvoxel_status"] = transvoxel.get("status", "missing")
	if int(data["tables"]["regular_cases"]) != 256:
		data["status"] = "FAIL"
	if int(data["tables"]["transition_cases"]) != 512:
		data["status"] = "FAIL"

	_write_json("res://validation/01_runtime/runtime_dump.json", data)
	print("runtime_dump=", data["status"])
	print(ProjectSettings.globalize_path("res://validation/01_runtime/runtime_dump.json"))
	quit(0 if data["status"] == "PASS" else 1)
