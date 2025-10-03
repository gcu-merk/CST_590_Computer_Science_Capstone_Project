#!/usr/bin/env python3
"""
Swagger Configuration for Traffic Monitoring Edge API
Provides OpenAPI/Swagger documentation and model definitions
"""

from flask_restx import Api, fields, Model
from datetime import datetime

# API Documentation Configuration
API_CONFIG = {
    'version': '1.0.0',
    'title': 'Traffic Monitoring Edge API',
    'description': """
    A production-ready edge computing traffic monitoring system powered by Raspberry Pi 5, Sony IMX500 AI camera, 
    and mmWave radar. Delivers real-time vehicle detection, classification, and speed analysis with <350ms latency. 
    Features multi-sensor fusion, weather integration, and comprehensive REST/WebSocket APIs for seamless integration. 
    All AI processing happens on-device with privacy-first architecture, backed by Redis caching, SQLite persistence, 
    and centralized logging for enterprise-grade reliability.
    """,
    'doc': '/docs/',  # Swagger UI path
    'contact': {
        'name': 'Traffic Monitoring System',
        'email': 'admin@trafficmonitor.local'
    },
    'license': {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    },
    'servers': [
        {
            'url': 'http://localhost:5000',
            'description': 'Development server'
        },
        {
            'url': 'http://100.121.231.16:5000',
            'description': 'Raspberry Pi deployment'
        }
    ],
    'tags': []  # Let Flask-RESTX auto-generate tags from namespaces
}

def create_api_models():
    """Create Flask-RESTX model definitions for API documentation"""
    
    # System Health Models
    system_health_model = Model('SystemHealth', {
        'status': fields.String(required=True, description='Overall system status', example='healthy'),
        'timestamp': fields.String(required=True, description='Health check timestamp', example='2025-09-18T10:30:00Z'),
        'uptime_seconds': fields.Float(description='System uptime in seconds', example=3600.5),
        'cpu_usage': fields.Float(description='CPU usage percentage', example=45.2),
        'memory_usage': fields.Float(description='Memory usage percentage', example=62.8),
        'disk_usage': fields.Float(description='Disk usage percentage', example=35.1),
        'temperature': fields.Float(description='System temperature in Celsius', example=42.5),
        'services': fields.Raw(description='Service status details')
    })
    
    # Vehicle Detection Models
    vehicle_detection_model = Model('VehicleDetection', {
        'id': fields.String(required=True, description='Detection ID', example='det_123456'),
        'timestamp': fields.String(required=True, description='Detection timestamp', example='2025-09-18T10:30:00Z'),
        'confidence': fields.Float(required=True, description='Detection confidence (0-1)', example=0.95),
        'bbox': fields.List(fields.Float, description='Bounding box [x, y, width, height]', example=[100, 50, 150, 200]),
        'vehicle_type': fields.String(description='Vehicle classification', example='car'),
        'direction': fields.String(description='Movement direction', example='north'),
        'lane': fields.Integer(description='Lane number', example=1)
    })
    
    vehicle_detections_response = Model('VehicleDetectionsResponse', {
        'detections': fields.List(fields.Nested(vehicle_detection_model)),
        'count': fields.Integer(description='Number of detections', example=5),
        'timespan_seconds': fields.Integer(description='Time span of data', example=60)
    })
    
    # Speed Analysis Models
    speed_detection_model = Model('SpeedDetection', {
        'id': fields.String(required=True, description='Speed detection ID', example='speed_123456'),
        'start_time': fields.String(required=True, description='Detection start time', example='2025-09-18T10:30:00Z'),
        'end_time': fields.String(required=True, description='Detection end time', example='2025-09-18T10:30:05Z'),
        'avg_speed_mps': fields.Float(description='Average speed in m/s', example=13.89),
        'avg_speed_mph': fields.Float(description='Average speed in mph', example=31.1),
        'max_speed_mps': fields.Float(description='Maximum speed in m/s', example=15.2),
        'direction': fields.String(description='Movement direction', example='north'),
        'confidence': fields.Float(description='Detection confidence', example=0.92)
    })
    
    speed_detections_response = Model('SpeedDetectionsResponse', {
        'speeds': fields.List(fields.Nested(speed_detection_model)),
        'count': fields.Integer(description='Number of speed detections', example=3),
        'timespan_seconds': fields.Integer(description='Time span of data', example=60)
    })
    
    # Weather Models
    weather_data_model = Model('WeatherData', {
        'timestamp': fields.String(required=True, description='Weather reading timestamp', example='2025-09-18T10:30:00Z'),
        'temperature_c': fields.Float(description='Temperature in Celsius', example=22.5),
        'temperature_f': fields.Float(description='Temperature in Fahrenheit', example=72.5),
        'humidity': fields.Float(description='Humidity percentage', example=65.3),
        'pressure': fields.Float(description='Atmospheric pressure in hPa', example=1013.25),
        'wind_speed': fields.Float(description='Wind speed in m/s', example=3.2),
        'wind_direction': fields.String(description='Wind direction', example='NW'),
        'visibility': fields.Float(description='Visibility in kilometers', example=10.0),
        'sky_condition': fields.String(description='Sky condition analysis', example='clear'),
        'weather_description': fields.String(description='Weather description', example='Clear sky')
    })
    
    weather_response = Model('WeatherResponse', {
        'current_conditions': fields.Nested(weather_data_model),
        'dht22_sensor': fields.Raw(description='DHT22 sensor data'),
        'airport_data': fields.Raw(description='Airport weather station data'),
        'analysis': fields.Raw(description='Weather analysis results')
    })
    
    # Analytics Models
    analytics_model = Model('TrafficAnalytics', {
        'period': fields.String(required=True, description='Analysis period', example='hour'),
        'timestamp': fields.String(required=True, description='Analysis timestamp', example='2025-09-18T10:30:00Z'),
        'vehicle_count': fields.Integer(description='Total vehicle count', example=45),
        'avg_speed': fields.Float(description='Average speed in mph', example=28.5),
        'speed_violations': fields.Integer(description='Number of speed violations', example=3),
        'detection_rate': fields.Float(description='Detection success rate', example=0.94),
        'hourly_distribution': fields.Raw(description='Hourly traffic distribution'),
        'speed_distribution': fields.Raw(description='Speed distribution data')
    })
    
    # Track Models
    vehicle_track_model = Model('VehicleTrack', {
        'track_id': fields.String(required=True, description='Track ID', example='track_123456'),
        'start_time': fields.String(description='Track start time', example='2025-09-18T10:30:00Z'),
        'last_update': fields.String(description='Last update time', example='2025-09-18T10:30:05Z'),
        'positions': fields.List(fields.Raw, description='Position history'),
        'speed_history': fields.List(fields.Float, description='Speed measurements'),
        'confidence': fields.Float(description='Track confidence', example=0.88),
        'status': fields.String(description='Track status', example='active')
    })
    
    tracks_response = Model('TracksResponse', {
        'tracks': fields.List(fields.Nested(vehicle_track_model)),
        'active_count': fields.Integer(description='Number of active tracks', example=2),
        'total_count': fields.Integer(description='Total tracks', example=5)
    })
    
    # Error Models
    error_model = Model('ErrorResponse', {
        'error': fields.String(required=True, description='Error message', example='Invalid parameter'),
        'status_code': fields.Integer(description='HTTP status code', example=400),
        'timestamp': fields.String(description='Error timestamp', example='2025-09-18T10:30:00Z')
    })
    
    # API Info Model
    api_info_model = Model('APIInfo', {
        'title': fields.String(description='API title', example='Traffic Monitoring Edge API'),
        'version': fields.String(description='API version', example='1.0.0'),
        'description': fields.String(description='API description'),
        'base_url': fields.String(description='Base URL', example='http://100.121.231.16:5000'),
        'timestamp': fields.String(description='Response timestamp', example='2025-09-18T10:30:00Z')
    })
    
    return {
        'system_health': system_health_model,
        'vehicle_detection': vehicle_detection_model,
        'vehicle_detections_response': vehicle_detections_response,
        'speed_detection': speed_detection_model,
        'speed_detections_response': speed_detections_response,
        'weather_data': weather_data_model,
        'weather_response': weather_response,
        'analytics': analytics_model,
        'vehicle_track': vehicle_track_model,
        'tracks_response': tracks_response,
        'error': error_model,
        'api_info': api_info_model
    }

