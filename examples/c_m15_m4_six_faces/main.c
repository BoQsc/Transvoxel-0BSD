/* SPDX-License-Identifier: 0BSD */
#include <stdint.h>
#include <stdio.h>
#include "transvoxel_m4_candidate.h"

#define GRID_SIZE 4
#define SEED_COUNT 4
#define FIELD_COUNT 7
#define SIDE_U_MIN 0
#define SIDE_U_MAX 1
#define SIDE_V_MIN 2
#define SIDE_V_MAX 3
#define MAX_FACE_SEGMENTS (TV_M4_TRANSITION_MAX_TRIANGLES * 3)

typedef struct Segment2i {
    int ax;
    int ay;
    int bx;
    int by;
} Segment2i;

typedef struct Fingerprint {
    int count;
    Segment2i segments[MAX_FACE_SEGMENTS];
} Fingerprint;

typedef struct EdgeCount {
    uint32_t a;
    uint32_t b;
    int count;
} EdgeCount;

typedef struct FaceTotals {
    int cases;
    int vertices;
    int triangles;
    int invalid_triangles;
    int degenerate_triangles;
    int transform_failures;
    int orientation_failures;
    int frame_failures;
    int seam_builds;
    int shared_faces;
    int seam_failures;
    int seam_vertices;
    int seam_triangles;
} FaceTotals;

static const int expected_axes[TV_M4_FACE_COUNT][9] = {
    {0, 1, 0, 0, 0, 1, 1, 0, 0},
    {0, -1, 0, 0, 0, 1, -1, 0, 0},
    {0, 0, 1, 1, 0, 0, 0, 1, 0},
    {0, 0, -1, 1, 0, 0, 0, -1, 0},
    {1, 0, 0, 0, 1, 0, 0, 0, 1},
    {-1, 0, 0, 0, 1, 0, 0, 0, -1}
};

static float absf_local(float value) {
    return value < 0.0f ? -value : value;
}

static int nearf_local(float a, float b) {
    return absf_local(a - b) <= 0.00002f;
}

static TvVec3 vec3(float x, float y, float z) {
    TvVec3 out;
    out.x = x;
    out.y = y;
    out.z = z;
    return out;
}

static TvVec3 add(TvVec3 a, TvVec3 b) {
    return vec3(a.x + b.x, a.y + b.y, a.z + b.z);
}

static TvVec3 sub(TvVec3 a, TvVec3 b) {
    return vec3(a.x - b.x, a.y - b.y, a.z - b.z);
}

static TvVec3 scale(TvVec3 a, float value) {
    return vec3(a.x * value, a.y * value, a.z * value);
}

static float dot(TvVec3 a, TvVec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static TvVec3 cross(TvVec3 a, TvVec3 b) {
    return vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x);
}

static float length_squared(TvVec3 value) {
    return dot(value, value);
}

static int vec_near(TvVec3 a, TvVec3 b) {
    return nearf_local(a.x, b.x)
        && nearf_local(a.y, b.y)
        && nearf_local(a.z, b.z);
}

static float frame_determinant(const TvM4TransitionFrame *frame) {
    return dot(cross(frame->axis_u, frame->axis_v), frame->axis_w);
}

static TvVec3 frame_to_local(const TvM4TransitionFrame *frame, TvVec3 world) {
    TvVec3 delta = sub(world, frame->origin);
    return vec3(
        dot(delta, frame->axis_u) / length_squared(frame->axis_u),
        dot(delta, frame->axis_v) / length_squared(frame->axis_v),
        dot(delta, frame->axis_w) / length_squared(frame->axis_w));
}

static TvVec3 expected_transformed_cross(
    const TvM4TransitionFrame *frame,
    TvVec3 local_cross) {
    float determinant = frame_determinant(frame);
    TvVec3 out = vec3(0.0f, 0.0f, 0.0f);
    out = add(out, scale(
        frame->axis_u,
        determinant * local_cross.x / length_squared(frame->axis_u)));
    out = add(out, scale(
        frame->axis_v,
        determinant * local_cross.y / length_squared(frame->axis_v)));
    out = add(out, scale(
        frame->axis_w,
        determinant * local_cross.z / length_squared(frame->axis_w)));
    return out;
}

