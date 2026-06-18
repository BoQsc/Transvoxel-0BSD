# M7 Normal API Backend Switch

M7 makes the M4 candidate backend selectable through the normal public C API.

Default behavior remains unchanged. A project must compile the M4 adapter and
install it explicitly:

```c
#include "transvoxel_m4_backend.h"

tv_install_m4_transition_backend_candidate();
/* Existing calls to tv_build_transition_cell() now use the M4 candidate. */
tv_uninstall_m4_transition_backend_candidate();
```

Compile the optional backend with:

```text
src/transvoxel.c
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
```

Run:

```text
RUN_M7.cmd
```

M7 validates:

- default normal API backend still builds all 512 cases;
- M4 installs into normal `tv_build_transition_cell()`;
- M4 through the normal API matches generated M4 counts for all 512 cases;
- M4 through the normal API passes deterministic strip seam validation;
- uninstall restores the default backend;
- M4/default remain structurally distinct.

Official equivalence remains `NOT_PROVEN`.
