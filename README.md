# Study Space

> An AI-powered personalized learning platform — chat with your documents, generate quizzes, flashcard decks, and AI explainer videos, all from your own study materials.

---

## Overview

Study Space is a full-stack web application that transforms how students interact with their study materials. Upload PDFs, notes, books, or links — and instantly unlock an AI tutor that can answer questions about them, generate quizzes to test your understanding, create flashcard decks tailored to your difficulty level, and produce narrated explainer videos from your content.

**The problem it solves:** Traditional studying is passive. Students read through materials but have no interactive way to verify comprehension, drill key concepts, or get a visual overview of a topic. Study Space bridges this gap by combining retrieval-augmented generation (RAG) with a conversational AI interface and a multi-modal content generation pipeline — so your documents become something you can actually _talk to_, get tested on, and watch explained.

---

## Features

- **Document Upload & Processing** — Upload PDFs, notes, books, or web links. Documents are parsed, chunked, and embedded asynchronously in the background.
- **Conversational Chat** — Ask questions about your uploaded documents in natural language. The AI retrieves relevant context from your files and answers with source grounding.
- **Multi-session Chat History** — Manage multiple chat sessions with persistent message history stored in PostgreSQL.
- **Quiz Generation** — Generate multiple-choice quizzes from your sources. Choose difficulty, number of questions, and optionally provide a focus prompt. Supports broad (all chunks) and focused (semantic RAG) modes.
- **Flashcard Decks** — Auto-generate two-sided flashcard decks from your materials with difficulty-aware card generation. Flip cards in-browser to self-test.
- **AI Explainer Video Generation** — Generate narrated short-form educational videos from your study materials. Gemini writes a scene-by-scene script, illustrates each scene (AI-generated images or Manim animations), adds TTS narration, and assembles the final MP4 using FFmpeg. Two render modes are supported: Image (Gemini image generation with Pillow fallback) and Manim (programmatically animated diagrams).
- **Document Viewer** — Preview uploaded PDFs side-by-side with your content without leaving the app.
- **JWT Authentication** — Secure login/signup with access and refresh token rotation via HttpOnly cookies.

---

## Tech Stack

### Frontend

| Layer           | Technology               |
| --------------- | ------------------------ |
| Framework       | Next.js 16 (App Router)  |
| Language        | TypeScript               |
| Styling         | Tailwind CSS v4          |
| HTTP Client     | Axios                    |
| Icons           | Lucide React             |
| Document Viewer | `@docmentis/udoc-viewer` |

### Backend

| Layer          | Technology                             |
| -------------- | -------------------------------------- |
| Framework      | FastAPI                                |
| Language       | Python 3.10+                           |
| ORM            | SQLAlchemy                             |
| Auth           | JWT (`python-jose`), `passlib[bcrypt]` |
| Task Queue     | Celery                                 |
| Message Broker | Redis                                  |

### Database & Storage

| Service    | Purpose                                                             |
| ---------- | ------------------------------------------------------------------- |
| PostgreSQL | Application data (users, files, chats, quizzes, flashcards, videos) |
| Pinecone   | Vector database for document embeddings                             |
| Local disk | Raw uploaded files and generated video assets                       |

### AI & Infrastructure

| Service                                         | Purpose                                                          |
| ----------------------------------------------- | ---------------------------------------------------------------- |
| Google Gemini (`gemini-3.1-flash-lite-preview`) | LLM for chat, quiz, flashcard, and video script generation       |
| Gemini Image Model (`gemini-2.5-flash-image`)   | Scene illustration generation for video                          |
| Gemini TTS (`gemini-2.5-flash-preview-tts`)     | Narration audio synthesis for video                              |
| Docling                                         | Document parsing and Markdown extraction                         |
| LangChain                                       | RAG chains, prompt templates, chat history                       |
| Pinecone Integrated Embeddings                  | Serverless embedding + vector search                             |
| Manim Community Edition                         | Programmatic animation rendering (optional video renderer)       |
| FFmpeg                                          | Video clip assembly, audio muxing, and thumbnail extraction      |
| Pillow                                          | Placeholder scene images when AI image generation is unavailable |

---

## Demo / Screenshots

**Typical workflow:**

