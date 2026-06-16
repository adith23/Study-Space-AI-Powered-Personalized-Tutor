"""
Chat API integration tests and Chat Session integration tests.

Covers: CHAT-INT-001 through CHAT-INT-005
        CHATSESS-INT-001 through CHATSESS-INT-004

See qa_testing_plan.md Sections 7.3 and 7.4.
"""

import uuid

import pytest
from unittest.mock import patch, MagicMock

# ==========================================================================
# CHATSESS-INT-001 through 004: Chat Session API
# ==========================================================================


class TestChatSessionAPI:
    """CHATSESS-INT-001 through 004: POST/GET /api/v1/materials/chat/sessions."""

    def test_create_session(self, client, test_user, auth_headers):
        """CHATSESS-INT-001: POST /chat/sessions creates a new session (201)."""
        response = client.post(
            "/api/v1/materials/chat/sessions",
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "New Chat"

    def test_list_sessions_returns_only_current_user(
        self, client, test_user, second_user, auth_headers, second_user_headers
    ):
        """CHATSESS-INT-002: GET /chat/sessions returns only current user's sessions."""
        # Create sessions for test_user
        client.post("/api/v1/materials/chat/sessions", headers=auth_headers)
        client.post("/api/v1/materials/chat/sessions", headers=auth_headers)

        # Create session for second_user
        client.post("/api/v1/materials/chat/sessions", headers=second_user_headers)

        # List as test_user
        response = client.get("/api/v1/materials/chat/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_session_messages(self, client, db_session, test_user, auth_headers):
        """CHATSESS-INT-003: GET /chat/sessions/{id}/messages returns messages."""
        from app.services.chat_session_service import create_chat_session
        from app.services.chat_history import PostgresChatMessageHistory

        session = create_chat_session(db=db_session, current_user=test_user)
        history = PostgresChatMessageHistory(
            session_id=str(session.id), db_session=db_session
        )
        history.add_user_message("Hello!")
        history.add_ai_message("Hi there!")

        response = client.get(
            f"/api/v1/materials/chat/sessions/{session.id}/messages",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "human"
        assert data[1]["role"] == "ai"

    def test_user_b_cannot_list_user_a_messages(
        self, client, db_session, test_user, second_user, second_user_headers
    ):
        """CHATSESS-INT-004: User A's session messages are 404 for User B."""
        from app.services.chat_session_service import create_chat_session

        session = create_chat_session(db=db_session, current_user=test_user)

        response = client.get(
            f"/api/v1/materials/chat/sessions/{session.id}/messages",
            headers=second_user_headers,
        )
        assert response.status_code == 404


# ==========================================================================
# CHAT-INT-001 through 005: Chat API
# ==========================================================================


class TestChatAPI:
    """CHAT-INT-001, 002, 004, 005: POST /api/v1/materials/chat."""

    @patch("app.services.chat_service._retrieve_documents")
    @patch("app.services.chat_service.create_stuff_documents_chain")
    @patch("app.services.chat_service.ChatGoogleGenerativeAI")
    def test_chat_with_valid_session_returns_response(
        self,
        mock_llm_class,
        mock_chain_fn,
        mock_retrieve,
        client,
        db_session,
        test_user,
        auth_headers,
    ):
        """CHAT-INT-001: POST /chat with valid session returns AI response."""
        from app.services.chat_session_service import create_chat_session

        session = create_chat_session(db=db_session, current_user=test_user)

        # Configure mocks
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="standalone question")
        mock_llm_class.return_value = mock_llm
        mock_retrieve.return_value = []
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "The answer is 42."
        mock_chain_fn.return_value = mock_chain

        response = client.post(
            "/api/v1/materials/chat",
            headers=auth_headers,
            json={
                "query": "What is the meaning of life?",
                "session_id": str(session.id),
                "file_ids": [1],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "The answer is 42."

    @patch("app.services.chat_service._retrieve_documents")
    @patch("app.services.chat_service.create_stuff_documents_chain")
    @patch("app.services.chat_service.ChatGoogleGenerativeAI")
    def test_chat_with_invalid_session_returns_404(
        self,
        mock_llm_class,
        mock_chain_fn,
        mock_retrieve,
        client,
        test_user,
        auth_headers,
    ):
        """CHAT-INT-004: POST /chat with invalid session_id returns 404."""
        fake_session_id = str(uuid.uuid4())

        response = client.post(
            "/api/v1/materials/chat",
            headers=auth_headers,
            json={
                "query": "Hello",
                "session_id": fake_session_id,
                "file_ids": [1],
            },
        )
        assert response.status_code == 404
