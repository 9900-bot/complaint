import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from shapely.geometry import box, mapping

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('render_runtime', ROOT / 'scripts/render_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def assets(tmp_path):
    frontend = tmp_path / 'dist'
    (frontend / 'assets').mkdir(parents=True)
    (frontend / 'index.html').write_text('<title>Civic Atlas</title>', encoding='utf-8')
    features = []
    for kind in ('state', 'district', 'constituency'):
        geometry = mapping(box(70, 10, 80, 20))
        features.append({
            'id': kind, 'stable_code': kind, 'name': kind.title(), 'region_type': kind,
            'parent_region_id': None if kind == 'state' else 'state',
            'dataset_version': 'test-only', 'geometry': geometry, 'display_geometry': geometry,
        })
    geography = tmp_path / 'regions.json'
    geography.write_text(json.dumps(features), encoding='utf-8')
    return frontend, geography


def test_missing_or_incomplete_artifacts_fail_before_start(tmp_path):
    with pytest.raises(RuntimeError, match='Frontend build missing'):
        runtime.validate_assets(tmp_path / 'missing', tmp_path / 'missing.json')
    frontend, geography = assets(tmp_path)
    geography.write_text('[]')
    with pytest.raises(RuntimeError, match='incomplete'):
        runtime.validate_assets(frontend, geography)
    geography.unlink()
    with pytest.raises(RuntimeError, match='Geographic bundle missing'):
        runtime.validate_assets(frontend, geography)


def test_build_check_never_opens_runtime_disk_and_start_is_idempotent(tmp_path):
    import sqlite3
    frontend, geography = assets(tmp_path)
    database = tmp_path / 'mounted-at-runtime' / 'atlas.db'
    env = os.environ | {
        'DATABASE_URL': f'sqlite:///{database.as_posix()}',
        'FRONTEND_DIST': str(frontend), 'GEOGRAPHY_PATH': str(geography),
        'PYTHONDONTWRITEBYTECODE': '1', 'WORKER_ENABLED': 'false',
    }
    check = subprocess.run([sys.executable, str(ROOT / 'scripts/render_runtime.py'), '--check-build'],
                           env=env, cwd=ROOT, capture_output=True, text=True, timeout=45)
    assert check.returncode == 0, check.stderr
    assert not database.exists()  # Render disks cannot be accessed during builds.
    for _ in range(2):
        start = subprocess.run([sys.executable, str(ROOT / 'scripts/render_runtime.py'), '--prepare-only'],
                               env=env, cwd=ROOT, capture_output=True, text=True, timeout=45)
        assert start.returncode == 0, start.stderr
    with sqlite3.connect(database) as db:
        assert db.execute('select count(*) from geographic_regions').fetchone()[0] == 3
        assert db.execute('select count(*) from complaints').fetchone()[0] == 0
        assert db.execute('select version_num from alembic_version').fetchone()


def test_runtime_preserves_custom_database_and_uses_build_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:////var/data/atlas.db')
    monkeypatch.setenv('HF_HOME', '/wrong/runtime-only/cache')
    original_path = sys.path[:]
    try:
        runtime.configure_environment(tmp_path)
        assert os.environ['DATABASE_URL'] == 'sqlite:////var/data/atlas.db'
        assert os.environ['HF_HOME'] == str(tmp_path / '.cache/huggingface')
        assert os.environ['HF_HUB_OFFLINE'] == '1'
    finally:
        sys.path[:] = original_path
        for name in ('GEOGRAPHY_PATH', 'FRONTEND_DIST', 'HF_HUB_OFFLINE', 'HF_HUB_DISABLE_SYMLINKS_WARNING',
                     'TOKENIZERS_PARALLELISM', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
            monkeypatch.delenv(name, raising=False)
