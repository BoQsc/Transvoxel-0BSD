/* SPDX-License-Identifier: 0BSD */
#include <stdint.h>
#include <stdio.h>
#include "transvoxel.h"
#include "transvoxel_m4_backend.h"
#include "transvoxel_m4_candidate.h"

#define FIELD_COUNT 7
#define SEED_COUNT 4

static TvVec3 vec3(float x, float y, float z) {
    TvVec3 out;
    out.x = x;
    out.y = y;
    out.z = z;
    return out;
}

static TvVec3 sub(TvVec3 a, TvVec3 b) {
    return vec3(a.x - b.x, a.y - b.y, a.z - b.z);
}

static TvVec3 cross(TvVec3 a, TvVec3 b) {
    return vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x);
}

static float dot(TvVec3 a, TvVec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static float density(TvVec3 p, int field_id, int seed) {
    float x = p.x;
    float y = p.y;
    float z = p.z;
    float epsilon = 0.037f * (float)(seed + 1) + 0.013f;
    switch (field_id) {
        case 0:
            return x + y + z - (0.75f + 0.25f * (float)(seed % 5)) + epsilon;
        case 1: {
            float dx = x - 0.7f;
            float dy = y - 0.9f;
            float dz = z - 1.1f;
            float radius = 0.8f + 0.1f * (float)(seed % 4);
            return dx * dx + dy * dy + dz * dz - radius * radius + epsilon;
        }
        case 2:
            return x * y + y * z + z * x - 0.2f * (float)(seed - 3) + epsilon;
        case 3:
            return x * x + 0.5f * y - 0.75f * z
                - (0.6f + 0.15f * (float)seed) + epsilon;
        case 4:
            return (x - 0.8f) * (y - 1.1f)
                - (z - 0.6f) * (0.5f + 0.1f * (float)seed) + epsilon;
        case 5:
            return x * x + y * y - z * z
                - (0.5f + 0.2f * (float)seed) + epsilon;
        default:
            return x + 2.0f * y - 1.5f * z
                + 0.2f * x * y - 0.1f * y * z + epsilon;
    }
}

static void fill_normal_samples_from_case(
    int case_index,
    float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
}

static int triangles_are_valid(
    const TvVec3 *vertices,
    const TvTriangle *triangles,
    int vertex_count,
    int triangle_count) {
    int i;
    for (i = 0; i < triangle_count; ++i) {
        TvTriangle triangle = triangles[i];
        TvVec3 normal;
        if (triangle.a >= (uint32_t)vertex_count
            || triangle.b >= (uint32_t)vertex_count
            || triangle.c >= (uint32_t)vertex_count
            || triangle.a == triangle.b
            || triangle.b == triangle.c
            || triangle.c == triangle.a) {
            return 0;
        }
        normal = cross(
            sub(vertices[triangle.b], vertices[triangle.a]),
            sub(vertices[triangle.c], vertices[triangle.a]));
        if (dot(normal, normal) <= 0.0000001f) return 0;
    }
    return 1;
}

static void make_corner_frames(
    int sign_x,
    int sign_y,
    int sign_z,
    TvM4TransitionFrame frames[3]) {
    frames[0].origin = vec3(0.0f, 0.0f, 0.0f);
    frames[0].axis_u = vec3(0.0f, (float)sign_y, 0.0f);
    frames[0].axis_v = vec3(0.0f, 0.0f, (float)sign_z);
    frames[0].axis_w = vec3(0.5f * (float)sign_x, 0.0f, 0.0f);
    frames[1].origin = vec3(0.0f, 0.0f, 0.0f);
    frames[1].axis_u = vec3(0.0f, 0.0f, (float)sign_z);
    frames[1].axis_v = vec3((float)sign_x, 0.0f, 0.0f);
    frames[1].axis_w = vec3(0.0f, 0.5f * (float)sign_y, 0.0f);
    frames[2].origin = vec3(0.0f, 0.0f, 0.0f);
    frames[2].axis_u = vec3((float)sign_x, 0.0f, 0.0f);
    frames[2].axis_v = vec3(0.0f, (float)sign_y, 0.0f);
    frames[2].axis_w = vec3(0.0f, 0.0f, 0.5f * (float)sign_z);
}

static int run_normal_api(
    int *vertex_total,
    int *triangle_total) {
    int case_index;
    for (case_index = 0; case_index < 512; ++case_index) {
        float samples[TV_TRANSITION_SAMPLE_COUNT];
        TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
        TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo info;
        fill_normal_samples_from_case(case_index, samples);
        info = tv_build_transition_cell(
            samples,
            0.0f,
            vec3(0.0f, 0.0f, 0.0f),
            vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_TRANSITION_MAX_VERTICES,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        if (info.result != TV_OK
            || info.case_index != case_index
            || !triangles_are_valid(
                vertices,
                triangles,
                info.vertex_count,
                info.triangle_count)) {
            return 1;
        }
        *vertex_total += info.vertex_count;
        *triangle_total += info.triangle_count;
    }
    return 0;
}

static int run_mapped_corner_cells(
    int *builds,
    int *vertex_total,
    int *triangle_total) {
    int sign_x;
    int sign_y;
    int sign_z;
    int field_id;
    int seed;
    for (sign_x = -1; sign_x <= 1; sign_x += 2) {
        for (sign_y = -1; sign_y <= 1; sign_y += 2) {
            for (sign_z = -1; sign_z <= 1; sign_z += 2) {
                TvM4TransitionFrame frames[3];
                make_corner_frames(sign_x, sign_y, sign_z, frames);
                for (field_id = 0; field_id < FIELD_COUNT; ++field_id) {
                    for (seed = 0; seed < SEED_COUNT; ++seed) {
                        int face;
                        for (face = 0; face < 3; ++face) {
                            TvVec3 sample_positions[TV_M4_TRANSITION_SAMPLE_COUNT];
                            float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT];
                            TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
                            TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
                            TvBuildInfo info;
                            int i;
                            if (tv_m4_transition_frame_sample_positions(
                                    &frames[face],
                                    TV_M4_BOUNDARY_U_MIN | TV_M4_BOUNDARY_V_MIN,
                                    0.5f,
                                    0.5f,
                                    sample_positions) != TV_OK) {
                                return 1;
                            }
                            for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
                                sample_values[i] = density(
                                    sample_positions[i],
                                    field_id,
                                    seed);
                            }
                            tv_m4_transition_fill_derived_samples(sample_values);
                            info = tv_m4_build_transition_cell_candidate_mapped(
                                sample_values,
                                sample_positions,
                                0.0f,
                                vertices,
                                TV_M4_TRANSITION_MAX_VERTICES,
                                triangles,
                                TV_M4_TRANSITION_MAX_TRIANGLES);
                            if (info.result != TV_OK
                                || !triangles_are_valid(
                                    vertices,
                                    triangles,
                                    info.vertex_count,
                                    info.triangle_count)) {
                                return 1;
                            }
                            ++(*builds);
                            *vertex_total += info.vertex_count;
                            *triangle_total += info.triangle_count;
                        }
                    }
                }
            }
        }
    }
    return 0;
}