static void fill_samples_from_case(
    int case_index,
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_m4_transition_fill_derived_samples(samples);
}

static int validate_frame(TvM4TransitionFace face) {
    TvM4TransitionFrame frame;
    TvM4TransitionFrame mirrored_frame;
    TvVec3 axes[3];
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 local_vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvVec3 mirrored_vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle local_triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    TvTriangle mirrored_triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo local_info;
    TvBuildInfo mirrored_info;
    int i;
    int failures = 0;
    if (tv_m4_transition_face_frame(
            face,
            vec3(3.0f, -5.0f, 7.0f),
            vec3(1.0f, 1.0f, 1.0f),
            &frame) != TV_OK) {
        return 1;
    }
    axes[0] = frame.axis_u;
    axes[1] = frame.axis_v;
    axes[2] = frame.axis_w;
    for (i = 0; i < 3; ++i) {
        if (!nearf_local(axes[i].x, (float)expected_axes[(int)face][i * 3])
            || !nearf_local(axes[i].y, (float)expected_axes[(int)face][i * 3 + 1])
            || !nearf_local(axes[i].z, (float)expected_axes[(int)face][i * 3 + 2])) {
            ++failures;
        }
    }
    if (!nearf_local(frame_determinant(&frame), 1.0f)) ++failures;
    if (!nearf_local(dot(frame.axis_u, frame.axis_v), 0.0f)) ++failures;
    if (!nearf_local(dot(frame.axis_u, frame.axis_w), 0.0f)) ++failures;
    if (!nearf_local(dot(frame.axis_v, frame.axis_w), 0.0f)) ++failures;
    for (i = 0; i < TV_M4_TRANSITION_SAMPLE_COUNT; ++i) {
        TvVec3 local_sample = tv_m4_transition_sample_position(i);
        TvVec3 world_sample = tv_m4_transition_frame_position(&frame, local_sample);
        if (!vec_near(frame_to_local(&frame, world_sample), local_sample)) {
            ++failures;
        }
    }

    fill_samples_from_case(1, samples);
    local_info = tv_m4_build_transition_cell_candidate(
        samples,
        0.0f,
        vec3(0.0f, 0.0f, 0.0f),
        vec3(1.0f, 1.0f, 1.0f),
        local_vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        local_triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    mirrored_info = tv_m4_build_transition_cell_candidate_oriented(
        samples,
        0.0f,
        face,
        vec3(3.0f, -5.0f, 7.0f),
        vec3(-1.0f, 1.0f, 1.0f),
        mirrored_vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        mirrored_triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    if (tv_m4_transition_face_frame(
            face,
            vec3(3.0f, -5.0f, 7.0f),
            vec3(-1.0f, 1.0f, 1.0f),
            &mirrored_frame) != TV_OK
        || frame_determinant(&mirrored_frame) >= 0.0f
        || local_info.result != TV_OK
        || mirrored_info.result != TV_OK
        || local_info.triangle_count != mirrored_info.triangle_count) {
        ++failures;
    } else {
        for (i = 0; i < local_info.triangle_count; ++i) {
            if (mirrored_triangles[i].a != local_triangles[i].a
                || mirrored_triangles[i].b != local_triangles[i].c
                || mirrored_triangles[i].c != local_triangles[i].b) {
                ++failures;
            }
        }
    }
    return failures;
}

static void validate_all_cases(TvM4TransitionFace face, FaceTotals *totals) {
    TvM4TransitionFrame frame;
    TvVec3 origin = vec3(11.0f, -7.0f, 3.0f);
    TvVec3 local_scale = vec3(0.75f, 1.25f, 1.5f);
    int case_index;

    totals->frame_failures += validate_frame(face);
    if (tv_m4_transition_face_frame(face, origin, local_scale, &frame) != TV_OK) {
        ++totals->frame_failures;
        return;
    }

    for (case_index = 0; case_index < (int)OTC_M4_CASE_COUNT; ++case_index) {
        float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
        TvVec3 local_vertices[TV_M4_TRANSITION_MAX_VERTICES];
        TvVec3 world_vertices[TV_M4_TRANSITION_MAX_VERTICES];
        TvTriangle local_triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
        TvTriangle world_triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo local_info;
        TvBuildInfo world_info;
        int i;

        fill_samples_from_case(case_index, samples);
        local_info = tv_m4_build_transition_cell_candidate(
            samples,
            0.0f,
            vec3(0.0f, 0.0f, 0.0f),
            vec3(1.0f, 1.0f, 1.0f),
            local_vertices,
            TV_M4_TRANSITION_MAX_VERTICES,
            local_triangles,
            TV_M4_TRANSITION_MAX_TRIANGLES);
        world_info = tv_m4_build_transition_cell_candidate_oriented(
            samples,
            0.0f,
            face,
            origin,
            local_scale,
            world_vertices,
            TV_M4_TRANSITION_MAX_VERTICES,
            world_triangles,
            TV_M4_TRANSITION_MAX_TRIANGLES);
        ++totals->cases;
        if (local_info.result != TV_OK
            || world_info.result != TV_OK
            || local_info.case_index != case_index
            || world_info.case_index != case_index
            || local_info.vertex_count != world_info.vertex_count
            || local_info.triangle_count != world_info.triangle_count) {
            ++totals->transform_failures;
            continue;
        }
        totals->vertices += world_info.vertex_count;
        totals->triangles += world_info.triangle_count;

        for (i = 0; i < world_info.vertex_count; ++i) {
            TvVec3 expected = tv_m4_transition_frame_position(&frame, local_vertices[i]);
            TvVec3 recovered = frame_to_local(&frame, world_vertices[i]);
            if (!vec_near(world_vertices[i], expected)
                || !vec_near(recovered, local_vertices[i])) {
                ++totals->transform_failures;
            }
        }

        for (i = 0; i < world_info.triangle_count; ++i) {
            TvTriangle local_tri = local_triangles[i];
            TvTriangle world_tri = world_triangles[i];
            TvVec3 local_cross;
            TvVec3 world_cross;
            TvVec3 expected_cross;
            if (world_tri.a >= (uint32_t)world_info.vertex_count
                || world_tri.b >= (uint32_t)world_info.vertex_count
                || world_tri.c >= (uint32_t)world_info.vertex_count
                || world_tri.a == world_tri.b
                || world_tri.b == world_tri.c
                || world_tri.c == world_tri.a) {
                ++totals->invalid_triangles;
                continue;
            }
            if (local_tri.a != world_tri.a
                || local_tri.b != world_tri.b
                || local_tri.c != world_tri.c) {
                ++totals->orientation_failures;
            }
            local_cross = cross(
                sub(local_vertices[local_tri.b], local_vertices[local_tri.a]),
                sub(local_vertices[local_tri.c], local_vertices[local_tri.a]));
            world_cross = cross(
                sub(world_vertices[world_tri.b], world_vertices[world_tri.a]),
                sub(world_vertices[world_tri.c], world_vertices[world_tri.a]));
            if (length_squared(world_cross) <= 0.0000001f) {
                ++totals->degenerate_triangles;
                continue;
            }
            expected_cross = expected_transformed_cross(&frame, local_cross);
            if (!vec_near(world_cross, expected_cross)) {
                ++totals->orientation_failures;
            }
        }
    }
}

static int quantize2(float value) {
    return value >= 0.0f
        ? (int)(value * 2.0f + 0.5f)
        : (int)(value * 2.0f - 0.5f);
}

static int segment_less(Segment2i a, Segment2i b) {
    if (a.ax != b.ax) return a.ax < b.ax;
    if (a.ay != b.ay) return a.ay < b.ay;
    if (a.bx != b.bx) return a.bx < b.bx;
    return a.by < b.by;
}

static int segment_equal(Segment2i a, Segment2i b) {
    return a.ax == b.ax && a.ay == b.ay
        && a.bx == b.bx && a.by == b.by;
}

static void canonicalize_segment(Segment2i *segment) {
    if (segment->bx < segment->ax
        || (segment->bx == segment->ax && segment->by < segment->ay)) {
        int ax = segment->ax;
        int ay = segment->ay;
        segment->ax = segment->bx;
        segment->ay = segment->by;
        segment->bx = ax;
        segment->by = ay;
    }
}

static void sort_fingerprint(Fingerprint *fingerprint) {
    int i;
    int j;
    for (i = 1; i < fingerprint->count; ++i) {
        Segment2i value = fingerprint->segments[i];
        j = i - 1;
        while (j >= 0 && segment_less(value, fingerprint->segments[j])) {
            fingerprint->segments[j + 1] = fingerprint->segments[j];
            --j;
        }
        fingerprint->segments[j + 1] = value;
    }
}

static int fingerprint_equal(const Fingerprint *a, const Fingerprint *b) {
    int i;
    if (a->count != b->count) return 0;
    for (i = 0; i < a->count; ++i) {
        if (!segment_equal(a->segments[i], b->segments[i])) return 0;
    }
    return 1;
}

static void add_edge(
    EdgeCount *edges,
    int *edge_count,
    uint32_t a,
    uint32_t b) {
    int i;
    if (b < a) {
        uint32_t tmp = a;
        a = b;
        b = tmp;
    }
    for (i = 0; i < *edge_count; ++i) {
        if (edges[i].a == a && edges[i].b == b) {
            ++edges[i].count;
            return;
        }
    }
    edges[*edge_count].a = a;
    edges[*edge_count].b = b;
    edges[*edge_count].count = 1;
    ++(*edge_count);
}

static int field_inside(int field_id, int x, int y, int seed) {
    int cx;
    int cy;
    int radius;
    uint32_t noise;
    switch (field_id) {
        case 0:
            return x < 3 + (seed % 3);
        case 1:
            return y < 3 + (seed % 3);
        case 2:
            return x + y < 6 + (seed % 4);
        case 3:
            cx = 3 + (seed % 2);
            cy = 3 + ((seed / 2) % 2);
            radius = 3 + (seed % 2);
            return (x - cx) * (x - cx) + (y - cy) * (y - cy)
                < radius * radius;
        case 4:
            return (x - 3) * (x - 3) - (y - 3) * (y - 3) + seed - 1 < 0;
        case 5:
            noise = ((uint32_t)x * 73856093u)
                ^ ((uint32_t)y * 19349663u)
                ^ ((uint32_t)seed * 83492791u);
            noise = (noise ^ (noise >> 13)) * 1274126177u;
            noise = noise ^ (noise >> 16);
            return (noise & 1u) != 0u;
        default:
            return ((x + seed) % 7) + ((y * 3 + seed) % 11) < 8;
    }
}

static int case_for_cell(int field_id, int cell_x, int cell_y, int seed) {
    int case_index = 0;
    int sx;
    int sy;
    int sample_id = 0;
    for (sy = 0; sy < 3; ++sy) {
        for (sx = 0; sx < 3; ++sx) {
            if (field_inside(
                    field_id,
                    cell_x * 2 + sx,
                    cell_y * 2 + sy,
                    seed)) {
                case_index |= 1 << sample_id;
            }
            ++sample_id;
        }
    }
    return case_index;
}

static int point_on_side(TvVec3 local, int side) {
    if (side == SIDE_U_MIN) return nearf_local(local.x, 0.0f);
    if (side == SIDE_U_MAX) return nearf_local(local.x, 2.0f);
    if (side == SIDE_V_MIN) return nearf_local(local.y, 0.0f);
    return nearf_local(local.y, 2.0f);
}

static Segment2i project_segment(TvVec3 a, TvVec3 b, int side) {
    Segment2i segment;
    if (side == SIDE_U_MIN || side == SIDE_U_MAX) {
        segment.ax = quantize2(a.y);
        segment.ay = quantize2(a.z);
        segment.bx = quantize2(b.y);
        segment.by = quantize2(b.z);
    } else {
        segment.ax = quantize2(a.x);
        segment.ay = quantize2(a.z);
        segment.bx = quantize2(b.x);
        segment.by = quantize2(b.z);
    }
    canonicalize_segment(&segment);
    return segment;
}

static int build_fingerprints(
    TvM4TransitionFace face,
    int case_index,
    TvVec3 origin,
    Fingerprint fingerprints[4],
    FaceTotals *totals) {
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    EdgeCount edges[TV_M4_TRANSITION_MAX_TRIANGLES * 3];
    TvM4TransitionFrame frame;
    TvBuildInfo info;
    int edge_count = 0;
    int side;
    int i;

    for (side = 0; side < 4; ++side) fingerprints[side].count = 0;
    fill_samples_from_case(case_index, samples);
    if (tv_m4_transition_face_frame(
            face,
            origin,
            vec3(1.0f, 1.0f, 1.0f),
            &frame) != TV_OK) {
        return 1;
    }
    info = tv_m4_build_transition_cell_candidate_oriented(
        samples,
        0.0f,
        face,
        origin,
        vec3(1.0f, 1.0f, 1.0f),
        vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    if (info.result != TV_OK || info.case_index != case_index) return 1;

    for (i = 0; i < info.triangle_count; ++i) {
        TvTriangle tri = triangles[i];
        add_edge(edges, &edge_count, tri.a, tri.b);
        add_edge(edges, &edge_count, tri.b, tri.c);
        add_edge(edges, &edge_count, tri.c, tri.a);
    }
    for (i = 0; i < edge_count; ++i) {
        if (edges[i].count == 1) {
            TvVec3 a = frame_to_local(&frame, vertices[edges[i].a]);
            TvVec3 b = frame_to_local(&frame, vertices[edges[i].b]);
            for (side = 0; side < 4; ++side) {
                if (point_on_side(a, side) && point_on_side(b, side)) {
                    Fingerprint *fingerprint = &fingerprints[side];
                    if (fingerprint->count >= MAX_FACE_SEGMENTS) return 1;
                    fingerprint->segments[fingerprint->count++] =
                        project_segment(a, b, side);
                }
            }
        } else if (edges[i].count > 2) {
            return 1;
        }
    }
    for (side = 0; side < 4; ++side) sort_fingerprint(&fingerprints[side]);
    totals->seam_vertices += info.vertex_count;
    totals->seam_triangles += info.triangle_count;
    return 0;
}

static void validate_seams(TvM4TransitionFace face, FaceTotals *totals) {
    TvM4TransitionFrame root_frame;
    TvVec3 root = vec3(-13.0f, 17.0f, 5.0f);
    int field_id;
    int seed;
    int x;
    int y;

    if (tv_m4_transition_face_frame(
            face,
            root,
            vec3(1.0f, 1.0f, 1.0f),
            &root_frame) != TV_OK) {
        ++totals->seam_failures;
        return;
    }

    for (field_id = 0; field_id < FIELD_COUNT; ++field_id) {
        for (seed = 0; seed < SEED_COUNT; ++seed) {
            Fingerprint fingerprints[GRID_SIZE][GRID_SIZE][4];
            for (y = 0; y < GRID_SIZE; ++y) {
                for (x = 0; x < GRID_SIZE; ++x) {
                    TvVec3 origin = root;
                    int case_index = case_for_cell(field_id, x, y, seed);
                    origin = add(origin, scale(root_frame.axis_u, (float)(x * 2)));
                    origin = add(origin, scale(root_frame.axis_v, (float)(y * 2)));
                    if (build_fingerprints(
                            face,
                            case_index,
                            origin,
                            fingerprints[y][x],
                            totals) != 0) {
                        ++totals->seam_failures;
                    }
                    ++totals->seam_builds;
                }
            }
            for (y = 0; y < GRID_SIZE; ++y) {
                for (x = 0; x < GRID_SIZE - 1; ++x) {
                    ++totals->shared_faces;
                    if (!fingerprint_equal(
                            &fingerprints[y][x][SIDE_U_MAX],
                            &fingerprints[y][x + 1][SIDE_U_MIN])) {
                        ++totals->seam_failures;
                    }
                }
            }
            for (y = 0; y < GRID_SIZE - 1; ++y) {
                for (x = 0; x < GRID_SIZE; ++x) {
                    ++totals->shared_faces;
                    if (!fingerprint_equal(
                            &fingerprints[y][x][SIDE_V_MAX],
                            &fingerprints[y + 1][x][SIDE_V_MIN])) {
                        ++totals->seam_failures;
                    }
                }
            }
        }
    }
}

static int face_failed(const FaceTotals *totals) {
    return totals->cases != 512
        || totals->vertices != 4096
        || totals->triangles != 2640
        || totals->invalid_triangles != 0
        || totals->degenerate_triangles != 0
        || totals->transform_failures != 0
        || totals->orientation_failures != 0
        || totals->frame_failures != 0
        || totals->seam_builds != 448
        || totals->shared_faces != 672
        || totals->seam_failures != 0;
}

int main(void) {
    FaceTotals all = {0};
    int face;
    int failed_faces = 0;

    for (face = 0; face < TV_M4_FACE_COUNT; ++face) {
        FaceTotals totals = {0};
        validate_all_cases((TvM4TransitionFace)face, &totals);
        validate_seams((TvM4TransitionFace)face, &totals);
        if (face_failed(&totals)) ++failed_faces;
        printf(
            "m15 face id=%d cases=%d vertices=%d triangles=%d invalid_triangles=%d degenerate_triangles=%d transform_failures=%d orientation_failures=%d frame_failures=%d seam_builds=%d shared_faces=%d seam_failures=%d seam_vertices=%d seam_triangles=%d\n",
            face,
            totals.cases,
            totals.vertices,
            totals.triangles,
            totals.invalid_triangles,
            totals.degenerate_triangles,
            totals.transform_failures,
            totals.orientation_failures,
            totals.frame_failures,
            totals.seam_builds,
            totals.shared_faces,
            totals.seam_failures,
            totals.seam_vertices,
            totals.seam_triangles);
        all.cases += totals.cases;
        all.vertices += totals.vertices;
        all.triangles += totals.triangles;
        all.invalid_triangles += totals.invalid_triangles;
        all.degenerate_triangles += totals.degenerate_triangles;
        all.transform_failures += totals.transform_failures;
        all.orientation_failures += totals.orientation_failures;
        all.frame_failures += totals.frame_failures;
        all.seam_builds += totals.seam_builds;
        all.shared_faces += totals.shared_faces;
        all.seam_failures += totals.seam_failures;
        all.seam_vertices += totals.seam_vertices;
        all.seam_triangles += totals.seam_triangles;
    }

    printf(
        "m15 totals faces=%d failed_faces=%d cases=%d vertices=%d triangles=%d invalid_triangles=%d degenerate_triangles=%d transform_failures=%d orientation_failures=%d frame_failures=%d seam_builds=%d shared_faces=%d seam_failures=%d seam_vertices=%d seam_triangles=%d\n",
        TV_M4_FACE_COUNT,
        failed_faces,
        all.cases,
        all.vertices,
        all.triangles,
        all.invalid_triangles,
        all.degenerate_triangles,
        all.transform_failures,
        all.orientation_failures,
        all.frame_failures,
        all.seam_builds,
        all.shared_faces,
        all.seam_failures,
        all.seam_vertices,
        all.seam_triangles);
    return failed_faces == 0 ? 0 : 1;
}
