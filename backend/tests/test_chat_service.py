"""
Chat Service, Chat Session, and Chat History unit tests.

Covers: CHAT-UNIT-001 through CHAT-UNIT-008
        CHATSESS-UNIT-001 through CHATSESS-UNIT-003
        CHATHISTORY-UNIT-001 through CHATHISTORY-UNIT-003

See qa_testing_plan.md Sections 6.3 and 6.9.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.chat_service import _extract_hits
from app.services.chat_session_service import (
    create_chat_session,
    get_chat_session,
    list_user_chat_sessions,
)

# ==========================================================================
# CHAT-UNIT-001, 002, 003: _extract_hits
# ==========================================================================


class TestExtractHits:
    """CHAT-UNIT-001, 002, 003: _extract_hits for different response formats."""

    def test_handles_dict_response_format(self):
        """CHAT-UNIT-001: Extracts hits from a dict response."""
        response = {
            "result": {
                "hits": [
                    {"_id": "1", "fields": {"chunk_text": "hello"}},
                    {"_id": "2", "fields": {"chunk_text": "world"}},
                ]
            }
        }
        hits = _extract_hits(response)
        assert len(hits) == 2
        assert hits[0]["_id"] == "1"

    def test_handles_object_response_format(self):
        """CHAT-UNIT-002: Extracts hits from an object response."""
        mock_hit = MagicMock()
        mock_hit._id = "1"
        mock_result = MagicMock()
        mock_result.hits = [mock_hit]
        mock_response = MagicMock()
        mock_response.result = mock_result
        # Ensure isinstance check doesn't match dict
        type(mock_response).__class__ = type(MagicMock)

        hits = _extract_hits(mock_response)
        assert len(hits) == 1

    def test_returns_empty_for_none_result(self):
        """CHAT-UNIT-003: Returns [] when result is None."""
        # Dict format with no result key
        assert _extract_hits({}) == []
        assert _extract_hits({"result": {}}) == []
        assert _extract_hits({"result": {"hits": None}}) == []
        assert _extract_hits({"result": {"hits": []}}) == []

    def test_returns_empty_for_object_with_none_result(self):
        """Supplementary: Returns [] when object has no result attribute."""
        mock_response = MagicMock(spec=[])  # no attributes
        hits = _extract_hits(mock_response)
        assert hits == []


# ==========================================================================
# CHAT-UNIT-004, 005: _retrieve_documents
# ==========================================================================


class TestRetrieveDocuments:
    """CHAT-UNIT-004, 005: Document retrieval with Pinecone filtering."""

    @patch("app.services.chat_service._get_pinecone_index")
    def test_filters_by_user_id_and_file_ids(self, mock_get_index):
        """CHAT-UNIT-004: Filters search by user_id and file_ids."""
        from app.services.chat_service import _retrieve_documents

        mock_index = MagicMock()
        mock_index.search_records.return_value = {"result": {"hits": []}}
        mock_get_index.return_value = mock_index

        mock_user = MagicMock()
        mock_user.id = 42

        _retrieve_documents(
            query_text="What is photosynthesis?",
            current_user=mock_user,
            file_ids=[1, 2, 3],
        )

        # Verify the filter in the search query
        call_args = mock_index.search_records.call_args
        query = call_args.kwargs.get("query") or call_args[1].get("query")
        assert query["filter"]["user_id"] == "42"
        assert query["filter"]["source_file_id"] == {"$in": [1, 2, 3]}

    @patch("app.services.chat_service._get_pinecone_index")
    @patch("app.services.chat_service.settings")
    def test_skips_hits_with_no_text(self, mock_settings, mock_get_index):
        """CHAT-UNIT-005: Skips hits that have no text content."""
        from app.services.chat_service import _retrieve_documents

        mock_settings.PINECONE_INTEGRATED_TEXT_FIELD = "chunk_text"
        mock_settings.PINECONE_NAMESPACE = "test-ns"
        mock_settings.PINECONE_INDEX_HOST = "host"

        mock_index = MagicMock()
        mock_index.search_records.return_value = {
            "result": {
                "hits": [
                    {"_id": "1", "fields": {"chunk_text": "real content"}},
                    {"_id": "2", "fields": {"chunk_text": ""}},  # empty
                    {"_id": "3", "fields": {}},  # missing
                ]
            }
        }
        mock_get_index.return_value = mock_index

        mock_user = MagicMock()
        mock_user.id = 1

        docs = _retrieve_documents(
            query_text="test", current_user=mock_user, file_ids=[1]
        )
        # Only the first hit has real content
        assert len(docs) == 1
        assert docs[0].page_content == "real content"


# ==========================================================================
# CHAT-UNIT-006, 007, 008: run_conversational_chat error handling
# ==========================================================================


class TestRunConversationalChat:
    """CHAT-UNIT-006, 007, 008: Chat error handling and message saving."""

    @patch("app.services.chat_service._retrieve_documents")
    @patch("app.services.chat_service.PostgresChatMessageHistory")
    @patch("app.services.chat_service.ChatGoogleGenerativeAI")
    @patch("app.services.chat_service.get_chat_session")
    @patch("app.services.chat_service.create_stuff_documents_chain")
    async def test_returns_429_on_quota_error(
        self,
        mock_chain_fn,
        mock_get_session,
        mock_llm_class,
        mock_history_class,
        mock_retrieve,
    ):
        """CHAT-UNIT-006: Returns 429 when Gemini raises resource_exhausted."""
        from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

        from app.schemas.chat_schema import ConversationalChatRequest
        from app.services.chat_service import run_conversational_chat

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ChatGoogleGenerativeAIError(
            "429 resource_exhausted: quota exceeded"
        )
        mock_llm_class.return_value = mock_llm
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_class.return_value = mock_history

        request = ConversationalChatRequest(
            query="test", session_id=uuid.uuid4(), file_ids=[1]
        )

        with pytest.raises(HTTPException) as exc_info:
            await run_conversational_chat(
                request=request, db=MagicMock(), current_user=MagicMock()
            )
        assert exc_info.value.status_code == 429

    @patch("app.services.chat_service._retrieve_documents")
    @patch("app.services.chat_service.PostgresChatMessageHistory")
    @patch("app.services.chat_service.ChatGoogleGenerativeAI")
    @patch("app.services.chat_service.get_chat_session")
    @patch("app.services.chat_service.create_stuff_documents_chain")
    async def test_returns_502_on_generic_error(
        self,
        mock_chain_fn,
        mock_get_session,
        mock_llm_class,
        mock_history_class,
        mock_retrieve,
    ):
        """CHAT-UNIT-007: Returns 502 on generic Gemini error."""
        from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

        from app.schemas.chat_schema import ConversationalChatRequest
        from app.services.chat_service import run_conversational_chat

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ChatGoogleGenerativeAIError(
            "Internal server error"
        )
        mock_llm_class.return_value = mock_llm
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_class.return_value = mock_history

        request = ConversationalChatRequest(
            query="test", session_id=uuid.uuid4(), file_ids=[1]
        )

        with pytest.raises(HTTPException) as exc_info:
            await run_conversational_chat(
                request=request, db=MagicMock(), current_user=MagicMock()
            )
        assert exc_info.value.status_code == 502


# ==========================================================================
# CHATSESS-UNIT-001, 002, 003: Chat session service
# ==========================================================================


class TestChatSessionService:
    """CHATSESS-UNIT-001, 002, 003: Chat session CRUD operations."""

    def test_create_chat_session(self, db_session, test_user):
        """CHATSESS-UNIT-001: create_chat_session creates a session with UUID and default name."""
        session = create_chat_session(db=db_session, current_user=test_user)
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.name == "New Chat"

    def test_get_session_raises_for_other_user(
        self, db_session, test_user, second_user
    ):
        """CHATSESS-UNIT-002: get_chat_session raises 404 when session doesn't belong to user."""
        session = create_chat_session(db=db_session, current_user=test_user)

        with pytest.raises(HTTPException) as exc_info:
            get_chat_session(
                session_id=session.id, db=db_session, current_user=second_user
            )
        assert exc_info.value.status_code == 404

    def test_list_returns_only_current_user_sessions(
        self, db_session, test_user, second_user
    ):
        """CHATSESS-UNIT-003: list_user_chat_sessions returns only current user's sessions."""
        create_chat_session(db=db_session, current_user=test_user)
        create_chat_session(db=db_session, current_user=test_user)
        create_chat_session(db=db_session, current_user=second_user)

        user_sessions = list_user_chat_sessions(db=db_session, current_user=test_user)
        assert len(user_sessions) == 2
        for s in user_sessions:
            assert s.user_id == test_user.id


