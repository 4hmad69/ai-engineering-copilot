# AI Engineering Copilot

AI Engineering Copilot is an agentic RAG platform for software projects.

It can understand codebases, answer questions with citations, review code, create feature plans, generate documentation, and evaluate RAG quality.

## Current Status

Step 1 completed:

- FastAPI backend foundation
- Modular API routing
- Environment-based configuration
- Health check endpoint
- Logging setup
- Service layer structure
- Pydantic response schema

Step 2 completed:

- Git hygiene
- README
- Architecture documentation
- Development roadmap
- Backend run script

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- Pydantic Settings
- Uvicorn

### Planned AI Stack

- LangChain
- LangGraph
- Hugging Face embeddings
- PostgreSQL
- pgvector
- Streamlit
- Docker

## Project Structure

```txt
ai-engineering-copilot/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   ├── architecture.md
│   └── roadmap.md
│
├── scripts/
│   └── run_backend.bat
│
├── .gitignore
└── README.md