/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>

#include "transvoxel.h"
#include "transvoxel_m4_candidate.h"

#define EXPECTED_CASE_COUNT 512
#define EXPECTED_TOTAL_VERTICES 4096
#define EXPECTED_TOTAL_TRIANGLES 2640
#define EXPECTED_MAX_VERTICES 12
#define EXPECTED_MAX_TRIANGLES 12
#define DEMO_CASE_INDEX 341

static int custom_backend_calls = 0;

static float absf_local(float value) {
    return value < 0.0f ? -value : value;
}

static int same_vec3(TvVec3 a, TvVec3 b) {
    return absf_local(a.x - b.x) <= 0.000001f
        && absf_local(a.y - b.y) <= 0.000001f
        && absf_local(a.z - b.z) <= 0.000001f;
}

static int same_triangle(TvTriangle a, TvTriangle b) {
    return a.a == b.a && a.b == b.b && a.c == b.c;
}

static void fill_transition_samples(
    int case_index,
    float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
}

static void copy_m4_samples(
    const float samples[TV_TRANSITION_SAMPLE_COUNT],
    float m4_samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_M4_TRANSITION_SAMPLE_COUNT; ++i) {
        m4_samples[i] = samples[i];
    }
}

static int same_build(
    TvBuildInfo a_info,
    const TvVec3 *a_vertices,
    const TvTriangle *a_triangles,
    TvBuildInfo b_info,
    const TvVec3 *b_vertices,
    const TvTriangle *b_triangles) {
    int i;
    if (a_info.result != b_info.result
        || a_info.case_index != b_info.case_index
        || a_info.vertex_count != b_info.vertex_count
        || a_info.triangle_count != b_info.triangle_count) {
        return 0;
    }
    for (i = 0; i < a_info.vertex_count; ++i) {
        if (!same_vec3(a_vertices[i], b_vertices[i])) {
            return 0;
        }
    }
    for (i = 0; i < a_info.triangle_count; ++i) {
        if (!same_triangle(a_triangles[i], b_triangles[i])) {
            return 0;
        }
    }
    return 1;
}

