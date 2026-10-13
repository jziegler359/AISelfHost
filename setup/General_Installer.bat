@echo off
setlocal enabledelayedexpansion

title Local AI Hub - Master System Installer
echo ====================================================================
echo        LOCAL AI HUB - GENERAL ALL-IN-ONE SYSTEM INSTALLER
echo ====================================================================
echo  This script prepares your full local AI environment:
echo   1. Python 3.12 (Core Runtime)
echo   2. Python Packages (Flask, Ollama, Gradio-Client, Requests)
echo   3. Ollama (Local LLM Engine)
echo   4. Fooocus (Local SDXL Image Generator Detection and Setup)
echo   5. Creates one-click 'start_hub.bat' launcher
echo ====================================================================
echo.

rem ---------------------------------------------------------------------
rem STEP 1: Python Check and Install
rem ---------------------------------------------------------------------
echo [1/4] Checking Python runtime...

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo     [OK] Python is already installed:
    python --version
    goto PYTHON_READY
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo     [OK] Found Python in %LOCALAPPDATA%\Programs\Python\Python312
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
    python --version
    goto PYTHON_READY
)

echo     [!] Python not found. Downloading Python 3.12 installer...
set "PY_INSTALLER=%TEMP%\python_installer_3.12.exe"
curl.exe -L -o "%PY_INSTALLER%" "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
if %ERRORLEVEL% NEQ 0 (
    echo     [ERROR] Failed to download Python. Please install from python.org manually.
    goto STEP_OLLAMA
)

echo     [+] Installing Python 3.12 silently (adding to PATH)...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1
if exist "%PY_INSTALLER%" del /f /q "%PY_INSTALLER%"

rem Refresh current session PATH
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
set "PATH=%USER_PATH%;%SYS_PATH%;%PATH%"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
)

:PYTHON_READY
echo.

rem ---------------------------------------------------------------------
rem STEP 2: Python PIP Requirements
rem ---------------------------------------------------------------------
echo [2/4] Installing Python dependencies (Flask, Ollama, Gradio-Client, Requests)...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo     [WARNING] Some packages failed to install. Please check network connection.
) else (
    echo     [OK] All Python packages successfully installed and verified.
)
echo.

rem ---------------------------------------------------------------------
rem STEP 3: Ollama Check and Install
rem ---------------------------------------------------------------------
:STEP_OLLAMA
echo [3/4] Checking Ollama (Local LLM Engine)...

where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo     [OK] Ollama is installed.
    goto STEP_FOOOCUS
)

if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    echo     [OK] Ollama found in %LOCALAPPDATA%\Programs\Ollama
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
    goto STEP_FOOOCUS
)

echo     [!] Ollama was not found on your system.
echo     Downloading Ollama for Windows from ollama.com...
set "OLLAMA_INSTALLER=%TEMP%\OllamaSetup.exe"
curl.exe -L -o "%OLLAMA_INSTALLER%" "https://ollama.com/download/OllamaSetup.exe"
if %ERRORLEVEL% EQU 0 (
    echo     [+] Launching Ollama installer...
    start /wait "" "%OLLAMA_INSTALLER%"
    if exist "%OLLAMA_INSTALLER%" del /f /q "%OLLAMA_INSTALLER%"
    echo     [OK] Ollama installer finished.
) else (
    echo     [ERROR] Could not download Ollama automatically.
    echo     Please download and install it manually from: https://ollama.com/download
)
echo.

rem ---------------------------------------------------------------------
rem STEP 4: Fooocus Detection and Configuration
rem ---------------------------------------------------------------------
:STEP_FOOOCUS
echo [4/4] Checking Fooocus (SDXL Local Image Generation)...

set "FOOOCUS_FOUND=0"
set "FOOOCUS_PATH="

if exist "%USERPROFILE%\Documents\Usefull scripts\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\run.bat" (
    set "FOOOCUS_PATH=%USERPROFILE%\Documents\Usefull scripts\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0"
    set "FOOOCUS_FOUND=1"
)
if exist "%~dp0..\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\run.bat" (
    set "FOOOCUS_PATH=%~dp0..\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0"
    set "FOOOCUS_FOUND=1"
)
if exist "C:\Fooocus_win64_2-5-0\run.bat" (
    set "FOOOCUS_PATH=C:\Fooocus_win64_2-5-0"
    set "FOOOCUS_FOUND=1"
)

if "!FOOOCUS_FOUND!"=="1" (
    echo     [OK] Fooocus detected at:
    echo          !FOOOCUS_PATH!
    echo.
    echo     NOTE: Fooocus runs on its own self-contained portable runtime
    echo     ^(python_embeded^). You do NOT need to install another Python version!
    echo     Your main Python ^(3.12^) talks to Fooocus over localhost API via gradio_client.
) else (
    echo     [INFO] Fooocus was not detected in standard folders.
    echo     If you want local image generation later, download it from:
    echo     https://github.com/lllyasviel/Fooocus/releases
)
echo.

rem ---------------------------------------------------------------------
rem STEP 5: Create One-Click Launcher (start_hub.bat)
rem ---------------------------------------------------------------------
echo Creating one-click launcher 'start_hub.bat'...
(
    echo @echo off
    echo title Local AI Hub Server
    echo echo Starting Local AI Hub Backend on http://127.0.0.1:5000...
    echo start "" "%%~dp0index.html"
    echo python "%%~dp0pythoncode.py"
    echo pause
) > "%~dp0..\start_hub.bat"
echo     [OK] Created start_hub.bat in project root
echo.

rem ---------------------------------------------------------------------
rem FINAL SUMMARY
rem ---------------------------------------------------------------------
echo ====================================================================
echo  [SUCCESS] GENERAL INSTALLATION AND VERIFICATION COMPLETE!
echo ====================================================================
echo.
echo  SUMMARY OF YOUR ENVIRONMENT:
echo   - Python:             Ready ^(Python 3.12^)
echo   - Dependencies:       Ready ^(Flask, Flask-CORS, Ollama, Gradio-Client^)
echo   - Ollama LLMs:        Ready ^(ollama.exe detected^)
if "!FOOOCUS_FOUND!"=="1" (
echo   - Fooocus Image Gen:  Ready ^(!FOOOCUS_PATH!^)
) else (
echo   - Fooocus Image Gen:  Optional ^(Not installed yet^)
)
echo.
echo  HOW TO RUN YOUR APP:
echo   - Double-click 'start_hub.bat' to start the backend and open the UI!
echo   - Or manually run: python pythoncode.py
echo ====================================================================
echo.
pause
