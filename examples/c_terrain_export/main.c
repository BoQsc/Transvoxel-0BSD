/* SPDX-License-Identifier: 0BSD */
#include <stdio.h>
#include "transvoxel.h"

#ifdef TV_EXAMPLE_USE_M4_BACKEND_CANDIDATE
#include "transvoxel_m4_backend.h"
#endif

/*
   Chunk + LOD seam OBJ example.

   This is still a small example, not a complete terrain engine. Its purpose is
   to show the normal core call pattern in one engine-independent C file:

     high LOD regular cells | transition strip | low LOD regular cells

   The OBJ uses separate groups/materials so the pieces are easy to inspect in
   Blender, MeshLab, Godot, or any other OBJ viewer.

   Negative scalar values are solid. Zero is the surface.
*/

typedef struct ObjStats {
    int vertex_index;
    int high_vertices;
    int high_triangles;
    int transition_vertices;
    int transition_triangles;
    int low_vertices;
    int low_triangles;
} ObjStats;

static float field(TvVec3 p) {
    /* A smooth hill/ridge that crosses the artificial LOD boundary. This avoids
       a flat debug plane while keeping the example deterministic and dependency-free. */
    float dx = p.x - 4.0f;
    float dz = p.z - 3.0f;
    float ridge = 1.55f - 0.055f * dx * dx - 0.090f * dz * dz + 0.10f * (p.x - p.z);
    return p.y - ridge;
}

static TvVec3 add3(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x + b.x;
    out.y = a.y + b.y;
    out.z = a.z + b.z;
    return out;
}

static TvVec3 mul3(TvVec3 a, TvVec3 b) {
    TvVec3 out;
    out.x = a.x * b.x;
    out.y = a.y * b.y;
    out.z = a.z * b.z;
    return out;
}

static TvVec3 sample_world(TvVec3 origin, TvVec3 scale, TvVec3 local) {
    return add3(origin, mul3(local, scale));
}

static const char *transition_backend_name(void) {
#ifdef TV_EXAMPLE_USE_M4_BACKEND_CANDIDATE
    return "m4_callback_adapter";
#else
    return "default_clean_room_m4";
#endif
}

static int install_transition_backend(void) {
#ifdef TV_EXAMPLE_USE_M4_BACKEND_CANDIDATE
    return tv_install_m4_transition_backend_candidate();
#else
    return TV_OK;
#endif
}

static void uninstall_transition_backend(void) {
#ifdef TV_EXAMPLE_USE_M4_BACKEND_CANDIDATE
    tv_uninstall_m4_transition_backend_candidate();
#endif
}

static void write_mtl(void) {
    FILE *f = fopen("terrain_lod_seam.mtl", "w");
    if (!f) {
        printf("warning: failed to write terrain_lod_seam.mtl\n");
        return;
    }
    fprintf(f, "# Materials for terrain_lod_seam.obj\n");
    fprintf(f, "newmtl high_lod0\nKd 0.20 0.70 0.30\nKa 0.02 0.07 0.03\n\n");
    fprintf(f, "newmtl transition\nKd 1.00 0.55 0.10\nKa 0.10 0.05 0.01\n\n");
    fprintf(f, "newmtl low_lod1\nKd 0.25 0.45 1.00\nKa 0.02 0.04 0.10\n\n");
    fclose(f);
}

static void write_triangle_obj(FILE *f, ObjStats *stats, const char *part, const TvVec3 *vertices, const TvTriangle *triangles, int tri_count) {
    int i;
    for (i = 0; i < tri_count; ++i) {
        TvVec3 a = vertices[triangles[i].a];
        TvVec3 b = vertices[triangles[i].b];
        TvVec3 c = vertices[triangles[i].c];
        fprintf(f, "v %.6f %.6f %.6f\n", a.x, a.y, a.z);
        fprintf(f, "v %.6f %.6f %.6f\n", b.x, b.y, b.z);
        fprintf(f, "v %.6f %.6f %.6f\n", c.x, c.y, c.z);
        fprintf(f, "f %d %d %d\n", stats->vertex_index, stats->vertex_index + 1, stats->vertex_index + 2);
        stats->vertex_index += 3;
    }

    if (part[0] == 'h') {
        stats->high_triangles += tri_count;
        stats->high_vertices += tri_count * 3;
    } else if (part[0] == 't') {
        stats->transition_triangles += tri_count;
        stats->transition_vertices += tri_count * 3;
    } else {
        stats->low_triangles += tri_count;
        stats->low_vertices += tri_count * 3;
    }
}