1. Upload a PDF → wait for the green checkmark (processed)
2. Select it as context → ask the AI a question in Chat
3. Open Quiz modal → generate a medium-difficulty quiz and attempt it
4. Open Flashcards modal → create a focused deck on a specific topic
5. Open Video modal → generate a ~3-10 minute narrated explainer and watch it in-browser

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (running locally or remote)
- Redis (running locally or remote)
- A Pinecone account with an index configured for integrated embeddings
- A Google AI Studio API key with access to Gemini (including image and TTS models)
- FFmpeg installed and accessible on your `PATH` (required for video generation)
- Manim Community Edition (optional — only needed for the Manim renderer)

### Clone

```bash
git clone https://github.com/your-username/study-space.git
cd study-space
```

### Backend dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend dependencies

```bash
cd frontend
npm install
```

---

## Environment Variables

Create `backend/.env` with the following variables:

```env
# ── Database ────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/StudySpace

# ── Redis / Celery ──────────────────────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ── JWT ─────────────────────────────────────────────────────
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Google Gemini ────────────────────────────────────────────
GEMINI_API_KEY=AIza...your_gemini_key

# ── Pinecone ─────────────────────────────────────────────────
PINECONE_API_KEY=pcsk_...your_pinecone_key
PINECONE_INDEX_NAME=study-space-index
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_HOST=                      # Optional: direct host URL
PINECONE_NAMESPACE=__default__
PINECONE_INTEGRATED_TEXT_FIELD=text

# ── Embedding Model ──────────────────────────────────────────
EMBEDDING_MODEL_NAME=your-embedding-model-name

# ── Video Generation ─────────────────────────────────────────
VIDEO_STORAGE_PATH=storage/generated/videos
VIDEO_IMAGE_MODEL=gemini-2.5-flash-image
VIDEO_TTS_MODEL=gemini-2.5-flash-preview-tts
VIDEO_TTS_VOICE=Kore
VIDEO_MAX_SCENES=3
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
VIDEO_ALIGNMENT_TOLERANCE_SECONDS=0.35

# ── Manim (only needed for Manim renderer) ───────────────────
MANIM_CLI_BIN=manim
MANIM_PYTHON_BIN=python
MANIM_RENDER_QUALITY=m
MANIM_RENDER_TIMEOUT_SECONDS=300
MANIM_DISABLE_CACHING=true
MANIM_TEX_ENABLED=false
MANIM_MAX_SCENES=8
MANIM_MAX_BLOCKS_PER_SCENE=5
```

> **Note:** `PINECONE_INDEX_HOST` takes priority over `PINECONE_INDEX_NAME` when set. Video generation requires FFmpeg on `PATH`. The Manim renderer additionally requires Manim Community Edition installed in the same environment as the Celery worker.

---

## How to Run

### 1. Start Redis

```bash
sudo service redis-server start
# or: redis-server
```

### 2. Start the FastAPI backend

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
# API: http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/api/v1/docs
```

### 3. Start the Celery worker (required for file processing and video generation)

In a separate terminal:

```bash
cd backend
source venv/bin/activate

# Linux / macOS
celery -A app.core.celery_worker.celery_app worker --loglevel=info

