@echo off

echo Starting AI Engineering Copilot backend...

cd /d %~dp0\..

call backend\.venv\Scripts\activate

uvicorn backend.app.main:app --reload

pause