'use client';

import React, { useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';
import { MarkdownRenderer } from './markdown-renderer';
import { CitationsPanel } from './citations-panel';
import type { Message } from '@/lib/types';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Bot className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-zinc-300 mb-2">Start a conversation</h2>
            <p className="text-sm text-zinc-500">Ask me anything about your documents</p>
          </div>
        </div>
      )}

      {messages.map(message => (
        <div
          key={message.id}
          className={`flex gap-2 sm:gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'} px-2 sm:px-4`}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center mt-1">
              <Bot className="w-3 h-3 sm:w-4 sm:h-4 text-zinc-400" />
            </div>
          )}

          <div
            className={`max-w-xs sm:max-w-md lg:max-w-2xl px-3 sm:px-4 py-2 sm:py-3 rounded-lg text-sm sm:text-base ${
              message.role === 'user'
                ? 'bg-zinc-800 text-zinc-100 rounded-br-none'
                : 'bg-zinc-900 text-zinc-100 border border-zinc-800 rounded-bl-none'
            }`}
          >
            <MarkdownRenderer content={message.content} />

            {message.role === 'assistant' && message.citations && message.citations.length > 0 && (
              <div className="mt-3 pt-3">
                <CitationsPanel citations={message.citations} />
              </div>
            )}
          </div>

          {message.role === 'user' && (
            <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center mt-1">
              <User className="w-3 h-3 sm:w-4 sm:h-4 text-zinc-400" />
            </div>
          )}
        </div>
      ))}

      {isLoading && (
        <div className="flex gap-2 sm:gap-3 px-2 sm:px-4">
          <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center mt-1">
            <Bot className="w-3 h-3 sm:w-4 sm:h-4 text-zinc-400" />
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg rounded-bl-none px-3 sm:px-4 py-2 sm:py-3">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