# Windows
celery -A app.core.celery_worker.celery_app worker --loglevel=info --pool=threads
```

### 4. Start the Next.js frontend

```bash
cd frontend
npm run dev
# App: http://localhost:5173
```

### Production build

```bash
cd frontend
npm run build
npm run start
```

---

## Usage

### Basic workflow

1. **Sign up / Log in** at `/signup` or `/login`.
2. **Upload a document** — click **Add Content** in the Content panel, select a PDF, and confirm. A spinner appears while it processes; the file becomes clickable once ready.
3. **Chat** — select the document via its checkbox, switch to the Chat tab in the AI Panel, and type your question. The AI retrieves relevant chunks and answers with source grounding.
4. **Generate a quiz** — click **Quiz** in the AI Panel. Pick difficulty and question count, optionally add a focus topic, and click **Create**. Answer all questions and submit for instant scoring.
5. **Generate flashcards** — click **Flashcards** in the AI Panel. Configure card count and difficulty, then click **Create**. Click any card to flip and reveal the answer.
6. **Generate an explainer video** — click **Video Explainer** in the AI Panel. Choose a style (Explainer, Summary, or Deep Dive) and optionally enter a focus prompt. Click **Generate Video**. The video generates asynchronously (~2–5 minutes); a live progress bar tracks each pipeline stage. When complete, the video plays directly in the centre panel.
7. **Preview documents** — click any processed file in the Content panel to open it in the centre viewer.

### Video styles

| Style     | Description                                    |
| --------- | ---------------------------------------------- |
| Explainer | Clear step-by-step walkthrough of key concepts |
| Summary   | Concise overview hitting only the highlights   |
| Deep Dive | In-depth exploration with nuance and detail    |

### Video pipeline stages

`pending` → `scripting` → `generating_images` (image mode) or `planning_visuals` → `compiling_manim` → `rendering_manim` (Manim mode) → `generating_audio` → `assembling` → `completed` / `failed`

### Example focus prompts

```
"Explain the difference between mitosis and meiosis"
"Chapter 3: thermodynamic laws and entropy"
"Key definitions in contract law"
```

---

## Project Structure

```
study-space/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api_routes.py
│   │   │   └── endpoints/
│   │   │       ├── auth_routes.py
│   │   │       ├── chat_routes.py
│   │   │       ├── flashcard_routes.py
│   │   │       ├── materials_file_routes.py
│   │   │       ├── quiz_routes.py
│   │   │       └── video_routes.py        # Video CRUD + stream/thumbnail
│   │   ├── core/                          # Config, DB, security, Celery
│   │   ├── models/
│   │   │   └── video_model.py             # GeneratedVideo ORM model
│   │   ├── schemas/
│   │   │   └── video_schema.py            # VideoScript, ManimRenderSpec, etc.
│   │   ├── services/
│   │   │   ├── video/
│   │   │   │   ├── script_generator.py    # Stage 1: Gemini script generation
│   │   │   │   ├── image_generator.py     # Stage 2a: Gemini images + Pillow fallback
│   │   │   │   ├── tts_generator.py       # Stage 3: Gemini TTS narration
│   │   │   │   ├── video_assembler.py     # Stage 4: FFmpeg assembly
│   │   │   │   ├── renderers/
│   │   │   │   │   ├── image_renderer.py  # Image-based render strategy
│   │   │   │   │   └── manim_renderer.py  # Manim-based render strategy
│   │   │   │   ├── manim_plan_generator.py
│   │   │   │   ├── manim_compiler.py      # Spec → Python Manim source
│   │   │   │   ├── manim_runner.py        # Subprocess manim CLI runner
│   │   │   │   ├── manim_spec.py          # Pydantic visual block models
│   │   │   │   ├── manim_spec_validator.py
│   │   │   │   ├── manim_templates.py     # Code-gen per block type
│   │   │   │   ├── video_generation_service.py  # Pipeline orchestrator
│   │   │   │   ├── workspace.py
│   │   │   │   ├── artifacts.py
│   │   │   │   └── health.py
│   │   │   ├── document_processor.py
│   │   │   ├── chat_service.py
│   │   │   ├── quiz_service.py
│   │   │   └── flashcard_service.py
│   │   └── tasks/
│   │       ├── material_tasks.py
│   │       ├── quiz_tasks.py
│   │       ├── flashcard_tasks.py
│   │       └── video_tasks.py             # Celery video generation task
│   ├── tests/
│   │   ├── test_manim_compiler.py
│   │   ├── test_manim_spec_validator.py
│   │   └── test_video_schema_renderer.py
│   ├── storage/
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── layout/
│       │   │   ├── StudySpaceChat.tsx     # Root component + state
│       │   │   ├── ContentPanel.tsx
│       │   │   ├── AIPanel.tsx            # Content tab + chat tab
│       │   │   └── TopNav.tsx
│       │   ├── viewers/
│       │   │   ├── DocumentViewer.tsx
│       │   │   ├── QuizViewer.tsx
│       │   │   ├── FlashcardViewer.tsx
│       │   │   └── VideoPlayer.tsx        # Progress bar + native <video>
│       │   ├── modals/
│       │   │   ├── UploadModal.tsx
│       │   │   ├── CustomizeQuizModal.tsx
│       │   │   ├── CustomizeFlashcardsModal.tsx
│       │   │   └── VideoStudioModal.tsx   # Style + focus prompt config
│       │   └── chat/
│       ├── hooks/
│       │   ├── useFiles.ts
│       │   ├── useChatSessions.ts
│       │   ├── useAIGeneration.ts
│       │   └── useVideoGeneration.ts      # Polling + video lifecycle
│       ├── lib/api/
│       │   ├── client.ts
│       │   ├── chat.ts
│       │   ├── files.ts
│       │   ├── flashcard.ts
│       │   ├── quiz.ts
│       │   └── video.ts
│       └── types/
│           ├── dashboard.ts
│           ├── quiz.ts
│           ├── flashcard.ts
│           └── video.ts
│
└── README.md
```

---

## API Details

Base URL: `http://127.0.0.1:8000/api/v1`  
Interactive docs: `http://127.0.0.1:8000/api/v1/docs`

