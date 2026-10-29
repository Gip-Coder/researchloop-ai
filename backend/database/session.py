"""
Database engine and session management for researchloop-ai.
Supports asynchronous SQLite (default for zero-configuration local runs) and PostgreSQL.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.database.models import Base

# Default to SQLite with aiosqlite for zero-credential / mock-mode offline execution
DEFAULT_DB_URL = "sqlite+aiosqlite:///./researchloop.db"


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", DEFAULT_DB_URL).strip()
    if not url:
        return DEFAULT_DB_URL
    # Normalize postgres URL if needed
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_url = get_database_url()
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database tables and apply lightweight migrations for SQLite."""
    eng = engine or get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Lightweight schema migration for SQLite (ensures newly added columns exist and nullability matches)
        if str(eng.url).startswith("sqlite"):
            def _migrate_sqlite_columns(connection):
                cursor = connection.connection.cursor()
                cursor.execute("PRAGMA table_info(papers)")
                raw_cols = cursor.fetchall()
                existing = [c[1] for c in raw_cols]
                if existing:
                    if "citation_count_available" not in existing:
                        cursor.execute("ALTER TABLE papers ADD COLUMN citation_count_available BOOLEAN DEFAULT 0")
                    if "matched_queries" not in existing:
                        cursor.execute("ALTER TABLE papers ADD COLUMN matched_queries JSON DEFAULT '[]'")
                    if "is_foundational_exception" not in existing:
                        cursor.execute("ALTER TABLE papers ADD COLUMN is_foundational_exception BOOLEAN DEFAULT 0")

                    # Check if citation_count has old NOT NULL constraint (notnull == 1)
                    cit_col = [c for c in raw_cols if c[1] == "citation_count"]
                    if cit_col and cit_col[0][3] == 1:
                        cursor.execute("PRAGMA foreign_keys = OFF;")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS papers_migrated (
                                id VARCHAR(255) NOT NULL, 
                                title TEXT NOT NULL, 
                                authors JSON NOT NULL, 
                                abstract TEXT, 
                                year INTEGER, 
                                venue VARCHAR(255), 
                                doi VARCHAR(255), 
                                url VARCHAR(1024), 
                                source VARCHAR(64) NOT NULL, 
                                citation_count INTEGER, 
                                citation_count_available BOOLEAN NOT NULL DEFAULT 0, 
                                matched_queries JSON NOT NULL DEFAULT '[]', 
                                is_foundational_exception BOOLEAN NOT NULL DEFAULT 0, 
                                publication_date VARCHAR(64), 
                                external_ids JSON NOT NULL DEFAULT '{}', 
                                categories JSON NOT NULL DEFAULT '[]', 
                                raw_source_id VARCHAR(255), 
                                created_at DATETIME NOT NULL, 
                                PRIMARY KEY (id)
                            );
                        """)
                        cursor.execute("""
                            INSERT INTO papers_migrated (
                                id, title, authors, abstract, year, venue, doi, url, source,
                                citation_count, citation_count_available, matched_queries, is_foundational_exception,
                                publication_date, external_ids, categories, raw_source_id, created_at
                            )
                            SELECT 
                                id, title, authors, abstract, year, venue, doi, url, source,
                                citation_count, 
                                COALESCE(citation_count_available, 0), 
                                COALESCE(matched_queries, '[]'), 
                                COALESCE(is_foundational_exception, 0),
                                publication_date, external_ids, categories, raw_source_id, created_at
                            FROM papers;
                        """)
                        cursor.execute("DROP TABLE papers;")
                        cursor.execute("ALTER TABLE papers_migrated RENAME TO papers;")
                        cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.close()

            await conn.run_sync(_migrate_sqlite_columns)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
