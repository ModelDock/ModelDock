@echo off
title ModelDock Studio Setup Wizard
color 0B

cd /d "%~dp0software\windows"

echo Launching ModelDock Studio Graphical Setup Wizard...
powershell -NoProfile -ExecutionPolicy Bypass -File "setup-wizard.ps1"
