#!/usr/bin/env python3
"""
Edge API Gateway
Flask-SocketIO server providing real-time API endpoints for the traffic monitoring system
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import logging
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeAPIGateway:
    """
    Main API gateway for edge processing services
    Provides REST endpoints and WebSocket communication
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'traffic_monitoring_edge_api'
        
        # Enable CORS for cross-origin requests
        CORS(self.app)
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Service references
        self.vehicle_detection_service = None
        self.speed_analysis_service = None
        self.data_fusion_engine = None
        self.system_health_monitor = None
        
        # Runtime state
        self.is_running = False
        self.client_count = 0
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket_events()
    
    def set_services(self, vehicle_detection=None, speed_analysis=None, 
                    data_fusion=None, system_health=None):
        """Set references to edge processing services"""
        self.vehicle_detection_service = vehicle_detection
        self.speed_analysis_service = speed_analysis
        self.data_fusion_engine = data_fusion
        self.system_health_monitor = system_health
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """System health check endpoint"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'services': {
                        'vehicle_detection': self.vehicle_detection_service is not None,
                        'speed_analysis': self.speed_analysis_service is not None,
                        'data_fusion': self.data_fusion_engine is not None,
                        'system_health': self.system_health_monitor is not None
                    },
                    'client_count': self.client_count
                }
                
                if self.system_health_monitor:
                    health_data.update(self.system_health_monitor.get_system_metrics())
                
                return jsonify(health_data)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/detections', methods=['GET'])
        def get_detections():
            """Get recent vehicle detections"""
            try:
                seconds = request.args.get('seconds', 10, type=int)
                detections = []
                
                if self.vehicle_detection_service:
                    camera_detections = self.vehicle_detection_service.get_recent_detections(seconds)
                    detections.extend([
                        {
                            'id': d.detection_id,
                            'timestamp': d.timestamp,
                            'bbox': d.bbox,
                            'confidence': d.confidence,
                            'vehicle_type': d.vehicle_type,
                            'source': 'camera'
                        }
                        for d in camera_detections
                    ])
                
                return jsonify({
                    'detections': detections,
                    'count': len(detections),
                    'timespan_seconds': seconds
                })
            except Exception as e:
                logger.error(f"Detections endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/speeds', methods=['GET'])
        def get_speeds():
            """Get recent speed measurements"""
            try:
                seconds = request.args.get('seconds', 60, type=int)
                speeds = []
                
                if self.speed_analysis_service:
                    speed_detections = self.speed_analysis_service.get_recent_detections(seconds)
                    speeds.extend([
                        {
                            'id': s.detection_id,
                            'start_time': s.start_time,
                            'end_time': s.end_time,
                            'avg_speed_mps': s.avg_speed_mps,
                            'max_speed_mps': s.max_speed_mps,
                            'direction': s.direction,
                            'confidence': s.confidence
                        }
                        for s in speed_detections
                    ])
                
                return jsonify({
                    'speeds': speeds,
                    'count': len(speeds),
                    'timespan_seconds': seconds
                })
            except Exception as e:
                logger.error(f"Speeds endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tracks', methods=['GET'])
        def get_tracks():
            """Get active vehicle tracks from data fusion"""
            try:
                tracks = []
                
                if self.data_fusion_engine:
                    active_tracks = self.data_fusion_engine.get_active_tracks()
                    tracks = [
                        {
                            'id': t.track_id,
                            'start_time': t.start_time,
                            'last_update': t.last_update,
                            'current_bbox': t.current_bbox,
                            'current_speed': t.current_speed,
                            'position_estimate': t.position_estimate,
                            'velocity_estimate': t.velocity_estimate,
                            'vehicle_type': t.vehicle_type,
                            'confidence': t.confidence
                        }
                        for t in active_tracks
                    ]
                
                return jsonify({
                    'tracks': tracks,
                    'count': len(tracks)
                })
            except Exception as e:
                logger.error(f"Tracks endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get traffic analytics summary"""
            try:
                period = request.args.get('period', 'hour')  # hour, day, week
                
                analytics = {
                    'period': period,
                    'timestamp': datetime.now().isoformat(),
                    'vehicle_count': 0,
                    'avg_speed': 0.0,
                    'speed_violations': 0,
                    'detection_rate': 0.0
                }
                
                # Calculate analytics from recent data
                if self.data_fusion_engine:
                    fusion_stats = self.data_fusion_engine.get_track_statistics()
                    analytics.update(fusion_stats)
                
                return jsonify(analytics)
            except Exception as e:
                logger.error(f"Analytics endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_websocket_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Client connected"""
            self.client_count += 1
            logger.info(f"Client connected. Total clients: {self.client_count}")
            emit('status', {'message': 'Connected to Edge API'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Client disconnected"""
            self.client_count -= 1
            logger.info(f"Client disconnected. Total clients: {self.client_count}")
        
        @self.socketio.on('subscribe_detections')
        def handle_subscribe_detections():
            """Subscribe to real-time detection updates"""
            emit('status', {'message': 'Subscribed to detection updates'})
            # Client will receive updates via broadcast_detection_update
        
        @self.socketio.on('subscribe_speeds')
        def handle_subscribe_speeds():
            """Subscribe to real-time speed updates"""
            emit('status', {'message': 'Subscribed to speed updates'})
            # Client will receive updates via broadcast_speed_update
    
    def broadcast_detection_update(self, detection_data):
        """Broadcast detection update to all connected clients"""
        try:
            self.socketio.emit('detection_update', detection_data)
        except Exception as e:
            logger.error(f"Error broadcasting detection update: {e}")
    
    def broadcast_speed_update(self, speed_data):
        """Broadcast speed update to all connected clients"""
        try:
            self.socketio.emit('speed_update', speed_data)
        except Exception as e:
            logger.error(f"Error broadcasting speed update: {e}")
    
    def broadcast_track_update(self, track_data):
        """Broadcast track update to all connected clients"""
        try:
            self.socketio.emit('track_update', track_data)
        except Exception as e:
            logger.error(f"Error broadcasting track update: {e}")
    
    def start_server(self):
        """Start the API server"""
        try:
            self.is_running = True
            logger.info(f"Starting Edge API Gateway on {self.host}:{self.port}")
            
            # Start background update broadcaster
            update_thread = threading.Thread(target=self._update_broadcaster)
            update_thread.daemon = True
            update_thread.start()
            
            # Start the server
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            self.is_running = False
    
    def _update_broadcaster(self):
        """Background thread to broadcast periodic updates"""
        while self.is_running:
            try:
                if self.client_count > 0:
                    # Broadcast recent detections
                    if self.vehicle_detection_service:
                        recent_detections = self.vehicle_detection_service.get_recent_detections(1)
                        for detection in recent_detections:
                            self.broadcast_detection_update({
                                'id': detection.detection_id,
                                'timestamp': detection.timestamp,
                                'bbox': detection.bbox,
                                'confidence': detection.confidence,
                                'vehicle_type': detection.vehicle_type
                            })
                    
                    # Broadcast recent speeds
                    if self.speed_analysis_service:
                        recent_speeds = self.speed_analysis_service.get_recent_detections(1)
                        for speed in recent_speeds:
                            self.broadcast_speed_update({
                                'id': speed.detection_id,
                                'avg_speed_mps': speed.avg_speed_mps,
                                'direction': speed.direction,
                                'confidence': speed.confidence
                            })
                
                time.sleep(1)  # Broadcast every second
                
            except Exception as e:
                logger.error(f"Update broadcaster error: {e}")
    
    def stop_server(self):
        """Stop the API server"""
        self.is_running = False
        logger.info("Edge API Gateway stopped")

if __name__ == "__main__":
    # Test the API gateway
    api_gateway = EdgeAPIGateway()
    
    try:
        api_gateway.start_server()
    except KeyboardInterrupt:
        api_gateway.stop_server()
