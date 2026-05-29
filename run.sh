#!/bin/sh
cd "$(dirname "$0")" || exit 1
MODE=${1:-full}
if [ "$MODE" = "fast" ] || [ "$MODE" = "core" ] || [ "$MODE" = "godot" ] || [ "$MODE" = "full" ]; then
    shift || true
    if command -v python3 >/dev/null 2>&1; then
        exec python3 tools/run_everything.py --mode "$MODE" "$@"
    fi
    exec python tools/run_everything.py --mode "$MODE" "$@"
fi
if command -v python3 >/dev/null 2>&1; then
    exec python3 tools/run_everything.py "$@"
fi
exec python tools/run_everything.py "$@"
