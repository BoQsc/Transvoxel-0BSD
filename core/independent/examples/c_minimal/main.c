/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>
#include "transvoxel.h"

static float field(TvVec3 p) {
    /* Tiny deterministic scalar field for the example. Real engines should
       sample their own density/SDF here. The surface is value == 0. */
    return p.x + p.y + p.z - 1.25f;
}

static void print_first_vertex(const char *label, const TvVec3 *vertices, int count) {
    if (count <= 0) {
        printf("%s first_vertex=none\n", label);
        return;
    }
    printf("%s first_vertex=(%.3f, %.3f, %.3f)\n", label, vertices[0].x, vertices[0].y, vertices[0].z);
}

int main(void) {
    TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo info;
    int i;

    float regular_samples[TV_REGULAR_SAMPLE_COUNT];
    for (i = 0; i < TV_REGULAR_SAMPLE_COUNT; ++i) {
        TvVec3 p = tv_regular_sample_position(i);
        regular_samples[i] = field(p);
    }

    info = tv_build_regular_cell(
        regular_samples,
        0.0f,
        tv_vec3(0.0f, 0.0f, 0.0f),
        tv_vec3(1.0f, 1.0f, 1.0f),
        vertices,
        TV_REGULAR_MAX_VERTICES,
        triangles,
        TV_REGULAR_MAX_TRIANGLES);

    if (info.result != TV_OK) {
        printf("regular failed result=%d\n", info.result);
        return 1;
    }
    printf("regular case=%d vertices=%d triangles=%d\n", info.case_index, info.vertex_count, info.triangle_count);
    print_first_vertex("regular", vertices, info.vertex_count);

    float transition_samples[TV_TRANSITION_SAMPLE_COUNT];
    for (i = 0; i < TV_TRANSITION_SAMPLE_COUNT; ++i) {
        TvVec3 p = tv_transition_sample_position(i);
        transition_samples[i] = field(p);
    }
    tv_transition_fill_derived_samples(transition_samples);

    info = tv_build_transition_cell(
        transition_samples,
        0.0f,
        tv_vec3(0.0f, 0.0f, 0.0f),
        tv_vec3(1.0f, 1.0f, 1.0f),
        vertices,
        TV_TRANSITION_MAX_VERTICES,
        triangles,
        TV_TRANSITION_MAX_TRIANGLES);

    if (info.result != TV_OK) {
        printf("transition failed result=%d\n", info.result);
        return 1;
    }
    printf("transition case=%d vertices=%d triangles=%d\n", info.case_index, info.vertex_count, info.triangle_count);
    print_first_vertex("transition", vertices, info.vertex_count);

    return 0;
}
