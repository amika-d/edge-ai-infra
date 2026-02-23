'use client';

import { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import { ChatSidebar } from '@/components/chat-sidebar';
import { ChatMessages } from '@/components/chat-messages';
import { ChatInput } from '@/components/chat-input';
import { useChat } from '@/hooks/use-chat';
import type { Document } from '@/lib/types';

export default function Home() {
  const chat = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
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
              <Menu className="w-5 h-5 text-zinc-400" />
            </button>
          </div>
        )}

        {/* Messages Area */}
        <ChatMessages messages={chat.messages} isLoading={chat.isLoading} />

        {/* Input Area */}
        <ChatInput
          onSend={handleSendMessage}
          isLoading={chat.isLoading}
          characterCount={0}
        />
      </main>
    </div>
  );
}
