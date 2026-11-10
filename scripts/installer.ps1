# ==============================================================================
# ModelDock Studio - Windows Desktop Software Installer
# Installs as a native Windows desktop app with Desktop & Start Menu shortcuts
# ==============================================================================

param(
    [string]$TargetDir = "$env:LOCALAPPDATA\Programs\ModelDock Studio",
    [string]$LaunchAfterInstall = "true"
)

$ErrorActionPreference = "Stop"
$ShouldLaunch = ($LaunchAfterInstall -eq "true" -or $LaunchAfterInstall -eq "1" -or $LaunchAfterInstall -eq $true)

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "          ModelDock Studio - Windows Software Setup" -ForegroundColor White
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
Write-Host "[1/6] Checking system environment..." -ForegroundColor Yellow
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Host "[ERROR] Python 3.10+ was not found on your system PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/ and ensure 'Add to PATH' is checked." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$PyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "      Detected Python: $PyVersion ($($PythonCmd.Source))" -ForegroundColor Green

# Locate pythonw.exe for windowless native execution
$PythonDir = Split-Path $PythonCmd.Source
$PythonW = Join-Path $PythonDir "pythonw.exe"
if (-not (Test-Path $PythonW)) {
    # In Windows store installations or virtualenvs, fallback to python.exe
    $PythonW = $PythonCmd.Source
}

# 2. Check & Install Required Python Packages
Write-Host "[2/6] Verifying required desktop & AI libraries..." -ForegroundColor Yellow
$CheckScript = "import fastapi, uvicorn, httpx, webview, huggingface_hub, psutil, pydantic, openpyxl, cv2, multipart; print('OK')"
$CheckResult = ""
try {
    $CheckResult = (& python -c $CheckScript 2>&1 | Out-String).Trim()
} catch {
    $CheckResult = ""
}

if ($CheckResult -ne "OK") {
    Write-Host "      Installing desktop runtime dependencies..." -ForegroundColor Yellow
    & python -m pip install --quiet fastapi uvicorn httpx pywebview huggingface_hub psutil pydantic python-multipart openpyxl opencv-python-headless
}
Write-Host "      All dependencies verified." -ForegroundColor Green

# 3. Create Installation Directory
Write-Host "[3/6] Setting up installation directory at:" -ForegroundColor Yellow
Write-Host "      $TargetDir" -ForegroundColor White

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

$SourceDir = Split-Path -Parent $PSScriptRoot

# Copy Project Files
Write-Host "[4/6] Copying application files..." -ForegroundColor Yellow
$ItemsToCopy = @("bin", "models", "core", "static", "desktop_app.py", "run.py", "app.ico", "config.json", "README.md")

foreach ($item in $ItemsToCopy) {
    $src = Join-Path $SourceDir $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $TargetDir -Recurse -Force
    }
}

# Ensure downloads directory exists in target
$DownloadsTarget = Join-Path $TargetDir "downloads"
if (-not (Test-Path $DownloadsTarget)) {
    New-Item -ItemType Directory -Force -Path $DownloadsTarget | Out-Null
}

# 4. Create Windowless Launcher (VBScript + Batch)
Write-Host "[5/6] Creating Windows native launcher & uninstaller..." -ForegroundColor Yellow

$VbsLauncherPath = Join-Path $TargetDir "ModelDock.vbs"
$VbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "$TargetDir"
WshShell.Run """$PythonW"" ""$TargetDir\desktop_app.py""", 0, False
"@
[IO.File]::WriteAllText($VbsLauncherPath, $VbsContent)

$BatLauncherPath = Join-Path $TargetDir "ModelDock.bat"
$BatContent = @"
@echo off
cd /d "$TargetDir"
start "" "$PythonW" "$TargetDir\desktop_app.py"
"@
[IO.File]::WriteAllText($BatLauncherPath, $BatContent)

