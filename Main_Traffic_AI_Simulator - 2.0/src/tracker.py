"""
Lightweight vehicle tracking module using center-distance heuristics.
Maintains tracks across frames to avoid duplicate counting.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict, deque


class Track:
    """Individual track for a detected vehicle."""
    
    def __init__(self, track_id: int, detection: Dict[str, Any], frame_idx: int):
        """
        Initialize a new track.
        
        Args:
            track_id: Unique identifier for this track
            detection: Detection dictionary
            frame_idx: Frame where track was created
        """
        self.track_id = track_id
        self.centers = deque(maxlen=10)  # Keep last 10 frame centers
        self.last_seen = frame_idx
        self.first_seen = frame_idx
        
        # Store the detection info
        self.class_name = detection['class']
        self.is_emergency = detection['is_emergency']
        
        # Add initial center
        self.centers.append(detection['center'])
    
    def update(self, detection: Dict[str, Any], frame_idx: int):
        """Update track with new detection."""
        self.centers.append(detection['center'])
        self.last_seen = frame_idx
        # Update emergency status (once emergency, always emergency for this track)
        if detection['is_emergency']:
            self.is_emergency = True
    
    def get_distance_to_detection(self, detection: Dict[str, Any]) -> float:
        """
        Calculate minimum distance from detection to any center in track history.
        
        Args:
            detection: Detection dictionary with center coordinates
            
        Returns:
            Minimum Euclidean distance to track centers
        """
        if not self.centers:
            return float('inf')
        
        det_center = np.array(detection['center'])
        distances = []
        
        for center in self.centers:
            track_center = np.array(center)
            distance = np.linalg.norm(det_center - track_center)
            distances.append(distance)
        
        return min(distances)
    
    def is_expired(self, current_frame: int, max_lost_frames: int) -> bool:
        """Check if track should be expired due to inactivity."""
        return (current_frame - self.last_seen) > max_lost_frames


class VehicleTracker:
    """Lightweight tracker using center-distance heuristics."""
    
    def __init__(self, max_lost_frames: int = 30, distance_threshold_ratio: float = 0.5):
        """
        Initialize tracker.
        
        Args:
            max_lost_frames: Frames without detection before track expires
            distance_threshold_ratio: Ratio of bbox size for matching threshold
        """
        self.max_lost_frames = max_lost_frames
        self.distance_threshold_ratio = distance_threshold_ratio
        
        self.tracks = {}  # track_id -> Track
        self.next_track_id = 1
        
        # Statistics
        self.total_tracks_created = 0
        self.expired_tracks = 0
    
    def _calculate_distance_threshold(self, detection: Dict[str, Any]) -> float:
        """
        Calculate matching distance threshold based on detection size.
        
        Args:
            detection: Detection dictionary with bbox
            
        Returns:
            Distance threshold for matching
        """
        bbox = detection['bbox']
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        # Use half of the maximum dimension as threshold
        max_dimension = max(width, height)
        return max_dimension * self.distance_threshold_ratio
    
    def update(self, detections: List[Dict[str, Any]], frame_idx: int) -> List[Dict[str, Any]]:
        """
        Update tracker with new detections and assign track IDs.
        
        Args:
            detections: List of detection dictionaries
            frame_idx: Current frame index
            
        Returns:
            Updated detections with track_id assigned
        """
        # Remove expired tracks first
        self._remove_expired_tracks(frame_idx)
        
        # Create cost matrix for Hungarian algorithm (simplified version)
        updated_detections = []
        unassigned_detections = []
        
        # Try to match each detection to existing tracks
        for detection in detections:
            best_track_id = None
            best_distance = float('inf')
            distance_threshold = self._calculate_distance_threshold(detection)
            
            # Find best matching track
            for track_id, track in self.tracks.items():
                # Only match same class vehicles (more strict)
                if track.class_name != detection['class']:
                    continue
                
                distance = track.get_distance_to_detection(detection)
                
                # Check if within threshold and better than current best
                if distance < distance_threshold and distance < best_distance:
                    best_distance = distance
                    best_track_id = track_id
            
            # Update existing track or mark as unassigned
            if best_track_id is not None:
                self.tracks[best_track_id].update(detection, frame_idx)
                detection['track_id'] = best_track_id
                updated_detections.append(detection)
            else:
                unassigned_detections.append(detection)
        
        # Create new tracks for unassigned detections
        for detection in unassigned_detections:
            new_track = Track(self.next_track_id, detection, frame_idx)
            self.tracks[self.next_track_id] = new_track
            detection['track_id'] = self.next_track_id
            
            self.next_track_id += 1
            self.total_tracks_created += 1
            updated_detections.append(detection)
        
        # Debug info
        if frame_idx % 50 == 0:
            print(f"Frame {frame_idx}: Active tracks: {len(self.tracks)}, New detections: {len(unassigned_detections)}")
        
        return updated_detections
    
    def _remove_expired_tracks(self, current_frame: int):
        """Remove tracks that haven't been seen for too long."""
        expired_track_ids = []
        
        for track_id, track in self.tracks.items():
            if track.is_expired(current_frame, self.max_lost_frames):
                expired_track_ids.append(track_id)
        
        for track_id in expired_track_ids:
            del self.tracks[track_id]
            self.expired_tracks += 1
    
    def get_active_tracks(self) -> Dict[int, Track]:
        """Get all currently active tracks."""
        return self.tracks.copy()
    
    def get_track_count(self) -> int:
        """Get number of active tracks."""
        return len(self.tracks)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        return {
            'active_tracks': len(self.tracks),
            'total_created': self.total_tracks_created,
            'expired_tracks': self.expired_tracks,
            'next_id': self.next_track_id
        }
    
    def reset(self):
        """Reset tracker state."""
        self.tracks.clear()
        self.next_track_id = 1
        self.total_tracks_created = 0
        self.expired_tracks = 0


def create_tracker(config: Dict[str, Any]) -> VehicleTracker:
    """
    Create tracker from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized VehicleTracker
    """
    max_lost_frames = config.get('max_lost_frames', 30)
    distance_threshold_ratio = config.get('distance_threshold_ratio', 0.5)
    
    return VehicleTracker(
        max_lost_frames=max_lost_frames,
        distance_threshold_ratio=distance_threshold_ratio
    )