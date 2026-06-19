/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>

#include "transvoxel.h"
#include "transvoxel_m4_backend.h"

#define DEMO_CASE_INDEX 341
#define DEMO_M4_EXPECTED_VERTICES 12
#define DEMO_M4_EXPECTED_TRIANGLES 12

static void fill_transition_samples_from_case(
    int case_index,
    float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
}

static TvBuildInfo build_demo_case(void) {
    float samples[TV_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];

    fill_transition_samples_from_case(DEMO_CASE_INDEX, samples);
    return tv_build_transition_cell(
        samples,
        0.0f,
        tv_vec3(0.0f, 0.0f, 0.0f),
        tv_vec3(1.0f, 1.0f, 1.0f),
        vertices,
        TV_TRANSITION_MAX_VERTICES,
        triangles,
        TV_TRANSITION_MAX_TRIANGLES);
}

int main(void) {
    TvBuildInfo default_info;
    TvBuildInfo m4_info;
    TvBuildInfo restored_info;

    if (tv_transition_backend_is_custom()) {
        printf("unexpected_custom_backend_at_start\n");
        return 1;
    }

    default_info = build_demo_case();
    if (default_info.result != TV_OK || default_info.case_index != DEMO_CASE_INDEX) {
        printf(
            "default_build_failed result=%d case=%d\n",
            default_info.result,
            default_info.case_index);
        return 1;
    }

    if (tv_install_m4_transition_backend_candidate() != TV_OK) {
        printf("m4_install_failed\n");
        return 1;
    }
    if (!tv_transition_backend_is_custom()
        || !tv_m4_transition_backend_candidate_is_installed()) {
        printf("m4_install_state_failed\n");
        return 1;
    }

    m4_info = build_demo_case();
    if (m4_info.result != TV_OK || m4_info.case_index != DEMO_CASE_INDEX) {
        printf("m4_build_failed result=%d case=%d\n", m4_info.result, m4_info.case_index);
        return 1;
    }
    if (m4_info.vertex_count != DEMO_M4_EXPECTED_VERTICES
        || m4_info.triangle_count != DEMO_M4_EXPECTED_TRIANGLES) {
        printf(
            "m4_count_mismatch vertices=%d triangles=%d\n",
            m4_info.vertex_count,
            m4_info.triangle_count);
        return 1;
    }

    tv_uninstall_m4_transition_backend_candidate();
    if (tv_transition_backend_is_custom()
        || tv_m4_transition_backend_candidate_is_installed()) {
        printf("m4_uninstall_state_failed\n");
        return 1;
    }

    restored_info = build_demo_case();
    if (restored_info.result != TV_OK
        || restored_info.case_index != DEMO_CASE_INDEX
        || restored_info.vertex_count != default_info.vertex_count
        || restored_info.triangle_count != default_info.triangle_count) {
        printf("default_restore_failed\n");
        return 1;
    }

    printf(
        "m4 package backend case=%d default_vertices=%d default_triangles=%d m4_vertices=%d m4_triangles=%d restored_default=1 custom_after=0\n",
        DEMO_CASE_INDEX,
        default_info.vertex_count,
        default_info.triangle_count,
        m4_info.vertex_count,
        m4_info.triangle_count);
    return 0;
}
