@echo off
title ModelDock Studio Windows Installer
color 0B

echo ======================================================================
echo          Installing ModelDock Studio for Windows Desktop
echo ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\installer.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed.
    pause
)
