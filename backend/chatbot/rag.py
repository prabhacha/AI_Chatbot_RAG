import json
import re
import uuid
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "rag_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = DATA_DIR / "documents.faiss"
CHUNKS_PATH = DATA_DIR / "chunks.json"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # The model downloads from Hugging Face the first time it is used.
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def extract_text(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(uploaded_file).pages)
    elif suffix in {".txt", ".md"}:
        text = uploaded_file.read().decode("utf-8", errors="replace")
    else:
        raise ValueError("Supported file types are PDF, TXT, and MD.")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError("No readable text found. Scanned PDFs need OCR before indexing.")
    return text


def split_text(text, chunk_size=1000, overlap=150):
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def read_chunks():
    if not CHUNKS_PATH.exists():
        return []
    return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))


def save_chunks(chunks):
    CHUNKS_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


def rebuild_index(chunks):
    if not chunks:
        INDEX_PATH.unlink(missing_ok=True)
        return
    model = get_embedding_model()
    vectors = model.encode([item["text"] for item in chunks], convert_to_numpy=True, normalize_embeddings=True)
    vectors = np.asarray(vectors, dtype="float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH))


def add_document(filename, text):
    chunks = read_chunks()
    document_id = uuid.uuid4().hex[:12]
    pieces = split_text(text)
    new_items = [
        {"document_id": document_id, "filename": filename, "chunk_number": i + 1, "text": piece}
        for i, piece in enumerate(pieces)
    ]
    if not new_items:
        raise ValueError("No text chunks were created.")
    updated = chunks + new_items
    # Rebuild before writing metadata so failed embeddings don't corrupt the metadata/index pair.
    rebuild_index(updated)
    save_chunks(updated)
    return {"document_id": document_id, "filename": filename, "chunks_added": len(new_items)}


def get_documents():
    docs = {}
    for item in read_chunks():
        doc_id = item["document_id"]
        if doc_id not in docs:
            docs[doc_id] = {"document_id": doc_id, "filename": item["filename"], "chunk_count": 0}
        docs[doc_id]["chunk_count"] += 1
    return list(docs.values())


def remove_document(document_id):
    old_chunks = read_chunks()
    remaining = [item for item in old_chunks if item["document_id"] != document_id]
    if len(remaining) == len(old_chunks):
        return False
    rebuild_index(remaining)
    save_chunks(remaining)
    return True


def retrieve(question, top_k=4):
    chunks = read_chunks()
    if not chunks or not INDEX_PATH.exists():
        return []
    model = get_embedding_model()
    query_vector = model.encode([question], convert_to_numpy=True, normalize_embeddings=True)
    query_vector = np.asarray(query_vector, dtype="float32")
    index = faiss.read_index(str(INDEX_PATH))
    scores, ids = index.search(query_vector, min(top_k, len(chunks)))
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx >= 0:
            item = chunks[int(idx)]
            results.append({
                "filename": item["filename"],
                "chunk_number": item["chunk_number"],
                "text": item["text"],
                "score": round(float(score), 4),
            })
    return results
