"""
Paper repository for saving academic papers and querying research run paper linkages.
"""

from __future__ import annotations

import uuid
from typing import List, Optional, Tuple, Any
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.database.models import PaperModel, ResearchRunPaperModel


class PaperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_paper(self, paper_data: dict[str, Any]) -> PaperModel:
        paper_id = paper_data["id"]
        existing = await self.session.get(PaperModel, paper_id)
        if existing:
            # Update mutable fields
            existing.title = paper_data.get("title", existing.title)
            existing.authors = paper_data.get("authors", existing.authors)
            existing.abstract = paper_data.get("abstract", existing.abstract)
            existing.year = paper_data.get("year", existing.year)
            existing.venue = paper_data.get("venue", existing.venue)
            existing.doi = paper_data.get("doi", existing.doi)
            existing.url = paper_data.get("url", existing.url)
            existing.source = paper_data.get("source", existing.source)
            existing.citation_count = paper_data.get("citation_count", existing.citation_count)
            existing.publication_date = paper_data.get("publication_date", existing.publication_date)
            existing.external_ids = paper_data.get("external_ids", existing.external_ids)
            existing.categories = paper_data.get("categories", existing.categories)
            existing.raw_source_id = paper_data.get("raw_source_id", existing.raw_source_id)
            await self.session.flush()
            return existing
        else:
            new_paper = PaperModel(
                id=paper_id,
                title=paper_data.get("title", ""),
                authors=paper_data.get("authors", []),
                abstract=paper_data.get("abstract"),
                year=paper_data.get("year"),
                venue=paper_data.get("venue"),
                doi=paper_data.get("doi"),
                url=paper_data.get("url"),
                source=paper_data.get("source", "unknown"),
                citation_count=paper_data.get("citation_count", 0),
                publication_date=paper_data.get("publication_date"),
                external_ids=paper_data.get("external_ids", {}),
                categories=paper_data.get("categories", []),
                raw_source_id=paper_data.get("raw_source_id"),
            )
            self.session.add(new_paper)
            await self.session.flush()
            return new_paper

    async def link_run_paper(
        self,
        run_id: str,
        paper_id: str,
        iteration_number: int = 1,
        is_relevant: Optional[bool] = None,
        relevance_score: Optional[float] = None,
        relevance_reason: Optional[str] = None,
    ) -> ResearchRunPaperModel:
        stmt = select(ResearchRunPaperModel).where(
            and_(
                ResearchRunPaperModel.run_id == run_id,
                ResearchRunPaperModel.paper_id == paper_id,
            )
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            if is_relevant is not None:
                existing.is_relevant = is_relevant
            if relevance_score is not None:
                existing.relevance_score = relevance_score
            if relevance_reason is not None:
                existing.relevance_reason = relevance_reason
            await self.session.flush()
            return existing
        else:
            link = ResearchRunPaperModel(
                id=str(uuid.uuid4()),
                run_id=run_id,
                paper_id=paper_id,
                iteration_number=iteration_number,
                is_relevant=is_relevant,
                relevance_score=relevance_score,
                relevance_reason=relevance_reason,
            )
            self.session.add(link)
            await self.session.flush()
            return link

    async def get_papers_for_run(
        self,
        run_id: str,
        is_relevant: Optional[bool] = None,
        source: Optional[str] = None,
        min_relevance: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "relevance",
    ) -> List[Tuple[PaperModel, ResearchRunPaperModel]]:
        stmt = (
            select(PaperModel, ResearchRunPaperModel)
            .join(ResearchRunPaperModel, ResearchRunPaperModel.paper_id == PaperModel.id)
            .where(ResearchRunPaperModel.run_id == run_id)
        )

        if is_relevant is not None:
            stmt = stmt.where(ResearchRunPaperModel.is_relevant == is_relevant)

        if source:
            stmt = stmt.where(PaperModel.source.ilike(f"%{source}%"))

        if min_relevance is not None:
            stmt = stmt.where(ResearchRunPaperModel.relevance_score >= min_relevance)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    PaperModel.title.ilike(search_term),
                    PaperModel.abstract.ilike(search_term),
                )
            )

        # Sorting
        if sort_by == "relevance":
            stmt = stmt.order_by(
                desc(ResearchRunPaperModel.relevance_score).nullslast(),
                desc(PaperModel.citation_count),
            )
        elif sort_by == "citations":
            stmt = stmt.order_by(desc(PaperModel.citation_count))
        elif sort_by == "year":
            stmt = stmt.order_by(desc(PaperModel.year).nullslast())
        elif sort_by == "title":
            stmt = stmt.order_by(asc(PaperModel.title))
        else:
            stmt = stmt.order_by(desc(ResearchRunPaperModel.relevance_score).nullslast())

        res = await self.session.execute(stmt)
        return list(res.all())
