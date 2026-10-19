# Civic Atlas tasks

Derived from [plan.md](plan.md). Check items only after implementation and verification.

## 1. Foundation
- [ ] Initialize standalone Git monorepo without modifying the existing application.
- [ ] Scaffold Vite/React/TypeScript and FastAPI packages, configuration, dependency locks and local commands.
- [ ] Add SQLite models, privacy boundaries, indexes, WAL/foreign keys and Alembic migration.

## 2. Design
- [ ] Write DESIGN.md: visual concept, tokens, typography, layouts, interaction/accessibility rules.
- [ ] Build shared responsive navigation, controls and feedback states.

## 3. Geography
- [ ] Verify source/license; pin data version and document vintage/coverage.
- [ ] Build reproducible geographic import and display simplification.
- [ ] Implement Shapely STRtree lookup, overlap diagnostics and geographic APIs.

## 4. Submission
- [ ] Validate email/text/coordinates; commit complaint and return reference immediately.
- [ ] Build geolocation, manual map placement, coverage feedback and confirmation UI.
- [ ] Build durable worker, startup recovery, bounded retries and local rate limiting.

## 5. Semantics
- [ ] Verify and document local model/scoring choices before implementation.
- [ ] Implement float32 vector interface and exact global assignment with inclusive threshold.
- [ ] Recompute full centroids/representatives and derive labels from content.
- [ ] Implement bounded cross-encoder candidate discovery and transactional/idempotent merges.
- [ ] Evaluate threshold examples and actual model integration.

## 6. Atlas
- [ ] Implement real state/district/Assembly layers, geographic navigation and keyboard alternatives.
- [ ] Implement heatmap, region and individual modes with truthful legends and selection.
- [ ] Add searchable semantic filters, summaries and safe complaint details.

## 7. Analytics
- [ ] Implement combined filters, metrics, category growth, geography, timelines and pagination.
- [ ] Build distinctive dashboard, category exploration and complaint records.

## 8. Quality
- [ ] Add and pass deterministic ML/merge/privacy/geography/API/recovery tests.
- [ ] Run actual local model integration and fictional demo generator through real pipeline.
- [ ] Verify frontend form, location denial, filters, modes, drill-down and errors.
- [ ] Inspect 390/768/1440/1920 layouts and empty/sparse/long-content states.

## 9. Polish and handoff
- [ ] Record design critique and fix observed visual/accessibility issues.
- [ ] Verify live submission → worker → categories/map/analytics.
- [ ] Document setup/run/demo/removal, tests, limitations and future service replacements.
- [ ] Commit the new repository and provide links and runnable local preview.
