"""Simple TF-IDF based RAG retriever over markdown knowledge corpus."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.models.schemas import RagSource

logger = logging.getLogger(__name__)


@dataclass
class Document:
    title: str
    path: str
    content: str
    category: str


class RAGRetriever:
    def __init__(self) -> None:
        self.documents: list[Document] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._initialized = False

    def initialize(self) -> None:
        knowledge_path = settings.knowledge_path
        if not knowledge_path.exists():
            logger.warning("Knowledge directory not found: %s", knowledge_path)
            self._initialized = True
            return

        for md_file in sorted(knowledge_path.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = self._extract_title(content) or md_file.stem.replace("-", " ").title()
            rel_path = str(md_file.relative_to(knowledge_path))
            category = md_file.parent.name
            self.documents.append(
                Document(title=title, path=rel_path, content=content, category=category)
            )

        if self.documents:
            texts = [f"{d.title} {d.content}" for d in self.documents]
            self._vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            self._matrix = self._vectorizer.fit_transform(texts)

        self._initialized = True
        logger.info("RAG initialized with %d documents", len(self.documents))

    def _extract_title(self, content: str) -> str | None:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def retrieve(self, query: str, top_k: int | None = None) -> list[RagSource]:
        if not self._initialized:
            self.initialize()

        k = top_k or settings.rag_top_k
        if not self.documents or self._vectorizer is None or self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        top_indices = scores.argsort()[::-1][:k]

        results: list[RagSource] = []
        for idx in top_indices:
            score = float(scores[idx])
            # Enforce strict minimum relevance threshold to prevent out-of-domain sources (e.g. Loyalty on FAQ Chatbots)
            if score < 0.15:
                continue
            doc = self.documents[idx]
            excerpt = doc.content[:400].replace("\n", " ").strip()
            if len(doc.content) > 400:
                excerpt += "..."
            results.append(
                RagSource(
                    title=doc.title,
                    path=doc.path,
                    excerpt=excerpt,
                    score=round(float(scores[idx]), 4),
                )
            )
        return results

    @property
    def document_count(self) -> int:
        if not self._initialized:
            self.initialize()
        return len(self.documents)

    @property
    def is_available(self) -> bool:
        if not self._initialized:
            self.initialize()
        return len(self.documents) > 0


rag_retriever = RAGRetriever()
