@echo off
echo ========================================
echo Circular 3D Scanner - Windows Setup
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://docker.com
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo [OK] Docker is installed and running
echo.

REM Pull Docker images
echo Pulling Docker images...
docker pull colmap/colmap:latest
docker pull redis:7-alpine

REM Create directories
echo Creating required directories...
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\processing" mkdir "backend\processing"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Python is not installed or not in PATH
    echo Backend will run in Docker only
) else (
    echo [OK] Python is installed
    echo Setting up Python virtual environment...
    cd backend
    if not exist "venv" (
        python -m venv venv
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
    ) else (
        echo [OK] Virtual environment already exists
    )
    cd ..
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Node.js is installed
echo.

REM Install frontend dependencies
echo Installing frontend dependencies...
call npm install

REM Start Docker services
echo Starting Docker services...
docker-compose up -d

REM Wait for services
echo Waiting for services to start...
timeout /t 5 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo ERROR: Some services failed to start
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Backend services are running:
echo - API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Redis: localhost:6379
echo.
echo To start the frontend:
echo   npm run dev
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
pause 