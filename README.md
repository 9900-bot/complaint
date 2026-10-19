# Civic Atlas

An India complaint intelligence application for localhost: report a text complaint, explore shared concerns on a real map, and read category, geographic and time-based analytics. Three pages, no accounts. Designed as a modern civic atlas with local fonts, warm reading surfaces and a dark geographic canvas.

Implementation follows [plan.md](plan.md) → [tasks.md](tasks.md). The original supplied specification is preserved in [BRIEF.md](BRIEF.md). This is a standalone local Git repository, separate from the existing party website. No cloud resources or remote repository are created.

## Quick start (Windows)

Prerequisites: Python **3.11**, Node.js **22+**, Git, and internet access for initial package/model/geography downloads. CPU inference is supported; no GPU, Docker or paid API is needed. Allow approximately 1–2 GB of local disk for the Python environment, models, packages and boundaries.

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
.\.venv\Scripts\python.exe scripts/dev.py
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8011/docs**. The launcher checks ports and stops both children on Ctrl+C. Port 8011 intentionally avoids another local service on 8000. Services bind only to loopback. Startup uses the installed Alembic schema; it does not silently recreate tables.

The current checkout has already been installed, migrated, populated with real boundaries, and seeded with fictional reports. The demo is optional and removable. A fresh install starts with zero complaints.

To run separately, use two terminals:

```powershell
# Backend, from repository root
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --workers 1 --no-access-log
```

```powershell
# Frontend, from repository root
Set-Location frontend
npm run dev
```

Use **one backend worker**. Access logging is disabled because the location-resolution query includes precise coordinates. Model cache files, raw boundaries, the generated geographic bundle, `.env`, SQLite and screenshots are ignored by Git. All normal runtime assets (fonts, map geometry and model weights) are local after setup. No external basemap tiles are required.

## Manual installation / macOS / Linux

```bash
python3.11 -m venv .venv
# Windows: .venv/Scripts/python.exe; macOS/Linux: .venv/bin/python
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci
cd ../backend
../.venv/bin/python -m alembic upgrade head
cd ..
.venv/bin/python scripts/prepare_geography.py
.venv/bin/python -c "import sys; sys.path.insert(0,'backend'); from app.ml import ModelRuntime; ModelRuntime().load(download=True)"
.venv/bin/python scripts/dev.py
```

The exact Python lock was verified on Windows/Python 3.11; other operating systems may require resolving from `backend/requirements.txt` for platform-compatible wheels. On Windows the setup script uses `py -3.11`. Existing checkouts should use their `.venv` Python rather than a global installation.

## Demo data

Stop the backend first, then run from the root:

```powershell
.\.venv\Scripts\python.exe scripts/demo.py --count 56
# Remove only explicitly tagged fictional data, retaining real submissions:
.\.venv\Scripts\python.exe scripts/demo.py --remove
```

Eight Indian cities, seven issue families, paraphrases, near-duplicates, same-issue/different-place and multi-issue examples. Every demo complaint runs through the **actual bi-encoder and cross-encoder pipeline**, with no manually assigned cluster IDs. A second seed run is refused until the existing demo is removed. Deletion refreshes surviving cluster centroids/counts/labels and retires empty clusters; historical merge records remain as an audit trail. The browser verification complaint is also tagged fictional and removable with this command.

## Architecture and behavior

- **Frontend:** React, TypeScript, Vite, Tailwind, MapLibre 6, Recharts and Lucide. Local Newsreader and IBM Plex Sans fonts. URL-backed filters, native keyboard-accessible region/category selectors, responsive charts, manual pin/coordinate entry, geolocation fallback, input validation and submission confirmation.
- **API:** FastAPI, explicit Pydantic public serializers, combined geographic/category/India-date filters, pagination and sort, bounded date ranges, rate-limited submission. Original text is rendered as text, never injected as HTML. Pending reports count in totals under “Uncategorised.”
- **Persistence:** SQLAlchemy, Alembic, SQLite, foreign keys, WAL and a 15-second busy timeout. Each complaint has one cluster reference, preventing duplicate membership. Sessions are short-lived and are never shared between threads.
- **Background work:** a single serialized polling thread uses durable pending/processing/completed/failed state in SQLite. Submission commits and returns immediately. Model inference runs outside the submission request. Restart recovers interrupted jobs, including interrupted final attempts. Retries back off and stop after three failures. After fixing missing model files, explicitly requeue failed jobs with `.\.venv\Scripts\python.exe scripts/retry_failed.py`. These states are internal reliability metadata and are not a user-facing complaint tracking system.
- **Clustering:** `ModelRuntime`, `SQLiteVectors`, `ClusterService` and `LabelService` separate inference, vectors, assignment/merge logic and content-derived labels. Exact global centroid comparison assigns on `cosine >= 0.62`. Normalized centroids and representatives reflect all current member embeddings.
- **Merging:** centroid shortlist only for merge discovery; actual cross-encoder comparisons require `score > 0.92`. Compare the representative pair plus the farthest member pair for larger clusters; refresh after every merge. Keep the oldest canonical ID, reassign members, retire source, refresh centroid/count/label and log history in one transaction. Bounded iterations and retry idempotency prevent blind transitive merging.

