import json
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import settings

Base = declarative_base()

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    intake_json = Column(Text, nullable=False)  # JSON string of IntakeRequest
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    outputs = relationship("AnalysisOutput", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="analysis", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="analysis", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="analysis", cascade="all, delete-orphan")

class AnalysisOutput(Base):
    __tablename__ = "analysis_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    requirements_json = Column(Text, nullable=False)
    architecture_json = Column(Text, nullable=False)
    security_json = Column(Text, nullable=False)
    documentation_json = Column(Text, nullable=False)
    provider = Column(String, default="azure_openai")
    elapsed_seconds = Column(String, default="0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    analysis = relationship("Analysis", back_populates="outputs")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    content_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    analysis = relationship("Analysis", back_populates="documents")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    source = Column(String, nullable=False)  # e.g., 'upload:filename.pdf', 'knowledge:kb.md', 'analysis:architecture'
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    vector_json = Column(Text, nullable=False)  # JSON serialized list of floats (embedding or tfidf)

    analysis = relationship("Analysis", back_populates="chunks")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    rag_sources_json = Column(Text, nullable=True)  # JSON array of retrieved sources
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    analysis = relationship("Analysis", back_populates="chat_messages")

# Database connection setup. The typed settings object is the single source of truth.
database_url = settings.database_url

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # Ensure directory exists for sqlite file
    import os
    db_path = database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
