# Circular 3D Scanner - Quick Start Guide

## 🚀 Fastest Setup (All Platforms with Docker)

```bash
# 1. Clone the repository
git clone <repository-url>
cd circular-3d

# 2. Start everything with Docker
docker-compose up -d
npm install
npm run dev

# 3. Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

## 💻 Platform-Specific Quick Start

### Windows (Using Batch Scripts)

```cmd
# 1. Clone and navigate
git clone <repository-url>
cd circular-3d

# 2. Run setup
setup.bat

# 3. Start application
start.bat
# Choose option 1 (Docker) when prompted
```

### macOS/Linux (Using Shell Scripts)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd circular-3d

# 2. Make scripts executable and run setup
chmod +x setup.sh start.sh
./setup.sh

# 3. Start application
npm run dev
```

## 📋 Prerequisites Checklist

- [ ] Git installed
- [ ] Node.js 16+ installed
- [ ] Docker Desktop installed and running
- [ ] 10GB free disk space
- [ ] Ports 8000 and 5173 available

## 🎯 First Test

1. Open http://localhost:5173
2. Upload 10+ photos of an object
3. Enter dimensions (e.g., 30x20x15 cm)
4. Click "Process Scan"
5. Wait for 3D model generation

## 🆘 Common Issues

### "Port already in use"
```bash
# Find and kill process on port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000
```

### "Docker not running"
- Start Docker Desktop application
- Wait for it to fully initialize
- Run `docker info` to verify

### "Module not found"
```bash
# Frontend fix
rm -rf node_modules package-lock.json
npm install

# Backend fix (if running locally)
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 📝 Essential Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

### Stop Everything
```bash
# Docker services
docker-compose down

# Frontend (Ctrl+C in terminal)
```

### Clean Restart
```bash
docker-compose down
docker-compose up -d
npm run dev
```

## 📚 Full Documentation

- Detailed setup: See `DEPLOYMENT_GUIDE.md`
- Photogrammetry info: See `PHOTOGRAMMETRY_SETUP.md`
- API documentation: http://localhost:8000/docs 