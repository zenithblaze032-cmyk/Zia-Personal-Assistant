@echo off
title JARVIS - Voice Assistant
color 0A
cls
echo.
echo  ============================================================
echo    J A R V I S  -  Voice-Activated Workspace Launcher
echo  ============================================================
echo.
echo  Say "JARVIS" to launch your workspace:
echo.
echo    [LEFT]   LeetCode
echo    [CENTRE] YouTube Playlist
echo    [RIGHT]  VS Code + Terminal
echo.
echo  Press Ctrl+C or say "shut down Jarvis" to exit.
echo  ============================================================
echo.

cd /d "%~dp0"

:: Locate Python — try known path first, then py launcher, then PATH
set PYTHON_EXE=C:\Python314\python.exe
if not exist "%PYTHON_EXE%" (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_EXE=py
        goto :run
    )
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_EXE=python
        goto :run
    )
    echo  [ERROR] Python not found at C:\Python314\python.exe
    echo  Install Python 3 or update PYTHON_EXE in this file.
    pause
    exit /b 1
)

:run
echo  Python  : %PYTHON_EXE%
echo  Script  : %~dp0jarvis.py
echo.
cmd /c ""%PYTHON_EXE%" "%~dp0jarvis.py""

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Jarvis exited with error code %ERRORLEVEL%.
    echo  Check the output above for details.
    pause
)
