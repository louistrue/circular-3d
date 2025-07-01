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
        
    def process_scan(self, scan_id: str, zip_path: Path, metadata: Dict, progress_callback=None) -> Dict:
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
            
            # Try to run COLMAP pipeline, but fallback if it fails
            try:
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
                
            except Exception as colmap_error:
                logger.warning(f"COLMAP processing failed: {str(colmap_error)}")
                logger.info("Creating fallback model based on dimensions...")
                
                # Create output directory and fallback model
                output_dir = scan_work_dir / "output"
                output_dir.mkdir(exist_ok=True)
                self._create_fallback_mesh(output_dir, metadata)
                
                output_models = {"mesh_obj": "output/mesh.obj"}
                results = {
                    "features_extracted": False,
                    "sparse_reconstruction": False,
                    "model_optimized": False,
                    "dense_reconstruction": False,
                    "fallback_model": True,
                    "error": str(colmap_error)
                }
            
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
        
        # For Docker-in-Docker, we need to use the host path
        host_processing_path = os.getenv('HOST_PROCESSING_PATH', '/app/processing')
        if host_processing_path and host_processing_path != '/app/processing':
            # Convert container path to host path
            relative_path = work_abs.relative_to(Path('/app/processing'))
            host_work_path = Path(host_processing_path) / relative_path
            # Normalize Windows paths for Docker
            host_work_str = str(host_work_path).replace('\\', '/')
        else:
            host_work_str = str(work_abs)
        
        # Use COLMAP image with MKL support or fallback to official image
        docker_image = os.getenv('COLMAP_IMAGE', 'colmap-cpu:latest')
        logger.info(f"Using COLMAP image: {docker_image}")
        logger.info(f"Mounting host path: {host_work_str}")
        
        # Base docker command with volume mount
        docker_base = [
            "docker", "run", "--rm",
            "-v", f"{host_work_str}:/work",
            docker_image
        ]
        
        try:
            # 1. Feature extraction
            logger.info("Extracting features...")
            subprocess.run([
                *docker_base, "feature_extractor",
                "--database_path", "/work/database.db",
                "--image_path", "/work/images",
                "--ImageReader.single_camera", "1",
                "--SiftExtraction.use_gpu", "0",
                "--SiftExtraction.max_image_size", "3200",
                "--SiftExtraction.max_num_features", "8192"
            ], check=True, capture_output=True, text=True)
            
            # 2. Feature matching
            logger.info("Matching features...")
            subprocess.run([
                *docker_base, "exhaustive_matcher",
                "--database_path", "/work/database.db",
                "--SiftMatching.use_gpu", "0",
                "--ExhaustiveMatching.block_size", "50"
            ], check=True, capture_output=True, text=True)
            
            # 3. Sparse reconstruction
            logger.info("Running sparse reconstruction...")
            subprocess.run([
                *docker_base, "mapper",
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
                    *docker_base, "bundle_adjuster",
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
        
        # Get the docker image
        docker_image = os.getenv('COLMAP_IMAGE', 'colmap-cpu:latest')
        
        # For Docker-in-Docker, we need to use the host path
        host_processing_path = os.getenv('HOST_PROCESSING_PATH', '/app/processing')
        if host_processing_path and host_processing_path != '/app/processing':
            # Convert container path to host path
            relative_path = work_abs.relative_to(Path('/app/processing'))
            host_work_path = Path(host_processing_path) / relative_path
            # Normalize Windows paths for Docker
            host_work_str = str(host_work_path).replace('\\', '/')
        else:
            host_work_str = str(work_abs)
        
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
                "-v", f"{host_work_str}:/work",
                docker_image,
                "model_converter",
                "--input_path", f"/work/sparse/{model_dir.name}",
                "--output_path", "/work/output/points.ply",
                "--output_type", "PLY"
            ], check=True, capture_output=True, text=True)
            
            models["points_ply"] = "output/points.ply"
            
            # Also export as text for easier parsing
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{host_work_str}:/work",
                docker_image,
                "model_converter",
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
            # First try to read from PLY file if it exists
            ply_file = output_dir / "points.ply"
            if ply_file.exists():
                logger.info(f"Reading points from PLY file: {ply_file}")
                points = self._read_points_from_ply(ply_file)
                if len(points) >= 4:
                    self._create_convex_hull_obj(points, output_dir / "mesh.obj")
                    return
            
            # Try to read points from COLMAP text format
            points_file = output_dir / "model" / "points3D.txt"
            if not points_file.exists():
                # Try the direct output path
                points_file = output_dir.parent / "sparse" / "0" / "points3D.txt"
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
    
    def _read_points_from_ply(self, ply_file: Path) -> np.ndarray:
        """Read points from PLY file"""
        points = []
        with open(ply_file, 'rb') as f:
            # Read header
            header_end = False
            vertex_count = 0
            format_binary = False
            properties = []
            
            while not header_end:
                line = f.readline().decode('ascii').strip()
                if line.startswith('format binary'):
                    format_binary = True
                elif line.startswith('element vertex'):
                    vertex_count = int(line.split()[-1])
                elif line.startswith('property'):
                    properties.append(line.split()[2])  # property name
                elif line == 'end_header':
                    header_end = True
            
            logger.info(f"PLY file has {vertex_count} vertices with properties: {properties}")
            
            if format_binary:
                # Binary format - COLMAP typically outputs x,y,z as floats and r,g,b as uchar
                import struct
                for i in range(vertex_count):
                    # Read x, y, z as floats (12 bytes)
                    xyz_data = f.read(12)
                    if len(xyz_data) == 12:
                        x, y, z = struct.unpack('<fff', xyz_data)
                        points.append([x, y, z])
                        # Skip RGB data (3 bytes for COLMAP output)
                        f.read(3)
            else:
                # ASCII format
                for i in range(vertex_count):
                    line = f.readline().decode('ascii').strip()
                    if line:
                        values = line.split()
                        if len(values) >= 3:
                            x, y, z = float(values[0]), float(values[1]), float(values[2])
                            points.append([x, y, z])
        
        return np.array(points) if points else np.array([]).reshape(0, 3)
    
    def _create_convex_hull_obj(self, points: np.ndarray, output_path: Path):
        """Create a simple convex hull OBJ file from points"""
        try:
            from scipy.spatial import ConvexHull
            
            # Normalize points to reasonable scale
            center = points.mean(axis=0)
            points_centered = points - center
            scale = np.abs(points_centered).max()
            if scale > 0:
                points_normalized = points_centered / scale * 2  # Scale to -2 to 2 range
            else:
                points_normalized = points_centered
            
            # Compute convex hull
            hull = ConvexHull(points_normalized)
            
            # Write OBJ file
            with open(output_path, 'w') as f:
                f.write("# OBJ file created by Circular 3D Scanner\n")
                f.write(f"# Generated from {len(points)} COLMAP points\n")
                f.write(f"# {len(hull.vertices)} vertices, {len(hull.simplices)} faces\n\n")
                
                # Write vertices
                for vertex_idx in hull.vertices:
                    v = points_normalized[vertex_idx]
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                
                f.write("\n")
                
                # Write faces (triangles)
                # Need to map from points indices to hull vertices indices
                vertex_map = {original_idx: new_idx + 1 for new_idx, original_idx in enumerate(hull.vertices)}
                
                for simplex in hull.simplices:
                    # OBJ faces are 1-indexed
                    face_indices = [vertex_map.get(idx, 1) for idx in simplex if idx in vertex_map]
                    if len(face_indices) == 3:
                        f.write(f"f {face_indices[0]} {face_indices[1]} {face_indices[2]}\n")
                        
            logger.info(f"Created convex hull mesh with {len(hull.vertices)} vertices and {len(hull.simplices)} faces")
            
        except ImportError:
            logger.error("scipy not available, creating simple point cloud OBJ")
            # Fallback: create point cloud OBJ
            with open(output_path, 'w') as f:
                f.write("# Point cloud OBJ file\n")
                f.write(f"# {len(points)} points from COLMAP\n\n")
                
                # Normalize and write vertices
                center = points.mean(axis=0)
                points_centered = points - center
                scale = np.abs(points_centered).max()
                if scale > 0:
                    points_normalized = points_centered / scale * 2
                else:
                    points_normalized = points_centered
                    
                for p in points_normalized:
                    f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
    
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