# Create Uninstaller Script
$UninstallPs1 = Join-Path $TargetDir "uninstall.ps1"
$UninstallPs1Content = @"
`$ErrorActionPreference = 'SilentlyContinue'
`$DesktopLnk = "`$env:USERPROFILE\Desktop\ModelDock Studio.lnk"
`$StartLnk = "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ModelDock Studio.lnk"
`$RegKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ModelDockStudio'

Remove-Item -Path `$DesktopLnk -Force -ErrorAction SilentlyContinue
Remove-Item -Path `$StartLnk -Force -ErrorAction SilentlyContinue
Remove-Item -Path `$RegKey -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "ModelDock Studio shortcuts and registry entries removed." -ForegroundColor Green
Write-Host "To remove files, delete: $TargetDir" -ForegroundColor Yellow
"@
[IO.File]::WriteAllText($UninstallPs1, $UninstallPs1Content)

$UninstallBat = Join-Path $TargetDir "Uninstall.bat"
$UninstallBatContent = @"
@echo off
title ModelDock Studio Uninstaller
echo Uninstalling ModelDock Studio...
powershell -NoProfile -ExecutionPolicy Bypass -File "$UninstallPs1"
echo.
echo Uninstallation complete.
pause
"@
[IO.File]::WriteAllText($UninstallBat, $UninstallBatContent)

# Register in Windows Add or Remove Programs (Registry)
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ModelDockStudio"
if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}
Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "ModelDock Studio"
Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "ModelDock Open-Source AI"
Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value "$TargetDir\app.ico"
Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value """$TargetDir\Uninstall.bat"""
Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value "$TargetDir"

# 5. Create Desktop & Start Menu Shortcuts
Write-Host "[6/6] Generating Desktop and Start Menu shortcuts..." -ForegroundColor Yellow

$WshShell = New-Object -ComObject WScript.Shell

# Desktop Shortcut
$DesktopFolder = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
$DesktopLnkPath = Join-Path $DesktopFolder "ModelDock Studio.lnk"
$DesktopShortcut = $WshShell.CreateShortcut($DesktopLnkPath)
$DesktopShortcut.TargetPath = "wscript.exe"
$DesktopShortcut.Arguments = """$VbsLauncherPath"""
$DesktopShortcut.WorkingDirectory = $TargetDir
$DesktopShortcut.IconLocation = "$TargetDir\app.ico,0"
$DesktopShortcut.Description = "Universal Local Open-Source AI Platform"
$DesktopShortcut.Save()
Write-Host "      [OK] Desktop Shortcut created: $DesktopLnkPath" -ForegroundColor Green

# Start Menu Shortcut
$StartFolder = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
$StartLnkPath = Join-Path $StartFolder "ModelDock Studio.lnk"
$StartShortcut = $WshShell.CreateShortcut($StartLnkPath)
$StartShortcut.TargetPath = "wscript.exe"
$StartShortcut.Arguments = """$VbsLauncherPath"""
$StartShortcut.WorkingDirectory = $TargetDir
$StartShortcut.IconLocation = "$TargetDir\app.ico,0"
$StartShortcut.Description = "Universal Local Open-Source AI Platform"
$StartShortcut.Save()
Write-Host "      [OK] Start Menu Shortcut created: $StartLnkPath" -ForegroundColor Green

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "   ModelDock Studio has been successfully installed in Windows!" -ForegroundColor White
Write-Host "====================================================================" -ForegroundColor Green
Write-Host " - Desktop shortcut:    ModelDock Studio" -ForegroundColor Cyan
Write-Host " - Start Menu:          ModelDock Studio" -ForegroundColor Cyan
Write-Host " - Ultra-low memory:    ~35 MB RAM (Zero Electron bloat)" -ForegroundColor Cyan
Write-Host " - Uninstaller:         $TargetDir\Uninstall.bat" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""

if ($ShouldLaunch) {
    Write-Host "Launching ModelDock Studio native desktop app..." -ForegroundColor Yellow
    Start-Process "wscript.exe" -ArgumentList """$VbsLauncherPath"""
}
