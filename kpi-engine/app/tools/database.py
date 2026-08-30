from typing import Any

from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


def execute_query(query: str, params: dict[str, Any] | None = None):
    with engine.begin() as connection:
        result = connection.execute(
            text(query),
            params or {},
        )

        return [dict(row._mapping) for row in result]