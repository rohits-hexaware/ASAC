import { useEffect, useState } from 'react';
import { History, Clock, FileText, X } from 'lucide-react';
import type { HistoryItem } from '../types';
import { fetchHistory } from '../api/client';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectAnalysis: (sessionId: string) => void;
}

export default function HistoryDrawer({ isOpen, onClose, onSelectAnalysis }: Props) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchHistory()
        .then(setHistory)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-gray-900">Saved Analysis Reports</h3>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <p className="text-sm text-gray-500 text-center py-8">Loading saved reports...</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No saved analysis reports found.</p>
          ) : (
            history.map((item) => (
              <div
                key={item.session_id}
                onClick={() => {
                  onSelectAnalysis(item.session_id);
                  onClose();
                }}
                className="p-3 bg-white border border-gray-200 rounded-xl hover:border-brand-500 hover:shadow-md cursor-pointer transition-all space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm text-gray-900">{item.project_name}</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-800 font-medium capitalize">
                    {item.status}
                  </span>
                </div>

                <p className="text-xs text-gray-600">Domain: {item.domain || 'N/A'}</p>

                <div className="flex items-center justify-between text-[11px] text-gray-400 pt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                  {item.has_documents && (
                    <span className="flex items-center gap-1 text-brand-600 font-medium">
                      <FileText className="w-3 h-3" /> Reference Docs Attached
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
