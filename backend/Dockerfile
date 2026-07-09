FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && python -m pip install -r /app/backend/requirements.txt

COPY --chown=appuser:appuser backend /app/backend

RUN mkdir -p /app/storage/uploads /app/storage/projects /app/.cache \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD python -m backend.app.db.init_db \
    && python -m backend.app.db.migrations.add_chunk_embeddings \
    && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000