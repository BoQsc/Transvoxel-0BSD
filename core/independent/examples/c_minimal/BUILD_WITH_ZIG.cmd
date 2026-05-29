@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist build mkdir build
set ZIG=%ZIG_EXE%
if "%ZIG%"=="" set ZIG=zig.exe
"%ZIG%" cc -std=c99 -Wall -Wextra -pedantic -Iinclude -Igenerated src\transvoxel.c examples\c_minimal\main.c -o build\c_minimal.exe
if errorlevel 1 exit /b 1
build\c_minimal.exe
