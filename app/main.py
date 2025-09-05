import os
import io
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .ocr import extract_text_from_file
from .qa import QAPipeline
from .rag import RAGIndex, chunk_text

ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"
ENABLE_NER = os.getenv("ENABLE_NER", "false").lower() == "true"

app = FastAPI(title="Abysalto - AI Document Insight Service")

# In-memory storage. For production, replace with DB/object store.
SESSIONS = {}
# SESSIONS[session_id] = {
#   "docs": List[{"filename": str, "text": str}],
#   "rag": RAGIndex | None
# }

qa_pipeline = QAPipeline(enable_ner=ENABLE_NER)

class AskRequest(BaseModel):
    session_id: str
    question: str
    use_rag: Optional[bool] = None
    top_k: int = 5

@app.get("/")
def root():
    return {"service": app.title, "enable_rag": ENABLE_RAG, "enable_ner": ENABLE_NER}

@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
):
    sid = session_id or str(uuid.uuid4())
    if sid not in SESSIONS:
        SESSIONS[sid] = {"docs": [], "rag": None}

    texts = []
    for f in files:
        try:
            content = await f.read()
            text = extract_text_from_file(io.BytesIO(content), f.filename)
            SESSIONS[sid]["docs"].append({"filename": f.filename, "text": text})
            texts.append({"filename": f.filename, "chars": len(text)})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process {f.filename}: {e}")

    # Build/update RAG index if enabled
    if ENABLE_RAG:
        if SESSIONS[sid]["rag"] is None:
            SESSIONS[sid]["rag"] = RAGIndex()
        rag = SESSIONS[sid]["rag"]
        # Chunk all new texts and add
        for doc in SESSIONS[sid]["docs"]:
            for chunk in chunk_text(doc["text"], chunk_size=600, overlap=100):
                rag.add_text(chunk, metadata={"source": doc["filename"]})

    return JSONResponse({"session_id": sid, "uploaded": texts, "rag_ready": ENABLE_RAG})

@app.post("/ask")
def ask(payload: AskRequest):
    sid = payload.session_id
    if sid not in SESSIONS or not SESSIONS[sid]["docs"]:
        raise HTTPException(status_code=404, detail="Session not found or empty. Upload documents first.")

    use_rag = payload.use_rag if payload.use_rag is not None else ENABLE_RAG

    if use_rag and SESSIONS[sid]["rag"] is not None:
        rag: RAGIndex = SESSIONS[sid]["rag"]
        contexts = rag.search(payload.question, top_k=payload.top_k)
        context_text = "\n\n".join([c.text for c in contexts])
        sources = list({c.metadata.get("source", "unknown") for c in contexts})
    else:
        # Concatenate all docs (truncate to avoid token explosion)
        all_text = "\n\n".join([d["text"] for d in SESSIONS[sid]["docs"]])
        context_text = all_text[:20000]
        sources = list({d["filename"] for d in SESSIONS[sid]["docs"]})

    answer, spans, entities = qa_pipeline.answer(payload.question, context_text)

    return {
        "answer": answer,
        "spans": spans,
        "entities": entities if ENABLE_NER else [],
        "sources": sources,
    }
