import { useState } from 'react';
import type { AnalyzeRequest } from '../types';
import { SAMPLE_SCENARIO } from '../data/sampleScenario';

interface Props {
  onSubmit: (request: AnalyzeRequest, files: File[]) => void;
  loading: boolean;
}

const EMPTY_FORM: AnalyzeRequest = {
  project_name: '',
  domain: '',
  business_goals: '',
  functional_requirements: '',
  constraints: {
    cloud: '',
    budget: '',
    timeline: '',
  },
  non_functional_requirements: '',
  compliance: '',
};

export default function RequirementsForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<AnalyzeRequest>(EMPTY_FORM);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);

  const update = (field: keyof AnalyzeRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const updateConstraint = (field: keyof AnalyzeRequest['constraints'], value: string) => {
    setForm((prev) => ({
      ...prev,
      constraints: { ...prev.constraints, [field]: value },
    }));
  };

  const loadSample = () => {
    setForm(SAMPLE_SCENARIO);
    setSelectedFiles([]);
    setFileError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);
    
    if (files.length > 2) {
      setFileError('Maximum 2 reference documents allowed.');
      return;
    }

    for (const f of files) {
      if (f.size > 2 * 1024 * 1024) {
        setFileError(`File "${f.name}" exceeds maximum allowed size of 2MB.`);
        return;
      }
    }

    setFileError(null);
    setSelectedFiles(files);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (fileError) return;

    if (
      !form.project_name.trim() ||
      !form.domain.trim() ||
      !form.business_goals.trim() ||
      !form.functional_requirements.trim()
    ) {
      alert('Please fill out all required fields marked with *');
      return;
    }

    onSubmit(form, selectedFiles);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Project Intake & Reference Documents</h2>
          <p className="text-sm text-gray-600 mt-1">
            Describe your project requirements or load sample test data for AI-powered architecture analysis.
          </p>
        </div>
        <button
          type="button"
          onClick={loadSample}
          className="text-sm text-brand-600 hover:text-brand-700 font-medium border border-brand-200 px-3 py-1.5 rounded-lg bg-brand-50/50"
        >
          Load test data
        </button>
      </div>

      {/* File Upload Section */}
      <div className="border border-dashed border-gray-300 rounded-lg p-4 bg-gray-50">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Attach Reference Documents (Optional - Max 2 files, 2MB each: PDF, DOCX, TXT, MD)
        </label>
        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.md"
          multiple
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
        />
        {fileError && <p className="text-xs text-red-600 mt-1">{fileError}</p>}

        {selectedFiles.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedFiles.map((file, idx) => (
              <div key={idx} className="flex items-center space-x-2 bg-white border border-gray-200 px-3 py-1 rounded-md text-xs font-medium text-gray-700">
                <span>📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                <button
                  type="button"
                  onClick={() => removeFile(idx)}
                  className="text-red-500 hover:text-red-700 font-bold"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Project Name *
          </label>
          <input
            type="text"
            required
            value={form.project_name}
            onChange={(e) => update('project_name', e.target.value)}
            placeholder="e.g. Enterprise Chat App"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Domain *</label>
          <input
            type="text"
            required
            value={form.domain}
            onChange={(e) => update('domain', e.target.value)}
            placeholder="e.g. Healthcare / Real-Time Messaging"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Business Goals *
        </label>
        <textarea
          required
          rows={3}
          value={form.business_goals}
          onChange={(e) => update('business_goals', e.target.value)}
          placeholder="Describe primary business objectives and ROI targets..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Functional Requirements *
        </label>
        <textarea
          required
          rows={5}
          value={form.functional_requirements}
          onChange={(e) => update('functional_requirements', e.target.value)}
          placeholder="List key functional requirements (one per line)..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm font-mono"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cloud</label>
          <input
            type="text"
            value={form.constraints.cloud || ''}
            onChange={(e) => updateConstraint('cloud', e.target.value)}
            placeholder="e.g. AWS / Azure / GCP"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Budget</label>
          <input
            type="text"
            value={form.constraints.budget || ''}
            onChange={(e) => updateConstraint('budget', e.target.value)}
            placeholder="e.g. $500K"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Timeline</label>
          <input
            type="text"
            value={form.constraints.timeline || ''}
            onChange={(e) => updateConstraint('timeline', e.target.value)}
            placeholder="e.g. 6 Months"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Non-Functional Requirements
        </label>
        <textarea
          rows={4}
          value={form.non_functional_requirements}
          onChange={(e) => update('non_functional_requirements', e.target.value)}
          placeholder="e.g. 99.99% Availability, Latency < 100ms"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm font-mono"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Compliance</label>
        <input
          type="text"
          value={form.compliance}
          onChange={(e) => update('compliance', e.target.value)}
          placeholder="e.g. HIPAA, GDPR, SOC2"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm"
        />
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={loading || !!fileError}
          className="px-6 py-2.5 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>
    </form>
  );
}
