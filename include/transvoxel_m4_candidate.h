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

#define TV_M4_BOUNDARY_U_MIN 0x01u
#define TV_M4_BOUNDARY_U_MAX 0x02u
#define TV_M4_BOUNDARY_V_MIN 0x04u
#define TV_M4_BOUNDARY_V_MAX 0x08u

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
 * from that face toward the four half-resolution samples. Thus +w points
 * into the low-resolution block and -w points toward the high-resolution
 * neighbor. TvM4TransitionFace names the world direction of local +w, not the
 * outward face normal of the low-resolution block. The frame axes include the
 * caller-provided local u/v/w scale.
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

/* M4 stores its clean-room runtime table in row-major sample-bit order:
 * sample ids 0..8 map to bits 0..8. The published dissertation convention
 * uses the same sample coordinates but the bit weights from Figure 4.17:
 * 01,02,04,80,100,08,40,20,10. These helpers provide an exact bijection
 * without changing the stable runtime-table index.
 */
int tv_m4_transition_reference_case_index(
    const float samples[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level);

/* The integer conversion helpers return TV_ERROR_BAD_CASE outside 0..511. */
int tv_m4_transition_reference_case_from_local(int local_case_index);

int tv_m4_transition_local_case_from_reference(int reference_case_index);

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

int tv_m4_transition_frame_sample_positions(
    const TvM4TransitionFrame *frame,
    unsigned int boundary_mask,
    float half_face_inset_u,
    float half_face_inset_v,
    TvVec3 out_positions[TV_M4_TRANSITION_SAMPLE_COUNT]);

TvBuildInfo tv_m4_build_transition_cell_candidate(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);

/* Builds from caller-provided positions for all 13 M4 samples. Winding is
 * corrected from the handedness of full-face axes 0->2, 0->6 and the inward
 * direction 0->9. This supports non-box transition cells at block edges and
 * corners while preserving the same clean-room topology table.
 */
TvBuildInfo tv_m4_build_transition_cell_candidate_mapped(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    const TvVec3 sample_positions[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
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
