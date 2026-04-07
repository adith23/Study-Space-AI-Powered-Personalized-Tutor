# Study Space - AI-Powered Personalized Tutor

An AI-powered learning platform with:
- FastAPI backend for auth, materials, and chat APIs
- React + TypeScript + Vite frontend
- Async document processing with Celery + Redis
- PostgreSQL for application data
- Pinecone + embeddings for retrieval

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Celery
- Redis
- LangChain + Google Gemini + Pinecone

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis

## Project Structure

```text
backend/   FastAPI app, Celery tasks, DB models
frontend/  React + Vite app
```

## Environment Configuration

Backend settings are loaded from `backend/.env` (see `backend/app/core/config.py`).

Create `backend/.env` with at least:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/StudySpace
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=your_gemini_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=study-space-index
PINECONE_ENVIRONMENT=gcp-starter
```

## Backend Setup and Run

From the repository root:

### Windows (CMD)

```bat
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Windows (PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Linux/macOS

```bash
cd backend
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend API:
- Base URL: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/api/v1/docs`

## Celery Worker (Required for file processing)

Run Redis first, then in a new terminal:

sudo service redis-server start


### Windows (CMD / PowerShell)

```bat
cd backend
venv\Scripts\activate
celery -A app.core.celery_worker.celery_app worker --loglevel=info --pool=threads
```

### Linux/macOS

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_worker.celery_app worker --loglevel=info
```

## Frontend Setup and Run

From the repository root:

```bash
cd frontend
npm install

cd frontend
npm run dev
```

Frontend URL:
- `http://localhost:5173`

## Common Dev Commands

### Backend tests

```bash
cd backend
pytest
```

### Frontend build

```bash
cd frontend
npm run build
```