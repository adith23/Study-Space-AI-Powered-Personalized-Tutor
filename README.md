# Study Space - AI-Powered Personalized Tutor

An intelligent learning platform that provides personalized study materials, interactive quizzes, and adaptive learning experiences powered by AI.

## Features

- AI-powered content processing and analysis
- Personalized learning paths
- Interactive quizzes and flashcards
- Real-time study sessions
- Progress tracking and analytics
- Multi-format content support (PDF, Video, Text)
- Adaptive difficulty adjustment
- Visual learning aids and mind maps

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL
- Redis
- Celery
- SQLAlchemy
- Pydantic
- Alembic

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- Redux Toolkit
- WebSocket

### AI/ML
- OpenAI GPT
- Anthropic Claude
- Custom ML models
- Embedding models
- Vision models

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/study-space.git
cd study-space
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development environment:
```bash
docker-compose up -d
```

4. Access the applications:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements/dev.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models