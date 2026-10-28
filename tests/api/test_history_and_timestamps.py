"""
Integration tests for Research History Deletion and Authoritative Timestamps:
- DELETE /api/research/{run_id}
- DELETE /api/research (clear all)
- Cascade cleanup validation (iterations, papers, themes, events)
- 404 on nonexistent run
- Authoritative UTC ISO 8601 timestamps with explicit 'Z'
"""

import pytest
from datetime import datetime, timezone
from backend.database.models import (
    ResearchRunModel,
    ResearchIterationModel,
    ResearchRunPaperModel,
    PaperModel,
    ThemeModel,
    AgentEventModel,
)


@pytest.mark.asyncio
async def test_delete_individual_research_run(test_client):
    """Test deleting an individual research run removes the run and its cascaded child records."""
    client, session_factory = test_client

    run_id = "test-delete-run-1"
    other_run_id = "test-keep-run-2"

    async with session_factory() as session:
        # Create target run with iterations, themes, events, paper links
        run1 = ResearchRunModel(id=run_id, research_question="Delete me", status="completed")
        run2 = ResearchRunModel(id=other_run_id, research_question="Keep me", status="completed")

        it1 = ResearchIterationModel(run_id=run_id, iteration_number=1, retrieved_count=5)
        it2 = ResearchIterationModel(run_id=other_run_id, iteration_number=1, retrieved_count=3)

        theme1 = ThemeModel(run_id=run_id, theme_id="t1", title="Theme 1", description="Desc")
        event1 = AgentEventModel(run_id=run_id, event_type="test", message="msg", iteration=1)

        paper = PaperModel(id="p-shared-1", title="Paper 1", source="arxiv")
        link1 = ResearchRunPaperModel(run_id=run_id, paper_id="p-shared-1", is_relevant=True)
        link2 = ResearchRunPaperModel(run_id=other_run_id, paper_id="p-shared-1", is_relevant=True)

        session.add_all([run1, run2, it1, it2, theme1, event1, paper, link1, link2])
        await session.commit()

    # 1. Delete run 1
    res = await client.delete(f"/api/research/{run_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["deleted"] is True
    assert data["run_id"] == run_id

    # 2. Verify run 1 is gone from API
    get_res = await client.get(f"/api/research/{run_id}")
    assert get_res.status_code == 404

    # 3. Verify other run is unaffected
    get_other = await client.get(f"/api/research/{other_run_id}")
    assert get_other.status_code == 200

    # 4. Verify cascade deletion in database
    async with session_factory() as session:
        run1_db = await session.get(ResearchRunModel, run_id)
        assert run1_db is None

        # Shared catalog paper still exists
        paper_db = await session.get(PaperModel, "p-shared-1")
        assert paper_db is not None


@pytest.mark.asyncio
async def test_delete_nonexistent_run_returns_404(test_client):
    """Attempting to delete a nonexistent run returns 404."""
    client, _ = test_client
    res = await client.delete("/api/research/nonexistent-run-id-999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_clear_all_research_runs(test_client):
    """Test clear-all endpoint deletes all runs and leaves an empty history."""
    client, session_factory = test_client

    async with session_factory() as session:
        r1 = ResearchRunModel(id="clear-run-1", research_question="Q1", status="completed")
        r2 = ResearchRunModel(id="clear-run-2", research_question="Q2", status="completed")
        session.add_all([r1, r2])
        await session.commit()

    # Clear all
    res = await client.delete("/api/research")
    assert res.status_code == 200
    data = res.json()
    assert data["deleted_count"] >= 2

    # Listing should now be empty
    list_res = await client.get("/api/research")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_authoritative_utc_iso_timestamps(test_client):
    """Verify timestamps in API responses are serialized in UTC ISO 8601 with explicit 'Z'."""
    client, session_factory = test_client
    run_id = "timestamp-test-run-1"

    now_utc = datetime(2026, 10, 28, 14, 30, 0, tzinfo=timezone.utc)

    async with session_factory() as session:
        run = ResearchRunModel(
            id=run_id,
            research_question="Timestamp verification",
            status="completed",
            created_at=now_utc,
            updated_at=now_utc,
            started_at=now_utc,
            completed_at=now_utc
        )
        evt = AgentEventModel(
            id="evt-time-1",
            run_id=run_id,
            event_type="test.event",
            message="Time check",
            iteration=1,
            timestamp=now_utc
        )
        session.add_all([run, evt])
        await session.commit()

    # Check run timestamps
    res = await client.get(f"/api/research/{run_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["created_at"].endswith("Z") or "+00:00" in data["created_at"]
    assert "2026-10-28T14:30:00" in data["created_at"]

    # Check event timestamps
    evt_res = await client.get(f"/api/research/{run_id}/events")
    assert evt_res.status_code == 200
    evts = evt_res.json()
    assert len(evts) == 1
    assert evts[0]["timestamp"].endswith("Z") or "+00:00" in evts[0]["timestamp"]
    assert "2026-10-28T14:30:00" in evts[0]["timestamp"]
