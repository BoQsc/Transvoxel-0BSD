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

TvBuildInfo tv_m4_build_transition_cell_candidate(
    const float sample_values[TV_M4_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);

#ifdef __cplusplus
}
#endif

#endif /* BOQSC_TRANSVOXEL_M4_CANDIDATE_H */
