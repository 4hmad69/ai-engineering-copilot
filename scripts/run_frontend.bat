@echo off
setlocal

cd /d "%~dp0\.."

echo Starting AI Engineering Copilot frontend...

if not exist "backend\.venv\Scripts\python.exe" (
    echo.
    echo ERROR: Python virtual environment was not found.
    echo Expected: backend\.venv\Scripts\python.exe
    exit /b 1
)

if not exist "frontend\app.py" (
    echo.
    echo ERROR: Streamlit entry file was not found.
    echo Expected: frontend\app.py
    exit /b 1
)

set "PYTHONPATH=%CD%"
set "FRONTEND_APP_NAME=AI Engineering Copilot"
set "FRONTEND_API_BASE_URL=http://127.0.0.1:8000/api/v1"
set "FRONTEND_REQUEST_TIMEOUT_SECONDS=300"
set "FRONTEND_MAX_CHAT_MESSAGES=40"

call "backend\.venv\Scripts\activate.bat"

python -m streamlit run "frontend\app.py"

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Frontend stopped with exit code %EXIT_CODE%.
)

endlocal
exit /b %EXIT_CODE%