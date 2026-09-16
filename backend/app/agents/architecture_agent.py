"""Architecture recommendation agent."""

from __future__ import annotations

from app.agents.base import run_agent
from app.models.schemas import (
    AlternativeConsidered,
    ArchitectureComponent,
    ArchitectureRecommendation,
    AnalyzeRequest,
    ConfidenceLevel,
    IntegrationPoint,
    RagSource,
    RequirementMapping,
    StructuredRequirements,
    TradeOff,

)
from app.rag.retriever import rag_retriever

SYSTEM_PROMPT = """You are a senior cloud solution architect.
Recommend a domain-tailored architecture following these 7 ARCHITECTURAL QUALITY RULES:

1. ARCHITECTURE DECISION RATIONALE:
   - For key architectural choices and patterns, explicitly provide the decision rationale ("Why") and rejected alternatives ("Why not selected").

2. END-TO-END TRACEABILITY:
   - Provide clear requirement-to-architecture mappings (`requirement_mappings`). Trace every component directly back to an explicit requirement, confirmed assumption, or derived technical capability.

3. CONFLICT PREVENTION & PIPELINE CONSISTENCY:
   - Inspect upstream requirements and database assumptions. If requirements assume a relational model (PostgreSQL/MySQL), DO NOT switch to a non-relational document/key-value store (e.g. DynamoDB/MongoDB) without explicitly noting the migration rationale in trade-offs and alternatives considered.

4. ACCURATE CLOUD SERVICE RECOMMENDATIONS:
   - Do NOT recommend a cloud service or security capability unless the service ACTUALLY PROVIDES that capability.
   - Example: AWS Macie is for sensitive PII discovery on S3, NOT virus/malware scanning (use AWS GuardDuty Malware Protection or ClamAV for virus scanning).

5. DYNAMIC MERMAID DIAGRAM:
   - The `mermaid_diagram` MUST BE A RICH MULTI-TIERED MERMAID DIAGRAM constructed dynamically for THIS project.
   - Use subgraphs depicting: Ingress/Edge, Auth/Security, Compute/App Services, Data/Cache/Vector, and AI/External Systems.
   - MUST USE EXACT NODE NAMES MATCHING YOUR `components` LIST.

6. APPLICATION COMPLETENESS & RESILIENCE:
   - Proactively include standard technical capabilities required for the solution type (API layer, session store, caching, security boundaries, rate limiting, and observability).

7. CONCISE FORMATTING:
   - Keep pattern rationale, component purposes, decision trade-offs, and rejected alternatives high-density and structured.

Respond with valid JSON only."""

SCHEMA_HINT = """{
  "pattern_name": "Name of the Architecture Pattern",
  "pattern_rationale": "Why this architecture fits the requirements",
  "components": [{"name": "Specific Component Name", "purpose": "Clear purpose", "technology": "Specific Technology"}],
  "integration_points": [{"source": "Source Component Name", "target": "Target Component Name", "protocol": "HTTPS/gRPC/SQL", "description": "Interaction description"}],
  "requirement_mappings": [{"requirement": "Specific Requirement", "component": "Specific Component Name"}],
  "trade_offs": [{"decision": "Key Architectural Decision", "benefit": "Major benefit", "cost": "Trade-off or cost"}],
  "alternatives_considered": [{"name": "Alternative Architecture", "reason_rejected": "Why rejected"}],
  "mermaid_diagram": "DYNAMIC MERMAID GRAPH STRING: Generate valid Mermaid graph TD string with subgraphs using your exact component names above",
  "confidence": "high|medium|low"
}"""



