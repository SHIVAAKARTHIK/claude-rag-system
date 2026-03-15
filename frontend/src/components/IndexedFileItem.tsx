'use client';

import { useState } from 'react';
import { useUpload } from '@/contexts/UploadContext';
import type { IndexedFile } from '@/types';

function fileIcon(type: IndexedFile['type']) {
  if (type === 'image') return '🖼';
  if (type === 'video') return '🎥';
  return '📄';
}

interface IndexedFileItemProps {
  file: IndexedFile;
}

export default function IndexedFileItem({ file }: IndexedFileItemProps) {
  const { deleteFile } = useUpload();
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteFile(file.file_id);
    } catch {
      setDeleting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50 group">
      <span className="text-base flex-shrink-0">{fileIcon(file.type)}</span>
      <span className="flex-1 truncate text-gray-700" title={file.filename}>
        {file.filename}
      </span>
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all disabled:opacity-30 flex-shrink-0"
        aria-label={`Delete ${file.filename}`}
        title="Remove from index"
      >
        {deleting ? (
          <span className="w-3.5 h-3.5 rounded-full border-2 border-gray-400 border-t-transparent animate-spin inline-block" />
        ) : (
          '🗑'
        )}
      </button>
    </div>
  );
}