# Query parameter models for documentation
QUERY_PARAMS = {
    'seconds': {
        'description': 'Time span in seconds for historical data',
        'type': 'integer',
        'default': 60,
        'minimum': 1,
        'maximum': 86400,
        'example': 300
    },
    'period': {
        'description': 'Analysis period',
        'type': 'string',
        'enum': ['hour', 'day', 'week'],
        'default': 'hour',
        'example': 'hour'
    },
    'hours': {
        'description': 'Number of hours for historical data',
        'type': 'integer',
        'default': 24,
        'minimum': 1,
        'maximum': 168,
        'example': 6
    },
    'limit': {
        'description': 'Maximum number of records to return',
        'type': 'integer',
        'default': 100,
        'minimum': 1,
        'maximum': 1000,
        'example': 50
    }
}

# Common response examples
RESPONSE_EXAMPLES = {
    'health_check': {
        'status': 'healthy',
        'timestamp': '2025-09-18T10:30:00Z',
        'uptime_seconds': 3600.5,
        'cpu_usage': 45.2,
        'memory_usage': 62.8,
        'disk_usage': 35.1,
        'temperature': 42.5,
        'services': {
            'redis': 'connected',
            'database': 'connected',
            'camera': 'active',
            'sensors': 'active'
        }
    },
    'vehicle_detection': {
        'detections': [
            {
                'id': 'det_123456',
                'timestamp': '2025-09-18T10:30:00Z',
                'confidence': 0.95,
                'bbox': [100, 50, 150, 200],
                'vehicle_type': 'car',
                'direction': 'north',
                'lane': 1
            }
        ],
        'count': 1,
        'timespan_seconds': 60
    },
    'weather_data': {
        'current_conditions': {
            'timestamp': '2025-09-18T10:30:00Z',
            'temperature_c': 22.5,
            'humidity': 65.3,
            'sky_condition': 'clear'
        },
        'analysis': {
            'visibility_impact': 'none',
            'detection_adjustment': 1.0
        }
    }
}