"""Chat handler grounded in database chunk retrieval."""

from __future__ import annotations

import json
import logging
import re
from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.service import ai_service
from app.ai.rag import retrieve_relevant_chunks
from app.db.models import get_db, Analysis, Chunk, ChatMessage as DBChatMessage
from app.models.schemas import ChatMessage, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are ASAC (AI Solution Architect Copilot), a strictly guarded technical copilot specialized ONLY in the active solution architecture project.

STRICT DOMAIN GUARDRAILS & TOPIC SCOPE:
1. MANDATORY REFUSAL FOR OFF-TOPIC QUERIES:
    - Refuse only questions that are clearly unrelated to the active project, its requirements, architecture design, security review, technology choices, compliance, or uploaded reference documents.
    - Questions about schedule, ownership, responsibilities, implementation technologies, frontend/backend, compute, vendors, or project capabilities are project-related even when they are short, informal, use synonyms, or are not answered explicitly in the generated outputs.
    - If a project-related answer is not present in the provided context, say that it is not specified and identify the relevant missing decision. Do NOT refuse merely because the question is ambiguous, broad, or has no exact keyword match.
    - For clearly off-topic or generic queries (such as math calculations like '2+2', unrelated programming help, jokes, recipes, or general world knowledge), YOU MUST REFUSE IMMEDIATELY.
   - Exact refusal format to use:
     "I am specialized strictly as your Solution Architect Copilot for project '{project_name}'. I can only answer questions related to your project requirements, system architecture, security review, and technical documentation."

2. GROUNDING & CONTEXT ADHERENCE:
   - Base your answers strictly on the generated project outputs (Requirements, Architecture, Security, Documentation) and retrieved RAG context snippets provided in the prompt.
   - Do NOT invent unstated business goals or facts beyond the scope of this project.
    - Treat the full Analysis Outputs as authoritative background context, even when no specific RAG snippet is retrieved.
    - Interpret natural-language equivalents: "full project" may refer to delivery timeline, "frontend tech" to UI/client technologies, and "compute resources" to application runtime/hosting components.

3. CONCISE & PROFESSIONAL:
   - Keep answers clear, technical, concise, and structured."""


def _is_off_topic_query(msg: str) -> bool:
    """Pre-check for obvious off-topic queries like math or general trivia."""
    text = msg.strip().lower()
    # Simple arithmetic / math patterns e.g. "2+2", "what is 5 * 10", "calculate 100/4"
    if re.match(r"^(\d+\s*[\+\-\*/\^]\s*\d+|\bwhat\s+is\s+\d+\s*[\+\-\*/\^]\s*\d+|\bmath\b|\btell\s+me\s+a\s+joke\b)", text):
        return True
    return False


async def handle_chat(request: ChatRequest, db: Session) -> ChatResponse:
    logger.info("Chat request received: session_id=%s message_length=%d", request.session_id, len(request.message))
    analysis = db.query(Analysis).filter(Analysis.id == request.session_id).first()
    if not analysis:
        logger.warning("Chat session not found: session_id=%s", request.session_id)
        return ChatResponse(
            session_id=request.session_id,
            reply="No analysis session found in database. Please run an analysis first.",
            messages=[],
            ai_provider_used="template",
        )

    project_name = analysis.project_name
    refusal_msg = (
        f"I am specialized strictly as your Solution Architect Copilot for project '{project_name}'. "
        "I can only answer questions related to your project requirements, system architecture, "
        "security review, and technical documentation."
    )

    # 0. Immediate pre-guardrail check for obvious off-topic queries
    if _is_off_topic_query(request.message):
        logger.info("Chat request rejected by pre-guardrail: session_id=%s", request.session_id)
        user_msg = DBChatMessage(analysis_id=request.session_id, role="user", content=request.message)
        bot_msg = DBChatMessage(analysis_id=request.session_id, role="assistant", content=refusal_msg, rag_sources_json="[]")
        db.add(user_msg)
        db.add(bot_msg)
        db.commit()

        past_messages = db.query(DBChatMessage).filter(DBChatMessage.analysis_id == request.session_id).order_by(DBChatMessage.created_at.asc()).all()
        chat_msgs = [ChatMessage(role=m.role, content=m.content, timestamp=m.created_at) for m in past_messages]
        return ChatResponse(
            session_id=request.session_id,
            reply=refusal_msg,
            messages=chat_msgs,
            ai_provider_used="guardrail",
        )

    # 1. Retrieve RAG chunks from database matching user query
    db_chunks = db.query(Chunk).filter(Chunk.analysis_id == request.session_id).all()
    retrieved = await retrieve_relevant_chunks(request.message, db_chunks, top_k=4)

    context_snippets = []
    rag_sources = []
    for chunk, score in retrieved:
        context_snippets.append(f"[{chunk.source} (Similarity: {score:.2f})]: {chunk.text}")
        rag_sources.append({
            "title": chunk.source,
            "excerpt": chunk.text[:150] + "...",
            "score": score
        })

    # Include full generated analysis output as primary background context
    output = analysis.outputs
    analysis_summary = ""
    if output:
        analysis_summary = f"""Analysis Outputs:
Requirements Context: {output.requirements_json}
Architecture Overview: {output.architecture_json}
Security Review: {output.security_json}
Documentation Summary: {output.documentation_json}"""

    # Fetch recent conversation history
    past_messages = db.query(DBChatMessage).filter(DBChatMessage.analysis_id == request.session_id).order_by(DBChatMessage.created_at.asc()).all()
    history_str = "\n".join([f"{m.role}: {m.content}" for m in past_messages[-6:]])

    user_prompt = f"""Active Session Project: {analysis.project_name}

{analysis_summary}

Grounded RAG Snippets:
{chr(10).join(context_snippets) if context_snippets else "No specific document snippet retrieved."}

Conversation History:
{history_str}

User Question:
{request.message}"""

    formatted_system_prompt = SYSTEM_PROMPT.format(project_name=project_name)

    # Query LLM
    reply, provider = await ai_service.complete_text(formatted_system_prompt, user_prompt)
    logger.info("Chat response generated: session_id=%s provider=%s rag_sources=%d", request.session_id, provider, len(rag_sources))

    # Persist chat messages to DB
    user_msg = DBChatMessage(analysis_id=request.session_id, role="user", content=request.message)
    bot_msg = DBChatMessage(
        analysis_id=request.session_id,
        role="assistant",
        content=reply,
        rag_sources_json=json.dumps(rag_sources)
    )
    db.add(user_msg)
    db.add(bot_msg)
    db.commit()

    # Load all messages for response
    updated_messages = db.query(DBChatMessage).filter(DBChatMessage.analysis_id == request.session_id).order_by(DBChatMessage.created_at.asc()).all()
    chat_msgs = [ChatMessage(role=m.role, content=m.content, timestamp=m.created_at) for m in updated_messages]

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        messages=chat_msgs,
        ai_provider_used=provider,
    )


async def get_chat_history(analysis_id: str, db: Session) -> list[ChatMessage]:
    past_messages = db.query(DBChatMessage).filter(DBChatMessage.analysis_id == analysis_id).order_by(DBChatMessage.created_at.asc()).all()
    # Return last 10 messages
    recent_messages = past_messages[-10:] if len(past_messages) > 10 else past_messages
    return [ChatMessage(role=m.role, content=m.content, timestamp=m.created_at) for m in recent_messages]


