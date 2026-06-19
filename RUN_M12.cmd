@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo Running Transvoxel 0BSD M12 M4 Godot backend comparison milestone...
echo.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 research\official_topology\m12\run_m12.py
    set RESULT=!ERRORLEVEL!
    echo.
    echo Finished. Result code: !RESULT!
    exit /b !RESULT!
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python research\official_topology\m12\run_m12.py
    set RESULT=!ERRORLEVEL!
    echo.
    echo Finished. Result code: !RESULT!
    exit /b !RESULT!
)
echo Python was not found. Install Python or add it to PATH.
exit /b 1
