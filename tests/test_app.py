import pytest
import json
from unittest.mock import patch, AsyncMock
from pymongo.errors import PyMongoError
from app.models import ChatRequest
from app.service_exceptions import AgentNotAvailable


@pytest.fixture(autouse=True)
def mock_db_session():
    """Mock database session for all tests"""
    with (
        patch("app.db.sessions", new_callable=AsyncMock) as mock_sessions,
        patch("app.db.records", new_callable=AsyncMock) as mock_records,
    ):
        yield mock_sessions, mock_records


def test_chat_database_error(client):
    with patch(
        "app.app.get_or_create_session", new_callable=AsyncMock
    ) as mock_get_session:
        mock_get_session.side_effect = PyMongoError("Database error")

        request = ChatRequest(session_id="", message="Test")
        response = client.post("/chat", json=request.model_dump())

        assert response.status_code == 503
        assert (
            response.json().get("detail")
            == "Database service is temporarily unavailable"
        )


def test_chat_agent_error(client, mock_db_session):
    mock_sessions, _ = mock_db_session
    mock_sessions.find_one.return_value = None

    with patch(
        "app.insurance_agent.InsuranceAgent.respond", new_callable=AsyncMock
    ) as mock_respond:
        mock_respond.side_effect = AgentNotAvailable("Agent error")
        request = ChatRequest(session_id="", message="Test")
        response = client.post("/chat", json=request.model_dump())
        assert response.status_code == 503
        assert "AI Agent is temporarily unavailable" in response.json()["detail"]


def test_chat_invalid_json_response(client, mock_db_session):
    mock_sessions, _ = mock_db_session
    mock_sessions.find_one.return_value = None

    with patch(
        "app.insurance_agent.InsuranceAgent.respond", new_callable=AsyncMock
    ) as mock_respond:
        mock_respond.return_value = "invalid json"
        request = ChatRequest(session_id="", message="Test")
        response = client.post("/chat", json=request.model_dump())
        assert response.status_code == 500
        assert "Error processing agent response" in response.json()["detail"]


def test_chat_missing_next_question(client, mock_db_session):
    mock_sessions, _ = mock_db_session
    mock_sessions.find_one.return_value = None

    with patch(
        "app.insurance_agent.InsuranceAgent.respond", new_callable=AsyncMock
    ) as mock_respond:
        mock_respond.return_value = json.dumps({"complete": False})
        request = ChatRequest(session_id="", message="Test")
        response = client.post("/chat", json=request.model_dump())
        assert response.status_code == 500
        assert "Invalid agent response format" in response.json()["detail"]
