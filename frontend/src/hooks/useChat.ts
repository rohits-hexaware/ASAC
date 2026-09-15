import { useCallback, useEffect, useState } from 'react';
import { sendChatMessage, fetchChatHistory } from '../api/client';
import type { ChatMessage } from '../types';

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      setFetchingHistory(true);
      fetchChatHistory(sessionId)
        .then((msgs) => {
          setMessages(msgs || []);
        })
        .catch(() => setMessages([]))
        .finally(() => setFetchingHistory(false));
    } else {
      setMessages([]);
      setFetchingHistory(false);
    }
  }, [sessionId]);


  const sendMessage = useCallback(
    async (text: string) => {
      if (!sessionId || !text.trim()) return;

      setLoading(true);
      setError(null);

      const optimistic: ChatMessage = {
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimistic]);

      try {
        const response = await sendChatMessage(sessionId, text);
        setMessages(response.messages);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to send message.';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  return { messages, loading, fetchingHistory, error, sendMessage };
}


