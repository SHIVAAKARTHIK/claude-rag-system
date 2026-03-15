'use client';

import { useState } from 'react';
import type { Sources } from '@/types';
import SourcesSection from './SourcesSection';

interface AIMessageProps {
  text: string;
  sources?: Sources;
  streaming?: boolean;
}

export default function AIMessage({ text, sources, streaming }: AIMessageProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex justify-start px-4 py-2">
      <div className="max-w-[80%] bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm px-4 py-3 space-y-2">
        {/* Loading skeleton */}
        {streaming && !text && (
          <div className="space-y-2 animate-pulse">
            <div className="h-3 bg-gray-200 rounded w-3/4" />
            <div className="h-3 bg-gray-200 rounded w-1/2" />
            <div className="h-3 bg-gray-200 rounded w-5/6" />
          </div>
        )}

        {/* Streaming text with cursor */}
        {text && (
          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
            {text}
            {streaming && <span className="inline-block w-0.5 h-4 bg-gray-600 ml-0.5 animate-pulse align-middle" />}
          </p>
        )}

        {/* Actions — only when done */}
        {!streaming && text && (
          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={handleCopy}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
        )}

        {/* Sources */}
        {!streaming && sources && <SourcesSection sources={sources} />}
      </div>
    </div>
  );
}
