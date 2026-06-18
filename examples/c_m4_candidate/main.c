/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>
#include "transvoxel_m4_candidate.h"

static float absf_local(float v) {
    return v < 0.0f ? -v : v;
}

static int almost_equal(float a, float b) {
    return absf_local(a - b) <= 0.00001f;
}

static int vec_equal(TvVec3 a, TvVec3 b) {
    return almost_equal(a.x, b.x)
        && almost_equal(a.y, b.y)
        && almost_equal(a.z, b.z);
}

static TvVec3 interp_expected(TvVec3 a, TvVec3 b, float va, float vb, float iso) {
    float da = va - iso;
    float db = vb - iso;
    float denom = absf_local(da) + absf_local(db);
    float t = 0.5f;
    TvVec3 out;
    if (denom > 0.000001f) {
        t = absf_local(da) / denom;
    }
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    out.x = a.x + (b.x - a.x) * t;
    out.y = a.y + (b.y - a.y) * t;
    out.z = a.z + (b.z - a.z) * t;
    return out;
}

static void fill_case_samples(int case_index, float samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = ((case_index & (1 << i)) != 0) ? -1.0f : 1.0f;
    }
    tv_m4_transition_fill_derived_samples(samples);
}

static int validate_case(int case_index, int *vertex_total, int *triangle_total) {
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo info;
    int vertex_start;
    int triangle_start;
    int expected_vertices;
    int expected_triangles;
    int i;

    fill_case_samples(case_index, samples);
    if (tv_m4_transition_case_index(samples, 0.0f) != case_index) {
        printf("case_index_mismatch case=%d\n", case_index);
        return 1;
    }

    info = tv_m4_build_transition_cell_candidate(
        samples,
        0.0f,
        (TvVec3){0.0f, 0.0f, 0.0f},
        (TvVec3){1.0f, 1.0f, 1.0f},
        vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);

    expected_vertices = (int)otc_m4_case_vertex_count[case_index];
    expected_triangles = (int)otc_m4_case_triangle_count[case_index];
    if (info.result != TV_OK
        || info.case_index != case_index
        || info.vertex_count != expected_vertices
        || info.triangle_count != expected_triangles) {
        printf(
            "build_mismatch case=%d result=%d got_v=%d expected_v=%d got_t=%d expected_t=%d\n",
            case_index,
            info.result,
            info.vertex_count,
            expected_vertices,
            info.triangle_count,
            expected_triangles);
        return 1;
    }

    vertex_start = (int)otc_m4_case_vertex_start[case_index];
    for (i = 0; i < expected_vertices; ++i) {
        int pair_id = vertex_start + i;
        int a = (int)otc_m4_vertex_pairs[pair_id][0];
        int b = (int)otc_m4_vertex_pairs[pair_id][1];
        TvVec3 expected;
        if ((samples[a] < 0.0f) == (samples[b] < 0.0f)) {
            printf("non_crossing_vertex_pair case=%d vertex=%d pair=(%d,%d)\n", case_index, i, a, b);
            return 1;
        }
        expected = interp_expected(
            tv_m4_transition_sample_position(a),
            tv_m4_transition_sample_position(b),
            samples[a],
            samples[b],
            0.0f);
        if (!vec_equal(vertices[i], expected)) {
            printf("vertex_position_mismatch case=%d vertex=%d\n", case_index, i);
            return 1;
        }
    }

    triangle_start = (int)otc_m4_case_triangle_start[case_index];
    for (i = 0; i < expected_triangles; ++i) {
        TvTriangle tri = triangles[i];
        int triangle_id = triangle_start + i;
        if (tri.a >= (uint32_t)expected_vertices
            || tri.b >= (uint32_t)expected_vertices
            || tri.c >= (uint32_t)expected_vertices
            || tri.a == tri.b
            || tri.b == tri.c
            || tri.c == tri.a) {
            printf("bad_triangle_indices case=%d triangle=%d\n", case_index, i);
            return 1;
        }
        if (tri.a != otc_m4_triangles[triangle_id][0]
            || tri.b != otc_m4_triangles[triangle_id][1]
            || tri.c != otc_m4_triangles[triangle_id][2]) {
            printf("triangle_table_mismatch case=%d triangle=%d\n", case_index, i);
            return 1;
        }
    }

    *vertex_total += expected_vertices;
    *triangle_total += expected_triangles;
    return 0;
}

static int validate_buffer_errors(void) {
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo info;
    int case_index = 341;

    fill_case_samples(case_index, samples);
    info = tv_m4_build_transition_cell_candidate(
        samples,
        0.0f,
        (TvVec3){0.0f, 0.0f, 0.0f},
        (TvVec3){1.0f, 1.0f, 1.0f},
        vertices,
        TV_M4_TRANSITION_MAX_VERTICES - 1,
        triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    if (info.result != TV_ERROR_SMALL_VERTEX_BUFFER) {
        printf("small_vertex_buffer_check_failed result=%d\n", info.result);
        return 1;
    }

    info = tv_m4_build_transition_cell_candidate(
        samples,
        0.0f,
        (TvVec3){0.0f, 0.0f, 0.0f},
        (TvVec3){1.0f, 1.0f, 1.0f},
        vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES - 1);
    if (info.result != TV_ERROR_SMALL_TRIANGLE_BUFFER) {
        printf("small_triangle_buffer_check_failed result=%d\n", info.result);
        return 1;
    }

    return 0;
}

int main(void) {
    int case_index;
    int vertex_total = 0;
    int triangle_total = 0;

    if (TV_M4_TRANSITION_SAMPLE_COUNT != 13) {
        printf("sample_count_mismatch\n");
        return 1;
    }
    if (TV_M4_TRANSITION_MAX_VERTICES != (int)OTC_M4_MAX_VERTICES_PER_CASE) {
        printf("max_vertex_macro_mismatch\n");
        return 1;
    }
    if (TV_M4_TRANSITION_MAX_TRIANGLES != (int)OTC_M4_MAX_TRIANGLES_PER_CASE) {
        printf("max_triangle_macro_mismatch\n");
        return 1;
    }

    for (case_index = 0; case_index < (int)OTC_M4_CASE_COUNT; ++case_index) {
        if (validate_case(case_index, &vertex_total, &triangle_total) != 0) {
            return 1;
        }
    }
    if (validate_buffer_errors() != 0) {
        return 1;
    }

    if (vertex_total != (int)OTC_M4_VERTEX_PAIR_COUNT) {
        printf("vertex_total_mismatch total=%d expected=%u\n", vertex_total, OTC_M4_VERTEX_PAIR_COUNT);
        return 1;
    }
    if (triangle_total != (int)OTC_M4_TRIANGLE_COUNT) {
        printf("triangle_total_mismatch total=%d expected=%u\n", triangle_total, OTC_M4_TRIANGLE_COUNT);
        return 1;
    }

    printf(
        "m4 candidate exhaustive cases=%u vertices=%u triangles=%u max_vertices=%u max_triangles=%u\n",
        OTC_M4_CASE_COUNT,
        OTC_M4_VERTEX_PAIR_COUNT,
        OTC_M4_TRIANGLE_COUNT,
        OTC_M4_MAX_VERTICES_PER_CASE,
        OTC_M4_MAX_TRIANGLES_PER_CASE);
    return 0;
}
