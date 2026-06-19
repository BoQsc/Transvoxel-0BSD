#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the Transvoxel table export against its canonical source tables."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED = PROJECT_ROOT / "generated"
VALIDATION = PROJECT_ROOT / "validation"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def canonical_case_signature(case: dict) -> dict:
    return {
        "vertices": [tuple(v["samples"]) for v in case["vertices"]],
        "triangles": [tuple(t["vertices"]) for t in case["triangles"]],
    }


def table_case_signature(table: dict, case_index: int) -> dict:
    cls = table["case_class"][case_index]
    cd = table["class_data"][cls]
    vo = cd["vertex_offset"]
    vc = cd["vertex_count"]
    to = cd["triangle_offset"]
    tc = cd["triangle_count"]
    return {
        "vertices": [tuple(v) for v in table["vertex_refs"][vo:vo + vc]],
        "triangles": [tuple(t) for t in table["triangles"][to:to + tc]],
    }


def validate_table(name: str, canonical: dict, table_export: dict) -> dict:
    errors: List[str] = []
    cases = canonical["cases"]
    if len(cases) != table_export["case_count"]:
        errors.append(f"{name}: case count mismatch")
    if len(table_export["case_class"]) != table_export["case_count"]:
        errors.append(f"{name}: case_class length mismatch")
    if len(table_export["class_data"]) != table_export["class_count"]:
        errors.append(f"{name}: class_data length mismatch")

    for i, case in enumerate(cases):
        if case["case"] != i:
            errors.append(f"{name}: canonical case order mismatch at {i}")
            continue
        a = canonical_case_signature(case)
        b = table_case_signature(table_export, i)
        if a != b:
            errors.append(f"{name}: case {i} signature mismatch")
            if len(errors) > 20:
                break
        # Validate local triangle indices.
        vc = len(b["vertices"])
        for tri in b["triangles"]:
            if any(v < 0 or v >= vc for v in tri):
                errors.append(f"{name}: case {i} triangle {tri} outside vertex count {vc}")
                break
    return {
        "name": name,
        "ok": not errors,
        "errors": errors,
        "case_count": table_export["case_count"],
        "class_count": table_export["class_count"],
        "vertex_ref_count": len(table_export["vertex_refs"]),
        "triangle_count": len(table_export["triangles"]),
        "max_vertex_count": table_export["max_vertex_count"],
        "max_triangle_count": table_export["max_triangle_count"],
    }


def compile_c_smoke_test(header: Path) -> dict:
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        return {"attempted": False, "ok": None, "reason": "no C compiler found"}
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "smoke.c"
        exe = td_path / "smoke"
        src.write_text(f"""
#include <stdio.h>
#include <stdint.h>
#include \"{header.as_posix()}\"
int main(void) {{
    if (TVC_REGULAR_CASE_COUNT != 256) return 10;
    if (TVC_TRANSITION_CASE_COUNT != 512) return 11;
    unsigned long long regular_triangles = 0;
    unsigned long long transition_triangles = 0;
    for (uint16_t i = 0; i < TVC_REGULAR_CASE_COUNT; ++i) {{
        uint16_t cls = tvc_regular_case_class[i];
        regular_triangles += tvc_regular_class_data[cls].triangle_count;
    }}
    for (uint16_t i = 0; i < TVC_TRANSITION_CASE_COUNT; ++i) {{
        uint16_t cls = tvc_transition_case_class[i];
        transition_triangles += tvc_transition_class_data[cls].triangle_count;
    }}
    if (regular_triangles != TVC_REGULAR_TRIANGLE_COUNT) return 12;
    if (transition_triangles != TVC_TRANSITION_TRIANGLE_COUNT) return 13;
    printf("regular=%llu transition=%llu\\n", regular_triangles, transition_triangles);
    return 0;
}}
""", encoding="utf-8")
        cmd = [cc, "-std=c99", "-Wall", "-Wextra", "-pedantic", str(src), "-o", str(exe)]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {"attempted": True, "ok": False, "compiler": cc, "stage": "compile", "stderr": proc.stderr[-4000:]}
        run = subprocess.run([str(exe)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return {"attempted": True, "ok": run.returncode == 0, "compiler": cc, "stage": "run", "stdout": run.stdout.strip(), "stderr": run.stderr.strip(), "returncode": run.returncode}


def main() -> int:
    VALIDATION.mkdir(exist_ok=True)
    regular = load(GENERATED / "regular_tables.json")
    transition = load(GENERATED / "official_topology_candidate_tables.json")
    transvoxel = load(GENERATED / "transvoxel_tables.json")
    reports = [
        validate_table("regular", regular, transvoxel["regular"]),
        validate_table("transition_m4_default", transition, transvoxel["transition"]),
    ]
    c_smoke = compile_c_smoke_test(GENERATED / "transvoxel_tables.h")
    ok = all(r["ok"] for r in reports) and (c_smoke["ok"] is not False)
    report = {
        "ok": ok,
        "transvoxel_schema": transvoxel.get("schema"),
        "transvoxel_sha256": transvoxel.get("sha256"),
        "default_transition_source": transvoxel.get("source_tables", {}).get("transition_source"),
        "tables": reports,
        "c_smoke_test": c_smoke,
        "status": (
            "validates Transvoxel table ABI against canonical JSON; default "
            "transition source is clean-room M4 published-topology behavior; "
            "not official Transvoxel.cpp byte clone"
        ),
    }
    (VALIDATION / "transvoxel_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = []
    md.append("# Transvoxel table validation")
    md.append("")
    md.append(f"Overall: {'PASS' if ok else 'FAIL'}")
    md.append("")
    md.append(f"Transvoxel schema: `{report['transvoxel_schema']}`")
    md.append(f"Transvoxel SHA-256: `{report['transvoxel_sha256']}`")
    md.append(f"Default transition source: `{report['default_transition_source']}`")
    md.append("")
    for r in reports:
        md.append(f"## {r['name']}")
        md.append("")
        md.append(f"- OK: `{r['ok']}`")
        md.append(f"- Cases: `{r['case_count']}`")
        md.append(f"- Classes: `{r['class_count']}`")
        md.append(f"- Vertex refs: `{r['vertex_ref_count']}`")
        md.append(f"- Triangles: `{r['triangle_count']}`")
        md.append(f"- Max vertices/case: `{r['max_vertex_count']}`")
        md.append(f"- Max triangles/case: `{r['max_triangle_count']}`")
        if r["errors"]:
            md.append("- Errors:")
            for e in r["errors"][:20]:
                md.append(f"  - {e}")
        md.append("")
    md.append("## C header smoke test")
    md.append("")
    md.append(f"- Attempted: `{c_smoke['attempted']}`")
    md.append(f"- OK: `{c_smoke['ok']}`")
    if c_smoke.get("compiler"):
        md.append(f"- Compiler: `{c_smoke['compiler']}`")
    if c_smoke.get("stdout"):
        md.append(f"- Output: `{c_smoke['stdout']}`")
    if c_smoke.get("reason"):
        md.append(f"- Reason: `{c_smoke['reason']}`")
    if c_smoke.get("stderr"):
        md.append("- Stderr excerpt:")
        md.append("```text")
        md.append(c_smoke["stderr"])
        md.append("```")
    md.append("")
    md.append("This proves that the generated table ABI round-trips back to the canonical JSON and can be consumed by a minimal C-style table reader. The default transition table is the clean-room M4 published-topology source. This does not prove byte-for-byte identity with Eric Lengyel's MIT-licensed table file.")
    (VALIDATION / "transvoxel_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("PASS" if ok else "FAIL")
    print(VALIDATION / "transvoxel_report.md")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
