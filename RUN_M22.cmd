@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo Running Transvoxel 0BSD M22 exact compatibility claim-boundary milestone...
echo.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 research\official_topology\m22\run_m22.py
    set RESULT=!ERRORLEVEL!
    echo.
    echo Finished. Result code: !RESULT!
    exit /b !RESULT!
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python research\official_topology\m22\run_m22.py
    set RESULT=!ERRORLEVEL!
    echo.
    echo Finished. Result code: !RESULT!
    exit /b !RESULT!
)
echo Python was not found. Install Python or add it to PATH.
exit /b 1
