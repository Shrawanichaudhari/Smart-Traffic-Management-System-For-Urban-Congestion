#!/usr/bin/env python3
"""
Visual debugging tool to see what YOLO detects and how tracking works
"""

import cv2
import sys
import os
sys.path.append('src')

from ultralytics import YOLO
import yaml
import numpy as np

def resize_frame_for_display(frame, max_width=1200, max_height=800):
    """Resize frame to fit on screen properly"""
    height, width = frame.shape[:2]
    
    # Calculate scaling factor
    scale_w = max_width / width
    scale_h = max_height / height
    scale = min(scale_w, scale_h, 1.0)  # Don't upscale
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized = cv2.resize(frame, (new_width, new_height))
        return resized, scale
    else:
        return frame, 1.0

def draw_detections(frame, results, model):
    """Draw all YOLO detections on frame"""
    display_frame = frame.copy()
    detections_info = []
    
    # Define colors for different classes
    colors = {
        'car': (255, 0, 0),        # Blue
        'motorcycle': (0, 0, 255), # Red  
        'bus': (0, 255, 255),      # Yellow
        'truck': (255, 0, 255),    # Magenta
        'bicycle': (0, 255, 0),    # Green
        'person': (255, 255, 0),   # Cyan
    }
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                # Get detection info
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                
                # Get color for this class
                color = colors.get(class_name, (128, 128, 128))  # Gray for unknown
                
                # Draw bounding box
                thickness = 3 if class_name in ['motorcycle', 'bicycle'] else 2
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
                
                # Draw label with confidence
                label = f"{class_name} {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(display_frame, (x1, y1-label_size[1]-10), 
                             (x1+label_size[0], y1), color, -1)
                cv2.putText(display_frame, label, (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Store detection info
                detections_info.append({
                    'class': class_name,
                    'conf': conf,
                    'bbox': [x1, y1, x2, y2],
                    'center': [(x1+x2)//2, (y1+y2)//2]
                })
    
    return display_frame, detections_info

def main():
    # Load model
    print("Loading YOLO model...")
    model = YOLO('yolov8n.pt')
    
    # Load config
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Open video
    video_path = 'test4.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return
    
    # Get video properties
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Video properties: {original_width}x{original_height} at {fps} FPS")
    print(f"Controls:")
    print("  'q' = quit")
    print("  'p' = pause/unpause") 
    print("  's' = save current frame")
    print("  SPACE = next frame (when paused)")
    print("  'r' = restart video")
    print("\nColors: Blue=Car, Red=Motorcycle, Green=Bicycle, Yellow=Bus, Magenta=Truck, Cyan=Person")
    
    frame_count = 0
    paused = False
    
    # Create window with specific size
    cv2.namedWindow('YOLO Detection Debug', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('YOLO Detection Debug', 1200, 800)
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("End of video - press 'r' to restart or 'q' to quit")
                key = cv2.waitKey(0) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue
            frame_count += 1
        
        # Run YOLO detection with low confidence
        results = model(frame, conf=0.15, verbose=False)  # Low confidence to catch everything
        
        # Draw detections
        display_frame, detections_info = draw_detections(frame, results, model)
        
        # Resize for display
        display_frame, scale = resize_frame_for_display(display_frame)
        
        # Print detection summary to console
        class_counts = {}
        for det in detections_info:
            class_name = det['class']
            if class_name not in class_counts:
                class_counts[class_name] = 0
            class_counts[class_name] += 1
        
        if frame_count % 30 == 1:  # Print every 30 frames
            print(f"\nFrame {frame_count} detections:", end=" ")
            for class_name, count in class_counts.items():
                vehicle_type = config['class_mapping'].get(class_name, 'UNMAPPED')
                print(f"{class_name}({count})", end=" ")
            if not class_counts:
                print("Nothing detected")
        
        # Add frame info to display
        info_y = 30
        cv2.putText(display_frame, f"Frame {frame_count} | Total: {len(detections_info)}", 
                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show vehicle counts
        info_y += 30
        for class_name in ['car', 'motorcycle', 'bus', 'truck', 'bicycle', 'person']:
            count = class_counts.get(class_name, 0)
            if count > 0:
                color = (0, 0, 255) if class_name == 'motorcycle' else (255, 255, 255)
                cv2.putText(display_frame, f"{class_name}: {count}", 
                           (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                info_y += 25
        
        # Show pause status
        if paused:
            cv2.putText(display_frame, "PAUSED - Press SPACE for next frame", 
                       (10, display_frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Display frame
        cv2.imshow('YOLO Detection Debug', display_frame)
        
        # Handle key presses
        wait_time = 50 if not paused else 0  # Slower playback for better viewing
        key = cv2.waitKey(wait_time) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
            print(f"{'Paused' if paused else 'Resumed'}")
        elif key == ord(' ') and paused:  # Space bar for next frame when paused
            continue
        elif key == ord('s'):
            # Save current frame
            filename = f'debug_frame_{frame_count}.jpg'
            cv2.imwrite(filename, frame)  # Save original frame
            cv2.imwrite(f'debug_annotated_{frame_count}.jpg', display_frame)  # Save annotated
            print(f"Saved {filename} and debug_annotated_{frame_count}.jpg")
        elif key == ord('r'):
            # Restart video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_count = 0
            paused = False
            print("Video restarted")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\nDebugging complete!")

if __name__ == '__main__':
    main()
