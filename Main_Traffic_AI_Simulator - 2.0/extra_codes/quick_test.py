#!/usr/bin/env python3
"""
Quick test to see what YOLO detects in your video
"""

from ultralytics import YOLO
import cv2

# Load YOLO
model = YOLO('yolov8n.pt')

# Test on your video
cap = cv2.VideoCapture('test2.mp4')
ret, frame = cap.read()

if ret:
    # Run detection
    results = model(frame, conf=0.2)
    
    # Count detections by class
    class_counts = {}
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                
                if class_name not in class_counts:
                    class_counts[class_name] = 0
                class_counts[class_name] += 1
    
    print("What YOLO detected in first frame:")
    for class_name, count in sorted(class_counts.items()):
        print(f"  {class_name}: {count}")
    
    # Check specifically for motorcycle
    if 'motorcycle' in class_counts:
        print(f"\n✓ Found {class_counts['motorcycle']} motorcycles!")
    else:
        print(f"\n✗ No motorcycles detected")
        print("Available vehicle classes in this frame:")
        vehicle_classes = ['car', 'motorcycle', 'bus', 'truck', 'bicycle', 'person']
        for vc in vehicle_classes:
            if vc in class_counts:
                print(f"  {vc}: {class_counts[vc]}")

else:
    print("Could not read video frame")

cap.release()