def _template_fallback(
    request: AnalyzeRequest,
    requirements: StructuredRequirements,
    rag_sources: list[RagSource],
) -> ArchitectureRecommendation:
    cloud = request.constraints.cloud or "AWS/Azure"
    
    mappings = []
    for req in (requirements.functional[:3] if requirements.functional else ["Core functionality"]):
        mappings.append(RequirementMapping(requirement=req, component="API Gateway / Services"))

    return ArchitectureRecommendation(
        pattern_name="Cloud-Native Microservices with Event-Driven Integration",
        pattern_rationale=(
            f"For {request.project_name} in the {request.domain} domain, a microservices "
            "architecture with event-driven communication provides scalability, team autonomy, "
            "and resilience for loyalty/modernization workloads."
        ),
        components=[
            ArchitectureComponent(
                name="API Gateway",
                purpose="Central entry point, routing, rate limiting and authentication",
                technology=f"{cloud} API Gateway",
            ),
            ArchitectureComponent(
                name=f"{request.project_name} Web/UI Client",
                purpose=f"User interface for {request.project_name}",
                technology="React / Next.js",
            ),
            ArchitectureComponent(
                name="Core Application Service",
                purpose=f"Core backend business logic for {request.project_name} ({request.domain})",
                technology="FastAPI / Node.js",
            ),
            ArchitectureComponent(
                name="Cache & Messaging Layer",
                purpose="Session storage, real-time messaging, and query caching",
                technology="Redis / WebSocket",
            ),
            ArchitectureComponent(
                name="Primary Database",
                purpose="Persistent relational storage for project state and domain data",
                technology="PostgreSQL",
            ),
            ArchitectureComponent(
                name="Identity Provider",
                purpose="Authentication, authorization, and RBAC",
                technology="OAuth2 / OIDC",
            ),
        ],
        integration_points=[
            IntegrationPoint(
                source="Web/UI Client",
                target="API Gateway",
                protocol="HTTPS/WSS",
                description="Client requests and real-time streams routed to gateway",
            ),
            IntegrationPoint(
                source="API Gateway",
                target="Core Application Service",
                protocol="HTTPS/REST",
                description="Gateway routes verified requests to application service",
            ),
            IntegrationPoint(
                source="Core Application Service",
                target="Cache & Messaging Layer",
                protocol="Redis TCP",
                description="Fast caching and pub/sub message distribution",
            ),
            IntegrationPoint(
                source="Core Application Service",
                target="Primary Database",
                protocol="SQL / TCP",
                description="Persistent data retrieval and transactional storage",
            ),
        ],
        requirement_mappings=mappings,
        trade_offs=[
            TradeOff(
                decision="Decoupled Gateway + Service Architecture",
                benefit="Improved security isolation and independent component scaling",
                cost="Slight network overhead across component boundary",
            ),
            TradeOff(
                decision="Redis In-Memory Cache with Relational Persistence",
                benefit="Sub-millisecond read response times for high concurrent traffic",
                cost="Requires cache invalidation strategy and dual storage management",
            ),
        ],
        alternatives_considered=[
            AlternativeConsidered(
                name="Single Monolithic App",
                reason_rejected="Harder to scale real-time user concurrency independently from storage",
            ),
            AlternativeConsidered(
                name="Pure Serverless Architecture",
                reason_rejected="Cold start latency and persistent connection overhead for real-time channels",
            ),
        ],
        mermaid_diagram=f"""graph TD
    subgraph Ingress_Tier["Edge & Ingress Tier"]
        Client["{request.project_name} UI"] -->|HTTPS / WSS| CDN["CDN & Web Application Firewall"]
        CDN --> GW["API Gateway & Reverse Proxy"]
    end
    subgraph Compute_Tier["Application & Compute Tier"]
        GW --> Auth["OAuth2 / OIDC Identity Provider"]
        GW --> App["Core App Engine Service"]
        App --> Worker["Async Job Worker / Task Queue"]
    end
    subgraph Storage_Tier["Data, Cache & Search Tier"]
        App -->|SQL Queries| DB[("Relational Database")]
        App -->|In-Memory Cache| Cache["Redis Cache / Session Store"]
        Worker -->|Vector Embeddings| VectorDB[("Vector Knowledge Store")]
    end
    subgraph AI_Tier["AI Model Provider Tier"]
        App --> LLM["Primary Model Provider"]
        LLM -. Circuit Breaker Failover .-> FallbackLLM["Fallback AI Provider"]
    end""",
        rag_sources=rag_sources,
        confidence=ConfidenceLevel.LOW,
    )



