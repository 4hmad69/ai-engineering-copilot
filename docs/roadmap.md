# Development Roadmap

## Phase 1: Backend Foundation

Status: Completed

Goals:

- Create FastAPI app
- Add settings management
- Add logging
- Add health check route
- Add clean project structure
- Add placeholder API modules

## Phase 2: Project Hygiene

Status: Completed

Goals:

- Add .gitignore
- Add README
- Add architecture docs
- Add roadmap docs
- Add backend run script

## Phase 3: File Upload And Ingestion

Status: Next

Goals:

- Add upload endpoint
- Accept zipped codebase
- Save uploaded file
- Extract zip safely
- Create project ID
- Return upload summary

## Phase 4: Codebase Loader

Status: Planned

Goals:

- Load supported files
- Support .py, .md, .txt, .json, .yaml
- Skip unsupported files
- Attach metadata
- Track file paths

## Phase 5: Chunking

Status: Planned

Goals:

- Split files by lines
- Store start and end line numbers
- Preserve file metadata
- Prepare chunks for embedding

## Phase 6: Embeddings And Vector Database

Status: Planned

Goals:

- Add Hugging Face embeddings
- Add PostgreSQL
- Add pgvector
- Store chunks as vectors
- Search chunks by similarity

## Phase 7: RAG Q&A

Status: Planned

Goals:

- Retrieve relevant chunks
- Format context
- Create prompt template
- Generate answer
- Return citations
- Return structured JSON

## Phase 8: Streamlit Frontend

Status: Planned

Goals:

- Upload codebase from UI
- Ask questions from UI
- Show answer
- Show citations
- Show confidence

## Phase 9: Code Review Chain

Status: Planned

Goals:

- Accept pasted code or Git diff
- Analyze issues
- Return structured review report
- Classify severity
- Suggest fixes

## Phase 10: Feature Planner Agent

Status: Planned

Goals:

- Accept feature request
- Retrieve relevant code context
- Identify affected files
- Generate implementation plan
- Suggest tests
- Estimate complexity

## Phase 11: RAG Evaluation Dashboard

Status: Planned

Goals:

- Run test questions
- Compare top-k values
- Compare chunk sizes
- Track latency
- Track answer quality
- Track citation quality

## Phase 12: Docker And Deployment

Status: Planned

Goals:

- Add Dockerfile
- Add docker-compose.yml
- Run backend, frontend, and database together
- Prepare project for portfolio demo