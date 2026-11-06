# Story Architect

Write a **presentation argument**, not a document pasted onto slides.

1. Extract audience, desired audience action, presentation duration, non-negotiable content, accessibility and language.
2. Compile an evidence ledger: claim, exact number, scope, date, source URL/file/page, confidence, and demo/estimate status.
3. Order the narrative: context → specific friction → why it matters → proposed response → fair options → evidence → boundaries → decision.
4. Title each slide with the conclusion the slide supports; at most one central claim. If the slide contains two claims, split it.
5. For each slide specify: type, title, supporting points, evidence, visualization and speaking note; do not overpopulate slide text.
6. Label simulated data, estimated costs, benchmark proxies and limitations as such; keep actual research separate.
7. Use `python scripts/studio.py validate <deck> --strict` and resolve errors before rendering.

## Exit criteria

A reviewer can summarize the main argument without speaker notes; all quantitative claims have explicit citations or are visibly labelled illustrative. If citations are missing, do not invent them; record unresolved evidence in the outline.
