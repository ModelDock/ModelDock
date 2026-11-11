@echo off
title ModelDock Studio - Native Desktop App [RUNNING]
color 0B

cd /d "%~dp0"

echo ======================================================================
echo              Starting ModelDock Desktop Application
echo ======================================================================
echo.

set PY_EXE=
if exist ".venv\Scripts\python.exe" (
    set PY_EXE=.venv\Scripts\python.exe
    echo [*] Using local ModelDock Python environment...
) else (
    set PY_EXE=python
    echo [*] Using system Python...
)

echo [*] Launching ModelDock Native Desktop Window...
echo [*] You can view runtime events and logs in this CMD window.
echo.

"%PY_EXE%" desktop_app.py
set EXIT_CODE=%errorlevel%

echo.
echo ======================================================================
if %EXIT_CODE% neq 0 (
    echo  [!] ModelDock Desktop closed with error code %EXIT_CODE%.
) else (
    echo  [*] ModelDock Desktop closed cleanly.
)
echo ======================================================================
echo Press any key to close this CMD window...
pause >nul
