"""Analyze endpoint with multipart upload support, RAG vector indexing, and database persistence."""

import json
import logging
from pathlib import PurePath
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.models.schemas import AnalysisResponse, AnalyzeRequest
from app.orchestration.pipeline import run_pipeline
from app.session.store import session_store
from app.db.models import get_db, Analysis, AnalysisOutput, Document, Chunk
from app.ai.rag import parse_document_file, create_chunks, process_and_vectorize_chunks

router = APIRouter()
logger = logging.getLogger(__name__)

from app.models.schemas import AnalysisResponse, AnalyzeRequest, DiscoveredRequirements, ConfirmRequirementsRequest
from app.orchestration.pipeline import run_pipeline, run_downstream_pipeline, resume_pipeline
from app.agents.requirement_agent import run_requirements_discovery_agent

@router.post("/analyze/requirements-discovery", response_model=DiscoveredRequirements)
async def discover_requirements(
    request: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
) -> DiscoveredRequirements:
    try:
        req_data = json.loads(request)
        analyze_req = AnalyzeRequest(**req_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {e}")

    session = session_store.create()
    session.intake = req_data
    session_docs: list[tuple[str, bytes]] = []

    # Keep uploads in the session until confirmation; only validated files enter persistence.
    if files:
        if len(files) > 2:
            raise HTTPException(status_code=400, detail="Maximum 2 reference documents allowed.")
        for f in files:
            safe_filename = PurePath(f.filename or "upload").name
            extension = PurePath(safe_filename).suffix.lower()
            if extension not in {".pdf", ".docx", ".doc", ".txt", ".md"}:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {extension or 'unknown'}")
            content = await f.read()
            if len(content) > 2 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File {safe_filename} exceeds 2MB limit.")
            session_docs.append((safe_filename, content))
    session.uploaded_docs = session_docs

    discovered, _ = await run_requirements_discovery_agent(session.session_id, analyze_req)
    logger.info("Requirements discovered: session_id=%s files=%d", session.session_id, len(session_docs))
    return discovered


@router.post("/analyze/confirm", response_model=AnalysisResponse)
async def confirm_requirements(
    payload: ConfirmRequirementsRequest,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    session = session_store.get(payload.session_id)
    if not session:
        session = session_store.create()
        session.session_id = payload.session_id

    analyze_req = payload.intake
    session.intake = analyze_req.model_dump()

    # Convert validated uploads to durable records and searchable chunks.
    uploaded_docs = getattr(session, "uploaded_docs", [])
    all_chunks_to_vectorize = []
    doc_records = []

    for filename, content_bytes in uploaded_docs:
        text = parse_document_file(filename, content_bytes)
        doc_records.append(
            Document(
                analysis_id=session.session_id,
                file_name=filename,
                file_size=len(content_bytes),
                file_type=filename.split(".")[-1] if "." in filename else "txt",
                content_text=text,
            )
        )
        file_chunks = create_chunks(text, source_name=f"upload:{filename}")
        all_chunks_to_vectorize.extend(file_chunks)

    # Execute downstream agents with user-validated requirements context
    response = await run_downstream_pipeline(analyze_req, session, payload.validated_context)

    # Convert pipeline outputs to RAG chunks
    if response.requirements:
        all_chunks_to_vectorize.extend(create_chunks(response.requirements.model_dump_json(), source_name="analysis:requirements"))
    if response.architecture:
        all_chunks_to_vectorize.extend(create_chunks(response.architecture.pattern_rationale, source_name="analysis:architecture"))
    if response.security:
        all_chunks_to_vectorize.extend(create_chunks(json.dumps(response.security.recommendations), source_name="analysis:security"))

    vectorized_chunks = await process_and_vectorize_chunks(all_chunks_to_vectorize)

    # Database persistence
    analysis_record = Analysis(
        id=session.session_id,
        project_name=analyze_req.project_name,
        intake_json=json.dumps(analyze_req.model_dump()),
        status=response.status,
    )
    db.add(analysis_record)

    for doc in doc_records:
        db.add(doc)

    for c in vectorized_chunks:
        db.add(
            Chunk(
                analysis_id=session.session_id,
                source=c["source"],
                text=c["text"],
                token_count=c["token_count"],
                vector_json=json.dumps(c["vector"]),
            )
        )

    output_record = AnalysisOutput(
        analysis_id=session.session_id,
        requirements_json=response.requirements.model_dump_json() if response.requirements else "",
        architecture_json=response.architecture.model_dump_json() if response.architecture else "",
        security_json=response.security.model_dump_json() if response.security else "",
        documentation_json=response.documentation.model_dump_json() if response.documentation else "",
        provider=response.ai_provider_used,
        elapsed_seconds=str(response.elapsed_seconds),
    )
    db.add(output_record)
    db.commit()

    return response


@router.post("/analyze/resume/{analysis_id}", response_model=AnalysisResponse)
async def resume_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    try:
        response = await resume_pipeline(analysis_id, db)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume analysis: {e}")


