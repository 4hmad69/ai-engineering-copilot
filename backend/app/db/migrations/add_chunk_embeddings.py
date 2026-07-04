import asyncio

from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.db.session import close_database_engine, get_database_engine


def _validate_schema_name(schema_name: str) -> str:
    normalized = schema_name.replace("_", "")

    if not normalized.isalnum() or schema_name[0].isdigit():
        raise ValueError(f"Invalid database schema name: {schema_name}")

    return schema_name


def _validate_embedding_dimension(dimension: int) -> int:
    if dimension <= 0 or dimension > 4096:
        raise ValueError(f"Invalid embedding dimension: {dimension}")

    return dimension


async def add_chunk_embedding_columns() -> None:
    settings = get_settings()

    schema_name = _validate_schema_name(settings.database_schema)
    embedding_dimension = _validate_embedding_dimension(settings.embedding_dimension)

    engine = get_database_engine()

    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        await connection.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.chunks
                ADD COLUMN IF NOT EXISTS embedding vector({embedding_dimension})
                """
            )
        )

        await connection.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.chunks
                ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(255)
                """
            )
        )

        await connection.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.chunks
                ADD COLUMN IF NOT EXISTS embedding_dimension INTEGER
                """
            )
        )

        await connection.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.chunks
                ADD COLUMN IF NOT EXISTS is_embedded BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        )

        await connection.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_chunks_project_is_embedded
                ON {schema_name}.chunks (project_id, is_embedded)
                """
            )
        )

    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(add_chunk_embedding_columns())