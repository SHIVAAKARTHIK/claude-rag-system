# Frontend Architecture Plan - Multimodal RAG Chatbot

## Objective
Two-panel layout: left side is a ChatGPT-style chat interface; right side is a dedicated Upload Sidebar where users index files (images, videos, documents) into the knowledge base and see real-time upload progress. Users can also attach a single image directly in the chat input to run a visual similarity search ("find images/videos like this").

---

## Page Structure
```
/ (Single Page)
┌──────────────────────────┬───────────────────────┐
│                          │   UPLOAD SIDEBAR       │
│      CHAT PANEL          │  ─────────────────────│
│   (scrollable thread)    │  Drop or Browse files  │
│                          │  ─────────────────────│
│                          │  ⏳ Uploading...       │
│                          │  ✅ report.pdf         │
│                          │  ✅ beach.jpg          │
│   [Chat Input Bar]       │  ✅ clip.mp4           │
└──────────────────────────┴───────────────────────┘
```

---

## Component Hierarchy
```
App Layout (layout.tsx)
├── Header (logo + "Clear Chat" button)
└── MainPage (app/page.tsx)  ← flex row, full height
    ├── ChatPanel (components/ChatPanel.tsx)  ← flex-1, flex col
    │   ├── ChatThread (components/ChatThread.tsx)
    │   │   ├── WelcomeScreen (shown when no messages)
    │   │   ├── UserMessage (components/UserMessage.tsx)
    │   │   │   └── QueryImagePreview (if image attached for visual search)
    │   │   └── AIMessage (components/AIMessage.tsx)
    │   │       ├── TextAnswer (streaming typewriter)
    │   │       └── SourcesSection (components/SourcesSection.tsx)
    │   │           ├── ImageSource (thumbnail)
    │   │           ├── VideoSource (playable clip + timestamp badge)
    │   │           └── DocumentSource (excerpt + page number)
    │   └── ChatInput (components/ChatInput.tsx)
    │       ├── QueryImagePreview (optional — image for visual search)
    │       ├── TextInput (multiline)
    │       └── Actions: [🖼 Attach Image] [Send ▶]
    └── UploadSidebar (components/UploadSidebar.tsx)  ← fixed 320px right
        ├── UploadZone (components/UploadZone.tsx)
        │   ├── DropArea (drag-drop target)
        │   └── BrowseButton (file picker)
        ├── UploadProgressList (active uploads)
        │   └── UploadProgressItem (filename, progress bar, status icon)
        └── IndexedFilesList (completed uploads — persists in session)
            └── IndexedFileItem (type icon, filename, badge, delete btn)
```

---

## Core Components

### 1. MainPage (`app/page.tsx`)

**Layout:**
```tsx
<div className="flex h-screen bg-gray-50">
  <ChatPanel className="flex-1 flex flex-col min-w-0" />
  <UploadSidebar className="w-80 border-l bg-white flex-shrink-0" />
</div>
```

---

### 2. UploadSidebar (`components/UploadSidebar.tsx`)

**Purpose:** Dedicated area for indexing files into the knowledge base. Completely separate from chat.

**Supported file types for indexing:**
- Images: PNG, JPEG/JPG
- Videos: MP4
- Documents: PDF, Markdown (.md)

**UI Layout:**
```
┌─────────────────────────┐
│  Knowledge Base          │
├─────────────────────────┤
│  ┌───────────────────┐  │
│  │  Drop files here  │  │
│  │   or  [Browse]    │  │  ← UploadZone
│  │  PNG·JPG·PDF·     │  │
│  │  MD·MP4           │  │
│  └───────────────────┘  │
├─────────────────────────┤
│  Uploading (2)           │
│  ⏳ beach.jpg  ████░░   │  ← UploadProgressItem
│  ⏳ clip.mp4   ██░░░░   │
├─────────────────────────┤
│  Indexed (3)             │
│  🖼 sunset.jpg     [🗑] │  ← IndexedFileItem
│  📄 report.pdf     [🗑] │
│  🎥 tour.mp4       [🗑] │
└─────────────────────────┘
```

**Props:** none (reads from UploadContext)

---

### 3. UploadZone (`components/UploadZone.tsx`)

**Purpose:** Drag-drop + browse file picker for indexing files

**Features:**
- Drag-and-drop files anywhere on the zone
- Click to open file picker
- Validates file type and size before upload
- Calls `uploadFile()` from UploadContext for each file
- Highlights on drag-over

**File validation:**
```typescript
const ACCEPTED_TYPES = {
  image: ['image/jpeg', 'image/png'],
  video: ['video/mp4'],
  document: ['application/pdf', 'text/markdown', 'text/x-markdown']
};

const SIZE_LIMITS = {
  image: 10 * 1024 * 1024,    // 10MB
  video: 100 * 1024 * 1024,   // 100MB
  document: 50 * 1024 * 1024  // 50MB
};
```

