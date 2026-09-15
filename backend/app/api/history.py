"""History routes for retrieving and downloading past analyses."""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.models import get_db, Analysis, AnalysisOutput, Document
from app.models.schemas import AnalysisResponse, StructuredRequirements, ArchitectureRecommendation, SecurityReview, DraftDocumentation

router = APIRouter()

@router.get("/history")
def list_history(db: Session = Depends(get_db)):
    """List all previously conducted analyses."""
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    results = []
    for a in analyses:
        intake = json.loads(a.intake_json) if a.intake_json else {}
        results.append({
            "session_id": a.id,
            "project_name": a.project_name,
            "domain": intake.get("domain", ""),
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "has_documents": len(a.documents) > 0,
        })
    return results

@router.get("/history/{analysis_id}", response_model=AnalysisResponse)
def get_history_detail(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve full analysis report by ID."""
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    out = a.outputs
    if not out:
        raise HTTPException(status_code=404, detail="Analysis output incomplete")

    reqs = StructuredRequirements.model_validate_json(out.requirements_json) if out.requirements_json else None
    arch = ArchitectureRecommendation.model_validate_json(out.architecture_json) if out.architecture_json else None
    sec = SecurityReview.model_validate_json(out.security_json) if out.security_json else None
    doc = DraftDocumentation.model_validate_json(out.documentation_json) if out.documentation_json else None

    return AnalysisResponse(
        session_id=a.id,
        project_name=a.project_name,
        status=a.status,
        requirements=reqs,
        architecture=arch,
        security=sec,
        documentation=doc,
        ai_provider_used=out.provider,
        created_at=a.created_at,
        elapsed_seconds=float(out.elapsed_seconds or 0),
    )

@router.get("/history/{analysis_id}/export/markdown")
def export_hld_markdown(analysis_id: str, db: Session = Depends(get_db)):
    """Export complete architecture analysis report across all 4 tabs as a downloadable Markdown file."""
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not a or not a.outputs:
        raise HTTPException(status_code=404, detail="Analysis not found")

    out = a.outputs
    reqs = StructuredRequirements.model_validate_json(out.requirements_json) if out.requirements_json else None
    arch = ArchitectureRecommendation.model_validate_json(out.architecture_json) if out.architecture_json else None
    sec_rev = SecurityReview.model_validate_json(out.security_json) if out.security_json else None
    doc = DraftDocumentation.model_validate_json(out.documentation_json) if out.documentation_json else None

    md_lines = [
        f"# Complete Solution Architecture Report: {a.project_name}",
        f"**Session ID**: `{a.id}` | **Status**: {a.status.capitalize()} | **AI Provider**: {out.provider}\n",
        "---",
        "\n# 1. Requirements Analysis",
    ]

    if reqs:
        md_lines.extend(["\n## Functional Requirements", "\n".join(f"- {f}" for f in reqs.functional)])
        md_lines.extend(["\n## Non-Functional Requirements", "\n".join(f"- {n}" for n in reqs.non_functional)])
        md_lines.extend(["\n## Constraints Summary", "\n".join(f"- {c}" for c in reqs.constraints_summary)])
        md_lines.extend(["\n## Assumptions & Domain Scope", "\n".join(f"- {asm}" for asm in reqs.assumptions)])
        md_lines.extend(["\n## Clarification Status & Open Questions", "\n".join(f"- {q}" for q in reqs.open_questions)])

    md_lines.append("\n---\n\n# 2. Architecture Recommendation")
    if arch:
        md_lines.append(f"\n### Architecture Pattern: {arch.pattern_name}")
        md_lines.append(f"**Rationale**: {arch.pattern_rationale}\n")
        md_lines.append("\n### Components")
        for c in arch.components:
            md_lines.append(f"- **{c.name}**: {c.purpose} ({c.technology or 'N/A'})")
        
        md_lines.append("\n### Integration Points")
        for ip in arch.integration_points:
            md_lines.append(f"- **{ip.source} -> {ip.target}** [{ip.protocol}]: {ip.description}")

        md_lines.append("\n### Trade-Offs")
        for t in arch.trade_offs:
            md_lines.append(f"- **Decision**: {t.decision} | **Benefit**: {t.benefit} | **Cost**: {t.cost}")

        if arch.mermaid_diagram:
            md_lines.append("\n### Architecture Diagram")
            md_lines.append(f"```mermaid\n{arch.mermaid_diagram}\n```")

    md_lines.append("\n---\n\n# 3. Security Review")
    if sec_rev:
        md_lines.append(f"\n**Overall Risk Level**: `{sec_rev.overall_risk.upper()}`\n")
        md_lines.append("\n### Findings")
        for f in sec_rev.findings:
            md_lines.append(f"- **[{f.severity.upper()}] {f.category}**: {f.description}")
            md_lines.append(f"  - *Remediation*: {f.remediation}")

        if sec_rev.recommendations:
            md_lines.extend(["\n### Security Recommendations", "\n".join(f"- {r}" for r in sec_rev.recommendations)])

    md_lines.append("\n---\n\n# 4. High-Level Design (HLD) Document")
    if doc:
        for section in sorted(doc.sections, key=lambda s: s.order):
            md_lines.append(f"\n## {section.heading}\n")
            md_lines.append(f"{section.content}\n")

    markdown_content = "\n".join(md_lines)
    filename = f"{a.project_name.lower().replace(' ', '_')}_full_report.md"

    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
