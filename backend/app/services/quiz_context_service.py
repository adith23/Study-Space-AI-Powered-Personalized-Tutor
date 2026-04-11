from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document
from pinecone import Pinecone as PineconeClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material_model import DocumentChunk, ProcessingStatus, UploadedFile
from app.models.quiz_model import QuizGenerationMode
from app.models.user_model import User

pinecone = PineconeClient(api_key=settings.PINECONE_API_KEY)


@dataclass
class QuizGenerationContext:
    mode: QuizGenerationMode
    context_text: str


def _get_pinecone_index():
    if settings.PINECONE_INDEX_HOST:
        return pinecone.Index(host=settings.PINECONE_INDEX_HOST)
    if settings.PINECONE_INDEX_NAME:
        return pinecone.Index(settings.PINECONE_INDEX_NAME)
    raise ValueError("PINECONE_INDEX_HOST or PINECONE_INDEX_NAME must be configured.")


def _extract_hits(response: object) -> list:
    if isinstance(response, dict):
        return response.get("result", {}).get("hits", []) or []

    result = getattr(response, "result", None)
    if result is None:
        return []
    return getattr(result, "hits", None) or []


def get_valid_selected_files(
    *, db: Session, current_user: User, file_ids: List[int]
) -> List[UploadedFile]:
    files = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id.in_(file_ids),
            UploadedFile.user_id == current_user.id,
        )
        .all()
    )
    if len(files) != len(set(file_ids)):
        raise ValueError("One or more selected sources were not found.")

    invalid_files = [
        file.name or f"File {file.id}"
        for file in files
        if file.status != ProcessingStatus.SUCCESS
    ]
    if invalid_files:
        raise ValueError(
            "All selected sources must be processed successfully before quiz generation."
        )

    file_map = {file.id: file for file in files}
    return [file_map[file_id] for file_id in file_ids]


def _build_broad_context(*, db: Session, files: List[UploadedFile]) -> QuizGenerationContext:
    file_ids = [file.id for file in files]
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.source_file_id.in_(file_ids))
        .all()
    )
    if not chunks:
        raise ValueError("No processed content is available for the selected sources.")

    file_name_map = {file.id: file.name or f"Source {file.id}" for file in files}
    ordered_chunks = sorted(
        chunks,
        key=lambda chunk: (
            file_ids.index(chunk.source_file_id),
            (chunk.metadata_ or {}).get("chunk_index", 0),
            chunk.id,
        ),
    )

    parts: List[str] = []
    for chunk in ordered_chunks:
        metadata = chunk.metadata_ or {}
        section_title = metadata.get("section_title") or "Untitled"
        heading_path = metadata.get("heading_path") or ""
        source_name = file_name_map.get(chunk.source_file_id, f"Source {chunk.source_file_id}")
        header = f"[Source: {source_name}] [Section: {section_title}]"
        if heading_path:
            header = f"{header} [Path: {heading_path}]"
        parts.append(f"{header}\n{chunk.content}")

    return QuizGenerationContext(
        mode=QuizGenerationMode.BROAD_FULL_SOURCE,
        context_text="\n\n".join(parts),
    )


def _retrieve_focused_documents(
    *, current_user: User, file_ids: List[int], focus_prompt: str, top_k: int
) -> List[Document]:
    index = _get_pinecone_index()
    text_field = settings.PINECONE_INTEGRATED_TEXT_FIELD
    response = index.search_records(
        namespace=settings.PINECONE_NAMESPACE,
        query={
            "inputs": {"text": focus_prompt},
            "top_k": top_k,
            "filter": {
                "user_id": str(current_user.id),
                "source_file_id": {"$in": file_ids},
            },
        },
        fields=[text_field, "section_title", "heading_path", "source", "chunk_index"],
    )

    documents: List[Document] = []
    for hit in _extract_hits(response):
        if isinstance(hit, dict):
            fields = hit.get("fields", {}) or {}
        else:
            fields = getattr(hit, "fields", {}) or {}
        chunk_text = fields.get(text_field)
        if not chunk_text:
            continue
        documents.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "section_title": fields.get("section_title"),
                    "heading_path": fields.get("heading_path"),
                    "source": fields.get("source"),
                    "chunk_index": fields.get("chunk_index"),
                },
            )
        )
    return documents


def _build_focused_context(
    *, current_user: User, files: List[UploadedFile], focus_prompt: str, top_k: int
) -> QuizGenerationContext:
    file_ids = [file.id for file in files]
    documents = _retrieve_focused_documents(
        current_user=current_user,
        file_ids=file_ids,
        focus_prompt=focus_prompt,
        top_k=top_k,
    )
    if not documents:
        raise ValueError("No focused context could be retrieved for the selected sources.")

    parts: List[str] = []
    for document in documents:
        metadata = document.metadata or {}
        section_title = metadata.get("section_title") or "Untitled"
        heading_path = metadata.get("heading_path") or ""
        source = metadata.get("source") or "Selected source"
        header = f"[Source: {source}] [Section: {section_title}]"
        if heading_path:
            header = f"{header} [Path: {heading_path}]"
        parts.append(f"{header}\n{document.page_content}")

    return QuizGenerationContext(
        mode=QuizGenerationMode.FOCUSED_RAG,
        context_text="\n\n".join(parts),
    )


def build_quiz_generation_context(
    *,
    db: Session,
    current_user: User,
    files: List[UploadedFile],
    focus_prompt: str | None,
    number_of_questions: int,
) -> QuizGenerationContext:
    if focus_prompt:
        return _build_focused_context(
            current_user=current_user,
            files=files,
            focus_prompt=focus_prompt,
            top_k=max(8, min(24, number_of_questions * 4)),
        )
    return _build_broad_context(db=db, files=files)
