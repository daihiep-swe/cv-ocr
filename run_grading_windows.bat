@echo off
setlocal enableextensions

rem Exam Grading System - Windows launcher
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo   Exam Grading System (Windows)
echo ========================================

echo [INFO] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not available in PATH
    exit /b 1
)

echo [INFO] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo [WARN] venv not found. Creating one...
    python -m venv venv || goto :venv_failed
)

call "venv\Scripts\activate.bat"

if not exist "src\app.py" (
    echo [ERROR] Missing src\app.py
    exit /b 1
)

if not exist "requirements.txt" (
    echo [ERROR] Missing requirements.txt
    exit /b 1
)

echo [INFO] Verifying core dependencies...
python -c "import cv2, numpy, pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Dependencies not fully installed. Installing from requirements.txt...
    python -m pip install -r requirements.txt || goto :deps_failed
) else (
    echo [INFO] Core dependencies already present.
)

if not exist "result" mkdir result
if not exist "logs" mkdir logs

echo [INFO] Starting grading...
python run_grading.py %*
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE%==0 (
    echo [OK] Completed successfully.
) else (
    echo [ERROR] Failed with exit code %EXITCODE%.
)

exit /b %EXITCODE%

:deps_failed
echo [ERROR] Dependency installation failed.
exit /b 1

:venv_failed
echo [ERROR] Failed to create virtual environment.
exit /b 1
