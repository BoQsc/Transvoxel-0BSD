# Self-Intersection Audit

Status: **PASS**

## regular

Cases: `256`
Triangle pairs checked: `7008`
Failures: `0`

## transition

Cases: `512`
Triangle pairs checked: `152352`
Failures: `0`

## Limitations

- This is a conservative generated-case geometry audit, not a formal computational geometry proof for all floating point interpolation values.
- It uses midpoint edge vertices because the current generated tables store sample-edge references, not arbitrary density interpolation positions.
