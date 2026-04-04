import os
from uuid import uuid4
from typing import Optional
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from pydantic import AnyUrl, ValidationError, BaseModel
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.material import UploadedFile, FileType, ProcessingStatus
from app.schemas.material import UploadedFileResponse, FileType
from app.models.user import User
from app.api.deps import get_current_active_user
from app.core.config import settings
from app.tasks.material_tasks import process_document_task
from app.models.chat import ChatSession

from app.services.document_processor import embeddings
from app.services.chat_history import PostgresChatMessageHistory
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

router = APIRouter()
UPLOAD_DIR = "storage/uploads"


@router.post("/file", response_model=UploadedFileResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file_type: FileType = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # This endpoint now handles validation correctly.
    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL.")

    # This block ensures the URL is valid *before* we try to save it.
    validated_url_str: Optional[str] = None
    if url:
        try:
            validated_url = AnyUrl(url)
            validated_url_str = str(validated_url)
        except ValidationError:
            # If validation fails, immediately raise a 422 error with a clear message.
            raise HTTPException(
                status_code=422,
                detail=[
                    {
                        "loc": ["body", "url"],
                        "msg": "Invalid URL format provided.",
                        "type": "value_error.url.parsing",
                    }
                ],
            )

    stored_path = None
    original_name = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "default.bin")[1]
        unique_name = f"{uuid4()}{ext}"
        stored_path = os.path.join(UPLOAD_DIR, unique_name)

        original_name = file.filename
        with open(stored_path, "wb") as f:
            f.write(await file.read())

    # Create the DB record using the pre-validated URL string.
    new_file = UploadedFile(
        stored_path=stored_path,
        url=validated_url_str,
        file_type=file_type,
        name=original_name,
        user_id=current_user.id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # *** TRIGGER THE BACKGROUND TASK ***
    # Instead of processing here, we call the Celery task.
    process_document_task.delay(new_file.id)

    return new_file


# NEW: Endpoint to check the processing status of a file
class StatusResponse(BaseModel):
    id: int
    name: str
    status: ProcessingStatus
    error_message: Optional[str] = None


@router.get("/{file_id}/status", response_model=StatusResponse)
def get_file_status(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return file_record


# --- New Chat Session Management ---
class ChatMessageResponse(BaseModel):
    role: str
    content: str

    class Config:
        orm_mode = True


class ChatSessionResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True


@router.post("/chat/sessions", response_model=ChatSessionResponse, status_code=201)
def create_chat_session(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Creates a new chat session for the current user."""
    new_session = ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
def get_user_chat_sessions(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Lists all chat sessions for the current user."""
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()


# NEW: Endpoint to get messages for a specific chat session
@router.get(
    "/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse]
)
def get_chat_session_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves all messages for a specific chat session."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session.messages


# --- Conversational Chat Endpoint ---
class ConversationalChatRequest(BaseModel):
    query: str
    session_id: UUID
    file_ids: List[int]


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def conversational_chat(
    request: ConversationalChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # 1. Initialize the LLM (Gemini)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY
    )

    # 2. Initialize the Retriever (Pinecone)
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME, embedding=embeddings
    )
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "filter": {
                "user_id": current_user.id,
                "source_file_id": {"$in": request.file_ids},
            }
        }
    )

    # 3. Get Chat History from our Postgres DB
    chat_history = PostgresChatMessageHistory(
        session_id=str(request.session_id), db_session=db
    )

    # 4. Create the History-Aware Retriever Chain (to reformulate the question)
    contextualize_q_system_prompt = """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 5. Create the Document Answering Chain
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

    # 6. Combine them into the final RAG chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # 7. Invoke the chain and save the history
    response = rag_chain.invoke(
        {"input": request.query, "chat_history": chat_history.messages}
    )

    chat_history.add_user_message(request.query)
    chat_history.add_ai_message(response["answer"])

    return {"answer": response["answer"]}
