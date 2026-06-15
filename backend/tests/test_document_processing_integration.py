"""
Document Processing integration tests.

Covers: DOCPROC-INT-001 through DOCPROC-INT-006

See qa_testing_plan.md Section 7.8.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.models.material_model import UploadedFile, DocumentChunk, FileType, ProcessingStatus
from app.services.document_processor import process_and_embed_document


# ==========================================================================
# Helpers
# ==========================================================================

SAMPLE_MARKDOWN = """# Introduction
This is the introduction to the study material. It covers key concepts
in biology including cells, DNA, and evolution.

## Cell Biology
Cells are the basic building blocks of life. Every organism is composed
of one or more cells. The cell membrane controls what enters and exits.

## Genetics
DNA carries the genetic information that determines the traits of organisms.
Genes are segments of DNA that code for specific proteins.
"""


def _create_pending_file(db_session, user, stored_path="/fake/test.pdf"):
    """Create a PENDING UploadedFile record."""
    f = UploadedFile(
        name="test_document.pdf",
        stored_path=stored_path,
        file_type=FileType.pdf,
        status=ProcessingStatus.PENDING,
        user_id=user.id,
    )
    db_session.add(f)
    db_session.commit()
    db_session.refresh(f)
    return f


# ==========================================================================
# DOCPROC-INT-001 through 006
# ==========================================================================


class TestProcessAndEmbedDocument:
    """DOCPROC-INT-001 through 006: Document processing pipeline."""

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_transitions_to_success(self, mock_extract, mock_index_fn, db_session, test_user):
        """DOCPROC-INT-001: File transitions PENDING → PROCESSING → SUCCESS."""
        mock_extract.return_value = SAMPLE_MARKDOWN
        mock_index = MagicMock()
        mock_index_fn.return_value = mock_index

        file_record = _create_pending_file(db_session, test_user)
        assert str(file_record.status) == ProcessingStatus.PENDING.value

        process_and_embed_document(db=db_session, file_id=file_record.id)

        db_session.refresh(file_record)
        assert str(file_record.status) == ProcessingStatus.SUCCESS.value

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_creates_document_chunks(self, mock_extract, mock_index_fn, db_session, test_user):
        """DOCPROC-INT-002: Processing creates correct number of DocumentChunk records."""
        mock_extract.return_value = SAMPLE_MARKDOWN
        mock_index = MagicMock()
        mock_index_fn.return_value = mock_index

        file_record = _create_pending_file(db_session, test_user)
        process_and_embed_document(db=db_session, file_id=file_record.id)

        chunks = (
            db_session.query(DocumentChunk)
            .filter(DocumentChunk.source_file_id == file_record.id)
            .all()
        )
        assert len(chunks) > 0
        # Each chunk should have content and a vector_id
        for chunk in chunks:
            assert chunk.content
            assert chunk.vector_id
            assert chunk.source_file_id == file_record.id

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_calls_pinecone_upsert(self, mock_extract, mock_index_fn, db_session, test_user):
        """DOCPROC-INT-003: Processing calls Pinecone upsert_records with correct namespace."""
        mock_extract.return_value = SAMPLE_MARKDOWN
        mock_index = MagicMock()
        mock_index_fn.return_value = mock_index

        file_record = _create_pending_file(db_session, test_user)
        process_and_embed_document(db=db_session, file_id=file_record.id)

        mock_index.upsert_records.assert_called_once()
        call_kwargs = mock_index.upsert_records.call_args.kwargs
        assert "namespace" in call_kwargs
        assert "records" in call_kwargs
        assert len(call_kwargs["records"]) > 0

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_failed_processing_sets_failed_status(
        self, mock_extract, mock_index_fn, db_session, test_user
    ):
        """DOCPROC-INT-004: Failed processing sets status to FAILED with error message."""
        mock_extract.side_effect = RuntimeError("Docling extraction failed after 3 attempts.")
        mock_index_fn.return_value = MagicMock()

        file_record = _create_pending_file(db_session, test_user)
        process_and_embed_document(db=db_session, file_id=file_record.id)

        db_session.refresh(file_record)
        assert str(file_record.status) == ProcessingStatus.FAILED.value
        assert file_record.error_message is not None
        assert "failed" in file_record.error_message.lower()

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_skips_already_successful_file(
        self, mock_extract, mock_index_fn, db_session, test_user
    ):
        """DOCPROC-INT-005: Reprocessing a SUCCESS file is skipped."""
        file_record = _create_pending_file(db_session, test_user)
        # Manually set to SUCCESS
        file_record.status = ProcessingStatus.SUCCESS.value
        db_session.commit()

        process_and_embed_document(db=db_session, file_id=file_record.id)

        # Should not have called extraction
        mock_extract.assert_not_called()

    @patch("app.services.document_processor.get_pinecone_index")
    @patch("app.services.document_processor._extract_markdown_with_retry")
    def test_error_message_truncated_to_500(
        self, mock_extract, mock_index_fn, db_session, test_user
    ):
        """DOCPROC-INT-006: Error message is truncated to 500 characters."""
        long_error = "X" * 1000
        mock_extract.side_effect = RuntimeError(long_error)
        mock_index_fn.return_value = MagicMock()

        file_record = _create_pending_file(db_session, test_user)
        process_and_embed_document(db=db_session, file_id=file_record.id)

        db_session.refresh(file_record)
        assert len(file_record.error_message) <= 500
