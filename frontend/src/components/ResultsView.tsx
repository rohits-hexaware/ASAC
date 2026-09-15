import { useState } from 'react';
import {
  FileText,
  Building2,
  Shield,
  BookOpen,
  AlertCircle,
  Clock,
  Cpu,
  Download,
} from 'lucide-react';
import type { AnalysisResponse, ResultTab, RagSource } from '../types';
import ConfidenceBadge from './ConfidenceBadge';
import MermaidDiagram from './MermaidDiagram';
import ErrorBanner from './ErrorBanner';
import { getExportMarkdownUrl } from '../api/client';

interface Props {
  result: AnalysisResponse;
  onResume?: (sessionId: string) => void;
  isResuming?: boolean;
}

const TABS: { id: ResultTab; label: string; icon: typeof FileText }[] = [
  { id: 'requirements', label: 'Requirements', icon: FileText },
  { id: 'architecture', label: 'Architecture', icon: Building2 },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'documentation', label: 'Documentation', icon: BookOpen },
];

function ListSection({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function RagSourcesBlock({ sources }: { sources?: RagSource[] }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-6 pt-4 border-t border-gray-200">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">Grounding & RAG Sources</h4>
      <div className="space-y-2">
        {sources.map((s, i) => (
          <div key={i} className="text-xs p-2.5 bg-blue-50/60 rounded border border-blue-100 flex justify-between items-start">
            <div>
              <span className="font-semibold text-blue-900">{s.title}</span>
              {s.excerpt && <p className="text-gray-600 mt-0.5 line-clamp-2">{s.excerpt}</p>}
            </div>
            {s.score !== undefined && (
              <span className="bg-blue-100 text-blue-800 text-[10px] px-1.5 py-0.5 rounded font-mono ml-2 shrink-0">
                Score: {s.score.toFixed(2)}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ResultsView({ result, onResume, isResuming }: Props) {
  const [activeTab, setActiveTab] = useState<ResultTab>('requirements');

  const severityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-blue-100 text-blue-800',
    info: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="space-y-4">
      {/* Meta bar */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          {result.elapsed_seconds}s
        </span>
        <span className="flex items-center gap-1">
          <Cpu className="w-3.5 h-3.5" />
          AI: {result.ai_provider_used}
        </span>
        <span
          className={`px-2 py-0.5 rounded-full font-medium ${
            result.status === 'complete'
              ? 'bg-green-100 text-green-800'
              : result.status === 'partial'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}
        >
          {result.status}
        </span>
      </div>

      {(result.errors.length > 0 || result.status !== 'complete') && (
        <ErrorBanner
          variant="warning"
          message={
            result.errors.length > 0
              ? `Pipeline partial/incomplete: ${result.errors.map((e) => `${e.agent} agent failed`).join(', ')}`
              : 'Some analysis stages are pending completion.'
          }
          onAction={onResume ? () => onResume(result.session_id) : undefined}
          actionLabel={isResuming ? 'Resuming...' : 'Resume Analysis'}
        />
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-1 -mb-px">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === id
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="py-4">
        {activeTab === 'requirements' && result.requirements && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Structured Requirements</h3>
              <ConfidenceBadge level={result.requirements.confidence} />
            </div>
            <ListSection title="Functional Requirements" items={result.requirements.functional} />
            <ListSection title="Non-Functional Requirements" items={result.requirements.non_functional} />
            <ListSection title="Constraints Summary" items={result.requirements.constraints_summary} />
            <ListSection title="Assumptions & Domain Scope" items={result.requirements.assumptions} />
            <ListSection title="Clarification Status & Open Questions" items={result.requirements.open_questions} />
          </div>
        )}

        {activeTab === 'architecture' && result.architecture && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{result.architecture.pattern_name}</h3>
              <ConfidenceBadge level={result.architecture.confidence} />
            </div>
            <p className="text-sm text-gray-600 mb-6">{result.architecture.pattern_rationale}</p>

            <MermaidDiagram diagram={result.architecture.mermaid_diagram} className="mb-6" />

            {/* Requirement to Component Mapping */}
            {result.architecture.requirement_mappings && result.architecture.requirement_mappings.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Requirement-to-Component Mapping</h4>
                <div className="divide-y divide-gray-200 border border-gray-200 rounded-lg overflow-hidden text-xs">
                  {result.architecture.requirement_mappings.map((m, i) => (
                    <div key={i} className="p-2.5 bg-white flex justify-between items-center">
                      <span className="text-gray-700 font-medium">"{m.requirement}"</span>
                      <span className="bg-brand-50 text-brand-700 px-2 py-0.5 rounded font-mono font-semibold">
                        → {m.component}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <h4 className="text-sm font-semibold text-gray-700 mb-2">Components</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
              {result.architecture.components.map((c, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="font-medium text-sm">{c.name}</p>
                  <p className="text-xs text-gray-600 mt-1">{c.purpose}</p>
                  {c.technology && (
                    <p className="text-xs text-brand-600 mt-1">{c.technology}</p>
                  )}
                </div>
              ))}
            </div>

            {result.architecture.trade_offs.length > 0 && (
              <>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Trade-offs</h4>
                <div className="space-y-2 mb-6">
                  {result.architecture.trade_offs.map((t, i) => (
                    <div key={i} className="text-sm p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium">{t.decision}</p>
                      <p className="text-green-700 text-xs mt-1">+ {t.benefit}</p>
                      <p className="text-red-700 text-xs">- {t.cost}</p>
                    </div>
                  ))}
                </div>
              </>
            )}

            <RagSourcesBlock sources={result.architecture.rag_sources} />
          </div>
        )}

        {activeTab === 'security' && result.security && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Security Review</h3>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${severityColors[result.security.overall_risk]}`}
                >
                  {result.security.overall_risk} risk
                </span>
                <ConfidenceBadge level={result.security.confidence} />
              </div>
            </div>

            <h4 className="text-sm font-semibold text-gray-700 mb-2">Findings</h4>
            <div className="space-y-2 mb-6">
              {result.security.findings.map((f, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`px-1.5 py-0.5 rounded text-xs font-medium ${severityColors[f.severity]}`}
                    >
                      {f.severity}
                    </span>
                    <span className="text-sm font-medium">{f.category}</span>
                  </div>
                  <p className="text-sm text-gray-600">{f.description}</p>
                  <p className="text-xs text-brand-700 mt-1">
                    <AlertCircle className="w-3 h-3 inline mr-1" />
                    {f.remediation}
                  </p>
                </div>
              ))}
            </div>

            <ListSection title="Compliance Gaps" items={result.security.compliance_gaps} />
            <ListSection title="Recommendations" items={result.security.recommendations} />

            <h4 className="text-sm font-semibold text-gray-700 mb-2 mt-4">Checklist Coverage</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {Object.entries(result.security.checklist_coverage).map(([key, covered]) => (
                <div
                  key={key}
                  className={`text-xs p-2 rounded text-center ${
                    covered ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                  }`}
                >
                  {key.replace(/_/g, ' ')}
                </div>
              ))}
            </div>

            <RagSourcesBlock sources={result.security.rag_sources} />
          </div>
        )}

        {activeTab === 'documentation' && result.documentation && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">{result.documentation.title}</h3>
                <p className="text-xs text-gray-500">{result.documentation.document_type}</p>
              </div>
              <a
                href={getExportMarkdownUrl(result.session_id)}
                download
                className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white text-xs font-medium rounded-md hover:bg-brand-700 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Export HLD Markdown
              </a>
            </div>

            <div className="space-y-6">
              {result.documentation.sections
                .sort((a, b) => a.order - b.order)
                .map((section, i) => (
                  <div key={i}>
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">
                      {section.heading}
                    </h4>
                    <div className="text-sm text-gray-600 whitespace-pre-wrap prose prose-sm max-w-none">
                      {section.content}
                    </div>
                  </div>
                ))}
            </div>

            <RagSourcesBlock sources={result.documentation.rag_sources} />
          </div>
        )}
      </div>
    </div>
  );
}
