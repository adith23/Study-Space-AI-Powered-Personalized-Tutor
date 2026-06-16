"""
Content Generation Context Service unit tests.

Covers: CTXSVC-UNIT-001 through CTXSVC-UNIT-008

See qa_testing_plan.md Section 6.8.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.material_model import ProcessingStatus
from app.models.quiz_model import QuizGenerationMode
from app.services.content_generation_context_service import (
    _build_broad_context, _extract_hits, build_content_generation_context,
    get_valid_selected_files)

# ==========================================================================
# CTXSVC-UNIT-001, 002, 003: get_valid_selected_files
# ==========================================================================


class TestGetValidSelectedFiles:
    """CTXSVC-UNIT-001, 002, 003: File validation for content generation."""

    def test_raises_when_file_ids_dont_belong_to_user(
        self, db_session, test_user, second_user
    ):
        """CTXSVC-UNIT-001: Raises ValueError when file_ids don't belong to the user."""
        from app.models.material_model import FileType, UploadedFile

        # Create a file belonging to test_user
        file_record = UploadedFile(
            name="notes.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        # second_user tries to access it
        with pytest.raises(ValueError, match="not found"):
            get_valid_selected_files(
                db=db_session, current_user=second_user, file_ids=[file_record.id]
            )

    def test_raises_when_files_not_fully_processed(self, db_session, test_user):
        """CTXSVC-UNIT-002: Raises ValueError when files aren't processed (status ≠ SUCCESS)."""
        from app.models.material_model import FileType, UploadedFile

        file_record = UploadedFile(
            name="pending.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.PENDING,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        with pytest.raises(ValueError, match="processed successfully"):
            get_valid_selected_files(
                db=db_session, current_user=test_user, file_ids=[file_record.id]
            )

    def test_returns_files_in_input_order(self, db_session, test_user):
        """CTXSVC-UNIT-003: Returns files in the same order as input file_ids."""
        from app.models.material_model import FileType, UploadedFile

        files = []
        for name in ["first.pdf", "second.pdf", "third.pdf"]:
            f = UploadedFile(
                name=name,
                file_type=FileType.pdf,
                status=ProcessingStatus.SUCCESS,
                user_id=test_user.id,
            )
            db_session.add(f)
            db_session.commit()
            db_session.refresh(f)
            files.append(f)

        # Request in reverse order
        result = get_valid_selected_files(
            db=db_session,
            current_user=test_user,
            file_ids=[files[2].id, files[0].id, files[1].id],
        )
        assert result[0].id == files[2].id
        assert result[1].id == files[0].id
        assert result[2].id == files[1].id

    def test_raises_for_nonexistent_file_id(self, db_session, test_user):
        """Supplementary: Raises ValueError for a file_id that doesn't exist at all."""
        with pytest.raises(ValueError, match="not found"):
            get_valid_selected_files(
                db=db_session, current_user=test_user, file_ids=[99999]
            )


# ==========================================================================
# CTXSVC-UNIT-004, 005: _build_broad_context
# ==========================================================================


class TestBuildBroadContext:
    """CTXSVC-UNIT-004, 005: Broad context building from chunks."""

    def test_orders_chunks_by_file_position_then_index(self, db_session, test_user):
        """CTXSVC-UNIT-004: Orders chunks by file position then chunk_index."""
        from app.models.material_model import (DocumentChunk, FileType,
                                               UploadedFile)

        # Create two files
        file_a = UploadedFile(
            name="file_a.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        file_b = UploadedFile(
            name="file_b.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add_all([file_a, file_b])
        db_session.commit()
        db_session.refresh(file_a)
        db_session.refresh(file_b)

        # Add chunks (insert in non-sequential order to test sorting)
        chunks = [
            DocumentChunk(
                content="B chunk 1",
                vector_id="b1",
                source_file_id=file_b.id,
                metadata_={"chunk_index": 0},
            ),
            DocumentChunk(
                content="A chunk 2",
                vector_id="a2",
                source_file_id=file_a.id,
                metadata_={"chunk_index": 1},
            ),
            DocumentChunk(
                content="A chunk 1",
                vector_id="a1",
                source_file_id=file_a.id,
                metadata_={"chunk_index": 0},
            ),
            DocumentChunk(
                content="B chunk 2",
                vector_id="b2",
                source_file_id=file_b.id,
                metadata_={"chunk_index": 1},
            ),
        ]
        db_session.add_all(chunks)
        db_session.commit()

        # Request files in order: file_a first, file_b second
        files = [file_a, file_b]
        context = _build_broad_context(db=db_session, files=files)

        # Context should be ordered: A-chunk0, A-chunk1, B-chunk0, B-chunk1
        assert "A chunk 1" in context.context_text
        assert "A chunk 2" in context.context_text
        a1_pos = context.context_text.index("A chunk 1")
        a2_pos = context.context_text.index("A chunk 2")
        b1_pos = context.context_text.index("B chunk 1")
        assert a1_pos < a2_pos < b1_pos

    def test_raises_when_no_chunks_exist(self, db_session, test_user):
        """CTXSVC-UNIT-005: Raises ValueError when no chunks exist."""
        from app.models.material_model import FileType, UploadedFile

        file_record = UploadedFile(
            name="empty.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        with pytest.raises(ValueError, match="No processed content"):
            _build_broad_context(db=db_session, files=[file_record])


# ==========================================================================
# CTXSVC-UNIT-006, 007: build_content_generation_context mode selection
# ==========================================================================


class TestBuildContentGenerationContext:
    """CTXSVC-UNIT-006, 007: Mode selection (focused vs broad)."""

    @patch("app.services.content_generation_context_service._build_focused_context")
    def test_uses_focused_mode_when_focus_prompt_set(self, mock_focused):
        """CTXSVC-UNIT-006: Uses FOCUSED_RAG mode when focus_prompt is set."""
        mock_focused.return_value = MagicMock(mode=QuizGenerationMode.FOCUSED_RAG)

        result = build_content_generation_context(
            db=MagicMock(),
            current_user=MagicMock(),
            files=[MagicMock()],
            focus_prompt="mitochondria",
            item_count=5,
        )
        assert result.mode == QuizGenerationMode.FOCUSED_RAG
        mock_focused.assert_called_once()

    @patch("app.services.content_generation_context_service._build_broad_context")
    def test_uses_broad_mode_when_no_focus_prompt(self, mock_broad):
        """CTXSVC-UNIT-007: Uses BROAD_FULL_SOURCE mode when focus_prompt is None."""
        mock_broad.return_value = MagicMock(mode=QuizGenerationMode.BROAD_FULL_SOURCE)

        result = build_content_generation_context(
            db=MagicMock(),
            current_user=MagicMock(),
            files=[MagicMock()],
            focus_prompt=None,
            item_count=5,
        )
        assert result.mode == QuizGenerationMode.BROAD_FULL_SOURCE
        mock_broad.assert_called_once()


# ==========================================================================
# CTXSVC-UNIT-008: _extract_hits (mirrors chat_service)
# ==========================================================================


class TestContextServiceExtractHits:
    """CTXSVC-UNIT-008: _extract_hits handles both dict and object formats."""

    def test_dict_format(self):
        """Dict format with result.hits."""
        response = {"result": {"hits": [{"_id": "1"}]}}
        assert len(_extract_hits(response)) == 1

    def test_object_format(self):
        """Object format with result.hits attribute."""
        mock_response = MagicMock()
        mock_response.result.hits = [MagicMock()]
        hits = _extract_hits(mock_response)
        assert len(hits) == 1

    def test_empty_response(self):
        """Empty/None result returns []."""
        assert _extract_hits({}) == []
