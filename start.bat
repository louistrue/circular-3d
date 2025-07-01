@echo off
echo ========================================
echo Starting Circular 3D Scanner
echo ========================================
echo.

REM Check if ports are available
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% eq 0 (
    echo ERROR: Port 8000 is already in use
    echo Please stop the process using port 8000
    pause
    exit /b 1
)

netstat -an | findstr ":5173" | findstr "LISTENING" >nul
if %errorlevel% eq 0 (
    echo ERROR: Port 5173 is already in use
    echo Please stop the process using port 5173
    pause
    exit /b 1
)

echo [OK] Required ports are available
echo.

REM Check if using Docker or local backend
echo Select backend mode:
echo 1. Docker (recommended)
echo 2. Local Python
echo.
set /p mode="Enter choice (1 or 2): "

if "%mode%"=="1" (
    echo Starting Docker services...
    docker-compose up -d
    
    REM Wait for services
    timeout /t 5 /nobreak >nul
    
    REM Check if services are running
    docker-compose ps | findstr "Up" >nul
    if %errorlevel% neq 0 (
        echo ERROR: Docker services failed to start
        echo Check logs with: docker-compose logs
        pause
        exit /b 1
    )
    
    echo [OK] Docker services started
) else if "%mode%"=="2" (
    echo Starting local backend services...
    
    REM Start Redis in Docker
    start "Redis" cmd /c "docker run -p 6379:6379 redis:7-alpine"
    
    REM Start Backend
    cd backend
    if exist "venv\Scripts\activate.bat" (
        start "FastAPI Backend" cmd /c "call venv\Scripts\activate.bat && python main.py"
        
        REM Start Celery Worker
        start "Celery Worker" cmd /c "call venv\Scripts\activate.bat && celery -A tasks worker --loglevel=info"
    ) else (
        echo ERROR: Python virtual environment not found
        echo Please run setup.bat first
        pause
        exit /b 1
    )
    cd ..
    
    echo [OK] Local backend services started
) else (
    echo Invalid choice
    pause
    exit /b 1
)

REM Wait for backend to be ready
echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend...
start "React Frontend" cmd /k "npm run dev"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Circular 3D Scanner is running!
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services...
pause >nul

REM Cleanup
echo.
echo Stopping services...

if "%mode%"=="1" (
    docker-compose down
) else (
    REM Stop local services
    taskkill /FI "WindowTitle eq Redis*" /F >nul 2>&1
    taskkill /FI "WindowTitle eq FastAPI Backend*" /F >nul 2>&1
    taskkill /FI "WindowTitle eq Celery Worker*" /F >nul 2>&1
)

taskkill /FI "WindowTitle eq React Frontend*" /F >nul 2>&1

echo [OK] All services stopped
pause 