# Civic Atlas tasks

## Render deployment repair — 26 October 2026
- [x] Diagnose backend-only root 404 on the deployed main branch.
- [x] Add same-origin production frontend routes without hiding missing API/assets.
- [x] Add build-time frontend/geography/model preparation and runtime-only SQLite migration/import.
- [x] Verify page/asset/privacy regression tests and startup idempotency.
- [ ] Apply the tested fix and publish a reviewable branch.
- [ ] Deploy the branch on Render with root directory cleared and verify the public URL.

Render deployment is not complete until the last checkbox is verified against the live service.

Derived from [plan.md](plan.md). Check items only after implementation and verification.

## 1. Foundation
- [x] Initialize standalone Git monorepo without modifying the existing application.
- [x] Scaffold Vite/React/TypeScript and FastAPI packages, configuration, dependency locks and local commands.
- [x] Add SQLite models, privacy boundaries, indexes, WAL/foreign keys and Alembic migration.

## 2. Design
- [x] Write DESIGN.md: visual concept, tokens, typography, layouts, interaction/accessibility rules.
- [x] Build shared responsive navigation, controls and feedback states.

## 3. Geography
- [x] Verify source/license; pin data version and document vintage/coverage.
- [x] Build reproducible geographic import and display simplification.
- [x] Implement Shapely STRtree lookup, overlap diagnostics and geographic APIs.

## 4. Submission
- [x] Validate email/text/coordinates; commit complaint and return reference immediately.
- [x] Build geolocation, manual map placement, coverage feedback and confirmation UI.
- [x] Build durable worker, startup recovery, bounded retries and local rate limiting.

## 5. Semantics
- [x] Verify and document local model/scoring choices before implementation.
- [x] Implement float32 vector interface and exact global assignment with inclusive threshold.
- [x] Recompute full centroids/representatives and derive labels from content.
- [x] Implement bounded cross-encoder candidate discovery and transactional/idempotent merges.
- [x] Evaluate threshold examples and actual model integration.

## 6. Atlas
- [x] Implement real state/district/Assembly layers, geographic navigation and keyboard alternatives.
- [x] Implement heatmap, region and individual modes with truthful legends and selection.
- [x] Add searchable semantic filters, summaries and safe complaint details.

## 7. Analytics
- [x] Implement combined filters, metrics, category growth, geography, timelines and pagination.
- [x] Build distinctive dashboard, category exploration and complaint records.

## 8. Quality
- [x] Add and pass deterministic ML/merge/privacy/geography/API/recovery tests.
- [x] Run actual local model integration and fictional demo generator through real pipeline.
- [x] Verify frontend form, location denial, filters, modes, drill-down and errors.
- [x] Inspect 390/768/1440/1920 layouts and empty/sparse/long-content states.

## 9. Polish and handoff
- [x] Record design critique and fix observed visual/accessibility issues.
- [x] Verify live submission → worker → categories/map/analytics.
- [x] Document setup/run/demo/removal, tests, limitations and future service replacements.
- [x] Commit the new repository and provide links and runnable local preview.


Completed 19 October 2026. Evidence: VERIFICATION.md. Final result: 29 backend tests, 7 frontend tests, production build and npm audit pass; actual-model demo and live browser submission verified. Responsive screenshots are local in outputs/screenshots. Temporary preview servers were stopped; restart with the documented launcher.
