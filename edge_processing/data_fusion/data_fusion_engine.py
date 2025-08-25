#!/usr/bin/env python3
"""
Data Fusion Engine
Combines vehicle detection from camera with speed analysis from radar
Uses Kalman filtering for accurate tracking and measurement fusion
"""

import time
import logging
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import deque
import numpy as np
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FusedVehicleTrack:
    """Fused vehicle track combining camera and radar data"""
    track_id: str
    start_time: float
    last_update: float
    
    # Position data from camera
    bbox_history: List[Tuple[int, int, int, int]] = field(default_factory=list)
    current_bbox: Optional[Tuple[int, int, int, int]] = None
    
    # Speed data from radar
    speed_history: List[float] = field(default_factory=list)
    current_speed: Optional[float] = None
    
    # Fused estimates
    position_estimate: Optional[Tuple[float, float]] = None  # center x, y
    velocity_estimate: Optional[Tuple[float, float]] = None  # vx, vy
    
    # Metadata
    vehicle_type: str = "unknown"
    confidence: float = 0.0
    is_active: bool = True
    
    # Kalman filter state
    state_vector: Optional[np.ndarray] = None  # [x, y, vx, vy]
    covariance_matrix: Optional[np.ndarray] = None

class KalmanFilter:
    """Simple Kalman filter for vehicle tracking"""
    
    def __init__(self):
        # State vector: [x, y, vx, vy]
        self.state = np.zeros(4)
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, 1, 0],  # x = x + vx*dt
            [0, 1, 0, 1],  # y = y + vy*dt
            [0, 0, 1, 0],  # vx = vx
            [0, 0, 0, 1]   # vy = vy
        ], dtype=float)
        
        # Measurement matrix (we observe position)
        self.H = np.array([
            [1, 0, 0, 0],  # observe x
            [0, 1, 0, 0]   # observe y
        ], dtype=float)
        
        # Process noise covariance
        self.Q = np.eye(4) * 0.1
        
        # Measurement noise covariance
        self.R = np.eye(2) * 10.0
        
        # Error covariance matrix
        self.P = np.eye(4) * 100.0
        
    def predict(self, dt):
        """Predict next state"""
        # Update state transition matrix with time step
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        
        # Predict state
        self.state = self.F @ self.state
        
        # Predict covariance
        self.P = self.F @ self.P @ self.F.T + self.Q
        
    def update(self, measurement):
        """Update with measurement"""
        # Innovation
        y = measurement - self.H @ self.state
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update covariance
        I = np.eye(len(self.state))
        self.P = (I - K @ self.H) @ self.P