# ==========================================================================
# CHATHISTORY-UNIT-001, 002, 003: PostgresChatMessageHistory
# ==========================================================================


class TestChatMessageHistory:
    """CHATHISTORY-UNIT-001, 002, 003: Chat message persistence."""

    def test_add_user_message(self, db_session, test_user):
        """CHATHISTORY-UNIT-001: add_user_message persists a human message."""
        from app.models.chat_model import ChatMessage
        from app.services.chat_history import PostgresChatMessageHistory

        session = create_chat_session(db=db_session, current_user=test_user)
        history = PostgresChatMessageHistory(
            session_id=str(session.id), db_session=db_session
        )

        history.add_user_message("What is the mitochondria?")

        messages = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .all()
        )
        assert len(messages) == 1
        assert messages[0].role == "human"
        assert messages[0].content == "What is the mitochondria?"

    def test_add_ai_message(self, db_session, test_user):
        """CHATHISTORY-UNIT-002: add_ai_message persists an AI message."""
        from app.models.chat_model import ChatMessage
        from app.services.chat_history import PostgresChatMessageHistory

        session = create_chat_session(db=db_session, current_user=test_user)
        history = PostgresChatMessageHistory(
            session_id=str(session.id), db_session=db_session
        )

        history.add_ai_message("The mitochondria is the powerhouse of the cell.")

        messages = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .all()
        )
        assert len(messages) == 1
        assert messages[0].role == "ai"

    def test_messages_in_chronological_order(self, db_session, test_user):
        """CHATHISTORY-UNIT-003: messages property returns messages in chronological order."""
        from app.services.chat_history import PostgresChatMessageHistory

        session = create_chat_session(db=db_session, current_user=test_user)
        history = PostgresChatMessageHistory(
            session_id=str(session.id), db_session=db_session
        )

        history.add_user_message("First question")
        history.add_ai_message("First answer")
        history.add_user_message("Second question")

        msgs = history.messages
        assert len(msgs) == 3
        assert msgs[0].content == "First question"
        assert msgs[1].content == "First answer"
        assert msgs[2].content == "Second question"
