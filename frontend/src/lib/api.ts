import type { ChatStreamEvent, IndexedFile } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function detectFileType(file: File): 'image' | 'video' | 'document' {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('video/')) return 'video';
  return 'document';
}

// Upload a file for indexing — streams SSE progress events
export async function uploadFile(
  file: File,
  onProgress: (progress: number, status: string) => void
): Promise<{ file_id: string; type: 'image' | 'video' | 'document' }> {
  const formData = new FormData();
  formData.append('file', file);

  const fileType = detectFileType(file);
  const endpoint = `/api/upload/${fileType}`;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  // Read SSE progress stream
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let result: { file_id: string; type: 'image' | 'video' | 'document' } | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n').filter(Boolean);
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        if (event.type === 'progress') onProgress(event.percent, event.status);
        if (event.type === 'done') result = { file_id: event.file_id, type: fileType };
        if (event.type === 'error') throw new Error(event.message);
      }
    }
  }

  if (!result) throw new Error('Upload completed without confirmation');
  return result;
}

// Stream chat — text query + optional query image for visual search
export async function* streamChat(
  message: string,
  queryImage?: File
): AsyncGenerator<ChatStreamEvent> {
  const formData = new FormData();
  formData.append('message', message);
  if (queryImage) formData.append('query_image', queryImage);

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n').filter(Boolean);
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6)) as ChatStreamEvent;
      }
    }
  }
}

// List all indexed files
export async function getIndexedFiles(): Promise<IndexedFile[]> {
  const res = await fetch(`${API_BASE_URL}/api/files`);
  if (!res.ok) throw new Error(`Failed to fetch files: ${res.statusText}`);
  return res.json();
}

// Delete a file from index + storage
export async function deleteFile(file_id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/delete/${file_id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
}