class DataFusionEngine:
    """
    Main data fusion engine that combines camera and radar data
    """
    
    def __init__(self, vehicle_detection_service=None, speed_analysis_service=None):
        self.vehicle_detection_service = vehicle_detection_service
        self.speed_analysis_service = speed_analysis_service
        
        self.active_tracks = {}  # track_id -> FusedVehicleTrack
        self.track_history = deque(maxlen=1000)
        self.is_running = False
        
        # Fusion parameters
        self.max_track_age = 5.0  # seconds
        self.association_threshold = 100.0  # pixels
        self.min_track_confidence = 0.3
        
    def start_fusion(self):
        """Start data fusion engine"""
        self.is_running = True
        fusion_thread = threading.Thread(target=self._fusion_loop)
        fusion_thread.start()
        logger.info("Data fusion engine started")
        
    def _fusion_loop(self):
        """Main fusion processing loop"""
        last_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                
                # Get latest detections from both sensors
                camera_detections = self._get_camera_detections()
                radar_detections = self._get_radar_detections()
                
                # Predict all active tracks
                self._predict_tracks(dt)
                
                # Associate camera detections with tracks
                self._associate_camera_detections(camera_detections, current_time)
                
                # Associate radar detections with tracks
                self._associate_radar_detections(radar_detections, current_time)
                
                # Remove old tracks
                self._cleanup_old_tracks(current_time)
                
                # Create new tracks from unassociated detections
                self._create_new_tracks(camera_detections, current_time)
                
                time.sleep(0.1)  # 10Hz fusion rate
                
            except Exception as e:
                logger.error(f"Fusion loop error: {e}")
    
    def _get_camera_detections(self):
        """Get recent camera detections"""
        if self.vehicle_detection_service:
            return self.vehicle_detection_service.get_recent_detections(seconds=1)
        return []
    
    def _get_radar_detections(self):
        """Get recent radar detections"""
        if self.speed_analysis_service:
            return self.speed_analysis_service.get_recent_detections(seconds=1)
        return []
    
    def _predict_tracks(self, dt):
        """Predict all active tracks forward in time"""
        for track in self.active_tracks.values():
            if track.state_vector is not None:
                # Create Kalman filter if needed
                if not hasattr(track, 'kalman_filter'):
                    track.kalman_filter = KalmanFilter()
                    track.kalman_filter.state = track.state_vector.copy()
                    track.kalman_filter.P = track.covariance_matrix.copy()
                
                # Predict
                track.kalman_filter.predict(dt)
                track.state_vector = track.kalman_filter.state.copy()
                track.covariance_matrix = track.kalman_filter.P.copy()
                
                # Update position estimate
                track.position_estimate = (track.state_vector[0], track.state_vector[1])
                track.velocity_estimate = (track.state_vector[2], track.state_vector[3])
    
    def _associate_camera_detections(self, detections, current_time):
        """Associate camera detections with existing tracks"""
        for detection in detections:
            bbox = detection.bbox
            detection_center = (bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2)
            
            # Find closest track
            best_track = None
            best_distance = float('inf')
            
            for track in self.active_tracks.values():
                if track.position_estimate:
                    distance = np.sqrt(
                        (detection_center[0] - track.position_estimate[0])**2 +
                        (detection_center[1] - track.position_estimate[1])**2
                    )
                    
                    if distance < best_distance and distance < self.association_threshold:
                        best_distance = distance
                        best_track = track
            
            if best_track:
                # Update track with camera detection
                best_track.current_bbox = bbox
                best_track.bbox_history.append(bbox)
                best_track.vehicle_type = detection.vehicle_type
                best_track.last_update = current_time
                
                # Update Kalman filter with position measurement
                if hasattr(best_track, 'kalman_filter'):
                    measurement = np.array([detection_center[0], detection_center[1]])
                    best_track.kalman_filter.update(measurement)
                    best_track.state_vector = best_track.kalman_filter.state.copy()
    
    def _associate_radar_detections(self, detections, current_time):
        """Associate radar detections with existing tracks"""
        for detection in detections:
            # Simple association - use the most recent active track
            # In a more sophisticated system, this would use spatial association
            if self.active_tracks:
                # Find track with most recent camera update
                best_track = max(
                    self.active_tracks.values(),
                    key=lambda t: t.last_update if t.current_bbox else 0
                )
                
                if best_track and current_time - best_track.last_update < 2.0:
                    # Update track with speed data
                    best_track.current_speed = detection.avg_speed_mps
                    best_track.speed_history.append(detection.avg_speed_mps)
                    best_track.last_update = current_time
    
    def _cleanup_old_tracks(self, current_time):
        """Remove tracks that haven't been updated recently"""
        tracks_to_remove = []
        
        for track_id, track in self.active_tracks.items():
            age = current_time - track.last_update
            if age > self.max_track_age or track.confidence < self.min_track_confidence:
                tracks_to_remove.append(track_id)
                track.is_active = False
                self.track_history.append(track)
        
        for track_id in tracks_to_remove:
            del self.active_tracks[track_id]
            logger.debug(f"Removed old track: {track_id}")
    
    def _create_new_tracks(self, camera_detections, current_time):
        """Create new tracks from unassociated camera detections"""
        for detection in camera_detections:
            # Check if this detection is already associated
            bbox = detection.bbox
            detection_center = (bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2)
            
            # If no nearby existing track, create new one
            is_new = True
            for track in self.active_tracks.values():
                if track.position_estimate:
                    distance = np.sqrt(
                        (detection_center[0] - track.position_estimate[0])**2 +
                        (detection_center[1] - track.position_estimate[1])**2
                    )
                    if distance < self.association_threshold:
                        is_new = False
                        break
            
            if is_new:
                track_id = str(uuid.uuid4())[:8]
                new_track = FusedVehicleTrack(
                    track_id=track_id,
                    start_time=current_time,
                    last_update=current_time,
                    current_bbox=bbox,
                    bbox_history=[bbox],
                    vehicle_type=detection.vehicle_type,
                    confidence=detection.confidence,
                    position_estimate=detection_center,
                    state_vector=np.array([detection_center[0], detection_center[1], 0, 0]),
                    covariance_matrix=np.eye(4) * 100.0
                )
                
                self.active_tracks[track_id] = new_track
                logger.info(f"Created new track: {track_id} ({detection.vehicle_type})")
    
    def stop_fusion(self):
        """Stop data fusion engine"""
        self.is_running = False
        logger.info("Data fusion engine stopped")
    
    def get_active_tracks(self):
        """Get all currently active tracks"""
        return list(self.active_tracks.values())
    
    def get_track_statistics(self):
        """Get fusion statistics"""
        active_count = len(self.active_tracks)
        total_processed = len(self.track_history) + active_count
        
        return {
            'active_tracks': active_count,
            'total_tracks_processed': total_processed,
            'fusion_running': self.is_running
        }

if __name__ == "__main__":
    # Test the data fusion engine
    fusion_engine = DataFusionEngine()
    
    try:
        fusion_engine.start_fusion()
        time.sleep(30)  # Run for 30 seconds
        
        stats = fusion_engine.get_track_statistics()
        logger.info(f"Fusion statistics: {stats}")
        
    finally:
        fusion_engine.stop_fusion()
