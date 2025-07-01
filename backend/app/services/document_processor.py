import logging
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.config import settings
from app.models.material import UploadedFile, DocumentChunk, ProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialize Global Services (done once on startup) ---
logger.info("Initializing embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},  # Use 'cuda' if GPU is available
)
logger.info("Embedding model initialized.")

logger.info("Initializing Pinecone client...")
pinecone = PineconeClient(api_key=settings.PINECONE_API_KEY)
# --- End Initialization ---


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

        # 1. Load and Chunk
        logger.info(f"Loading file: {file_record.stored_path}")
        loader = UnstructuredFileLoader(str(file_record.stored_path))
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=150
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} text chunks.")

        if not chunks:
            raise ValueError("No text could be extracted from the document.")

        # 2. Prepare data for Pinecone
        # We need unique IDs for each vector and metadata
        texts_to_embed = [chunk.page_content for chunk in chunks]
        vector_ids = [str(uuid4()) for _ in texts_to_embed]

        # Add our relational DB IDs to the metadata for later use
        metadata_list = [
            {
                "text": chunk.page_content,
                "source_file_id": file_id,
                "user_id": file_record.user_id,
                **(chunk.metadata or {}),
            }
            for chunk in chunks
        ]

        # 3. Add to Pinecone
        # Ensure the index exists. Using serverless for simplicity.
        # The dimension must match your embedding model (384 for all-MiniLM-L6-v2)
        if settings.PINECONE_INDEX_NAME not in pinecone.list_indexes().names():
            pinecone.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")

        logger.info("Upserting vectors to Pinecone...")
        # Use the LangChain vector store to handle embedding and upserting
        PineconeVectorStore.from_texts(
            texts=texts_to_embed,
            embedding=embeddings,
            metadatas=metadata_list,
            ids=vector_ids,
            index_name=settings.PINECONE_INDEX_NAME,
        )

        # 4. Store chunk metadata in PostgreSQL
        # Delete old chunks first to ensure idempotency
        db.query(DocumentChunk).filter(DocumentChunk.source_file_id == file_id).delete()
        db.commit()

        for i, chunk_text in enumerate(texts_to_embed):
            new_chunk = DocumentChunk(
                content=chunk_text,
                vector_id=vector_ids[i],  # Store the Pinecone vector ID
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
