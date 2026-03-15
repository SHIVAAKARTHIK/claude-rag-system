export type MessageRole = 'user' | 'assistant';

export interface IndexedFile {
  file_id: string;
  filename: string;
  type: 'image' | 'video' | 'document';
  indexed_at: string;
}

export interface UploadItem {
  id: string;            // local UUID for tracking
  filename: string;
  progress: number;      // 0–100
  status: 'uploading' | 'processing' | 'indexed' | 'failed';
  file_id?: string;      // set when server confirms indexed
  type?: 'image' | 'video' | 'document';
  error?: string;
}

export interface ImageSource {
  id: string;
  filename: string;
  thumbnail_path: string;
  score: number;
}

export interface VideoSource {
  id: string;
  filename: string;
  timestamp_sec: number;
  score: number;
}

export interface DocumentSource {
  id: string;
  filename: string;
  excerpt: string;
  page?: number;
  score: number;
}

export interface Sources {
  images: ImageSource[];
  videos: VideoSource[];
  documents: DocumentSource[];
}

export interface Message {
  id: string;
  role: MessageRole;
  text: string;
  queryImage?: { name: string };  // visual search image (user messages only)
  sources?: Sources;              // AI messages only
  streaming?: boolean;
}

// Streaming event types from /api/chat
export type ChatStreamEvent =
  | { type: 'text_chunk'; content: string }
  | { type: 'sources'; data: Sources }
  | { type: 'error'; message: string };

// Streaming event types from /api/upload/*
export type UploadStreamEvent =
  | { type: 'progress'; percent: number; status: string }
  | { type: 'done'; file_id: string }
  | { type: 'error'; message: string };
