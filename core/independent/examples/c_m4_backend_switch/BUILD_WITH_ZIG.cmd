@echo off
setlocal
cd /d "%~dp0\..\.."
zig cc -std=c99 -Wall -Wextra -pedantic -Iinclude -Igenerated src\transvoxel.c src\transvoxel_m4_candidate.c src\transvoxel_m4_backend.c examples\c_m4_backend_switch\main.c -o c_m4_backend_switch.exe
if errorlevel 1 exit /b 1
c_m4_backend_switch.exe
