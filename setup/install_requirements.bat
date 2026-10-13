@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     Local AI Hub - Python Dependencies Installer
echo ===================================================
echo.

:: Check if Python is installed and available in PATH
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/3] Python detected:
python --version
echo.

echo [2/3] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo.

echo [3/3] Installing required packages from requirements.txt...
python -m pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Some packages failed to install. Please check your internet connection or error messages above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo  [SUCCESS] All dependencies are installed and ready!
echo ===================================================
echo.
pause
