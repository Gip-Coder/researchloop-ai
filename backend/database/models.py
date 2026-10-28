"""
SQLAlchemy ORM models for researchloop-ai application persistence.
Captures research runs, iterations, papers, themes, agent events, and evaluations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchRunModel(Base):
    """
    Persistent record of an end-to-end research session.
    """
    __tablename__ = "research_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    research_question = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    current_iteration = Column(Integer, default=0, nullable=False)
    max_iterations = Column(Integer, default=3, nullable=False)
    coverage = Column(Float, default=0.0, nullable=False)
    stopping_reason = Column(String(255), nullable=True)
    error = Column(Text, nullable=True)

    config = Column(JSON, nullable=True)
    final_review = Column(JSON, nullable=True)
    synthesis = Column(JSON, nullable=True)
    reflection = Column(JSON, nullable=True)
    evaluation = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    iterations = relationship(
        "ResearchIterationModel",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ResearchIterationModel.iteration_number",
        lazy="selectin",
    )
    run_papers = relationship(
        "ResearchRunPaperModel",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    themes = relationship(
        "ThemeModel",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events = relationship(
        "AgentEventModel",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentEventModel.timestamp",
        lazy="selectin",
    )


class ResearchIterationModel(Base):
    """
    Audit log of an individual iteration within a research run.
    """
    __tablename__ = "research_iterations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    
    search_plan = Column(JSON, nullable=True)
    queries = Column(JSON, default=list, nullable=True)
    retrieved_count = Column(Integer, default=0, nullable=False)
    new_papers_count = Column(Integer, default=0, nullable=False)
    relevant_count = Column(Integer, default=0, nullable=False)
    coverage = Column(Float, default=0.0, nullable=False)
    reflection = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run = relationship("ResearchRunModel", back_populates="iterations")


class PaperModel(Base):
    """
    Canonical academic paper catalog normalized across academic providers.
    """
    __tablename__ = "papers"

    id = Column(String(255), primary_key=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list, nullable=False)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True, index=True)
    venue = Column(String(255), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    url = Column(String(1024), nullable=True)
    source = Column(String(64), nullable=False, index=True)
    citation_count = Column(Integer, nullable=True, default=None)
    citation_count_available = Column(Boolean, default=False, nullable=False)
    matched_queries = Column(JSON, default=list, nullable=False)
    is_foundational_exception = Column(Boolean, default=False, nullable=False)
    publication_date = Column(String(64), nullable=True)
    external_ids = Column(JSON, default=dict, nullable=False)
    categories = Column(JSON, default=list, nullable=False)
    raw_source_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run_links = relationship("ResearchRunPaperModel", back_populates="paper", cascade="all, delete-orphan")


class ResearchRunPaperModel(Base):
    """
    Association link between a research run and a paper, storing relevance evaluations.
    """
    __tablename__ = "research_run_papers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(String(255), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    iteration_number = Column(Integer, default=1, nullable=False)
    
    is_relevant = Column(Boolean, nullable=True, index=True)
    relevance_score = Column(Float, nullable=True)
    relevance_reason = Column(Text, nullable=True)

    run = relationship("ResearchRunModel", back_populates="run_papers")
    paper = relationship("PaperModel", back_populates="run_links", lazy="joined")


class ThemeModel(Base):
    """
    Synthesized thematic cluster discovered across papers in a research run.
    """
    __tablename__ = "themes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    paper_ids = Column(JSON, default=list, nullable=False)
    key_findings = Column(JSON, default=list, nullable=False)
    contradictions_or_tensions = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run = relationship("ResearchRunModel", back_populates="themes")


class AgentEventModel(Base):
    """
    Chronological trace of agent decisions, tool invocations, and lifecycle events.
    """
    __tablename__ = "agent_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    iteration = Column(Integer, default=0, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    payload = Column(JSON, default=dict, nullable=False)

    run = relationship("ResearchRunModel", back_populates="events")
