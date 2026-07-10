# Frontend Upgrade Guide

This package replaces only the `frontend` directory and the local frontend run script. It does not require deleting or modifying backend source files.

## Safe migration order

1. Confirm Step 16 is committed and the working tree is clean.
2. Create a dedicated upgrade branch and safety tag.
3. Back up the current frontend outside the repository.
4. Stop the frontend container or local Streamlit process.
5. Replace the `frontend` directory with the new one.
6. Copy the updated `scripts/run_frontend.bat`.
7. Test locally against the existing backend.
8. Rebuild only the frontend Docker image.
9. Run the full Docker stack and complete the smoke test.
10. Commit the upgrade after all modules pass.

## Required smoke test

- Dashboard reports backend and database health.
- Upload creates a project ID.
- File inspection succeeds.
- Chunk preview succeeds.
- Chunk persistence succeeds.
- Embedding generation succeeds.
- Semantic search returns results.
- RAG chat returns an answer with sources.
- Code review returns structured issues.
- Feature planner returns affected files and steps.
- Documentation downloads as Markdown.
- Evaluation runs in retrieval mode.
