import logging
import re
import time
from functools import lru_cache
from dataclasses import dataclass
from typing import List, Optional, Tuple

from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone as PineconeClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.config import settings
from app.models.material_model import UploadedFile, DocumentChunk, ProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing Pinecone client...")
pinecone = PineconeClient(api_key=settings.PINECONE_API_KEY)

MAX_DOCLING_ATTEMPTS = 3
DOCLING_RETRY_BASE_DELAY_SECONDS = 1
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 80
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
PIPELINE_VERSION = "v2"
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Section chunk data class
@dataclass
class SectionChunk:
    text: str
    section_title: str
    heading_path: str

# Get the Docling converter
@lru_cache(maxsize=1)
def get_docling_converter() -> DocumentConverter:
    logger.info("Initializing Docling converter...")
    return DocumentConverter()

# Get the Pinecone index
@lru_cache(maxsize=1)
def get_pinecone_index():
    if settings.PINECONE_INDEX_HOST:
        return pinecone.Index(host=settings.PINECONE_INDEX_HOST)
    if settings.PINECONE_INDEX_NAME:
        return pinecone.Index(settings.PINECONE_INDEX_NAME)
    raise ValueError("PINECONE_INDEX_HOST or PINECONE_INDEX_NAME must be configured.")

# Extract the markdown with Docling
def _extract_markdown_with_docling(file_path: str) -> str:
    conversion_result = get_docling_converter().convert(file_path)
    docling_document = getattr(conversion_result, "document", None)
    if docling_document is None:
        raise ValueError("Docling conversion produced no document output.")

    markdown_text = docling_document.export_to_markdown()
    if not markdown_text or not markdown_text.strip():
        raise ValueError("Docling returned empty markdown output.")

    return markdown_text

# Extract the markdown with retry
def _extract_markdown_with_retry(file_path: str) -> str:
    last_error = None
    for attempt in range(1, MAX_DOCLING_ATTEMPTS + 1):
        try:
            return _extract_markdown_with_docling(file_path)
        except Exception as exc:
            last_error = exc
            if attempt == MAX_DOCLING_ATTEMPTS:
                break
            delay_seconds = DOCLING_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Docling extraction failed for %s on attempt %d/%d. Retrying in %ss.",
                file_path,
                attempt,
                MAX_DOCLING_ATTEMPTS,
                delay_seconds,
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Docling extraction failed after {MAX_DOCLING_ATTEMPTS} attempts."
    ) from last_error

# Build the token splitter
def _build_token_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        separators=CHUNK_SEPARATORS,
    )

# Heading path to string
def _heading_path_to_string(active_headings: List[Tuple[int, str]]) -> str:
    if not active_headings:
        return ""
    return " > ".join([heading for _, heading in active_headings])

# Structure aware sections
def _structure_aware_sections(markdown_text: str) -> List[SectionChunk]:
    lines = markdown_text.splitlines()
    sections: List[SectionChunk] = []
    active_headings: List[Tuple[int, str]] = []
    current_lines: List[str] = []
    current_section_title = "Untitled"

    def flush_current() -> None:
        nonlocal current_lines, current_section_title
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                SectionChunk(
                    text=text,
                    section_title=current_section_title,
                    heading_path=_heading_path_to_string(active_headings),
                )
            )
        current_lines = []

    for line in lines:
        heading_match = HEADING_PATTERN.match(line.strip())
        if heading_match:
            flush_current()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            while active_headings and active_headings[-1][0] >= level:
                active_headings.pop()
            active_headings.append((level, title))
            current_section_title = title or "Untitled"
            current_lines = [line]
            continue
        current_lines.append(line)

    flush_current()

    if not sections:
        stripped = markdown_text.strip()
        if stripped:
            sections.append(
                SectionChunk(text=stripped, section_title="Untitled", heading_path="")
            )

    return sections

