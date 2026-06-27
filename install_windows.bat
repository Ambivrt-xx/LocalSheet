@echo off
REM ============================================================
REM  LocalSheet — Windows Installer
REM  Builds the app, installs to Start Menu + Desktop,
REM  and creates an app launcher entry.
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo  ========================================
echo   LocalSheet — Windows Installer
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

REM --- Install dependencies ---
echo  [1/5] Installing dependencies...
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1

REM --- Build ---
echo  [2/5] Building LocalSheet executable...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist LocalSheet.spec del /q LocalSheet.spec

pyinstaller --onefile --windowed --name LocalSheet --collect-all src app.py >nul 2>&1
if not exist "dist\LocalSheet.exe" (
    echo  [ERROR] Build failed. Try running: python build.py
    pause
    exit /b 1
)

REM --- Install location ---
set "INSTALL_DIR=%LOCALAPPDATA%\Programs\LocalSheet"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\LocalSheet"
set "DESKTOP=%USERPROFILE%\Desktop"

echo  [3/5] Installing to %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "dist\LocalSheet.exe" "%INSTALL_DIR%\LocalSheet.exe" >nul

REM --- Create Start Menu shortcut ---
echo  [4/5] Creating Start Menu shortcut...
if not exist "%STARTMENU_DIR%" mkdir "%STARTMENU_DIR%"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%STARTMENU_DIR%\LocalSheet.lnk'); " ^
  "$s.TargetPath = '%INSTALL_DIR%\LocalSheet.exe'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'LocalSheet — Offline Spreadsheet'; " ^
  "$s.Save()"

REM --- Create Desktop shortcut ---
echo  [5/5] Creating Desktop shortcut...
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%DESKTOP%\LocalSheet.lnk'); " ^
  "$s.TargetPath = '%INSTALL_DIR%\LocalSheet.exe'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'LocalSheet — Offline Spreadsheet'; " ^
  "$s.Save()"

REM --- Create uninstaller ---
copy /y "uninstall_windows.bat" "%INSTALL_DIR%\uninstall.bat" >nul

echo.
echo  ========================================
echo   Installation complete!
echo  ========================================
echo.
echo  LocalSheet is now installed to:
echo    %INSTALL_DIR%
echo.
echo  Shortcuts created:
echo    - Desktop:        LocalSheet.lnk
echo    - Start Menu:     LocalSheet
echo.
echo  To uninstall, run:
echo    %INSTALL_DIR%\uninstall.bat
echo.
pause