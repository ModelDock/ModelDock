@echo off
setlocal enabledelayedexpansion
title ModelDock Documentation
color 0A

cd /d "%~dp0ModelDockdoc"

echo ========================================================
echo        ModelDock Documentation Viewer
echo ========================================================
echo.

set "PY_EXE="
if exist "..\.venv\Scripts\python.exe" (
    set "PY_EXE=..\.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_EXE=python"
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_EXE=py -3"
        )
    )
)

if not "!PY_EXE!"=="" (
    echo [*] Starting documentation preview server...
    "!PY_EXE!" -c "import http.server, socketserver, webbrowser, socket; p = 8080; s = socket.socket(); is_free = s.connect_ex(('127.0.0.1', p)) != 0; s.close(); port = p if is_free else 8085; print(f'Serving documentation at http://localhost:{port}/ ...'); webbrowser.open(f'http://localhost:{port}/index.html'); socketserver.TCPServer.allow_reuse_address = True; httpd = socketserver.TCPServer(('127.0.0.1', port), http.server.SimpleHTTPRequestHandler); httpd.serve_forever()"
) else (
    echo [!] Opening documentation directly in default browser...
    start "" index.html
)

if errorlevel 1 (
    echo Opening index.html directly in browser...
    start "" index.html
)

pause
