# AI Engineering Copilot

AI Engineering Copilot is a production-style, retrieval-augmented developer workspace for understanding, reviewing, planning, documenting, and evaluating software projects.

It accepts a zipped codebase, safely extracts and indexes supported files, creates embeddings, retrieves relevant code context, and uses a local coding LLM to provide grounded developer assistance.

## Core Features

### Codebase Ingestion

- Safe ZIP upload and extraction
- ZIP path-traversal protection
- Upload size and extracted-size limits
- Project file discovery and metadata inspection
- Binary, cache, dependency, and generated-directory filtering

### Semantic Search

- Code and documentation chunking
- Sentence Transformer embeddings
- PostgreSQL and pgvector storage
- Cosine similarity search
- Similarity and MMR retrieval strategies

### Grounded RAG Chat

- Codebase-aware natural-language Q&A
- Structured JSON LLM responses
- Source citations and line ranges
- Confidence calibration
- Missing-context detection
- Retrieval diagnostics
- Prompt-injection-resistant context handling

### AI Code Review

- Code and Git-diff review
- Bug and security detection
- Severity and category classification
- Missing-test identification
- Evidence-based recommendations
- Structured Pydantic output

### Feature Planner

- Retrieval-grounded feature planning
- Affected-file identification
- Implementation steps
- API and database changes
- Test planning
- Risks, assumptions, and complexity estimation

### Documentation Generator

- README generation
- Architecture documentation
- API documentation
- Developer onboarding documentation
- Markdown preview and download
- Source-backed generation

### RAG Evaluation

- Retrieval-only evaluation
- Full RAG evaluation
- Expected-source-file validation
- Keyword coverage
- Retrieval hit rate
- Similarity metrics
- Per-case failure reasons

### GPT-Style Frontend

- Streamlit SaaS workspace
- Sidebar navigation
- Project-aware session state
- Native chat interface
- Source and diagnostics panels
- System-health dashboard
- Responsive dark theme

## Architecture

```text
User
  |
  v
Streamlit Frontend
  |
  v
FastAPI Backend
  |
  +--> Upload and Project Services
  |
  +--> Document Loader and Chunker
  |
  +--> Sentence Transformer Embeddings
  |
  +--> PostgreSQL + pgvector
  |
  +--> Similarity / MMR Retriever
  |
  +--> Ollama Coding LLM
  |
  +--> RAG, Review, Planner, Documentation, Evaluation
```

## Technology Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Frontend | Streamlit |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Vector Store | pgvector |
| Embeddings | Sentence Transformers |
| LLM Runtime | Ollama |
| Local Model | Configurable coding model |
| HTTP Client | HTTPX |
| Containers | Docker and Docker Compose |
| Tests | Pytest |
| Quality | Ruff |

## Repository Structure

```text
ai-engineering-copilot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── prompts/
│   │   ├── schemas/
│   │   └── services/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── components/
│   ├── services/
│   ├── styles/
│   ├── utils/
│   ├── views/
│   ├── Dockerfile
│   └── app.py
├── tests/
│   ├── api/
│   └── unit/
├── docs/
├── docker/
├── scripts/
├── docker-compose.yml
├── docker-compose.full.yml
└── README.md
```

## Prerequisites

Install:

- Python 3.12
- Docker Desktop
- Ollama
- Git

Pull the configured Ollama model before using LLM-powered modules:

```cmd
ollama pull qwen2.5-coder:3b
```

The selected model can be changed using environment variables.

## Run With Docker

Create the Docker environment file:

```cmd
copy .env.docker.example .env.docker
```

Start Ollama on the host:

```cmd
ollama serve
```

Start the complete stack:

```cmd
docker compose -f docker-compose.full.yml up -d --build
```

Open:

- Frontend: `http://localhost:8501`
- Swagger: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/v1/health`
- Database health: `http://localhost:8000/api/v1/health/database`

Check containers:

```cmd
docker compose -f docker-compose.full.yml ps
```

Stop the stack:

```cmd
docker compose -f docker-compose.full.yml down
```

## Run Locally

Start PostgreSQL:

```cmd
docker compose up -d db
```

Activate the backend environment:

```cmd
backend\.venv\Scripts\activate
```

Run FastAPI:

```cmd
uvicorn backend.app.main:app --reload
```

Run Streamlit in another terminal:

```cmd
scripts\run_frontend.bat
```

## End-to-End Workflow

1. Upload a zipped codebase.
2. Inspect supported project files.
3. Preview and persist chunks.
4. Generate embeddings.
5. Run semantic search.
6. Ask grounded RAG questions.
7. Review code or Git diffs.
8. Create feature implementation plans.
9. Generate project documentation.
10. Run retrieval and RAG evaluations.

## Testing

Install development dependencies:

```cmd
pip install -r backend\requirements-dev.txt
```

Run unit and API tests:

```cmd
python -m pytest
```

Run coverage:

```cmd
python -m pytest --cov=backend --cov=frontend --cov-report=term-missing
```

Run complete verification:

```cmd
scripts\verify_project.bat
```

With the full Docker stack running:

```cmd
scripts\verify_project.bat --smoke
```

## Environment Configuration

Important settings include:

```env
DATABASE_URL=postgresql+asyncpg://...
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_TIMEOUT_SECONDS=300

RAG_DEFAULT_TOP_K=5
RAG_MAX_CONTEXT_CHARACTERS=7000
RAG_RETRIEVAL_CANDIDATE_K=12
RAG_MMR_LAMBDA=0.65
```

Inside Docker, the backend uses:

```env
DATABASE_URL=postgresql+asyncpg://ai_copilot:ai_copilot_password@db:5432/ai_copilot
OLLAMA_BASE_URL=http://host.docker.internal:11434
FRONTEND_API_BASE_URL=http://backend:8000/api/v1
```

## Design Decisions

### Local LLM Runtime

Ollama keeps generation local and allows the coding model to be changed without rewriting the application.

### PostgreSQL and pgvector

Project metadata, documents, chunks, and vectors are stored in one durable database.

### Structured LLM Responses

LLM outputs are validated through Pydantic before they reach API consumers.

### MMR Retrieval

MMR reduces duplicate context and balances relevance with source diversity.

### Guardrails

The RAG pipeline validates source IDs, calibrates confidence, handles missing context, and prevents retrieved code from becoming system instructions.

### Separate Frontend and Backend Containers

The frontend remains lightweight while AI, database, and retrieval dependencies stay in the backend container.

## Troubleshooting

### PostgreSQL Is Not Reachable

```cmd
docker compose -f docker-compose.full.yml up -d db
```

### Ollama Is Not Reachable

```cmd
ollama serve
```

Ensure Docker uses:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Ollama Is Slow

Use a smaller configured model, reduce `top_k`, reduce `candidate_k`, or lower `RAG_MAX_CONTEXT_CHARACTERS`.

### Frontend Cannot Reach Backend

Local frontend:

```env
FRONTEND_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Docker frontend:

```env
FRONTEND_API_BASE_URL=http://backend:8000/api/v1
```

## Current Release

`v1.0.0`

The first portfolio-ready release includes ingestion, vector search, RAG chat, code review, feature planning, documentation generation, evaluation, Docker deployment, automated tests, and a GPT-style frontend.