/* SPDX-License-Identifier: 0BSD */
#include <stdint.h>
#include <stdio.h>
#include "official_topology_candidate_tables.h"
#include "transvoxel.h"
#include "transvoxel_m4_backend.h"

#define GRID_SIZE 8
#define SEED_COUNT 12
#define FIELD_COUNT 7
#define FACE_X_MIN 0
#define FACE_X_MAX 1
#define FACE_Y_MIN 2
#define FACE_Y_MAX 3
#define MAX_FACE_SEGMENTS (TV_TRANSITION_MAX_TRIANGLES * 3)

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

static float absf_local(float v) {
    return v < 0.0f ? -v : v;
}

static int coord_equal(float a, float b) {
    return absf_local(a - b) <= 0.00001f;
}

static int quantize2(float v) {
    return v >= 0.0f ? (int)(v * 2.0f + 0.5f) : (int)(v * 2.0f - 0.5f);
}

static int segment_less(Segment2i a, Segment2i b) {
    if (a.ax != b.ax) return a.ax < b.ax;
    if (a.ay != b.ay) return a.ay < b.ay;
    if (a.bx != b.bx) return a.bx < b.bx;
    return a.by < b.by;
}

static int segment_equal(Segment2i a, Segment2i b) {
    return a.ax == b.ax && a.ay == b.ay && a.bx == b.bx && a.by == b.by;
}

static void canonicalize_segment(Segment2i *segment) {
    int swap = 0;
    if (segment->bx < segment->ax) {
        swap = 1;
    } else if (segment->bx == segment->ax && segment->by < segment->ay) {
        swap = 1;
    }
    if (swap) {
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
        if (!segment_equal(a->segments[i], b->segments[i])) {
            return 0;
        }
    }
    return 1;
}

static void add_edge(EdgeCount *edges, int *edge_count, uint32_t a, uint32_t b) {
    int i;
    if (b < a) {
        uint32_t tmp = a;
        a = b;
        b = tmp;
    }
    for (i = 0; i < *edge_count; ++i) {
        if (edges[i].a == a && edges[i].b == b) {
            edges[i].count += 1;
            return;
        }
    }
    edges[*edge_count].a = a;
    edges[*edge_count].b = b;
    edges[*edge_count].count = 1;
    *edge_count += 1;
}

static float area2(TvVec3 a, TvVec3 b, TvVec3 c) {
    float ux = b.x - a.x;
    float uy = b.y - a.y;
    float uz = b.z - a.z;
    float vx = c.x - a.x;
    float vy = c.y - a.y;
    float vz = c.z - a.z;
    float cx = uy * vz - uz * vy;
    float cy = uz * vx - ux * vz;
    float cz = ux * vy - uy * vx;
    return cx * cx + cy * cy + cz * cz;
}

static void fill_samples_from_case(int case_index, float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
}

static int field_inside(int field_id, int x, int y, int seed) {
    int cx;
    int cy;
    int r;
    uint32_t n;
    switch (field_id) {
        case 0:
            return x < 5 + (seed % 3);
        case 1:
            return y < 4 + (seed % 4);
        case 2:
            return x + y < 8 + (seed % 5);
        case 3:
            cx = 6 + (seed % 3);
            cy = 6 + ((seed / 2) % 3);
            r = 5 + (seed % 2);
            return (x - cx) * (x - cx) + (y - cy) * (y - cy) < r * r;
        case 4:
            return (x - 6) * (x - 6) - (y - 6) * (y - 6) + seed - 2 < 0;
        case 5:
            n = ((uint32_t)x * 73856093u)
                ^ ((uint32_t)y * 19349663u)
                ^ ((uint32_t)seed * 83492791u);
            n = (n ^ (n >> 13)) * 1274126177u;
            n = n ^ (n >> 16);
            return (n & 1u) != 0u;
        default:
            return ((x + seed) % 7) + ((y * 3 + seed) % 11) < 8;
    }
}

static int case_for_cell(int field_id, int cx, int cy, int seed) {
    int case_index = 0;
    int sx;
    int sy;
    int sample_id = 0;
    for (sy = 0; sy < 3; ++sy) {
        for (sx = 0; sx < 3; ++sx) {
            int gx = cx * 2 + sx;
            int gy = cy * 2 + sy;
            if (field_inside(field_id, gx, gy, seed)) {
                case_index |= 1 << sample_id;
            }
            ++sample_id;
        }
    }
    return case_index;
}

static int point_on_face(TvVec3 p, int face) {
    if (face == FACE_X_MIN) return coord_equal(p.x, 0.0f);
    if (face == FACE_X_MAX) return coord_equal(p.x, 2.0f);
    if (face == FACE_Y_MIN) return coord_equal(p.y, 0.0f);
    return coord_equal(p.y, 2.0f);
}

