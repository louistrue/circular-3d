#!/bin/bash

# Circular 3D Scanner - Startup Script
echo "🚀 Starting Circular 3D Scanner..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Check if required ports are available
echo -e "${BLUE}Checking ports...${NC}"

if ! check_port 8000; then
    echo -e "${RED}❌ Port 8000 is already in use (FastAPI backend)${NC}"
    echo -e "${YELLOW}Please stop the process using port 8000 or change the backend port${NC}"
    exit 1
fi

if ! check_port 5173; then
    echo -e "${RED}❌ Port 5173 is already in use (Vite frontend)${NC}"
    echo -e "${YELLOW}Please stop the process using port 5173 or change the frontend port${NC}"
    exit 1
fi

# Create virtual environment for backend if it doesn't exist
if [ ! -d "backend-example/venv" ]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    cd backend-example
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo -e "${GREEN}✅ Python virtual environment found${NC}"
fi

# Start backend server in background
echo -e "${BLUE}Starting FastAPI backend on port 8000...${NC}"
cd backend-example
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if check_port 8000; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
else
    echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID)${NC}"
fi

# Start frontend server
echo -e "${BLUE}Starting React frontend on port 5173...${NC}"
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if check_port 5173; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 1
else
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Circular 3D Scanner is now running!${NC}"
echo ""
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:5173"
echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait 