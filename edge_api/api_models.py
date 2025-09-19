#!/usr/bin/env python3
"""
API Models and Schemas for Traffic Monitoring System
Provides data validation, serialization, and Swagger documentation models
"""

from flask_restx import fields, Model
from marshmallow import Schema, fields as ma_fields, validate, post_load
from datetime import datetime
from typing import Dict, List, Optional

class BaseSchema(Schema):
    """Base schema with common functionality"""
    
    class Meta:
        ordered = True
        unknown = 'EXCLUDE'  # Exclude unknown fields
    
    def handle_error(self, error, data, **kwargs):
        """Custom error handling"""
        raise ValueError(f"Validation error: {error}")

# System Health Schemas
class SystemHealthSchema(BaseSchema):
    """Schema for system health responses"""
    status = ma_fields.String(required=True, validate=validate.OneOf(['healthy', 'warning', 'critical']))
    timestamp = ma_fields.DateTime(required=True, format='iso')
    uptime_seconds = ma_fields.Float(validate=validate.Range(min=0))
    cpu_usage = ma_fields.Float(validate=validate.Range(min=0, max=100))
    memory_usage = ma_fields.Float(validate=validate.Range(min=0, max=100))
    disk_usage = ma_fields.Float(validate=validate.Range(min=0, max=100))
    temperature = ma_fields.Float(validate=validate.Range(min=-50, max=150))
    services = ma_fields.Dict()

# Vehicle Detection Schemas
class BoundingBoxSchema(BaseSchema):
    """Schema for bounding box coordinates"""
    x = ma_fields.Float(required=True, validate=validate.Range(min=0))
    y = ma_fields.Float(required=True, validate=validate.Range(min=0))
    width = ma_fields.Float(required=True, validate=validate.Range(min=0))
    height = ma_fields.Float(required=True, validate=validate.Range(min=0))

class VehicleDetectionSchema(BaseSchema):
    """Schema for vehicle detection data"""
    id = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    confidence = ma_fields.Float(required=True, validate=validate.Range(min=0, max=1))
    bbox = ma_fields.List(ma_fields.Float(), validate=validate.Length(equal=4))
    vehicle_type = ma_fields.String(validate=validate.OneOf([
        'car', 'truck', 'motorcycle', 'bus', 'bicycle', 'unknown'
    ]))
    direction = ma_fields.String(validate=validate.OneOf([
        'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest'
    ]))
    lane = ma_fields.Integer(validate=validate.Range(min=1, max=10))

class VehicleDetectionsResponseSchema(BaseSchema):
    """Schema for vehicle detections response"""
    detections = ma_fields.List(ma_fields.Nested(VehicleDetectionSchema))
    count = ma_fields.Integer(validate=validate.Range(min=0))
    timespan_seconds = ma_fields.Integer(validate=validate.Range(min=1))

# Speed Analysis Schemas
class SpeedDetectionSchema(BaseSchema):
    """Schema for speed detection data"""
    id = ma_fields.String(required=True)
    start_time = ma_fields.DateTime(required=True, format='iso')
    end_time = ma_fields.DateTime(required=True, format='iso')
    avg_speed_mps = ma_fields.Float(validate=validate.Range(min=0, max=100))
    avg_speed_mph = ma_fields.Float(validate=validate.Range(min=0, max=223))
    max_speed_mps = ma_fields.Float(validate=validate.Range(min=0, max=100))
    direction = ma_fields.String()
    confidence = ma_fields.Float(validate=validate.Range(min=0, max=1))

class SpeedDetectionsResponseSchema(BaseSchema):
    """Schema for speed detections response"""
    speeds = ma_fields.List(ma_fields.Nested(SpeedDetectionSchema))
    count = ma_fields.Integer(validate=validate.Range(min=0))
    timespan_seconds = ma_fields.Integer(validate=validate.Range(min=1))

