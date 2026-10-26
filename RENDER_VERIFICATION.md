# Render frontend repair verification

26 October 2026.

The main branch at `b7cb0a9` defines API routes only. The user's deployed root returned FastAPI's `{"detail":"Not Found"}`. This fix builds the frontend and adds explicit HTML routes at `/`, `/raise` and `/analytics`, retaining API routes at `/api/*`.

Executed against a staged copy using the project's installed Python 3.11 environment:

- Final suite: **42 passed, 2 skipped in 8.44 seconds**. The skipped tests download/run actual models; inference code was unchanged.
- New tests cover all three page paths, HTML MIME type and no-cache response, compiled asset MIME type, API access at the same origin, unknown API/asset 404 behavior, private/source traversal rejection and an actionable error when no frontend build exists.
- New deployment tests verify a build check does not create/access runtime SQLite, startup migrations create its parent directory and database, and repeated geographic import produces no duplicate rows or seeded complaints.
- The startup environment preserves the configured disk-backed SQLite URL and uses the build's model-cache directory offline.
- An additional production-bundle check fetches the existing compiled Vite entrypoint and every referenced JavaScript/CSS asset through FastAPI.

The original React source and ML code are unchanged. A Linux Render build, new model downloads, persistent disk configuration and public deployment have not been executed in this repair. The prepared scripts are designed around Render's documented native Node/Python toolchain and runtime-only disk availability.

Required dashboard changes after merging: clear Root Directory; build `bash scripts/render_build.sh`; start `python scripts/render_runtime.py`; health `/api/health`. See DEPLOY_RENDER.md. This is not proof of a completed live deployment.
