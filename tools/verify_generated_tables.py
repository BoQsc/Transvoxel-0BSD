#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def load_generator():
    root = Path(__file__).resolve().parents[1]
    path = root / "tools" / "generate_transition.py"
    spec = importlib.util.spec_from_file_location("generate_transition_tables", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    generated = root / "generated" / "transition_tables.json"

    if not generated.exists():
        print("missing generated table:", generated)
        return 1

    gen = load_generator()
    current = json.loads(generated.read_text(encoding="utf-8"))
    fresh = gen.generate_tables()

    if current != fresh:
        print("generated table is not reproducible")
        print("current sha256:", current.get("sha256_without_this_field"))
        print("fresh sha256:", fresh.get("sha256_without_this_field"))
        return 1

    errors = gen.verify_table(current)
    if errors:
        print("\n".join(errors))
        return 1

    print("ok")
    print("sha256:", current["sha256_without_this_field"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