static int emit_regular_cell(FILE *f, ObjStats *stats, const char *part, TvVec3 origin, TvVec3 scale) {
    float samples[TV_REGULAR_SAMPLE_COUNT];
    TvVec3 vertices[TV_REGULAR_MAX_VERTICES];
    TvTriangle triangles[TV_REGULAR_MAX_TRIANGLES];
    TvBuildInfo info;
    int i;

    for (i = 0; i < TV_REGULAR_SAMPLE_COUNT; ++i) {
        samples[i] = field(sample_world(origin, scale, tv_regular_sample_position(i)));
    }

    info = tv_build_regular_cell(
        samples,
        0.0f,
        origin,
        scale,
        vertices,
        TV_REGULAR_MAX_VERTICES,
        triangles,
        TV_REGULAR_MAX_TRIANGLES);

    if (info.result != TV_OK) {
        return info.result;
    }

    write_triangle_obj(f, stats, part, vertices, triangles, info.triangle_count);
    return TV_OK;
}

static int emit_transition_cell(FILE *f, ObjStats *stats, TvVec3 origin, TvVec3 scale) {
    float samples[TV_TRANSITION_SAMPLE_COUNT];
    TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
    TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
    TvBuildInfo info;
    int i;

    for (i = 0; i < TV_TRANSITION_SAMPLE_COUNT; ++i) {
        samples[i] = field(sample_world(origin, scale, tv_transition_sample_position(i)));
    }

    /* The public helper fills the derived coarse-side samples using the same
       conservative transition boundary contract as the proof suite. Engines
       with their own coarse voxel samples can fill all 14 samples explicitly. */
    tv_transition_fill_derived_samples(samples);

    info = tv_build_transition_cell(
        samples,
        0.0f,
        origin,
        scale,
        vertices,
        TV_TRANSITION_MAX_VERTICES,
        triangles,
        TV_TRANSITION_MAX_TRIANGLES);

    if (info.result != TV_OK) {
        return info.result;
    }

    write_triangle_obj(f, stats, "transition", vertices, triangles, info.triangle_count);
    return TV_OK;
}

static int emit_high_lod_chunk(FILE *f, ObjStats *stats) {
    int x, y, z;
    int rc;
    fprintf(f, "\no high_lod0_regular_cells\nusemtl high_lod0\n");

    for (z = 0; z < 4; ++z) {
        for (y = 0; y < 3; ++y) {
            for (x = 0; x < 4; ++x) {
                rc = emit_regular_cell(f, stats, "high", tv_vec3((float)x, (float)y, (float)z), tv_vec3(1.0f, 1.0f, 1.0f));
                if (rc != TV_OK) return rc;
            }
        }
    }
    return TV_OK;
}

static int emit_transition_strip(FILE *f, ObjStats *stats) {
    int y, z;
    int rc;
    fprintf(f, "\no transition_strip_between_lod0_and_lod1\nusemtl transition\n");

    /* Transition cells cover a 2x2 high-resolution face footprint. Place a
       small strip beside the high-LOD chunk so the OBJ reads left-to-right as:
       green high LOD -> orange transition -> blue low LOD. */
    for (z = 0; z < 2; ++z) {
        for (y = 0; y < 2; ++y) {
            rc = emit_transition_cell(f, stats, tv_vec3(4.0f, (float)y * 2.0f, (float)z * 2.0f), tv_vec3(1.0f, 1.0f, 1.0f));
            if (rc != TV_OK) return rc;
        }
    }
    return TV_OK;
}

static int emit_low_lod_chunk(FILE *f, ObjStats *stats) {
    int x, y, z;
    int rc;
    fprintf(f, "\no low_lod1_regular_cells_scale_2\nusemtl low_lod1\n");

    for (z = 0; z < 2; ++z) {
        for (y = 0; y < 2; ++y) {
            for (x = 0; x < 2; ++x) {
                rc = emit_regular_cell(f, stats, "low", tv_vec3(6.0f + (float)x * 2.0f, (float)y * 2.0f, (float)z * 2.0f), tv_vec3(2.0f, 2.0f, 2.0f));
                if (rc != TV_OK) return rc;
            }
        }
    }
    return TV_OK;
}

