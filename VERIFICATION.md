# Executed verification

19 October 2026, Windows, Python 3.11.9, Node 22.18.0. Localhost only. This document distinguishes automated checks from browser observations.

## Automated
- Final backend full suite: **29 passed**, including 26 deterministic checks, two actual-model integration checks and a fresh Alembic upgrade/downgrade/upgrade test (75.08s).
- Actual models: dimension/unit norm/similarity ordering and sigmoid range verified. Real cross-encoder merge at strict >0.92 verified using an intentionally fragmented identical short complaint pair; 2 integration tests passed. Longer paraphrases may fall below the default threshold; this is documented, not hidden by mocked integration results.
- Final frontend suite: **7 passed** (2.17s). Form behavior with mocked network/map fixtures: successful reference, denied location/manual fallback, unresolved location rejection, three map modes, region drill-down, combined date/geography/category filters, empty data and service-error retry, 123,456,789-report formatting and a 3,000-character complaint.
- Final frontend production build: **passed**, including TypeScript and bundled MapLibre worker. MapLibre remains a large JavaScript dependency; Vite reports a chunk-size advisory (not a build failure).
- Final npm security audit: **0 vulnerabilities**. Dependencies were updated after installation to address reported MapLibre/Vitest issues.
- Boundary import: 36 state/UT, 641 district source records, 4,095 identified Assembly constituencies; 7 geometry repairs, 53 dissolved multipart duplicates, 34 unnamed/zero-code Assembly fragments excluded; no orphaned geographic parents.
- Real demo pipeline: 56 complaints, eight states, 11 active semantic categories. No manually supplied category IDs.

## Live end-to-end
A fictional browser submission at 12.9716,77.5946 resolved to Shivajinagar Assembly / Bangalore district / Karnataka. The form returned reference `7ce6822b-c7f7-4347-95b6-f5e8fd4cc5ca` immediately. The serialized worker produced a 384-dimensional local model embedding and assigned an existing lighting concern cluster. SQLite, map and analytics totals agreed. The fixture was marked fictional/removable, bringing this checkout to 57 demo reports.

`scripts/smoke_test.py` verified ten public endpoints return 200, no private field names/values appear, public point coordinates differ from submitted GPS, and combined state/district/Assembly/category filters agree between records and overview. The result is saved locally in `outputs/smoke-test.json`.

## Visual critique and fixes
- First browser render revealed MapLibre 6's worker was not bundled by default. Fixed with the official Vite `?worker&url` entry and `setWorkerUrl`; actual state polygons now render.
- Initial narrow-layout category search collapsed to zero width. Gave it an explicit flexible row, preserved search at tablet widths, and verified its visible input.
- Desktop-to-mobile map resizing retained an excessively close camera. Track the current geographic bounds and refit on width changes; preserve panning during background data refresh.
- Zero-data region legend misleadingly ran from one report to zero. Replaced it with an explicit no-reports state.
- Reduced chart animation to 240ms, increased small reading-panel text and added accessible paginated records below Individual map mode.
- Prevented background refreshes from repeatedly resetting the map camera. Districts and Assemblies remain independent filters.
- Disabled access logs in the documented launcher so geographic-resolution URLs do not log precise locations.
- Date filters/timeline buckets now consistently use Asia/Kolkata calendar days.

## Responsive review
Actual browser inspection completed at **390, 768, 1440 and 1920** widths for the three main pages. PNGs for each page/width are saved in `outputs/screenshots/`, plus confirmation, Assembly heatmap, empty date range, sparse category view and long state-name views. No page-level horizontal overflow was found at the inspected widths; the record table intentionally scrolls on narrow screens. The 390px atlas now shows the full India geometry and a visible category search. Long state names wrap in the reading panel. The 1920px sparse dashboard correctly reports one complaint after combining Karnataka with the generated drinking-water category; the future-date empty view reports zero in-period complaints and a zero-baseline chart.

Browser-tested actions: manual coordinates resolve to actual district/Assembly, submission confirmation, state/district/Assembly selection, all three map modes, independent category filtering, filter reset, category exploration/records, and responsive resizing. Date-range deep links were verified in the browser; date-input change events and combined filter state are covered by the frontend suite. Geolocation denial is deterministically simulated in the frontend suite; no real device location permission was granted. Large totals and very long input were tested with automated fixtures; they were not inserted as live complaint counts.

MapLibre emitted fit-bounds warnings during intermediate narrow resizing. Lowered the minimum zoom and guarded transient small dimensions; rendered views fit correctly. No new JavaScript errors were observed after fixing the worker integration. Earlier console worker failures were from the pre-fix build.

## Local operation and cleanup
The one-command `scripts/dev.py` launcher was executed: frontend returned HTTP 200 and backend health returned `ok=true` with geography installed. Its stop path released both localhost ports. Temporary QA services were stopped after verification; run the launcher to reopen the application.

Demo removal was executed against `.cache/removal-check.db`, a copied database containing one fixture marked as a genuine report. Removal preserved that report, recalculated its cluster to one member, retired empty clusters and removed all demo rows. The original database retained all 57 fictional reports.
