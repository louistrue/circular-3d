# FastAPI Backend for Circular 3D Scanner

A simple FastAPI backend that works with the React frontend for circular 3D scanning.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- pip

### Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Open browser** to `http://localhost:8000` for API docs

## 📚 API Endpoints

- `GET /` - API information
- `POST /upload/` - Upload ZIP file with photos and metadata  
- `GET /status/{scan_id}` - Get scan processing status
- `GET /download/{scan_id}` - Download processed scan
- `GET /scans/` - List all scans
- `DELETE /scans/{scan_id}` - Delete a scan
- `GET /stats` - System statistics
- `GET /health` - Health check

## 🔧 Configuration

### CORS Settings
The backend is configured to accept requests from:
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`

### File Storage
- Uploaded files are stored in `uploads/` directory
- Each scan gets a unique UUID folder
- ZIP files and metadata are preserved

## 📁 Directory Structure

```
uploads/
├── uuid-1/
│   ├── photos.zip
│   └── metadata.json
├── uuid-2/
│   ├── photos.zip
│   └── metadata.json
└── ...
```

## 🔄 Development

This is a simplified backend for prototyping. For production:
- Add database integration (PostgreSQL, MongoDB)
- Implement actual 3D processing pipeline
- Add authentication and authorization
- Add file validation and virus scanning
- Implement proper error logging
- Add rate limiting and security headers 