static void write_report(const ObjStats *stats) {
    FILE *f = fopen("terrain_lod_seam_report.txt", "w");
    if (!f) {
        printf("warning: failed to write terrain_lod_seam_report.txt\n");
        return;
    }
    fprintf(f, "Transvoxel 0BSD C terrain export example\n");
    fprintf(f, "=======================================\n\n");
    fprintf(f, "Output OBJ: terrain_lod_seam.obj\n");
    fprintf(f, "Output MTL: terrain_lod_seam.mtl\n\n");
    fprintf(f, "Transition backend: %s\n\n", transition_backend_name());
    fprintf(f, "Groups/materials:\n");
    fprintf(f, "  high_lod0_regular_cells          green, regular cells at scale 1\n");
    fprintf(f, "  transition_strip_between_lod0_and_lod1  orange, transition cells\n");
    fprintf(f, "  low_lod1_regular_cells_scale_2   blue, regular cells at scale 2\n\n");
    fprintf(f, "Triangle counts:\n");
    fprintf(f, "  high_lod0:   %d triangles, %d OBJ vertices\n", stats->high_triangles, stats->high_vertices);
    fprintf(f, "  transition:  %d triangles, %d OBJ vertices\n", stats->transition_triangles, stats->transition_vertices);
    fprintf(f, "  low_lod1:    %d triangles, %d OBJ vertices\n", stats->low_triangles, stats->low_vertices);
    fprintf(f, "  total:       %d triangles, %d OBJ vertices\n\n",
        stats->high_triangles + stats->transition_triangles + stats->low_triangles,
        stats->high_vertices + stats->transition_vertices + stats->low_vertices);
    fprintf(f, "This example demonstrates the public C call pattern. It is not a full terrain engine,\n");
    fprintf(f, "streaming system, collision system, or official Transvoxel.cpp equivalence proof.\n");
    fclose(f);
}

int main(void) {
    FILE *f;
    ObjStats stats;
    int rc;

    stats.vertex_index = 1;
    stats.high_vertices = 0;
    stats.high_triangles = 0;
    stats.transition_vertices = 0;
    stats.transition_triangles = 0;
    stats.low_vertices = 0;
    stats.low_triangles = 0;

    write_mtl();

    rc = install_transition_backend();
    if (rc != TV_OK) {
        printf("transition backend install failed result=%d\n", rc);
        return 1;
    }

    f = fopen("terrain_lod_seam.obj", "w");
    if (!f) {
        printf("failed to open terrain_lod_seam.obj\n");
        uninstall_transition_backend();
        return 1;
    }

    fprintf(f, "# Generated by Transvoxel 0BSD examples/c_terrain_export\n");
    fprintf(f, "# Green high LOD regular cells, orange transition strip, blue low LOD regular cells.\n");
    fprintf(f, "# Vertices are intentionally duplicated for readability.\n");
    fprintf(f, "# Transition backend: %s\n", transition_backend_name());
    fprintf(f, "mtllib terrain_lod_seam.mtl\n");

    rc = emit_high_lod_chunk(f, &stats);
    if (rc != TV_OK) {
        fclose(f);
        printf("high LOD chunk failed result=%d\n", rc);
        uninstall_transition_backend();
        return 1;
    }

    rc = emit_transition_strip(f, &stats);
    if (rc != TV_OK) {
        fclose(f);
        printf("transition strip failed result=%d\n", rc);
        uninstall_transition_backend();
        return 1;
    }

    rc = emit_low_lod_chunk(f, &stats);
    if (rc != TV_OK) {
        fclose(f);
        printf("low LOD chunk failed result=%d\n", rc);
        uninstall_transition_backend();
        return 1;
    }

    fclose(f);
    write_report(&stats);
    uninstall_transition_backend();

    printf("wrote terrain_lod_seam.obj\n");
    printf("wrote terrain_lod_seam.mtl\n");
    printf("wrote terrain_lod_seam_report.txt\n");
    printf("transition backend=%s\n", transition_backend_name());
    printf("high_lod0 triangles=%d transition triangles=%d low_lod1 triangles=%d\n",
        stats.high_triangles, stats.transition_triangles, stats.low_triangles);
    return 0;
}
