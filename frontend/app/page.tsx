'use client';

import { useState, useEffect } from 'react';
import { ChatSidebar } from '@/components/chat-sidebar';
import { ChatMessages } from '@/components/chat-messages';
import { ChatInput } from '@/components/chat-input';
import { useChat } from '@/hooks/use-chat';
import type { Document } from '@/lib/types';

export default function Home() {
  const chat = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile on mount
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleSendMessage = async (message: string) => {
    await chat.sendMessage(message);
  };

  const handleNewChat = () => {
    chat.clearMessages();
  };

  const handleCloseSidebar = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 dark">
      {/* Sidebar */}
      <ChatSidebar
        selectedDocuments={chat.selectedDocuments}
        onDocumentsChange={chat.setSelectedDocuments}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        onClose={handleCloseSidebar}
        onToggle={() => setSidebarOpen(o => !o)}
      />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Mobile Header */}
        {isMobile && !sidebarOpen && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900">
            <h1 className="font-semibold text-zinc-100">Chat</h1>
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-zinc-800 rounded transition-colors"
            >
              
            </button>
          </div>
        )}

       
        <div className="flex-1 overflow-y-auto px-3">
  <div className="max-w-4xl mx-auto">
    <ChatMessages messages={chat.messages} isLoading={chat.isLoading} />
  </div>
</div>

<div className="px-3 pb-4">
  <div className="max-w-4xl mx-auto">
    <ChatInput
      onSend={handleSendMessage}
      isLoading={chat.isLoading}
    />
  </div>
</div>
      </main>
    </div>
  );
}
