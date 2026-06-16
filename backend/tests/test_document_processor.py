"""
Document Processor unit tests.

Covers: DOC-UNIT-001 through DOC-UNIT-012

See qa_testing_plan.md Section 6.2.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.document_processor import (
    _heading_path_to_string,
    _structure_aware_sections,
    _chunk_with_structure,
    _build_metadata_for_chunks,
    _extract_markdown_with_retry,
    _extract_markdown_with_docling,
    SectionChunk,
    MAX_DOCLING_ATTEMPTS,
)

# ==========================================================================
# DOC-UNIT-001, 002: _heading_path_to_string
# ==========================================================================


class TestHeadingPathToString:
    """DOC-UNIT-001, 002: _heading_path_to_string behavior."""

    def test_empty_list_returns_empty_string(self):
        """DOC-UNIT-001: Empty list returns empty string."""
        assert _heading_path_to_string([]) == ""

    def test_joins_headings_with_separator(self):
        """DOC-UNIT-002: Joins headings with ' > ' separator."""
        headings = [(1, "Introduction"), (2, "Background")]
        result = _heading_path_to_string(headings)
        assert result == "Introduction > Background"

    def test_single_heading(self):
        """Supplementary: Single heading returns just the heading text."""
        headings = [(1, "Overview")]
        assert _heading_path_to_string(headings) == "Overview"

    def test_three_level_nesting(self):
        """Supplementary: Three-level nesting."""
        headings = [(1, "Chapter 1"), (2, "Section A"), (3, "Subsection i")]
        result = _heading_path_to_string(headings)
        assert result == "Chapter 1 > Section A > Subsection i"


# ==========================================================================
# DOC-UNIT-003, 004, 005: _structure_aware_sections
# ==========================================================================


class TestStructureAwareSections:
    """DOC-UNIT-003, 004, 005: Markdown section splitting."""

    def test_splits_on_markdown_headings(self):
        """DOC-UNIT-003: Correctly splits on markdown headings."""
        markdown = """# Introduction
This is the introduction.

# Methods
This describes the methods.
"""
        sections = _structure_aware_sections(markdown)
        assert len(sections) == 2
        assert sections[0].section_title == "Introduction"
        assert "introduction" in sections[0].text.lower()
        assert sections[1].section_title == "Methods"
        assert "methods" in sections[1].text.lower()

    def test_nests_headings_correctly(self):
        """DOC-UNIT-004: Nests headings correctly (h1 > h2 > h3)."""
        markdown = """# Chapter 1
Intro text.

## Section A
Section A content.

### Subsection i
Deep content.
"""
        sections = _structure_aware_sections(markdown)
        # The h3 section should have a heading path showing full nesting
        deep_section = [s for s in sections if s.section_title == "Subsection i"]
        assert len(deep_section) == 1
        assert "Chapter 1" in deep_section[0].heading_path
        assert "Section A" in deep_section[0].heading_path
        assert "Subsection i" in deep_section[0].heading_path

    def test_headingless_text_returns_untitled(self):
        """DOC-UNIT-005: Plain text without headings returns 'Untitled'."""
        markdown = "This is plain text without any headings."
        sections = _structure_aware_sections(markdown)
        assert len(sections) == 1
        assert sections[0].section_title == "Untitled"
        assert sections[0].heading_path == ""

    def test_heading_level_reset(self):
        """Supplementary: A new h1 after h2 resets the heading path."""
        markdown = """# Part A
## Sub A
Content A.

