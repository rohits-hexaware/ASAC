"""Pydantic schemas for ASAC structured outputs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# --- Intake / Request Models ---


class ConstraintsInput(BaseModel):
    cloud: str | None = Field(default=None, max_length=200)
    budget: str | None = Field(default=None, max_length=200)
    timeline: str | None = Field(default=None, max_length=200)


class AnalyzeRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., min_length=1, max_length=200)
    business_goals: str = Field(..., min_length=1, max_length=10000)
    functional_requirements: str = Field(..., min_length=1, max_length=20000)
    constraints: ConstraintsInput = Field(default_factory=ConstraintsInput)
    non_functional_requirements: str = Field(default="", max_length=10000)
    compliance: str = Field(default="", max_length=5000)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=4000)


class DiscoveredRequirementItem(BaseModel):
    id: str
    text: str
    category: str = "General"
    status: Literal["accepted", "rejected", "pending"] = "pending"

class DiscoveredRequirements(BaseModel):
    session_id: str = ""
    project_name: str = ""
    domain: str = ""
    explicit_requirements: list[str] = Field(default_factory=list)
    suggested_derived_requirements: list[DiscoveredRequirementItem] = Field(default_factory=list)
    needs_clarification: list[str] = Field(default_factory=list)
    constraints_summary: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

class ValidatedRequirementsContext(BaseModel):
    explicit_requirements: list[str] = Field(default_factory=list)
    confirmed_derived_requirements: list[str] = Field(default_factory=list)
    rejected_suggestions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    user_clarifications: dict[str, str] = Field(default_factory=dict)

class ConfirmRequirementsRequest(BaseModel):
    session_id: str
    intake: AnalyzeRequest
    validated_context: ValidatedRequirementsContext

class StructuredRequirements(BaseModel):
    functional: list[str] = Field(default_factory=list)
    non_functional: list[str] = Field(default_factory=list)
    constraints_summary: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    validated_context: ValidatedRequirementsContext | None = None


class ArchitectureComponent(BaseModel):
    name: str = "Core App"
    purpose: str = "Handles core application domain logic"
    technology: str | None = "Python / FastAPI"


class IntegrationPoint(BaseModel):
    source: str = "Client"
    target: str = "API Gateway"
    protocol: str = "HTTPS"
    description: str = "REST API request/response"


class TradeOff(BaseModel):
    decision: str = "Monolith vs Microservices"
    benefit: str = "Simpler deployment and lower operational cost"
    cost: str = "Independent component scaling requires refactoring"


class AlternativeConsidered(BaseModel):
    name: str = "Serverless"
    reason_rejected: str = "Potential cold-start latency"


class RagSource(BaseModel):
    title: str = "Architecture Guide"
    path: str = ""
    excerpt: str = ""
    score: float | None = None


class RequirementMapping(BaseModel):
    requirement: str = "Core Domain Features"
    component: str = "Core App Service"


class ArchitectureRecommendation(BaseModel):
    pattern_name: str = "Layered Monolith Architecture"
    pattern_rationale: str = "Domain-driven architecture focused on reliability and maintainability."
    components: list[ArchitectureComponent] = Field(default_factory=list)
    integration_points: list[IntegrationPoint] = Field(default_factory=list)
    requirement_mappings: list[RequirementMapping] = Field(default_factory=list)
    trade_offs: list[TradeOff] = Field(default_factory=list)
    alternatives_considered: list[AlternativeConsidered] = Field(default_factory=list)
    mermaid_diagram: str = ""
    rag_sources: list[RagSource] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SecurityFinding(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"] = "medium"
    category: str = "General Security"
    description: str = "Security monitoring baseline"
    remediation: str = "Apply TLS 1.3 and input sanitization"


class SecurityReview(BaseModel):
    overall_risk: Literal["critical", "high", "medium", "low"] = "medium"
    findings: list[SecurityFinding] = Field(default_factory=list)
    compliance_gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    checklist_coverage: dict[str, bool] = Field(default_factory=dict)
    rag_sources: list[RagSource] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class DocumentSection(BaseModel):
    heading: str = "Section"
    content: str = ""
    order: int = 1


class DraftDocumentation(BaseModel):
    document_type: str = "HLD"
    title: str = "High-Level Design Document"
    sections: list[DocumentSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    export_formats: list[str] = Field(default_factory=lambda: ["markdown", "json"])
    rag_sources: list[RagSource] = Field(default_factory=list)



# --- Pipeline / Response Models ---


class AgentError(BaseModel):
    agent: str
    error: str


class PipelineStage(str, Enum):
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisResponse(BaseModel):
    session_id: str
    project_name: str
    status: Literal["complete", "partial", "failed"]
    requirements: StructuredRequirements | None = None
    architecture: ArchitectureRecommendation | None = None
    security: SecurityReview | None = None
    documentation: DraftDocumentation | None = None
    errors: list[AgentError] = Field(default_factory=list)
    ai_provider_used: str = "template"
    rag_available: bool = False
    elapsed_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    messages: list[ChatMessage]
    ai_provider_used: str = "template"


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str = "1.0.0"
    ai_providers: dict[str, str]
    rag: dict[str, Any]
    sessions_active: int = 0
