import asyncio

from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import close_database_engine, get_database_engine


def _validate_schema_name(schema_name: str) -> str:
    normalized = schema_name.replace("_", "")

    if not normalized.isalnum() or schema_name[0].isdigit():
        raise ValueError(f"Invalid database schema name: {schema_name}")

    return schema_name


async def init_database() -> None:
    settings = get_settings()
    schema_name = _validate_schema_name(settings.database_schema)

    engine = get_database_engine()

    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        await connection.run_sync(Base.metadata.create_all)

    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(init_database())
