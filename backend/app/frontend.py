"""Serve the built React application and API from the same origin."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: Path):
    directory = directory.resolve()
    assets = directory / 'assets'
    if assets.is_dir():
        app.mount('/assets', StaticFiles(directory=assets), name='frontend-assets')

    # Explicit page routes avoid swallowing API errors or serving repository files.
    @app.get('/', include_in_schema=False)
    @app.get('/raise', include_in_schema=False)
    @app.get('/analytics', include_in_schema=False)
    def frontend_page():
        index = directory / 'index.html'
        if not index.is_file():
            raise HTTPException(
                503,
                'The website has not been built. Run the Render build command from the repository root.',
            )
        return FileResponse(index, media_type='text/html', headers={'Cache-Control': 'no-cache'})
