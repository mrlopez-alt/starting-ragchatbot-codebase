"""API endpoint tests for /api/query, /api/courses and the static root."""
import pytest

from conftest import (
    INDEX_HTML,
    SAMPLE_ANSWER,
    SAMPLE_COURSE_TITLES,
    SAMPLE_SESSION_ID,
    SAMPLE_SOURCES,
)

pytestmark = pytest.mark.api


class TestQueryEndpoint:
    def test_query_without_session_creates_one(self, client, mock_rag_system):
        response = client.post("/api/query", json={"query": "What is computer use?"})

        assert response.status_code == 200
        assert response.json() == {
            "answer": SAMPLE_ANSWER,
            "sources": SAMPLE_SOURCES,
            "session_id": SAMPLE_SESSION_ID,
        }
        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once_with("What is computer use?", SAMPLE_SESSION_ID)

    def test_query_with_existing_session_reuses_it(self, client, mock_rag_system):
        response = client.post(
            "/api/query", json={"query": "Tell me more", "session_id": "session_42"}
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session_42"
        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("Tell me more", "session_42")

    def test_query_with_empty_sources(self, client, mock_rag_system):
        mock_rag_system.query.return_value = ("General answer", [])

        response = client.post("/api/query", json={"query": "Hello"})

        assert response.status_code == 200
        assert response.json()["sources"] == []

    def test_query_missing_query_field_returns_422(self, client, mock_rag_system):
        response = client.post("/api/query", json={"session_id": "session_1"})

        assert response.status_code == 422
        mock_rag_system.query.assert_not_called()

    def test_query_wrong_type_returns_422(self, client):
        response = client.post("/api/query", json={"query": 123})

        assert response.status_code == 422

    def test_query_invalid_json_returns_422(self, client):
        response = client.post(
            "/api/query", content="not json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_rag_error_returns_500_with_detail(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("vector store unavailable")

        response = client.post("/api/query", json={"query": "anything"})

        assert response.status_code == 500
        assert response.json() == {"detail": "vector store unavailable"}

    def test_query_get_falls_through_to_static_mount(self, client, mock_rag_system):
        # The POST-only route doesn't match GET, so the request reaches the "/"
        # static mount (as in backend/app.py), which has no such file -> 404.
        response = client.get("/api/query")

        assert response.status_code == 404
        mock_rag_system.query.assert_not_called()


class TestCoursesEndpoint:
    def test_courses_returns_stats(self, client, mock_rag_system):
        response = client.get("/api/courses")

        assert response.status_code == 200
        assert response.json() == {
            "total_courses": len(SAMPLE_COURSE_TITLES),
            "course_titles": SAMPLE_COURSE_TITLES,
        }
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_courses_empty_catalog(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        assert response.json() == {"total_courses": 0, "course_titles": []}

    def test_courses_analytics_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = Exception("chroma down")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert response.json() == {"detail": "chroma down"}

    def test_courses_malformed_analytics_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {"total_courses": 1}

        response = client.get("/api/courses")

        assert response.status_code == 500

    def test_courses_post_method_not_allowed(self, client):
        response = client.post("/api/courses")

        assert response.status_code == 405


class TestRootEndpoint:
    def test_root_serves_index_html(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.text == INDEX_HTML

    def test_unknown_static_path_returns_404(self, client):
        response = client.get("/does-not-exist.js")

        assert response.status_code == 404

    def test_api_routes_take_precedence_over_static_mount(self, client, mock_rag_system):
        response = client.get("/api/courses")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
