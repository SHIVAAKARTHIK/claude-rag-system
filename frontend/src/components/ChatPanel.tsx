'use client';

import { useChat } from '@/contexts/ChatContext';
import ChatThread from './ChatThread';
import ChatInput from './ChatInput';

export default function ChatPanel() {
  const { messages, isLoading, sendMessage } = useChat();

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      <ChatThread messages={messages} className="flex-1 overflow-y-auto" />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
