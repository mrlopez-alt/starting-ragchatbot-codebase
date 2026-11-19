"""Shared fixtures for the RAG system test suite.

backend/app.py builds a real RAGSystem (ChromaDB + embeddings + Anthropic client)
at import time and mounts ../frontend as static files, so importing it in tests
is slow and fails when the frontend directory isn't reachable. Instead,
`create_test_app` builds an app with the same API contract as app.py, wired to
a mocked RAG system and a temporary static directory.
"""

from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from pydantic import BaseModel

# --- Test data -------------------------------------------------------------

SAMPLE_COURSE_TITLES = [
    "Building Towards Computer Use with Anthropic",
    "MCP: Build Rich-Context AI Apps with Anthropic",
]
SAMPLE_ANSWER = (
    "Computer use lets Claude operate a desktop through screenshots and actions."
)
SAMPLE_SOURCES = ["Building Towards Computer Use with Anthropic - Lesson 1"]
SAMPLE_SESSION_ID = "session_1"
INDEX_HTML = (
    "<!DOCTYPE html><html><body><h1>Course Materials Assistant</h1></body></html>"
)


# --- Request/response models (mirror backend/app.py) -----------------------


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


def create_test_app(rag_system, static_dir: Optional[str] = None) -> FastAPI:
    """Build a FastAPI app with the same endpoints as backend/app.py."""
    app = FastAPI(title="Course Materials RAG System (test)")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if static_dir is not None:
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


# --- Fixtures --------------------------------------------------------------


@pytest.fixture
def mock_rag_system():
    """RAG system double with happy-path return values."""
    rag = MagicMock()
    rag.session_manager.create_session.return_value = SAMPLE_SESSION_ID
    rag.query.return_value = (SAMPLE_ANSWER, list(SAMPLE_SOURCES))
    rag.get_course_analytics.return_value = {
        "total_courses": len(SAMPLE_COURSE_TITLES),
        "course_titles": list(SAMPLE_COURSE_TITLES),
    }
    return rag


@pytest.fixture
def static_dir(tmp_path):
    """Temporary frontend directory with a minimal index.html."""
    (tmp_path / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def test_app(mock_rag_system, static_dir):
    return create_test_app(mock_rag_system, static_dir=str(static_dir))


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as c:
        yield c
