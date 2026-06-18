/* SPDX-License-Identifier: 0BSD */
#include "transvoxel_m4_candidate.h"

static const TvVec3 tv_m4_transition_positions[TV_M4_TRANSITION_SAMPLE_COUNT] = {
    {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {2.0f, 0.0f, 0.0f},
    {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 0.0f}, {2.0f, 1.0f, 0.0f},
    {0.0f, 2.0f, 0.0f}, {1.0f, 2.0f, 0.0f}, {2.0f, 2.0f, 0.0f},
    {0.0f, 0.0f, 1.0f}, {2.0f, 0.0f, 1.0f},
    {0.0f, 2.0f, 1.0f}, {2.0f, 2.0f, 1.0f}
};

static TvVec3 tv_m4_vec3(float x, float y, float z) {
    TvVec3 v;
    v.x = x;
    v.y = y;
    v.z = z;
    return v;
}

static TvVec3 tv_m4_add(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x + b.x;
    out.y = a.y + b.y;
    out.z = a.z + b.z;
    return out;
}

static TvVec3 tv_m4_mul(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x * b.x;
    out.y = a.y * b.y;
    out.z = a.z * b.z;
    return out;
}

static TvVec3 tv_m4_lerp(TvVec3 a, TvVec3 b, float t) {
    TvVec3 out;
    out.x = a.x + (b.x - a.x) * t;
    out.y = a.y + (b.y - a.y) * t;
    out.z = a.z + (b.z - a.z) * t;
    return out;
}

static float tv_m4_absf(float v) {
    return v < 0.0f ? -v : v;
}

static float tv_m4_clampf(float v, float lo, float hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static TvVec3 tv_m4_world_pos(TvVec3 origin, TvVec3 scale, TvVec3 local) {
    return tv_m4_add(origin, tv_m4_mul(local, scale));
}

static TvVec3 tv_m4_interp_position(
    TvVec3 a,
    TvVec3 b,
    float va,
    float vb,
    float iso_level) {
    float da = va - iso_level;
    float db = vb - iso_level;
    float denom = tv_m4_absf(da) + tv_m4_absf(db);
    float t = 0.5f;
    if (denom > 0.000001f) {
        t = tv_m4_absf(da) / denom;
    }
    return tv_m4_lerp(a, b, tv_m4_clampf(t, 0.0f, 1.0f));
}

static TvBuildInfo tv_m4_make_info(
    int result,
    int case_index,
    int vertex_count,
    int triangle_count) {
    TvBuildInfo info;
    info.result = result;
    info.case_index = case_index;
    info.vertex_count = vertex_count;
    info.triangle_count = triangle_count;
    return info;
}

int tv_m4_transition_case_index(
    const float samples[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level) {
    int index = 0;
    int i;
    if (!samples) return 0;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        if (samples[i] < iso_level) {
            index |= (1 << i);
        }
    }
    return index;
}

void tv_m4_transition_fill_derived_samples(
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    if (!samples) return;
    samples[9] = samples[0];
    samples[10] = samples[2];
    samples[11] = samples[6];
    samples[12] = samples[8];
}

TvVec3 tv_m4_transition_sample_position(int sample_id) {
    if (sample_id < 0 || sample_id >= TV_M4_TRANSITION_SAMPLE_COUNT) {
        return tv_m4_vec3(0.0f, 0.0f, 0.0f);
    }
    return tv_m4_transition_positions[sample_id];
}

TvBuildInfo tv_m4_build_transition_cell_candidate(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles) {

    int case_index;
    int vertex_start;
    int vertex_count;
    int triangle_start;
    int triangle_count;
    int i;

    if (!sample_values || !out_vertices || !out_triangles) {
        return tv_m4_make_info(TV_ERROR_NULL, 0, 0, 0);
    }

    case_index = tv_m4_transition_case_index(sample_values, iso_level);
    if (case_index < 0 || case_index >= (int)OTC_M4_CASE_COUNT) {
        return tv_m4_make_info(TV_ERROR_BAD_CASE, case_index, 0, 0);
    }

    vertex_start = (int)otc_m4_case_vertex_start[case_index];
    vertex_count = (int)otc_m4_case_vertex_count[case_index];
    triangle_start = (int)otc_m4_case_triangle_start[case_index];
    triangle_count = (int)otc_m4_case_triangle_count[case_index];

    if (max_vertices < vertex_count) {
        return tv_m4_make_info(
            TV_ERROR_SMALL_VERTEX_BUFFER,
            case_index,
            vertex_count,
            triangle_count);
    }
    if (max_triangles < triangle_count) {
        return tv_m4_make_info(
            TV_ERROR_SMALL_TRIANGLE_BUFFER,
            case_index,
            vertex_count,
            triangle_count);
    }

    for (i = 0; i < vertex_count; ++i) {
        int pair_id = vertex_start + i;
        int a = (int)otc_m4_vertex_pairs[pair_id][0];
        int b = (int)otc_m4_vertex_pairs[pair_id][1];
        TvVec3 pa = tv_m4_world_pos(origin, scale, tv_m4_transition_positions[a]);
        TvVec3 pb = tv_m4_world_pos(origin, scale, tv_m4_transition_positions[b]);
        out_vertices[i] = tv_m4_interp_position(
            pa,
            pb,
            sample_values[a],
            sample_values[b],
            iso_level);
    }

    for (i = 0; i < triangle_count; ++i) {
        int triangle_id = triangle_start + i;
        out_triangles[i].a = otc_m4_triangles[triangle_id][0];
        out_triangles[i].b = otc_m4_triangles[triangle_id][1];
        out_triangles[i].c = otc_m4_triangles[triangle_id][2];
    }

    return tv_m4_make_info(TV_OK, case_index, vertex_count, triangle_count);
}
