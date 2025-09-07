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
    
    def _convert_performance_temps(self, perf_summary):
        """Convert temperature values in performance summary from Celsius to Fahrenheit"""
        try:
            # Check if perf_summary is a valid dictionary
            if not isinstance(perf_summary, dict):
                logger.warning(f"Performance summary is not a dictionary: {type(perf_summary)}")
                return perf_summary
            
            if not perf_summary or 'temperature' not in perf_summary or perf_summary['temperature'] is None:
                return perf_summary
            
            temp_data = perf_summary['temperature']
            
            # Check if temp_data is a valid dictionary
            if not isinstance(temp_data, dict):
                logger.warning(f"Temperature data is not a dictionary: {type(temp_data)}")
                return perf_summary
            
            # Check if required temperature keys exist
            required_keys = ['avg', 'max', 'min']
            if not all(key in temp_data for key in required_keys):
                logger.warning(f"Temperature data missing required keys: {temp_data.keys()}")
                return perf_summary
            
            converted = perf_summary.copy()
            converted['temperature'] = {
                'avg': round((temp_data['avg'] * 9/5) + 32, 1),
                'max': round((temp_data['max'] * 9/5) + 32, 1),
                'min': round((temp_data['min'] * 9/5) + 32, 1),
                'avg_celsius': temp_data['avg'],
                'max_celsius': temp_data['max'],
                'min_celsius': temp_data['min']
            }
            
            return converted
        except Exception as e:
            logger.error(f"Error converting performance temperatures: {e}")
            return perf_summary
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Enhanced system health check endpoint"""
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
                    # Basic system metrics
                    try:
                        basic_metrics = self.system_health_monitor.get_system_metrics()
                        
                        # Convert temperature from Celsius to Fahrenheit
                        if isinstance(basic_metrics, dict) and 'temperature' in basic_metrics and basic_metrics['temperature'] is not None:
                            celsius_temp = basic_metrics['temperature']
                            if isinstance(celsius_temp, (int, float)):
                                fahrenheit_temp = round((celsius_temp * 9/5) + 32, 1)
                                basic_metrics['temperature'] = fahrenheit_temp  # Replace with Fahrenheit
                                basic_metrics['temperature_celsius'] = celsius_temp  # Keep Celsius for reference
                        
                        health_data.update(basic_metrics if isinstance(basic_metrics, dict) else {})
                        
                        # Enhanced health information with error handling
                        try:
                            health_score = self.system_health_monitor.get_health_score()
                            health_data['health_score'] = health_score if isinstance(health_score, (int, float)) else None
                        except Exception as e:
                            logger.warning(f"Error getting health score: {e}")
                            health_data['health_score'] = None
                        
                        try:
                            service_details = self.system_health_monitor.get_service_statuses()
                            health_data['service_details'] = service_details if isinstance(service_details, dict) else {}
                        except Exception as e:
                            logger.warning(f"Error getting service details: {e}")
                            health_data['service_details'] = {}
                        
                        try:
                            recent_alerts = self.system_health_monitor.get_recent_alerts(30)
                            health_data['recent_alerts'] = recent_alerts if isinstance(recent_alerts, list) else []
                        except Exception as e:
                            logger.warning(f"Error getting recent alerts: {e}")
                            health_data['recent_alerts'] = []
                        
                        try:
                            performance_summary = self.system_health_monitor.get_performance_summary(30)
                            health_data['performance_summary'] = self._convert_performance_temps(performance_summary) if isinstance(performance_summary, dict) else {}
                        except Exception as e:
                            logger.warning(f"Error getting performance summary: {e}")
                            health_data['performance_summary'] = {}
                        
                        health_data.update({
                            'system_info': {
                                'hostname': __import__('socket').gethostname(),
                                'python_version': __import__('sys').version.split()[0],
                                'platform': __import__('platform').platform(),
                                'uptime': basic_metrics.get('uptime_seconds', 0) if isinstance(basic_metrics, dict) else 0
                            },
                            'camera_snapshot': self._get_latest_camera_snapshot()
                        })
                    except Exception as e:
                        logger.error(f"Error getting system health data: {e}")
                        health_data['system_health_error'] = str(e)
                
                return jsonify(health_data)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/', methods=['GET'])
        def hello_world():
            """Simple hello world endpoint"""
            return jsonify({
                'message': 'Hello World!',
                'service': 'Raspberry Pi Edge Traffic Monitoring API',
                'timestamp': datetime.now().isoformat(),
                'status': 'running'
            })
        
        @self.app.route('/hello', methods=['GET'])
        def hello():
            """Alternative hello endpoint"""
            return jsonify({'message': 'Hello from Raspberry Pi Edge API!'})
        
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
        
        @self.app.route('/api/camera/snapshot/<filename>', methods=['GET'])
        def get_camera_snapshot(filename):
            """Serve camera snapshot images"""
            try:
                import os
                from flask import send_file
                
                # Check multiple possible locations for snapshots
                possible_paths = [
                    "/mnt/storage/periodic_snapshots",  # Primary SSD location
                    "/tmp/periodic_snapshots",          # Fallback temp location
                    "/app/periodic_snapshots",          # Docker app directory
                    os.path.join(os.getcwd(), "periodic_snapshots")  # Current working directory
                ]
                
                file_path = None
                for snapshot_path in possible_paths:
                    potential_path = os.path.join(snapshot_path, filename)
                    if os.path.exists(potential_path):
                        file_path = potential_path
                        break
                
                # Security check - only allow access to snapshot files
                if not filename.startswith('periodic_snapshot_') or not filename.endswith('.jpg'):
                    return jsonify({'error': 'Invalid filename'}), 400
                
                if not file_path or not os.path.exists(file_path):
                    return jsonify({'error': 'Snapshot not found in any location'}), 404
                
                return send_file(file_path, mimetype='image/jpeg')
                
            except Exception as e:
                logger.error(f"Camera snapshot endpoint error: {e}")
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
    
    def _get_latest_camera_snapshot(self):
        """Get information about the latest periodic camera snapshot"""
        try:
            import os
            
            # Check multiple possible locations for snapshots
            possible_paths = [
                "/mnt/storage/periodic_snapshots",  # Primary SSD location
                "/tmp/periodic_snapshots",          # Fallback temp location
                "/app/periodic_snapshots",          # Docker app directory
                os.path.join(os.getcwd(), "periodic_snapshots")  # Current working directory
            ]
            
            snapshot_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    snapshot_path = path
                    break
            
            if not snapshot_path:
                return {
                    'available': False,
                    'message': 'No snapshots directory found in any location'
                }
            
            # Find the latest snapshot
            try:
                snapshot_files = [f for f in os.listdir(snapshot_path) 
                                if f.startswith('periodic_snapshot_') and f.endswith('.jpg')]
            except OSError as e:
                return {
                    'available': False,
                    'message': f'Error accessing snapshot directory: {str(e)}'
                }
            
            if not snapshot_files:
                return {
                    'available': False,
                    'message': f'No snapshots found in {snapshot_path}'
                }
            
            # Get the most recent snapshot
            try:
                latest_snapshot = max(snapshot_files, 
                                    key=lambda x: os.path.getmtime(os.path.join(snapshot_path, x)))
                
                snapshot_full_path = os.path.join(snapshot_path, latest_snapshot)
                mod_time = os.path.getmtime(snapshot_full_path)
                file_size = os.path.getsize(snapshot_full_path)
                
                # Create URL based on the actual path
                if snapshot_path == "/mnt/storage/periodic_snapshots":
                    url_path = f'/api/camera/snapshot/{latest_snapshot}'
                else:
                    # For fallback locations, we'll need to serve from different endpoints
                    url_path = f'/api/camera/snapshot/{latest_snapshot}'
                
                return {
                    'available': True,
                    'filename': latest_snapshot,
                    'timestamp': datetime.fromtimestamp(mod_time).isoformat(),
                    'file_size_bytes': file_size,
                    'path': snapshot_path,
                    'url': url_path
                }
            except (OSError, ValueError) as e:
                return {
                    'available': False,
                    'message': f'Error accessing snapshot file: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error getting latest camera snapshot: {e}")
            return {
                'available': False,
                'message': f'Error: {str(e)}'
            }
    
    def _convert_performance_temps(self, performance_data):
        """Convert temperature values in performance data to Fahrenheit"""
        if not performance_data or not isinstance(performance_data, (list, tuple)):
            return performance_data
            
        # Convert temperature fields to Fahrenheit
        temp_fields = ['cpu_temp', 'gpu_temp', 'temperature']
        
        for entry in performance_data:
            if isinstance(entry, dict):
                for field in temp_fields:
                    if field in entry and entry[field] is not None:
                        celsius = entry[field]
                        fahrenheit = round((celsius * 9/5) + 32, 1)
                        entry[field] = fahrenheit
                        entry[f'{field}_celsius'] = celsius  # Keep original Celsius value
        
        return performance_data

if __name__ == "__main__":
    # Test the API gateway
    api_gateway = EdgeAPIGateway()
    
    try:
        api_gateway.start_server()
    except KeyboardInterrupt:
        api_gateway.stop_server()
