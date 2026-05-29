@echo off
setlocal
cd /d "%~dp0"
echo Opening Transvoxel 0BSD interactive sandbox...
echo.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 tools\run_everything.py --mode interactive
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo Interactive session report, if created: godot\validation\06_interactive_sandbox\session.json
    echo Upload this single file if it exists: proof\SEND_TO_CHATGPT.zip
    pause
    exit /b %RESULT%
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python tools\run_everything.py --mode interactive
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo Interactive session report, if created: godot\validation\06_interactive_sandbox\session.json
    echo Upload this single file if it exists: proof\SEND_TO_CHATGPT.zip
    pause
    exit /b %RESULT%
)
echo Python was not found. Install Python or add it to PATH.
echo.
pause
exit /b 1
