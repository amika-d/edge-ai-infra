'use client';

import React, { useState } from 'react';
import { Plus, Menu, X } from 'lucide-react';
import { DocumentSelector } from './document-selector';
import type { Document } from '@/lib/types';

interface ChatSidebarProps {
  selectedDocuments: Document[];
  onDocumentsChange: (documents: Document[]) => void;
  onNewChat: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

interface Conversation {
  id: string;
  title: string;
  timestamp: Date;
}

export function ChatSidebar({
  selectedDocuments,
  onDocumentsChange,
  onNewChat,
  isOpen = true,
  onClose,
}: ChatSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'API Integration Questions',
      timestamp: new Date(Date.now() - 86400000),
    },
    {
      id: '2',
      title: 'Database Design Discussion',
      timestamp: new Date(Date.now() - 172800000),
    },
    {
      id: '3',
      title: 'Performance Optimization',
      timestamp: new Date(Date.now() - 259200000),
    },
  ]);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative inset-y-0 left-0 w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col transition-transform duration-300 md:translate-x-0 z-40 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <h1 className="text-lg font-bold text-zinc-100">Chat</h1>
          <button
            onClick={onClose}
            className="md:hidden p-1.5 hover:bg-zinc-900 rounded transition-colors"
          >
            <X className="w-5 h-5 text-zinc-400" />
          </button>
        </div>

        {/* New Chat Button */}
        <button
  onClick={onNewChat}
  className="mx-4 mt-4 mb-2 flex items-center justify-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors font-medium"
>
  <Plus className="w-4 h-4" />
  New Chat
</button>

        {/* Document Selector */}
        <div className="px-4 py-3 border-b border-zinc-800">
          <DocumentSelector
            selectedDocuments={selectedDocuments}
            onDocumentsChange={onDocumentsChange}
          />
        </div>

        {/* Conversations */}
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-xs font-semibold text-zinc-500 uppercase mb-3">
            Conversations
          </h2>
          <div className="space-y-2">
            {conversations.map(conv => (
              <button
                key={conv.id}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-900 transition-colors group"
              >
                <p className="text-sm text-zinc-300 group-hover:text-zinc-100 truncate">
                  {conv.title}
                </p>
                <p className="text-xs text-zinc-600 mt-1">
                  {conv.timestamp.toLocaleDateString()}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900">
          <p className="text-xs text-zinc-500 mb-2">Session Info</p>
          <div className="text-xs text-zinc-600 space-y-1">
            <p>Messages: 0</p>
            <p>Documents: {selectedDocuments.length}</p>
          </div>
        </div>
      </aside>

      {/* Mobile Menu Button */}
      {!isOpen && (
        <button
          onClick={() => {}}
          className="md:hidden fixed bottom-20 right-4 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg"
        >
          <Menu className="w-5 h-5" />
        </button>
      )}
    </>
  );
}
