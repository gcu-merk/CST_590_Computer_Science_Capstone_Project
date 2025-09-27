#!/usr/bin/env python3
"""
Enhanced Swagger-Enabled Edge API Gateway - WITH CENTRALIZED LOGGING
Flask-RESTX server providing documented REST API endpoints for the traffic monitoring system
NOW WITH CENTRALIZED LOGGING AND CORRELATION TRACKING

This enhanced API gateway provides:
- Comprehensive REST API endpoints with Swagger documentation
- Request/response correlation tracking across all endpoints
- Performance monitoring for API calls and database queries
- Centralized logging with business event tracking
- Real-time WebSocket communication with correlation
- System health monitoring and diagnostics
- Error tracking and API analytics

Architecture:
HTTP Requests -> Enhanced API Gateway -> ServiceLogger -> Redis/Database -> Centralized Logging
"""

from flask import Flask, jsonify, request, send_file, g
from flask_restx import Api, Resource, Namespace, reqparse

from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import threading
import json
import os
import subprocess
import socket
import platform
import sys
import uuid
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import functools

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir / "edge_processing"))
from shared_logging import ServiceLogger, CorrelationContext

# Import our Swagger configuration and models
from swagger_config import API_CONFIG, create_api_models, QUERY_PARAMS, RESPONSE_EXAMPLES
from api_models import (
    get_model_registry, system_health_schema, vehicle_detections_response_schema,
    speed_detections_response_schema, weather_response_schema, traffic_analytics_schema,
    tracks_response_schema, error_response_schema, time_range_query_schema,
    analytics_query_schema, weather_history_query_schema
)

# Initialize centralized logging
logger = ServiceLogger("api_gateway_service")

