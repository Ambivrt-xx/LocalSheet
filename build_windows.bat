@echo off
REM ============================================================
REM  LocalSheet — Windows build script
REM  Double-click this file (or run in CMD) to build a
REM  standalone LocalSheet.exe that needs no installation.
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo  ========================================
echo   LocalSheet — Windows Build
echo  ========================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Please install Python 3.10+ from https://python.org
    echo  Tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  [1/4] Installing dependencies...
pip install -r requirements.txt || (
    echo  [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo  [2/4] Installing PyInstaller...
pip install pyinstaller || (
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

echo.
echo  [3/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist LocalSheet.spec del /q LocalSheet.spec

echo.
echo  [4/4] Building executable (this takes a minute)...
pyinstaller --onefile --windowed --name LocalSheet --collect-all src app.py || (
    echo  [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Build complete!
echo  ========================================
echo.
echo  Your executable is ready:
echo    dist\LocalSheet.exe
echo.
echo  You can zip that folder and share it.
echo.
echo  TIP: For a full install with Start Menu + Desktop shortcuts,
echo  run install_windows.bat instead.
echo.
pause