'use client';

import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Message, Sources } from '@/types';
import { streamChat } from '@/lib/api';

interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (text: string, queryImage?: File) => Promise<void>;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (text: string, queryImage?: File) => {
    // Add user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      text,
      queryImage: queryImage ? { name: queryImage.name } : undefined,
    };
    setMessages(prev => [...prev, userMsg]);

    // Add empty AI message (streaming placeholder)
    const aiMsgId = crypto.randomUUID();
    const aiMsg: Message = { id: aiMsgId, role: 'assistant', text: '', streaming: true };
    setMessages(prev => [...prev, aiMsg]);
    setIsLoading(true);

    try {
      for await (const event of streamChat(text, queryImage)) {
        if (event.type === 'text_chunk') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId ? { ...m, text: m.text + event.content } : m
          ));
        } else if (event.type === 'sources') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId ? { ...m, sources: event.data as Sources, streaming: false } : m
          ));
        } else if (event.type === 'error') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { ...m, text: m.text || `Error: ${event.message}`, streaming: false }
              : m
          ));
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Something went wrong';
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? { ...m, text: `Error: ${msg}`, streaming: false } : m
      ));
    } finally {
      setIsLoading(false);
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? { ...m, streaming: false } : m
      ));
    }
  };

  const clearChat = () => setMessages([]);

  return (
    <ChatContext.Provider value={{ messages, isLoading, sendMessage, clearChat }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}
