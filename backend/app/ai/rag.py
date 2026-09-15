"""RAG Engine: Document extraction, sliding window chunking, dense vector/TF-IDF indexing, and cosine retrieval."""

import io
import json
import math
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from pypdf import PdfReader
from docx import Document as DocxDocument

from app.ai.service import ai_service
from app.db.models import Chunk

logger = logging.getLogger(__name__)

def parse_document_file(filename: str, content_bytes: bytes) -> str:
    """Extract raw text from uploaded PDF, DOCX, TXT, or MD files."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    text = ""
    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(content_bytes))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        elif ext in ["docx", "doc"]:
            doc = DocxDocument(io.BytesIO(content_bytes))
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
        else: # txt, md, or plaintext
            text = content_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error("Error parsing document %s: %s", filename, e)
        text = content_bytes.decode("utf-8", errors="ignore")
    return text.strip()

def create_chunks(text: str, source_name: str, chunk_size_words: int = 250, overlap_words: int = 50) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks and count tokens/words."""
    words = text.split()
    if not words:
        return []
    
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size_words]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "source": source_name,
            "text": chunk_text,
            "token_count": len(chunk_words),
        })
        i += (chunk_size_words - overlap_words)
    return chunks

async def process_and_vectorize_chunks(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Vectorize chunks using Dense Azure/OpenAI embeddings or TF-IDF fallback."""
    if not chunks:
        return []

    texts = [c["text"] for c in chunks]
    
    # Try dense embedding for first chunk to test availability
    first_vec = await ai_service.get_embedding(texts[0])
    
    if first_vec is not None:
        # Use dense embeddings
        logger.info("Vectorizing using Dense API Embeddings")
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                vec = first_vec
            else:
                vec = await ai_service.get_embedding(chunk["text"]) or [0.0] * len(first_vec)
            chunk["vector"] = vec
    else:
        # Fallback to TF-IDF vectorization
        logger.info("Vectorizing using local scikit-learn TF-IDF")
        vectorizer = TfidfVectorizer(max_features=512)
        tfidf_matrix = vectorizer.fit_transform(texts).toarray()
        for idx, chunk in enumerate(chunks):
            chunk["vector"] = tfidf_matrix[idx].tolist()

    return chunks

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    if len(a) != len(b):
        # Truncate or pad if dimensions mismatch
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

async def retrieve_relevant_chunks(
    query: str,
    db_chunks: List[Chunk],
    top_k: int = 5
) -> List[Tuple[Chunk, float]]:
    """Retrieve top K chunks matching the query string from stored database chunks."""
    if not db_chunks:
        return []

    # Get query embedding or TF-IDF
    query_vec = await ai_service.get_embedding(query)
    
    if query_vec is None:
        # Fallback to TF-IDF matching over current corpus
        corpus = [c.text for c in db_chunks] + [query]
        vectorizer = TfidfVectorizer(max_features=512)
        matrix = vectorizer.fit_transform(corpus).toarray()
        query_vec = matrix[-1].tolist()
        chunk_vecs = matrix[:-1].tolist()
    else:
        chunk_vecs = [json.loads(c.vector_json) for c in db_chunks]

    scored_chunks = []
    for chunk, vec in zip(db_chunks, chunk_vecs):
        score = cosine_similarity(query_vec, vec)
        scored_chunks.append((chunk, score))

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return scored_chunks[:top_k]
