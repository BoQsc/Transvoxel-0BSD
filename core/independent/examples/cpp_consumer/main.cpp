// SPDX-License-Identifier: 0BSD
#include <cstdio>

#include "transvoxel.h"

static void fill_transition_samples(
    int case_index,
    float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    for (int i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
}

int main() {
    static_assert(TV_REGULAR_MAX_VERTICES == 12, "regular max vertex contract");
    static_assert(TV_REGULAR_MAX_TRIANGLES == 5, "regular max triangle contract");
    static_assert(TV_TRANSITION_SAMPLE_COUNT == 14, "public transition sample ABI");
    static_assert(TV_TRANSITION_MAX_VERTICES == 12, "M21 transition max vertex contract");
    static_assert(TV_TRANSITION_MAX_TRIANGLES == 12, "M21 transition max triangle contract");

    float samples[TV_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
    fill_transition_samples(341, samples);

    TvBuildInfo info = tv_build_transition_cell(
        samples,
        0.0f,
        tv_vec3(0.0f, 0.0f, 0.0f),
        tv_vec3(1.0f, 1.0f, 1.0f),
        vertices,
        TV_TRANSITION_MAX_VERTICES,
        triangles,
        TV_TRANSITION_MAX_TRIANGLES);
    if (info.result != TV_OK
        || info.case_index != 341
        || info.vertex_count != 12
        || info.triangle_count != 12) {
        std::printf(
            "cpp consumer failed result=%d case=%d vertices=%d triangles=%d\n",
            info.result,
            info.case_index,
            info.vertex_count,
            info.triangle_count);
        return 1;
    }

    std::printf(
        "cpp consumer transition case=%d vertices=%d triangles=%d\n",
        info.case_index,
        info.vertex_count,
        info.triangle_count);
    return 0;
}
