"""Run both localhost services; Ctrl+C stops the child processes."""
from pathlib import Path
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
for port in (8011,5173):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port))==0:
            raise SystemExit(f'Port {port} is already in use. Stop the other service first.')
node=shutil.which('node')
if not node:raise SystemExit('Install Node.js 22 or later first.')
flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
children=[]
try:
    children.append(subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8011','--workers','1','--no-access-log'],cwd=ROOT/'backend',creationflags=flags))
    children.append(subprocess.Popen([node,str(ROOT/'frontend/node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5173'],cwd=ROOT/'frontend',creationflags=flags))
    print('Civic Atlas: http://127.0.0.1:5173  |  API docs: http://127.0.0.1:8011/docs',flush=True)
    while all(p.poll() is None for p in children):time.sleep(.5)
except KeyboardInterrupt:
    pass
finally:
    for process in children:
        if process.poll() is None:process.terminate()
    for process in children:
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill()
