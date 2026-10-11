@echo off
REM PAPI RFID Scanner - Build Script
REM Double-click to run or:
REM   build.bat              - Release (default)
REM   build.bat Debug        - Debug mode
REM ============================================================

setlocal

set CONFIG=%1
if "%CONFIG%"=="" set CONFIG=Release

echo.
echo ============================================================
echo   PAPI RFID Scanner - Build
echo   Mode: %CONFIG%
echo ============================================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0build-all.ps1" -Config %CONFIG%

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo   Done!
echo ============================================================
echo.
echo   Single-file:  %~dp0singlefile\RfidScanner.exe
echo   Installer:    %~dp0installer_output\PAPI.RfidScanner.Setup.exe
echo   MSI:          %~dp0msi_output\PAPI.RfidScanner.msi
echo.
