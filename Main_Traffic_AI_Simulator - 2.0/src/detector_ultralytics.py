"""
Vehicle Detection Module using Ultralytics YOLOv8/YOLOv7
More stable alternative to the original YOLOv7 implementation.
"""

import cv2
import numpy as np
from typing import List, Dict, Any
import yaml

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    print("Ultralytics not available, falling back to basic detection")


class VehicleDetectorUltralytics:
    """Ultralytics YOLO-based vehicle detector with configurable class mapping."""
    
    def __init__(self, config_path: str):
        """
        Initialize detector with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model_path = self.config.get('model_path', 'yolov8n.pt')
        self.conf_threshold = self.config['conf_threshold']
        self.class_mapping = self.config['class_mapping']
        self.emergency_labels = set(self.config['emergency_labels'])
        self.emergency_color_threshold = self.config['emergency_color_threshold']
        
        # Load model
        self.model = self._load_model()
        
        # COCO class names (same as YOLOv7/v8)
        self.coco_classes = [
            'person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train',
            'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
            'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
            'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
            'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
            'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
            'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
            'sofa', 'pottedplant', 'bed', 'diningtable', 'toilet', 'tvmonitor',
            'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
            'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
            'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
    
    def _load_model(self):
        """Load YOLO model using Ultralytics."""
        if not ULTRALYTICS_AVAILABLE:
            raise ImportError("Ultralytics YOLO not available. Install with: pip install ultralytics")
        
        try:
            print(f"Loading model: {self.model_path}")
            model = YOLO(self.model_path)
            print("Model loaded successfully!")
            return model
        except Exception as e:
            print(f"Error loading model {self.model_path}: {e}")
            print("Trying to download YOLOv8n model...")
            try:
                model = YOLO('yolov8n.pt')  # This will auto-download
                print("YOLOv8n model downloaded and loaded!")
                return model
            except Exception as e2:
                print(f"Failed to load any model: {e2}")
                raise
    
    def _detect_emergency_by_color(self, image: np.ndarray, bbox: List[int]) -> bool:
        """
        Detect emergency vehicles by color heuristics (red/blue in top region).
        
        Args:
            image: Original frame
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            True if emergency colors detected above threshold
        """
        x1, y1, x2, y2 = bbox
        
        # Extract vehicle region
        vehicle_patch = image[y1:y2, x1:x2]
        if vehicle_patch.size == 0:
            return False
        
        # Focus on top 20% of the vehicle (where sirens usually are)
        top_height = max(1, int((y2 - y1) * 0.2))
        top_patch = vehicle_patch[:top_height, :]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(top_patch, cv2.COLOR_BGR2HSV)
        
        # Define red and blue color ranges in HSV
        # Red (two ranges due to HSV wrap-around)
        red_lower1 = np.array([0, 100, 100])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([160, 100, 100])
        red_upper2 = np.array([180, 255, 255])
        
        # Blue
        blue_lower = np.array([100, 100, 100])
        blue_upper = np.array([130, 255, 255])
        
        # Create masks
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
        
        # Combine emergency color masks
        emergency_mask = cv2.bitwise_or(red_mask, blue_mask)
        
        # Calculate ratio of emergency colors
        total_pixels = top_patch.shape[0] * top_patch.shape[1]
        emergency_pixels = np.sum(emergency_mask > 0)
        emergency_ratio = emergency_pixels / total_pixels
        
        return emergency_ratio > self.emergency_color_threshold
    
    def run_on_frame(self, image: np.ndarray, frame_idx: int) -> List[Dict[str, Any]]:
        """
        Run detection on a single frame.
        
        Args:
            image: Input frame (BGR format)
            frame_idx: Frame index for tracking
            
        Returns:
            List of detection dictionaries
        """
        # Run inference with lower confidence for better detection
        results = self.model(image, conf=max(0.25, self.conf_threshold), verbose=False)
        
        # Process results
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                # Extract box data
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls_id = int(box.cls[0].cpu().numpy())
                
                # Filter by confidence (use the configured threshold)
                if conf < self.conf_threshold:
                    continue
                
                # Map class to vehicle type
                cls_name = self.coco_classes[cls_id] if cls_id < len(self.coco_classes) else 'unknown'
                vehicle_type = self.class_mapping.get(cls_name)
                
                # Skip non-vehicle classes
                if vehicle_type is None:
                    continue
                
                # Filter out very small detections (likely noise)
                bbox_width = x2 - x1
                bbox_height = y2 - y1
                if bbox_width < 20 or bbox_height < 20:
                    continue
                
                # Convert coordinates to integers
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Calculate center
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                # Detect emergency vehicles - ONLY use explicit class labels
                is_emergency = vehicle_type in self.emergency_labels
                
                # Debug info
                if frame_idx % 50 == 0 and len(detections) < 3:  # Print first few detections every 50 frames
                    print(f"Frame {frame_idx}: Detected {cls_name} -> {vehicle_type}, conf={conf:.2f}, emergency={is_emergency}")
                
                detection_obj = {
                    "frame": frame_idx,
                    "track_id": None,  # Will be assigned by tracker
                    "class": vehicle_type,
                    "conf": float(conf),
                    "bbox": [x1, y1, x2, y2],
                    "center": [cx, cy],
                    "is_emergency": is_emergency,
                    "original_class": cls_name  # Keep original YOLO class for debugging
                }
                
                detections.append(detection_obj)
        
        return detections


def load_detector(config_path: str):
    """
    Convenience function to load detector with config.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Initialized VehicleDetectorUltralytics
    """
    return VehicleDetectorUltralytics(config_path)