All protected endpoints require a `Bearer <access_token>` header or an `access_token` HttpOnly cookie.

### Authentication

| Method | Endpoint        | Description                             |
| ------ | --------------- | --------------------------------------- |
| `POST` | `/auth/signup`  | Register a new user                     |
| `POST` | `/auth/login`   | Login, returns access + refresh tokens  |
| `POST` | `/auth/refresh` | Exchange a refresh token for new tokens |

### Materials

| Method | Endpoint                             | Description                                           |
| ------ | ------------------------------------ | ----------------------------------------------------- |
| `POST` | `/materials/file`                    | Upload a file (`multipart/form-data`) or submit a URL |
| `GET`  | `/materials/files`                   | List all uploaded files                               |
| `GET`  | `/materials/{file_id}/status`        | Poll processing status                                |
| `GET`  | `/materials/files/{file_id}/content` | Download raw file bytes                               |

### Chat

| Method | Endpoint                                         | Description                               |
| ------ | ------------------------------------------------ | ----------------------------------------- |
| `POST` | `/materials/chat/sessions`                       | Create a new chat session                 |
| `GET`  | `/materials/chat/sessions`                       | List all sessions                         |
| `GET`  | `/materials/chat/sessions/{session_id}/messages` | List messages                             |
| `POST` | `/materials/chat`                                | Send a message and receive an AI response |

### Quizzes

| Method | Endpoint                                             | Description                 |
| ------ | ---------------------------------------------------- | --------------------------- |
| `POST` | `/materials/quizzes`                                 | Create and queue a new quiz |
| `GET`  | `/materials/quizzes`                                 | List all quizzes            |
| `GET`  | `/materials/quizzes/{quiz_id}`                       | Get quiz detail             |
| `POST` | `/materials/quizzes/{quiz_id}/attempts`              | Submit answers              |
| `GET`  | `/materials/quizzes/{quiz_id}/attempts/{attempt_id}` | Retrieve a past attempt     |

### Flashcards

| Method | Endpoint                          | Description                 |
| ------ | --------------------------------- | --------------------------- |
| `POST` | `/materials/flashcards`           | Create and queue a new deck |
| `GET`  | `/materials/flashcards`           | List all decks              |
| `GET`  | `/materials/flashcards/{deck_id}` | Get deck detail             |

### Videos

| Method   | Endpoint                       | Description                          |
| -------- | ------------------------------ | ------------------------------------ |
| `POST`   | `/videos/generate`             | Start video generation pipeline      |
| `GET`    | `/videos`                      | List all videos for the current user |
| `GET`    | `/videos/{video_id}`           | Get video status and metadata        |
| `GET`    | `/videos/{video_id}/stream`    | Stream the generated MP4             |
| `GET`    | `/videos/{video_id}/thumbnail` | Fetch the JPEG thumbnail             |
| `DELETE` | `/videos/{video_id}`           | Delete a video and its files         |

**Generate video request:**

```json
{
  "file_ids": [3, 7],
  "style": "explainer",
  "renderer": "image",
  "focus_prompt": "Focus on photosynthesis and the Calvin cycle"
}
```

**Video status response:**

