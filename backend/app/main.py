"""ASAC Backend - AI Solution Architect Copilot."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.health import router as health_router
from app.api.routes import router as chat_router
from app.config import settings
from app.rag.retriever import rag_retriever


from app.db.models import init_db
from app.api.history import router as history_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag_retriever.initialize()
    yield


app = FastAPI(
    title="ASAC - AI Solution Architect Copilot",
    description="Enterprise Agentic AI MVP for Solution Architects",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1", tags=["analyze"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(history_router, prefix="/api/v1", tags=["history"])

