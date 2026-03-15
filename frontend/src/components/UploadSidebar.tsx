'use client';

import { useUpload } from '@/contexts/UploadContext';
import UploadZone from './UploadZone';
import UploadProgressItem from './UploadProgressItem';
import IndexedFileItem from './IndexedFileItem';

export default function UploadSidebar() {
  const { uploads, indexedFiles } = useUpload();

  return (
    <aside className="w-80 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
        <h2 className="text-sm font-semibold text-gray-700">Knowledge Base</h2>
      </div>

      {/* Upload zone */}
      <div className="flex-shrink-0">
        <UploadZone />
      </div>

      {/* Scrollable list area */}
      <div className="flex-1 overflow-y-auto">
        {/* In-progress uploads */}
        {uploads.length > 0 && (
          <div>
            <div className="px-4 py-2 border-b border-gray-100">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Uploading ({uploads.length})
              </span>
            </div>
            {uploads.map(item => (
              <UploadProgressItem key={item.id} item={item} />
            ))}
          </div>
        )}

        {/* Indexed files */}
        {indexedFiles.length > 0 && (
          <div>
            <div className="px-4 py-2 border-b border-gray-100">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Indexed ({indexedFiles.length})
              </span>
            </div>
            {indexedFiles.map(file => (
              <IndexedFileItem key={file.file_id} file={file} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {uploads.length === 0 && indexedFiles.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-400 text-sm">
            <p>No files indexed yet.</p>
            <p className="mt-1 text-xs">Drop files above to get started.</p>
          </div>
        )}
      </div>
    </aside>
  );
}
