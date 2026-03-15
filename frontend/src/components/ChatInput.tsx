'use client';

import { useRef, useState, type KeyboardEvent, type ChangeEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string, queryImage?: File) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState('');
  const [queryImage, setQueryImage] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (disabled || !text.trim()) return;
    onSend(text.trim(), queryImage ?? undefined);
    setText('');
    setQueryImage(null);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setQueryImage(file);
    e.target.value = '';
  };

  return (
    <div className="border-t bg-white px-4 py-3">
      {/* Query image preview */}
      {queryImage && (
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center gap-1 bg-blue-50 border border-blue-200 text-blue-700 text-xs px-3 py-1 rounded-full">
            🖼 {queryImage.name}
            <button
              onClick={() => setQueryImage(null)}
              className="ml-1 text-blue-400 hover:text-blue-700 leading-none"
              aria-label="Remove image"
            >
              ×
            </button>
          </span>
          <span className="text-xs text-gray-400">Visual search</span>
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2">
        {/* Attach image for visual search */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-40 transition-colors flex-shrink-0"
          aria-label="Attach image for visual search"
          title="Attach image to find similar content"
        >
          🖼
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handleImageChange}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={queryImage ? 'Find images/videos similar to this...' : 'Type a message...'}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400 placeholder-gray-400 overflow-hidden"
          style={{ maxHeight: '200px' }}
        />

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="flex-shrink-0 bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send ▶
        </button>
      </div>
    </div>
  );
}
