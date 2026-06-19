/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>

#include "transvoxel_m4_candidate.h"

static const int reference_case_bits[9] = {
    0x001, 0x002, 0x004,
    0x080, 0x100, 0x008,
    0x040, 0x020, 0x010
};

static void fill_samples_from_local_case(
    int local_case,
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int sample_id;
    for (sample_id = 0; sample_id < 9; ++sample_id) {
        samples[sample_id] = (local_case & (1 << sample_id))
            ? -1.0f
            : 1.0f;
    }
    tv_m4_transition_fill_derived_samples(samples);
}

static int expected_reference_case(int local_case) {
    int sample_id;
    int result = 0;
    for (sample_id = 0; sample_id < 9; ++sample_id) {
        if (local_case & (1 << sample_id)) {
            result |= reference_case_bits[sample_id];
        }
    }
    return result;
}

static int rotate_180_local(int local_case) {
    int sample_id;
    int result = 0;
    for (sample_id = 0; sample_id < 9; ++sample_id) {
        if (local_case & (1 << sample_id)) {
            result |= 1 << (8 - sample_id);
        }
    }
    return result;
}

static float determinant(TvM4TransitionFrame frame) {
    float cx = frame.axis_u.y * frame.axis_v.z
        - frame.axis_u.z * frame.axis_v.y;
    float cy = frame.axis_u.z * frame.axis_v.x
        - frame.axis_u.x * frame.axis_v.z;
    float cz = frame.axis_u.x * frame.axis_v.y
        - frame.axis_u.y * frame.axis_v.x;
    return cx * frame.axis_w.x + cy * frame.axis_w.y + cz * frame.axis_w.z;
}

int main(void) {
    int local_case;
    int failures = 0;
    int mapping_checks = 0;
    int roundtrip_checks = 0;
    int complement_checks = 0;
    int rotation_checks = 0;
    int build_checks = 0;
    int frame_checks = 0;
    int total_vertices = 0;
    int total_triangles = 0;
    unsigned char seen_reference[512] = {0};

    if (
        tv_m4_transition_reference_case_from_local(-1) != TV_ERROR_BAD_CASE
        || tv_m4_transition_reference_case_from_local(512) != TV_ERROR_BAD_CASE
        || tv_m4_transition_local_case_from_reference(-1) != TV_ERROR_BAD_CASE
        || tv_m4_transition_local_case_from_reference(512) != TV_ERROR_BAD_CASE
    ) {
        failures += 1;
    }

    for (local_case = 0; local_case < 512; ++local_case) {
        float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
        TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
        TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
        int expected_reference = expected_reference_case(local_case);
        int actual_reference;
        int rotated_reference;
        int expected_rotated_reference;
        TvBuildInfo info;

        fill_samples_from_local_case(local_case, samples);
        actual_reference = tv_m4_transition_reference_case_index(samples, 0.0f);
        if (
            tv_m4_transition_case_index(samples, 0.0f) != local_case
            || actual_reference != expected_reference
            || tv_m4_transition_reference_case_from_local(local_case)
                != expected_reference
        ) {
            failures += 1;
        }
        mapping_checks += 1;

        if (
            tv_m4_transition_local_case_from_reference(expected_reference)
            != local_case
        ) {
            failures += 1;
        }
        roundtrip_checks += 2;
        seen_reference[expected_reference] = 1;

        if (
            tv_m4_transition_reference_case_from_local(local_case ^ 0x1FF)
            != (expected_reference ^ 0x1FF)
        ) {
            failures += 1;
        }
        complement_checks += 1;

        rotated_reference = tv_m4_transition_reference_case_from_local(
            rotate_180_local(local_case)
        );
        expected_rotated_reference =
            ((expected_reference & 0x00F) << 4)
            | ((expected_reference & 0x0F0) >> 4)
            | (expected_reference & 0x100);
        if (rotated_reference != expected_rotated_reference) {
            failures += 1;
        }
        rotation_checks += 1;

        info = tv_m4_build_transition_cell_candidate(
            samples,
            0.0f,
            (TvVec3){0.0f, 0.0f, 0.0f},
            (TvVec3){1.0f, 1.0f, 1.0f},
            vertices,
            TV_M4_TRANSITION_MAX_VERTICES,
            triangles,
            TV_M4_TRANSITION_MAX_TRIANGLES
        );
        if (info.result != TV_OK || info.case_index != local_case) {
            failures += 1;
        }
        total_vertices += info.vertex_count;
        total_triangles += info.triangle_count;
        build_checks += 1;
    }

    for (local_case = 0; local_case < 512; ++local_case) {
        if (!seen_reference[local_case]) {
            failures += 1;
        }
    }

    for (local_case = 0; local_case < TV_M4_FACE_COUNT; ++local_case) {
        TvM4TransitionFrame frame;
        int result = tv_m4_transition_face_frame(
            (TvM4TransitionFace)local_case,
            (TvVec3){0.0f, 0.0f, 0.0f},
            (TvVec3){1.0f, 1.0f, 1.0f},
            &frame
        );
        if (result != TV_OK || determinant(frame) <= 0.0f) {
            failures += 1;
        }
        frame_checks += 1;
    }

    printf(
        "m18 reference cases=%d mapping_checks=%d roundtrip_checks=%d "
        "complement_checks=%d rotation_checks=%d build_checks=%d "
        "frame_checks=%d vertices=%d triangles=%d failures=%d\n",
        512,
        mapping_checks,
        roundtrip_checks,
        complement_checks,
        rotation_checks,
        build_checks,
        frame_checks,
        total_vertices,
        total_triangles,
        failures
    );
    return failures == 0 ? 0 : 1;
}
