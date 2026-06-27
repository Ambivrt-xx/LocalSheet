@echo off
REM ============================================================
REM  LocalSheet — One-Click Windows Installer
REM  Double-click this file to build, install, and launch.
REM  Creates Desktop + Start Menu shortcuts automatically.
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

title LocalSheet Installer

echo.
echo   ============================================
echo      LocalSheet — One-Click Installer
echo   ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Python not found!
    echo       Install Python 3.10+ from https://python.org
    echo       Make sure to tick "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo   [1/4] Installing dependencies...
pip install -r requirements.txt pyinstaller >nul 2>&1

echo   [2/4] Building LocalSheet...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist LocalSheet.spec del /q LocalSheet.spec >nul 2>&1

pyinstaller --onefile --windowed --name LocalSheet --collect-all src app.py >nul 2>&1
if not exist "dist\LocalSheet.exe" (
    echo   [X] Build failed!
    echo       Try running: python build.py
    pause
    exit /b 1
)

echo   [3/4] Installing to AppData...
set "DEST=%LOCALAPPDATA%\Programs\LocalSheet"
if not exist "%DEST%" mkdir "%DEST%"
copy /y "dist\LocalSheet.exe" "%DEST%\LocalSheet.exe" >nul
copy /y "Uninstall.bat" "%DEST%\Uninstall.bat" >nul 2>&1

echo   [4/4] Creating shortcuts...
set "START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\LocalSheet"
if not exist "%START%" mkdir "%START%"

powershell -NoProfile -Command ^
  "$w=New-Object -ComObject WScript.Shell;" ^
  "$s=$w.CreateShortcut('%START%\LocalSheet.lnk');" ^
  "$s.TargetPath='%DEST%\LocalSheet.exe';" ^
  "$s.WorkingDirectory='%DEST%';" ^
  "$s.Description='LocalSheet — Offline Spreadsheet';" ^
  "$s.Save();" ^
  "$d=$w.CreateShortcut('%USERPROFILE%\Desktop\LocalSheet.lnk');" ^
  "$d.TargetPath='%DEST%\LocalSheet.exe';" ^
  "$d.WorkingDirectory='%DEST%';" ^
  "$d.Description='LocalSheet — Offline Spreadsheet';" ^
  "$d.Save()"

echo.
echo   ============================================
echo      Installation Complete!
echo   ============================================
echo.
echo    LocalSheet is now on your Desktop and
echo    Start Menu. Just double-click to launch.
echo.
echo    Installed to: %DEST%
echo.
echo    To uninstall: Run Uninstall.bat
echo.

REM --- Launch immediately ---
start "" "%DEST%\LocalSheet.exe"