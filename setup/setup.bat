@echo off
setlocal enabledelayedexpansion

title Local AI Hub - System Setup
echo =======================================================
echo           LOCAL AI HUB - SYSTEM SETUP
echo =======================================================
echo  Please select your operating system:
echo.
echo    [1] Windows (10 / 11)
echo    [2] Linux (Ubuntu, Debian, Fedora, Arch, etc.)
echo    [3] macOS (Apple Silicon / Intel)
echo =======================================================
echo.

:ASK_CHOICE
set "CHOICE="
set /p "CHOICE=Enter choice (1, 2, or 3): "

if "%CHOICE%"=="1" (
    set "OS_ID=windows"
    set "OS_NAME=Windows"
    goto :SAVE_CONFIG
)
if "%CHOICE%"=="2" (
    set "OS_ID=linux"
    set "OS_NAME=Linux"
    goto :SAVE_CONFIG
)
if "%CHOICE%"=="3" (
    set "OS_ID=macos"
    set "OS_NAME=macOS"
    goto :SAVE_CONFIG
)

echo [!] Invalid option. Please enter 1, 2, or 3.
goto :ASK_CHOICE

:SAVE_CONFIG
echo.
echo [+] Selected Operating System: !OS_NAME!

rem Save to project root config.json using built-in PowerShell (no Python required)
powershell -NoProfile -Command ^
    "$projectRoot = (Resolve-Path '%~dp0..').Path; " ^
    "$path = Join-Path $projectRoot 'config.json'; " ^
    "$json = if (Test-Path $path) { Get-Content $path -Raw | ConvertFrom-Json } else { [PSCustomObject]@{} }; " ^
    "$json | Add-Member -NotePropertyName 'os' -NotePropertyValue '!OS_ID!' -Force; " ^
    "$json | Add-Member -NotePropertyName 'os_display_name' -NotePropertyValue '!OS_NAME!' -Force; " ^
    "$json | ConvertTo-Json -Depth 5 | Set-Content $path -Encoding UTF8"

echo [SUCCESS] Saved OS configuration ('!OS_NAME!') into config.json in project root!
echo.
pause
