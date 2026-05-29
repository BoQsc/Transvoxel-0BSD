# v17 release notes

v17 fixes the C compiler detection regression found in v16.

The v16 package could carry a stale `proof/c_compiler_cache.json` from a Linux build machine.
On Windows this made `tools/test_core_c.py` try `/usr/bin/cc` and crash before it reached the
real local Zig compiler.

v17 changes:
- Removes shipped compiler cache from the package.
- Ignores old cache files without platform metadata.
- Skips missing compiler candidates instead of crashing.
- Continues to the next compiler candidate, including auto-detected `zig.exe`.
- Writes `validation/core_c_report.json` even when compiler startup fails.
