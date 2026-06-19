/* SPDX-License-Identifier: 0BSD */
#include <math.h>
#include <stdio.h>

#include "transvoxel.h"
#include "transvoxel_tables.h"

static int nearf(float a, float b) {
    return fabsf(a - b) <= 0.00001f;
}

static void fill_case(int case_index, float samples[TV_REGULAR_SAMPLE_COUNT]) {
    int sample_id;
    for (sample_id = 0; sample_id < TV_REGULAR_SAMPLE_COUNT; ++sample_id) {
        samples[sample_id] = (case_index & (1 << sample_id))
            ? -1.0f
            : 1.0f;
    }
}

int main(void) {
    int case_index;
    int failures = 0;
    int total_vertices = 0;
    int total_triangles = 0;
    int max_vertices = 0;
    int max_triangles = 0;
    int small_buffer_checks = 0;

    for (case_index = 0; case_index < 256; ++case_index) {
        float samples[TV_REGULAR_SAMPLE_COUNT];
        TvVec3 vertices[TV_REGULAR_MAX_VERTICES];
        TvTriangle triangles[TV_REGULAR_MAX_TRIANGLES];
        TvBuildInfo info;
        uint16_t class_index;
        TVCClassData class_data;
        int i;

        fill_case(case_index, samples);
        info = tv_build_regular_cell(
            samples,
            0.0f,
            tv_vec3(0.0f, 0.0f, 0.0f),
            tv_vec3(1.0f, 1.0f, 1.0f),
            vertices,
            TV_REGULAR_MAX_VERTICES,
            triangles,
            TV_REGULAR_MAX_TRIANGLES
        );
        class_index = tvc_regular_case_class[case_index];
        class_data = tvc_regular_class_data[class_index];
        if (
            info.result != TV_OK
            || info.case_index != case_index
            || info.vertex_count != (int)class_data.vertex_count
            || info.triangle_count != (int)class_data.triangle_count
        ) {
            failures += 1;
            continue;
        }
        for (i = 0; i < info.vertex_count; ++i) {
            TVCVertexRef ref = tvc_regular_vertex_refs[
                class_data.vertex_offset + i
            ];
            TvVec3 a = tv_regular_sample_position((int)ref.sample_a);
            TvVec3 b = tv_regular_sample_position((int)ref.sample_b);
            if (
                (samples[ref.sample_a] < 0.0f)
                == (samples[ref.sample_b] < 0.0f)
                || !nearf(vertices[i].x, (a.x + b.x) * 0.5f)
                || !nearf(vertices[i].y, (a.y + b.y) * 0.5f)
                || !nearf(vertices[i].z, (a.z + b.z) * 0.5f)
            ) {
                failures += 1;
            }
        }
        for (i = 0; i < info.triangle_count; ++i) {
            TvTriangle triangle = triangles[i];
            if (
                triangle.a >= (uint32_t)info.vertex_count
                || triangle.b >= (uint32_t)info.vertex_count
                || triangle.c >= (uint32_t)info.vertex_count
                || triangle.a == triangle.b
                || triangle.b == triangle.c
                || triangle.c == triangle.a
            ) {
                failures += 1;
            }
        }
        if (info.vertex_count > 0) {
            TvBuildInfo small = tv_build_regular_cell(
                samples,
                0.0f,
                tv_vec3(0.0f, 0.0f, 0.0f),
                tv_vec3(1.0f, 1.0f, 1.0f),
                vertices,
                info.vertex_count - 1,
                triangles,
                TV_REGULAR_MAX_TRIANGLES
            );
            if (small.result != TV_ERROR_SMALL_VERTEX_BUFFER) {
                failures += 1;
            }
            small_buffer_checks += 1;
        }
        if (info.triangle_count > 0) {
            TvBuildInfo small = tv_build_regular_cell(
                samples,
                0.0f,
                tv_vec3(0.0f, 0.0f, 0.0f),
                tv_vec3(1.0f, 1.0f, 1.0f),
                vertices,
                TV_REGULAR_MAX_VERTICES,
                triangles,
                info.triangle_count - 1
            );
            if (small.result != TV_ERROR_SMALL_TRIANGLE_BUFFER) {
                failures += 1;
            }
            small_buffer_checks += 1;
        }
        total_vertices += info.vertex_count;
        total_triangles += info.triangle_count;
        if (info.vertex_count > max_vertices) max_vertices = info.vertex_count;
        if (info.triangle_count > max_triangles) {
            max_triangles = info.triangle_count;
        }
    }

    printf(
        "m20 regular cases=256 vertices=%d triangles=%d max_vertices=%d "
        "max_triangles=%d small_buffer_checks=%d failures=%d\n",
        total_vertices,
        total_triangles,
        max_vertices,
        max_triangles,
        small_buffer_checks,
        failures
    );
    return failures == 0 ? 0 : 1;
}
