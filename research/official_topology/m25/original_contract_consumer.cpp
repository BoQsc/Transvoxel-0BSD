// SPDX-License-Identifier: 0BSD
#include <cstddef>
#include <cstdint>
#include <cstdio>

#include "Transvoxel.cpp"

static int regular_sign(int case_index, int sample_id) {
    return (case_index >> sample_id) & 1;
}

static int transition_sign(int case_index, int sample_id) {
    static const int sample_bits[9] = {0, 1, 2, 7, 8, 3, 6, 5, 4};
    static const int half_sources[4] = {0, 2, 6, 8};
    if (sample_id < 9) {
        return (case_index >> sample_bits[sample_id]) & 1;
    }
    return transition_sign(case_index, half_sources[sample_id - 9]);
}

static unsigned short expected_regular_code(int a, int b) {
    static const int positions[8][3] = {
        {0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {1, 1, 0},
        {0, 0, 1}, {1, 0, 1}, {0, 1, 1}, {1, 1, 1},
    };
    static const int direction_bits[3] = {1, 2, 4};
    static const int axis_indexes[3] = {2, 1, 3};
    int axis = -1;
    int fixed_all_max = 1;
    int direction = 0;
    for (int i = 0; i < 3; ++i) {
        if (positions[a][i] != positions[b][i]) {
            axis = i;
        }
    }
    if (axis < 0) return 0;
    for (int i = 0; i < 3; ++i) {
        if (i == axis) continue;
        if (positions[a][i] == 0) {
            direction |= direction_bits[i];
            fixed_all_max = 0;
        }
    }
    if (fixed_all_max) direction = 8;
    return static_cast<unsigned short>(
        ((((direction << 4) | axis_indexes[axis]) << 8)
        | (a << 4) | b));
}

static unsigned short expected_transition_code(int a, int b) {
    static const int positions[13][3] = {
        {0, 0, 0}, {1, 0, 0}, {2, 0, 0},
        {0, 1, 0}, {1, 1, 0}, {2, 1, 0},
        {0, 2, 0}, {1, 2, 0}, {2, 2, 0},
        {0, 0, 1}, {2, 0, 1}, {0, 2, 1}, {2, 2, 1},
    };
    const bool horizontal = positions[a][1] == positions[b][1];
    const bool half = positions[a][2] == 1;
    int direction;
    int index;
    if (horizontal) {
        const int coordinate = positions[a][1];
        direction = coordinate == 0 ? 2 : (coordinate == 2 ? 8 : 4);
        index = half ? 8 : (positions[a][0] == 0 ? 3 : 4);
    } else {
        const int coordinate = positions[a][0];
        direction = coordinate == 0 ? 1 : (coordinate == 2 ? 8 : 4);
        index = half ? 9 : (positions[a][1] == 0 ? 5 : 6);
    }
    return static_cast<unsigned short>(
        ((((direction << 4) | index) << 8) | (a << 4) | b));
}

int main() {
    static_assert(sizeof(regularCellClass) / sizeof(regularCellClass[0]) == 256);
    static_assert(sizeof(regularCellData) / sizeof(regularCellData[0]) == 16);
    static_assert(sizeof(regularVertexData) / sizeof(regularVertexData[0]) == 256);
    static_assert(sizeof(transitionCellClass) / sizeof(transitionCellClass[0]) == 512);
    static_assert(sizeof(transitionCellData) / sizeof(transitionCellData[0]) == 56);
    static_assert(sizeof(transitionCornerData) / sizeof(transitionCornerData[0]) == 13);
    static_assert(sizeof(transitionVertexData) / sizeof(transitionVertexData[0]) == 512);

    int failures = 0;
    int regular_vertices = 0;
    int regular_triangles = 0;
    int transition_vertices = 0;
    int transition_triangles = 0;

    for (int case_index = 0; case_index < 256; ++case_index) {
        const int class_index = regularCellClass[case_index];
        if (class_index >= 16) {
            ++failures;
            continue;
        }
        const RegularCellData &data = regularCellData[class_index];
        const int vertex_count = static_cast<int>(data.GetVertexCount());
        const int triangle_count = static_cast<int>(data.GetTriangleCount());
        regular_vertices += vertex_count;
        regular_triangles += triangle_count;
        for (int i = 0; i < vertex_count; ++i) {
            const unsigned short code = regularVertexData[case_index][i];
            const int a = (code >> 4) & 0x0F;
            const int b = code & 0x0F;
            if (a >= b || regular_sign(case_index, a) == regular_sign(case_index, b)) {
                ++failures;
            }
            if (code != expected_regular_code(a, b)) {
                ++failures;
            }
        }
        for (int i = 0; i < triangle_count * 3; ++i) {
            if (data.vertexIndex[i] >= vertex_count) {
                ++failures;
            }
        }
    }

    for (int case_index = 0; case_index < 512; ++case_index) {
        const int class_code = transitionCellClass[case_index];
        const int class_index = class_code & 0x7F;
        if (class_index >= 56) {
            ++failures;
            continue;
        }
        const TransitionCellData &data = transitionCellData[class_index];
        const int vertex_count = static_cast<int>(data.GetVertexCount());
        const int triangle_count = static_cast<int>(data.GetTriangleCount());
        transition_vertices += vertex_count;
        transition_triangles += triangle_count;
        for (int i = 0; i < vertex_count; ++i) {
            const unsigned short code = transitionVertexData[case_index][i];
            const int a = (code >> 4) & 0x0F;
            const int b = code & 0x0F;
            if (a >= b || transition_sign(case_index, a) == transition_sign(case_index, b)) {
                ++failures;
            }
            if (code != expected_transition_code(a, b)) {
                ++failures;
            }
        }
        for (int i = 0; i < triangle_count * 3; ++i) {
            if (data.vertexIndex[i] >= vertex_count) {
                ++failures;
            }
        }
    }

    if (regular_vertices != 1536 || regular_triangles != 820) ++failures;
    if (transition_vertices != 4096 || transition_triangles != 2640) ++failures;

    std::printf(
        "m25 original contract regular_vertices=%d regular_triangles=%d "
        "transition_vertices=%d transition_triangles=%d failures=%d\n",
        regular_vertices,
        regular_triangles,
        transition_vertices,
        transition_triangles,
        failures);
    return failures == 0 ? 0 : 1;
}
