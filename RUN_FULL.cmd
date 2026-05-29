@echo off
setlocal
cd /d "%~dp0"
echo Running Transvoxel 0BSD FULL release proof...
echo.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 tools\run_everything.py --mode full
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo See proof\ONE_CLICK_RESULT.txt and proof\SEND_TO_CHATGPT.zip
    pause
    exit /b %RESULT%
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python tools\run_everything.py --mode full
    set RESULT=%ERRORLEVEL%
    echo.
    echo Finished. Result code: %RESULT%
    echo See proof\ONE_CLICK_RESULT.txt and proof\SEND_TO_CHATGPT.zip
    pause
    exit /b %RESULT%
)
echo Python was not found. Install Python or add it to PATH.
echo.
pause
exit /b 1
