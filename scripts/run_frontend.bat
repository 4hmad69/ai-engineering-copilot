@echo off

echo Starting AI Engineering Copilot frontend...

cd /d %~dp0\..

call backend\.venv\Scripts\activate

set FRONTEND_API_BASE_URL=http://127.0.0.1:8000/api/v1
set FRONTEND_REQUEST_TIMEOUT_SECONDS=180

streamlit run frontend\app.py

pause