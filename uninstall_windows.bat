@echo off
REM ============================================================
REM  LocalSheet — Windows Uninstaller
REM  Removes shortcuts and the installed application.
REM ============================================================

setlocal

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\LocalSheet"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\LocalSheet"
set "DESKTOP=%USERPROFILE%\Desktop"

echo.
echo  ========================================
echo   LocalSheet — Uninstaller
echo  ========================================
echo.

echo  Removing Desktop shortcut...
if exist "%DESKTOP%\LocalSheet.lnk" del /q "%DESKTOP%\LocalSheet.lnk"

echo  Removing Start Menu entries...
if exist "%STARTMENU_DIR%" rmdir /s /q "%STARTMENU_DIR%"

echo  Removing application files...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo.
echo  LocalSheet has been uninstalled.
echo.
pause