import re

def _generate_dynamic_mermaid(request: AnalyzeRequest, result: ArchitectureRecommendation) -> str:
    """Build a readable tiered diagram while preserving generated component relationships."""
    components = result.components
    if not components:
        return f"""graph TD
    subgraph Client_Layer["Client Layer"]
        Client["{request.project_name} UI"] -->|HTTPS| GW["API Gateway"]
    end
    subgraph App_Layer["Application Services"]
        GW --> App["Core App Engine"]
    end
    subgraph Data_Layer["Storage Tier"]
        App --> DB[("Primary Database")]
    end"""

    ingress_nodes = []
    auth_nodes = []
    compute_nodes = []
    storage_nodes = []
    ai_nodes = []
    component_ids: dict[str, str] = {}
    used_ids: set[str] = set()

    def clean(value: str) -> str:
        return value.replace('"', "'").replace("\n", " ").strip()

    def component_label(node_id: str, component: ArchitectureComponent) -> str:
        name = clean(component.name)
        technology = clean(component.technology or "")
        purpose = clean(component.purpose)
        detail = f"<br/><b>{technology}</b>" if technology else ""
        detail += f"<br/><small>{purpose[:100]}</small>" if purpose else ""
        return f'{node_id}["{name}{detail}"]'

    for c in components:
        name_clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', c.name).strip() or "Component"
        name_lower = (c.name + " " + (c.technology or "") + " " + c.purpose).lower()
        node_id = re.sub(r'[^a-zA-Z0-9]', '', name_clean) or "Node"
        if not node_id[0].isalpha():
            node_id = "N" + node_id
        base_id = node_id
        suffix = 2
        while node_id in used_ids:
            node_id = f"{base_id}{suffix}"
            suffix += 1
        used_ids.add(node_id)
        component_ids[c.name.lower().strip()] = node_id
        label = component_label(node_id, c)

        if any(w in name_lower for w in ["gateway", "waf", "cdn", "ingress", "frontend", "ui", "client", "proxy", "alb", "cloudfront"]):
            ingress_nodes.append((node_id, label))
        elif any(w in name_lower for w in ["auth", "cognito", "identity", "oidc", "iam", "keycloak", "sso"]):
            auth_nodes.append((node_id, label))
        elif any(w in name_lower for w in ["db", "database", "postgres", "mysql", "aurora", "redis", "cache", "s3", "storage", "vector", "pinecone", "opensearch", "qdrant", "chroma", "mongo"]):
            storage_nodes.append((node_id, label))
        elif any(w in name_lower for w in ["llm", "ai", "bedrock", "openai", "groq", "model", "gpt", "anthropic", "claude"]):
            ai_nodes.append((node_id, label))
        elif any(w in name_lower for w in ["worker", "service", "app", "engine", "backend", "microservice", "celery", "lambda", "ecs", "eks", "k8s", "kubernetes", "processor", "pipeline", "ingest"]):
            compute_nodes.append((node_id, label))
        else:
            compute_nodes.append((node_id, label))

    lines = ["graph TD"]

    # Subgraph 1: Ingress
    lines.append('    subgraph Ingress_Tier["Edge & Ingress Tier"]')
    lines.append(f'        Client["{request.project_name} UI / Client"] -->|HTTPS / REST| GW["API Gateway & Reverse Proxy"]')
    for _, lbl in ingress_nodes:
        lines.append(f'        GW --> {lbl}')
    lines.append('    end')

    # Subgraph 2: Compute
    lines.append('    subgraph Compute_Tier["Application & Compute Services"]')
    for _, lbl in compute_nodes:
        lines.append(f'        {lbl}')
    for _, lbl in auth_nodes:
        lines.append(f'        {lbl}')
    if not compute_nodes:
        compute_nodes = [("AppEngine", f'AppEngine["{request.project_name} Core App Service"]')]
        lines.append(f'        {compute_nodes[0][1]}')
    lines.append('    end')

    # Subgraph 3: Storage
    lines.append('    subgraph Storage_Tier["Storage, Caching & Vector Tier"]')
    for _, lbl in storage_nodes:
        lines.append(f'        {lbl}')
    if not storage_nodes:
        storage_nodes = [("MainDB", 'MainDB[("Primary Database")]')]
        lines.append(f'        {storage_nodes[0][1]}')
    lines.append('    end')

    # Subgraph 4: AI
    if ai_nodes:
        lines.append('    subgraph AI_Tier["AI & Model Services"]')
        for _, lbl in ai_nodes:
            lines.append(f'        {lbl}')
        lines.append('    end')

    # Connect the client and gateway to the primary application component.
    first_compute = compute_nodes[0][0]
    lines.append(f'    GW -->|Authenticated Request| {first_compute}')

    def resolve_component(name: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9]", "", name.lower())
        for component_name, node_id in component_ids.items():
            candidate = re.sub(r"[^a-z0-9]", "", component_name)
            if normalized == candidate or normalized in candidate or candidate in normalized:
                return node_id
        return None

    valid_integrations = 0
    for integration in result.integration_points:
        source_id = resolve_component(integration.source)
        target_id = resolve_component(integration.target)
        if source_id and target_id and source_id != target_id:
            protocol = clean(integration.protocol or "connects")
            lines.append(f'    {source_id} -->|{protocol[:30]}| {target_id}')
            valid_integrations += 1

    # Keep a useful fallback when the model omitted usable integration endpoints.
    if valid_integrations == 0:
        for nid, _ in compute_nodes[1:]:
            lines.append(f'    {first_compute} --> {nid}')
        for nid, _ in storage_nodes:
            lines.append(f'    {first_compute} -->|Read / Write| {nid}')
        for nid, _ in ai_nodes:
            lines.append(f'    {first_compute} -->|Infer / Query| {nid}')

    return "\n".join(lines)


