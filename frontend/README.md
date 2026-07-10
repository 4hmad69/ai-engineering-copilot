# AI Engineering Copilot Frontend

A production-oriented Streamlit interface for the AI Engineering Copilot backend.

## Modules

- Dashboard and service health
- ZIP codebase upload and indexing
- Semantic search
- Grounded RAG chat with sources and diagnostics
- Structured AI code review
- Retrieval-grounded feature planning
- README, architecture, API, and onboarding documentation
- Retrieval and full-RAG evaluation

## Local environment

Copy the example environment file:

```cmd
copy frontend\.env.example frontend\.env
```

Local defaults:

```env
FRONTEND_APP_NAME=AI Engineering Copilot
FRONTEND_API_BASE_URL=http://127.0.0.1:8000/api/v1
FRONTEND_REQUEST_TIMEOUT_SECONDS=300
FRONTEND_MAX_CHAT_MESSAGES=40
```

## Local run

Start the backend first:

```cmd
docker compose up -d db
backend\.venv\Scriptsctivate
uvicorn backend.app.main:app --reload
```

Start the frontend in a second terminal:

```cmd
backend\.venv\Scriptsctivate
streamlit run frontendpp.py
```

Open `http://localhost:8501`.

## Docker run

Your root `.env.docker` must contain:

```env
FRONTEND_API_BASE_URL=http://backend:8000/api/v1
FRONTEND_REQUEST_TIMEOUT_SECONDS=300
FRONTEND_APP_NAME=AI Engineering Copilot
FRONTEND_MAX_CHAT_MESSAGES=40
```

Rebuild only the frontend after UI changes:

```cmd
docker compose -f docker-compose.full.yml build --no-cache frontend
docker compose -f docker-compose.full.yml up -d frontend
```

Or rebuild and start the full stack:

```cmd
docker compose -f docker-compose.full.yml up -d --build
```