```json
{
  "id": 12,
  "status": "generating_audio",
  "progress_pct": 75,
  "title": "Photosynthesis Explained",
  "duration_seconds": null,
  "video_url": null,
  "style": "explainer",
  "renderer": "image"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js)                            │
│  Content Panel ─ Document/Quiz/Flashcard/Video Viewer               │
│  AI Panel (Chat tab + AI Content tab with Video Explainer button)   │
│  VideoStudioModal → VideoPlayer (progress bar + <video> element)    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTPS / HttpOnly Cookie (JWT)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                 │
│  /auth  /materials  /chat  /quizzes  /flashcards  /videos           │
└──────┬───────────────────────────┬───────────────────────────────────┘
       │ SQLAlchemy                 │ Celery tasks (async)
       ▼                           ▼
┌──────────────┐    ┌──────────────────────────────────────────────┐
│  PostgreSQL  │    │  Celery Worker                               │
│              │    │  ┌──────────────────────────────────────┐   │
│  users       │    │  │ Document Pipeline                    │   │
│  files       │    │  │  Docling → chunk → Pinecone upsert   │   │
│  chunks      │    │  └──────────────────────────────────────┘   │
│  sessions    │    │                                              │
│  messages    │    │  ┌──────────────────────────────────────┐   │
│  quizzes     │    │  │ Video Pipeline                       │   │
│  flashcards  │    │  │  1. Script (Gemini)                  │   │
│  videos      │    │  │  2a. Image renderer                  │   │
└──────────────┘    │  │      Gemini image → Pillow fallback  │   │
                    │  │  2b. Manim renderer                  │   │
                    │  │      Gemini plan → compile → CLI     │   │
                    │  │  3. TTS narration (Gemini TTS)       │   │
                    │  │  4. FFmpeg: mux + concat + thumbnail │   │
                    │  └──────────────────────────────────────┘   │
                    └──────┬───────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │  ← Celery broker + result backend
                    └──────┬──────┘
                           │ vector search
                           ▼
                    ┌──────────────┐
                    │   Pinecone   │  ← Integrated embedding index
                    └──────────────┘
                           │ LLM / image / TTS calls
                           ▼
                    ┌──────────────┐
                    │Google Gemini │  ← Chat, quiz, flashcard,
                    └──────────────┘    script, image gen, TTS
```

---

## Database Schema

### `users`

| Column            | Type       | Notes  |
| ----------------- | ---------- | ------ |
| `id`              | Integer PK |        |
| `username`        | String     | Unique |
| `email`           | String     | Unique |
| `hashed_password` | String     | bcrypt |

### `uploaded_files`

| Column        | Type       | Notes                                         |
| ------------- | ---------- | --------------------------------------------- |
| `id`          | Integer PK |                                               |
| `user_id`     | FK → users |                                               |
| `name`        | String     | Original filename                             |
| `stored_path` | String     | Disk path                                     |
| `url`         | String     | For web/YouTube sources                       |
| `file_type`   | Enum       | `pdf`, `notes`, `book`, etc.                  |
| `status`      | Enum       | `pending` → `processing` → `success`/`failed` |
| `uploaded_at` | DateTime   |                                               |

### `document_chunks`

| Column           | Type                | Notes                                          |
| ---------------- | ------------------- | ---------------------------------------------- |
| `id`             | Integer PK          |                                                |
| `source_file_id` | FK → uploaded_files |                                                |
| `content`        | String              | Raw chunk text                                 |
| `vector_id`      | String              | Pinecone record ID                             |
| `metadata_`      | JSON                | section_title, heading_path, chunk_index, etc. |

### `chat_sessions` / `chat_messages`

Sessions use UUID PKs and store a display name. Messages store `role` (`human` / `ai`) and `content`.

### `quizzes` / `quiz_questions` / `quiz_attempts` / `quiz_answers`

Quizzes track difficulty, question count, generation mode (`broad_full_source` or `focused_rag`), and status. Questions store four options and `correct_option`. Attempts record per-question answers and a percentage score.

### `flashcard_decks` / `flashcards`

Mirrors the quiz structure. Each `Flashcard` stores `front_text`, `back_text`, `card_order`, and an optional `source_snippet`.

### `generated_videos`

