# Echosense AI

> Intelligent Call Monitoring AI System

Echosense AI is an advanced call monitoring system that uses AI to transcribe, analyze, and score customer service calls. It provides real-time insights into call quality, sentiment analysis, and performance metrics.

## Features

- **Voice Transcription**: Automatic speech-to-text using Whisper AI
- **Sentiment Analysis**: Real-time sentiment detection and scoring
- **Call Quality Scoring**: Automated scoring based on multiple criteria
- **Performance Analytics**: Comprehensive dashboards and reports
- **Compliance Monitoring**: Keyword detection and compliance checking
- **Fast Processing**: Under 8-minute turnaround time for call analysis

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11+**: Core programming language
- **PostgreSQL**: Primary database for structured data
- **MongoDB**: Analytics and logging database
- **Redis**: Task queue and caching
- **Celery**: Asynchronous task processing

### AI/ML
- **OpenAI Whisper**: Speech-to-text transcription
- **Transformers**: NLP and sentiment analysis
- **PyAnnote**: Speaker diarization
- **Sentence Transformers**: Semantic analysis

### Storage
- **MinIO/AWS S3**: Audio file storage

## Project Structure

```
echosense-ai/
├── backend/              # FastAPI backend application
│   ├── api/             # API route handlers
│   ├── database/        # Database connections and models
│   ├── services/        # Business logic services
│   ├── models.py        # SQLAlchemy models
│   ├── config.py        # Configuration management
│   └── main.py          # Application entry point
├── ai-models/           # AI/ML model implementations
│   ├── whisper_stt.py   # Speech-to-text model
│   ├── sentiment.py     # Sentiment analysis
│   └── scoring.py       # Call scoring logic
├── frontend/            # Frontend application (if applicable)
├── docker/              # Docker configuration files
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Getting Started

### Prerequisites

- Python 3.11 or 3.12 (Python 3.14 has compatibility issues with some audio libraries)
- PostgreSQL 14+
- MongoDB 6+
- Redis 7+
- MinIO (for local development) or AWS S3 account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/echosense-ai.git
   cd echosense-ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Start required services**
   
   Using Docker Compose (recommended):
   ```bash
   docker-compose up -d postgres mongodb redis minio
   ```

   Or install services individually on your system.

5. **Run database migrations**
   ```bash
   # From backend directory
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   python main.py
   ```

   The server will start at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/echosense
MONGODB_URL=mongodb://localhost:27017/echosense_analytics

# Storage
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AI Models
OPENAI_API_KEY=your_openai_api_key
WHISPER_MODEL_SIZE=base

# Application
BACKEND_PORT=8000
DEBUG=True
```

## Development

### Running in Development Mode

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest
```

### Code Style

This project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

## Deployment

### Using Docker

```bash
docker-compose up -d
```

### Manual Deployment

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Known Limitations

- Python 3.14 compatibility issues with audio processing libraries (`pyaudioop`)
- Requires external services (PostgreSQL, MongoDB, Redis, MinIO/S3)
- Audio processing features require Python 3.11 or 3.12

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Roadmap

- [ ] Real-time call monitoring
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Custom scoring models
- [ ] Integration with popular CRM systems

## Acknowledgments

- OpenAI Whisper for speech recognition
- FastAPI for the excellent web framework
- The open-source community for various tools and libraries
