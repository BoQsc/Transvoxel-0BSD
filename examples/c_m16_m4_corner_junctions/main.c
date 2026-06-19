/* SPDX-License-Identifier: 0BSD */
#include <stdint.h>
#include <stdio.h>
#include "transvoxel_m4_candidate.h"

#define FIELD_COUNT 7
#define SEED_COUNT 8
#define MAX_BOUNDARY_EDGES (TV_M4_TRANSITION_MAX_TRIANGLES * 3)
#define SIDE_U_MIN 0
#define SIDE_V_MIN 1

typedef struct QuantizedPoint {
    int x;
    int y;
    int z;
} QuantizedPoint;

typedef struct Segment3i {
    QuantizedPoint a;
    QuantizedPoint b;
    int direction;
} Segment3i;

typedef struct Fingerprint {
    int count;
    Segment3i segments[MAX_BOUNDARY_EDGES];
} Fingerprint;

typedef struct EdgeUse {
    uint32_t key_a;
    uint32_t key_b;
    uint32_t directed_a;
    uint32_t directed_b;
    int count;
} EdgeUse;

typedef struct MappedCell {
    TvVec3 samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    float values[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    unsigned int vertex_side_mask[TV_M4_TRANSITION_MAX_VERTICES];
    TvBuildInfo info;
} MappedCell;

typedef struct Totals {
    int octants;
    int junctions;
    int builds;
    int vertices;
    int triangles;
    int invalid_triangles;
    int degenerate_triangles;
    int internal_winding_failures;
    int shared_faces;
    int nonempty_shared_faces;
    int shared_samples;
    int sample_position_failures;
    int sample_value_failures;
    int lateral_geometry_failures;
    int lateral_winding_failures;
    int corner_position_failures;
    int corner_value_failures;
} Totals;

static const int u_min_samples[5] = {0, 3, 6, 9, 11};
static const int v_min_samples[5] = {0, 1, 2, 9, 10};

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

static float length_squared(TvVec3 value) {
    return dot(value, value);
}

static float absf_local(float value) {
    return value < 0.0f ? -value : value;
}

static int nearf_local(float a, float b) {
    return absf_local(a - b) <= 0.00002f;
}

static int vec_near(TvVec3 a, TvVec3 b) {
    return nearf_local(a.x, b.x)
        && nearf_local(a.y, b.y)
        && nearf_local(a.z, b.z);
}

static int sample_in_list(int sample_id, const int samples[5]) {
    int i;
    for (i = 0; i < 5; ++i) {
        if (samples[i] == sample_id) return 1;
    }
    return 0;
}

static float density(TvVec3 p, int field_id, int seed) {
    float x = p.x;
    float y = p.y;
    float z = p.z;
    float epsilon = 0.037f * (float)(seed + 1) + 0.013f;
    switch (field_id) {
        case 0:
            return x + y + z
                - (0.75f + 0.25f * (float)(seed % 5))
                + epsilon;
        case 1: {
            float dx = x - 0.7f;
            float dy = y - 0.9f;
            float dz = z - 1.1f;
            float radius = 0.8f + 0.1f * (float)(seed % 4);
            return dx * dx + dy * dy + dz * dz
                - radius * radius + epsilon;
        }
        case 2:
            return x * y + y * z + z * x
                - 0.2f * (float)(seed - 3) + epsilon;
        case 3:
            return x * x + 0.5f * y - 0.75f * z
                - (0.6f + 0.15f * (float)seed) + epsilon;
        case 4:
            return (x - 0.8f) * (y - 1.1f)
                - (z - 0.6f) * (0.5f + 0.1f * (float)seed)
                + epsilon;
        case 5:
            return x * x + y * y - z * z
                - (0.5f + 0.2f * (float)seed) + epsilon;
        default:
            return x + 2.0f * y - 1.5f * z
                + 0.2f * x * y - 0.1f * y * z
                + epsilon;
    }
}

static void fill_values(MappedCell *cell, int field_id, int seed) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        cell->values[i] = density(cell->samples[i], field_id, seed);
    }
    tv_m4_transition_fill_derived_samples(cell->values);
}

static unsigned int vertex_side_mask(int sample_a, int sample_b) {
    unsigned int mask = 0;
    if (sample_in_list(sample_a, u_min_samples)
        && sample_in_list(sample_b, u_min_samples)) {
        mask |= 1u << SIDE_U_MIN;
    }
    if (sample_in_list(sample_a, v_min_samples)
        && sample_in_list(sample_b, v_min_samples)) {
        mask |= 1u << SIDE_V_MIN;
    }
    return mask;
}

