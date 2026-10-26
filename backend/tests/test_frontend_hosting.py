from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def hosted(tmp_path, sessions, geo, runtime, config):
    frontend = tmp_path / 'frontend-dist'
    (frontend / 'assets').mkdir(parents=True)
    (frontend / 'index.html').write_text('<!doctype html><title>Civic Atlas</title><div id="root"></div>', encoding='utf-8')
    (frontend / 'assets/app-123.js').write_text('console.log("atlas")', encoding='utf-8')
    # A source file outside the public build must never be served by path fallback.
    (tmp_path / '.env').write_text('PRIVATE_CONFIG=never-public', encoding='utf-8')
    with TestClient(create_app(sessions, geo, runtime, config.model_copy(update={'frontend_dist': frontend}))) as client:
        yield client


@pytest.mark.parametrize('page', ['/', '/raise', '/analytics', '/analytics?state_id=s1'])
def test_frontend_routes_return_html(hosted, page):
    response = hosted.get(page)
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert '<title>Civic Atlas</title>' in response.text
    assert response.headers['cache-control'] == 'no-cache'


def test_assets_and_api_share_origin(hosted):
    response = hosted.get('/assets/app-123.js')
    assert response.status_code == 200
    assert 'javascript' in response.headers['content-type']
    assert hosted.get('/api/health').json() == {'ok': True, 'geography_available': True}
    assert hosted.get('/api/complaints').json()['items'] == []
    assert hosted.get('/api/unknown').status_code == 404
    assert hosted.post('/raise').status_code == 405


@pytest.mark.parametrize('path', ['/assets/missing.js', '/.env', '/backend/app/config.py',
                                '/assets/%2e%2e/.env', '/unknown-page'])
def test_no_spa_fallback_for_missing_assets_or_private_paths(hosted, path):
    response = hosted.get(path)
    assert response.status_code == 404
    assert 'PRIVATE_CONFIG' not in response.text
    assert '<title>Civic Atlas</title>' not in response.text


def test_missing_build_has_actionable_error_not_blank_json_404(tmp_path, sessions, geo, runtime, config):
    missing = config.model_copy(update={'frontend_dist': tmp_path / 'missing-dist'})
    with TestClient(create_app(sessions, geo, runtime, missing)) as client:
        assert client.get('/').status_code == 503
        assert 'not been built' in client.get('/').json()['detail']
        assert client.get('/api/health').status_code == 200
