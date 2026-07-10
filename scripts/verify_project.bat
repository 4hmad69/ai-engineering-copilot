@echo off
setlocal

cd /d "%~dp0\.."

echo.
echo ================================================
echo AI Engineering Copilot Verification
echo ================================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: backend virtual environment was not found.
    echo Expected: backend\.venv\Scripts\python.exe
    exit /b 1
)

call "backend\.venv\Scripts\activate.bat"

echo [1/5] Compiling Python files...
python -m compileall -q backend frontend tests
if errorlevel 1 goto :failed

echo [2/5] Running Ruff lint checks...
python -m ruff check backend frontend tests
if errorlevel 1 goto :failed

echo [3/5] Checking Ruff formatting...
python -m ruff format --check backend frontend tests
if errorlevel 1 goto :failed

echo [4/5] Running automated tests...
python -m pytest --cov=backend --cov=frontend --cov-report=term-missing
if errorlevel 1 goto :failed

echo [5/5] Validating Docker Compose configuration...
docker compose -f docker-compose.full.yml config > nul
if errorlevel 1 goto :failed

if /I "%~1"=="--smoke" (
    echo.
    echo Running full-stack smoke tests...
    python scripts\smoke_test.py
    if errorlevel 1 goto :failed
)

echo.
echo ================================================
echo Verification completed successfully.
echo ================================================
exit /b 0

:failed
echo.
echo ================================================
echo Verification failed. Review the output above.
echo ================================================
exit /b 1