import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, FileCheck, ArrowRight, Edit2, Plus } from 'lucide-react';
import type { DiscoveredRequirements, DiscoveredRequirementItem, ValidatedRequirementsContext } from '../types';

interface Props {
  discovered: DiscoveredRequirements;
  onConfirm: (validatedContext: ValidatedRequirementsContext) => void;
  onCancel: () => void;
  loading: boolean;
}

export default function RequirementsConfirmationView({
  discovered,
  onConfirm,
  onCancel,
  loading,
}: Props) {
  const [items, setItems] = useState<DiscoveredRequirementItem[]>(
    discovered.suggested_derived_requirements
  );
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState<string>('');
  const [newRequirementText, setNewRequirementText] = useState<string>('');

  const [clarifications, setClarifications] = useState<Record<string, string>>({});

  const toggleStatus = (id: string, status: 'accepted' | 'rejected') => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status } : item))
    );
  };

  const startEdit = (item: DiscoveredRequirementItem) => {
    setEditingId(item.id);
    setEditingText(item.text);
  };

  const saveEdit = (id: string) => {
    if (!editingText.trim()) return;
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, text: editingText.trim() } : item))
    );
    setEditingId(null);
  };

  const addCustomDerivedRequirement = () => {
    if (!newRequirementText.trim()) return;
    const newItem: DiscoveredRequirementItem = {
      id: `CUSTOM-${Date.now()}`,
      text: newRequirementText.trim(),
      category: 'User Added',
      status: 'accepted',
    };
    setItems((prev) => [...prev, newItem]);
    setNewRequirementText('');
  };

  const handleClarificationChange = (question: string, answer: string) => {
    setClarifications((prev) => ({ ...prev, [question]: answer }));
  };

  const handleConfirm = () => {
    const acceptedDerived = items
      .filter((i) => i.status === 'accepted' || i.status === 'pending')
      .map((i) => i.text);

    const rejectedDerived = items
      .filter((i) => i.status === 'rejected')
      .map((i) => i.text);

    const context: ValidatedRequirementsContext = {
      explicit_requirements: discovered.explicit_requirements,
      confirmed_derived_requirements: acceptedDerived,
      rejected_suggestions: rejectedDerived,
      constraints: discovered.constraints_summary,
      assumptions: discovered.assumptions,
      open_questions: discovered.needs_clarification,
      user_clarifications: clarifications,
    };

    onConfirm(context);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <FileCheck className="w-6 h-6 text-brand-600" />
            <h2 className="text-xl font-bold text-gray-900">
              Requirements Discovery & Review
            </h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Review the baseline requirements inferred by the Solution Architect. Accept, reject, or edit capabilities before starting architecture generation.
          </p>
        </div>
        <span className="px-3 py-1 bg-brand-50 text-brand-700 text-xs font-semibold rounded-full border border-brand-200">
          Step 2 of 2: Confirmation
        </span>
      </div>

      {/* 1. Confirmed from Input */}
      <div className="bg-emerald-50/50 border border-emerald-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-emerald-900 flex items-center gap-2 mb-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          Confirmed from Your Input (Explicit Requirements)
        </h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          {discovered.explicit_requirements.map((req, i) => (
            <li key={i}>{req}</li>
          ))}
        </ul>
      </div>

      {/* 2. Suggested / Derived Capabilities */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900">
            Suggested / Derived Technical Capabilities
          </h3>
          <span className="text-xs text-gray-500">
            Click Accept or Reject for each architectural capability
          </span>
        </div>

        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className={`p-3 rounded-lg border flex items-center justify-between gap-3 transition-colors ${
                item.status === 'rejected'
                  ? 'bg-red-50/50 border-red-200 opacity-65'
                  : item.status === 'accepted'
                    ? 'bg-blue-50/40 border-blue-200'
                    : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex-1 min-w-0">
                {editingId === item.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                      className="flex-1 text-sm border border-brand-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                    <button
                      onClick={() => saveEdit(item.id)}
                      className="text-xs bg-brand-600 text-white px-2.5 py-1 rounded hover:bg-brand-700"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-200/80 font-medium text-gray-700 shrink-0">
                      {item.category}
                    </span>
                    <span className="text-sm text-gray-800 truncate">{item.text}</span>
                    <button
                      onClick={() => startEdit(item)}
                      className="text-gray-400 hover:text-gray-600 p-1"
                      title="Edit requirement text"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => toggleStatus(item.id, 'accepted')}
                  className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                    item.status === 'accepted'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-emerald-100 hover:text-emerald-800'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Accept
                </button>
                <button
                  onClick={() => toggleStatus(item.id, 'rejected')}
                  className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                    item.status === 'rejected'
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-red-100 hover:text-red-800'
                  }`}
                >
                  <XCircle className="w-3.5 h-3.5" />
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add custom derived requirement */}
        <div className="flex items-center gap-2 pt-2">
          <input
            type="text"
            placeholder="Add custom capability requirement..."
            value={newRequirementText}
            onChange={(e) => setNewRequirementText(e.target.value)}
            className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="button"
            onClick={addCustomDerivedRequirement}
            className="flex items-center gap-1 text-xs bg-gray-800 text-white px-3 py-2 rounded-lg hover:bg-gray-900 transition-colors shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Capability
          </button>
        </div>
      </div>

      {/* 3. Needs Clarification */}
      {discovered.needs_clarification.length > 0 && (
        <div className="bg-amber-50/50 border border-amber-200 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-amber-900 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-amber-600" />
            Needs Clarification (Optional Input)
          </h3>
          <p className="text-xs text-amber-800">
            Answering these helps refine the architecture. Unanswered items will remain marked as TBD/Needs Validation.
          </p>
          <div className="space-y-3">
            {discovered.needs_clarification.map((question, i) => (
              <div key={i} className="space-y-1">
                <label className="text-xs font-medium text-gray-700 block">
                  {question}
                </label>
                <input
                  type="text"
                  placeholder="Type answer or leave blank for TBD..."
                  value={clarifications[question] || ''}
                  onChange={(e) => handleClarificationChange(question, e.target.value)}
                  className="w-full text-xs border border-gray-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-white"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer Actions */}
      <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-gray-600 hover:text-gray-900 font-medium px-3 py-2"
        >
          Cancel & Edit Form
        </button>

        <button
          type="button"
          disabled={loading}
          onClick={handleConfirm}
          className="flex items-center gap-2 bg-brand-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {loading ? 'Generating Architecture...' : 'Confirm Requirements & Continue'}
          {!loading && <ArrowRight className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}