# Weather Schemas
class WeatherConditionsSchema(BaseSchema):
    """Schema for weather conditions"""
    timestamp = ma_fields.DateTime(required=True, format='iso')
    temperature_c = ma_fields.Float(validate=validate.Range(min=-50, max=60))
    temperature_f = ma_fields.Float(validate=validate.Range(min=-58, max=140))
    humidity = ma_fields.Float(validate=validate.Range(min=0, max=100))
    pressure = ma_fields.Float(validate=validate.Range(min=900, max=1100))
    wind_speed = ma_fields.Float(validate=validate.Range(min=0, max=100))
    wind_direction = ma_fields.String()
    visibility = ma_fields.Float(validate=validate.Range(min=0, max=50))
    sky_condition = ma_fields.String(validate=validate.OneOf([
        'clear', 'partly_cloudy', 'cloudy', 'overcast', 'foggy', 'rainy', 'snowy'
    ]))
    weather_description = ma_fields.String()

class WeatherResponseSchema(BaseSchema):
    """Schema for weather response"""
    current_conditions = ma_fields.Nested(WeatherConditionsSchema)
    dht22_sensor = ma_fields.Dict()
    airport_data = ma_fields.Dict()
    analysis = ma_fields.Dict()

# Analytics Schemas
class TrafficAnalyticsSchema(BaseSchema):
    """Schema for traffic analytics"""
    period = ma_fields.String(required=True, validate=validate.OneOf(['hour', 'day', 'week', 'month']))
    timestamp = ma_fields.DateTime(required=True, format='iso')
    vehicle_count = ma_fields.Integer(validate=validate.Range(min=0))
    avg_speed = ma_fields.Float(validate=validate.Range(min=0))
    speed_violations = ma_fields.Integer(validate=validate.Range(min=0))
    detection_rate = ma_fields.Float(validate=validate.Range(min=0, max=1))
    hourly_distribution = ma_fields.Dict()
    speed_distribution = ma_fields.Dict()

