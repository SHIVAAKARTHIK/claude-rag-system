'use client';

import { useChat } from '@/contexts/ChatContext';
import ChatPanel from '@/components/ChatPanel';
import UploadSidebar from '@/components/UploadSidebar';

export default function MainPage() {
  const { messages, clearChat } = useChat();

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 h-14 flex items-center justify-between flex-shrink-0">
        <span className="font-semibold text-gray-900 tracking-tight">Multimodal RAG</span>
        <button
          onClick={clearChat}
          disabled={messages.length === 0}
          className="text-sm text-gray-500 hover:text-gray-800 disabled:opacity-30 transition-colors"
        >
          Clear Chat
        </button>
      </header>

      {/* Body: chat panel + upload sidebar */}
      <div className="flex flex-1 overflow-hidden">
        <ChatPanel />
        <UploadSidebar />
      </div>
    </div>
  );
}