See [backend/MODELS.md](backend/MODELS.md) for pinned model revisions and score conventions. The models are **all-MiniLM-L6-v2** (384 dimensions) and **stsb-TinyBERT-L4** (explicit sigmoid STS similarity). Neither uses a paid inference service. Scores are not calibrated probabilities. The English example-pair evaluation is recorded in [backend/model-evaluation.json](backend/model-evaluation.json). The default is conservative: some paraphrases remain separate. Original-language submissions are accepted without translation; multilingual quality has not been validated. Generated TF-IDF phrase labels can be awkward and may change as membership changes; cluster IDs remain stable.

## Geography and privacy

Real **DataMeet Community Maps** data is pinned to commit `b3fbbde595310b397a55d718e0958ce249a4fa1f`. Imported: 36 states/UTs, 641 district records, 4,095 identified Assembly constituencies. Seven invalid geometries were repaired, 53 duplicate multipart records dissolved, and 34 unidentified Assembly fragments excluded. The district source includes a “Data Not Available” record; this is source metadata, not a current district. Source dates vary: the district data is Census 2011; several Assembly states are pre-delimitation. Names, positions, recent reorganizations and gaps require care. **These are exploratory boundaries, not an authoritative current electoral or legal map.** Never substitute Parliamentary for Assembly boundaries.

Districts and Assemblies independently link to states by polygon intersection; an Assembly can cross district boundaries. Shapely STRtrees resolve precise private coordinates against unsimplified geometry. On shared boundaries/overlaps, choose the smallest polygon then stable ID, and record ambiguity privately. Valid Indian state coverage with missing Assembly membership is accepted with an unknown constituency. Locations outside the supported geometry are rejected explicitly. Display geometry is simplified separately.

Boundary attribution, layer-specific CC BY 2.5 India / repository CC BY 4.0 licenses and source limitations are in [data/geography/README.md](data/geography/README.md); reproducible checksums and import diagnostics are in [source-manifest.json](data/geography/source-manifest.json). The importer verifies the committed checksums and WGS84 CRS. Initial geographic preparation can take several minutes.

Public map positions are stable **0.05° grid-cell centers**, approximately 5 km at the equator, not precise complaint locations. Heatmaps aggregate the same cells. Bounding boxes filter public centers, preventing repeated precise-boundary probing of private coordinates. Public endpoints never serialize private email, precise latitude/longitude, embeddings or processing metadata. Complaint prose itself is public: users are asked not to include personal contact details in it. SQLite stores private fields without encryption; protect the local machine and database backups.

## Tests and verification

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
# Actual-model integration (downloads only if not already cached):
$env:RUN_MODEL_TESTS='1'
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ../frontend
npm test
npm run build
npm audit
```

Model diagnostic, from root: `.\.venv\Scripts\python.exe scripts/evaluate_models.py`.

After a fictional live browser submission, verify its saved reference with `.\.venv\Scripts\python.exe scripts/smoke_test.py --reference <reference-id>`. This checks actual worker completion, 384-dimensional embeddings, Assembly resolution, public privacy and ten synchronized endpoints. It tags only the specifically named synthetic browser fixture as removable demo data.

See [VERIFICATION.md](VERIFICATION.md) for executed results and the responsive visual critique. Screenshots are saved locally in `outputs/screenshots/` and ignored by Git. The test suite uses deterministic mock vectors for semantic invariants; the opt-in suite additionally runs both actual models and an actual cross-encoder merge at the configured strict threshold.

## Configuration and limits

Copy `.env.example` to `.env` only to override defaults. Configure thresholds, text length, retry settings or model IDs in the documented `Settings` class. Changing embedding model/revision requires explicit full re-embedding and reclustering; mixed versions are rejected. `COMPLAINT_MAX_LENGTH` is published by `/api/config` so frontend/backend agree.

This implementation targets 1–2 concurrent localhost users. No authentication, moderation, complaint resolution/status tracking, department routing, translation, media, email verification or notifications are included. It must not be exposed to the internet as-is. Chart/region aggregation currently reads matching rows into memory; bounded lists are paginated after filtering. Individual marker data is appropriate for this local scale, not a nationwide production volume. The strict cross-encoder threshold can leave fragmented categories, and mixed-issue reports can remain ambiguous.

The stored history and service boundaries permit future replacement of SQLite with PostgreSQL, float32 storage/exact NumPy with pgvector, Shapely with PostGIS, and the local worker with a persistent external queue. Those changes should preserve the API and semantic invariants; distributed concurrency, locking, migrations and privacy policies would need a separate production design.