async def run_architecture_agent(
    request: AnalyzeRequest,
    requirements: StructuredRequirements,
) -> tuple[ArchitectureRecommendation, str]:
    query = f"{request.domain} {request.project_name} architecture {request.business_goals}"
    rag_sources = rag_retriever.retrieve(query)
    rag_context = "\n\n".join(f"[{s.title}]: {s.excerpt}" for s in rag_sources) or "No RAG context available."

    func_summary = "; ".join(requirements.functional[:4])
    nfr_summary = "; ".join(requirements.non_functional[:3])
    constraints_summary = "; ".join(requirements.constraints_summary[:3])

    user_prompt = f"""Design architecture for:
Project: {request.project_name} ({request.domain})
Business Goals: {request.business_goals}
Functional Reqs: {func_summary}
Non-Functional Reqs: {nfr_summary}
Constraints: {constraints_summary}
RAG Context: {rag_context[:300]}
"""
    result, provider = await run_agent(
        "architecture",
        SYSTEM_PROMPT,
        user_prompt,
        ArchitectureRecommendation,
        SCHEMA_HINT,
        lambda: _template_fallback(request, requirements, rag_sources),
    )
    if not result.rag_sources:
        result.rag_sources = rag_sources

    # Ensure dynamic diagram matches the actual components generated for this project
    if not result.mermaid_diagram or "Client App" in result.mermaid_diagram or len(result.mermaid_diagram.strip()) < 30:
        result.mermaid_diagram = _generate_dynamic_mermaid(request, result)

    return result, provider
