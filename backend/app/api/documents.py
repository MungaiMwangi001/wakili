"""
app/api/documents.py - upload, list, get, delete.
"""
import os
import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse as DocumentOut
from app.utils.auth_deps import get_current_user
from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import index_document, delete_document_collection
from app.services.groq_service import get_groq_service
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])
log = structlog.get_logger()


def _delete_file_from_disk(filepath: str) -> None:
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        log.warning("Could not delete file", path=filepath, error=str(e))


def _process_document(doc_id: int, filepath: str, file_ext: str):
    """
    Background task: extract -> chunk -> embed -> analyse -> mark ready.
    Creates its own DB session — the request-scoped session is already
    closed by the time this background task runs.
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            log.warning("Document not found in background task", doc_id=doc_id)
            return

        # Extract text from file
        text = extract_text(filepath, file_ext)
        if not text.strip():
            log.warning("No text extracted from document", doc_id=doc_id)
            doc.status = "failed"
            db.commit()
            return

        # STORE THE EXTRACTED CONTENT (this is critical)
        doc.content = text
        log.info(f"Extracted {len(text)} characters from document", doc_id=doc_id)

        # GENERATE EMBEDDING FOR PGVECTOR SEARCH (this is what was missing!)
        from app.services.embedding_service import EmbeddingService
        embedder = EmbeddingService.get_instance()
        
        # Use first 2000 chars for embedding (good balance of context vs performance)
        content_for_embedding = text[:2000] if len(text) > 2000 else text
        doc.embedding = embedder.embed_single(content_for_embedding)
        log.info(f"Generated embedding for document", doc_id=doc_id)

        # Chunk the text for detailed search
        chunks = chunk_text(text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
        texts = [c["text"] for c in chunks]
        
        # Generate embeddings for chunks (optional, for more granular search)
        chunk_embeddings = embedder.embed(texts)
        
        # Store chunks in a separate table or JSON field (optional)
        # For now, we'll just store the count
        doc.chunk_count = len(chunks)
        
        # Analyse with Groq
        groq = get_groq_service()
        context = "\n\n".join(c["text"] for c in chunks[:8])
        analysis = groq.analyse(context, language=doc.detected_language or "en")

        doc.clause_summaries = analysis.get("clause_summaries", [])
        doc.risk_flags = analysis.get("risk_flags", [])
        doc.obligations = analysis.get("obligations", [])
        doc.status = "ready"
        db.commit()
        
        log.info("Document processed successfully with pgvector embedding", 
                 doc_id=doc_id, 
                 chunks=len(chunks),
                 has_embedding=doc.embedding is not None)

    except Exception as e:
        log.error("Document processing failed", doc_id=doc_id, error=str(e))
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{current_user.id}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(content)

    doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        title=(file.filename or "").rsplit(".", 1)[0].replace("_", " ").replace("-", " "),
        file_type=ext,
        file_path=filepath,
        file_size_bytes=len(content),
        status="processing",
        detected_language=None,
        clause_summaries=[],
        risk_flags=[],
        obligations=[],
        chunk_count=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Pass only serializable args — no db session
    background_tasks.add_task(_process_document, doc.id, filepath, ext)
    log.info("Document uploaded", doc_id=doc.id, filename=file.filename)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    delete_document_collection(doc_id)
    _delete_file_from_disk(doc.file_path)
    db.delete(doc)
    db.commit()
    log.info("Document deleted", doc_id=doc_id)