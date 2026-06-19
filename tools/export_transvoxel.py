#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""
Export the canonical tables into a Transvoxel table ABI.

This exporter intentionally does not copy Eric Lengyel's MIT-licensed
Transvoxel.cpp table values, names, packed encodings, or 73-class data layout.
It proves that our canonical tables can be consumed through the same high-level
pattern used by classic Transvoxel implementations:

    case index -> class index -> class data -> vertex refs + triangles

Each exported case is its own class. That is less compressed than the standard
73 transition equivalence classes, but it preserves behavior and keeps the
exporter mechanically generated from the canonical JSON. The default transition
table is the clean-room M4 published-topology table generated in
generated/official_topology_candidate_tables.json; the older independent
transition table remains a historical/auxiliary artifact, not the public
default transition backend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED = PROJECT_ROOT / "generated"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compact_case(case: dict) -> dict:
    vertices: List[Tuple[int, int]] = []
    for v in case["vertices"]:
        a, b = v["samples"]
        vertices.append((int(a), int(b)))
    triangles: List[Tuple[int, int, int]] = []
    for t in case["triangles"]:
        a, b, c = t["vertices"]
        triangles.append((int(a), int(b), int(c)))
    return {
        "case": int(case["case"]),
        "vertices": vertices,
        "triangles": triangles,
    }


def build_table(source: dict, prefix: str) -> dict:
    # Direct class mapping: every case gets its own class index.
    # This makes the table ABI obvious and avoids any hidden use of the
    # official 73-class equivalence table.
    cases = [compact_case(c) for c in source["cases"]]
    cases.sort(key=lambda c: c["case"])

    case_class: List[int] = []
    class_data: List[dict] = []
    vertex_refs: List[Tuple[int, int]] = []
    triangles: List[Tuple[int, int, int]] = []

    for cls, c in enumerate(cases):
        if c["case"] != cls:
            raise ValueError(f"{prefix}: expected case {cls}, got {c['case']}")
        case_class.append(cls)
        vo = len(vertex_refs)
        to = len(triangles)
        vertex_refs.extend(c["vertices"])
        triangles.extend(c["triangles"])
        class_data.append({
            "vertex_offset": vo,
            "vertex_count": len(c["vertices"]),
            "triangle_offset": to,
            "triangle_count": len(c["triangles"]),
        })

    return {
        "case_count": len(cases),
        "class_count": len(class_data),
        "case_class": case_class,
        "class_data": class_data,
        "vertex_refs": vertex_refs,
        "triangles": triangles,
        "max_vertex_count": max((len(c["vertices"]) for c in cases), default=0),
        "max_triangle_count": max((len(c["triangles"]) for c in cases), default=0),
    }


