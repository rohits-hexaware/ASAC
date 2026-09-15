"""Sequential agent orchestration pipeline."""

from __future__ import annotations

import asyncio
import logging
import time

from app.agents.architecture_agent import run_architecture_agent
from app.agents.documentation_agent import run_documentation_agent
from app.agents.requirement_agent import run_requirement_agent
from app.agents.security_agent import run_security_agent
from app.config import settings
from app.models.schemas import AgentError, AnalysisResponse, AnalyzeRequest
from app.rag.retriever import rag_retriever
from app.session.store import Session, session_store

logger = logging.getLogger(__name__)


async def _run_with_timeout(coro, timeout: int, agent_name: str):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Agent {agent_name} timed out after {timeout}s")
    except Exception as e:
        raise RuntimeError(f"Agent {agent_name} failed: {e}") from e


from app.models.schemas import AgentError, AnalysisResponse, AnalyzeRequest, StructuredRequirements, ValidatedRequirementsContext, ConfidenceLevel

async def run_downstream_pipeline(
    request: AnalyzeRequest,
    session: Session,
    validated_context: ValidatedRequirementsContext | None = None,
) -> AnalysisResponse:
    start = time.time()
    errors: list[AgentError] = []
    providers_used: set[str] = set()

    architecture = None
    security = None
    documentation = None

    rag_available = rag_retriever.is_available
    session.intake = request.model_dump()

    # Step 1: Build structured requirements from validated context if provided, else run discovery/requirements agent
    if validated_context:
        formatted_questions = []
        for q in validated_context.open_questions:
            if q in validated_context.user_clarifications and validated_context.user_clarifications[q].strip():
                formatted_questions.append(f"{q} -> [Answered]: {validated_context.user_clarifications[q].strip()}")
            else:
                formatted_questions.append(f"{q} -> [TBD / Needs Validation]")

        # Enrich requirements with LLM requirement agent while locking confirmed validated context
        enriched_reqs = None
        try:
            enriched_reqs, provider = await _run_with_timeout(
                run_requirement_agent(request, user_clarifications=validated_context.user_clarifications),
                settings.agent_timeout,
                "requirement",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.warning("Requirement agent enrichment failed during confirmation, proceeding with confirmed scope: %s", e)

        # Strictly deduplicate functional & non-functional lists
        func_list = list(dict.fromkeys(validated_context.explicit_requirements + validated_context.confirmed_derived_requirements + (enriched_reqs.functional if enriched_reqs else [])))
        
        nfr_items = enriched_reqs.non_functional if enriched_reqs else [
            f"High availability during operational business hours for {request.project_name}",
            f"Sub-second response latency (< 500ms) for core {request.domain} endpoints",
        ]
        nfr_list = list(dict.fromkeys(nfr_items))

        requirements = StructuredRequirements(
            functional=func_list,
            non_functional=nfr_list,
            constraints_summary=list(dict.fromkeys(validated_context.constraints or ["No explicit constraints"])),
            assumptions=list(dict.fromkeys(validated_context.assumptions + (enriched_reqs.assumptions if enriched_reqs else []))),
            open_questions=formatted_questions,
            confidence=ConfidenceLevel.HIGH if not any("[TBD" in q for q in formatted_questions) else ConfidenceLevel.MEDIUM,
            validated_context=validated_context,
        )
    else:
        try:
            requirements, provider = await _run_with_timeout(
                run_requirement_agent(request),
                settings.agent_timeout,
                "requirement",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.error("Requirement agent failed: %s", e)
            errors.append(AgentError(agent="requirement", error=str(e)))
            requirements = None

    # Stage 2: Architecture
    if requirements:
        try:
            architecture, provider = await _run_with_timeout(
                run_architecture_agent(request, requirements),
                settings.agent_timeout,
                "architecture",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.error("Architecture agent failed: %s", e)
            errors.append(AgentError(agent="architecture", error=str(e)))

    # Stage 3: Security
    if requirements and architecture:
        try:
            security, provider = await _run_with_timeout(
                run_security_agent(request, requirements, architecture),
                settings.agent_timeout,
                "security",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.error("Security agent failed: %s", e)
            errors.append(AgentError(agent="security", error=str(e)))

    # Stage 4: Documentation
    if requirements and architecture and security:
        try:
            documentation, provider = await _run_with_timeout(
                run_documentation_agent(request, requirements, architecture, security),
                settings.agent_timeout,
                "documentation",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.error("Documentation agent failed: %s", e)
            errors.append(AgentError(agent="documentation", error=str(e)))

    elapsed = round(time.time() - start, 2)
    ai_provider = "mixed" if len(providers_used) > 1 else (next(iter(providers_used)) if providers_used else "template")

    if documentation:
        status = "partial" if errors else "complete"
    elif requirements or architecture or security:
        status = "partial"
    else:
        status = "failed"

    response = AnalysisResponse(
        session_id=session.session_id,
        project_name=request.project_name,
        status=status,
        requirements=requirements,
        architecture=architecture,
        security=security,
        documentation=documentation,
        errors=errors,
        ai_provider_used=ai_provider,
        rag_available=rag_available,
        elapsed_seconds=elapsed,
    )

    session.analysis = response
    return response


async def run_pipeline(request: AnalyzeRequest, session: Session) -> AnalysisResponse:
    return await run_downstream_pipeline(request, session, None)


async def resume_pipeline(analysis_id: str, db: Session) -> AnalysisResponse:
    """Resumes execution of pending/failed pipeline stages for an existing analysis."""
    from app.db.models import Analysis, AnalysisOutput, Chunk
    from app.ai.rag import create_chunks, process_and_vectorize_chunks
    import json

    analysis_rec = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    output_rec = db.query(AnalysisOutput).filter(AnalysisOutput.analysis_id == analysis_id).first()

    session = session_store.get(analysis_id)

    intake_dict = None
    if analysis_rec and analysis_rec.intake_json:
        try:
            intake_dict = json.loads(analysis_rec.intake_json)
        except Exception:
            pass

    if not intake_dict and session and session.intake:
        intake_dict = session.intake

    if not intake_dict:
        raise ValueError(f"Analysis session {analysis_id} not found or intake context missing")

    request = AnalyzeRequest(**intake_dict)

    if not session:
        session = session_store.get_or_create(analysis_id)
        session.intake = intake_dict

    start = time.time()
    errors: list[AgentError] = []
    providers_used: set[str] = set()

    if output_rec and output_rec.provider:
        providers_used.add(output_rec.provider)

    requirements: StructuredRequirements | None = None
    architecture = None
    security = None
    documentation = None

    if output_rec and output_rec.requirements_json:
        try:
            requirements = StructuredRequirements.model_validate_json(output_rec.requirements_json)
        except Exception as e:
            logger.warning("Failed to deserialize saved requirements: %s", e)

    if output_rec and output_rec.architecture_json:
        try:
            architecture = ArchitectureRecommendation.model_validate_json(output_rec.architecture_json)
        except Exception as e:
            logger.warning("Failed to deserialize saved architecture: %s", e)

    if output_rec and output_rec.security_json:
        try:
            security = SecurityReview.model_validate_json(output_rec.security_json)
        except Exception as e:
            logger.warning("Failed to deserialize saved security: %s", e)

    if output_rec and output_rec.documentation_json:
        try:
            documentation = DraftDocumentation.model_validate_json(output_rec.documentation_json)
        except Exception as e:
            logger.warning("Failed to deserialize saved documentation: %s", e)

    rag_available = rag_retriever.is_available
    new_chunks = []

    # Step 1: Requirements if missing
    if not requirements:
        try:
            requirements, provider = await _run_with_timeout(
                run_requirement_agent(request),
                settings.agent_timeout,
                "requirement",
            )
            providers_used.add(provider)
            new_chunks.extend(create_chunks(requirements.model_dump_json(), source_name="analysis:requirements"))
        except Exception as e:
            logger.error("Requirement agent failed during resume: %s", e)
            errors.append(AgentError(agent="requirement", error=str(e)))

    # Step 2: Architecture if missing
    if requirements and not architecture:
        try:
            architecture, provider = await _run_with_timeout(
                run_architecture_agent(request, requirements),
                settings.agent_timeout,
                "architecture",
            )
            providers_used.add(provider)
            new_chunks.extend(create_chunks(architecture.pattern_rationale, source_name="analysis:architecture"))
        except Exception as e:
            logger.error("Architecture agent failed during resume: %s", e)
            errors.append(AgentError(agent="architecture", error=str(e)))

    # Step 3: Security if missing
    if requirements and architecture and not security:
        try:
            security, provider = await _run_with_timeout(
                run_security_agent(request, requirements, architecture),
                settings.agent_timeout,
                "security",
            )
            providers_used.add(provider)
            new_chunks.extend(create_chunks(json.dumps(security.recommendations), source_name="analysis:security"))
        except Exception as e:
            logger.error("Security agent failed during resume: %s", e)
            errors.append(AgentError(agent="security", error=str(e)))

    # Step 4: Documentation if missing
    if requirements and architecture and security and not documentation:
        try:
            documentation, provider = await _run_with_timeout(
                run_documentation_agent(request, requirements, architecture, security),
                settings.agent_timeout,
                "documentation",
            )
            providers_used.add(provider)
        except Exception as e:
            logger.error("Documentation agent failed during resume: %s", e)
            errors.append(AgentError(agent="documentation", error=str(e)))

    prev_elapsed = float(output_rec.elapsed_seconds) if output_rec and output_rec.elapsed_seconds else 0.0
    elapsed = round(prev_elapsed + (time.time() - start), 2)
    ai_provider = "mixed" if len(providers_used) > 1 else (next(iter(providers_used)) if providers_used else "template")

    if documentation:
        status = "partial" if errors else "complete"
    elif requirements or architecture or security:
        status = "partial"
    else:
        status = "failed"

    response = AnalysisResponse(
        session_id=analysis_id,
        project_name=request.project_name,
        status=status,
        requirements=requirements,
        architecture=architecture,
        security=security,
        documentation=documentation,
        errors=errors,
        ai_provider_used=ai_provider,
        rag_available=rag_available,
        elapsed_seconds=elapsed,
    )

    # Persist updated status & outputs in DB
    if not analysis_rec:
        analysis_rec = Analysis(
            id=analysis_id,
            project_name=request.project_name,
            intake_json=json.dumps(request.model_dump()),
            status=status,
        )
        db.add(analysis_rec)
    else:
        analysis_rec.status = status

    if new_chunks:
        vectorized_chunks = await process_and_vectorize_chunks(new_chunks)
        for c in vectorized_chunks:
            db.add(
                Chunk(
                    analysis_id=analysis_id,
                    source=c["source"],
                    text=c["text"],
                    token_count=c["token_count"],
                    vector_json=json.dumps(c["vector"]),
                )
            )

    if not output_rec:
        output_rec = AnalysisOutput(analysis_id=analysis_id)
        db.add(output_rec)

    output_rec.requirements_json = requirements.model_dump_json() if requirements else ""
    output_rec.architecture_json = architecture.model_dump_json() if architecture else ""
    output_rec.security_json = security.model_dump_json() if security else ""
    output_rec.documentation_json = documentation.model_dump_json() if documentation else ""
    output_rec.provider = ai_provider
    output_rec.elapsed_seconds = str(elapsed)

    db.commit()

    session.analysis = response
    return response

