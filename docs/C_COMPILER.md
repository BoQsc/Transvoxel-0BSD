# C compiler setup

The core test accepts normal C compilers and Zig's C compiler driver.

Recommended temporary setup on Windows:

1. Create `c_compiler_path.txt` next to `RUN.cmd`.
2. Put only the path to `zig.exe` inside it.

Example:

```text
C:\Users\Windows10_new\Documents\gpu-marching-cubes\addons\gdextension_setup\zig-x86_64-windows-0.16.0-dev.1484+d0ba6642b\zig.exe
```

The runner automatically calls it as:

```text
zig.exe cc
```

After a successful compile, the selected compiler is cached in:

```text
proof/c_compiler_cache.json
```

Run choices:

```text
RUN_CORE.cmd   only the C core/dist check
RUN_FAST.cmd   skip the C compiler and Godot for quick edits
RUN_FULL.cmd   full release proof
```

## v17 cache safety

The runner may cache a working compiler in `proof/c_compiler_cache.json`, but the cache is platform-specific.
A Linux cache such as `/usr/bin/cc` must never block Windows detection. The v17 compiler test ignores old
cache files without platform metadata and skips missing compiler paths instead of crashing.

