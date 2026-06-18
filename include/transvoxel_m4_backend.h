/* SPDX-License-Identifier: 0BSD
 * M4 candidate backend adapter for the normal transvoxel.h API.
 *
 * Compile this adapter together with src/transvoxel.c and
 * src/transvoxel_m4_candidate.c, then call
 * tv_install_m4_transition_backend_candidate(). After installation, existing
 * calls to tv_build_transition_cell() route through the M4 candidate backend.
 */
#ifndef BOQSC_TRANSVOXEL_M4_BACKEND_H
#define BOQSC_TRANSVOXEL_M4_BACKEND_H

#include "transvoxel.h"

#ifdef __cplusplus
extern "C" {
#endif

int tv_install_m4_transition_backend_candidate(void);
void tv_uninstall_m4_transition_backend_candidate(void);
int tv_m4_transition_backend_candidate_is_installed(void);

#ifdef __cplusplus
}
#endif

#endif /* BOQSC_TRANSVOXEL_M4_BACKEND_H */
