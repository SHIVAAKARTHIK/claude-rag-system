'use client';

import { useEffect, useRef } from 'react';
import type { Message } from '@/types';
import UserMessage from './UserMessage';
import AIMessage from './AIMessage';

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 space-y-4 text-gray-500">
      <div className="space-y-2 text-lg">
        <p>📁 Upload files in the sidebar to index them</p>
        <p>🖼 Attach an image in chat to find similar content</p>
        <p>💬 Ask questions and get answers with sources</p>
      </div>
    </div>
  );
}

interface ChatThreadProps {
  messages: Message[];
  className?: string;
}

export default function ChatThread({ messages, className }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={`flex flex-col ${className ?? ''}`}>
      {messages.length === 0 ? (
        <WelcomeScreen />
      ) : (
        <div className="py-4 space-y-1">
          {messages.map(msg =>
            msg.role === 'user' ? (
              <UserMessage key={msg.id} text={msg.text} queryImage={msg.queryImage} />
            ) : (
              <AIMessage
                key={msg.id}
                text={msg.text}
                sources={msg.sources}
                streaming={msg.streaming}
              />
            )
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