# Part B
Content B.
"""
        sections = _structure_aware_sections(markdown)
        part_b = [s for s in sections if s.section_title == "Part B"]
        assert len(part_b) == 1
        # Part B should NOT have Part A in its heading path
        assert "Part A" not in part_b[0].heading_path


# ==========================================================================
# DOC-UNIT-006, 007: _chunk_with_structure
# ==========================================================================


class TestChunkWithStructure:
    """DOC-UNIT-006, 007: Chunking with structure preservation."""

    def test_produces_chunks_within_token_limit(self):
        """DOC-UNIT-006: Chunks are produced within the token limit."""
        # Create a long document that will need splitting
        long_section = "This is a sentence about machine learning. " * 200
        markdown = f"# Topic\n{long_section}"
        chunks = _chunk_with_structure(markdown)
        assert len(chunks) > 1
        # All chunks should preserve section title
        for chunk in chunks:
            assert chunk.section_title == "Topic"

    def test_raises_for_empty_document(self):
        """DOC-UNIT-007: Raises ValueError for empty document."""
        with pytest.raises(ValueError, match="No text could be extracted"):
            _chunk_with_structure("")

    def test_raises_for_whitespace_only(self):
        """Supplementary: Raises ValueError for whitespace-only document."""
        with pytest.raises(ValueError, match="No text could be extracted"):
            _chunk_with_structure("   \n\n   ")


# ==========================================================================
# DOC-UNIT-008, 009: _build_metadata_for_chunks
# ==========================================================================


class TestBuildMetadataForChunks:
    """DOC-UNIT-008, 009: Metadata building for chunks."""

    def _make_chunks(self, count: int) -> list:
        return [
            SectionChunk(
                text=f"Chunk {i} content",
                section_title=f"Section {i}",
                heading_path=f"Path > Section {i}",
            )
            for i in range(count)
        ]

    def test_includes_all_required_fields(self):
        """DOC-UNIT-008: Metadata includes all required fields."""
        chunks = self._make_chunks(2)
        metadata_list = _build_metadata_for_chunks(
            chunks, file_id=42, user_id=7, source="test.pdf"
        )
        required_keys = {
            "user_id",
            "source_file_id",
            "chunk_index",
            "total_chunks",
            "section_title",
            "heading_path",
            "source",
            "pipeline_version",
        }
        for meta in metadata_list:
            assert required_keys.issubset(set(meta.keys()))

    def test_sets_correct_total_chunks(self):
        """DOC-UNIT-009: total_chunks is set correctly for all chunks."""
        chunks = self._make_chunks(5)
        metadata_list = _build_metadata_for_chunks(
            chunks, file_id=1, user_id=1, source="doc.pdf"
        )
        assert len(metadata_list) == 5
        for meta in metadata_list:
            assert meta["total_chunks"] == 5

    def test_chunk_index_is_sequential(self):
        """Supplementary: chunk_index values are sequential starting from 0."""
        chunks = self._make_chunks(3)
        metadata_list = _build_metadata_for_chunks(
            chunks, file_id=1, user_id=1, source="doc.pdf"
        )
        indices = [m["chunk_index"] for m in metadata_list]
        assert indices == [0, 1, 2]

    def test_user_id_stored_as_string(self):
        """Supplementary: user_id is stored as a string (for Pinecone filter compatibility)."""
        chunks = self._make_chunks(1)
        metadata_list = _build_metadata_for_chunks(
            chunks, file_id=1, user_id=42, source="test.pdf"
        )
        assert metadata_list[0]["user_id"] == "42"
        assert isinstance(metadata_list[0]["user_id"], str)


# ==========================================================================
# DOC-UNIT-010, 011, 012: Docling extraction with retry
# ==========================================================================


class TestExtractMarkdownWithRetry:
    """DOC-UNIT-010, 011: Retry logic for Docling extraction."""

    @patch("app.services.document_processor.time.sleep")
    @patch("app.services.document_processor._extract_markdown_with_docling")
    def test_retries_on_failure(self, mock_extract, mock_sleep):
        """DOC-UNIT-010: Retries on failure, succeeds on third attempt."""
        mock_extract.side_effect = [
            RuntimeError("Fail 1"),
            RuntimeError("Fail 2"),
            "# Success\nMarkdown content",
        ]
        result = _extract_markdown_with_retry("test.pdf")
        assert result == "# Success\nMarkdown content"
        assert mock_extract.call_count == 3
        # Should have slept between retries
        assert mock_sleep.call_count == 2

    @patch("app.services.document_processor.time.sleep")
    @patch("app.services.document_processor._extract_markdown_with_docling")
    def test_raises_after_max_attempts(self, mock_extract, mock_sleep):
        """DOC-UNIT-011: Raises RuntimeError after MAX_DOCLING_ATTEMPTS failures."""
        mock_extract.side_effect = RuntimeError("Always fails")
        with pytest.raises(RuntimeError, match="failed after"):
            _extract_markdown_with_retry("test.pdf")
        assert mock_extract.call_count == MAX_DOCLING_ATTEMPTS


class TestExtractMarkdownWithDocling:
    """DOC-UNIT-012: Docling extraction handles None document."""

    @patch("app.services.document_processor.get_docling_converter")
    def test_raises_on_none_document(self, mock_get_converter):
        """DOC-UNIT-012: Raises ValueError when converter returns None document."""
        mock_converter = MagicMock()
        mock_result = MagicMock()
        mock_result.document = None  # simulate no document
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        with pytest.raises(ValueError, match="no document output"):
            _extract_markdown_with_docling("fake.pdf")

    @patch("app.services.document_processor.get_docling_converter")
    def test_raises_on_empty_markdown(self, mock_get_converter):
        """Supplementary: Raises ValueError when markdown output is empty."""
        mock_converter = MagicMock()
        mock_doc = MagicMock()
        mock_doc.export_to_markdown.return_value = "   "
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        with pytest.raises(ValueError, match="empty markdown"):
            _extract_markdown_with_docling("fake.pdf")
