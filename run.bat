@echo off
title ModelDock Studio - Universal Local AI Platform
color 0B

echo ======================================================================
echo    Starting ModelDock Studio (Hugging Face + Ollama Universal Runner)
echo ======================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

python run.py

if errorlevel 1 (
    echo.
    echo [ERROR] ModelDock Studio encountered an issue.
    pause
)