---

### 4. UploadProgressItem (`components/UploadProgressItem.tsx`)

**Purpose:** Shows live progress for an in-flight upload

**Props:**
```typescript
interface UploadProgressItemProps {
  filename: string;
  progress: number;   // 0–100
  status: 'uploading' | 'processing' | 'indexed' | 'failed';
}
```

**UI:** filename + animated progress bar + status icon
- `uploading` → spinner
- `processing` → spinning gear icon (server is embedding)
- `indexed` → green checkmark (moves to IndexedFilesList)
- `failed` → red X + error tooltip

---

### 5. IndexedFileItem (`components/IndexedFileItem.tsx`)

**Purpose:** Displays a successfully indexed file in the sidebar list

**Props:**
```typescript
interface IndexedFileItemProps {
  file_id: string;
  filename: string;
  type: 'image' | 'video' | 'document';
  onDelete: (file_id: string) => void;
}
```

**UI:** `[type icon] filename.ext [🗑]`
- 🖼 for images, 🎥 for videos, 📄 for documents
- Delete calls `DELETE /api/delete/{file_id}` and removes from list

---

### 6. ChatInput (`components/ChatInput.tsx`)

**Purpose:** Chat query bar. Supports text + optional single image for visual similarity search.

> **Important distinction:** The 🖼 attach button here is for **visual search queries only** (e.g. "find similar images to this"). It does NOT index the file into Pinecone. Indexing happens only through the UploadSidebar.

**Features:**
- Multiline text input (Enter to send, Shift+Enter for newline)
- 🖼 button to attach one image for visual query (PNG/JPEG only)
- Shows image preview thumbnail above input when attached
- Remove preview with ×
- Greyed out while AI is streaming

**Props:**
```typescript
interface ChatInputProps {
  onSend: (message: string, queryImage?: File) => void;
  disabled?: boolean;
}
```

**UI Layout:**
```
┌────────────────────────────────────────┐
│ [🖼 photo.jpg ×]                       │  ← query image preview (if attached)
├────────────────────────────────────────┤
│ 🖼  Type a message...        [Send ▶] │
└────────────────────────────────────────┘
```

---

### 7. ChatThread (`components/ChatThread.tsx`)

**Purpose:** Scrollable message history

**Features:**
- Auto-scrolls to bottom on new messages
- Shows WelcomeScreen when no messages
- Maps over `messages[]` and renders `UserMessage` or `AIMessage`

**WelcomeScreen:**
```
📁 Upload files in the sidebar to index them
🖼  Attach an image in chat to find similar content
💬 Ask questions and get answers with sources
```

---

### 8. UserMessage (`components/UserMessage.tsx`)

**Purpose:** Right-aligned user bubble

**Props:**
```typescript
interface UserMessageProps {
  text: string;
  queryImage?: { name: string };  // visual search image, if any
}
```

Shows query image as a small thumbnail pill if present.

---

### 9. AIMessage (`components/AIMessage.tsx`)

**Purpose:** AI response with streaming text + sources

**Props:**
```typescript
interface AIMessageProps {
  text: string;
  sources?: Sources;
  streaming?: boolean;
}
```

**Features:**
- Typewriter streaming text
- Loading skeleton while waiting for first chunk
- Collapsible "Sources (N)" section once streaming finishes
- Copy button

---

### 10. SourcesSection (`components/SourcesSection.tsx`)

**Purpose:** Collapsible panel showing media sources

**Features:**
- Toggle "Sources (N)" to expand/collapse
- Images: thumbnail grid (click to expand full-size lightbox)
- Videos: thumbnail + ▶ overlay + timestamp badge (click to play)
- Documents: filename + excerpt + page chip

**UI Layout:**
```
▼ Sources (3)
┌─────────────────────────────────────┐
│ Images                               │
│ [🖼 beach.jpg]  [🖼 sunset.jpg]     │
│                                      │
│ Videos                               │
│ [▶ clip.mp4  0:23]                  │
│                                      │
│ Documents                            │
│ 📄 report.pdf · p.3                 │
│ "The beach area shows tropical..."  │
└─────────────────────────────────────┘
```

---

## API Client (`lib/api.ts`)

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Upload a file for indexing — returns SSE progress stream
export async function uploadFile(
  file: File,
  onProgress: (progress: number, status: string) => void
): Promise<{ file_id: string; type: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const fileType = detectFileType(file);
  const endpoint = `/api/upload/${fileType}`;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  // SSE progress stream
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let result: { file_id: string; type: string } | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n').filter(Boolean);
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        if (event.type === 'progress') onProgress(event.percent, event.status);
        if (event.type === 'done') result = { file_id: event.file_id, type: fileType };
      }
    }
  }
  return result!;
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

  const reader = response.body!.getReader();
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
  return res.json();
}

