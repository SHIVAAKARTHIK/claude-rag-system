'use client';

import { useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { useUpload } from '@/contexts/UploadContext';

const ACCEPTED_TYPES = [
  'image/jpeg',
  'image/png',
  'video/mp4',
  'application/pdf',
  'text/markdown',
  'text/x-markdown',
];

const SIZE_LIMITS: Record<string, number> = {
  image: 10 * 1024 * 1024,    // 10 MB
  video: 100 * 1024 * 1024,   // 100 MB
  document: 50 * 1024 * 1024, // 50 MB
};

function getCategory(mimeType: string): 'image' | 'video' | 'document' {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('video/')) return 'video';
  return 'document';
}

export default function UploadZone() {
  const { uploadFile } = useUpload();
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFiles = (files: File[]) => {
    for (const file of files) {
      if (!ACCEPTED_TYPES.includes(file.type)) continue;
      const category = getCategory(file.type);
      if (file.size > SIZE_LIMITS[category]) continue;
      uploadFile(file);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    processFiles(Array.from(e.dataTransfer.files));
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) processFiles(Array.from(e.target.files));
    e.target.value = '';
  };

  return (
    <div className="mx-3 my-3">
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
      >
        <p className="text-2xl mb-2">📂</p>
        <p className="text-sm text-gray-600 font-medium">Drop files here</p>
        <p className="text-xs text-gray-400 mt-1">or click to browse</p>
        <p className="text-xs text-gray-400 mt-2">PNG · JPG · PDF · MD · MP4</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES.join(',')}
        className="hidden"
        onChange={handleChange}
      />
    </div>
  );
}
