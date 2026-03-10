'use client';

import React, { useState, useRef } from 'react';
import { ArrowUp } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className="fixed bottom-4 left-0 right-0 px-4 pointer-events-none">
      <div className="mx-auto max-w-2xl pointer-events-auto">
        <div className="backdrop-blur-xl bg-black/30 border border-white/10 rounded-2xl shadow-2xl shadow-black/50">
          <form onSubmit={handleSubmit} className="flex items-end gap-3 p-3">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={e => setMessage(e.target.value)}
              onInput={e => {
                const t = e.target as HTMLTextAreaElement;
                t.style.height = 'auto';
                t.style.height = Math.min(t.scrollHeight, 128) + 'px';
              }}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Ask anything..."
              rows={1}
              disabled={isLoading}
              className="min-h-10 flex-1 bg-white/5 border border-white/10 text-zinc-100 placeholder-zinc-400 resize-none focus-visible:ring-1 focus-visible:ring-white/20 focus-visible:border-white/20 rounded-xl transition-all duration-200 hover:bg-white/10"
            />
            <Button
              type="submit"
              disabled={!message.trim() || isLoading}
              className="h-10 w-10 p-0 shrink-0 bg-white/5 border border-white/20 hover:bg-white/20 disabled:opacity-30 transition-all duration-200 rounded-xl"
            >
              <ArrowUp className="w-4 h-4 text-zinc-300" />
            </Button>
          </form>
          <p className="text-center text-[10px] text-white/40 pb-2">
            AI can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </div>
  );
}
