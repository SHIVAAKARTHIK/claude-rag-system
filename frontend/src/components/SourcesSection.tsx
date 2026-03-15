'use client';

import { useState } from 'react';
import type { Sources, ImageSource, VideoSource, DocumentSource } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function formatTimestamp(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function ImageCard({ source }: { source: ImageSource }) {
  const [expanded, setExpanded] = useState(false);
  // thumbnail_path already starts with '/', so don't add another slash
  const src = `${API_BASE_URL}${source.thumbnail_path}`;

  return (
    <>
      <button
        onClick={() => setExpanded(true)}
        className="w-24 h-24 rounded-lg overflow-hidden border border-gray-200 hover:ring-2 hover:ring-blue-400 transition-all flex-shrink-0"
        title={source.filename}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={source.filename} className="w-full h-full object-cover" loading="lazy" />
      </button>

      {expanded && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          onClick={() => setExpanded(false)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt={source.filename}
            className="max-w-full max-h-full rounded-xl shadow-2xl"
            onClick={e => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}

function VideoCard({ source }: { source: VideoSource }) {
  return (
    <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
      <span className="text-2xl">▶</span>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{source.filename}</p>
        <p className="text-xs text-gray-500">{formatTimestamp(source.timestamp_sec)}</p>
      </div>
      <span className="ml-auto text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full flex-shrink-0">
        {Math.round(source.score * 100)}%
      </span>
    </div>
  );
}

function DocumentCard({ source }: { source: DocumentSource }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-gray-800 truncate">
          📄 {source.filename}
          {source.page != null && (
            <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">
              p.{source.page}
            </span>
          )}
        </span>
        <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full flex-shrink-0">
          {Math.round(source.score * 100)}%
        </span>
      </div>
      <p className="text-xs text-gray-500 italic line-clamp-2">&ldquo;{source.excerpt}&rdquo;</p>
    </div>
  );
}

interface SourcesSectionProps {
  sources: Sources;
}

export default function SourcesSection({ sources }: SourcesSectionProps) {
  const [open, setOpen] = useState(false);
  const total = sources.images.length + sources.videos.length + sources.documents.length;

  if (total === 0) return null;

  return (
    <div className="mt-3 border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700"
      >
        <span>{open ? '▼' : '▶'} Sources ({total})</span>
      </button>

      {open && (
        <div className="px-4 py-3 space-y-4">
          {sources.images.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Images</p>
              <div className="flex flex-wrap gap-2">
                {sources.images.map(s => <ImageCard key={s.id} source={s} />)}
              </div>
            </div>
          )}

          {sources.videos.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Videos</p>
              <div className="space-y-2">
                {sources.videos.map(s => <VideoCard key={s.id} source={s} />)}
              </div>
            </div>
          )}

          {sources.documents.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Documents</p>
              <div className="space-y-2">
                {sources.documents.map(s => <DocumentCard key={s.id} source={s} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
