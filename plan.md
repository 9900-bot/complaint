# Civic Atlas — implementation plan

## Product and constraints
Build the supplied India Complaint Intelligence brief as a local-only monorepo, separate from the existing party website. Exactly three pages: India atlas, raise complaint, analytics. React/TypeScript/Vite, Tailwind, MapLibre; FastAPI/SQLAlchemy/Alembic/SQLite; local sentence-transformers and NumPy; Shapely spatial indexes. No accounts, paid APIs, cloud, containers, or distributed queues.

## Architecture
- Frontend calls explicit public REST schemas through a Vite localhost proxy. Geographic controls and semantic filters remain independent.
- SQLite is authoritative. Foreign keys, WAL, busy timeout, indexed filters, short sessions. Private email and coordinates never enter public response serializers.
- Submission commits before returning a reference. One durable polling worker recovers unfinished work on restart, retries with bounds, and serializes semantic changes.
- Separate model runtime, vector serialization, cluster service, label service, geography service, public queries, and worker orchestration.
- Bi-encoder: normalize original text minimally, use an exact global cosine comparison with all active centroids, assign when similarity >= membership threshold; otherwise create a cluster. Centroids represent every member.
- Cross-encoder: shortlist close cluster centroids only for merging, compare representative texts, merge transactionally only when score > 0.92. Keep the oldest canonical ID, record history, re-evaluate after changes, bound iterations.
- Default models: all-MiniLM-L6-v2 (384 dimensions, English baseline) and stsb-TinyBERT-L4 (bounded STS similarity, conservative threshold; not calibrated probability). Verify model cards and actual behavior before finalizing. No untested multilingual claims.
- Geography: verify open source licenses and pinned versions; import real state, district, and Assembly polygons. Districts and constituencies independently reference states. Preserve full resolution geometry for private spatial lookup, simplify display geometry. Record missing coverage and ambiguities; never synthesize boundaries.
- Public positions use stable 0.05-degree grid centers. Heatmap aggregates these same cells, including bounding-box filtering, so repeated requests cannot reconstruct exact coordinates.

## Ordered phases
1. Foundation: initialize independent Git repository, frontend/backend dependencies, schemas, migrations, local scripts.
2. Design: document tokens and three compositions in DESIGN.md before UI code. Editorial ivory interface, dark map, Newsreader/IBM Plex Sans, viridian and copper accents. Map dominates atlas.
3. Geography: identify, pin, download, validate, import datasets; STRtree lookup, stable IDs, metadata and GeoJSON endpoints.
4. Submission: accessible form, geolocation/manual placement, validation, persistence, durable worker.
5. ML: implement local runtimes, vectors, exact assignment, complete centroids, transactional merges, content-derived labels, threshold evaluation.
6. Atlas: real map, three modes, region drill-down, independent searchable categories, complaint inspection and empty/error states.
7. Analytics: combined date/geography/category filters, daily/weekly timelines, category growth and exploration, geographic rankings and paginated records.
8. Quality: deterministic semantic/backend tests; actual-model integration; fictional demo via the real pipeline; frontend interactions and responsive browser checks.
9. Polish: explicit critique, correct observed problems, verify end-to-end, document run commands, sources, limits and future replacement boundaries.

## Acceptance and evidence
Track work in tasks.md. Record actual test results and screenshots; do not mark unexecuted checks complete. Verify privacy on every public endpoint, geographic resolution from actual polygons, membership and merge invariants, restart recovery, submission-to-analytics flow, and empty/sparse/long-content layouts at 390/768/1440/1920 widths. Models and boundaries download during setup, then runtime works locally with no required external map tiles.

## Risks and honest limits
Boundary vintages may differ and may not reflect recent administrative changes or official territorial positions. Coverage must be visible in documentation. English models are an explicit baseline; short texts and mixed issues may cluster imperfectly. Cross-encoder scores are model-dependent similarities, not calibrated probabilities. Local SQLite includes personal data and must not be committed or published. This phase targets one server process and 1–2 users.
