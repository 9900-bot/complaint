#!/usr/bin/env bash
set -euo pipefail

# Run from the repository root, regardless of the dashboard's previous cwd.
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/backend"
export HF_HOME="$PWD/.cache/huggingface"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export HF_HUB_OFFLINE=0

# CPU wheels avoid downloading the CUDA runtime on a CPU-only host.
python -m pip install 'torch>=2.6,<3' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build

# Build-time downloads never touch the runtime SQLite database or mounted disk.
python scripts/prepare_geography.py --download-only
python -c "from app.ml import ModelRuntime; ModelRuntime().load(download=True)"
python scripts/render_runtime.py --check-build
