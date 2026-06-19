/* SPDX-License-Identifier: 0BSD
 * Opt-in M4 runtime candidate API.
 *
 * This path consumes generated/official_topology_candidate_tables.h. It is not
 * the default core backend and does not claim official Transvoxel.cpp table
 * identity or official topology equivalence.
 */
#ifndef BOQSC_TRANSVOXEL_M4_CANDIDATE_H
#define BOQSC_TRANSVOXEL_M4_CANDIDATE_H

#include "transvoxel.h"
#include "official_topology_candidate_tables.h"

#ifdef __cplusplus
extern "C" {
#endif

#define TV_M4_TRANSITION_SAMPLE_COUNT ((int)OTC_M4_SAMPLE_COUNT)
#define TV_M4_TRANSITION_MAX_VERTICES ((int)OTC_M4_MAX_VERTICES_PER_CASE)
#define TV_M4_TRANSITION_MAX_TRIANGLES ((int)OTC_M4_MAX_TRIANGLES_PER_CASE)

typedef enum TvM4TransitionFace {
    TV_M4_FACE_POSITIVE_X = 0,
    TV_M4_FACE_NEGATIVE_X = 1,
    TV_M4_FACE_POSITIVE_Y = 2,
    TV_M4_FACE_NEGATIVE_Y = 3,
    TV_M4_FACE_POSITIVE_Z = 4,
    TV_M4_FACE_NEGATIVE_Z = 5,
    TV_M4_FACE_COUNT = 6
} TvM4TransitionFace;

/* The local transition cell uses u/v on the 3x3 full-resolution face and w
 * from that face toward the four half-resolution samples. The frame axes
 * include the caller-provided local u/v/w scale.
 */
typedef struct TvM4TransitionFrame {
    TvVec3 origin;
    TvVec3 axis_u;
    TvVec3 axis_v;
    TvVec3 axis_w;
} TvM4TransitionFrame;

/* M4 uses public transition samples 0..12 only. The older independent core
 * also has synthetic sample 13; this opt-in M4 path intentionally does not use
 * that synthetic center sample.
 */
int tv_m4_transition_case_index(
    const float samples[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level);

void tv_m4_transition_fill_derived_samples(
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT]);

TvVec3 tv_m4_transition_sample_position(int sample_id);

int tv_m4_transition_face_frame(
    TvM4TransitionFace face,
    TvVec3 origin,
    TvVec3 local_scale,
    TvM4TransitionFrame *out_frame);

TvVec3 tv_m4_transition_frame_position(
    const TvM4TransitionFrame *frame,
    TvVec3 local_position);

TvBuildInfo tv_m4_build_transition_cell_candidate(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);

TvBuildInfo tv_m4_build_transition_cell_candidate_oriented(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvM4TransitionFace face,
    TvVec3 origin,
    TvVec3 local_scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);

#ifdef __cplusplus
}
#endif

#endif /* BOQSC_TRANSVOXEL_M4_CANDIDATE_H */