int main(void) {
    int normal_vertices = 0;
    int normal_triangles = 0;
    int mapped_builds = 0;
    int mapped_vertices = 0;
    int mapped_triangles = 0;
    int restored = 0;
    float restored_samples[TV_TRANSITION_SAMPLE_COUNT];
    TvVec3 restored_vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle restored_triangles[TV_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo default_before;
    TvBuildInfo default_after;

    if (tv_transition_backend_is_custom()) return 1;
    fill_normal_samples_from_case(341, restored_samples);
    default_before = tv_build_transition_cell(
        restored_samples,
        0.0f,
        vec3(0.0f, 0.0f, 0.0f),
        vec3(1.0f, 1.0f, 1.0f),
        restored_vertices,
        TV_TRANSITION_MAX_VERTICES,
        restored_triangles,
        TV_TRANSITION_MAX_TRIANGLES);
    if (default_before.result != TV_OK) return 1;

    if (tv_install_m4_transition_backend_candidate() != TV_OK
        || !tv_m4_transition_backend_candidate_is_installed()) {
        return 1;
    }
    if (run_normal_api(&normal_vertices, &normal_triangles) != 0) return 1;
    if (run_mapped_corner_cells(
            &mapped_builds,
            &mapped_vertices,
            &mapped_triangles) != 0) {
        return 1;
    }
    tv_uninstall_m4_transition_backend_candidate();
    default_after = tv_build_transition_cell(
        restored_samples,
        0.0f,
        vec3(0.0f, 0.0f, 0.0f),
        vec3(1.0f, 1.0f, 1.0f),
        restored_vertices,
        TV_TRANSITION_MAX_VERTICES,
        restored_triangles,
        TV_TRANSITION_MAX_TRIANGLES);
    restored = (
        !tv_transition_backend_is_custom()
        && default_after.result == TV_OK
        && default_after.vertex_count == default_before.vertex_count
        && default_after.triangle_count == default_before.triangle_count);

    printf(
        "m17 production normal_cases=512 normal_vertices=%d normal_triangles=%d mapped_builds=%d mapped_vertices=%d mapped_triangles=%d backend_installed=1 restored_default=%d failures=0\n",
        normal_vertices,
        normal_triangles,
        mapped_builds,
        mapped_vertices,
        mapped_triangles,
        restored);
    return (
        normal_vertices == 4096
        && normal_triangles == 2640
        && mapped_builds == 672
        && mapped_vertices > 0
        && mapped_triangles > 0
        && restored
    ) ? 0 : 1;
}
