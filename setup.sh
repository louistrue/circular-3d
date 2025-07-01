#!/bin/bash

echo "🚀 Setting up Circular 3D Scanner with Photogrammetry..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"

# Pull required images
echo "📦 Pulling Docker images..."
docker pull colmap/colmap:latest
docker pull redis:7-alpine

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads
mkdir -p backend/processing

# Install backend dependencies (if running locally)
if [ -d "backend/venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "🐍 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose build
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install

echo ""
echo "✨ Setup complete! ✨"
echo ""
echo "To start the system:"
echo "1. Backend is already running on http://localhost:8000"
echo "2. Start the frontend with: npm run dev"
echo ""
echo "To monitor logs:"
echo "- Backend: docker-compose logs -f backend"
echo "- Worker: docker-compose logs -f worker"
echo ""
echo "📖 See PHOTOGRAMMETRY_SETUP.md for detailed instructions" 