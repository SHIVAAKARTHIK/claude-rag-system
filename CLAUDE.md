# Multimodal RAG System - Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools) to build and maintain a production-ready multimodal RAG system. This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution.

## System Overview

**Project Name:** Multimodal RAG System  
**Owner:** Karthik  
**Purpose:** Semantic search and retrieval across images, videos, and documents with GPT-4 powered answer generation

**Tech Stack:**
- **Vector DB:** Pinecone (cloud, scalable)
- **Backend:** FastAPI (async, modern)
- **Frontend:** React + Next.js
- **Embeddings:** OpenAI (text-embedding-3-large for text, CLIP for images/video)
- **LLM:** GPT-4 for answer generation
- **Storage:** Local filesystem
- **Deployment:** Local development environment

## Core Capabilities

1. **Upload & Index**
   - Documents (PDF, TXT, DOCX, MD)
   - Images (JPG, PNG, WEBP)
   - Videos (MP4, AVI, MOV) - extracts key frames

2. **Search & Retrieve**
   - Semantic image search by text description
   - Find videos by content description
   - Upload image to find similar images
   - Hybrid search (keyword + semantic) across all media types

3. **Answer Generation**
   - Retrieves top-k relevant results from Pinecone
   - Passes context to GPT-4
   - Generates comprehensive answers with source citations

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- See `workflows/BACKEND_PLAN.md` and `workflows/FRONTEND_PLAN.md` for detailed component plans
- Each workflow defines objectives, inputs, tools, outputs, and edge case handling

**Layer 2: Agents (The Decision-Maker)**
- You read workflows, coordinate tools, handle failures, and ask clarifying questions
- Connect intent to execution without attempting direct implementation
- Example: Need to extract video frames? Read `workflows/video_processing.md`, then execute `tools/extract_frames.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` for deterministic operations
- Backend API routes in `backend/app/`
- Frontend components in `frontend/src/`
- Credentials stored in `.env` files

## How to Operate

**1. Start with existing workflows**
Before building anything:
- Check `workflows/BACKEND_PLAN.md` for backend architecture
- Check `workflows/FRONTEND_PLAN.md` for frontend structure
- Review component-specific workflows in `workflows/components/`

**2. Learn and adapt when things fail**
When errors occur:
- Read full error traces
- Check API rate limits (OpenAI, Pinecone)
- Fix the tool/script and retest
- Update the workflow with lessons learned
- Document API quirks and constraints

**3. Keep workflows current**
- Update workflows as you discover better approaches
- Document rate limits, timing issues, edge cases
- Never overwrite workflows without asking first
- These are your source of truth

## File Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── api/                    # API routes
│   │   │   ├── upload.py           # File upload endpoints
│   │   │   ├── search.py           # Search endpoints
│   │   │   └── health.py           # Health checks
│   │   ├── core/
│   │   │   ├── config.py           # Environment config
│   │   │   └── dependencies.py     # Shared dependencies
│   │   ├── services/
│   │   │   ├── pinecone_service.py # Vector DB operations
│   │   │   ├── embedding_service.py # OpenAI embeddings
│   │   │   ├── llm_service.py      # GPT-4 generation
│   │   │   └── storage_service.py  # File storage
│   │   └── models/
│   │       └── schemas.py          # Pydantic models
│   ├── requirements.txt
│   ├── .env                        # API keys (gitignored)
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Home page
│   │   │   ├── layout.tsx          # Root layout
│   │   │   └── search/
│   │   │       └── page.tsx        # Search page
│   │   ├── components/
│   │   │   ├── UploadZone.tsx      # Drag-drop upload
│   │   │   ├── SearchBar.tsx       # Search interface
│   │   │   ├── ResultsGrid.tsx     # Results display
│   │   │   └── AnswerPanel.tsx     # GPT-4 answers
│   │   ├── lib/
│   │   │   └── api.ts              # Backend API client
│   │   └── types/
│   │       └── index.ts            # TypeScript types
│   ├── package.json
│   ├── next.config.js
│   └── .env.local                  # API endpoint config
│
├── tools/
│   ├── extract_frames.py           # Video frame extraction
│   ├── process_document.py         # Document chunking
│   ├── generate_embeddings.py      # Batch embedding generation
│   └── pinecone_init.py            # Initialize Pinecone index
│
├── workflows/
│   ├── BACKEND_PLAN.md             # Backend architecture & plan
│   ├── FRONTEND_PLAN.md            # Frontend architecture & plan
│   ├── components/
│   │   ├── upload_workflow.md      # File upload process
│   │   ├── search_workflow.md      # Search process
│   │   ├── video_processing.md     # Video frame extraction
│   │   └── embedding_workflow.md   # Embedding generation
│   └── deployment/
│       └── local_setup.md          # Local dev setup
│
├── .tmp/                           # Temporary processing files
│   ├── uploads/                    # Uploaded files (regenerable)
│   ├── frames/                     # Extracted video frames
│   └── chunks/                     # Document chunks
│
└── data/                           # Persistent local storage
    ├── uploads/                    # Original uploaded files
    └── metadata/                   # File metadata JSON
