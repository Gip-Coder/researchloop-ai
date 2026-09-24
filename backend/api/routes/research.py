"""
FastAPI router for autonomous research operations.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from backend.api.dependencies import get_research_service
from backend.api.schemas.research import (
    AgentEventResponse,
    CreateResearchRequest,
    EvaluationResponse,
    PaperResponse,
    ResearchIterationResponse,
    ResearchResultResponse,
    ResearchRunResponse,
    ThemeResponse,
)
from backend.database.models import ResearchRunModel
from backend.services.research_runner import (
    register_listener,
    unregister_listener,
)
from backend.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["Research"])


def _run_to_response(run: ResearchRunModel) -> ResearchRunResponse:
    total_papers = len(run.run_papers) if run.run_papers else 0
    relevant_papers = sum(1 for rp in run.run_papers if rp.is_relevant is True) if run.run_papers else 0
    themes_count = len(run.themes) if run.themes else 0
    iterations_count = len(run.iterations) if run.iterations else 0

    return ResearchRunResponse(
        id=run.id,
        research_question=run.research_question,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        current_iteration=run.current_iteration,
        max_iterations=run.max_iterations,
        coverage=run.coverage,
        stopping_reason=run.stopping_reason,
        error=run.error,
        total_papers=total_papers,
        relevant_papers_count=relevant_papers,
        themes_count=themes_count,
        iterations_count=iterations_count,
    )


@router.post(
    "",
    response_model=ResearchRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start a new autonomous research run",
)
async def create_research(
    payload: CreateResearchRequest,
    service: ResearchService = Depends(get_research_service),
) -> ResearchRunResponse:
    # 1. Validation
    question = payload.research_question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Research question cannot be empty.",
        )
    if len(question) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Research question must be at least 5 characters long.",
        )

    # 2. Create in DB
    run = await service.create_research_run(question, payload.config)

    # 3. Launch background execution
    await service.start_research_run(run.id)

    return _run_to_response(run)


@router.get(
    "",
    response_model=List[ResearchRunResponse],
    summary="List historical research runs",
)
async def list_research_runs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ResearchService = Depends(get_research_service),
) -> List[ResearchRunResponse]:
    runs = await service.list_runs(limit=limit, offset=offset)
    return [_run_to_response(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=ResearchRunResponse,
    summary="Get status and details of a specific research run",
)
async def get_research_run(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
) -> ResearchRunResponse:
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    return _run_to_response(run)


@router.get(
    "/{run_id}/iterations",
    response_model=List[ResearchIterationResponse],
    summary="Get iterative audit log for a research run",
)
async def get_iterations(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
) -> List[ResearchIterationResponse]:
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    iterations = await service.get_iterations(run_id)
    return [
        ResearchIterationResponse(
            id=it.id,
            run_id=it.run_id,
            iteration_number=it.iteration_number,
            search_plan=it.search_plan,
            queries=it.queries or [],
            retrieved_count=it.retrieved_count,
            new_papers_count=it.new_papers_count,
            relevant_count=it.relevant_count,
            coverage=it.coverage,
            reflection=it.reflection,
            created_at=it.created_at,
        )
        for it in iterations
    ]


@router.get(
    "/{run_id}/papers",
    response_model=List[PaperResponse],
    summary="Get papers discovered for a research run with filtering and sorting",
)
async def get_papers(
    run_id: str,
    is_relevant: Optional[bool] = Query(None, description="Filter by relevance status"),
    source: Optional[str] = Query(None, description="Filter by originating source (arxiv, crossref, etc.)"),
    min_relevance: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum relevance score threshold"),
    search: Optional[str] = Query(None, description="Search keyword in title or abstract"),
    sort_by: Optional[str] = Query("relevance", description="Sort by: relevance, citations, year, title"),
    service: ResearchService = Depends(get_research_service),
) -> List[PaperResponse]:
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    records = await service.get_papers(
        run_id=run_id,
        is_relevant=is_relevant,
        source=source,
        min_relevance=min_relevance,
        search=search,
        sort_by=sort_by,
    )
    return [
        PaperResponse(
            id=paper.id,
            title=paper.title,
            authors=paper.authors or [],
            abstract=paper.abstract,
            year=paper.year,
            venue=paper.venue,
            doi=paper.doi,
            url=paper.url,
            source=paper.source,
            citation_count=paper.citation_count,
            publication_date=paper.publication_date,
            categories=paper.categories or [],
            is_relevant=link.is_relevant,
            relevance_score=link.relevance_score,
            relevance_reason=link.relevance_reason,
            iteration_number=link.iteration_number,
        )
        for paper, link in records
    ]


@router.get(
    "/{run_id}/themes",
    response_model=List[ThemeResponse],
    summary="Get thematic clusters extracted for a research run",
)
async def get_themes(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
) -> List[ThemeResponse]:
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    themes = await service.get_themes(run_id)
    return [
        ThemeResponse(
            id=t.id,
            theme_id=t.theme_id,
            title=t.title,
            description=t.description,
            paper_ids=t.paper_ids or [],
            key_findings=t.key_findings or [],
            contradictions_or_tensions=t.contradictions_or_tensions or [],
        )
        for t in themes
    ]


@router.get(
    "/{run_id}/events",
    response_model=List[AgentEventResponse],
    summary="Get agent telemetry events and execution trace",
)
async def get_events(
    run_id: str,
    after_id: Optional[str] = Query(None, description="Fetch events occurred after this event id"),
    limit: int = Query(500, ge=1, le=1000),
    service: ResearchService = Depends(get_research_service),
) -> List[AgentEventResponse]:
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    events = await service.get_events(run_id, after_id=after_id, limit=limit)
    return [
        AgentEventResponse(
            id=e.id,
            run_id=e.run_id,
            event_type=e.event_type,
            iteration=e.iteration,
            message=e.message,
            timestamp=e.timestamp,
            payload=e.payload or {},
        )
        for e in events
    ]


@router.get(
    "/{run_id}/events/stream",
    summary="Stream live AgentEvents via Server-Sent Events (SSE)",
)
async def stream_events(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
):
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        register_listener(run_id, queue)
        try:
            # Yield initial connection confirmation
            yield f"event: connected\ndata: {json.dumps({'run_id': run_id, 'status': run.status})}\n\n"

            # If already completed or failed, emit current status and close
            if run.status in ("completed", "failed", "cancelled"):
                yield f"event: {run.status}\ndata: {json.dumps({'status': run.status})}\n\n"
                return

            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    evt_type = event_data.get("event_type", "message")
                    yield f"event: {evt_type}\ndata: {json.dumps(event_data)}\n\n"
                    if evt_type in ("research.completed", "research.failed", "research.cancelled"):
                        break
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield ": ping\n\n"
        finally:
            unregister_listener(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{run_id}/result",
    response_model=ResearchResultResponse,
    summary="Get final synthesized literature review and report",
)
async def get_result(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
) -> ResearchResultResponse:
    result = await service.get_result(run_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    return ResearchResultResponse(
        run_id=result["run_id"],
        research_question=result["research_question"],
        status=result["status"],
        coverage_score=result["coverage_score"],
        stop_reason=result["stop_reason"],
        final_review=result["final_review"],
        synthesis=result["synthesis"],
        reflection=result["reflection"],
        metadata=result["metadata"],
    )


@router.get(
    "/{run_id}/evaluation",
    response_model=EvaluationResponse,
    summary="Get comprehensive evaluation metrics and benchmark comparisons",
)
async def get_evaluation(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
) -> EvaluationResponse:
    evaluation = await service.get_evaluation(run_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    return EvaluationResponse(
        run_id=evaluation["run_id"],
        coverage=evaluation.get("coverage", 0.0),
        relevance=evaluation.get("relevance", 0.0),
        coherence=evaluation.get("coherence", 0.0),
        citation_distribution=evaluation.get("citation_distribution", {}),
        topic_coverage=evaluation.get("topic_coverage"),
        paper_recall=evaluation.get("paper_recall"),
        evaluation_type=evaluation.get("evaluation_type", "intrinsic"),
        benchmark_comparison=evaluation.get("benchmark_comparison"),
    )


@router.post(
    "/{run_id}/cancel",
    summary="Cancel an active research run",
)
async def cancel_research(
    run_id: str,
    service: ResearchService = Depends(get_research_service),
):
    run = await service.get_research_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found.",
        )
    cancelled = await service.cancel_run(run_id)
    return {"run_id": run_id, "cancelled": cancelled}