# Request correlation decorator
def with_correlation_tracking(f):
    """Decorator to add correlation tracking to API endpoints"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate or use existing correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(correlation_id):
            # Log request start
            logger.info("API request started", extra={
                "business_event": "api_request_start",
                "correlation_id": correlation_id,
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "query_params": dict(request.args),
                "user_agent": request.headers.get('User-Agent'),
                "client_ip": request.remote_addr
            })
            
            start_time = time.time()
            try:
                # Execute the endpoint
                result = f(*args, **kwargs)
                
                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                logger.info("API request completed successfully", extra={
                    "business_event": "api_request_success",
                    "correlation_id": correlation_id,
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "response_type": type(result).__name__
                })
                
                # Add correlation ID to response headers
                if hasattr(result, 'headers'):
                    result.headers['X-Correlation-ID'] = correlation_id
                elif isinstance(result, tuple):
                    # Handle Flask tuple responses (data, status_code, headers)
                    if len(result) == 3:
                        data, status, headers = result
                        headers = headers or {}
                        headers['X-Correlation-ID'] = correlation_id
                        result = (data, status, headers)
                    elif len(result) == 2:
                        data, status = result
                        headers = {'X-Correlation-ID': correlation_id}
                        result = (data, status, headers)
                
                return result
                
            except Exception as e:
                # Log error response
                duration_ms = (time.time() - start_time) * 1000
                logger.error("API request failed", extra={
                    "business_event": "api_request_failure",
                    "correlation_id": correlation_id,
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                raise
                
    return decorated_function


class EnhancedSwaggerAPIGateway:
    """
    Enhanced Swagger-enabled API gateway with centralized logging and correlation tracking
    Provides documented REST endpoints and WebSocket communication with full observability
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": 0.0,
            "active_connections": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Connection health tracking
        self.connection_health = {
            "socket_connections": set(),
            "connection_history": [],
            "total_connections": 0,
            "ping_responses": 0,
            "last_activity": datetime.now().isoformat()
        }
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'traffic_monitoring_edge_api_enhanced'
        self.app.config['RESTX_MASK_SWAGGER'] = False
        
        # Enable CORS for cross-origin requests
        CORS(self.app)
        
        # Initialize Flask-RESTX API with Swagger configuration and /api prefix
        self.api = Api(
            self.app,
            version=API_CONFIG['version'],
            title=API_CONFIG['title'] + " - Enhanced",
            description=API_CONFIG['description'] + " (with centralized logging)",
            doc=API_CONFIG['doc'],
            contact=API_CONFIG['contact'],
            license=API_CONFIG['license'],
            tags=API_CONFIG['tags'],
            validate=True,
            prefix='/api'  # Add proper API prefix for industry standard
        )
        
        # Register models with API
        self._register_models()
        
        # Initialize SocketIO with correlation tracking
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self._setup_socketio_correlation()
        
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
        
        # Initialize Redis client with enhanced logging
        self.redis_client = None
        self._setup_redis_connection()
        
        # Setup route handlers with correlation tracking
        self._setup_enhanced_routes()
        
        # Setup request/response middleware
        self._setup_middleware()
        
        logger.info("Enhanced API gateway initialized", extra={
            "business_event": "api_gateway_initialization",
            "host": self.host,
            "port": self.port,
            "redis_available": self.redis_client is not None
        })
    
    def _setup_redis_connection(self):
        """Setup Redis connection with enhanced logging"""
        try:
            import redis
            redis_host = os.environ.get('REDIS_HOST', 'redis')
            redis_port = int(os.environ.get('REDIS_PORT', 6379))
            
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0, 
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            logger.info("Redis connection established", extra={
                "business_event": "redis_connection_established",
                "redis_host": redis_host,
                "redis_port": redis_port
            })
            
        except ImportError:
            logger.warning("Redis library not available", extra={
                "business_event": "redis_unavailable",
                "reason": "import_error"
            })
        except Exception as e:
            logger.error("Redis connection failed", extra={
                "business_event": "redis_connection_failure",
                "error": str(e),
                "redis_host": os.environ.get('REDIS_HOST', 'redis')
            })
    
    def _setup_socketio_correlation(self):
        """Setup WebSocket event handlers with correlation tracking"""
        
        @self.socketio.on('connect')
        def handle_connect():
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                # Update connection health tracking
                self.connection_health["socket_connections"].add(request.sid)
                self.connection_health["total_connections"] += 1
                self.connection_health["last_activity"] = datetime.now().isoformat()
                
                # Update legacy client count
                self.client_count += 1
                self.stats["active_connections"] = len(self.connection_health["socket_connections"])
                
                logger.info("WebSocket client connected", extra={
                    "business_event": "websocket_connection",
                    "correlation_id": correlation_id,
                    "client_id": request.sid,
                    "active_connections": self.stats["active_connections"],
                    "total_connections": self.connection_health["total_connections"]
                })
                
                # Send connection confirmation with correlation ID
                emit('connected', {
                    'correlation_id': correlation_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                # Update connection health tracking
                self.connection_health["socket_connections"].discard(request.sid)
                self.connection_health["last_activity"] = datetime.now().isoformat()
                
                # Update legacy client count
                self.client_count = max(0, self.client_count - 1)
                self.stats["active_connections"] = len(self.connection_health["socket_connections"])
                
                logger.info("WebSocket client disconnected", extra={
                    "business_event": "websocket_disconnection",
                    "correlation_id": correlation_id,
                    "client_id": request.sid,
                    "active_connections": self.stats["active_connections"]
                })
        
        @self.socketio.on('subscribe_events')
        def handle_subscribe_events():
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                logger.info("Client subscribed to events stream", extra={
                    "business_event": "events_subscription",
                    "correlation_id": correlation_id,
                    "client_id": request.sid
                })
                
                # Send recent events from database
                recent_events = self._get_recent_events(limit=10)
                for event in recent_events:
                    emit('real_time_event', event)
                
                emit('events_status', {
                    'status': 'subscribed',
                    'correlation_id': correlation_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('ping')
        def handle_ping(timestamp, callback=None):
            """Handle ping requests for connection health monitoring"""
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                # Update ping statistics
                self.connection_health["ping_responses"] += 1
                self.connection_health["last_activity"] = datetime.now().isoformat()
                
                logger.debug("Ping received from client", extra={
                    "business_event": "socket_ping",
                    "correlation_id": correlation_id,
                    "client_id": request.sid,
                    "client_timestamp": timestamp,
                    "total_pings": self.connection_health["ping_responses"]
                })
                
                # Respond with pong
                if callback:
                    callback({
                        'pong': True,
                        'server_timestamp': datetime.now().isoformat(),
                        'client_timestamp': timestamp
                    })
    
    def _setup_middleware(self):
        """Setup request/response middleware for logging and stats"""
        
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            self.stats["total_requests"] += 1
        
        @self.app.after_request
        def after_request(response):
            # Update response time statistics
            if hasattr(g, 'start_time'):
                duration_ms = (time.time() - g.start_time) * 1000
                
                # Update average response time
                if self.stats["successful_requests"] > 0:
                    current_avg = self.stats["avg_response_time_ms"]
                    new_avg = ((current_avg * (self.stats["successful_requests"] - 1)) + duration_ms) / self.stats["successful_requests"]
                    self.stats["avg_response_time_ms"] = round(new_avg, 2)
                else:
                    self.stats["avg_response_time_ms"] = round(duration_ms, 2)
            
            if response.status_code < 400:
                self.stats["successful_requests"] += 1
            else:
                self.stats["failed_requests"] += 1
            
            # Add server headers
            response.headers['X-API-Gateway'] = 'Enhanced-Traffic-Monitor'
            response.headers['X-API-Version'] = API_CONFIG['version']
            
            return response
    
    def _register_models(self):
        """Register Swagger models with enhanced logging"""
        try:
            model_registry = get_model_registry()
            
            for model_name, model_schema in model_registry.items():
                self.api.models[model_name] = self.api.model(model_name, model_schema)
            
            logger.info("API models registered successfully", extra={
                "business_event": "api_models_registered",
                "model_count": len(model_registry)
            })
            
        except Exception as e:
            logger.error("Failed to register API models", extra={
                "business_event": "api_models_registration_failure",
                "error": str(e)
            })
    
    def _setup_enhanced_routes(self):
        """Setup API routes with enhanced logging and correlation tracking"""
        
        # Capture gateway instance for Resource classes
        gateway = self
        
        # Simple health check endpoint for Docker healthcheck
        @self.app.route('/health')
        def simple_health_check():
            """Simple health check endpoint for container monitoring"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}, 200
        
        # Create namespaces
        health_ns = self.api.namespace('health', description='System health and monitoring')
        vehicle_ns = self.api.namespace('vehicles', description='Vehicle detection and tracking')
        weather_ns = self.api.namespace('weather', description='Weather data and monitoring')
        analytics_ns = self.api.namespace('analytics', description='Traffic analytics and insights')
        events_ns = self.api.namespace('events', description='Real-time event streaming and logs')
        
        # Health endpoints
        @health_ns.route('/system')
        class SystemHealth(Resource):
            @with_correlation_tracking
            @health_ns.marshal_with(gateway.api.models['SystemHealth'])
            def get(self):
                """Get comprehensive system health status"""
                try:
                    health_data = gateway._get_system_health()
                    
                    logger.debug("System health check completed", extra={
                        "business_event": "system_health_check",
                        "cpu_usage": health_data.get("cpu_usage"),
                        "memory_usage": health_data.get("memory_usage"),
                        "disk_usage": health_data.get("disk_usage")
                    })
                    
                    return health_data
                    
                except Exception as e:
                    logger.error("System health check failed", extra={
                        "business_event": "system_health_check_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        @health_ns.route('/stats')
        class APIStats(Resource):
            @with_correlation_tracking
            def get(self):
                """Get API gateway statistics"""
                try:
                    stats_data = {
                        **self.stats,
                        "uptime_seconds": (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds(),
                        "success_rate": (self.stats["successful_requests"] / max(1, self.stats["total_requests"])) * 100
                    }
                    
                    logger.debug("API statistics retrieved", extra={
                        "business_event": "api_stats_retrieved",
                        "total_requests": stats_data["total_requests"],
                        "success_rate": stats_data["success_rate"]
                    })
                    
                    return stats_data
                    
                except Exception as e:
                    logger.error("Failed to retrieve API statistics", extra={
                        "business_event": "api_stats_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        # Vehicle detection endpoints
        @vehicle_ns.route('/detections')
        class VehicleDetections(Resource):
            @with_correlation_tracking
            @vehicle_ns.marshal_with(gateway.api.models['VehicleDetectionsResponse'])
            def get(self):
                """Get recent vehicle detections"""
                try:
                    detections = gateway._get_vehicle_detections()
                    
                    logger.debug("Vehicle detections retrieved", extra={
                        "business_event": "vehicle_detections_retrieved",
                        "detection_count": len(detections.get("detections", []))
                    })
                    
                    return detections
                    
                except Exception as e:
                    logger.error("Failed to retrieve vehicle detections", extra={
                        "business_event": "vehicle_detections_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @vehicle_ns.route('/consolidated')
        class ConsolidatedEvents(Resource):
            @with_correlation_tracking
            def get(self):
                """Get consolidated vehicle events (JSON format from dual storage)"""
                try:
                    # Parse query parameters
                    parser = reqparse.RequestParser()
                    parser.add_argument('limit', type=int, default=20, help='Number of events to retrieve')
                    parser.add_argument('since', type=str, help='Get events since timestamp (ISO format)')
                    args = parser.parse_args()
                    
                    consolidated_events = gateway._get_consolidated_events(
                        limit=args['limit'],
                        since=args['since']
                    )
                    
                    logger.debug("Consolidated events retrieved", extra={
                        "business_event": "consolidated_events_retrieved",
                        "event_count": len(consolidated_events.get("events", []))
                    })
                    
                    return consolidated_events
                    
                except Exception as e:
                    logger.error("Failed to retrieve consolidated events", extra={
                        "business_event": "consolidated_events_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        # Weather endpoints
        @weather_ns.route('/current')
        class CurrentWeather(Resource):
            @with_correlation_tracking
            @weather_ns.marshal_with(gateway.api.models['WeatherData'])
            def get(self):
                """Get current weather conditions"""
                try:
                    weather_data = gateway._get_current_weather()
                    
                    logger.debug("Current weather retrieved", extra={
                        "business_event": "weather_data_retrieved",
                        "temperature": weather_data.get("temperature"),
                        "humidity": weather_data.get("humidity"),
                        "data_sources": len(weather_data.get("sources", []))
                    })
                    
                    return weather_data
                    
                except Exception as e:
                    logger.error("Failed to retrieve weather data", extra={
                        "business_event": "weather_data_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        # Analytics endpoints
        @analytics_ns.route('/summary')
        class AnalyticsSummary(Resource):
            @with_correlation_tracking
            def get(self):
                """Get analytics summary data"""
                try:
                    # Placeholder analytics data
                    return {
                        "total_vehicles": 0,
                        "avg_speed": 0,
                        "peak_hours": [],
                        "vehicle_types": {},
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get analytics summary", extra={
                        "business_event": "analytics_summary_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/speeds')
        class AnalyticsSpeeds(Resource):
            @with_correlation_tracking
            def get(self):
                """Get speed analytics data"""
                try:
                    # Placeholder speed data
                    return {
                        "speeds": [],
                        "avg_speed": 0,
                        "max_speed": 0,
                        "min_speed": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get speed analytics", extra={
                        "business_event": "speed_analytics_failure", 
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/patterns')
        class AnalyticsPatterns(Resource):
            @with_correlation_tracking
            def get(self):
                """Get traffic pattern analytics"""
                try:
                    return {
                        "patterns": [],
                        "peak_times": [],
                        "trends": {},
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get pattern analytics", extra={
                        "business_event": "pattern_analytics_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/safety')
        class AnalyticsSafety(Resource):
            @with_correlation_tracking
            def get(self):
                """Get safety analytics"""
                try:
                    return {
                        "safety_score": 0,
                        "violations": [],
                        "incidents": [],
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get safety analytics", extra={
                        "business_event": "safety_analytics_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/reports/summary')
        class ReportsSummary(Resource):
            @with_correlation_tracking
            def get(self):
                """Get reports summary"""
                try:
                    return {
                        "reports": [],
                        "summary": {},
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get reports summary", extra={
                        "business_event": "reports_summary_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/reports/violations')
        class ReportsViolations(Resource):
            @with_correlation_tracking
            def get(self):
                """Get violation reports"""
                try:
                    return {
                        "violations": [],
                        "count": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get violation reports", extra={
                        "business_event": "violation_reports_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        @analytics_ns.route('/reports/monthly')
        class ReportsMonthly(Resource):
            @with_correlation_tracking
            def get(self):
                """Get monthly reports"""
                try:
                    return {
                        "monthly_data": [],
                        "trends": {},
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error("Failed to get monthly reports", extra={
                        "business_event": "monthly_reports_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        # Events endpoints for real-time dashboard
        @events_ns.route('/recent')
        class RecentEvents(Resource):
            @with_correlation_tracking
            def get(self):
                """Get recent events for dashboard (fallback to REST when WebSocket unavailable)"""
                try:
                    # Get query parameters
                    parser = reqparse.RequestParser()
                    parser.add_argument('limit', type=int, default=50, help='Number of recent events to return')
                    args = parser.parse_args()
                    
                    # Access the gateway instance method correctly
                    events = gateway._get_recent_events(limit=args['limit'])
                    
                    logger.debug("Recent events retrieved via REST", extra={
                        "business_event": "events_rest_retrieval",
                        "event_count": len(events),
                        "limit": args['limit']
                    })
                    
                    return {
                        "events": events,
                        "count": len(events),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error("Failed to retrieve recent events via REST", extra={
                        "business_event": "events_rest_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500

        # New realtime events endpoint for GitHub Pages compatibility
        @events_ns.route('/realtime')
        class RealtimeEvents(Resource):
            @with_correlation_tracking
            def get(self):
                """Get realtime events - alias for recent events for GitHub Pages compatibility"""
                try:
                    # Get query parameters
                    parser = reqparse.RequestParser()
                    parser.add_argument('limit', type=int, default=20, help='Number of realtime events to return')
                    args = parser.parse_args()
                    
                    # Access the gateway instance method correctly  
                    events = gateway._get_recent_events(limit=args['limit'])
                    
                    logger.debug("Realtime events retrieved via REST", extra={
                        "business_event": "realtime_events_retrieval",
                        "event_count": len(events),
                        "limit": args['limit']
                    })
                    
                    # Format for GitHub Pages compatibility
                    return {
                        "status": "success",
                        "events": events,
                        "count": len(events),
                        "timestamp": datetime.now().isoformat(),
                        "realtime": True
                    }
                    
                except Exception as e:
                    logger.error("Failed to retrieve realtime events", extra={
                        "business_event": "realtime_events_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        @events_ns.route('/broadcast')
        class BroadcastEvent(Resource):
            @with_correlation_tracking
            def post(self):
                """Receive event from broadcaster service and send to WebSocket clients"""
                try:
                    event_data = request.get_json()
                    
                    if not event_data:
                        return {"error": "No event data provided"}, 400
                    
                    # Broadcast the event to WebSocket clients
                    self.broadcast_event(event_data)
                    
                    logger.debug("Event broadcast request processed", extra={
                        "business_event": "broadcast_request_processed",
                        "event_type": event_data.get('business_event'),
                        "source_service": event_data.get('service_name')
                    })
                    
                    return {
                        "status": "broadcasted",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error("Failed to process broadcast request", extra={
                        "business_event": "broadcast_request_failure",
                        "error": str(e)
                    })
                    return {"error": str(e)}, 500
        
        # Routes registered successfully - no dynamic binding needed
    
    @logger.monitor_performance("system_health_check")
    def _get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status with monitoring"""
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check service health
        redis_healthy = self.redis_client is not None
        if redis_healthy:
            try:
                self.redis_client.ping()
            except:
                redis_healthy = False
        
        health_status = {
            "status": "healthy" if cpu_usage < 80 and memory.percent < 85 else "warning",
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "redis_healthy": redis_healthy,
            "api_stats": self.stats,
            "system_info": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "hostname": socket.gethostname()
            },
            "metrics_available": True
        }
        
        return health_status
    
    @logger.monitor_performance("vehicle_detections_query")
    def _get_vehicle_detections(self) -> Dict[str, Any]:
        """Get recent vehicle detections with monitoring"""
        detections = []
        
        if self.redis_client:
            try:
                # Get recent vehicle detections from Redis
                detection_keys = self.redis_client.keys("vehicle:detection:*")
                
                for key in detection_keys[-10:]:  # Get last 10 detections
                    detection_data = self.redis_client.hgetall(key)
                    if detection_data:
                        detections.append(detection_data)
                
            except Exception as e:
                logger.warning("Failed to retrieve detections from Redis", extra={
                    "error": str(e)
                })
        
        return {
            "detections": detections,
            "total_count": len(detections),
            "timestamp": datetime.now().isoformat()
        }

    @logger.monitor_performance("consolidated_events_query")
    def _get_consolidated_events(self, limit: int = 20, since: Optional[str] = None) -> Dict[str, Any]:
        """Get consolidated vehicle events from dual storage JSON table with monitoring"""
        events = []
        
        try:
            # Get database path from environment
            db_path = os.environ.get('DATABASE_PATH', '/app/data/traffic_monitoring.db')
            
            # Check if database file exists
            if not os.path.exists(db_path):
                logger.warning("Database file not found", extra={
                    "db_path": db_path
                })
                return {
                    "events": [],
                    "total_count": 0,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Database not found"
                }
            
            # Connect to the SQLite database
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Build query with optional time filter
            query = """
                SELECT consolidation_id, event_json, created_at 
                FROM consolidated_events 
            """
            params = []
            
            if since:
                query += "WHERE created_at >= ? "
                params.append(since)
            
            query += "ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Process each row
            for row in rows:
                try:
                    # Parse the JSON data
                    event_data = json.loads(row['event_json'])
                    
                    # Add metadata
                    event_record = {
                        "consolidation_id": row['consolidation_id'],
                        "created_at": row['created_at'],
                        **event_data  # Merge the JSON data
                    }
                    events.append(event_record)
                    
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in consolidated event", extra={
                        "consolidation_id": row['consolidation_id'],
                        "error": str(e)
                    })
            
            conn.close()
            
            logger.info("Consolidated events retrieved successfully", extra={
                "business_event": "consolidated_events_query_success",
                "event_count": len(events),
                "limit": limit,
                "since_filter": since is not None
            })
            
        except Exception as e:
            logger.error("Failed to retrieve consolidated events", extra={
                "business_event": "consolidated_events_query_failure",
                "error": str(e),
                "db_path": db_path
            })
        
        return {
            "events": events,
            "total_count": len(events),
            "timestamp": datetime.now().isoformat(),
            "query_params": {
                "limit": limit,
                "since": since
            }
        }
    
    @logger.monitor_performance("weather_data_query") 
    def _get_current_weather(self) -> Dict[str, Any]:
        """Get current weather data from multiple sources with monitoring"""
        weather_sources = {}
        
        if self.redis_client:
            try:
                # Get DHT22 sensor data
                dht22_data = self.redis_client.hgetall("weather:dht22")
                if dht22_data:
                    weather_sources["dht22"] = dht22_data
                
                # Get airport weather data
                airport_data = self.redis_client.get("weather:airport:latest")
                if airport_data:
                    weather_sources["airport"] = json.loads(airport_data)
                
                # Get weather correlation
                correlation_data = self.redis_client.get("weather:correlation:airport_dht22")
                if correlation_data:
                    weather_sources["correlation"] = json.loads(correlation_data)
                
            except Exception as e:
                logger.warning("Failed to retrieve weather data from Redis", extra={
                    "error": str(e)
                })
        
        return {
            "sources": weather_sources,
            "primary_temperature": weather_sources.get("dht22", {}).get("temperature"),
            "primary_humidity": weather_sources.get("dht22", {}).get("humidity"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_recent_events(self, limit=50) -> List[Dict[str, Any]]:
        """Get recent events from the centralized logging database for real-time streaming"""
        events = []
        
        try:
            # Connect to the SQLite database where ServiceLogger stores events
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'centralized_logs.db')
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            cursor = conn.cursor()
            
            # Query recent business events for the dashboard
            cursor.execute("""
                SELECT timestamp, service_name, level, message, 
                       business_event, correlation_id, extra_data
                FROM logs 
                WHERE business_event IS NOT NULL 
                   AND business_event IN (
                       'vehicle_detection', 'vehicle_detected', 'api_request_success',
                       'radar_alert', 'system_status', 'health_check'
                   )
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                # Parse extra_data JSON if available
                extra_data = {}
                if row['extra_data']:
                    try:
                        extra_data = json.loads(row['extra_data'])
                    except json.JSONDecodeError:
                        pass
                
                event = {
                    'timestamp': row['timestamp'],
                    'service_name': row['service_name'],
                    'level': row['level'],
                    'message': row['message'],
                    'business_event': row['business_event'],
                    'correlation_id': row['correlation_id'],
                    **extra_data  # Merge extra data fields
                }
                events.append(event)
            
            conn.close()
            
        except Exception as e:
            logger.error("Failed to retrieve recent events", extra={
                "business_event": "events_retrieval_failure",
                "error": str(e)
            })
        
        return events
    
    def broadcast_event(self, event_data):
        """Broadcast a real-time event to all connected WebSocket clients"""
        try:
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                # Add timestamp if not present
                if 'timestamp' not in event_data:
                    event_data['timestamp'] = datetime.now().isoformat()
                
                # Emit to all connected clients
                self.socketio.emit('real_time_event', event_data)
                
                logger.debug("Event broadcasted to WebSocket clients", extra={
                    "business_event": "event_broadcast",
                    "correlation_id": correlation_id,
                    "event_type": event_data.get('business_event', 'unknown'),
                    "active_connections": self.client_count
                })
                
        except Exception as e:
            logger.error("Failed to broadcast event", extra={
                "business_event": "event_broadcast_failure",
                "error": str(e)
            })
    
    def run(self, debug=False):
        """Run the enhanced API gateway with logging"""
        try:
            logger.info("Starting enhanced API gateway server", extra={
                "business_event": "api_gateway_start",
                "host": self.host,
                "port": self.port,
                "debug_mode": debug
            })
            
            self.is_running = True
            
            # Run the SocketIO server
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=debug,
                use_reloader=False,  # Disable reloader to prevent double initialization
                allow_unsafe_werkzeug=True  # Allow Werkzeug in container environment
            )
            
        except Exception as e:
            logger.error("API gateway server failed to start", extra={
                "business_event": "api_gateway_start_failure",
                "error": str(e),
                "host": self.host,
                "port": self.port
            })
            raise
        finally:
            self.is_running = False
            logger.info("API gateway server stopped", extra={
                "business_event": "api_gateway_stop",
                "final_stats": self.stats
            })


def main():
    """Main entry point for enhanced API gateway"""
    try:
        # Configuration from environment
        host = os.environ.get('API_HOST', '0.0.0.0')
        port = int(os.environ.get('API_PORT', 5000))
        debug = os.environ.get('API_DEBUG', 'false').lower() == 'true'
        
        # Create and run enhanced gateway
        gateway = EnhancedSwaggerAPIGateway(host=host, port=port)
        gateway.run(debug=debug)
        
    except KeyboardInterrupt:
        logger.info("API gateway shutdown requested by user", extra={
            "business_event": "api_gateway_manual_shutdown"
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error("API gateway failed to start", extra={
            "business_event": "api_gateway_startup_failure",
            "error": str(e),
            "traceback": error_details
        })
        print(f"FATAL ERROR: {e}")
        print(f"TRACEBACK: {error_details}")
        sys.exit(1)


if __name__ == "__main__":
    main()