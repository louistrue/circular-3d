from celery import Celery
from pathlib import Path
import json
import os
import logging
from photogrammetry import PhotogrammetryProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
app = Celery('tasks', broker=redis_url, backend=redis_url)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
)

# Initialize processor
processor = PhotogrammetryProcessor()

@app.task(bind=True)
def process_photogrammetry(self, scan_id: str, zip_path: str, metadata: dict):
    """Background task to process photogrammetry"""
    
    logger.info(f"Starting photogrammetry task for scan {scan_id}")
    
    # Update task state
    self.update_state(state='PROCESSING', meta={
        'stage': 'initializing',
        'progress': 0
    })
    
    # Update scan status
    update_scan_status(scan_id, "processing", {
        "stage": "initializing",
        "progress": 0
    })
    
    try:
        # Update progress
        self.update_state(state='PROCESSING', meta={
            'stage': 'extracting_features',
            'progress': 10
        })
        update_scan_status(scan_id, "processing", {
            "stage": "extracting_features",
            "progress": 10
        })
        
        # Run photogrammetry
        result = processor.process_scan(
            scan_id=scan_id,
            zip_path=Path(zip_path),
            metadata=metadata
        )
        
        if result["status"] == "success":
            # Processing succeeded
            self.update_state(state='SUCCESS', meta={
                'stage': 'completed',
                'progress': 100,
                'models': result["models"],
                'stats': result["stats"]
            })
            
            update_scan_status(scan_id, "completed", {
                "models": result["models"],
                "stats": result["stats"],
                "photo_count": result.get("photo_count", 0)
            })
            
            logger.info(f"Photogrammetry completed for scan {scan_id}")
            return {
                'status': 'success',
                'scan_id': scan_id,
                'models': result["models"]
            }
        else:
            # Processing failed
            error_msg = result.get("error", "Unknown error")
            self.update_state(state='FAILURE', meta={
                'stage': 'failed',
                'error': error_msg
            })
            
            update_scan_status(scan_id, "failed", {
                "error": error_msg
            })
            
            logger.error(f"Photogrammetry failed for scan {scan_id}: {error_msg}")
            return {
                'status': 'failed',
                'scan_id': scan_id,
                'error': error_msg
            }
            
    except Exception as e:
        logger.error(f"Task exception for scan {scan_id}: {str(e)}")
        
        self.update_state(state='FAILURE', meta={
            'stage': 'error',
            'error': str(e)
        })
        
        update_scan_status(scan_id, "failed", {
            "error": str(e)
        })
        
        return {
            'status': 'error',
            'scan_id': scan_id,
            'error': str(e)
        }

def update_scan_status(scan_id: str, status: str, data: dict):
    """Update scan status in filesystem (should be database in production)"""
    
    # Update status file
    status_file = Path(f"uploads/{scan_id}/status.json")
    if status_file.parent.exists():
        current_status = {}
        if status_file.exists():
            with open(status_file, 'r') as f:
                current_status = json.load(f)
        
        # Update status
        from datetime import datetime
        current_status.update({
            "status": status,
            "last_updated": datetime.now().isoformat(),
            **data
        })
        
        # Write updated status
        with open(status_file, 'w') as f:
            json.dump(current_status, f, indent=2)
    
    # Also update the metadata file
    metadata_file = Path(f"uploads/{scan_id}/metadata.json")
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metadata["status"] = status
        metadata["processing_data"] = data
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

@app.task
def cleanup_old_scans(days_old: int = 7):
    """Clean up old scan files"""
    import time
    from datetime import datetime, timedelta
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        return
    
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    cleaned = 0
    
    for scan_dir in uploads_dir.iterdir():
        if scan_dir.is_dir():
            # Check modification time
            if scan_dir.stat().st_mtime < cutoff_time:
                logger.info(f"Cleaning up old scan: {scan_dir.name}")
                import shutil
                shutil.rmtree(scan_dir)
                cleaned += 1
    
    return f"Cleaned up {cleaned} old scans" 