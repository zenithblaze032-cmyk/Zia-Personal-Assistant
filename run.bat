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
        goto :setup_venv
    )
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_EXE=python
        goto :setup_venv
    )
    echo  [ERROR] Python not found at C:\Python314\python.exe or in PATH.
    echo  Install Python 3 or update PYTHON_EXE in this file.
    pause
    exit /b 1
)

:setup_venv
if not exist "venv\Scripts\python.exe" (
    echo  [SETUP] Creating virtual environment...
    "%PYTHON_EXE%" -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [SETUP] Installing dependencies...
    venv\Scripts\python.exe -m pip install --upgrade pip -q
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    :: Quick check for updates
    venv\Scripts\python.exe -m pip install -r requirements.txt -q
)

:run
echo  Python  : venv\Scripts\python.exe
echo  Script  : %~dp0jarvis.py
echo.
cmd /c "venv\Scripts\python.exe "%~dp0jarvis.py""

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Jarvis exited with error code %ERRORLEVEL%.
    echo  Check the output above for details.
    pause
)
