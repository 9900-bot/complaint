import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def test_fresh_migration_round_trip(tmp_path):
    path=tmp_path/'migrated.db'
    env=os.environ|{'DATABASE_URL':f'sqlite:///{path.as_posix()}'}
    backend=Path(__file__).resolve().parents[1]
    for command in [('upgrade','head'),('downgrade','base'),('upgrade','head')]:
        result=subprocess.run([sys.executable,'-m','alembic',*command],cwd=backend,env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
    with sqlite3.connect(path) as db:
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'complaints','clusters','geographic_regions','cluster_merges','alembic_version'}<=tables
        assert db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        assert len(db.execute('PRAGMA foreign_key_list(complaints)').fetchall())==4
