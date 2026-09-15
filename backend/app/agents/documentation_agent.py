"""Documentation generation agent."""

from __future__ import annotations

from app.agents.base import run_agent
from app.models.schemas import (
    AnalyzeRequest,
    ArchitectureRecommendation,
    ConfidenceLevel,
    DocumentSection,
    DraftDocumentation,
    SecurityReview,
    StructuredRequirements,
)
from app.rag.retriever import rag_retriever

SYSTEM_PROMPT = """You are a technical documentation specialist for solution architecture.
Generate a High-Level Design (HLD) document following these ARCHITECTURE ANALYSIS QUALITY RULES:

1. HLD GENERATION:
   - Construct HLD strictly based on validated requirements, architecture design, and security findings.
   - Do NOT introduce new unsupported business facts, SLAs, or data classifications at the HLD stage.
   - Clearly communicate: Business Context, Atomic Requirements, Constraints & Assumptions, Architecture Overview, Runtime & Ingestion Data Flows, Component Responsibilities, Security Considerations, Resilience/Failover, Architecture Decision Trade-offs, and Open Questions.
2. CONCISE FORMATTING:
   - Keep section content concise, clear, and high-density. Avoid filler paragraphs to conserve output tokens.

Respond with valid JSON only."""

SCHEMA_HINT = """{
  "document_type": "HLD",
  "title": "string",
  "sections": [{"heading": "...", "content": "...", "order": 1}],
  "metadata": {"author": "ASAC", "version": "0.1"},
  "export_formats": ["markdown", "json"]
}"""


def _template_fallback(
    request: AnalyzeRequest,
    requirements: StructuredRequirements,
    architecture: ArchitectureRecommendation,
    security: SecurityReview,
) -> DraftDocumentation:
    components_text = "\n".join(
        f"- **{c.name}**: {c.purpose} ({c.technology or 'TBD'})"
        for c in architecture.components
    )
    findings_text = "\n".join(
        f"- [{f.severity.upper()}] {f.category}: {f.description}"
        for f in security.findings[:5]
    )

    return DraftDocumentation(
        document_type="HLD",
        title=f"High-Level Design: {request.project_name}",
        sections=[
            DocumentSection(
                heading="1. Executive Summary",
                content=(
                    f"This document describes the high-level architecture for **{request.project_name}**, "
                    f"a {request.domain} initiative. The recommended pattern is "
                    f"**{architecture.pattern_name}**.\n\n"
                    f"**Business Goals:** {request.business_goals}"
                ),
                order=1,
            ),
            DocumentSection(
                heading="2. Requirements Overview",
                content=(
                    "**Functional Requirements:**\n"
                    + "\n".join(f"- {r}" for r in requirements.functional)
                    + "\n\n**Non-Functional Requirements:**\n"
                    + "\n".join(f"- {r}" for r in requirements.non_functional)
                ),
                order=2,
            ),
            DocumentSection(
                heading="3. Architecture Overview",
                content=(
                    f"**Pattern:** {architecture.pattern_name}\n\n"
                    f"**Rationale:** {architecture.pattern_rationale}\n\n"
                    f"**Components:**\n{components_text}"
                ),
                order=3,
            ),
            DocumentSection(
                heading="4. Architecture Diagram",
                content=f"```mermaid\n{architecture.mermaid_diagram}\n```",
                order=4,
            ),
            DocumentSection(
                heading="5. Security Considerations",
                content=(
                    f"**Overall Risk Level:** {security.overall_risk.upper()}\n\n"
                    f"**Key Findings:**\n{findings_text}\n\n"
                    f"**Recommendations:**\n"
                    + "\n".join(f"- {r}" for r in security.recommendations)
                ),
                order=5,
            ),
            DocumentSection(
                heading="6. Constraints & Assumptions",
                content=(
                    "**Constraints:**\n"
                    + "\n".join(f"- {c}" for c in requirements.constraints_summary)
                    + "\n\n**Assumptions:**\n"
                    + "\n".join(f"- {a}" for a in requirements.assumptions)
                ),
                order=6,
            ),
            DocumentSection(
                heading="7. Open Questions",
                content="\n".join(f"- {q}" for q in requirements.open_questions),
                order=7,
            ),
        ],
        metadata={
            "author": "ASAC - AI Solution Architect Copilot",
            "version": "0.1-draft",
            "project": request.project_name,
            "domain": request.domain,
            "generated_by": "template",
        },
        export_formats=["markdown", "json"],
    )


async def run_documentation_agent(
    request: AnalyzeRequest,
    requirements: StructuredRequirements,
    architecture: ArchitectureRecommendation,
    security: SecurityReview,
) -> tuple[DraftDocumentation, str]:
    rag_sources = rag_retriever.retrieve("HLD document template architecture")
    rag_context = "\n\n".join(f"[{s.title}]: {s.excerpt}" for s in rag_sources)

    comp_summary = ", ".join(c.name for c in architecture.components[:4])
    func_summary = "; ".join(requirements.functional[:3])

    user_prompt = f"""Generate HLD documentation for:
Project: {request.project_name} ({request.domain})
Architecture Pattern: {architecture.pattern_name}
Key Components: {comp_summary}
Security Risk Level: {security.overall_risk}
Key Requirements: {func_summary}
"""
    return await run_agent(
        "documentation",
        SYSTEM_PROMPT,
        user_prompt,
        DraftDocumentation,
        SCHEMA_HINT,
        lambda: _template_fallback(request, requirements, architecture, security),
    )
