from celery import Celery
from pathlib import Path
import json
import os
import logging
from photogrammetry import PhotogrammetryProcessor
from datetime import datetime, timedelta

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

# Bind task to self for status updates
class CallbackTask(app.Task):
    def on_success(self, retval, task_id, args, kwargs):
        """Success handler."""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Error handler."""
        logger.error(f"Task {task_id} failed with exception: {exc}")

@app.task(bind=True, base=CallbackTask)
def process_photogrammetry(self, scan_id: str, zip_path: str, metadata: dict):
    """
    Process photogrammetry scan using COLMAP
    """
    logger.info(f"Starting photogrammetry task for scan {scan_id}")
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 'Initializing processor...'})
        
        # Initialize processor
        processor = PhotogrammetryProcessor()
        
        # Create a progress callback
        def update_progress(message):
            self.update_state(state='PROGRESS', meta={'current': message})
        
        # Process the scan with progress updates
        self.update_state(state='PROGRESS', meta={'current': 'Extracting photos from ZIP...'})
        
        # Run photogrammetry processing
        result = processor.process_scan(
            scan_id=scan_id,
            zip_path=Path(zip_path),
            metadata=metadata
        )
        
        # Update scan status
        scan_dir = Path("uploads") / scan_id
        status_file = scan_dir / "status.json"
        
        status_data = {
            "status": "completed" if result["status"] == "success" else "failed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        }
        
        with status_file.open("w") as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Photogrammetry completed for scan {scan_id}")
        
        return {
            "status": result["status"],
            "scan_id": scan_id,
            "models": result.get("models", {})
        }
        
    except Exception as e:
        logger.error(f"Photogrammetry failed for scan {scan_id}: {str(e)}")
        
        # Update scan status
        scan_dir = Path("uploads") / scan_id
        status_file = scan_dir / "status.json"
        
        status_data = {
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        }
        
        with status_file.open("w") as f:
            json.dump(status_data, f, indent=2)
        
        raise

@app.task
def cleanup_old_scans():
    """
    Clean up old scan files (older than 7 days)
    """
    logger.info("Starting cleanup of old scans")
    
    cutoff_date = datetime.now() - timedelta(days=7)
    cleaned_count = 0
    
    for directory in [Path("uploads"), Path("processing")]:
        if not directory.exists():
            continue
            
        for scan_dir in directory.iterdir():
            if not scan_dir.is_dir():
                continue
                
            # Check metadata file for creation date
            metadata_file = scan_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with metadata_file.open("r") as f:
                        metadata = json.load(f)
                    
                    created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                    if created_at < cutoff_date:
                        # Delete the directory
                        import shutil
                        shutil.rmtree(scan_dir)
                        cleaned_count += 1
                        logger.info(f"Deleted old scan: {scan_dir.name}")
                        
                except Exception as e:
                    logger.error(f"Error processing {scan_dir}: {e}")
    
    logger.info(f"Cleanup completed. Deleted {cleaned_count} old scans")
    return {"cleaned_count": cleaned_count}

# Schedule periodic cleanup
app.conf.beat_schedule = {
    'cleanup-old-scans': {
        'task': 'tasks.cleanup_old_scans',
        'schedule': timedelta(hours=24),
    },
} 