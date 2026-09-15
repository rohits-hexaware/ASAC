export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface ConstraintsInput {
  cloud?: string;
  budget?: string;
  timeline?: string;
}

export interface AnalyzeRequest {
  project_name: string;
  domain: string;
  business_goals: string;
  functional_requirements: string;
  constraints: ConstraintsInput;
  non_functional_requirements: string;
  compliance: string;
}

export interface DiscoveredRequirementItem {
  id: string;
  text: string;
  category: string;
  status: 'accepted' | 'rejected' | 'pending';
}

export interface DiscoveredRequirements {
  session_id: string;
  project_name: string;
  domain: string;
  explicit_requirements: string[];
  suggested_derived_requirements: DiscoveredRequirementItem[];
  needs_clarification: string[];
  constraints_summary: string[];
  assumptions: string[];
  confidence: ConfidenceLevel;
}

export interface ValidatedRequirementsContext {
  explicit_requirements: string[];
  confirmed_derived_requirements: string[];
  rejected_suggestions: string[];
  constraints: string[];
  assumptions: string[];
  open_questions: string[];
  user_clarifications: Record<string, string>;
}

export interface ConfirmRequirementsRequest {
  session_id: string;
  intake: AnalyzeRequest;
  validated_context: ValidatedRequirementsContext;
}

export interface StructuredRequirements {
  functional: string[];
  non_functional: string[];
  constraints_summary: string[];
  assumptions: string[];
  open_questions: string[];
  confidence: ConfidenceLevel;
  validated_context?: ValidatedRequirementsContext;
}

export interface ArchitectureComponent {
  name: string;
  purpose: string;
  technology?: string;
}

export interface IntegrationPoint {
  source: string;
  target: string;
  protocol: string;
  description: string;
}

export interface TradeOff {
  decision: string;
  benefit: string;
  cost: string;
}

export interface AlternativeConsidered {
  name: string;
  reason_rejected: string;
}

export interface RagSource {
  title: string;
  path: string;
  excerpt: string;
  score?: number;
}

export interface RequirementMapping {
  requirement: string;
  component: string;
}

export interface ArchitectureRecommendation {
  pattern_name: string;
  pattern_rationale: string;
  components: ArchitectureComponent[];
  integration_points: IntegrationPoint[];
  requirement_mappings?: RequirementMapping[];
  trade_offs: TradeOff[];
  alternatives_considered: AlternativeConsidered[];
  mermaid_diagram: string;
  rag_sources: RagSource[];
  confidence: ConfidenceLevel;
}

export interface SecurityFinding {
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  description: string;
  remediation: string;
}

export interface SecurityReview {
  overall_risk: 'critical' | 'high' | 'medium' | 'low';
  findings: SecurityFinding[];
  compliance_gaps: string[];
  recommendations: string[];
  checklist_coverage: Record<string, boolean>;
  rag_sources?: RagSource[];
  confidence: ConfidenceLevel;
}

export interface DocumentSection {
  heading: string;
  content: string;
  order: number;
}

export interface DraftDocumentation {
  document_type: string;
  title: string;
  sections: DocumentSection[];
  metadata: Record<string, unknown>;
  export_formats: string[];
  rag_sources?: RagSource[];
}

export interface HistoryItem {
  session_id: string;
  project_name: string;
  domain: string;
  status: string;
  created_at: string;
  has_documents: boolean;
}


export interface AgentError {
  agent: string;
  error: string;
}

export interface AnalysisResponse {
  session_id: string;
  project_name: string;
  status: 'complete' | 'partial' | 'failed';
  requirements: StructuredRequirements | null;
  architecture: ArchitectureRecommendation | null;
  security: SecurityReview | null;
  documentation: DraftDocumentation | null;
  errors: AgentError[];
  ai_provider_used: string;
  rag_available: boolean;
  elapsed_seconds: number;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  messages: ChatMessage[];
  ai_provider_used: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  ai_providers: Record<string, string>;
  rag: { available: boolean; document_count: number };
  sessions_active: number;
}

export type ResultTab = 'requirements' | 'architecture' | 'security' | 'documentation';
