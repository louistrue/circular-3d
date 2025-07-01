from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import uvicorn
import logging
from tasks import process_photogrammetry, app as celery_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Circular 3D Scanner API",
    description="Backend API for circular 3D scanning with photo upload and processing",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create processing directory
PROCESSING_DIR = Path("processing")
PROCESSING_DIR.mkdir(exist_ok=True)

# In-memory storage for scan metadata (use database in production)
scans_db = {}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Circular 3D Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload/",
            "download": "GET /download/{scan_id}",
            "status": "GET /status/{scan_id}",
            "model": "GET /model/{scan_id}",
            "task_status": "GET /task/{task_id}",
            "scans": "GET /scans/",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Redis connection
    redis_status = "unknown"
    try:
        celery_app.backend.get('test')
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "processing_dir": str(PROCESSING_DIR.absolute()),
        "processing_dir_exists": PROCESSING_DIR.exists(),
        "redis_status": redis_status
    }

@app.post("/upload/")
async def upload_scan(
    zipfile: UploadFile = File(..., description="ZIP file containing photos"),
    metadata: str = Form(..., description="JSON metadata about the scan")
):
    """
    Upload a ZIP file with photos and metadata for 3D scanning
    """
    try:
        # Parse metadata
        scan_metadata = json.loads(metadata)
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Create scan directory
        scan_dir = UPLOAD_DIR / scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        
        # Save ZIP file
        zip_path = scan_dir / "photos.zip"
        with zip_path.open("wb") as buffer:
            shutil.copyfileobj(zipfile.file, buffer)
        
        # Create scan record
        scan_record = {
            "uuid": scan_id,
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "filename": zipfile.filename,
            "file_size": zip_path.stat().st_size,
            "metadata": scan_metadata,
            "processing_started": False,
            "processing_completed": False,
            "task_id": None
        }
        
        # Save metadata to file
        metadata_path = scan_dir / "metadata.json"
        with metadata_path.open("w") as f:
            json.dump(scan_record, f, indent=2)
        
        # Store in memory (use database in production)
        scans_db[scan_id] = scan_record
        
        # Start background photogrammetry processing
        logger.info(f"Starting photogrammetry processing for scan {scan_id}")
        task = process_photogrammetry.delay(
            scan_id=scan_id,
            zip_path=str(zip_path),
            metadata=scan_metadata
        )
        
        # Update scan record with task ID
        scans_db[scan_id]["status"] = "processing"
        scans_db[scan_id]["processing_started"] = True
        scans_db[scan_id]["task_id"] = task.id
        
        # Update metadata file
        scan_record["status"] = "processing"
        scan_record["processing_started"] = True
        scan_record["task_id"] = task.id
        with metadata_path.open("w") as f:
            json.dump(scan_record, f, indent=2)
        
        return {
            "uuid": scan_id,
            "status": "processing",
            "message": "Scan uploaded successfully and photogrammetry processing started",
            "file_size": scan_record["file_size"],
            "photo_count": scan_metadata.get("photoCount", 0),
            "task_id": task.id
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/status/{scan_id}")
async def get_scan_status(scan_id: str):
    """
    Get the status of a scan by ID
    """
    if scan_id not in scans_db:
        # Try to load from disk
        metadata_path = UPLOAD_DIR / scan_id / "metadata.json"
        if metadata_path.exists():
            with metadata_path.open("r") as f:
                scans_db[scan_id] = json.load(f)
        else:
            raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scans_db[scan_id]
    
    # Check status file for updates
    status_file = UPLOAD_DIR / scan_id / "status.json"
    if status_file.exists():
        with status_file.open("r") as f:
            status_data = json.load(f)
            scan["status"] = status_data.get("status", scan["status"])
            scan["processing_data"] = status_data
    
    # Check task status if available
    if scan.get("task_id"):
        task_result = celery_app.AsyncResult(scan["task_id"])
        scan["task_status"] = task_result.status
        scan["task_info"] = task_result.info
    
    return {
        "uuid": scan_id,
        "status": scan["status"],
        "created_at": scan["created_at"],
        "completed_at": scan.get("completed_at"),
        "metadata": scan["metadata"],
        "processing_data": scan.get("processing_data", {}),
        "task_status": scan.get("task_status"),
        "task_info": scan.get("task_info")
    }

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "info": task_result.info,
        "ready": task_result.ready(),
        "successful": task_result.successful(),
        "failed": task_result.failed()
    }