| Column                        | Type       | Notes                                                                                                                                                                   |
| ----------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                          | Integer PK |                                                                                                                                                                         |
| `user_id`                     | FK → users |                                                                                                                                                                         |
| `title`                       | String     | Set after script generation                                                                                                                                             |
| `status`                      | Enum       | `pending` → `scripting` → `generating_images` / `planning_visuals` → `compiling_manim` → `rendering_manim` → `generating_audio` → `assembling` → `completed` / `failed` |
| `progress_pct`                | Integer    | 0–100, updated at each stage                                                                                                                                            |
| `style`                       | Enum       | `explainer`, `summary`, `deep_dive`                                                                                                                                     |
| `renderer`                    | Enum       | `image`, `manim`                                                                                                                                                        |
| `script_json`                 | JSON       | Scene-by-scene script                                                                                                                                                   |
| `render_spec_json`            | JSON       | Manim render spec (Manim renderer only)                                                                                                                                 |
| `artifacts_json`              | JSON       | Registry of all generated files + stage timings                                                                                                                         |
| `source_file_ids`             | JSON       | List of source uploaded_file IDs                                                                                                                                        |
| `focus_prompt`                | String     | Optional                                                                                                                                                                |
| `video_path`                  | String     | Path to final MP4                                                                                                                                                       |
| `thumbnail_path`              | String     | Path to JPEG thumbnail                                                                                                                                                  |
| `duration_seconds`            | Float      | Total video duration                                                                                                                                                    |
| `error_message`               | String     | Populated on failure                                                                                                                                                    |
| `created_at` / `completed_at` | DateTime   |                                                                                                                                                                         |

---

## Deployment

No live deployment is currently configured. The application is designed to run locally.

**Recommended deployment targets:**

- **Backend + Celery:** Railway, Render, or a VPS with Docker Compose
- **Frontend:** Vercel (native Next.js support, zero config)
- **PostgreSQL:** Supabase, Railway, or managed RDS
- **Redis:** Upstash (serverless Redis) or Railway

> **Note on video generation in production:** The video pipeline generates multi-MB MP4 files and runs for 2–5 minutes per video. Ensure the Celery worker has sufficient CPU, memory, and disk. FFmpeg must be installed in the same environment as the worker. For high-load scenarios, consider a dedicated video worker queue.

Set `NEXT_PUBLIC_API_BASE_URL` in your frontend environment to your deployed backend URL.

---

## Testing

### Backend tests

```bash
cd backend
source venv/bin/activate
pytest
```

```bash
# With coverage
pytest --cov=app --cov-report=html
```

**What is tested:**

The test suite specifically covers the video generation pipeline:

- `test_manim_compiler.py` — verifies the `ManimTemplateCompiler` correctly generates Python Manim scene classes from a `ManimRenderSpec`, including proper class naming and block code emission.
- `test_manim_spec_validator.py` — tests `ManimSpecValidator` accepts valid specs and correctly rejects invalid ones (duplicate scene numbers, missing visual blocks, oversized content).
- `test_video_schema_renderer.py` — confirms the `VideoGenerateRequest` schema defaults to `renderer = "image"` when no renderer is specified.

### Frontend

No automated frontend tests are currently configured. Manual testing covers the full upload → chat → quiz → flashcard → video generation workflow.

---

## Future Improvements

1. **YouTube & web link processing** — The backend models support `youtube` and `web_link` file types but processing pipelines for these sources are not yet implemented.
2. **Streaming chat responses** — Switch the chat endpoint to SSE/streaming so responses appear word-by-word rather than waiting for the full completion.
3. **Spaced repetition for flashcards** — Track card performance over time and surface cards due for review using an SM-2 or FSRS algorithm.
4. **User dashboard & analytics** — Quiz attempt history, score trends, weak-topic identification, and study time tracking.
5. **Video sharing and export** — Allow users to share generated videos via a public link or download them directly from the UI.

---

## License

This project is currently unlicensed. If you intend to use or adapt this codebase, please contact the author.

---

## Contact

Built by [Your Name](https://github.com/your-username)

- GitHub: [github.com/your-username](https://github.com/your-username)
- LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)
- Email: your.email@example.com