# Track Schemas
class PositionSchema(BaseSchema):
    """Schema for position data"""
    x = ma_fields.Float(required=True)
    y = ma_fields.Float(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')

class VehicleTrackSchema(BaseSchema):
    """Schema for vehicle track data"""
    track_id = ma_fields.String(required=True)
    start_time = ma_fields.DateTime(format='iso')
    last_update = ma_fields.DateTime(format='iso')
    positions = ma_fields.List(ma_fields.Nested(PositionSchema))
    speed_history = ma_fields.List(ma_fields.Float())
    confidence = ma_fields.Float(validate=validate.Range(min=0, max=1))
    status = ma_fields.String(validate=validate.OneOf(['active', 'lost', 'completed']))

class TracksResponseSchema(BaseSchema):
    """Schema for tracks response"""
    tracks = ma_fields.List(ma_fields.Nested(VehicleTrackSchema))
    active_count = ma_fields.Integer(validate=validate.Range(min=0))
    total_count = ma_fields.Integer(validate=validate.Range(min=0))

# Error Schemas
class ErrorResponseSchema(BaseSchema):
    """Schema for error responses"""
    error = ma_fields.String(required=True)
    status_code = ma_fields.Integer(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    details = ma_fields.Dict(load_default={})

# Query Parameter Schemas
class TimeRangeQuerySchema(BaseSchema):
    """Schema for time range query parameters"""
    seconds = ma_fields.Integer(
        validate=validate.Range(min=1, max=86400),
        load_default=60
    )

class AnalyticsQuerySchema(BaseSchema):
    """Schema for analytics query parameters"""
    period = ma_fields.String(
        validate=validate.OneOf(['hour', 'day', 'week', 'month']),
        load_default='hour'
    )

class WeatherHistoryQuerySchema(BaseSchema):
    """Schema for weather history query parameters"""
    hours = ma_fields.Integer(
        validate=validate.Range(min=1, max=168),
        load_default=24
    )
    limit = ma_fields.Integer(
        validate=validate.Range(min=1, max=1000),
        load_default=100
    )

# Schema instances for use in endpoints
system_health_schema = SystemHealthSchema()
vehicle_detection_schema = VehicleDetectionSchema()
vehicle_detections_response_schema = VehicleDetectionsResponseSchema()
speed_detection_schema = SpeedDetectionSchema()
speed_detections_response_schema = SpeedDetectionsResponseSchema()
weather_conditions_schema = WeatherConditionsSchema()
weather_response_schema = WeatherResponseSchema()
traffic_analytics_schema = TrafficAnalyticsSchema()
vehicle_track_schema = VehicleTrackSchema()
tracks_response_schema = TracksResponseSchema()
error_response_schema = ErrorResponseSchema()

# Query parameter schemas
time_range_query_schema = TimeRangeQuerySchema()
analytics_query_schema = AnalyticsQuerySchema()
weather_history_query_schema = WeatherHistoryQuerySchema()

# Model registry for Flask-RESTX
def get_model_registry() -> Dict[str, Model]:
    """Get all Flask-RESTX models for API documentation"""
    return {
        'SystemHealth': Model('SystemHealth', {
            'status': fields.String(required=True, description='Overall system status', enum=['healthy', 'warning', 'critical']),
            'timestamp': fields.String(required=True, description='Health check timestamp'),
            'uptime_seconds': fields.Float(description='System uptime in seconds'),
            'cpu_usage': fields.Float(description='CPU usage percentage'),
            'memory_usage': fields.Float(description='Memory usage percentage'),
            'disk_usage': fields.Float(description='Disk usage percentage'),
            'temperature': fields.Float(description='System temperature in Celsius'),
            'services': fields.Raw(description='Service status details')
        }),
        
        'VehicleDetection': Model('VehicleDetection', {
            'id': fields.String(required=True, description='Detection ID'),
            'timestamp': fields.String(required=True, description='Detection timestamp'),
            'confidence': fields.Float(required=True, description='Detection confidence (0-1)'),
            'bbox': fields.List(fields.Float, description='Bounding box [x, y, width, height]'),
            'vehicle_type': fields.String(description='Vehicle classification', enum=['car', 'truck', 'motorcycle', 'bus', 'bicycle', 'unknown']),
            'direction': fields.String(description='Movement direction'),
            'lane': fields.Integer(description='Lane number')
        }),
        
        'VehicleDetectionsResponse': Model('VehicleDetectionsResponse', {
            'detections': fields.List(fields.Raw, description='List of vehicle detections'),
            'count': fields.Integer(description='Number of detections'),
            'timespan_seconds': fields.Integer(description='Time span of data')
        }),
        
        'SpeedDetection': Model('SpeedDetection', {
            'id': fields.String(required=True, description='Speed detection ID'),
            'start_time': fields.String(required=True, description='Detection start time'),
            'end_time': fields.String(required=True, description='Detection end time'),
            'avg_speed_mps': fields.Float(description='Average speed in m/s'),
            'avg_speed_mph': fields.Float(description='Average speed in mph'),
            'max_speed_mps': fields.Float(description='Maximum speed in m/s'),
            'direction': fields.String(description='Movement direction'),
            'confidence': fields.Float(description='Detection confidence')
        }),
        
        'WeatherData': Model('WeatherData', {
            'timestamp': fields.String(required=True, description='Weather reading timestamp'),
            'temperature_c': fields.Float(description='Temperature in Celsius'),
            'temperature_f': fields.Float(description='Temperature in Fahrenheit'),
            'humidity': fields.Float(description='Humidity percentage'),
            'pressure': fields.Float(description='Atmospheric pressure in hPa'),
            'wind_speed': fields.Float(description='Wind speed in m/s'),
            'wind_direction': fields.String(description='Wind direction'),
            'visibility': fields.Float(description='Visibility in kilometers'),
            'sky_condition': fields.String(description='Sky condition analysis'),
            'weather_description': fields.String(description='Weather description')
        }),
        
        'AirportWeatherData': Model('AirportWeatherData', {
            'source': fields.String(required=True, description='Data source (weather.gov API)'),
            'redis_key': fields.String(required=True, description='Redis key used'),
            'retrieved_at': fields.String(required=True, description='Timestamp when data was retrieved'),
            'data': fields.Nested(Model('AirportObservation', {
                'timestamp': fields.String(description='Observation timestamp'),
                'textDescription': fields.String(description='Weather description'),
                'temperature': fields.Float(description='Temperature value'),
                'windDirection': fields.Float(description='Wind direction in degrees'),
                'windSpeed': fields.Float(description='Wind speed'),
                'visibility': fields.Float(description='Visibility'),
                'precipitationLast3Hours': fields.Float(description='Precipitation in last 3 hours'),
                'relativeHumidity': fields.Float(description='Relative humidity percentage'),
                'cloudLayers': fields.List(fields.Raw, description='Cloud layer information'),
                'stationId': fields.String(description='Weather station ID'),
                'stationName': fields.String(description='Weather station name'),
                'error': fields.String(description='Error message if any')
            }), required=True, description='Weather observation data')
        }),
        
        'DHT22WeatherData': Model('DHT22WeatherData', {
            'source': fields.String(required=True, description='Data source (DHT22 Local Sensor)'),
            'redis_key': fields.String(required=True, description='Redis key used'),
            'retrieved_at': fields.String(required=True, description='Timestamp when data was retrieved'),
            'data': fields.Nested(Model('DHT22Observation', {
                'temperature_c': fields.Float(description='Temperature in Celsius'),
                'temperature_f': fields.Float(description='Temperature in Fahrenheit'),
                'humidity': fields.Float(description='Relative humidity percentage'),
                'timestamp': fields.String(description='Reading timestamp')
            }), required=True, description='DHT22 sensor data')
        }),
        
        'TrafficAnalytics': Model('TrafficAnalytics', {
            'period': fields.String(required=True, description='Analysis period'),
            'timestamp': fields.String(required=True, description='Analysis timestamp'),
            'vehicle_count': fields.Integer(description='Total vehicle count'),
            'avg_speed': fields.Float(description='Average speed in mph'),
            'speed_violations': fields.Integer(description='Number of speed violations'),
            'detection_rate': fields.Float(description='Detection success rate'),
            'hourly_distribution': fields.Raw(description='Hourly traffic distribution'),
            'speed_distribution': fields.Raw(description='Speed distribution data')
        }),
        
        'VehicleTrack': Model('VehicleTrack', {
            'track_id': fields.String(required=True, description='Track ID'),
            'start_time': fields.String(description='Track start time'),
            'last_update': fields.String(description='Last update time'),
            'positions': fields.List(fields.Raw, description='Position history'),
            'speed_history': fields.List(fields.Float, description='Speed measurements'),
            'confidence': fields.Float(description='Track confidence'),
            'status': fields.String(description='Track status', enum=['active', 'lost', 'completed'])
        }),
        
        'ErrorResponse': Model('ErrorResponse', {
            'error': fields.String(required=True, description='Error message'),
            'status_code': fields.Integer(description='HTTP status code'),
            'timestamp': fields.String(description='Error timestamp'),
            'details': fields.Raw(description='Additional error details')
        })
    }

# Validation utilities
def validate_time_range(seconds: int) -> bool:
    """Validate time range parameter"""
    return 1 <= seconds <= 86400

def validate_period(period: str) -> bool:
    """Validate period parameter"""
    return period in ['hour', 'day', 'week', 'month']

def validate_limit(limit: int) -> bool:
    """Validate limit parameter"""
    return 1 <= limit <= 1000

def register_models(api):
    """Register Flask-RESTX models with the API instance"""
    model_registry = get_model_registry()
    for model_name, model_def in model_registry.items():
        api.add_model(model_name, model_def)
    return api