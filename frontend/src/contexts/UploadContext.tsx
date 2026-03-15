'use client';

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { UploadItem, IndexedFile } from '@/types';
import {
  uploadFile as apiUploadFile,
  getIndexedFiles,
  deleteFile as apiDeleteFile,
} from '@/lib/api';

interface UploadContextType {
  uploads: UploadItem[];           // in-progress uploads
  indexedFiles: IndexedFile[];     // successfully indexed files
  uploadFile: (file: File) => void;
  deleteFile: (file_id: string) => Promise<void>;
}

const UploadContext = createContext<UploadContextType | null>(null);

export function UploadProvider({ children }: { children: ReactNode }) {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [indexedFiles, setIndexedFiles] = useState<IndexedFile[]>([]);

  // Load existing indexed files on mount
  useEffect(() => {
    getIndexedFiles()
      .then(files => setIndexedFiles(files))
      .catch(() => {/* backend may not be running yet */});
  }, []);

  const uploadFile = (file: File) => {
    const localId = crypto.randomUUID();

    // Add to in-progress list immediately
    setUploads(prev => [...prev, {
      id: localId,
      filename: file.name,
      progress: 0,
      status: 'uploading',
    }]);

    apiUploadFile(file, (progress, status) => {
      setUploads(prev => prev.map(u =>
        u.id === localId ? { ...u, progress, status: status as UploadItem['status'] } : u
      ));
    })
      .then(result => {
        // Move to indexed list
        setUploads(prev => prev.filter(u => u.id !== localId));
        setIndexedFiles(prev => [...prev, {
          file_id: result.file_id,
          filename: file.name,
          type: result.type,
          indexed_at: new Date().toISOString(),
        }]);
      })
      .catch(err => {
        setUploads(prev => prev.map(u =>
          u.id === localId
            ? { ...u, status: 'failed', error: err instanceof Error ? err.message : String(err) }
            : u
        ));
      });
  };

  const deleteFile = async (file_id: string) => {
    await apiDeleteFile(file_id);
    setIndexedFiles(prev => prev.filter(f => f.file_id !== file_id));
  };

  return (
    <UploadContext.Provider value={{ uploads, indexedFiles, uploadFile, deleteFile }}>
      {children}
    </UploadContext.Provider>
  );
}

export function useUpload() {
  const ctx = useContext(UploadContext);
  if (!ctx) throw new Error('useUpload must be used within UploadProvider');
  return ctx;
}