def sha256_canonical(obj: dict) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def c_array_u16(name: str, values: List[int], cols: int = 16) -> str:
    lines = [f"static const uint16_t {name}[{len(values)}] = {{"]
    for i in range(0, len(values), cols):
        chunk = values[i:i + cols]
        lines.append("    " + ", ".join(str(v) for v in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def c_pairs(name: str, values: List[Tuple[int, int]], cols: int = 4) -> str:
    lines = [f"static const TVCVertexRef {name}[{len(values)}] = {{"]
    for i in range(0, len(values), cols):
        chunk = values[i:i + cols]
        lines.append("    " + ", ".join(f"{{{a}, {b}}}" for a, b in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def c_tris(name: str, values: List[Tuple[int, int, int]], cols: int = 3) -> str:
    lines = [f"static const TVCTriangle {name}[{len(values)}] = {{"]
    for i in range(0, len(values), cols):
        chunk = values[i:i + cols]
        lines.append("    " + ", ".join(f"{{{a}, {b}, {c}}}" for a, b, c in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def c_class_data(name: str, values: List[dict], cols: int = 2) -> str:
    lines = [f"static const TVCClassData {name}[{len(values)}] = {{"]
    entries = [f"{{{d['vertex_offset']}, {d['vertex_count']}, {d['triangle_offset']}, {d['triangle_count']}}}" for d in values]
    for i in range(0, len(entries), cols):
        lines.append("    " + ", ".join(entries[i:i + cols]) + ",")
    lines.append("};")
    return "\n".join(lines)


def emit_h(data: dict) -> str:
    reg = data["regular"]
    trans = data["transition"]
    lines = []
    lines.append("/* SPDX-License-Identifier: 0BSD")
    lines.append(" * Generated by tools/export_transvoxel.py.")
    lines.append(" * Independent Transvoxel table ABI.")
    lines.append(" * Default transition source: clean-room M4 published-topology behavior.")
    lines.append(" * Not copied from, and not byte-compatible with, Eric Lengyel's MIT Transvoxel.cpp.")
    lines.append(" */")
    lines.append("#ifndef BOQSC_TRANSVOXEL_TABLES_H")
    lines.append("#define BOQSC_TRANSVOXEL_TABLES_H")
    lines.append("#include <stdint.h>")
    lines.append("#ifdef __cplusplus")
    lines.append("extern \"C\" {")
    lines.append("#endif")
    lines.append("")
    lines.append("typedef struct TVCVertexRef { uint8_t sample_a; uint8_t sample_b; } TVCVertexRef;")
    lines.append("typedef struct TVCTriangle { uint8_t v0; uint8_t v1; uint8_t v2; } TVCTriangle;")
    lines.append("typedef struct TVCClassData { uint16_t vertex_offset; uint8_t vertex_count; uint16_t triangle_offset; uint8_t triangle_count; } TVCClassData;")
    lines.append("")
    lines.append(f"#define TVC_REGULAR_CASE_COUNT {reg['case_count']}")
    lines.append(f"#define TVC_REGULAR_CLASS_COUNT {reg['class_count']}")
    lines.append(f"#define TVC_REGULAR_VERTEX_REF_COUNT {len(reg['vertex_refs'])}")
    lines.append(f"#define TVC_REGULAR_TRIANGLE_COUNT {len(reg['triangles'])}")
    lines.append(f"#define TVC_REGULAR_MAX_VERTEX_COUNT {reg['max_vertex_count']}")
    lines.append(f"#define TVC_REGULAR_MAX_TRIANGLE_COUNT {reg['max_triangle_count']}")
    lines.append(f"#define TVC_TRANSITION_CASE_COUNT {trans['case_count']}")
    lines.append(f"#define TVC_TRANSITION_CLASS_COUNT {trans['class_count']}")
    lines.append(f"#define TVC_TRANSITION_VERTEX_REF_COUNT {len(trans['vertex_refs'])}")
    lines.append(f"#define TVC_TRANSITION_TRIANGLE_COUNT {len(trans['triangles'])}")
    lines.append(f"#define TVC_TRANSITION_MAX_VERTEX_COUNT {trans['max_vertex_count']}")
    lines.append(f"#define TVC_TRANSITION_MAX_TRIANGLE_COUNT {trans['max_triangle_count']}")
    lines.append("")
    lines.append(c_array_u16("tvc_regular_case_class", reg["case_class"]))
    lines.append(c_class_data("tvc_regular_class_data", reg["class_data"]))
    lines.append(c_pairs("tvc_regular_vertex_refs", reg["vertex_refs"]))
    lines.append(c_tris("tvc_regular_triangles", reg["triangles"]))
    lines.append("")
    lines.append(c_array_u16("tvc_transition_case_class", trans["case_class"]))
    lines.append(c_class_data("tvc_transition_class_data", trans["class_data"]))
    lines.append(c_pairs("tvc_transition_vertex_refs", trans["vertex_refs"]))
    lines.append(c_tris("tvc_transition_triangles", trans["triangles"]))
    lines.append("")
    lines.append("#ifdef __cplusplus")
    lines.append("}")
    lines.append("#endif")
    lines.append("#endif")
    lines.append("")
    return "\n".join(lines)


def d_array_u16(name: str, values: List[int]) -> str:
    body = ", ".join(str(v) for v in values)
    return f"immutable ushort[] {name} = [{body}];"


def d_pairs(name: str, values: List[Tuple[int, int]]) -> str:
    body = ", ".join(f"TVCVertexRef({a}, {b})" for a, b in values)
    return f"immutable TVCVertexRef[] {name} = [{body}];"


def d_tris(name: str, values: List[Tuple[int, int, int]]) -> str:
    body = ", ".join(f"TVCTriangle({a}, {b}, {c})" for a, b, c in values)
    return f"immutable TVCTriangle[] {name} = [{body}];"


def d_class_data(name: str, values: List[dict]) -> str:
    body = ", ".join(
        f"TVCClassData({d['vertex_offset']}, {d['vertex_count']}, {d['triangle_offset']}, {d['triangle_count']})"
        for d in values
    )
    return f"immutable TVCClassData[] {name} = [{body}];"


def emit_d(data: dict) -> str:
    reg = data["regular"]
    trans = data["transition"]
    lines = []
    lines.append("// SPDX-License-Identifier: 0BSD")
    lines.append("// Generated by tools/export_transvoxel.py.")
    lines.append("// Independent Transvoxel table ABI.")
    lines.append("// Default transition source: clean-room M4 published-topology behavior.")
    lines.append("module transvoxel_tables;")
    lines.append("")
    lines.append("struct TVCVertexRef { ubyte sampleA; ubyte sampleB; }")
    lines.append("struct TVCTriangle { ubyte v0; ubyte v1; ubyte v2; }")
    lines.append("struct TVCClassData { ushort vertexOffset; ubyte vertexCount; ushort triangleOffset; ubyte triangleCount; }")
    lines.append("")
    for k, v in [
        ("TVC_REGULAR_CASE_COUNT", reg['case_count']),
        ("TVC_REGULAR_CLASS_COUNT", reg['class_count']),
        ("TVC_REGULAR_VERTEX_REF_COUNT", len(reg['vertex_refs'])),
        ("TVC_REGULAR_TRIANGLE_COUNT", len(reg['triangles'])),
        ("TVC_TRANSITION_CASE_COUNT", trans['case_count']),
        ("TVC_TRANSITION_CLASS_COUNT", trans['class_count']),
        ("TVC_TRANSITION_VERTEX_REF_COUNT", len(trans['vertex_refs'])),
        ("TVC_TRANSITION_TRIANGLE_COUNT", len(trans['triangles'])),
    ]:
        lines.append(f"enum {k} = {v};")
    lines.append("")
    lines.append(d_array_u16("tvcRegularCaseClass", reg["case_class"]))
    lines.append(d_class_data("tvcRegularClassData", reg["class_data"]))
    lines.append(d_pairs("tvcRegularVertexRefs", reg["vertex_refs"]))
    lines.append(d_tris("tvcRegularTriangles", reg["triangles"]))
    lines.append("")
    lines.append(d_array_u16("tvcTransitionCaseClass", trans["case_class"]))
    lines.append(d_class_data("tvcTransitionClassData", trans["class_data"]))
    lines.append(d_pairs("tvcTransitionVertexRefs", trans["vertex_refs"]))
    lines.append(d_tris("tvcTransitionTriangles", trans["triangles"]))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(GENERATED), help="output directory")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    regular = load_json(GENERATED / "regular_tables.json")
    transition = load_json(GENERATED / "official_topology_candidate_tables.json")
    legacy_transition = load_json(GENERATED / "transition_tables.json")
    transvoxel = {
        "schema": "boqsc.transvoxel_tables.v1",
        "license": "0BSD",
        "status": (
            "transvoxel-table-export; default transition uses clean-room M4 "
            "published-topology behavior; not official Transvoxel.cpp "
            "byte/table clone"
        ),
        "table_contract": "case index -> class index -> class data -> vertex refs + triangles",
        "compression": "direct one-class-per-case; no official 73-class packed layout",
        "regular": build_table(regular, "regular"),
        "transition": build_table(transition, "transition_m4_default"),
        "source_tables": {
            "regular_schema": regular.get("schema"),
            "regular_sha256_without_this_field": regular.get("sha256_without_this_field"),
            "transition_source": "generated/official_topology_candidate_tables.json",
            "transition_schema": transition.get("schema"),
            "transition_sha256_without_this_field": transition.get("sha256_without_this_field"),
            "legacy_transition_source": "generated/transition_tables.json",
            "legacy_transition_schema": legacy_transition.get("schema"),
            "legacy_transition_sha256_without_this_field": legacy_transition.get("sha256_without_this_field"),
        },
    }
    transvoxel["sha256"] = sha256_canonical({k: v for k, v in transvoxel.items() if k != "sha256"})

    (out / "transvoxel_tables.json").write_text(
        json.dumps(transvoxel, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "transvoxel_tables.h").write_text(emit_h(transvoxel), encoding="utf-8")
    (out / "transvoxel_tables.d").write_text(emit_d(transvoxel), encoding="utf-8")
    print("wrote", out / "transvoxel_tables.json")
    print("sha256", transvoxel["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
