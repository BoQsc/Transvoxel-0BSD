/* SPDX-License-Identifier: 0BSD */
#include "transvoxel_m4_backend.h"
#include "transvoxel_m4_candidate.h"

static TvBuildInfo tv_m4_transition_backend_adapter(
    const float sample_values[TV_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles) {

    float m4_samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    int i;

    if (!sample_values) {
        return tv_m4_build_transition_cell_candidate(
            0,
            iso_level,
            origin,
            scale,
            out_vertices,
            max_vertices,
            out_triangles,
            max_triangles);
    }

    for (i = 0; i < TV_M4_TRANSITION_SAMPLE_COUNT; ++i) {
        m4_samples[i] = sample_values[i];
    }

    return tv_m4_build_transition_cell_candidate(
        m4_samples,
        iso_level,
        origin,
        scale,
        out_vertices,
        max_vertices,
        out_triangles,
        max_triangles);
}

int tv_install_m4_transition_backend_candidate(void) {
    return tv_set_transition_backend_callback(tv_m4_transition_backend_adapter);
}

void tv_uninstall_m4_transition_backend_candidate(void) {
    if (tv_get_transition_backend_callback() == tv_m4_transition_backend_adapter) {
        tv_reset_transition_backend_callback();
    }
}

int tv_m4_transition_backend_candidate_is_installed(void) {
    return tv_get_transition_backend_callback() == tv_m4_transition_backend_adapter;
}