static TvBuildInfo custom_backend(
    const float sample_values[TV_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles) {
    (void)sample_values;
    (void)iso_level;
    (void)origin;
    (void)scale;
    (void)out_triangles;
    (void)max_triangles;
    ++custom_backend_calls;
    if (!out_vertices) {
        return (TvBuildInfo){TV_ERROR_NULL, 0, 0, 0};
    }
    if (max_vertices < 1) {
        return (TvBuildInfo){TV_ERROR_SMALL_VERTEX_BUFFER, 777, 1, 0};
    }
    out_vertices[0] = tv_vec3(7.0f, 8.0f, 9.0f);
    return (TvBuildInfo){TV_OK, 777, 1, 0};
}

int main(void) {
    int case_index;
    int total_vertices = 0;
    int total_triangles = 0;
    int max_vertices = 0;
    int max_triangles = 0;
    int matches = 0;
    int sample13_ignored = 0;

    if (TV_TRANSITION_MAX_VERTICES != EXPECTED_MAX_VERTICES
        || TV_TRANSITION_MAX_TRIANGLES != EXPECTED_MAX_TRIANGLES) {
        printf(
            "transition_max_constants_wrong vertices=%d triangles=%d\n",
            TV_TRANSITION_MAX_VERTICES,
            TV_TRANSITION_MAX_TRIANGLES);
        return 1;
    }
    if (TV_TRANSITION_SAMPLE_COUNT != 14 || TV_M4_TRANSITION_SAMPLE_COUNT != 13) {
        printf(
            "sample_count_contract_wrong public=%d m4=%d\n",
            TV_TRANSITION_SAMPLE_COUNT,
            TV_M4_TRANSITION_SAMPLE_COUNT);
        return 1;
    }
    if (tv_transition_backend_is_custom()) {
        printf("unexpected_custom_backend_at_start\n");
        return 1;
    }

    for (case_index = 0; case_index < EXPECTED_CASE_COUNT; ++case_index) {
        float samples[TV_TRANSITION_SAMPLE_COUNT];
        float samples_alt13[TV_TRANSITION_SAMPLE_COUNT];
        float m4_samples[TV_M4_TRANSITION_SAMPLE_COUNT];
        TvVec3 default_vertices[TV_TRANSITION_MAX_VERTICES];
        TvVec3 default_vertices_alt13[TV_TRANSITION_MAX_VERTICES];
        TvVec3 m4_vertices[TV_M4_TRANSITION_MAX_VERTICES];
        TvTriangle default_triangles[TV_TRANSITION_MAX_TRIANGLES];
        TvTriangle default_triangles_alt13[TV_TRANSITION_MAX_TRIANGLES];
        TvTriangle m4_triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo default_info;
        TvBuildInfo default_alt13_info;
        TvBuildInfo m4_info;
        int i;

        fill_transition_samples(case_index, samples);
        for (i = 0; i < TV_TRANSITION_SAMPLE_COUNT; ++i) {
            samples_alt13[i] = samples[i];
        }
        samples[13] = 12345.0f;
        samples_alt13[13] = -12345.0f;
        copy_m4_samples(samples, m4_samples);

        default_info = tv_build_transition_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            default_vertices,
            TV_TRANSITION_MAX_VERTICES,
            default_triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        m4_info = tv_m4_build_transition_cell_candidate(
            m4_samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            m4_vertices,
            TV_M4_TRANSITION_MAX_VERTICES,
            m4_triangles,
            TV_M4_TRANSITION_MAX_TRIANGLES);
        default_alt13_info = tv_build_transition_cell(
            samples_alt13,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            default_vertices_alt13,
            TV_TRANSITION_MAX_VERTICES,
            default_triangles_alt13,
            TV_TRANSITION_MAX_TRIANGLES);

        if (default_info.result != TV_OK || m4_info.result != TV_OK) {
            printf(
                "case_build_failed case=%d default_result=%d m4_result=%d\n",
                case_index,
                default_info.result,
                m4_info.result);
            return 1;
        }
        if (!same_build(
                default_info,
                default_vertices,
                default_triangles,
                m4_info,
                m4_vertices,
                m4_triangles)) {
            printf("default_m4_mismatch case=%d\n", case_index);
            return 1;
        }
        ++matches;
        if (!same_build(
                default_info,
                default_vertices,
                default_triangles,
                default_alt13_info,
                default_vertices_alt13,
                default_triangles_alt13)) {
            printf("sample13_changed_default_output case=%d\n", case_index);
            return 1;
        }
        ++sample13_ignored;

        total_vertices += default_info.vertex_count;
        total_triangles += default_info.triangle_count;
        if (default_info.vertex_count > max_vertices) {
            max_vertices = default_info.vertex_count;
        }
        if (default_info.triangle_count > max_triangles) {
            max_triangles = default_info.triangle_count;
        }
    }

    if (total_vertices != EXPECTED_TOTAL_VERTICES
        || total_triangles != EXPECTED_TOTAL_TRIANGLES
        || max_vertices != EXPECTED_MAX_VERTICES
        || max_triangles != EXPECTED_MAX_TRIANGLES) {
        printf(
            "aggregate_mismatch vertices=%d triangles=%d max_vertices=%d max_triangles=%d\n",
            total_vertices,
            total_triangles,
            max_vertices,
            max_triangles);
        return 1;
    }

    {
        float samples[TV_TRANSITION_SAMPLE_COUNT];
        TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
        TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo small_vertices;
        TvBuildInfo small_triangles;
        TvBuildInfo custom_info;
        TvBuildInfo restored_info;

        fill_transition_samples(DEMO_CASE_INDEX, samples);
        small_vertices = tv_build_transition_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_TRANSITION_MAX_VERTICES - 1,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        small_triangles = tv_build_transition_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_TRANSITION_MAX_VERTICES,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES - 1);
        if (small_vertices.result != TV_ERROR_SMALL_VERTEX_BUFFER
            || small_triangles.result != TV_ERROR_SMALL_TRIANGLE_BUFFER) {
            printf(
                "small_buffer_contract_failed vertex_result=%d triangle_result=%d\n",
                small_vertices.result,
                small_triangles.result);
            return 1;
        }

        if (tv_set_transition_backend_callback(custom_backend) != TV_OK
            || !tv_transition_backend_is_custom()) {
            printf("custom_callback_install_failed\n");
            return 1;
        }
        custom_info = tv_build_transition_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_TRANSITION_MAX_VERTICES,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        if (custom_backend_calls != 1
            || custom_info.result != TV_OK
            || custom_info.case_index != 777
            || custom_info.vertex_count != 1) {
            printf(
                "custom_callback_route_failed calls=%d result=%d case=%d vertices=%d\n",
                custom_backend_calls,
                custom_info.result,
                custom_info.case_index,
                custom_info.vertex_count);
            return 1;
        }
        tv_reset_transition_backend_callback();
        if (tv_transition_backend_is_custom()) {
            printf("custom_callback_reset_failed\n");
            return 1;
        }
        restored_info = tv_build_transition_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_TRANSITION_MAX_VERTICES,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        if (restored_info.result != TV_OK
            || restored_info.case_index != DEMO_CASE_INDEX
            || restored_info.vertex_count != EXPECTED_MAX_VERTICES
            || restored_info.triangle_count != EXPECTED_MAX_TRIANGLES) {
            printf(
                "default_restore_failed result=%d case=%d vertices=%d triangles=%d\n",
                restored_info.result,
                restored_info.case_index,
                restored_info.vertex_count,
                restored_info.triangle_count);
            return 1;
        }
    }

    printf(
        "m21 consumer contract cases=%d default_vertices=%d default_triangles=%d max_vertices=%d max_triangles=%d m4_matches=%d sample13_ignored=%d callback_checks=3 failures=0\n",
        EXPECTED_CASE_COUNT,
        total_vertices,
        total_triangles,
        max_vertices,
        max_triangles,
        matches,
        sample13_ignored);
    return 0;
}
