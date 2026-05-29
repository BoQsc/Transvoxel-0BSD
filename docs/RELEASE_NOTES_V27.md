# v27 Release Notes

v27 fixes the final report ordering for `validation/external_alignment_report.json`.

In v26 the strict correctness audit was rerun after Godot seam metrics and
auto-interaction, but the external alignment report could still remain from the
earlier Python proof-suite pass and therefore show auto-interaction / production
-gate checks as `SKIPPED` in the upload bundle.

v27 reruns `tools/external_alignment_report.py` after the final production gate
in full mode, so `SEND_TO_CHATGPT.zip` reflects the complete run:

- production gate: PASS
- automated dig/add interaction: PASS
- full production gate alignment: PASS

No core table or algorithm behavior changed.
