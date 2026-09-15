import { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import { useChat } from '../hooks/useChat';

interface Props {
  sessionId: string | null;
}

function FormattedChatMessage({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inTable = false;
  let tableHeader: string[] = [];
  let tableRows: string[][] = [];

  const flushTable = (keyPrefix: string) => {
    if (tableHeader.length > 0) {
      elements.push(
        <div key={`table-${keyPrefix}`} className="my-2 overflow-x-auto border border-gray-300 rounded">
          <table className="min-w-full text-xs text-left divide-y divide-gray-200">
            <thead className="bg-gray-200/80 font-semibold">
              <tr>
                {tableHeader.map((th, i) => (
                  <th key={i} className="px-2 py-1 border-r border-gray-300 last:border-r-0">{th.trim()}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {tableRows.map((row, ri) => (
                <tr key={ri} className="hover:bg-gray-50">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-2 py-1 border-r border-gray-200 last:border-r-0">{cell.trim()}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    tableHeader = [];
    tableRows = [];
    inTable = false;
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const cells = trimmed.split('|').slice(1, -1);
      if (trimmed.replace(/[\s|:-]/g, '').length === 0) {
        // Separator line e.g. |---|---|
        return;
      }
      if (!inTable) {
        inTable = true;
        tableHeader = cells;
      } else {
        tableRows.push(cells);
      }
    } else {
      if (inTable) {
        flushTable(`${index}`);
      }
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        elements.push(
          <li key={index} className="ml-4 list-disc text-xs my-0.5">
            {trimmed.substring(2)}
          </li>
        );
      } else if (trimmed.length > 0) {
        elements.push(
          <p key={index} className="text-xs my-1 leading-relaxed">
            {trimmed}
          </p>
        );
      }
    }
  });

  if (inTable) {
    flushTable('end');
  }

  return <div className="space-y-0.5">{elements}</div>;
}

export default function ChatPanel({ sessionId }: Props) {
  const [input, setInput] = useState('');
  const { messages, loading, fetchingHistory, error, sendMessage } = useChat(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput('');
  };

  if (!sessionId) {
    return (
      <div className="flex flex-col h-full bg-white border-l border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-brand-600" />
          <h3 className="font-semibold text-gray-900">Architect Chat</h3>
        </div>
        <p className="text-sm text-gray-500">Run an analysis to start chatting.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 w-full bg-white border-l border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 p-4 border-b border-gray-200 shrink-0">
        <Sparkles className="w-5 h-5 text-brand-600" />
        <h3 className="font-semibold text-gray-900">Architect Chat</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {fetchingHistory && (
          <div className="flex justify-center items-center py-8 text-gray-400 gap-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading conversation history...</span>
          </div>
        )}
        {!fetchingHistory && messages.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-8">
            Ask follow-up questions about the architecture results.
          </p>
        )}
        {!fetchingHistory && messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[90%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <FormattedChatMessage content={msg.content} />
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="px-4 pb-2">
          <p className="text-xs text-red-600">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the architecture..."
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
