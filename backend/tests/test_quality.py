import asyncio

import pytest
from pydantic import ValidationError

from app.ai.service import AIService
from app.api.chat import _is_off_topic_query
from app.config import settings
from app.models.schemas import AnalyzeRequest, ChatRequest


def test_request_limits_reject_oversized_input() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(session_id="session", message="x" * 4001)

    with pytest.raises(ValidationError):
        AnalyzeRequest(
            project_name="Vendor Platform",
            domain="procurement",
            business_goals="x",
            functional_requirements="x" * 20001,
        )


def test_chat_guardrail_only_rejects_obvious_off_topic_queries() -> None:
    assert _is_off_topic_query("what is 2 + 2")
    assert not _is_off_topic_query("what frontend technology is used?")
    assert not _is_off_topic_query("how long will the project take?")


def test_selected_azure_provider_does_not_call_other_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AIService()
    monkeypatch.setattr(settings, "ai_provider", "azure_openai")
    monkeypatch.setattr(settings, "template_fallback", True)
    monkeypatch.setattr(service, "_get_azure_client", lambda: None)
    monkeypatch.setattr(
        service,
        "_get_openai_client",
        lambda: (_ for _ in ()).throw(AssertionError("OpenAI fallback called")),
    )
    monkeypatch.setattr(
        service,
        "_call_ollama",
        lambda *_: (_ for _ in ()).throw(AssertionError("Ollama fallback called")),
    )

    result, provider = asyncio.run(service.complete_json("system", "user"))

    assert result == {}
    assert provider == "template"