// Delete a file from index + storage
export async function deleteFile(file_id: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/delete/${file_id}`, { method: 'DELETE' });
}

function detectFileType(file: File): 'image' | 'video' | 'document' {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('video/')) return 'video';
  return 'document';
}
```

---

## TypeScript Types (`types/index.ts`)

```typescript
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
```

---

## State Management

### ChatContext (`contexts/ChatContext.tsx`)

```typescript
interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (text: string, queryImage?: File) => Promise<void>;
  clearChat: () => void;
}

const sendMessage = async (text: string, queryImage?: File) => {
  // 1. Add user message
  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: 'user',
    text,
    queryImage: queryImage ? { name: queryImage.name } : undefined,
  };
  setMessages(prev => [...prev, userMsg]);

  // 2. Add empty AI message (streaming placeholder)
  const aiMsg: Message = { id: crypto.randomUUID(), role: 'assistant', text: '', streaming: true };
  setMessages(prev => [...prev, aiMsg]);
  setIsLoading(true);

  // 3. Stream response
  for await (const event of streamChat(text, queryImage)) {
    if (event.type === 'text_chunk') {
      setMessages(prev => prev.map(m =>
        m.id === aiMsg.id ? { ...m, text: m.text + event.content } : m
      ));
    } else if (event.type === 'sources') {
      setMessages(prev => prev.map(m =>
        m.id === aiMsg.id ? { ...m, sources: event.data, streaming: false } : m
      ));
    }
  }
  setIsLoading(false);
};
```

### UploadContext (`contexts/UploadContext.tsx`)

```typescript
interface UploadContextType {
  uploads: UploadItem[];           // in-progress
  indexedFiles: IndexedFile[];     // completed
  uploadFile: (file: File) => void;
  deleteFile: (file_id: string) => Promise<void>;
}

const uploadFile = async (file: File) => {
  const localId = crypto.randomUUID();

  // Add to in-progress list immediately
  setUploads(prev => [...prev, {
    id: localId,
    filename: file.name,
    progress: 0,
    status: 'uploading'
  }]);

  try {
    const result = await apiUploadFile(file, (progress, status) => {
      setUploads(prev => prev.map(u =>
        u.id === localId ? { ...u, progress, status: status as any } : u
      ));
    });

    // Move to indexed list
    setUploads(prev => prev.filter(u => u.id !== localId));
    setIndexedFiles(prev => [...prev, {
      file_id: result.file_id,
      filename: file.name,
      type: result.type as any,
      indexed_at: new Date().toISOString()
    }]);
  } catch (err) {
    setUploads(prev => prev.map(u =>
      u.id === localId ? { ...u, status: 'failed', error: String(err) } : u
    ));
  }
};
```

---

## Styling Strategy

**Approach:** Tailwind CSS

**Key layout:**
```tsx
// app/page.tsx
<div className="flex h-screen bg-gray-50 overflow-hidden">
  {/* Chat panel — takes remaining space */}
  <div className="flex-1 flex flex-col min-w-0">
    <ChatThread className="flex-1 overflow-y-auto px-4" />
    <ChatInput className="border-t bg-white p-4" />
  </div>
  {/* Upload sidebar — fixed width */}
  <UploadSidebar className="w-80 border-l bg-white flex-shrink-0 flex flex-col overflow-hidden" />
</div>
```

**Upload sidebar sections:**
- Header: `text-sm font-semibold text-gray-700 px-4 py-3 border-b`
- UploadZone: `border-2 border-dashed rounded-lg m-3 p-6 text-center cursor-pointer hover:bg-gray-50`
- Progress items: `flex items-center gap-2 px-4 py-2 text-sm`
- Indexed items: `flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50`

**Message bubbles:**
- User: right-aligned, `bg-blue-600 text-white rounded-2xl`
- AI: left-aligned, `bg-white border rounded-2xl shadow-sm`

---

## Dependencies (`package.json`)

```json
{
  "dependencies": {
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/react": "^18.2.48",
    "@types/node": "^20.11.0",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.1.0"
  }
}
```

---

## Start Here
1. Create Next.js app: `npx create-next-app@latest multimodal-rag-frontend --typescript --tailwind`
2. Create `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Build in order:
   - `types/index.ts`
   - `contexts/UploadContext.tsx`
   - `contexts/ChatContext.tsx`
   - `lib/api.ts`
   - `components/UploadZone.tsx`
   - `components/UploadProgressItem.tsx`
   - `components/IndexedFileItem.tsx`
   - `components/UploadSidebar.tsx`
   - `components/ChatInput.tsx`
   - `components/UserMessage.tsx`
   - `components/SourcesSection.tsx`
   - `components/AIMessage.tsx`
   - `components/ChatThread.tsx`
   - `components/ChatPanel.tsx`
   - `app/page.tsx`
4. Test with backend running: `npm run dev`