@app.get("/model/{scan_id}")
async def get_3d_model(scan_id: str, format: str = "obj"):
    """
    Get the generated 3D model
    
    Args:
        scan_id: The scan UUID
        format: Model format (obj, ply)
    """
    
    # Check if scan exists
    if scan_id not in scans_db:
        metadata_path = UPLOAD_DIR / scan_id / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Scan not found")
    
    # Check for model files
    output_dir = PROCESSING_DIR / scan_id / "output"
    
    if format == "obj":
        model_file = output_dir / "mesh.obj"
    elif format == "ply":
        model_file = output_dir / "points.ply"
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'obj' or 'ply'")
    
    if not model_file.exists():
        raise HTTPException(status_code=404, detail=f"Model file not found. Processing may still be in progress.")
    
    return FileResponse(
        path=model_file,
        filename=f"model_{scan_id}.{format}",
        media_type=f"model/{format}"
    )

@app.get("/download/{scan_id}")
async def download_scan(scan_id: str):
    """
    Download the original uploaded ZIP file
    """
    if scan_id not in scans_db:
        metadata_path = UPLOAD_DIR / scan_id / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_dir = UPLOAD_DIR / scan_id
    zip_path = scan_dir / "photos.zip"
    
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Scan file not found")
    
    return FileResponse(
        path=zip_path,
        filename=f"scan_{scan_id}.zip",
        media_type="application/zip"
    )

@app.get("/scans/")
async def list_scans(limit: Optional[int] = 10):
    """
    Get list of all scans with pagination
    """
    # Load all scans from disk
    all_scans = {}
    
    for scan_dir in UPLOAD_DIR.iterdir():
        if scan_dir.is_dir():
            metadata_path = scan_dir / "metadata.json"
            if metadata_path.exists():
                with metadata_path.open("r") as f:
                    scan_data = json.load(f)
                    all_scans[scan_dir.name] = scan_data
    
    # Merge with in-memory data
    all_scans.update(scans_db)
    
    scans_list = list(all_scans.values())
    
    # Sort by creation date (newest first)
    scans_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply limit
    if limit:
        scans_list = scans_list[:limit]
    
    return {
        "scans": scans_list,
        "total": len(all_scans),
        "limit": limit
    }

@app.delete("/scans/{scan_id}")
async def delete_scan(scan_id: str):
    """
    Delete a scan and its associated files
    """
    if scan_id not in scans_db:
        metadata_path = UPLOAD_DIR / scan_id / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Scan not found")
    
    # Remove upload files
    scan_dir = UPLOAD_DIR / scan_id
    if scan_dir.exists():
        shutil.rmtree(scan_dir)
    
    # Remove processing files
    processing_dir = PROCESSING_DIR / scan_id
    if processing_dir.exists():
        shutil.rmtree(processing_dir)
    
    # Remove from memory
    if scan_id in scans_db:
        del scans_db[scan_id]
    
    return {"message": f"Scan {scan_id} deleted successfully"}

@app.get("/stats")
async def get_stats():
    """
    Get system statistics
    """
    # Load all scans
    all_scans = {}
    for scan_dir in UPLOAD_DIR.iterdir():
        if scan_dir.is_dir():
            metadata_path = scan_dir / "metadata.json"
            if metadata_path.exists():
                with metadata_path.open("r") as f:
                    all_scans[scan_dir.name] = json.load(f)
    
    all_scans.update(scans_db)
    
    total_scans = len(all_scans)
    completed_scans = sum(1 for scan in all_scans.values() if scan.get("status") == "completed")
    processing_scans = sum(1 for scan in all_scans.values() if scan.get("status") == "processing")
    failed_scans = sum(1 for scan in all_scans.values() if scan.get("status") == "failed")
    
    # Calculate total storage used
    total_size = 0
    for directory in [UPLOAD_DIR, PROCESSING_DIR]:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
    
    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "processing_scans": processing_scans,
        "failed_scans": failed_scans,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / 1024 / 1024, 2),
        "upload_directory": str(UPLOAD_DIR.absolute()),
        "processing_directory": str(PROCESSING_DIR.absolute())
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 