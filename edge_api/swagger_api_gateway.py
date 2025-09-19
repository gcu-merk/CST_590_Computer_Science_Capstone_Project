#!/usr/bin/env python3
"""
Swagger-Enabled Edge API Gateway
Flask-RESTX server providing documented REST API endpoints for the traffic monitoring system
"""

from flask import Flask, jsonify, request, send_file
from flask_restx import Api, Resource, Namespace, reqparse
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import logging
import threading
import json
import os
import subprocess
import socket
import platform
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Import our Swagger configuration and models
from swagger_config import API_CONFIG, create_api_models, QUERY_PARAMS, RESPONSE_EXAMPLES
from api_models import (
    get_model_registry, system_health_schema, vehicle_detections_response_schema,
    speed_detections_response_schema, weather_response_schema, traffic_analytics_schema,
    tracks_response_schema, error_response_schema, time_range_query_schema,
    analytics_query_schema, weather_history_query_schema
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwaggerAPIGateway:
    """
    Swagger-enabled API gateway for edge processing services
    Provides documented REST endpoints and WebSocket communication
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'traffic_monitoring_edge_api'
        self.app.config['RESTX_MASK_SWAGGER'] = False
        
        # Enable CORS for cross-origin requests
        CORS(self.app)
        
        # Initialize Flask-RESTX API with Swagger configuration
        self.api = Api(
            self.app,
            version=API_CONFIG['version'],
            title=API_CONFIG['title'],
            description=API_CONFIG['description'],
            doc=API_CONFIG['doc'],
            contact=API_CONFIG['contact'],
            license_name=API_CONFIG['license']['name'],
            license_url=API_CONFIG['license']['url'],
            validate=True
        )
        
        # Register models with API
        self._register_models()
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Service references
        self.vehicle_detection_service = None
        self.speed_analysis_service = None
        self.data_fusion_engine = None
        self.system_health_monitor = None
        self.sky_analyzer = None
        self.system_status = None
        self.weather_storage = None
        
        # Runtime state
        self.is_running = False
        self.client_count = 0
        
        # Initialize Redis client with error handling
        self.redis_client = None
        try:
            import redis
            # Use Docker hostname for Redis if available
            redis_host = os.environ.get('REDIS_HOST', 'redis')
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connection established to host: {redis_host}")
        except ImportError:
            logger.warning("Redis not available - weather:latest endpoint will not work")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - weather:latest endpoint will not work")
        
        # Setup namespaces and routes
        self._setup_namespaces()
        self._setup_websocket_events()
    
    def _register_models(self):
        """Register all API models with Flask-RESTX"""
        models = get_model_registry()
        for name, model in models.items():
            self.api.models[name] = model
    
    def _setup_namespaces(self):
        """Setup API namespaces and routes"""
        
        # System namespace
        system_ns = Namespace('system', description='System health and status endpoints', path='/api')
        
        @system_ns.route('/health')
        class SystemHealth(Resource):
            @system_ns.doc('get_system_health')
            @system_ns.marshal_with(self.api.models['SystemHealth'])
            @system_ns.response(200, 'Success', self.api.models['SystemHealth'])
            @system_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get comprehensive system health status
                
                Returns detailed system health information including:
                - Overall status (healthy/warning/critical)
                - System resource usage (CPU, memory, disk)
                - Service connectivity status
                - Hardware metrics (temperature, uptime)
                """
                try:
                    health_data = {
                        'status': 'healthy',
                        'timestamp': datetime.now().isoformat(),
                        'uptime_seconds': time.time() - getattr(self, '_start_time', time.time()),
                        'services': {}
                    }
                    
                    # Add system metrics if available
                    if hasattr(self, 'system_health_monitor') and self.system_health_monitor:
                        try:
                            metrics = self.system_health_monitor.get_system_metrics()
                            health_data.update(metrics)
                        except Exception as e:
                            logger.warning(f"Health monitor error: {e}")
                    
                    # Check service connectivity
                    health_data['services'] = {
                        'redis': 'connected' if self._check_redis() else 'disconnected',
                        'vehicle_detection': 'active' if self.vehicle_detection_service else 'inactive',
                        'speed_analysis': 'active' if self.speed_analysis_service else 'inactive',
                        'data_fusion': 'active' if self.data_fusion_engine else 'inactive'
                    }
                    
                    return health_data
                    
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    return {'error': str(e), 'status_code': 500, 'timestamp': datetime.now().isoformat()}, 500
        
        # Vehicle Detection namespace
        detection_ns = Namespace('vehicle-detection', description='Vehicle detection and tracking endpoints', path='/api')
        
        # Create query parser for detections
        detection_parser = reqparse.RequestParser()
        detection_parser.add_argument('seconds', type=int, default=60, 
                                    help='Time span in seconds for historical data (1-86400)')
        
        @detection_ns.route('/detections')
        class VehicleDetections(Resource):
            @detection_ns.doc('get_vehicle_detections')
            @detection_ns.expect(detection_parser)
            @detection_ns.marshal_with(self.api.models['VehicleDetectionsResponse'])
            @detection_ns.response(200, 'Success', self.api.models['VehicleDetectionsResponse'])
            @detection_ns.response(400, 'Bad Request', self.api.models['ErrorResponse'])
            @detection_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get recent vehicle detections
                
                Retrieves vehicle detection data from the specified time period.
                Includes bounding boxes, confidence scores, vehicle classifications,
                and movement directions.
                """
                try:
                    args = detection_parser.parse_args()
                    seconds = args['seconds']
                    
                    if not (1 <= seconds <= 86400):
                        return {
                            'error': 'Invalid seconds parameter. Must be between 1 and 86400.',
                            'status_code': 400,
                            'timestamp': datetime.now().isoformat()
                        }, 400
                    
                    detections = []
                    
                    if self.vehicle_detection_service:
                        try:
                            vehicle_detections = self.vehicle_detection_service.get_recent_detections(seconds)
                            detections.extend([
                                {
                                    'id': d.detection_id,
                                    'timestamp': d.timestamp.isoformat() if hasattr(d.timestamp, 'isoformat') else str(d.timestamp),
                                    'confidence': d.confidence,
                                    'bbox': d.bbox,
                                    'vehicle_type': getattr(d, 'vehicle_type', 'unknown'),
                                    'direction': getattr(d, 'direction', None),
                                    'lane': getattr(d, 'lane', None)
                                }
                                for d in vehicle_detections
                            ])
                        except AttributeError as e:
                            logger.warning(f"Vehicle detection service method missing: {e}")
                    
                    return {
                        'detections': detections,
                        'count': len(detections),
                        'timespan_seconds': seconds
                    }
                    
                except Exception as e:
                    logger.error(f"Detections endpoint error: {e}")
                    return {
                        'error': str(e),
                        'status_code': 500,
                        'timestamp': datetime.now().isoformat()
                    }, 500
        
        @detection_ns.route('/tracks')
        class VehicleTracks(Resource):
            @detection_ns.doc('get_vehicle_tracks')
            @detection_ns.marshal_with(self.api.models['VehicleTrack'], as_list=True)
            @detection_ns.response(200, 'Success')
            @detection_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get active vehicle tracks from data fusion
                
                Returns currently tracked vehicles with their movement history,
                position data, and tracking confidence scores.
                """
                try:
                    tracks = []
                    
                    if self.data_fusion_engine:
                        try:
                            active_tracks = self.data_fusion_engine.get_active_tracks()
                            tracks.extend([
                                {
                                    'track_id': t.track_id,
                                    'start_time': t.start_time.isoformat() if hasattr(t.start_time, 'isoformat') else str(t.start_time),
                                    'last_update': t.last_update.isoformat() if hasattr(t.last_update, 'isoformat') else str(t.last_update),
                                    'positions': getattr(t, 'positions', []),
                                    'speed_history': getattr(t, 'speed_history', []),
                                    'confidence': t.confidence,
                                    'status': getattr(t, 'status', 'active')
                                }
                                for t in active_tracks
                            ])
                        except AttributeError as e:
                            logger.warning(f"Data fusion engine method missing: {e}")
                    
                    return {
                        'tracks': tracks,
                        'active_count': len([t for t in tracks if t.get('status') == 'active']),
                        'total_count': len(tracks)
                    }
                    
                except Exception as e:
                    logger.error(f"Tracks endpoint error: {e}")
                    return {
                        'error': str(e),
                        'status_code': 500,
                        'timestamp': datetime.now().isoformat()
                    }, 500
        
        # Speed Analysis namespace
        speed_ns = Namespace('speed-analysis', description='Speed measurement and analysis endpoints', path='/api')
        
        speed_parser = reqparse.RequestParser()
        speed_parser.add_argument('seconds', type=int, default=60,
                                help='Time span in seconds for historical data (1-86400)')
        
        @speed_ns.route('/speeds')
        class SpeedDetections(Resource):
            @speed_ns.doc('get_speed_detections')
            @speed_ns.expect(speed_parser)
            @speed_ns.marshal_with(self.api.models['SpeedDetection'], as_list=True)
            @speed_ns.response(200, 'Success')
            @speed_ns.response(400, 'Bad Request', self.api.models['ErrorResponse'])
            @speed_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get recent speed measurements
                
                Retrieves speed detection data including average and maximum speeds,
                movement directions, and confidence scores for the specified time period.
                """
                try:
                    args = speed_parser.parse_args()
                    seconds = args['seconds']
                    
                    if not (1 <= seconds <= 86400):
                        return {
                            'error': 'Invalid seconds parameter. Must be between 1 and 86400.',
                            'status_code': 400,
                            'timestamp': datetime.now().isoformat()
                        }, 400
                    
                    speeds = []
                    
                    if self.speed_analysis_service:
                        try:
                            speed_detections = self.speed_analysis_service.get_recent_detections(seconds)
                            speeds.extend([
                                {
                                    'id': s.detection_id,
                                    'start_time': s.start_time.isoformat() if hasattr(s.start_time, 'isoformat') else str(s.start_time),
                                    'end_time': s.end_time.isoformat() if hasattr(s.end_time, 'isoformat') else str(s.end_time),
                                    'avg_speed_mps': s.avg_speed_mps,
                                    'avg_speed_mph': s.avg_speed_mps * 2.237 if s.avg_speed_mps else None,
                                    'max_speed_mps': s.max_speed_mps,
                                    'direction': s.direction,
                                    'confidence': s.confidence
                                }
                                for s in speed_detections
                            ])
                        except AttributeError as e:
                            logger.warning(f"Speed service method missing: {e}")
                    
                    return {
                        'speeds': speeds,
                        'count': len(speeds),
                        'timespan_seconds': seconds
                    }
                    
                except Exception as e:
                    logger.error(f"Speeds endpoint error: {e}")
                    return {
                        'error': str(e),
                        'status_code': 500,
                        'timestamp': datetime.now().isoformat()
                    }, 500
        
        # Weather namespace
        weather_ns = Namespace('weather', description='Weather monitoring and analysis endpoints', path='/api')
        
        @weather_ns.route('/weather')
        class CurrentWeather(Resource):
            @weather_ns.doc('get_current_weather')
            @weather_ns.marshal_with(self.api.models['WeatherData'])
            @weather_ns.response(200, 'Success', self.api.models['WeatherData'])
            @weather_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get current weather conditions and sky analysis
                
                Returns comprehensive weather data from multiple sources including
                DHT22 sensor readings, airport weather station data, and sky condition analysis.
                """
                try:
                    weather_data = {
                        'timestamp': datetime.now().isoformat(),
                        'current_conditions': {},
                        'dht22_sensor': {},
                        'airport_data': {},
                        'analysis': {}
                    }
                    
                    # Get DHT22 sensor data from Redis
                    if self.redis_client:
                        try:
                            dht22_data = self.redis_client.get('weather:dht22:latest')
                            if dht22_data:
                                weather_data['dht22_sensor'] = json.loads(dht22_data)
                        except Exception as e:
                            logger.warning(f"DHT22 data retrieval error: {e}")
                    
                    # Get sky analysis if available
                    if self.sky_analyzer:
                        try:
                            sky_conditions = self.sky_analyzer.get_current_conditions()
                            weather_data['analysis'] = sky_conditions
                        except Exception as e:
                            logger.warning(f"Sky analyzer error: {e}")
                    
                    return weather_data
                    
                except Exception as e:
                    logger.error(f"Weather endpoint error: {e}")
                    return {
                        'error': str(e),
                        'status_code': 500,
                        'timestamp': datetime.now().isoformat()
                    }, 500
        
        # Analytics namespace
        analytics_ns = Namespace('analytics', description='Traffic analytics and insights endpoints', path='/api')
        
        analytics_parser = reqparse.RequestParser()
        analytics_parser.add_argument('period', type=str, default='hour', choices=['hour', 'day', 'week'],
                                    help='Analysis period')
        
        @analytics_ns.route('/analytics')
        class TrafficAnalytics(Resource):
            @analytics_ns.doc('get_traffic_analytics')
            @analytics_ns.expect(analytics_parser)
            @analytics_ns.marshal_with(self.api.models['TrafficAnalytics'])
            @analytics_ns.response(200, 'Success', self.api.models['TrafficAnalytics'])
            @analytics_ns.response(500, 'Internal Server Error', self.api.models['ErrorResponse'])
            def get(self):
                """Get traffic analytics and performance insights
                
                Provides comprehensive traffic analysis including vehicle counts,
                average speeds, violation statistics, and detection rates for the specified period.
                """
                try:
                    args = analytics_parser.parse_args()
                    period = args['period']
                    
                    analytics = {
                        'period': period,
                        'timestamp': datetime.now().isoformat(),
                        'vehicle_count': 0,
                        'avg_speed': 0.0,
                        'speed_violations': 0,
                        'detection_rate': 0.0,
                        'hourly_distribution': {},
                        'speed_distribution': {}
                    }
                    
                    # Calculate analytics from recent data
                    if self.data_fusion_engine:
                        try:
                            fusion_stats = self.data_fusion_engine.get_track_statistics()
                            if isinstance(fusion_stats, dict):
                                analytics.update(fusion_stats)
                        except AttributeError as e:
                            logger.warning(f"Data fusion statistics method missing: {e}")
                    
                    return analytics
                    
                except Exception as e:
                    logger.error(f"Analytics endpoint error: {e}")
                    return {
                        'error': str(e),
                        'status_code': 500,
                        'timestamp': datetime.now().isoformat()
                    }, 500
        
        # Register all namespaces
        self.api.add_namespace(system_ns)
        self.api.add_namespace(detection_ns)
        self.api.add_namespace(speed_ns)
        self.api.add_namespace(weather_ns)
        self.api.add_namespace(analytics_ns)
        
        # Add legacy endpoints for backward compatibility
        self._setup_legacy_routes()
    
    def _setup_legacy_routes(self):
        """Setup legacy routes for backward compatibility"""
        
        @self.app.route('/', methods=['GET'])
        def hello_world():
            """Simple hello world endpoint"""
            return jsonify({
                'message': 'Hello World!',
                'service': 'Raspberry Pi Edge Traffic Monitoring API',
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'documentation': '/docs/'
            })
        
        @self.app.route('/hello', methods=['GET'])
        def hello():
            """Alternative hello endpoint"""
            return jsonify({
                'message': 'Hello from Raspberry Pi Edge API!',
                'documentation': '/docs/'
            })
    
    def _check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except:
            pass
        return False
    
    def _setup_websocket_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.client_count += 1
            logger.info(f"Client connected. Total clients: {self.client_count}")
            emit('status', {'message': 'Connected to Traffic Monitoring API'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.client_count -= 1
            logger.info(f"Client disconnected. Total clients: {self.client_count}")
    
    def set_services(self, vehicle_detection=None, speed_analysis=None, 
                    data_fusion=None, system_health=None, sky_analyzer=None, 
                    system_status=None, weather_storage=None):
        """Set references to edge processing services"""
        self.vehicle_detection_service = vehicle_detection
        self.speed_analysis_service = speed_analysis
        self.data_fusion_engine = data_fusion
        self.system_health_monitor = system_health
        self.sky_analyzer = sky_analyzer
        self.system_status = system_status
        self.weather_storage = weather_storage
    
    def start_server(self):
        """Start the API server"""
        self._start_time = time.time()
        self.is_running = True
        logger.info(f"Starting Swagger-enabled API server on {self.host}:{self.port}")
        logger.info(f"Swagger UI available at: http://{self.host}:{self.port}/docs/")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=False, allow_unsafe_werkzeug=True)
    
    def stop_server(self):
        """Stop the API server"""
        self.is_running = False
        logger.info("API server stopped")

if __name__ == "__main__":
    # Test the Swagger API gateway
    api_gateway = SwaggerAPIGateway()
    
    try:
        api_gateway.start_server()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        api_gateway.stop_server()
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        api_gateway.stop_server()