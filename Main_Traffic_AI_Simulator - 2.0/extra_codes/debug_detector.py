#!/usr/bin/env python3
"""
Debug script to check what the detector is actually detecting.
Run this to see the raw YOLO detections before our filtering.
"""

import cv2
import sys
import os
sys.path.append('src')

from ultralytics import YOLO
import yaml

# Load model
model = YOLO('yolov8n.pt')

# Load our config to see mappings
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print("Our class mapping from config:")
for original, mapped in config['class_mapping'].items():
    print(f"  {original} -> {mapped}")

print("\n" + "="*50)

# Test on multiple frames to see what's detected
video_path = 'test2.mp4'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Could not open video: {video_path}")
    exit(1)

print(f"Video properties:")
print(f"  FPS: {cap.get(cv2.CAP_PROP_FPS)}")
print(f"  Total frames: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")
print(f"  Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

# Test on first 5 frames
frame_count = 0
all_detected_classes = {}

while frame_count < 5:
    ret, frame = cap.read()
    if not ret:
        break
    
    print(f"\n--- FRAME {frame_count} ---")
    
    # Run detection with low confidence to see everything
    results = model(frame, conf=0.1, verbose=False)
    
    frame_detections = []
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls_id]
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Track all detected classes
                if class_name not in all_detected_classes:
                    all_detected_classes[class_name] = 0
                all_detected_classes[class_name] += 1
                
                # Show details for vehicle-related classes
                if class_name in ['car', 'motorcycle', 'motorbike', 'bus', 'truck', 'bicycle', 'person', 'train']:
                    bbox_width = x2 - x1
                    bbox_height = y2 - y1
                    print(f"  {class_name}: conf={conf:.3f}, size={bbox_width:.0f}x{bbox_height:.0f}")
                    
                    # Check if it would be filtered by our mapping
                    vehicle_type = config['class_mapping'].get(class_name)
                    if vehicle_type:
                        print(f"    -> Mapped to: {vehicle_type}")
                    else:
                        print(f"    -> NOT MAPPED (would be ignored)")
    
    frame_count += 1

print(f"\n" + "="*50)
print("SUMMARY - All classes detected across frames:")
for class_name, count in sorted(all_detected_classes.items()):
    vehicle_type = config['class_mapping'].get(class_name)
    status = f"-> {vehicle_type}" if vehicle_type else "-> NOT MAPPED"
    print(f"  {class_name}: {count} detections {status}")

print(f"\n" + "="*50)
print("YOLO model class names (vehicle-related):")
vehicle_related = ['car', 'motorcycle', 'motorbike', 'bus', 'truck', 'bicycle', 'person', 'train']
for i, name in model.names.items():
    if name in vehicle_related:
        print(f"  {i}: {name}")

# Check what's in the video visually
print(f"\n" + "="*50)
print("Showing first frame with all detections...")

cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
ret, frame = cap.read()
if ret:
    results = model(frame, conf=0.2, verbose=False)
    
    display_frame = frame.copy()
    detection_count = 0
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                
                # Draw all detections
                color = (0, 255, 0)  # Green for all
                if class_name in ['motorcycle', 'motorbike']:
                    color = (0, 0, 255)  # Red for motorcycles
                elif class_name == 'car':
                    color = (255, 0, 0)  # Blue for cars
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name} {conf:.2f}"
                cv2.putText(display_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                detection_count += 1
    
    print(f"Drew {detection_count} detections on frame")
    cv2.imwrite('debug_detections.jpg', display_frame)
    print("Saved debug_detections.jpg - check this image to see what YOLO detected")

cap.release()
print("\nRun this and check what classes are actually detected!")