static Segment2i project_segment(TvVec3 a, TvVec3 b, int face) {
    Segment2i segment;
    if (face == FACE_X_MIN || face == FACE_X_MAX) {
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

static int build_normal_api_fingerprints(
    int case_index,
    Fingerprint fingerprints[4],
    int *vertex_total,
    int *triangle_total) {
    float samples[TV_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
    EdgeCount edges[TV_TRANSITION_MAX_TRIANGLES * 3];
    TvBuildInfo info;
    int edge_count = 0;
    int face;
    int i;

    for (face = 0; face < 4; ++face) {
        fingerprints[face].count = 0;
    }

    fill_samples_from_case(case_index, samples);
    info = tv_build_transition_cell(
        samples,
        0.0f,
        (TvVec3){0.0f, 0.0f, 0.0f},
        (TvVec3){1.0f, 1.0f, 1.0f},
        vertices,
        TV_TRANSITION_MAX_VERTICES,
        triangles,
        TV_TRANSITION_MAX_TRIANGLES);
    if (info.result != TV_OK || info.case_index != case_index) {
        printf("normal_api_build_failed case=%d result=%d\n", case_index, info.result);
        return 1;
    }
    if (info.vertex_count != (int)otc_m4_case_vertex_count[case_index]
        || info.triangle_count != (int)otc_m4_case_triangle_count[case_index]) {
        printf("normal_api_m4_count_mismatch case=%d\n", case_index);
        return 1;
    }

    for (i = 0; i < info.triangle_count; ++i) {
        TvTriangle tri = triangles[i];
        if (tri.a >= (uint32_t)info.vertex_count
            || tri.b >= (uint32_t)info.vertex_count
            || tri.c >= (uint32_t)info.vertex_count
            || tri.a == tri.b
            || tri.b == tri.c
            || tri.c == tri.a) {
            printf("normal_api_bad_triangle_indices case=%d triangle=%d\n", case_index, i);
            return 1;
        }
        if (area2(vertices[tri.a], vertices[tri.b], vertices[tri.c]) <= 0.0000001f) {
            printf("normal_api_degenerate_triangle case=%d triangle=%d\n", case_index, i);
            return 1;
        }
        add_edge(edges, &edge_count, tri.a, tri.b);
        add_edge(edges, &edge_count, tri.b, tri.c);
        add_edge(edges, &edge_count, tri.c, tri.a);
    }

    for (i = 0; i < edge_count; ++i) {
        if (edges[i].count == 1) {
            TvVec3 a = vertices[edges[i].a];
            TvVec3 b = vertices[edges[i].b];
            for (face = 0; face < 4; ++face) {
                if (point_on_face(a, face) && point_on_face(b, face)) {
                    Fingerprint *fp = &fingerprints[face];
                    if (fp->count >= MAX_FACE_SEGMENTS) {
                        printf("normal_api_too_many_face_segments case=%d face=%d\n", case_index, face);
                        return 1;
                    }
                    fp->segments[fp->count++] = project_segment(a, b, face);
                }
            }
        } else if (edges[i].count > 2) {
            printf("normal_api_overused_edge case=%d\n", case_index);
            return 1;
        }
    }

    for (face = 0; face < 4; ++face) {
        sort_fingerprint(&fingerprints[face]);
    }
    *vertex_total += info.vertex_count;
    *triangle_total += info.triangle_count;
    return 0;
}

static int validate_all_cases(
    int expect_m4,
    int *vertex_total,
    int *triangle_total,
    int *count_differences) {
    int case_index;
    *vertex_total = 0;
    *triangle_total = 0;
    *count_differences = 0;
    for (case_index = 0; case_index < (int)OTC_M4_CASE_COUNT; ++case_index) {
        float samples[TV_TRANSITION_SAMPLE_COUNT];
        TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
        TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo info;
        fill_samples_from_case(case_index, samples);
        info = tv_build_transition_cell(
            samples,
            0.0f,
            (TvVec3){0.0f, 0.0f, 0.0f},
            (TvVec3){1.0f, 1.0f, 1.0f},
            vertices,
            TV_TRANSITION_MAX_VERTICES,
            triangles,
            TV_TRANSITION_MAX_TRIANGLES);
        if (info.result != TV_OK || info.case_index != case_index) {
            printf("backend_case_build_failed case=%d result=%d\n", case_index, info.result);
            return 1;
        }
        if (expect_m4) {
            if (info.vertex_count != (int)otc_m4_case_vertex_count[case_index]
                || info.triangle_count != (int)otc_m4_case_triangle_count[case_index]) {
                printf("m4_backend_case_count_mismatch case=%d\n", case_index);
                return 1;
            }
        } else if (info.vertex_count != (int)otc_m4_case_vertex_count[case_index]
            || info.triangle_count != (int)otc_m4_case_triangle_count[case_index]) {
            *count_differences += 1;
        }
        *vertex_total += info.vertex_count;
        *triangle_total += info.triangle_count;
    }
    return 0;
}

static int validate_m4_normal_api_strips(
    int *builds_out,
    int *shared_faces_out,
    int *failures_out,
    int *vertex_total_out,
    int *triangle_total_out) {
    int field_id;
    int seed;
    int x;
    int y;
    int builds = 0;
    int shared_faces = 0;
    int failures = 0;
    int vertex_total = 0;
    int triangle_total = 0;
    Fingerprint fingerprints[GRID_SIZE][GRID_SIZE][4];

    for (field_id = 0; field_id < FIELD_COUNT; ++field_id) {
        for (seed = 0; seed < SEED_COUNT; ++seed) {
            for (y = 0; y < GRID_SIZE; ++y) {
                for (x = 0; x < GRID_SIZE; ++x) {
                    int case_index = case_for_cell(field_id, x, y, seed);
                    if (build_normal_api_fingerprints(
                        case_index,
                        fingerprints[y][x],
                        &vertex_total,
                        &triangle_total) != 0) {
                        return 1;
                    }
                    ++builds;
                }
            }
            for (y = 0; y < GRID_SIZE; ++y) {
                for (x = 0; x < GRID_SIZE - 1; ++x) {
                    ++shared_faces;
                    if (!fingerprint_equal(
                        &fingerprints[y][x][FACE_X_MAX],
                        &fingerprints[y][x + 1][FACE_X_MIN])) {
                        ++failures;
                    }
                }
            }
            for (y = 0; y < GRID_SIZE - 1; ++y) {
                for (x = 0; x < GRID_SIZE; ++x) {
                    ++shared_faces;
                    if (!fingerprint_equal(
                        &fingerprints[y][x][FACE_Y_MAX],
                        &fingerprints[y + 1][x][FACE_Y_MIN])) {
                        ++failures;
                    }
                }
            }
        }
    }

    *builds_out = builds;
    *shared_faces_out = shared_faces;
    *failures_out = failures;
    *vertex_total_out = vertex_total;
    *triangle_total_out = triangle_total;
    return failures == 0 ? 0 : 1;
}

int main(void) {
    int default_vertices = 0;
    int default_triangles = 0;
    int default_differences = 0;
    int m4_vertices = 0;
    int m4_triangles = 0;
    int m4_differences = 0;
    int restored_vertices = 0;
    int restored_triangles = 0;
    int restored_differences = 0;
    int strip_builds = 0;
    int strip_shared_faces = 0;
    int strip_failures = 0;
    int strip_vertices = 0;
    int strip_triangles = 0;

    if (tv_transition_backend_is_custom()) {
        printf("backend_unexpectedly_custom_at_start\n");
        return 1;
    }
    if (validate_all_cases(0, &default_vertices, &default_triangles, &default_differences) != 0) {
        return 1;
    }
    if (default_vertices != 10496 || default_triangles != 12288 || default_differences != 510) {
        printf("default_backend_totals_unexpected\n");
        return 1;
    }

    if (tv_install_m4_transition_backend_candidate() != TV_OK) {
        printf("m4_install_failed\n");
        return 1;
    }
    if (!tv_transition_backend_is_custom() || !tv_m4_transition_backend_candidate_is_installed()) {
        printf("m4_install_state_failed\n");
        return 1;
    }
    if (validate_all_cases(1, &m4_vertices, &m4_triangles, &m4_differences) != 0) {
        return 1;
    }
    if (m4_vertices != 4096 || m4_triangles != 2640 || m4_differences != 0) {
        printf("m4_backend_totals_unexpected\n");
        return 1;
    }
    if (validate_m4_normal_api_strips(
        &strip_builds,
        &strip_shared_faces,
        &strip_failures,
        &strip_vertices,
        &strip_triangles) != 0) {
        return 1;
    }

    tv_uninstall_m4_transition_backend_candidate();
    if (tv_transition_backend_is_custom() || tv_m4_transition_backend_candidate_is_installed()) {
        printf("m4_uninstall_state_failed\n");
        return 1;
    }
    if (validate_all_cases(0, &restored_vertices, &restored_triangles, &restored_differences) != 0) {
        return 1;
    }
    if (restored_vertices != default_vertices
        || restored_triangles != default_triangles
        || restored_differences != default_differences) {
        printf("default_backend_restore_failed\n");
        return 1;
    }

    printf(
        "m7 backend switch cases=%u default_vertices=%d default_triangles=%d m4_vertices=%d m4_triangles=%d count_differences=%d restored_default=1\n",
        OTC_M4_CASE_COUNT,
        default_vertices,
        default_triangles,
        m4_vertices,
        m4_triangles,
        default_differences);
    printf(
        "m7 normal_api_m4_seams fields=%d seeds=%d grid=%d builds=%d shared_faces=%d failures=%d total_vertices=%d total_triangles=%d\n",
        FIELD_COUNT,
        SEED_COUNT,
        GRID_SIZE,
        strip_builds,
        strip_shared_faces,
        strip_failures,
        strip_vertices,
        strip_triangles);
    return 0;
}