static void add_edge_use(
    EdgeUse edges[MAX_BOUNDARY_EDGES],
    int *edge_count,
    uint32_t a,
    uint32_t b) {
    uint32_t key_a = a < b ? a : b;
    uint32_t key_b = a < b ? b : a;
    int i;
    for (i = 0; i < *edge_count; ++i) {
        if (edges[i].key_a == key_a && edges[i].key_b == key_b) {
            ++edges[i].count;
            return;
        }
    }
    edges[*edge_count].key_a = key_a;
    edges[*edge_count].key_b = key_b;
    edges[*edge_count].directed_a = a;
    edges[*edge_count].directed_b = b;
    edges[*edge_count].count = 1;
    ++(*edge_count);
}

static int validate_cell(MappedCell *cell, Totals *totals) {
    EdgeUse edges[MAX_BOUNDARY_EDGES];
    int edge_count = 0;
    int vertex_start;
    int i;
    if (cell->info.result != TV_OK) return 1;
    vertex_start = (int)otc_m4_case_vertex_start[cell->info.case_index];
    for (i = 0; i < cell->info.vertex_count; ++i) {
        int pair_id = vertex_start + i;
        cell->vertex_side_mask[i] = vertex_side_mask(
            (int)otc_m4_vertex_pairs[pair_id][0],
            (int)otc_m4_vertex_pairs[pair_id][1]);
    }
    for (i = 0; i < cell->info.triangle_count; ++i) {
        TvTriangle triangle = cell->triangles[i];
        if (triangle.a >= (uint32_t)cell->info.vertex_count
            || triangle.b >= (uint32_t)cell->info.vertex_count
            || triangle.c >= (uint32_t)cell->info.vertex_count
            || triangle.a == triangle.b
            || triangle.b == triangle.c
            || triangle.c == triangle.a) {
            ++totals->invalid_triangles;
            continue;
        }
        if (length_squared(cross(
                sub(cell->vertices[triangle.b], cell->vertices[triangle.a]),
                sub(cell->vertices[triangle.c], cell->vertices[triangle.a])))
            <= 0.0000001f) {
            ++totals->degenerate_triangles;
        }
        add_edge_use(edges, &edge_count, triangle.a, triangle.b);
        add_edge_use(edges, &edge_count, triangle.b, triangle.c);
        add_edge_use(edges, &edge_count, triangle.c, triangle.a);
    }
    for (i = 0; i < edge_count; ++i) {
        if (edges[i].count == 2) {
            int j;
            int reverse_found = 0;
            for (j = 0; j < cell->info.triangle_count; ++j) {
                TvTriangle triangle = cell->triangles[j];
                uint32_t pairs[3][2] = {
                    {triangle.a, triangle.b},
                    {triangle.b, triangle.c},
                    {triangle.c, triangle.a}
                };
                int pair_id;
                for (pair_id = 0; pair_id < 3; ++pair_id) {
                    if (pairs[pair_id][0] == edges[i].directed_b
                        && pairs[pair_id][1] == edges[i].directed_a) {
                        reverse_found = 1;
                    }
                }
            }
            if (!reverse_found) ++totals->internal_winding_failures;
        } else if (edges[i].count > 2) {
            ++totals->invalid_triangles;
        }
    }
    totals->vertices += cell->info.vertex_count;
    totals->triangles += cell->info.triangle_count;
    return 0;
}

static int quantize(float value) {
    return value >= 0.0f
        ? (int)(value * 100000.0f + 0.5f)
        : (int)(value * 100000.0f - 0.5f);
}

static QuantizedPoint quantized_point(TvVec3 value) {
    QuantizedPoint point;
    point.x = quantize(value.x);
    point.y = quantize(value.y);
    point.z = quantize(value.z);
    return point;
}

static int point_compare(QuantizedPoint a, QuantizedPoint b) {
    if (a.x != b.x) return a.x < b.x ? -1 : 1;
    if (a.y != b.y) return a.y < b.y ? -1 : 1;
    if (a.z != b.z) return a.z < b.z ? -1 : 1;
    return 0;
}

