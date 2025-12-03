# Frontend-Backend Integration Guide

## Quick Start

Your Echosense AI frontend is now integrated with the backend! Here's how to get started:

### 1. Start the Backend Server

```bash
cd C:\Users\siddh\OneDrive\Desktop\echosenseai\echosense-ai\backend
python main.py
```

The backend will start at `http://localhost:8000`

### 2. Access the Application

Open your browser and navigate to:
- **Landing Page**: `http://localhost:8000/static/index.html`
- **Dashboard**: `http://localhost:8000/static/dashboard.html`
- **Upload**: `http://localhost:8000/static/upload.html`

## Features

### Dashboard (`dashboard.html`)
- View overall statistics (total calls, processed calls, avg quality score, compliance flags)
- Quality trends chart showing performance over the last 30 days
- Recent calls table with quick access to call details
- Real-time data from backend API

### Upload (`upload.html`)
- Drag-and-drop audio file upload
- Supported formats: MP3, WAV, M4A, OGG, FLAC
- Maximum file size: 100MB
- Progress indicator during upload
- Automatic redirect to call details after successful upload

### Call Details (`call-details.html`)
- Complete call information
- Quality scores breakdown (overall, politeness, clarity, empathy, resolution)
- Full transcript with speaker diarization
- Sentiment analysis for each transcript segment
- Compliance flags with severity levels

## API Endpoints

The frontend connects to these backend endpoints:

- `POST /api/upload/audio` - Upload audio files
- `GET /api/processing/status/{call_id}` - Get processing status
- `GET /api/processing/full-report/{call_id}` - Get complete call analysis
- `GET /api/analytics/dashboard` - Get dashboard statistics
- `GET /api/analytics/recent-calls` - Get recent calls list
- `GET /api/analytics/quality-trends` - Get quality trends data

## Project Structure

```
echosense-ai/
├── backend/
│   ├── api/              # API endpoints
│   ├── database/         # Database connections
│   ├── services/         # Business logic
│   ├── models.py         # Data models
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI application
├── frontend/
│   ├── js/
│   │   └── api.js        # API client
│   ├── index.html        # Landing page
│   ├── dashboard.html    # Analytics dashboard
│   ├── upload.html       # File upload page
│   ├── call-details.html # Call details view
│   ├── about.html        # About page
│   ├── contact.html      # Contact page
│   └── getstared.html    # Features page
└── ai-models/            # AI/ML models
```

## Next Steps

1. **Set up databases**: Configure PostgreSQL and MongoDB as per the main README
2. **Configure environment**: Update `.env` file with your API keys and database credentials
3. **Test upload**: Try uploading a sample audio file
4. **Verify processing**: Check that the call appears in the dashboard
5. **View details**: Click on a processed call to see the full analysis

## Troubleshooting

### Backend not starting
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version (3.11 or 3.12 recommended)
- Check database connections in `.env`

### Frontend not loading
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify CORS is enabled in backend

### Upload failing
- Check file format (must be audio file)
- Verify file size (max 100MB)
- Ensure backend has write permissions for file storage
- Check MinIO/S3 configuration

## Development

To modify the frontend:
1. Edit HTML/CSS/JS files in `frontend/` directory
2. Refresh browser to see changes (no build step required)
3. API client is in `frontend/js/api.js`

To modify the backend:
1. Edit Python files in `backend/` directory
2. Restart the server to apply changes
3. Use `--reload` flag for auto-reload during development:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Support

For issues or questions, refer to the main project README or contact the development team.
