"""Health check endpoint."""

from fastapi import APIRouter

from app.ai.service import ai_service
from app.config import settings
from app.models.schemas import HealthStatus
from app.rag.retriever import rag_retriever
from app.session.store import session_store


router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    azure_status = await ai_service.check_azure_openai()
    openai_status = await ai_service.check_openai()
    ollama_status = await ai_service.check_ollama()

    rag_available = rag_retriever.is_available
    doc_count = rag_retriever.document_count

    if azure_status == "available" or openai_status == "available" or ollama_status == "available":
        overall = "healthy"
    else:
        overall = "degraded"

    return HealthStatus(
        status=overall,
        ai_providers={
            "azure_openai": azure_status,
            "openai": openai_status,
            "ollama": ollama_status,
            "template_fallback": "enabled" if settings.template_fallback else "disabled",
        },
        rag={
            "available": rag_available,
            "document_count": doc_count,
        },
        sessions_active=session_store.count(),
    )

