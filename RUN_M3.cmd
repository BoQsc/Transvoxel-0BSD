@echo off
setlocal
cd /d "%~dp0"
echo Running Transvoxel 0BSD official-topology M3 research...
echo.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 research\official_topology\m3\run_m3.py
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo See research\official_topology\m3\results.md
    pause
    exit /b %RESULT%
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python research\official_topology\m3\run_m3.py
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo See research\official_topology\m3\results.md
    pause
    exit /b %RESULT%
)
echo Python was not found. Install Python or add it to PATH.
echo.
pause
exit /b 1
