# Multimodal RAG System

A production-ready Retrieval-Augmented Generation (RAG) system that supports semantic search and intelligent Q&A across **documents, images, and videos** — powered by OpenAI and Pinecone.

---

## Features

- **Upload & Index** — PDFs, DOCX, TXT, images (JPG/PNG/WEBP), and videos (MP4/AVI/MOV)
- **Semantic Search** — Find content by meaning, not just keywords
- **Image Search** — Search images by text description or upload a similar image
- **Video Search** — Extracts key frames and indexes them for content-based retrieval
- **AI Answer Generation** — GPT-4 reads retrieved results and generates comprehensive answers with source citations
- **Hybrid Search** — Combines keyword and semantic search across all media types

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Next.js (TypeScript) |
| Backend | FastAPI (Python, async) |
| Vector Database | Pinecone |
| Embeddings | OpenAI `text-embedding-3-large` (text), CLIP (images/video) |
| LLM | GPT-4 |
| Storage | Local filesystem |

---

## Project Structure

```
.
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # Upload, search, chat, health endpoints
│   │   ├── core/             # Config and dependencies
│   │   ├── models/           # Pydantic schemas
│   │   └── services/         # Pinecone, OpenAI, storage, video services
│   ├── requirements.txt
│   ├── .env.example          # Environment variable template
│   └── Dockerfile
│
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/              # Pages (home, search)
│   │   ├── components/       # UI components
│   │   ├── contexts/         # React context (chat, upload)
│   │   ├── lib/              # API client
│   │   └── types/            # TypeScript types
│   └── .env.local.example    # Frontend env template
│
├── tools/                    # CLI scripts
│   ├── pinecone_init.py      # Initialize Pinecone index
│   ├── extract_frames.py     # Video frame extraction
│   ├── process_document.py   # Document chunking
│   └── generate_embeddings.py
│
├── workflows/                # Architecture & SOP docs
│   ├── BACKEND_PLAN.md
│   ├── FRONTEND_PLAN.md
│   └── components/           # Per-feature workflow docs
│
└── carousel/                 # Presentation slides (HTML)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Pinecone](https://www.pinecone.io/) account
- [OpenAI](https://platform.openai.com/) API key

### 1. Clone the repo

```bash
git clone https://github.com/SHIVAAKARTHIK/claude-rag-system.git
cd claude-rag-system
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # Fill in your API keys
```

### 3. Initialize Pinecone index

```bash
python ../tools/pinecone_init.py
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Frontend setup

```bash
cd ../frontend
npm install
cp .env.local.example .env.local   # Set NEXT_PUBLIC_API_URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

**`backend/.env`** (copy from `.env.example`)

```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=multimodal-rag
OPENAI_API_KEY=your_openai_api_key
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=100MB
```

**`frontend/.env.local`** (copy from `.env.local.example`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload and index a file |
| `GET` | `/api/search?q=...` | Semantic search |
| `POST` | `/api/chat` | Ask a question, get GPT-4 answer |
| `GET` | `/api/health` | Health check |

---

## Architecture

This project follows the **WAT framework** (Workflows → Agents → Tools):

- **Workflows** (`workflows/`) — Markdown SOPs defining how each feature works
- **Agents** — AI reasoning layer that reads workflows and coordinates tools
- **Tools** (`tools/`) — Deterministic Python scripts for execution

---

## License

MIT
