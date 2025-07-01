# Circular 3D Scanner - Deployment Guide

This guide provides detailed instructions for setting up and running the Circular 3D Scanner project on a new PC. The project includes a React frontend, FastAPI backend, and uses COLMAP for photogrammetry processing.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start (Automated)](#quick-start-automated)
3. [Manual Setup](#manual-setup)
4. [Docker Setup](#docker-setup)
5. [Verification Steps](#verification-steps)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum (16GB recommended for processing)
- **Storage**: 10GB free space
- **CPU**: Multi-core processor (4+ cores recommended)
- **GPU**: Optional but recommended for faster COLMAP processing

### Software Requirements
- **Git**: For cloning the repository
- **Node.js**: Version 16 or higher
- **Python**: Version 3.9 or higher
- **Docker Desktop**: Latest version (for Docker deployment)
- **Web Browser**: Chrome, Firefox, or Edge (latest versions)

## Quick Start (Automated)

### Option 1: Using Setup Script (macOS/Linux)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd circular-3d
   ```

2. **Make scripts executable**:
   ```bash
   chmod +x setup.sh start.sh
   ```

3. **Run setup**:
   ```bash
   ./setup.sh
   ```

4. **Start the application**:
   ```bash
   # For Docker deployment
   npm run dev  # Frontend will start automatically

   # For local deployment (without Docker)
   ./start.sh
   ```

### Option 2: Using Docker Compose (All Platforms)

1. **Clone and navigate to project**:
   ```bash
   git clone <repository-url>
   cd circular-3d
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   npm install
   npm run dev
   ```

## Manual Setup

### Step 1: Install Prerequisites

#### Windows
```powershell
# Install Node.js from https://nodejs.org/
# Install Python from https://python.org/
# Install Docker Desktop from https://docker.com/

# Verify installations
node --version
python --version
docker --version
```

#### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python@3.9
brew install --cask docker

# Verify installations
node --version
python3 --version
docker --version
```

#### Linux (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python
sudo apt install -y python3.9 python3.9-venv python3-pip

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone Repository
```bash
git clone <repository-url>
cd circular-3d
```

### Step 3: Backend Setup

#### Create Python Virtual Environment
```bash
cd backend
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
cd ..
```

### Step 4: Frontend Setup
```bash
# Install Node dependencies
npm install
```

### Step 5: Docker Images (for photogrammetry)
```bash
docker pull colmap/colmap:latest
docker pull redis:7-alpine
```

### Step 6: Create Required Directories
```bash
mkdir -p backend/uploads
mkdir -p backend/processing
```

## Docker Setup

### Full Docker Deployment

1. **Ensure Docker is running**:
   ```bash
   docker info
   ```

2. **Build and start all services**:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. **Check services status**:
   ```bash
   docker-compose ps
   ```

4. **Start frontend separately**:
   ```bash
   npm install
   npm run dev
   ```

### Docker Service Details

The `docker-compose.yml` starts:
- **Backend API**: Port 8000
- **Redis**: Port 6379 (for task queue)
- **Celery Worker**: Background processing
- **COLMAP**: Available for photogrammetry tasks

## Running the Application

### Method 1: Using Start Script (Local)
```bash
./start.sh
```

### Method 2: Manual Start (Local)

1. **Terminal 1 - Redis**:
   ```bash
   docker run -p 6379:6379 redis:7-alpine
   ```

2. **Terminal 2 - Backend**:
   ```bash
   cd backend
   source venv/bin/activate  # Windows: venv\Scripts\activate
   python main.py
   ```

3. **Terminal 3 - Celery Worker**:
   ```bash
   cd backend
   source venv/bin/activate  # Windows: venv\Scripts\activate
   celery -A tasks worker --loglevel=info
   ```

4. **Terminal 4 - Frontend**:
   ```bash
   npm run dev
   ```

### Method 3: Docker + Frontend
```bash
# Start backend services with Docker
docker-compose up -d

# Start frontend
npm run dev
```

## Verification Steps

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### 2. Check API Documentation
Open: http://localhost:8000/docs

### 3. Check Frontend
Open: http://localhost:5173

### 4. Check Docker Services
```bash
docker-compose ps
# All services should show "Up" status
```

### 5. Test Upload Flow
1. Navigate to http://localhost:5173
2. Upload sample photos (10+ images)
3. Enter dimensions (e.g., 30x20x15 cm)
4. Click "Process Scan"
5. Monitor progress

## Environment Variables

### Backend (.env file in backend/)
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Processing Configuration
MAX_UPLOAD_SIZE=500000000  # 500MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
```

### Frontend (src/utils/api.js)
```javascript
const API_BASE_URL = 'http://localhost:8000'  // Change for production
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill process or change port in configuration
```

#### Docker Permission Denied
```bash
# Linux only
sudo chmod 666 /var/run/docker.sock
# OR
sudo usermod -aG docker $USER
newgrp docker
```

#### Python Module Not Found
```bash
# Ensure virtual environment is activated
# Re-install requirements
pip install -r requirements.txt
```

#### Node Modules Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### COLMAP Processing Fails
- Ensure minimum 10 photos uploaded
- Check photo quality and overlap
- Verify Docker has enough memory allocated
- Check worker logs: `docker-compose logs worker`

### Viewing Logs

#### Docker Services
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f redis
```

#### Local Services
Check terminal output for each service

## Production Deployment

### Backend Deployment

1. **Update configuration**:
   - Set production database
   - Configure cloud storage (S3/GCS)
   - Set secure Redis password
   - Enable HTTPS

2. **Docker Production Build**:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Deploy to Cloud**:
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances
   - Kubernetes

### Frontend Deployment

1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Deploy options**:
   - **Static hosting**: Netlify, Vercel, GitHub Pages
   - **CDN**: CloudFront, Cloudflare
   - **Container**: Nginx Docker image

3. **Update API endpoint**:
   ```javascript
   // src/utils/api.js
   const API_BASE_URL = 'https://api.your-domain.com'
   ```

### Security Considerations

1. **API Security**:
   - Add authentication (JWT/OAuth)
   - Implement rate limiting
   - Enable CORS properly
   - Use HTTPS only

2. **File Upload Security**:
   - Validate file types
   - Limit file sizes
   - Scan for malware
   - Use secure storage

3. **Infrastructure**:
   - Use environment variables
   - Secure database connections
   - Monitor and log activities
   - Regular security updates

## Maintenance

### Regular Tasks
```bash
# Clean up old files (weekly)
rm -rf backend/uploads/*
rm -rf backend/processing/*

# Update dependencies (monthly)
cd backend && pip install --upgrade -r requirements.txt
cd .. && npm update

# Backup data
docker-compose exec redis redis-cli BGSAVE

# Check disk space
df -h
```

### Monitoring
- Set up health check endpoints
- Monitor Redis memory usage
- Track processing times
- Check error logs regularly

## Support

For issues:
1. Check logs for error messages
2. Verify all services are running
3. Test with sample data
4. Check GitHub issues
5. Contact support team

---

**Note**: This guide assumes basic familiarity with terminal/command line usage. For Windows users, consider using PowerShell or WSL2 for better compatibility with bash scripts. 