'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  characterCount?: number;
}

export function ChatInput({ onSend, isLoading, characterCount = 0 }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSend(message);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-zinc-800 bg-zinc-950 p-3 sm:p-4">
      <div className="space-y-2 sm:space-y-3">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something... (Shift+Enter for new line)"
            className="w-full resize-none px-3 sm:px-4 py-2 sm:py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-sm sm:text-base text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 transition-colors focus:ring-1 focus:ring-blue-500/20 max-h-24"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="absolute right-2 sm:right-3 bottom-2 sm:bottom-3 p-1.5 sm:p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="hidden sm:flex items-center justify-between text-xs">
          <span className="text-zinc-500">
            {message.length > 0 && `${message.length} characters`}
          </span>
          <span className="text-zinc-600">
            Press Shift+Enter for new line
          </span>
        </div>
      </div>
    </div>
  );
}
