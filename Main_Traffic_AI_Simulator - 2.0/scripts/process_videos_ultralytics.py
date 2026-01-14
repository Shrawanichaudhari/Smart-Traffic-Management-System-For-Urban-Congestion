#!/usr/bin/env python3
"""
CLI script to process videos with vehicle detection and tracking using Ultralytics YOLO.
More stable version that works with modern Python versions.
"""

import argparse
import cv2
import json
import os
import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from detector_ultralytics import VehicleDetectorUltralytics as VehicleDetector
except ImportError:
    print("Error: Could not import ultralytics detector. Trying original...")
    from detector import VehicleDetector

from tracker import VehicleTracker, create_tracker


def process_single_video(
    video_path: str, 
    detector: VehicleDetector, 
    tracker: VehicleTracker,
    output_dir: str,
    max_frames: int = None,
    show_display: bool = False
) -> Dict[str, Any]:
    """
    Process a single video file.
    
    Args:
        video_path: Path to video file
        detector: Initialized detector
        tracker: Initialized tracker  
        output_dir: Output directory
        max_frames: Maximum frames to process (None for all)
        show_display: Whether to show annotated frames
        
    Returns:
        Processing statistics
    """
    print(f"Processing video: {video_path}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if max_frames:
        total_frames = min(total_frames, max_frames)
    
    print(f"Video FPS: {fps}, Total frames to process: {total_frames}")
    
    # Prepare output files
    video_name = Path(video_path).stem
    detections_list = []
    summary_data = []
    
    # Vehicle type categories for counting (including rickshaw)
    vehicle_types = ['car', 'motorbike', 'bus', 'truck', 'bicycle', 'train', 'rickshaw', 'ambulance', 'fire_truck']
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or (max_frames and frame_idx >= max_frames):
            break
        
        # Calculate timestamp
        timestamp = frame_idx / fps if fps > 0 else frame_idx
        
        # Run detection
        try:
            detections = detector.run_on_frame(frame, frame_idx)
        except Exception as e:
            print(f"Detection error on frame {frame_idx}: {e}")
            detections = []
        
        # Update tracker
        tracked_detections = tracker.update(detections, frame_idx)
        
        # Store detailed detections
        for detection in tracked_detections:
            detection['timestamp'] = timestamp
            detection['video'] = video_name
            detections_list.append(detection.copy())
        
        # Generate frame summary
        frame_summary = {
            'frame': frame_idx,
            'timestamp': timestamp,
            'video': video_name
        }
        
        # Count vehicles by type
        for vehicle_type in vehicle_types:
            count_key = f'count_{vehicle_type}'
            frame_summary[count_key] = sum(1 for d in tracked_detections if d['class'] == vehicle_type)
        
        # Count emergency vehicles
        frame_summary['emergency_count'] = sum(1 for d in tracked_detections if d['is_emergency'])
        frame_summary['total_vehicles'] = len(tracked_detections)
        
        summary_data.append(frame_summary)
        
        # Display annotated frame if requested
        if show_display:
            display_frame = frame.copy()
            for detection in tracked_detections:
                bbox = detection['bbox']
                center = detection['center']
                
                # Choose color (red for emergency, green for normal)
                color = (0, 0, 255) if detection['is_emergency'] else (0, 255, 0)
                thickness = 3 if detection['is_emergency'] else 2
                
                # Draw bounding box
                cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, thickness)
                
                # Draw center point
                cv2.circle(display_frame, tuple(center), 5, color, -1)
                
                # Draw label
                label = f"{detection['class']} ID:{detection['track_id']}"
                if detection['is_emergency']:
                    label += " [EMERGENCY]"
                
                cv2.putText(display_frame, label, (bbox[0], bbox[1]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Show frame info
            info_text = f"Frame: {frame_idx}, Vehicles: {len(tracked_detections)}"
            cv2.putText(display_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow(f'Processing: {video_name}', display_frame)
            
            # Press 'q' to quit, any other key to continue
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        frame_idx += 1
        
        # Progress update
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx}/{total_frames} frames")
    
    cap.release()
    if show_display:
        cv2.destroyAllWindows()
    
    # Save outputs
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Save detailed detections JSON
    detections_json_path = output_dir_path / f"{video_name}_detections.json"
    with open(detections_json_path, 'w') as f:
        json.dump(detections_list, f, indent=2)
    
    # Save detailed detections CSV
    detections_csv_path = output_dir_path / f"{video_name}_detections.csv"
    if detections_list:
        detections_df = pd.DataFrame(detections_list)
        detections_df.to_csv(detections_csv_path, index=False)
    else:
        # Create empty CSV with correct columns
        empty_df = pd.DataFrame(columns=[
            'frame', 'timestamp', 'video', 'track_id', 'class', 'conf', 
            'bbox', 'center', 'is_emergency'
        ])
        empty_df.to_csv(detections_csv_path, index=False)
    
    # Save frame summary CSV
    summary_csv_path = output_dir_path / f"{video_name}_summary.csv"
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_csv_path, index=False)
    
    print(f"Outputs saved to {output_dir_path}")
    print(f"  - Detections JSON: {detections_json_path}")
    print(f"  - Detections CSV: {detections_csv_path}")
    print(f"  - Summary CSV: {summary_csv_path}")
    
    # Return statistics
    tracker_stats = tracker.get_statistics()
    return {
        'video_path': video_path,
        'frames_processed': frame_idx,
        'total_detections': len(detections_list),
        'emergency_detections': sum(1 for d in detections_list if d['is_emergency']),
        'tracker_stats': tracker_stats
    }


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Process videos for vehicle detection and tracking (Ultralytics version)')
    parser.add_argument('--videos', nargs='+',
                       help='One or more video file paths (default: all .mp4 files in input_videos/)')
    parser.add_argument('--output_dir',
                       help='Output directory for results (default: output/)')
    parser.add_argument('--config', default='../configs/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--show', action='store_true', default=True,
                       help='Display annotated frames during processing (default: True)')
    parser.add_argument('--max_frames', type=int, default=None,
                       help='Maximum frames to process per video (for testing)')

    args = parser.parse_args()

    # Set default values if not provided
    if not args.videos:
        input_videos_dir = Path(__file__).parent.parent / 'input_videos'
        if input_videos_dir.exists():
            args.videos = list(input_videos_dir.glob('*.mp4'))
            if not args.videos:
                print(f"No .mp4 files found in {input_videos_dir}")
                return 1
            print(f"Found {len(args.videos)} video files: {[str(v) for v in args.videos]}")
        else:
            print(f"Input videos directory not found: {input_videos_dir}")
            return 1

    if not args.output_dir:
        args.output_dir = str(Path(__file__).parent.parent / 'output')
        print(f"Using default output directory: {args.output_dir}")
    
    # Validate inputs
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        return 1
    
    for video_path in args.videos:
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return 1
    
    try:
        # Initialize detector and tracker
        print("Loading detector and tracker...")
        detector = VehicleDetector(args.config)
        
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        tracker = create_tracker(config)
        
        print(f"Processing {len(args.videos)} video(s)...")
        
        # Process each video
        video_stats = []
        for video_path in args.videos:
            try:
                stats = process_single_video(
                    video_path, detector, tracker, args.output_dir,
                    max_frames=args.max_frames, show_display=args.show
                )
                video_stats.append(stats)
                
                # Reset tracker for next video
                tracker.reset()
                
            except Exception as e:
                print(f"Error processing {video_path}: {e}")
                continue
        
        # Print final statistics
        print("\n=== Processing Summary ===")
        for stats in video_stats:
            video_name = Path(stats['video_path']).stem
            print(f"{video_name}:")
            print(f"  Frames processed: {stats['frames_processed']}")
            print(f"  Total detections: {stats['total_detections']}")
            print(f"  Emergency vehicles: {stats['emergency_detections']}")
            print(f"  Unique tracks: {stats['tracker_stats']['total_created']}")
        
        print("Processing completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())