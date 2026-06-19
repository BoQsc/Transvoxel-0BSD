# M27 Terminal Exact-0BSD Decision

Status: `TERMINAL_M27_EXACT_0BSD_REPLACEMENT_NOT_ACHIEVED`

- Exact 0BSD goal achieved: `False`
- Technical exact integration proven: `True`
- Independent regular exact matches: `86/256`
- Independent transition exact matches: `139/512`
- Oracle-calibrated regular exact matches: `256/256`
- Oracle-calibrated transition exact matches: `512/512`
- M24 regular rules with nonzero oracle selection: `170`
- M24 transition representative rules with nonzero oracle selection: `50`
- Roadmap terminal: `True`
- Next milestone: `NONE_TERMINAL`

The published rules constrain robust boundary connectivity but permit multiple legal interior triangulations. The independent deterministic 0BSD rule therefore does not reproduce every authored official interior. The exact M24-M26 candidate is technically proven, but it depends on selections calibrated against the MIT implementation and is explicitly MIT rather than 0BSD.

Terminal choices are: retain MIT for exact compatibility, use the functional non-exact 0BSD core, or obtain explicit permission. There is no automatic M28.

This is an engineering provenance decision, not legal advice.

No zip artifact is built.
