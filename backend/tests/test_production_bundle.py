"""Exercise the actual Vite bundle when a local production build is available."""
from pathlib import Path
from html.parser import HTMLParser
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        path = values.get('src') or values.get('href')
        if path and path.startswith('/assets/'):
            self.paths.append(path)


def test_real_vite_entrypoint_and_assets(sessions, geo, runtime, config):
    bundle = Path(__file__).resolve().parents[2] / 'frontend/dist'
    if not (bundle / 'index.html').is_file():
        pytest.skip('Run npm --prefix frontend run build to verify the actual production bundle.')
    with TestClient(create_app(sessions, geo, runtime, config.model_copy(update={'frontend_dist': bundle}))) as client:
        response = client.get('/')
        assert response.status_code == 200
        assert 'Civic Atlas' in response.text
        parser = Assets()
        parser.feed(response.text)
        assert any(path.endswith('.js') for path in parser.paths)
        assert any(path.endswith('.css') for path in parser.paths)
        for path in parser.paths:
            asset = client.get(path)
            assert asset.status_code == 200
            assert not asset.headers['content-type'].startswith('text/html')
        assert all(client.get(page).status_code == 200 for page in ('/raise', '/analytics'))
        assert client.get('/api/health').json()['geography_available'] is True