# Chunk with structure
def _chunk_with_structure(markdown_text: str) -> List[SectionChunk]:
    sections = _structure_aware_sections(markdown_text)
    splitter = _build_token_splitter()

    final_chunks: List[SectionChunk] = []
    for section in sections:
        for part in splitter.split_text(section.text):
            clean_part = part.strip()
            if clean_part:
                final_chunks.append(
                    SectionChunk(
                        text=clean_part,
                        section_title=section.section_title,
                        heading_path=section.heading_path,
                    )
                )

    if not final_chunks:
        raise ValueError("No text could be extracted from the document.")

    return final_chunks

# Build metadata for chunks
def _build_metadata_for_chunks(
    chunks: List[SectionChunk], *, file_id: int, user_id: int, source: Optional[str]
) -> List[dict]:
    total_chunks = len(chunks)
    return [
        {
            "user_id": str(user_id),
            "source_file_id": file_id,
            "chunk_index": idx,
            "total_chunks": total_chunks,
            "section_title": chunk.section_title or "Untitled",
            "heading_path": chunk.heading_path,
            "source": source or "",
            "pipeline_version": PIPELINE_VERSION,
        }
        for idx, chunk in enumerate(chunks)
    ]

# Process and embed document
def process_and_embed_document(db: Session, file_id: int):
    """
    The core function to process a single uploaded file.
    This is designed to be called from a background task.
    """
    logger.info(f"Starting processing for file_id: {file_id}")
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()

    if not file_record:
        logger.error(f"File with id {file_id} not found.")
        return

    # Prevent reprocessing
    if str(file_record.status) == ProcessingStatus.SUCCESS.value:
        logger.warning(
            f"File {file_id} has already been processed successfully. Skipping."
        )
        return

    try:
        # Update status to PROCESSING
        setattr(file_record, "status", ProcessingStatus.PROCESSING.value)
        db.commit()

        # 1. Extract markdown with Docling and build multi-stage chunks.
        logger.info("Extracting markdown with Docling from file: %s", file_record.stored_path)
        markdown_text = _extract_markdown_with_retry(str(file_record.stored_path))
        final_chunks = _chunk_with_structure(markdown_text)
        texts_to_embed = [chunk.text for chunk in final_chunks]
        logger.info("Created %d text chunks.", len(texts_to_embed))

        # 2. Prepare data for Pinecone
        vector_ids = [str(uuid4()) for _ in texts_to_embed]

        metadata_list = _build_metadata_for_chunks(
            final_chunks,
            file_id=file_id,
            user_id=file_record.user_id,
            source=file_record.stored_path,
        )

        # 3. Add records to Pinecone integrated-embedding index.
        logger.info("Upserting records to Pinecone integrated index...")
        index = get_pinecone_index()
        text_field = settings.PINECONE_INTEGRATED_TEXT_FIELD
        records = []
        for i, chunk_text in enumerate(texts_to_embed):
            record = {"_id": vector_ids[i], text_field: chunk_text, **metadata_list[i]}
            records.append(record)

        index.upsert_records(namespace=settings.PINECONE_NAMESPACE, records=records)

        # 4. Store chunk metadata in PostgreSQL
        db.query(DocumentChunk).filter(DocumentChunk.source_file_id == file_id).delete()
        db.commit()

        for i, chunk_text in enumerate(texts_to_embed):
            new_chunk = DocumentChunk(
                content=chunk_text,
                vector_id=vector_ids[i], 
                metadata_=metadata_list[i],
                source_file_id=file_id,
            )
            db.add(new_chunk)

        # 5. Update status to SUCCESS
        setattr(file_record, "status", ProcessingStatus.SUCCESS.value)
        setattr(file_record, "error_message", "")
        db.commit()
        logger.info(f"Successfully processed and embedded file_id: {file_id}")

    except Exception as e:
        logger.error(f"Error processing file {file_id}: {e}", exc_info=True)
        setattr(file_record, "status", ProcessingStatus.FAILED.value)
        setattr(file_record, "error_message", str(e)[:500])
        db.commit()
