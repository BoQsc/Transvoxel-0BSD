# Topology Signature Analysis

Status: **RESEARCH_PASS_TOPOLOGY_CLASSES_DERIVED_OFFICIAL_EQUIVALENCE_NOT_PROVEN**

Official class target: `73`

## Class counts

- `exact_sample_edge_topology`: `256` classes
- `d4_sample_edge_topology`: `201` classes
- `d4_complement_sample_edge_topology`: `201` classes
- `graph_only_topology_coarse`: `484` classes
- `raw_d4_complement_orbit`: `51` classes

## Closest count

- `raw_d4_complement_orbit`: `51` classes, distance `22` from 73

## Interpretation

- This project's generated topology classes do not prove official Transvoxel 73-class equivalence.
- If none of the topology signature counts equals 73, the current tetrahedralized transition topology is structurally different from the official 73-class table design, or the official classes depend on a richer equivalence relation not represented by these signatures.
- Even if a count equaled 73, that would still be only a structural clue, not proof of matching official class IDs or triangle encodings.

## Limitations

- graph_only_topology is a coarse color-refinement signature, not a formal graph-isomorphism proof.
- sample-edge topology uses midpoint/sample-edge references from this generator, not arbitrary density interpolation positions.
- No official MIT table values are loaded, compared, or copied.
