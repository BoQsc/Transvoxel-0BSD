# SPDX-License-Identifier: 0BSD
extends SceneTree

func _init() -> void:
	var files: Array = [
		"res://generated/regular_tables.json",
		"res://generated/transition_tables.json",
		"res://generated/transvoxel_tables.json",
	]
	var ok: bool = true
	for raw_path in files:
		var path: String = String(raw_path)
		if not FileAccess.file_exists(path):
			push_error("missing: " + path)
			ok = false
			continue
		var text: String = FileAccess.get_file_as_string(path)
		var parsed: Variant = JSON.parse_string(text)
		if typeof(parsed) != TYPE_DICTIONARY:
			push_error("bad json: " + path)
			ok = false
		else:
			var data: Dictionary = parsed as Dictionary
			print(path, " schema=", data.get("schema", "none"))
	print("headless_validation=", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)