static int point_equal(QuantizedPoint a, QuantizedPoint b) {
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

static int segment_less(Segment3i a, Segment3i b) {
    int compare = point_compare(a.a, b.a);
    if (compare != 0) return compare < 0;
    compare = point_compare(a.b, b.b);
    if (compare != 0) return compare < 0;
    return a.direction < b.direction;
}

static void sort_fingerprint(Fingerprint *fingerprint) {
    int i;
    int j;
    for (i = 1; i < fingerprint->count; ++i) {
        Segment3i value = fingerprint->segments[i];
        j = i - 1;
        while (j >= 0 && segment_less(value, fingerprint->segments[j])) {
            fingerprint->segments[j + 1] = fingerprint->segments[j];
            --j;
        }
        fingerprint->segments[j + 1] = value;
    }
}

static Fingerprint fingerprint_for_side(
    const MappedCell *cell,
    int side) {
    EdgeUse edges[MAX_BOUNDARY_EDGES];
    Fingerprint fingerprint;
    int edge_count = 0;
    int i;
    fingerprint.count = 0;
    for (i = 0; i < cell->info.triangle_count; ++i) {
        TvTriangle triangle = cell->triangles[i];
        add_edge_use(edges, &edge_count, triangle.a, triangle.b);
        add_edge_use(edges, &edge_count, triangle.b, triangle.c);
        add_edge_use(edges, &edge_count, triangle.c, triangle.a);
    }
    for (i = 0; i < edge_count; ++i) {
        if (edges[i].count == 1
            && (cell->vertex_side_mask[edges[i].directed_a] & (1u << side))
            && (cell->vertex_side_mask[edges[i].directed_b] & (1u << side))) {
            Segment3i segment;
            segment.a = quantized_point(cell->vertices[edges[i].directed_a]);
            segment.b = quantized_point(cell->vertices[edges[i].directed_b]);
            segment.direction = 1;
            if (point_compare(segment.b, segment.a) < 0) {
                QuantizedPoint swap = segment.a;
                segment.a = segment.b;
                segment.b = swap;
                segment.direction = -1;
            }
            fingerprint.segments[fingerprint.count++] = segment;
        }
    }
    sort_fingerprint(&fingerprint);
    return fingerprint;
}

static void compare_fingerprints(
    const Fingerprint *a,
    const Fingerprint *b,
    Totals *totals) {
    int i;
    ++totals->shared_faces;
    if (a->count > 0 || b->count > 0) ++totals->nonempty_shared_faces;
    if (a->count != b->count) {
        ++totals->lateral_geometry_failures;
        return;
    }
    for (i = 0; i < a->count; ++i) {
        if (!point_equal(a->segments[i].a, b->segments[i].a)
            || !point_equal(a->segments[i].b, b->segments[i].b)) {
            ++totals->lateral_geometry_failures;
        } else if (a->segments[i].direction + b->segments[i].direction != 0) {
            ++totals->lateral_winding_failures;
        }
    }
}

static void compare_shared_samples(
    const MappedCell *a,
    const int a_ids[5],
    const MappedCell *b,
    const int b_ids[5],
    Totals *totals) {
    int i;
    for (i = 0; i < 5; ++i) {
        ++totals->shared_samples;
        if (!vec_near(a->samples[a_ids[i]], b->samples[b_ids[i]])) {
            ++totals->sample_position_failures;
        }
        if (!nearf_local(a->values[a_ids[i]], b->values[b_ids[i]])) {
            ++totals->sample_value_failures;
        }
    }
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

static int build_cell(
    MappedCell *cell,
    const TvM4TransitionFrame *frame,
    int field_id,
    int seed,
    Totals *totals) {
    if (tv_m4_transition_frame_sample_positions(
            frame,
            TV_M4_BOUNDARY_U_MIN | TV_M4_BOUNDARY_V_MIN,
            0.5f,
            0.5f,
            cell->samples) != TV_OK) {
        return 1;
    }
    fill_values(cell, field_id, seed);
    cell->info = tv_m4_build_transition_cell_candidate_mapped(
        cell->values,
        cell->samples,
        0.0f,
        cell->vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        cell->triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    ++totals->builds;
    return validate_cell(cell, totals);
}

static void validate_corner(
    int sign_x,
    int sign_y,
    int sign_z,
    int field_id,
    int seed,
    Totals *totals) {
    TvM4TransitionFrame frames[3];
    MappedCell cells[3];
    Fingerprint x_to_y;
    Fingerprint y_to_x;
    Fingerprint y_to_z;
    Fingerprint z_to_y;
    Fingerprint z_to_x;
    Fingerprint x_to_z;
    TvVec3 expected_inner = vec3(
        0.5f * (float)sign_x,
        0.5f * (float)sign_y,
        0.5f * (float)sign_z);

    make_corner_frames(sign_x, sign_y, sign_z, frames);
    if (build_cell(&cells[0], &frames[0], field_id, seed, totals) != 0
        || build_cell(&cells[1], &frames[1], field_id, seed, totals) != 0
        || build_cell(&cells[2], &frames[2], field_id, seed, totals) != 0) {
        ++totals->lateral_geometry_failures;
        return;
    }
    ++totals->junctions;

    compare_shared_samples(
        &cells[0], u_min_samples,
        &cells[1], v_min_samples,
        totals);
    compare_shared_samples(
        &cells[1], u_min_samples,
        &cells[2], v_min_samples,
        totals);
    compare_shared_samples(
        &cells[2], u_min_samples,
        &cells[0], v_min_samples,
        totals);

    if (!vec_near(cells[0].samples[0], cells[1].samples[0])
        || !vec_near(cells[1].samples[0], cells[2].samples[0])
        || !vec_near(cells[0].samples[9], expected_inner)
        || !vec_near(cells[1].samples[9], expected_inner)
        || !vec_near(cells[2].samples[9], expected_inner)) {
        ++totals->corner_position_failures;
    }
    if (!nearf_local(cells[0].values[0], cells[1].values[0])
        || !nearf_local(cells[1].values[0], cells[2].values[0])
        || !nearf_local(cells[0].values[9], cells[1].values[9])
        || !nearf_local(cells[1].values[9], cells[2].values[9])) {
        ++totals->corner_value_failures;
    }

    x_to_y = fingerprint_for_side(&cells[0], SIDE_U_MIN);
    y_to_x = fingerprint_for_side(&cells[1], SIDE_V_MIN);
    y_to_z = fingerprint_for_side(&cells[1], SIDE_U_MIN);
    z_to_y = fingerprint_for_side(&cells[2], SIDE_V_MIN);
    z_to_x = fingerprint_for_side(&cells[2], SIDE_U_MIN);
    x_to_z = fingerprint_for_side(&cells[0], SIDE_V_MIN);
    compare_fingerprints(&x_to_y, &y_to_x, totals);
    compare_fingerprints(&y_to_z, &z_to_y, totals);
    compare_fingerprints(&z_to_x, &x_to_z, totals);
}

int main(void) {
    Totals totals = {0};
    int sign_x;
    int sign_y;
    int sign_z;
    int field_id;
    int seed;
    int failed;

    for (sign_x = -1; sign_x <= 1; sign_x += 2) {
        for (sign_y = -1; sign_y <= 1; sign_y += 2) {
            for (sign_z = -1; sign_z <= 1; sign_z += 2) {
                ++totals.octants;
                for (field_id = 0; field_id < FIELD_COUNT; ++field_id) {
                    for (seed = 0; seed < SEED_COUNT; ++seed) {
                        validate_corner(
                            sign_x,
                            sign_y,
                            sign_z,
                            field_id,
                            seed,
                            &totals);
                    }
                }
            }
        }
    }

    failed = totals.octants != 8
        || totals.junctions != 448
        || totals.builds != 1344
        || totals.shared_faces != 1344
        || totals.shared_samples != 6720
        || totals.nonempty_shared_faces <= 300
        || totals.invalid_triangles != 0
        || totals.degenerate_triangles != 0
        || totals.internal_winding_failures != 0
        || totals.sample_position_failures != 0
        || totals.sample_value_failures != 0
        || totals.lateral_geometry_failures != 0
        || totals.lateral_winding_failures != 0
        || totals.corner_position_failures != 0
        || totals.corner_value_failures != 0;

    printf(
        "m16 junctions octants=%d fields=%d seeds=%d junctions=%d builds=%d vertices=%d triangles=%d invalid_triangles=%d degenerate_triangles=%d internal_winding_failures=%d shared_faces=%d nonempty_shared_faces=%d shared_samples=%d sample_position_failures=%d sample_value_failures=%d lateral_geometry_failures=%d lateral_winding_failures=%d corner_position_failures=%d corner_value_failures=%d\n",
        totals.octants,
        FIELD_COUNT,
        SEED_COUNT,
        totals.junctions,
        totals.builds,
        totals.vertices,
        totals.triangles,
        totals.invalid_triangles,
        totals.degenerate_triangles,
        totals.internal_winding_failures,
        totals.shared_faces,
        totals.nonempty_shared_faces,
        totals.shared_samples,
        totals.sample_position_failures,
        totals.sample_value_failures,
        totals.lateral_geometry_failures,
        totals.lateral_winding_failures,
        totals.corner_position_failures,
        totals.corner_value_failures);
    return failed ? 1 : 0;
}
