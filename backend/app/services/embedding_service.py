from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.app.config import Settings


@lru_cache(maxsize=1)
def _load_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def generate_embeddings(
    texts: list[str],
    settings: Settings,
) -> list[list[float]]:
    if not texts:
        return []

    model = _load_embedding_model(settings.embedding_model_name)

    embeddings = model.encode(
        texts,
        batch_size=settings.embedding_batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    vectors = embeddings.tolist()

    for vector in vectors:
        if len(vector) != settings.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch. "
                f"Expected {settings.embedding_dimension}, got {len(vector)}."
            )

    return vectors


def generate_query_embedding(
    query: str,
    settings: Settings,
) -> list[float]:
    return generate_embeddings(
        texts=[query],
        settings=settings,
    )[0]