@echo off
setlocal
cd /d "%~dp0"
python tools\run_everything.py --mode auto --pause
endlocal
