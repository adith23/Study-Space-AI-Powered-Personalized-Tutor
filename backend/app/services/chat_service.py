from fastapi import HTTPException
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from pinecone import Pinecone as PineconeClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user_model import User
from app.schemas.chat_schema import ConversationalChatRequest
from app.services.chat_history import PostgresChatMessageHistory
from app.services.chat_session_service import get_chat_session

pinecone = PineconeClient(api_key=settings.PINECONE_API_KEY)


# Get the Pinecone index
def _get_pinecone_index():
    if settings.PINECONE_INDEX_HOST:
        return pinecone.Index(host=settings.PINECONE_INDEX_HOST)
    if settings.PINECONE_INDEX_NAME:
        return pinecone.Index(settings.PINECONE_INDEX_NAME)
    raise ValueError("PINECONE_INDEX_HOST or PINECONE_INDEX_NAME must be configured.")


# Extract the hits from the response
def _extract_hits(response: object) -> list:
    if isinstance(response, dict):
        return response.get("result", {}).get("hits", []) or []

    result = getattr(response, "result", None)
    if result is None:
        return []
    hits = getattr(result, "hits", None)
    return hits or []


# Retrieve the documents from the Pinecone index
def _retrieve_documents(
    *, query_text: str, current_user: User, file_ids: list[int], top_k: int = 8
) -> list[Document]:
    index = _get_pinecone_index()
    text_field = settings.PINECONE_INTEGRATED_TEXT_FIELD
    response = index.search_records(
        namespace=settings.PINECONE_NAMESPACE,
        query={
            "inputs": {"text": query_text},
            "top_k": top_k,
            "filter": {
                "user_id": str(current_user.id),
                "source_file_id": {"$in": file_ids},
            },
        },
        fields=[text_field, "section_title", "heading_path", "source", "chunk_index"],
    )

    documents: list[Document] = []
    for hit in _extract_hits(response):
        if isinstance(hit, dict):
            hit_id = hit.get("_id") or hit.get("id")
            hit_score = hit.get("_score") or hit.get("score")
            fields = hit.get("fields", {}) or {}
        else:
            hit_id = getattr(hit, "_id", None) or getattr(hit, "id", None)
            hit_score = getattr(hit, "_score", None) or getattr(hit, "score", None)
            fields = getattr(hit, "fields", {}) or {}

        chunk_text = fields.get(text_field)
        if not chunk_text:
            continue

        documents.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "id": hit_id,
                    "score": hit_score,
                    "section_title": fields.get("section_title"),
                    "heading_path": fields.get("heading_path"),
                    "source": fields.get("source"),
                    "chunk_index": fields.get("chunk_index"),
                },
            )
        )

    return documents


# Run a conversational chat
async def run_conversational_chat(
    *, request: ConversationalChatRequest, db: Session, current_user: User
) -> dict:
    get_chat_session(
        session_id=request.session_id,
        db=db,
        current_user=current_user,
    )

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )

    chat_history = PostgresChatMessageHistory(
        session_id=str(request.session_id), db_session=db
    )

    contextualize_q_system_prompt = """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    qa_system_prompt = """You are an expert study assistant. Use the following pieces of retrieved context to answer the user's question. If you don't know the answer, just say that you don't know. Be concise and helpful.

    Context:
    {context}"""
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    try:
        standalone_question = llm.invoke(
            contextualize_q_prompt.format_messages(
                chat_history=chat_history.messages,
                input=request.query,
            )
        )
        standalone_question_text = (
            standalone_question.content
            if hasattr(standalone_question, "content")
            else str(standalone_question)
        ).strip() or request.query

        retrieved_docs = _retrieve_documents(
            query_text=standalone_question_text,
            current_user=current_user,
            file_ids=request.file_ids,
        )

        response = question_answer_chain.invoke(
            {
                "input": request.query,
                "chat_history": chat_history.messages,
                "context": retrieved_docs,
            }
        )
    except ChatGoogleGenerativeAIError as e:
        err = str(e).lower()
        if "resource_exhausted" in err or "429" in str(e) or "quota" in err:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota or rate limit exceeded for this project/key. "
                    "Check billing and limits at https://ai.google.dev/gemini-api/docs/rate-limits "
                    "or set GEMINI_CHAT_MODEL in .env to another model your tier supports."
                ),
            ) from e
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an error. Try again later.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail="The retrieval service returned an error. Try again later.",
        ) from e

    if isinstance(response, str):
        answer = response
    elif isinstance(response, dict):
        answer = response.get("answer") or response.get("output_text") or str(response)
    else:
        answer = str(response)

    chat_history.add_user_message(request.query)
    chat_history.add_ai_message(answer)
    return {"answer": answer}
