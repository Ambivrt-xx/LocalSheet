@echo off
REM ============================================================
REM  LocalSheet — Uninstaller
REM  Removes shortcuts and application files.
REM ============================================================

setlocal
title LocalSheet Uninstaller

set "DEST=%LOCALAPPDATA%\Programs\LocalSheet"
set "START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\LocalSheet"

echo.
echo   ============================================
echo      LocalSheet — Uninstaller
echo   ============================================
echo.

echo   Removing Desktop shortcut...
del /q "%USERPROFILE%\Desktop\LocalSheet.lnk" >nul 2>&1

echo   Removing Start Menu entries...
if exist "%START%" rmdir /s /q "%START%" >nul 2>&1

echo   Removing application files...
if exist "%DEST%" rmdir /s /q "%DEST%" >nul 2>&1

echo.
echo   LocalSheet has been removed.
echo.
pause