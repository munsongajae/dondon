@echo off
REM Daily Kakao report sender

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if not exist "%PYTHON_EXE%" (
    echo Python 3.10 executable not found at %PYTHON_EXE%.
    exit /b 1
)

"%PYTHON_EXE%" -m reporting.send_report >> "%SCRIPT_DIR%report.log" 2>&1

