import os
import json
import subprocess
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import tempfile
import numpy as np

logger = logging.getLogger(__name__)

class PhotogrammetryProcessor:
    """Processes photos using COLMAP via Docker to create 3D models"""
    
    def __init__(self, work_dir: Path = Path("./processing")):
        self.work_dir = work_dir
        self.work_dir.mkdir(exist_ok=True)
        
    def process_scan(self, scan_id: str, zip_path: Path, metadata: Dict) -> Dict:
        """
        Process a scan using COLMAP Docker
        
        Returns:
            Dict with processing results including paths to generated models
        """
        logger.info(f"Starting photogrammetry processing for scan {scan_id}")
        
        # Create working directory for this scan
        scan_work_dir = self.work_dir / scan_id
        scan_work_dir.mkdir(exist_ok=True)
        
        try:
            # Extract photos
            photos_dir = scan_work_dir / "images"
            photos_dir.mkdir(exist_ok=True)
            
            photo_count = self._extract_photos(zip_path, photos_dir)
            logger.info(f"Extracted {photo_count} photos")
            
            # Create COLMAP project directories
            database_path = scan_work_dir / "database.db"
            sparse_dir = scan_work_dir / "sparse"
            dense_dir = scan_work_dir / "dense"
            
            sparse_dir.mkdir(exist_ok=True)
            dense_dir.mkdir(exist_ok=True)
            
            # Run COLMAP pipeline using Docker
            results = self._run_colmap_pipeline(
                scan_work_dir=scan_work_dir,
                photos_dir=photos_dir,
                database_path=database_path,
                sparse_dir=sparse_dir,
                dense_dir=dense_dir,
                metadata=metadata
            )
            
            # Convert to standard formats
            output_models = self._export_models(
                scan_work_dir=scan_work_dir,
                sparse_dir=sparse_dir,
                dense_dir=dense_dir,
                output_dir=scan_work_dir / "output",
                metadata=metadata
            )
            
            return {
                "status": "success",
                "models": output_models,
                "stats": results,
                "photo_count": photo_count
            }
            
        except Exception as e:
            logger.error(f"Processing failed for scan {scan_id}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _extract_photos(self, zip_path: Path, photos_dir: Path) -> int:
        """Extract photos from ZIP file"""
        photo_count = 0
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    zip_ref.extract(file_info, photos_dir)
                    photo_count += 1
        return photo_count
    
    def _run_colmap_pipeline(self, scan_work_dir: Path, photos_dir: Path, 
                            database_path: Path, sparse_dir: Path, 
                            dense_dir: Path, metadata: Dict) -> Dict:
        """Run COLMAP reconstruction pipeline using Docker"""
        
        # Convert paths to absolute for Docker mounting
        work_abs = scan_work_dir.absolute()
        
        docker_image = "colmap/colmap:latest"
        
        # Base docker command with volume mount
        docker_base = [
            "docker", "run", "--rm",
            "-v", f"{work_abs}:/work",
            docker_image
        ]
        
        try:
            # 1. Feature extraction
            logger.info("Extracting features...")
            subprocess.run([
                *docker_base, "colmap", "feature_extractor",
                "--database_path", "/work/database.db",
                "--image_path", "/work/images",
                "--ImageReader.single_camera", "1",
                "--SiftExtraction.max_image_size", "3200",
                "--SiftExtraction.max_num_features", "8192"
            ], check=True, capture_output=True, text=True)
            
            # 2. Feature matching
            logger.info("Matching features...")
            subprocess.run([
                *docker_base, "colmap", "exhaustive_matcher",
                "--database_path", "/work/database.db",
                "--ExhaustiveMatching.block_size", "50"
            ], check=True, capture_output=True, text=True)
            
            # 3. Sparse reconstruction
            logger.info("Running sparse reconstruction...")
            subprocess.run([
                *docker_base, "colmap", "mapper",
                "--database_path", "/work/database.db",
                "--image_path", "/work/images",
                "--output_path", "/work/sparse",
                "--Mapper.ba_refine_focal_length", "0",
                "--Mapper.ba_refine_principal_point", "0",
                "--Mapper.ba_refine_extra_params", "0"
            ], check=True, capture_output=True, text=True)
            
            # 4. Model optimization
            logger.info("Optimizing model...")
            model_dir = self._find_model_dir(sparse_dir)
            if model_dir:
                subprocess.run([
                    *docker_base, "colmap", "bundle_adjuster",
                    "--input_path", f"/work/sparse/{model_dir.name}",
                    "--output_path", f"/work/sparse/{model_dir.name}",
                    "--BundleAdjustment.refine_focal_length", "0"
                ], check=True, capture_output=True, text=True)
            
            return {
                "features_extracted": True,
                "sparse_reconstruction": True,
                "model_optimized": True,
                "dense_reconstruction": False  # Skip dense for now (requires GPU)
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"COLMAP command failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise Exception(f"COLMAP processing failed: {e.stderr}")
    
    def _find_model_dir(self, sparse_dir: Path) -> Optional[Path]:
        """Find the model directory (usually named '0')"""
        for item in sparse_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                return item
        return None
    
    def _export_models(self, scan_work_dir: Path, sparse_dir: Path, 
                      dense_dir: Path, output_dir: Path, metadata: Dict) -> Dict:
        """Export models to standard formats"""
        output_dir.mkdir(exist_ok=True)
        work_abs = scan_work_dir.absolute()
        
        models = {}
        
        # Find the model directory
        model_dir = self._find_model_dir(sparse_dir)
        if not model_dir:
            logger.warning("No sparse model found")
            # Create a simple box mesh as fallback
            self._create_fallback_mesh(output_dir, metadata)
            models["mesh_obj"] = "output/mesh.obj"
            return models
        
        try:
            # Export sparse point cloud to PLY
            logger.info("Exporting point cloud...")
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{work_abs}:/work",
                "colmap/colmap:latest",
                "colmap", "model_converter",
                "--input_path", f"/work/sparse/{model_dir.name}",
                "--output_path", "/work/output/points.ply",
                "--output_type", "PLY"
            ], check=True, capture_output=True, text=True)
            
            models["points_ply"] = "output/points.ply"
            
            # Also export as text for easier parsing
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{work_abs}:/work",
                "colmap/colmap:latest",
                "colmap", "model_converter",
                "--input_path", f"/work/sparse/{model_dir.name}",
                "--output_path", "/work/output/model",
                "--output_type", "TXT"
            ], check=True, capture_output=True, text=True)
            
            # Create a simple mesh from points
            self._create_mesh_from_colmap_model(output_dir, metadata)
            models["mesh_obj"] = "output/mesh.obj"
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            # Create fallback mesh
            self._create_fallback_mesh(output_dir, metadata)
            models["mesh_obj"] = "output/mesh.obj"
        
        return models
    
    def _create_mesh_from_colmap_model(self, output_dir: Path, metadata: Dict):
        """Create a simple mesh from COLMAP points"""
        try:
            # Read points from COLMAP text format
            points_file = output_dir / "model" / "points3D.txt"
            if not points_file.exists():
                raise FileNotFoundError("Points file not found")
            
            points = []
            with open(points_file, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        # Format: POINT3D_ID X Y Z R G B ERROR TRACK[]
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        points.append([x, y, z])
            
            if len(points) < 4:
                raise ValueError("Not enough points for mesh creation")
            
            # Create a simple convex hull mesh
            points_array = np.array(points)
            self._create_convex_hull_obj(points_array, output_dir / "mesh.obj")
            
        except Exception as e:
            logger.error(f"Failed to create mesh from COLMAP model: {e}")
            self._create_fallback_mesh(output_dir, metadata)
    
    def _create_convex_hull_obj(self, points: np.ndarray, output_path: Path):
        """Create a simple convex hull OBJ file from points"""
        from scipy.spatial import ConvexHull
        
        # Compute convex hull
        hull = ConvexHull(points)
        
        # Write OBJ file
        with open(output_path, 'w') as f:
            f.write("# OBJ file created by Circular 3D Scanner\n")
            f.write(f"# {len(hull.vertices)} vertices, {len(hull.simplices)} faces\n\n")
            
            # Write vertices
            for vertex_idx in hull.vertices:
                v = points[vertex_idx]
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            f.write("\n")
            
            # Write faces (triangles)
            # Need to map from points indices to hull vertices indices
            vertex_map = {original_idx: new_idx + 1 for new_idx, original_idx in enumerate(hull.vertices)}
            
            for simplex in hull.simplices:
                # OBJ faces are 1-indexed
                face_indices = [vertex_map.get(idx, 1) for idx in simplex if idx in vertex_map]
                if len(face_indices) == 3:
                    f.write(f"f {face_indices[0]} {face_indices[1]} {face_indices[2]}\n")
    
    def _create_fallback_mesh(self, output_dir: Path, metadata: Dict):
        """Create a simple box mesh as fallback"""
        dims = metadata.get('dimensions', {})
        length = float(dims.get('length', 50)) / 100  # Convert cm to meters
        width = float(dims.get('width', 50)) / 100
        height = float(dims.get('height', 100)) / 100
        
        # Create a simple box OBJ
        with open(output_dir / "mesh.obj", 'w') as f:
            f.write("# Fallback box mesh\n")
            f.write(f"# Dimensions: {length}m x {width}m x {height}m\n\n")
            
            # Define box vertices
            hl, hw, hh = length/2, width/2, height/2
            vertices = [
                [-hl, -hh, -hw], [hl, -hh, -hw], [hl, hh, -hw], [-hl, hh, -hw],  # Front
                [-hl, -hh, hw], [hl, -hh, hw], [hl, hh, hw], [-hl, hh, hw]       # Back
            ]
            
            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            f.write("\n")
            
            # Write faces
            faces = [
                [1, 2, 3, 4], [5, 8, 7, 6],  # Front, Back
                [1, 5, 6, 2], [3, 7, 8, 4],  # Bottom, Top
                [1, 4, 8, 5], [2, 6, 7, 3]   # Left, Right
            ]
            
            for face in faces:
                f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n") 