@echo off
setlocal enabledelayedexpansion

title Local AI Hub - Windows Environment Setup
echo ====================================================================
echo             LOCAL AI HUB - FULL WINDOWS SETUP
echo ====================================================================
echo.

:: ---------------------------------------------------------------------
:: STEP 1: Check for Python installation
:: ---------------------------------------------------------------------
echo [1/3] Checking for Python installation...

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo     Python is already installed!
    python --version
    goto :PYTHON_READY
)

:: Also check default Python 3.12 install directory if not in current PATH
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo     Python detected in %LOCALAPPDATA%\Programs\Python\Python312
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
    python --version
    goto :PYTHON_READY
)

:: ---------------------------------------------------------------------
:: Python not found: Download and install Python 3.12
:: ---------------------------------------------------------------------
echo.
echo     Python was NOT detected on this system.
echo     Downloading official Python 3.12 installer from python.org...
echo.

set "PY_INSTALLER=%TEMP%\python_installer_3.12.exe"
set "PY_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"

:: Download using Windows curl
curl.exe -L -o "%PY_INSTALLER%" "%PY_URL%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to download Python installer.
    echo Please ensure you are connected to the internet, or manually install
    echo Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo     Installing Python 3.12 (silent setup, adding to PATH)...
echo     Please wait, this may take a minute or two...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1

:: Delete the temporary installer
if exist "%PY_INSTALLER%" del /f /q "%PY_INSTALLER%"

:: Refresh PATH for the current session
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
set "PATH=%USER_PATH%;%SYS_PATH%;%PATH%"

:: Add default Python path explicitly just in case
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
)

:: Verify Python installation succeeded
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Python installation completed, but 'python' command is not immediately available.
    echo Please close this window and run 'Windows Installation.bat' once more.
    pause
    exit /b 1
)

echo.
echo     Python installed successfully:
python --version

:PYTHON_READY
echo.

:: ---------------------------------------------------------------------
:: STEP 2: Run Python dependencies installation script
:: ---------------------------------------------------------------------
echo [2/3] Installing Python requirements...
echo.

if exist "%~dp0install_requirements.bat" (
    call "%~dp0install_requirements.bat"
) else (
    python -m pip install --upgrade pip --quiet
    python -m pip install -r "%~dp0requirements.txt"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install all Python requirements.
    pause
    exit /b %ERRORLEVEL%
)

:: ---------------------------------------------------------------------
:: STEP 3: Complete environment readiness summary
:: ---------------------------------------------------------------------
echo.
echo [3/3] Checking environment status...
echo.
echo ====================================================================
echo  [SUCCESS] FULL ENVIRONMENT IS READY!
echo ====================================================================
echo.
echo  To run your Local AI Hub:
echo    1. Start the backend:  python pythoncode.py
echo    2. Open frontend:      index.html in your web browser
echo.
echo  Optional Fooocus Image Generation:
echo    - Launch your local Fooocus run.bat if you want image generation.
echo ====================================================================
echo.
pause
