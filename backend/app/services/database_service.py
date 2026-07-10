from time import perf_counter

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import DatabaseConnectionError
from backend.app.schemas.database_schema import DatabaseHealthResponse


async def get_database_health(
    session: AsyncSession,
) -> DatabaseHealthResponse:
    start_time = perf_counter()

    try:
        database_result = await session.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user
                """
            )
        )

        database_row = database_result.mappings().one()

        pgvector_result = await session.execute(
            text(
                """
                SELECT extversion
                FROM pg_extension
                WHERE extname = 'vector'
                """
            )
        )

        pgvector_version = pgvector_result.scalar_one_or_none()

        latency_ms = round((perf_counter() - start_time) * 1000, 2)

        return DatabaseHealthResponse(
            status="ok",
            database_name=database_row["database_name"],
            database_user=database_row["database_user"],
            pgvector_enabled=pgvector_version is not None,
            pgvector_version=pgvector_version,
            latency_ms=latency_ms,
        )

    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        raise DatabaseConnectionError(
            "Database health check failed. Make sure PostgreSQL is running and DATABASE_URL is correct.",
            details={
                "error_type": exc.__class__.__name__,
                "hint": "Run: docker compose up -d db",
            },
        ) from exc
