"""Requirement extraction agent."""

from __future__ import annotations

from app.agents.base import run_agent
from app.models.schemas import AnalyzeRequest, ConfidenceLevel, StructuredRequirements

SYSTEM_PROMPT = """You are a senior solution architect specializing in requirements analysis.
Extract and structure deep, comprehensive requirements from the project intake following these 7 ARCHITECTURAL QUALITY RULES:

1. HARD RULE AGAINST INVENTED REQUIREMENTS & HALLUCINATIONS:
   - NEVER introduce business requirements, SLAs, budgets, cloud providers, performance targets, file size limits, retention periods, compliance mandates, or user volumes that are NOT explicitly present in user input or supporting documents.
   - If a capability is necessary but unstated, classify it under "assumptions" or "open_questions". NEVER fabricate arbitrary numeric targets (e.g. 99.999% SLA or 5,000 users) if unstated.

2. CLASSIFY & ATTRIBUTE SOURCE TO EVERY ITEM:
   - For every requirement, prefix or attribute its source context where applicable (e.g. "Source: User Input", "Source: Confirmed Answer", "Source: Derived Capability").

3. DISTINCT CATEGORIZATION:
   - Strictly separate items into: EXPLICIT REQUIREMENTS, DERIVED REQUIREMENTS, ASSUMPTIONS, RECOMMENDATIONS, and OPEN QUESTIONS.

4. DEDUPLICATION & ZERO DUPLICATES:
   - Ensure ZERO duplicate or synonymous statements across functional and non-functional requirement lists.

5. CROSS-VALIDATION & CONFLICT PREVENTION:
   - CROSS-VALIDATE WITH CONFIRMED INPUTS & ANSWERS: If user intake or clarification answers specify a target (e.g. 300 concurrent users), ALL generated Non-Functional Requirements MUST MATCH those numbers. NEVER generate conflicting figures.

6. DOMAIN-ACCURATE TECHNICAL RECOMMENDATIONS:
   - Recommend service capabilities with domain accuracy. Do NOT recommend a cloud service for a capability unless the service actually provides that capability (e.g. AWS Macie is for S3 data privacy/sensitive data discovery, NOT virus scanning - for virus scanning recommend ClamAV / GuardDuty Malware Protection).

7. CONCISE FORMATTING:
   - Keep requirement statements crisp, high-density, and actionable to conserve output tokens.

Respond with valid JSON only."""


SCHEMA_HINT = """{
  "functional": ["list of functional requirements"],
  "non_functional": ["list of NFRs"],
  "constraints_summary": ["list of constraints"],
  "assumptions": ["list of assumptions"],
  "open_questions": ["list of clarifying questions"],
  "confidence": "high|medium|low"
}"""


def _template_fallback(request: AnalyzeRequest) -> StructuredRequirements:
    func_lines = [
        line.strip()
        for line in request.functional_requirements.replace(";", "\n").split("\n")
        if line.strip()
    ]
    nfr_lines = [
        line.strip()
        for line in request.non_functional_requirements.replace(";", "\n").split("\n")
        if line.strip()
    ] or [
        f"High availability (99.9%+) for {request.project_name}",
        f"Sub-second response time for core {request.domain} transactions",
        "Role-based access control and TLS 1.3 data encryption",
    ]

    constraints = []
    if request.constraints.cloud:
        constraints.append(f"Cloud platform: {request.constraints.cloud}")
    if request.constraints.budget:
        constraints.append(f"Budget: {request.constraints.budget}")
    if request.constraints.timeline:
        constraints.append(f"Timeline: {request.constraints.timeline}")

    return StructuredRequirements(
        functional=func_lines or [f"Deliver {request.domain} capabilities for {request.project_name}"],
        non_functional=nfr_lines,
        constraints_summary=constraints or ["No explicit constraints provided"],
        assumptions=[
            f"Project '{request.project_name}' operates within the {request.domain} domain",
            "Target users align with enterprise organizational scale",
            "Cloud infrastructure provides baseline network redundancy",
        ],
        open_questions=[
            "What is the peak concurrent active user count during business hours?",
            "Are there existing legacy enterprise databases to integrate with?",
            "What specific data residency and compliance audit rules apply?",
        ],
        confidence=ConfidenceLevel.LOW,
    )



async def run_requirement_agent(
    request: AnalyzeRequest,
    user_clarifications: dict[str, str] | None = None,
) -> tuple[StructuredRequirements, str]:
    answers_str = (
        "\n".join(f"- {q}: {a}" for q, a in user_clarifications.items() if a.strip())
        if user_clarifications
        else "None provided"
    )

    user_prompt = f"""Analyze this project intake:

Project: {request.project_name} ({request.domain})
Business Goals: {request.business_goals}
Functional Requirements: {request.functional_requirements}
Non-Functional Requirements: {request.non_functional_requirements}
Constraints - Cloud: {request.constraints.cloud}, Budget: {request.constraints.budget}, Timeline: {request.constraints.timeline}
Compliance: {request.compliance or 'None specified'}

Confirmed User Answers to Clarification Questions:
{answers_str}

CRITICAL: Cross-validate generated NFRs and specs against the user's confirmed answers above. Do NOT generate conflicting numbers or SLA figures. Deduplicate all requirement lists strictly.
"""
    return await run_agent(
        "requirement",
        SYSTEM_PROMPT,
        user_prompt,
        StructuredRequirements,
        SCHEMA_HINT,
        lambda: _template_fallback(request),
    )


