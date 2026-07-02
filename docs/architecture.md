# AI Engineering Copilot Architecture

## High-Level Idea

AI Engineering Copilot is designed as a modular AI engineering system.

The system allows a user to upload a software project. The backend ingests the codebase, splits the files into chunks, creates embeddings, stores them in a vector database, retrieves relevant context, and uses an LLM to generate grounded answers.

Later modules will add code review, feature planning, documentation generation, and RAG evaluation.

## Current Architecture

```txt
User
 |
 | sends request
 v
FastAPI Backend
 |
 | routes request
 v
API Router
 |
 | calls business logic
 v
Service Layer
 |
 | returns typed response
 v
Pydantic Schema
 |
 | JSON response
 v
User