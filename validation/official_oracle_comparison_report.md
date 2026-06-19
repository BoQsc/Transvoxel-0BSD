# M23 Official Oracle Comparison

Status: `PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY`

The external MIT file is used only as an isolated comparison oracle. No oracle arrays are emitted or packaged in the 0BSD repository.

## Oracle

- Origin: `https://github.com/EricLengyel/Transvoxel.git`
- Commit: `51a494f03c5b024cd153b596bcc7152eb3cc93a6`
- SHA-256: `83a5511346b54c42e4e66dec916d3971c92f4fbda1c7878cbad5901a820dcab4`

## Exhaustive results

- Regular cases compared: `256`
- Regular unoriented topology matches: `86`
- Regular oriented topology matches: `86`
- Transition cases compared: `512`
- Transition unoriented topology matches: `139`
- Transition oriented topology matches: `139`

## Exact replacement decision

- Exact topology ready: `False`
- Exact table layout ready: `False`
- Exact replacement ready: `False`

The next milestone must change the implementation, not the claim wording: converge regular and transition case topology on the oracle before starting unchanged-consumer integration tests.
