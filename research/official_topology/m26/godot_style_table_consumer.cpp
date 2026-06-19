#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "meshers/transvoxel/transvoxel_tables.cpp"

namespace tables = zylann::voxel::transvoxel::tables;

static std::string hex_code(unsigned int value, int width) {
	char buffer[16];
	std::snprintf(buffer, sizeof(buffer), "%0*X", width, value);
	return buffer;
}

static std::string canonical_oriented_triangle(
		unsigned int a, unsigned int b, unsigned int c) {
	const std::string rotations[3] = {
		hex_code(a, 2) + hex_code(b, 2) + hex_code(c, 2),
		hex_code(b, 2) + hex_code(c, 2) + hex_code(a, 2),
		hex_code(c, 2) + hex_code(a, 2) + hex_code(b, 2),
	};
	return *std::min_element(rotations, rotations + 3);
}

static std::string join_sorted(std::vector<std::string> values) {
	std::sort(values.begin(), values.end());
	std::string result;
	for (size_t i = 0; i < values.size(); ++i) {
		if (i != 0) {
			result += ",";
		}
		result += values[i];
	}
	return result;
}

static std::string regular_record(unsigned int case_index) {
	const unsigned int class_index = tables::get_regular_cell_class(case_index);
	const tables::RegularCellData &data =
			tables::get_regular_cell_data(class_index);
	const unsigned int vertex_count = data.GetVertexCount();
	const unsigned int triangle_count = data.GetTriangleCount();
	std::vector<unsigned int> edge_codes;
	std::vector<unsigned int> packed_codes;
	for (unsigned int i = 0; i < vertex_count; ++i) {
		const unsigned int code =
				tables::get_regular_vertex_data(case_index, i);
		edge_codes.push_back(code & 0xff);
		packed_codes.push_back(code);
	}
	std::vector<std::string> triangles;
	for (unsigned int i = 0; i < triangle_count; ++i) {
		const unsigned int base = i * 3;
		const unsigned int a = data.get_vertex_index(base);
		const unsigned int b = data.get_vertex_index(base + 1);
		const unsigned int c = data.get_vertex_index(base + 2);
		if (a >= vertex_count || b >= vertex_count || c >= vertex_count) {
			return "INVALID_INDEX";
		}
		triangles.push_back(canonical_oriented_triangle(
				edge_codes[a], edge_codes[b], edge_codes[c]));
	}
	std::sort(packed_codes.begin(), packed_codes.end());
	std::vector<std::string> packed;
	for (const unsigned int code : packed_codes) {
		packed.push_back(hex_code(code, 4));
	}
	return std::to_string(vertex_count) + "|" +
			std::to_string(triangle_count) + "|" +
			join_sorted(triangles) + "|" + join_sorted(packed);
}

static std::string transition_record(unsigned int case_index) {
	const unsigned int class_code =
			tables::get_transition_cell_class(case_index);
	const bool flip = (class_code & 0x80) != 0;
	const tables::TransitionCellData &data =
			tables::get_transition_cell_data(class_code & 0x7f);
	const unsigned int vertex_count = data.GetVertexCount();
	const unsigned int triangle_count = data.GetTriangleCount();
	std::vector<unsigned int> edge_codes;
	std::vector<unsigned int> packed_codes;
	for (unsigned int i = 0; i < vertex_count; ++i) {
		const unsigned int code =
				tables::get_transition_vertex_data(case_index, i);
		edge_codes.push_back(code & 0xff);
		packed_codes.push_back(code);
	}
	std::vector<std::string> triangles;
	for (unsigned int i = 0; i < triangle_count; ++i) {
		const unsigned int base = i * 3;
		unsigned int a = data.get_vertex_index(base);
		unsigned int b = data.get_vertex_index(base + 1);
		unsigned int c = data.get_vertex_index(base + 2);
		if (a >= vertex_count || b >= vertex_count || c >= vertex_count) {
			return "INVALID_INDEX";
		}
		if (flip) {
			std::swap(a, c);
		}
		triangles.push_back(canonical_oriented_triangle(
				edge_codes[a], edge_codes[b], edge_codes[c]));
	}
	std::sort(packed_codes.begin(), packed_codes.end());
	std::vector<std::string> packed;
	for (const unsigned int code : packed_codes) {
		packed.push_back(hex_code(code, 4));
	}
	return std::to_string(vertex_count) + "|" +
			std::to_string(triangle_count) + "|" +
			join_sorted(triangles) + "|" + join_sorted(packed);
}

int main() {
	static_assert(sizeof(tables::regularCellClass) /
					sizeof(tables::regularCellClass[0]) == 256);
	static_assert(sizeof(tables::regularCellData) /
					sizeof(tables::regularCellData[0]) == 16);
	static_assert(sizeof(tables::regularVertexData) /
					sizeof(tables::regularVertexData[0]) == 256);
	static_assert(sizeof(tables::transitionCellClass) /
					sizeof(tables::transitionCellClass[0]) == 512);
	static_assert(sizeof(tables::transitionCellData) /
					sizeof(tables::transitionCellData[0]) == 56);
	static_assert(sizeof(tables::transitionCornerData) /
					sizeof(tables::transitionCornerData[0]) == 13);
	static_assert(sizeof(tables::transitionVertexData) /
					sizeof(tables::transitionVertexData[0]) == 512);

	for (unsigned int i = 0; i < 256; ++i) {
		std::printf("R|%u|%s\n", i, regular_record(i).c_str());
	}
	for (unsigned int i = 0; i < 512; ++i) {
		std::printf("T|%u|%s\n", i, transition_record(i).c_str());
	}
	for (unsigned int i = 0; i < 13; ++i) {
		std::printf(
				"C|%u|%02X\n",
				i,
				static_cast<unsigned int>(
						tables::get_transition_corner_data(i)));
	}
	return 0;
}
