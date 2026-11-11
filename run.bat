@echo off
title ModelDock Studio - Universal Local AI Platform [RUNNING]
color 0B

cd /d "%~dp0"

echo ======================================================================
echo    Starting ModelDock Studio - Hugging Face + Ollama Universal Runner
echo ======================================================================
echo.

set PY_EXE=
if exist ".venv\Scripts\python.exe" (
    set PY_EXE=.venv\Scripts\python.exe
    echo [*] Using local ModelDock Python environment - RTX 4060 GPU enabled...
) else (
    set PY_EXE=python
    echo [*] Using system Python...
)

echo [*] Launching ModelDock Web Server...
echo [*] Live logs and requests will stream directly in this CMD window:
echo.

"%PY_EXE%" run.py
set EXIT_CODE=%errorlevel%

rem Clean up any orphaned llama-server background instances safely
taskkill /F /IM llama-server.exe >nul 2>&1

echo.
echo ======================================================================
if %EXIT_CODE% neq 0 (
    echo  [!] ModelDock Studio stopped with exit code %EXIT_CODE%.
) else (
    echo  [*] ModelDock Studio has stopped cleanly.
)
echo ======================================================================
echo Press any key to close this CMD window...
pause >nul
