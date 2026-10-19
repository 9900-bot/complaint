$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required. Install it and rerun setup.' }
}
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $pythonPath -m pip install -r backend/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location -LiteralPath frontend
npm ci
if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
Pop-Location
Push-Location -LiteralPath backend
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
Pop-Location
& $pythonPath scripts/prepare_geography.py
if ($LASTEXITCODE -ne 0) { throw 'Geographic preparation failed.' }
& $pythonPath -c "import sys; sys.path.insert(0,'backend'); from app.ml import ModelRuntime; ModelRuntime().load(download=True); print('Local models ready.')"
if ($LASTEXITCODE -ne 0) { throw 'Model download failed. Check network access and retry.' }
Write-Output 'Setup complete. Run .\.venv\Scripts\python.exe scripts/dev.py'
