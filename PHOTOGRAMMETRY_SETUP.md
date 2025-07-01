# Circular 3D Scanner - Photogrammetry Setup Guide

This guide will help you set up and run the complete photogrammetry system using Docker and COLMAP.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Node.js** (v16 or higher) installed
3. **Python 3.9** installed (only if running backend locally without Docker)

## Quick Start

### 1. Pull Required Docker Images

```bash
# Pull COLMAP image
docker pull colmap/colmap:latest

# Pull Redis image
docker pull redis:7-alpine
```

### 2. Install Backend Dependencies (if running locally)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start the System with Docker Compose

From the project root directory:

```bash
# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

This will start:
- **Backend API** on http://localhost:8000
- **Redis** on localhost:6379
- **Celery Worker** for background processing

### 4. Start the Frontend

In a new terminal:

```bash
npm install  # If not already done
npm run dev
```

Frontend will be available at http://localhost:5173

## How It Works

1. **Upload Photos**: Use the frontend to upload multiple photos of an object
2. **Processing**: The backend uses COLMAP via Docker to:
   - Extract features from photos
   - Match features between photos
   - Create sparse 3D reconstruction
   - Generate 3D mesh (OBJ format)
3. **View Results**: The frontend displays the generated 3D model

## Testing the System

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

### 2. Upload Test Photos

1. Open http://localhost:5173
2. Upload 10-20 photos of an object taken from different angles
3. Enter object dimensions (length, width, height in cm)
4. Click "Generate 3D Model"

### 3. Monitor Processing

Check Docker logs:

```bash
# Backend logs
docker-compose logs -f backend

# Worker logs
docker-compose logs -f worker
```

### 4. View Processing Status

The frontend will show:
- Upload progress
- Processing status
- Final 3D model when complete

## Troubleshooting

### Docker Issues

```bash
# Restart services
docker-compose restart

# Check Docker daemon
docker ps

# View all logs
docker-compose logs

# Rebuild containers
docker-compose build --no-cache
```

### Permission Issues (Docker-in-Docker)

If you get "permission denied" errors:

```bash
# On macOS/Linux
sudo chmod 666 /var/run/docker.sock

# Or add your user to docker group
sudo usermod -aG docker $USER
```

### COLMAP Processing Fails

1. Check if photos are valid JPEG/PNG
2. Ensure minimum 10 photos for good results
3. Photos should have good overlap (60-80%)
4. Check worker logs for specific errors

### WebGL Issues in Frontend

1. Refresh the page
2. Check browser console for errors
3. Try a different browser (Chrome/Firefox recommended)

## API Endpoints

- `GET /health` - Health check
- `POST /upload/` - Upload photos ZIP
- `GET /status/{scan_id}` - Check processing status
- `GET /model/{scan_id}?format=obj` - Download 3D model
- `GET /task/{task_id}` - Check Celery task status

## Tips for Better Results

1. **Photo Requirements**:
   - Take 20-50 photos for best results
   - Move around the object in a circle
   - Overlap photos by 60-80%
   - Good lighting, avoid shadows
   - Keep object in focus

2. **Object Types**:
   - Works best with textured objects
   - Avoid reflective/transparent surfaces
   - Stationary objects only

3. **Processing Time**:
   - 10-20 photos: 2-5 minutes
   - 20-50 photos: 5-15 minutes
   - Depends on photo resolution

## Development

### Run Backend Locally (without Docker)

```bash
cd backend
source venv/bin/activate

# Start Redis (in Docker)
docker run -p 6379:6379 redis:7-alpine

# Start Celery worker
celery -A tasks worker --loglevel=info

# Start FastAPI (in another terminal)
python main.py
```

### View Celery Tasks

```bash
# Monitor tasks in real-time
celery -A tasks flower
# Open http://localhost:5555
```

## Production Considerations

1. Use a proper database (PostgreSQL) instead of in-memory storage
2. Set up persistent volumes for Docker
3. Configure HTTPS for API
4. Add authentication/authorization
5. Use cloud storage (S3) for files
6. Scale workers based on load

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Clean up old files
rm -rf backend/uploads/*
rm -rf backend/processing/*
``` 