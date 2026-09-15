"""Security review agent."""

from __future__ import annotations

from app.agents.base import run_agent
from app.models.schemas import (
    AnalyzeRequest,
    ArchitectureRecommendation,
    ConfidenceLevel,
    RagSource,
    SecurityFinding,
    SecurityReview,
    StructuredRequirements,
)
from app.rag.retriever import rag_retriever

SYSTEM_PROMPT = """You are a senior security architect.
Perform a contextual security review following these ARCHITECTURE ANALYSIS QUALITY RULES:

1. DOMAIN-ACCURATE SERVICE CAPABILITIES (ZERO WRONG SERVICE RECOMMENDATIONS):
   - DO NOT recommend a cloud service for a security capability unless the service actually provides that specific capability.
   - Example: Amazon Macie is for sensitive data discovery and PII inspection on Amazon S3; it does NOT scan for viruses or malware. For malware/virus scanning, recommend AWS GuardDuty Malware Protection, ClamAV, or trend micro/third-party S3 scanners.
   - When uncertain about a specific cloud vendor product name, state the generic capability category (e.g. "Container Vulnerability Scanner", "Static Malware Analyzer") rather than hallucinating an inaccurate service name.

2. CONTEXTUAL & DOMAIN-ACCURATE SECURITY:
   - Carefully inspect the application type and domain. For public/anonymous systems (e.g. public FAQ chatbot on a website, static help center), DO NOT invent Authentication, Authorization, User Account, or PII Data Protection findings unless explicit user login or personal data handling is stated.
   - For public FAQ chatbots or simple web widgets, focus strictly on relevant threat vectors: API rate-limiting, prompt injection, DDoS mitigation, web application firewall (WAF) throttling, and CORS policies.
   - NEVER invent non-existent PII, financial data, health data, or enterprise compliance mandates not established by the intake or architecture.

3. CLASSIFICATION & REFERENCE MATERIAL:
   - Differentiate findings into: Confirmed Risk/Requirement, Recommended Control, and Open Security Question.
   - Standard framework checklists (OWASP, NIST) provide guidance, but checklist items must not automatically become findings unless applicable to the specific project domain.

4. CONCISE FORMATTING:
   - Keep finding descriptions, remediations, and recommendations crisp, high-density, and direct to conserve output tokens.

Respond with valid JSON only."""

SCHEMA_HINT = """{
  "overall_risk": "critical|high|medium|low",
  "findings": [{"severity": "critical|high|medium|low|info", "category": "...", "description": "...", "remediation": "..."}],
  "compliance_gaps": ["..."],
  "recommendations": ["..."],
  "checklist_coverage": {"authentication": true, "encryption_at_rest": true},
  "confidence": "high|medium|low"
}"""


def _template_fallback(
    request: AnalyzeRequest,
    architecture: ArchitectureRecommendation,
    rag_sources: list[RagSource],
) -> SecurityReview:
    compliance = request.compliance or "Standard web application security baseline"
    is_public = "faq" in request.domain.lower() or "public" in request.domain.lower() or "chatbot" in request.project_name.lower()

    if is_public:
        findings = [
            SecurityFinding(
                severity="high",
                category="API Rate Limiting & Denial of Service",
                description=f"Public endpoints for {request.project_name} are vulnerable to automated scraping and volumetric DDoS without aggressive rate limiting.",
                remediation="Deploy Web Application Firewall (WAF) rate-limiting rules and Cloudflare / AWS Shield protection.",
            ),
            SecurityFinding(
                severity="medium",
                category="Prompt Injection & Input Validation",
                description="Public chat inputs require strict sanitization to prevent prompt injection and indirect model manipulation.",
                remediation="Implement input validation filters, system prompt boundary guarding, and maximum query token length caps.",
            ),
            SecurityFinding(
                severity="medium",
                category="CORS & Web Widget Hardening",
                description="Public chatbot widget script must enforce strict origin checks to prevent unauthorized third-party site embedding.",
                remediation="Configure explicit CORS headers and Content Security Policy (CSP) frame-ancestors directives.",
            ),
            SecurityFinding(
                severity="low",
                category="API Key & Model Provider Protection",
                description="Model provider API keys must never be exposed to the client browser.",
                remediation="Route all LLM requests through backend API proxy with secret storage in KMS / Key Vault.",
            ),
        ]
        gaps = [
            f"Verify alignment with: {compliance}",
            "CORS allowed origins list not explicitly defined",
            "Public query logging retention period to be confirmed",
        ]
    else:
        findings = [
            SecurityFinding(
                severity="high",
                category="Authentication & RBAC",
                description=f"Enforce enterprise OAuth2/OIDC single sign-on with MFA for {request.project_name} users.",
                remediation="Integrate with enterprise IdP, enforce MFA, implement token rotation.",
            ),
            SecurityFinding(
                severity="medium",
                category="Data Protection",
                description="Data at rest and in transit requires encryption.",
                remediation="Enable TLS 1.3 for network transit and KMS AES-256 for persistent database storage.",
            ),
            SecurityFinding(
                severity="medium",
                category="API Security",
                description="API Gateway must implement rate limiting and input validation.",
                remediation="Configure WAF rules, OWASP API Top 10 controls, request size limits.",
            ),
            SecurityFinding(
                severity="low",
                category="Logging",
                description="Security events must be centrally logged and monitored.",
                remediation="Integrate with SIEM, alert on anomalous access patterns.",
            ),
        ]
        gaps = [
            f"Verify alignment with: {compliance}",
            "Data retention policy not specified for transaction history",
            "Cross-border data transfer controls need assessment",
        ]

    return SecurityReview(
        overall_risk="medium" if is_public else "high",
        findings=findings,
        compliance_gaps=gaps,
        recommendations=[
            "Conduct threat modeling workshop before production deployment",
            "Implement WAF rate-limiting and query length limits",
            "Regular penetration testing of API endpoints",
            "Establish security monitoring alerts for anomalous traffic",
        ],
        checklist_coverage={
            "authentication": not is_public,
            "authorization": not is_public,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "input_validation": True,
            "logging_monitoring": True,
            "secrets_management": True,
            "vulnerability_scanning": False,
        },
        confidence=ConfidenceLevel.LOW,
    )


async def run_security_agent(
    request: AnalyzeRequest,
    requirements: StructuredRequirements,
    architecture: ArchitectureRecommendation,
) -> tuple[SecurityReview, str]:
    query = f"security review {request.compliance} {architecture.pattern_name} OWASP"
    rag_sources = rag_retriever.retrieve(query)
    rag_context = "\n\n".join(f"[{s.title}]: {s.excerpt}" for s in rag_sources) or "No RAG context."

    comp_summary = ", ".join(c.name for c in architecture.components[:4])
    func_summary = "; ".join(requirements.functional[:3])

    user_prompt = f"""Security review for:
Project: {request.project_name} ({request.domain})
Compliance: {request.compliance or 'Standard web baseline'}
Architecture Pattern: {architecture.pattern_name}
Components: {comp_summary}
Key Requirements: {func_summary}
RAG Security Context: {rag_context[:300]}
"""
    return await run_agent(
        "security",
        SYSTEM_PROMPT,
        user_prompt,
        SecurityReview,
        SCHEMA_HINT,
        lambda: _template_fallback(request, architecture, rag_sources),
    )
