# Deploy the whole Civic Atlas on Render

The original Python-only service returns `{"detail":"Not Found"}` at `/` because it has no frontend route. This deployment builds React and serves it from FastAPI at the same origin. No separate frontend service, CORS setup or localhost proxy is needed.

## Update the existing service

After merging the deployment fix into your deployed branch, open **Settings → Build & Deploy**:

| Setting | Value |
| --- | --- |
| Repository | `9900-bot/complaint` |
| Branch | `main` (after merge) |
| Runtime | Python 3 |
| Root Directory | **Clear it; leave blank** |
| Build Command | `bash scripts/render_build.sh` |
| Start Command | `python scripts/render_runtime.py` |
| Health Check Path | `/api/health` |

The root directory must be empty: the build needs both `frontend/` and `backend/`. A service rooted at `backend` cannot use these commands correctly. Root directory controls source-trigger scope too; leaving it empty allows frontend changes to deploy. Python and Node versions are pinned by root files. Set `PYTHON_VERSION=3.11.9` if an existing environment override uses another version.

## Preserve complaints

For durable SQLite, use a paid web-service instance and attach a persistent disk at **`/var/data`**. Set:

```text
DATABASE_URL=sqlite:////var/data/atlas.db
PYTHON_VERSION=3.11.9
```

Do not put `HF_HOME`, `GEOGRAPHY_PATH` or `FRONTEND_DIST` on that disk. The build creates immutable model and boundary assets in the deploy artifact; only SQLite belongs on the runtime disk. The launcher migrates the disk-backed SQLite file and imports geographic metadata **after the disk is mounted**, then starts exactly one Uvicorn worker. Restarting preserves existing complaints; startup does not seed fictional reports or reset the database.

For a disposable demo on a free service, remove any `DATABASE_URL` override and use the default file inside the deployment. **All saved reports can disappear on restart/redeploy/spin-down.** 512 MB is not a validated budget for nationwide geometry plus PyTorch. Start memory testing with at least 2 GB; this is not a guarantee or authorization to purchase a plan. No paid service is created by these files.

If this service already contains real complaints in an ephemeral database, export them before changing the database URL or redeploying. A disk path change does not copy an old database automatically.

## What the scripts do

- Build: install CPU PyTorch and backend dependencies, install/build Vite frontend, download and validate pinned real boundaries, preload both pinned models. No SQLite writes, and no access to `/var/data` during build.
- Start: verify frontend/geography artifacts, create the SQLite parent directory, run Alembic, idempotently import regions, and run FastAPI. Model inference reads the bundled cache offline.
- Routes: `/`, `/raise` and `/analytics` return React; `/assets/*` serves only compiled assets; `/api/*` stays JSON. Unknown API/assets/source paths remain 404.

The build takes longer on first deploy because the models and real geographic boundaries must download. Stop after a failed build and inspect its logs instead of disabling the checks. This release preserves the local run commands in README.md.

## Verify the deployment

1. Open `https://complaint-website.onrender.com/`: expect Civic Atlas HTML rather than a JSON 404.
2. Refresh `/raise` and `/analytics` directly; all three pages must load.
3. Open `/api/health`: expect `ok: true` and `geography_available: true`. This is liveness/geometry evidence, not proof that model inference or disk persistence worked.
4. Make an explicitly fictional report. Confirm its reference, then confirm it appears in category/map/analytics results.
5. On a disk-backed service, restart and verify that reference still exists.

Local regression checks:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

Deployment verification is distinct from local tests; do not claim that Render is fixed until a new build is deployed and the public URL is checked.

References: [Render FastAPI](https://render.com/docs/deploy-fastapi), [native build tools](https://render.com/docs/native-runtimes), [disk lifecycle](https://render.com/docs/disks). The app is an early civic-reporting release with no moderation/authentication, historical boundary limitations and conservative English semantic models; retain those limits when hosting publicly.
