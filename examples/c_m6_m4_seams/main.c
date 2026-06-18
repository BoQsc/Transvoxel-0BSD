/* SPDX-License-Identifier: 0BSD */
#include <stdint.h>
#include <stdio.h>
#include "transvoxel.h"
#include "transvoxel_m4_candidate.h"

#define GRID_SIZE 8
#define SEED_COUNT 12
#define FIELD_COUNT 7
#define FACE_X_MIN 0
#define FACE_X_MAX 1
#define FACE_Y_MIN 2
#define FACE_Y_MAX 3
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
            n = (n ^ (n >> 13)) * 1274126177;
            n = n ^ (n >> 16);
            return (n & 1) != 0;
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

static void fill_m4_samples_from_case(
    int case_index,
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_m4_transition_fill_derived_samples(samples);
}

static void fill_default_samples_from_case(
    int case_index,
    float samples[TV_TRANSITION_SAMPLE_COUNT]) {
    int i;
    for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
        samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
    }
    tv_transition_fill_derived_samples(samples);
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

static int build_m4_fingerprints(
    int case_index,
    Fingerprint fingerprints[4],
    int *vertex_total,
    int *triangle_total) {
    float samples[TV_M4_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_M4_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_M4_TRANSITION_MAX_TRIANGLES];
    EdgeCount edges[TV_M4_TRANSITION_MAX_TRIANGLES * 3];
    TvBuildInfo info;
    int edge_count = 0;
    int face;
    int i;

    for (face = 0; face < 4; ++face) {
        fingerprints[face].count = 0;
    }

    fill_m4_samples_from_case(case_index, samples);
    info = tv_m4_build_transition_cell_candidate(
        samples,
        0.0f,
        (TvVec3){0.0f, 0.0f, 0.0f},
        (TvVec3){1.0f, 1.0f, 1.0f},
        vertices,
        TV_M4_TRANSITION_MAX_VERTICES,
        triangles,
        TV_M4_TRANSITION_MAX_TRIANGLES);
    if (info.result != TV_OK || info.case_index != case_index) {
        printf("m4_build_failed case=%d result=%d\n", case_index, info.result);
        return 1;
    }
    if (info.vertex_count != (int)otc_m4_case_vertex_count[case_index]
        || info.triangle_count != (int)otc_m4_case_triangle_count[case_index]) {
        printf("m4_count_mismatch case=%d\n", case_index);
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
            printf("m4_bad_triangle_indices case=%d triangle=%d\n", case_index, i);
            return 1;
        }
        if (area2(vertices[tri.a], vertices[tri.b], vertices[tri.c]) <= 0.0000001f) {
            printf("m4_degenerate_triangle case=%d triangle=%d\n", case_index, i);
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
                        printf("m4_too_many_face_segments case=%d face=%d\n", case_index, face);
                        return 1;
                    }
                    fp->segments[fp->count++] = project_segment(a, b, face);
                }
            }
        } else if (edges[i].count > 2) {
            printf("m4_overused_edge case=%d\n", case_index);
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

static int validate_m4_strips(void) {
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
                    if (build_m4_fingerprints(
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

    printf(
        "m6 m4 seams fields=%d seeds=%d grid=%d builds=%d shared_faces=%d failures=%d total_vertices=%d total_triangles=%d\n",
        FIELD_COUNT,
        SEED_COUNT,
        GRID_SIZE,
        builds,
        shared_faces,
        failures,
        vertex_total,
        triangle_total);
    return failures == 0 ? 0 : 1;
}

static int compare_default_and_m4(void) {
    int case_index;
    int default_failures = 0;
    int m4_failures = 0;
    int count_differences = 0;
    int default_triangles = 0;
    int m4_triangles = 0;
    int default_vertices = 0;
    int m4_vertices = 0;

    for (case_index = 0; case_index < (int)OTC_M4_CASE_COUNT; ++case_index) {
        float default_samples[TV_TRANSITION_SAMPLE_COUNT];
        float m4_samples[TV_M4_TRANSITION_SAMPLE_COUNT];
        TvVec3 default_vertices_buf[TV_TRANSITION_MAX_VERTICES];
        TvTriangle default_triangles_buf[TV_TRANSITION_MAX_TRIANGLES];
        TvVec3 m4_vertices_buf[TV_M4_TRANSITION_MAX_VERTICES];
        TvTriangle m4_triangles_buf[TV_M4_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo default_info;
        TvBuildInfo m4_info;

        fill_default_samples_from_case(case_index, default_samples);
        fill_m4_samples_from_case(case_index, m4_samples);

        default_info = tv_build_transition_cell(
            default_samples,
            0.0f,
            (TvVec3){0.0f, 0.0f, 0.0f},
            (TvVec3){1.0f, 1.0f, 1.0f},
            default_vertices_buf,
            TV_TRANSITION_MAX_VERTICES,
            default_triangles_buf,
            TV_TRANSITION_MAX_TRIANGLES);
        m4_info = tv_m4_build_transition_cell_candidate(
            m4_samples,
            0.0f,
            (TvVec3){0.0f, 0.0f, 0.0f},
            (TvVec3){1.0f, 1.0f, 1.0f},
            m4_vertices_buf,
            TV_M4_TRANSITION_MAX_VERTICES,
            m4_triangles_buf,
            TV_M4_TRANSITION_MAX_TRIANGLES);

        if (default_info.result != TV_OK || default_info.case_index != case_index) {
            ++default_failures;
            continue;
        }
        if (m4_info.result != TV_OK || m4_info.case_index != case_index) {
            ++m4_failures;
            continue;
        }

        default_vertices += default_info.vertex_count;
        default_triangles += default_info.triangle_count;
        m4_vertices += m4_info.vertex_count;
        m4_triangles += m4_info.triangle_count;
        if (default_info.vertex_count != m4_info.vertex_count
            || default_info.triangle_count != m4_info.triangle_count) {
            ++count_differences;
        }
    }

    printf(
        "m6 default comparison cases=%u default_failures=%d m4_failures=%d count_differences=%d default_vertices=%d default_triangles=%d m4_vertices=%d m4_triangles=%d structurally_distinct=%d\n",
        OTC_M4_CASE_COUNT,
        default_failures,
        m4_failures,
        count_differences,
        default_vertices,
        default_triangles,
        m4_vertices,
        m4_triangles,
        count_differences > 0 ? 1 : 0);

    return default_failures == 0 && m4_failures == 0 && count_differences > 0 ? 0 : 1;
}

int main(void) {
    if (validate_m4_strips() != 0) {
        return 1;
    }
    if (compare_default_and_m4() != 0) {
        return 1;
    }
    return 0;
}
