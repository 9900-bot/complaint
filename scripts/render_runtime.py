"""Validate deploy artifacts, migrate/import at runtime, and start one ASGI process."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def configure_environment(root=ROOT):
    # The same model cache is included in the build artifact and used at runtime.
    os.environ['HF_HOME'] = str(root / '.cache/huggingface')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['MKL_NUM_THREADS'] = '2'
    # Respect DATABASE_URL explicitly configured for a persistent disk.
    os.environ.setdefault('DATABASE_URL', f"sqlite:///{(root / 'data/atlas.db').as_posix()}")
    os.environ.setdefault('GEOGRAPHY_PATH', str(root / 'data/geography/regions.json'))
    os.environ.setdefault('FRONTEND_DIST', str(root / 'frontend/dist'))
    sys.path.insert(0, str(root / 'backend'))


def validate_assets(frontend_dist: Path, geography_path: Path):
    if not (frontend_dist / 'index.html').is_file() or not (frontend_dist / 'assets').is_dir():
        raise RuntimeError('Frontend build missing. Use bash scripts/render_build.sh from the repository root.')
    if not geography_path.is_file():
        raise RuntimeError('Geographic bundle missing. The Render build must run prepare_geography.py --download-only.')
    # Parsing catches partial/corrupt downloads before publishing a healthy service.
    features = json.loads(geography_path.read_text(encoding='utf-8'))
    kinds = {feature.get('region_type') for feature in features}
    if not {'state', 'district', 'constituency'} <= kinds:
        raise RuntimeError('Geographic bundle is incomplete.')


def migrate_and_import(database_url: str, geography_path: Path, root=ROOT):
    from sqlalchemy.engine import make_url
    from alembic import command
    from alembic.config import Config
    from app.database import make_engine
    from app.geography import Geography
    from sqlalchemy.orm import sessionmaker

    url = make_url(database_url)
    if url.get_backend_name() != 'sqlite' or not url.database or url.database == ':memory:':
        raise RuntimeError('This release requires a SQLite file DATABASE_URL.')
    Path(url.database).resolve().parent.mkdir(parents=True, exist_ok=True)
    migration = Config(str(root / 'backend/alembic.ini'))
    migration.set_main_option('script_location', str(root / 'backend/migrations'))
    # env.py reads settings (initialized only after configure_environment).
    command.upgrade(migration, 'head')
    engine = make_engine(database_url)
    try:
        Geography(geography_path).import_metadata(sessionmaker(engine, expire_on_commit=False))
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-build', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    configure_environment()
    from app.config import settings
    validate_assets(settings.frontend_dist, settings.geography_path)
    if args.check_build:
        print('Frontend and geographic build artifacts verified.', flush=True)
        return

    # Disks are available only now, not in Render build/pre-deploy commands.
    migrate_and_import(settings.database_url, settings.geography_path)
    print('SQLite migrated and geographic metadata imported.', flush=True)
    if args.prepare_only:
        return
    import uvicorn
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '8011')),
        workers=1,
        access_log=False,
        proxy_headers=True,
    )


if __name__ == '__main__':
    main()
