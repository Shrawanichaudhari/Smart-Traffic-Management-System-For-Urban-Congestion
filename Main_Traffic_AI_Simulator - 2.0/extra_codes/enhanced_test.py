#!/usr/bin/env python3
"""
Enhanced test with different YOLO models and settings
"""

from ultralytics import YOLO
import cv2

def test_model(model_name, frame):
    """Test a specific YOLO model on the frame"""
    print(f"\n--- Testing {model_name} ---")
    
    try:
        model = YOLO(model_name)
        results = model(frame, conf=0.1, verbose=False)  # Very low confidence
        
        detections = {}
        total_detections = 0
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = model.names[cls_id]
                    
                    if class_name not in detections:
                        detections[class_name] = []
                    detections[class_name].append(conf)
                    total_detections += 1
        
        print(f"Total detections: {total_detections}")
        
        # Show vehicle-related detections
        vehicle_classes = ['car', 'motorcycle', 'bus', 'truck', 'bicycle', 'person']
        for vc in vehicle_classes:
            if vc in detections:
                confs = detections[vc]
                avg_conf = sum(confs) / len(confs)
                print(f"  {vc}: {len(confs)} detections (avg conf: {avg_conf:.3f})")
        
        return detections
        
    except Exception as e:
        print(f"Error with {model_name}: {e}")
        return {}

def main():
    # Load first frame
    cap = cv2.VideoCapture('test2.mp4')
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Could not read video")
        return
    
    print(f"Testing different YOLO models on your video frame...")
    print(f"Frame size: {frame.shape}")
    
    # Test different YOLO models
    models_to_test = [
        'yolov8n.pt',  # Nano (fastest, less accurate)
        'yolov8s.pt',  # Small (good balance)
        'yolov8m.pt',  # Medium (more accurate)
    ]
    
    all_results = {}
    
    for model_name in models_to_test:
        all_results[model_name] = test_model(model_name, frame)
    
    # Compare motorcycle detections
    print(f"\n{'='*50}")
    print("MOTORCYCLE DETECTION COMPARISON:")
    
    for model_name, detections in all_results.items():
        motorcycle_count = len(detections.get('motorcycle', []))
        if motorcycle_count > 0:
            avg_conf = sum(detections['motorcycle']) / len(detections['motorcycle'])
            print(f"  {model_name}: {motorcycle_count} motorcycles (avg conf: {avg_conf:.3f})")
        else:
            print(f"  {model_name}: 0 motorcycles detected")
    
    # Best model recommendation
    best_model = None
    best_count = 0
    
    for model_name, detections in all_results.items():
        motorcycle_count = len(detections.get('motorcycle', []))
        if motorcycle_count > best_count:
            best_count = motorcycle_count
            best_model = model_name
    
    if best_model and best_count > 0:
        print(f"\nRECOMMENDATION: Use {best_model} (detected {best_count} motorcycles)")
        
        # Update config suggestion
        print(f"\nTo use this model, update your configs/config.yaml:")
        print(f'model_path: "{best_model}"')
        
    else:
        print(f"\nNo motorcycles detected by any model!")
        print("This could mean:")
        print("1. The video frame doesn't contain clear motorcycles")
        print("2. Motorcycles are too small/blurred to detect")
        print("3. You might need a model trained specifically on Indian traffic")
    
    # Show what was detected instead
    print(f"\nWhat WAS detected across all models:")
    all_classes = set()
    for detections in all_results.values():
        all_classes.update(detections.keys())
    
    for class_name in sorted(all_classes):
        counts = []
        for model_name, detections in all_results.items():
            counts.append(len(detections.get(class_name, [])))
        if max(counts) > 0:
            print(f"  {class_name}: {counts} (across nano/small/medium models)")

if __name__ == '__main__':
    main()