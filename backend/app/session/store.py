"""In-memory session store for MVP."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.models.schemas import AnalysisResponse, ChatMessage


class Session:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.analysis: AnalysisResponse | None = None
        self.intake: dict[str, Any] = {}
        self.chat_messages: list[ChatMessage] = []


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id)
        return self._sessions[session_id]

    def count(self) -> int:
        return len(self._sessions)


session_store = SessionStore()