DISCOVERY_SYSTEM_PROMPT = """You are a senior solution architect performing initial Requirements Discovery.
Extract explicit requirements, infer missing technical/business capabilities (derived requirements), and identify important unknown clarification items.
DO NOT design detailed architecture or select cloud products at this stage. Focus on understanding and expanding the problem scope.

Categorize output into:
1. explicit_requirements: directly stated by the user (max 4 concise items).
2. suggested_derived_requirements: capabilities standard/necessary for this system (max 3-4 key items) with id, text (under 15 words), category, status="pending".
3. needs_clarification: important open questions that affect scope (max 3 items).
4. constraints_summary: constraints provided (max 3 items).
5. assumptions: inferred assumptions marked for validation (max 3 items).

OUTPUT BUDGET RULE: Keep all list items crisp and short. Ensure the JSON document completes fully.
Respond with valid JSON only."""

DISCOVERY_SCHEMA_HINT = """{
  "session_id": "string",
  "project_name": "string",
  "domain": "string",
  "explicit_requirements": ["..."],
  "suggested_derived_requirements": [{"id": "DER-001", "text": "...", "category": "Technical Capability", "status": "pending"}],
  "needs_clarification": ["..."],
  "constraints_summary": ["..."],
  "assumptions": ["..."],
  "confidence": "high|medium|low"
}"""


from app.models.schemas import DiscoveredRequirements, DiscoveredRequirementItem

def _discovery_template_fallback(session_id: str, request: AnalyzeRequest) -> DiscoveredRequirements:
    explicit = [
        line.strip()
        for line in request.functional_requirements.replace(";", "\n").split("\n")
        if line.strip()
    ] or [request.business_goals]

    derived = [
        DiscoveredRequirementItem(id="DER-001", text="Authentication & User Role Management", category="Security", status="pending"),
        DiscoveredRequirementItem(id="DER-002", text="Audit Logging & Activity Tracking", category="Compliance", status="pending"),
        DiscoveredRequirementItem(id="DER-003", text="Data Backup & Disaster Recovery", category="Operations", status="pending"),
        DiscoveredRequirementItem(id="DER-004", text="API Rate Limiting & Input Validation", category="Architecture", status="pending"),
    ]

    constraints = []
    if request.constraints.cloud:
        constraints.append(f"Cloud: {request.constraints.cloud}")
    if request.constraints.budget:
        constraints.append(f"Budget: {request.constraints.budget}")
    if request.constraints.timeline:
        constraints.append(f"Timeline: {request.constraints.timeline}")

    return DiscoveredRequirements(
        session_id=session_id,
        project_name=request.project_name,
        domain=request.domain,
        explicit_requirements=explicit,
        suggested_derived_requirements=derived,
        needs_clarification=[
            "What is the expected peak concurrent active user volume?",
            "Are there existing legacy systems or databases requiring data migration?",
            "What specific regulatory or data compliance standards apply?",
        ],
        constraints_summary=constraints or ["No explicit constraints specified"],
        assumptions=[
            f"System operates within the {request.domain} domain",
            "Baseline high availability (99.9%) is required during business hours",
        ],
        confidence=ConfidenceLevel.LOW,
    )

async def run_requirements_discovery_agent(session_id: str, request: AnalyzeRequest) -> tuple[DiscoveredRequirements, str]:
    user_prompt = f"""Discover requirements for:
Project: {request.project_name}
Domain: {request.domain}
Business Goals: {request.business_goals}
Functional Requirements: {request.functional_requirements}
Non-Functional Requirements: {request.non_functional_requirements}
Constraints: cloud={request.constraints.cloud}, budget={request.constraints.budget}, timeline={request.constraints.timeline}
Compliance: {request.compliance}
"""
    result, provider = await run_agent(
        "requirements_discovery",
        DISCOVERY_SYSTEM_PROMPT,
        user_prompt,
        DiscoveredRequirements,
        DISCOVERY_SCHEMA_HINT,
        lambda: _discovery_template_fallback(session_id, request),
    )
    result.session_id = session_id
    result.project_name = request.project_name
    result.domain = request.domain

    if not result.explicit_requirements:
        result.explicit_requirements = [
            line.strip()
            for line in request.functional_requirements.replace(";", "\n").split("\n")
            if line.strip()
        ] or [request.business_goals]

    if not result.needs_clarification:
        result.needs_clarification = [
            "What is the expected peak concurrent active user volume?",
            "Are there existing legacy systems or databases requiring data migration?",
            "What specific regulatory or data compliance standards apply?",
        ]

    if not result.assumptions:
        result.assumptions = [
            f"System operates within the {request.domain} domain scope",
            "High availability (99.9%) is required during operational business hours",
        ]

    return result, provider