```

## Key Workflows Reference

**Backend Development:**
- See `workflows/BACKEND_PLAN.md` for complete backend architecture
- API design, service layer structure, error handling patterns

**Frontend Development:**
- See `workflows/FRONTEND_PLAN.md` for complete frontend architecture
- Component hierarchy, state management, API integration

**Core Operations:**
- `workflows/components/upload_workflow.md` - File upload and indexing
- `workflows/components/search_workflow.md` - Search and retrieval
- `workflows/components/video_processing.md` - Video frame extraction
- `workflows/components/embedding_workflow.md` - Embedding generation

## Environment Variables

**Backend (.env):**
```
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=multimodal-rag
OPENAI_API_KEY=your_key_here
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=100MB
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## The Self-Improvement Loop

Every failure strengthens the system:
1. Identify what broke (API limit? File format? Network error?)
2. Fix the tool/service
3. Verify the fix works
4. Update the relevant workflow with the new approach
5. Continue with a more robust system

## Critical Constraints

**API Rate Limits:**
- OpenAI embeddings: 3,000 RPM (requests per minute)
- OpenAI GPT-4: 10,000 TPM (tokens per minute)
- Pinecone: Check your plan limits
- Implement exponential backoff in services

**File Processing:**
- Video frame extraction: Max 10 frames per video to control costs
- Document chunking: 500 token chunks with 50 token overlap
- Image processing: Resize to max 1024x1024 before embedding

**Error Handling:**
- All API calls wrapped in try-catch with retries
- Failed uploads stored in error log with recovery path
- Graceful degradation if embedding service is down

## Development Workflow

**Starting a new feature:**
1. Check if a workflow exists for it
2. If not, create one in `workflows/components/`
3. Build the tool in `tools/` or service in `backend/app/services/`
4. Test thoroughly with edge cases
5. Update the workflow with learnings

**Debugging:**
1. Check logs in backend (FastAPI auto-logs)
2. Check browser console for frontend errors
3. Verify API keys are loaded correctly
4. Test Pinecone connection independently
5. Check OpenAI API status page if embedding fails

## Bottom Line

You sit between what needs to be done (workflows) and what actually gets executed (tools/services). Your job is to:
- Read instructions from workflows
- Make intelligent decisions about execution
- Call the right tools/services in correct sequence
- Recover gracefully from errors
- Keep improving the system as you learn

Stay pragmatic. Stay reliable. Keep learning.

---

**Quick Start:**
1. Read `workflows/BACKEND_PLAN.md` for backend setup
2. Read `workflows/FRONTEND_PLAN.md` for frontend setup
3. Run `tools/pinecone_init.py` to initialize vector database
4. Start coding!
