/* SPDX-License-Identifier: 0BSD */
#include "transvoxel_m4_candidate.h"

static const TvVec3 tv_m4_transition_positions[TV_M4_TRANSITION_SAMPLE_COUNT] = {
    {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {2.0f, 0.0f, 0.0f},
    {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 0.0f}, {2.0f, 1.0f, 0.0f},
    {0.0f, 2.0f, 0.0f}, {1.0f, 2.0f, 0.0f}, {2.0f, 2.0f, 0.0f},
    {0.0f, 0.0f, 1.0f}, {2.0f, 0.0f, 1.0f},
    {0.0f, 2.0f, 1.0f}, {2.0f, 2.0f, 1.0f}
};

static const unsigned short tv_m4_reference_case_bits[
    TV_TRANSITION_HIGH_SAMPLE_COUNT
] = {
    0x001u, 0x002u, 0x004u,
    0x080u, 0x100u, 0x008u,
    0x040u, 0x020u, 0x010u
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

static TvVec3 tv_m4_sub(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x - b.x;
    out.y = a.y - b.y;
    out.z = a.z - b.z;
    return out;
}

static TvVec3 tv_m4_mul(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x * b.x;
    out.y = a.y * b.y;
    out.z = a.z * b.z;
    return out;
}

static TvVec3 tv_m4_scale(TvVec3 a, float scale) {
    TvVec3 out;
    out.x = a.x * scale;
    out.y = a.y * scale;
    out.z = a.z * scale;
    return out;
}

static TvVec3 tv_m4_cross(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.y * b.z - a.z * b.y;
    out.y = a.z * b.x - a.x * b.z;
    out.z = a.x * b.y - a.y * b.x;
    return out;
}

static float tv_m4_dot(TvVec3 a, TvVec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
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

int tv_m4_transition_reference_case_index(
    const float samples[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level) {
    int index = 0;
    int i;
    if (!samples) return 0;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        if (samples[i] < iso_level) {
            index |= (int)tv_m4_reference_case_bits[i];
        }
    }
    return index;
}

int tv_m4_transition_reference_case_from_local(int local_case_index) {
    int reference_case_index = 0;
    int i;
    if (local_case_index < 0 || local_case_index > 0x1FF) {
        return TV_ERROR_BAD_CASE;
    }
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        if (local_case_index & (1 << i)) {
            reference_case_index |= (int)tv_m4_reference_case_bits[i];
        }
    }
    return reference_case_index;
}

int tv_m4_transition_local_case_from_reference(int reference_case_index) {
    int local_case_index = 0;
    int i;
    if (reference_case_index < 0 || reference_case_index > 0x1FF) {
        return TV_ERROR_BAD_CASE;
    }
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        if (reference_case_index & (int)tv_m4_reference_case_bits[i]) {
            local_case_index |= (1 << i);
        }
    }
    return local_case_index;
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

int tv_m4_transition_face_frame(
    TvM4TransitionFace face,
    TvVec3 origin,
    TvVec3 local_scale,
    TvM4TransitionFrame *out_frame) {
    TvVec3 unit_u;
    TvVec3 unit_v;
    TvVec3 unit_w;

    if (!out_frame) return TV_ERROR_NULL;

    switch (face) {
        case TV_M4_FACE_POSITIVE_X:
            unit_u = tv_m4_vec3(0.0f, 1.0f, 0.0f);
            unit_v = tv_m4_vec3(0.0f, 0.0f, 1.0f);
            unit_w = tv_m4_vec3(1.0f, 0.0f, 0.0f);
            break;
        case TV_M4_FACE_NEGATIVE_X:
            unit_u = tv_m4_vec3(0.0f, -1.0f, 0.0f);
            unit_v = tv_m4_vec3(0.0f, 0.0f, 1.0f);
            unit_w = tv_m4_vec3(-1.0f, 0.0f, 0.0f);
            break;
        case TV_M4_FACE_POSITIVE_Y:
            unit_u = tv_m4_vec3(0.0f, 0.0f, 1.0f);
            unit_v = tv_m4_vec3(1.0f, 0.0f, 0.0f);
            unit_w = tv_m4_vec3(0.0f, 1.0f, 0.0f);
            break;
        case TV_M4_FACE_NEGATIVE_Y:
            unit_u = tv_m4_vec3(0.0f, 0.0f, -1.0f);
            unit_v = tv_m4_vec3(1.0f, 0.0f, 0.0f);
            unit_w = tv_m4_vec3(0.0f, -1.0f, 0.0f);
            break;
        case TV_M4_FACE_POSITIVE_Z:
            unit_u = tv_m4_vec3(1.0f, 0.0f, 0.0f);
            unit_v = tv_m4_vec3(0.0f, 1.0f, 0.0f);
            unit_w = tv_m4_vec3(0.0f, 0.0f, 1.0f);
            break;
        case TV_M4_FACE_NEGATIVE_Z:
            unit_u = tv_m4_vec3(-1.0f, 0.0f, 0.0f);
            unit_v = tv_m4_vec3(0.0f, 1.0f, 0.0f);
            unit_w = tv_m4_vec3(0.0f, 0.0f, -1.0f);
            break;
        default:
            return TV_ERROR_BAD_CASE;
    }

    out_frame->origin = origin;
    out_frame->axis_u = tv_m4_scale(unit_u, local_scale.x);
    out_frame->axis_v = tv_m4_scale(unit_v, local_scale.y);
    out_frame->axis_w = tv_m4_scale(unit_w, local_scale.z);
    return TV_OK;
}

TvVec3 tv_m4_transition_frame_position(
    const TvM4TransitionFrame *frame,
    TvVec3 local_position) {
    TvVec3 out;
    if (!frame) return tv_m4_vec3(0.0f, 0.0f, 0.0f);
    out = frame->origin;
    out = tv_m4_add(out, tv_m4_scale(frame->axis_u, local_position.x));
    out = tv_m4_add(out, tv_m4_scale(frame->axis_v, local_position.y));
    out = tv_m4_add(out, tv_m4_scale(frame->axis_w, local_position.z));
    return out;
}

int tv_m4_transition_frame_sample_positions(
    const TvM4TransitionFrame *frame,
    unsigned int boundary_mask,
    float half_face_inset_u,
    float half_face_inset_v,
    TvVec3 out_positions[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int sample_id;
    if (!frame || !out_positions) return TV_ERROR_NULL;
    for (sample_id = 0; sample_id < TV_M4_TRANSITION_SAMPLE_COUNT; ++sample_id) {
        TvVec3 local = tv_m4_transition_positions[sample_id];
        if (sample_id >= 9) {
            if (local.x == 0.0f && (boundary_mask & TV_M4_BOUNDARY_U_MIN)) {
                local.x += half_face_inset_u;
            }
            if (local.x == 2.0f && (boundary_mask & TV_M4_BOUNDARY_U_MAX)) {
                local.x -= half_face_inset_u;
            }
            if (local.y == 0.0f && (boundary_mask & TV_M4_BOUNDARY_V_MIN)) {
                local.y += half_face_inset_v;
            }
            if (local.y == 2.0f && (boundary_mask & TV_M4_BOUNDARY_V_MAX)) {
                local.y -= half_face_inset_v;
            }
        }
        out_positions[sample_id] = tv_m4_transition_frame_position(frame, local);
    }
    return TV_OK;
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

TvBuildInfo tv_m4_build_transition_cell_candidate_mapped(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    const TvVec3 sample_positions[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles) {
    int case_index;
    int vertex_start;
    int vertex_count;
    int triangle_start;
    int triangle_count;
    float determinant;
    int i;

    if (!sample_values || !sample_positions || !out_vertices || !out_triangles) {
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
        out_vertices[i] = tv_m4_interp_position(
            sample_positions[a],
            sample_positions[b],
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

    determinant = tv_m4_dot(
        tv_m4_cross(
            tv_m4_sub(sample_positions[2], sample_positions[0]),
            tv_m4_sub(sample_positions[6], sample_positions[0])),
        tv_m4_sub(sample_positions[9], sample_positions[0]));
    if (determinant < 0.0f) {
        for (i = 0; i < triangle_count; ++i) {
            uint32_t tmp = out_triangles[i].b;
            out_triangles[i].b = out_triangles[i].c;
            out_triangles[i].c = tmp;
        }
    }
    return tv_m4_make_info(
        TV_OK,
        case_index,
        vertex_count,
        triangle_count);
}

TvBuildInfo tv_m4_build_transition_cell_candidate_oriented(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvM4TransitionFace face,
    TvVec3 origin,
    TvVec3 local_scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles) {
    TvM4TransitionFrame frame;
    TvBuildInfo info;
    float determinant;
    int i;
    int frame_result = tv_m4_transition_face_frame(
        face,
        origin,
        local_scale,
        &frame);

    if (frame_result != TV_OK) {
        return tv_m4_make_info(frame_result, 0, 0, 0);
    }

    info = tv_m4_build_transition_cell_candidate(
        sample_values,
        iso_level,
        tv_m4_vec3(0.0f, 0.0f, 0.0f),
        tv_m4_vec3(1.0f, 1.0f, 1.0f),
        out_vertices,
        max_vertices,
        out_triangles,
        max_triangles);
    if (info.result != TV_OK) return info;

    for (i = 0; i < info.vertex_count; ++i) {
        out_vertices[i] = tv_m4_transition_frame_position(&frame, out_vertices[i]);
    }

    determinant = tv_m4_dot(
        tv_m4_cross(frame.axis_u, frame.axis_v),
        frame.axis_w);
    if (determinant < 0.0f) {
        for (i = 0; i < info.triangle_count; ++i) {
            uint32_t tmp = out_triangles[i].b;
            out_triangles[i].b = out_triangles[i].c;
            out_triangles[i].c = tmp;
        }
    }

    return info;
}
