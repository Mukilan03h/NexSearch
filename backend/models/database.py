"""
PostgreSQL database setup using SQLAlchemy async engine.
Stores research queries, reports metadata, and paper references.
"""
import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class ResearchQueryDB(Base):
    """Stores each research query and its metadata."""
    __tablename__ = "research_queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    papers_fetched = Column(Integer, default=0)
    papers_analyzed = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_time_seconds = Column(Float, nullable=True)
    search_plan = Column(JSON, nullable=True)


class ReportDB(Base):
    """Stores generated research reports."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String, nullable=False)
    query_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    markdown_content = Column(Text, nullable=True)
    minio_path = Column(String(500), nullable=True)
    papers_count = Column(Integer, default=0)
    themes = Column(JSON, nullable=True)
    citations = Column(JSON, nullable=True)
    top_papers = Column(JSON, nullable=True)


class PaperDB(Base):
    """Stores paper metadata for deduplication and history."""
    __tablename__ = "papers"

    id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON, nullable=True)
    abstract = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=True)
    url = Column(String(1000), nullable=True)
    source = Column(String(50), nullable=False)
    citations = Column(Integer, nullable=True)
    pdf_url = Column(String(1000), nullable=True)
    doi = Column(String(200), nullable=True)
    minio_pdf_path = Column(String(500), nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)


# --- Engine & Session Factory ---

_engine = None
_session_factory = None


def get_database_url(
    host: str = "postgres",
    port: int = 5432,
    db: str = "research_assistant",
    user: str = "research_user",
    password: str = "research_pass_2026",
) -> str:
    """Build async PostgreSQL connection URL."""
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def init_database(database_url: str) -> None:
    """Initialize the database engine and create all tables."""
    global _engine, _session_factory

    _engine = create_async_engine(database_url, echo=False, pool_size=5, max_overflow=10)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    async with _session_factory() as session:
        yield session


async def close_database() -> None:
    """Close the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
