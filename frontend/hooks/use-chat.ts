import { useState, useCallback } from 'react';
import type { Message, Document, ChatState, ApiResponse } from '@/lib/types';

const generateId = () => Math.random().toString(36).substr(2, 9);

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    activeDocumentId: null,
    selectedDocuments: [],
  });

  const addMessage = useCallback((role: 'user' | 'assistant', content: string, citations?: any[]) => {
    const message: Message = {
      id: generateId(),
      role,
      content,
      citations,
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
    }));

    return message;
  }, []);

  const sendMessage = useCallback(async (userMessage: string) => {
    addMessage('user', userMessage);
    setState(prev => ({ ...prev, isLoading: true, error: undefined }));

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          documentIds: state.selectedDocuments.map(d => d.id),
          conversationHistory: state.messages,
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data: ApiResponse = await response.json();
      addMessage('assistant', data.message, data.citations);
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'An error occurred',
      }));
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.messages, state.selectedDocuments, addMessage]);

  const setSelectedDocuments = useCallback((documents: Document[]) => {
    setState(prev => ({ ...prev, selectedDocuments: documents }));
  }, []);

  const clearMessages = useCallback(() => {
    setState(prev => ({ ...prev, messages: [] }));
  }, []);

  return {
    ...state,
    sendMessage,
    addMessage,
    setSelectedDocuments,
    clearMessages,
  };
}
