#!/usr/bin/env python3
"""
Enhanced API Models for Image Analysis System
Extends existing API models with image analysis, vehicle detection, and sky analysis schemas
"""

from flask_restx import fields, Model
from marshmallow import Schema, fields as ma_fields, validate, post_load
from datetime import datetime
from typing import Dict, List, Optional

# Import base schemas
try:
    from .api_models import BaseSchema
    BASE_MODELS_AVAILABLE = True
except ImportError:
    try:
        from api_models import BaseSchema
        BASE_MODELS_AVAILABLE = True
    except ImportError:
        # Fallback base schema
        from marshmallow import Schema
        class BaseSchema(Schema):
            class Meta:
                ordered = True
                unknown = 'EXCLUDE'
        BASE_MODELS_AVAILABLE = False

# Enhanced Vehicle Detection Schemas
class EnhancedBoundingBoxSchema(BaseSchema):
    """Enhanced schema for bounding box coordinates with confidence"""
    x = ma_fields.Integer(required=True, validate=validate.Range(min=0))
    y = ma_fields.Integer(required=True, validate=validate.Range(min=0))
    width = ma_fields.Integer(required=True, validate=validate.Range(min=1))
    height = ma_fields.Integer(required=True, validate=validate.Range(min=1))
    confidence = ma_fields.Float(required=True, validate=validate.Range(min=0, max=1))

class EnhancedVehicleDetectionSchema(BaseSchema):
    """Enhanced schema for vehicle detection with additional classification"""
    detection_id = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    vehicle_type = ma_fields.String(required=True, validate=validate.OneOf([
        'pedestrian', 'bicycle', 'motorcycle', 'car', 'truck', 'bus', 
        'van', 'delivery_truck', 'emergency_vehicle', 'unknown'
    ]))
    confidence = ma_fields.Float(required=True, validate=validate.Range(min=0, max=1))
    bounding_box = ma_fields.Nested(EnhancedBoundingBoxSchema, required=True)
    additional_metadata = ma_fields.Dict(missing={})

# Sky Analysis Schemas
class SkyAnalysisSchema(BaseSchema):
    """Schema for sky condition analysis"""
    analysis_id = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    condition = ma_fields.String(required=True, validate=validate.OneOf([
        'clear', 'partly_cloudy', 'overcast', 'stormy', 
        'night_clear', 'night_cloudy', 'dawn_dusk', 'unknown'
    ]))
    confidence = ma_fields.Float(required=True, validate=validate.Range(min=0, max=1))
    light_level = ma_fields.Float(validate=validate.Range(min=0, max=1), allow_none=True)
    cloud_coverage = ma_fields.Float(validate=validate.Range(min=0, max=1), allow_none=True)
    additional_metadata = ma_fields.Dict(missing={})

# Image Analysis Schemas
class ImageMetadataSchema(BaseSchema):
    """Schema for image metadata"""
    image_size = ma_fields.String()
    confidence_threshold = ma_fields.Float(validate=validate.Range(min=0, max=1))
    detection_version = ma_fields.String()
    analysis_version = ma_fields.String()

class ImageAnalysisResultSchema(BaseSchema):
    """Schema for complete image analysis result"""
    image_id = ma_fields.String(required=True)
    image_path = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    trigger_source = ma_fields.String(required=True, validate=validate.OneOf([
        'radar', 'manual', 'scheduled', 'test', 'unknown'
    ]))
    vehicle_detections = ma_fields.List(ma_fields.Nested(EnhancedVehicleDetectionSchema))
    sky_analysis = ma_fields.Nested(SkyAnalysisSchema)
    processing_time_ms = ma_fields.Float(validate=validate.Range(min=0))
    image_metadata = ma_fields.Nested(ImageMetadataSchema, missing={})

# Consolidated Data Schemas
class ProcessingMetadataSchema(BaseSchema):
    """Schema for processing metadata"""
    consolidation_version = ma_fields.String()
    consolidation_timestamp = ma_fields.DateTime(format='iso')
    data_sources = ma_fields.Dict()

class ConsolidatedImageDataSchema(BaseSchema):
    """Schema for consolidated image analysis data"""
    consolidation_id = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(required=True, format='iso')
    image_analysis = ma_fields.Nested(ImageAnalysisResultSchema)
    weather_data = ma_fields.Dict(allow_none=True)
    system_metrics = ma_fields.Dict(allow_none=True)
    trigger_source = ma_fields.String()
    processing_metadata = ma_fields.Nested(ProcessingMetadataSchema, missing={})

# API Response Schemas
class ImageAnalysisListResponseSchema(BaseSchema):
    """Schema for image analysis list response"""
    results = ma_fields.List(ma_fields.Nested(ImageAnalysisResultSchema))
    count = ma_fields.Integer(validate=validate.Range(min=0))
    timespan_seconds = ma_fields.Integer(validate=validate.Range(min=1))
    page = ma_fields.Integer(validate=validate.Range(min=1), missing=1)
    per_page = ma_fields.Integer(validate=validate.Range(min=1, max=100), missing=50)

class ConsolidatedDataListResponseSchema(BaseSchema):
    """Schema for consolidated data list response"""
    results = ma_fields.List(ma_fields.Nested(ConsolidatedImageDataSchema))
    count = ma_fields.Integer(validate=validate.Range(min=0))
    timespan_seconds = ma_fields.Integer(validate=validate.Range(min=1))
    page = ma_fields.Integer(validate=validate.Range(min=1), missing=1)
    per_page = ma_fields.Integer(validate=validate.Range(min=1, max=100), missing=50)

# Statistics Schemas
class VehicleStatisticsSchema(BaseSchema):
    """Schema for vehicle detection statistics"""
    total_detections = ma_fields.Integer(validate=validate.Range(min=0))
    detections_by_type = ma_fields.Dict()
    avg_confidence = ma_fields.Float(validate=validate.Range(min=0, max=1))
    time_period = ma_fields.String()

class SkyStatisticsSchema(BaseSchema):
    """Schema for sky condition statistics"""
    conditions_distribution = ma_fields.Dict()
    avg_light_level = ma_fields.Float(validate=validate.Range(min=0, max=1))
    avg_cloud_coverage = ma_fields.Float(validate=validate.Range(min=0, max=1))
    time_period = ma_fields.String()

class AnalyticsResponseSchema(BaseSchema):
    """Schema for analytics response"""
    vehicle_statistics = ma_fields.Nested(VehicleStatisticsSchema)
    sky_statistics = ma_fields.Nested(SkyStatisticsSchema)
    period_start = ma_fields.DateTime(format='iso')
    period_end = ma_fields.DateTime(format='iso')
    total_images_analyzed = ma_fields.Integer(validate=validate.Range(min=0))

# Query Parameter Schemas
class ImageAnalysisQuerySchema(BaseSchema):
    """Schema for image analysis query parameters"""
    since = ma_fields.DateTime(format='iso', missing=None)
    until = ma_fields.DateTime(format='iso', missing=None)
    trigger_source = ma_fields.String(validate=validate.OneOf([
        'radar', 'manual', 'scheduled', 'test', 'all'
    ]), missing='all')
    vehicle_type = ma_fields.String(validate=validate.OneOf([
        'pedestrian', 'bicycle', 'motorcycle', 'car', 'truck', 'bus', 
        'van', 'delivery_truck', 'emergency_vehicle', 'all'
    ]), missing='all')
    sky_condition = ma_fields.String(validate=validate.OneOf([
        'clear', 'partly_cloudy', 'overcast', 'stormy', 
        'night_clear', 'night_cloudy', 'dawn_dusk', 'all'
    ]), missing='all')
    min_confidence = ma_fields.Float(validate=validate.Range(min=0, max=1), missing=0.0)
    page = ma_fields.Integer(validate=validate.Range(min=1), missing=1)
    per_page = ma_fields.Integer(validate=validate.Range(min=1, max=100), missing=50)

class AnalyticsQuerySchema(BaseSchema):
    """Schema for analytics query parameters"""
    period = ma_fields.String(validate=validate.OneOf([
        'hour', 'day', 'week', 'month'
    ]), missing='day')
    since = ma_fields.DateTime(format='iso', missing=None)
    until = ma_fields.DateTime(format='iso', missing=None)
    group_by = ma_fields.String(validate=validate.OneOf([
        'hour', 'day', 'vehicle_type', 'sky_condition'
    ]), missing='day')

# Error Schemas
class ImageAnalysisErrorSchema(BaseSchema):
    """Schema for image analysis error responses"""
    error = ma_fields.String(required=True)
    message = ma_fields.String(required=True)
    timestamp = ma_fields.DateTime(format='iso', missing=datetime.utcnow)
    request_id = ma_fields.String()
    details = ma_fields.Dict(missing={})

# Create schema instances for use in API
enhanced_bounding_box_schema = EnhancedBoundingBoxSchema()
enhanced_vehicle_detection_schema = EnhancedVehicleDetectionSchema()
sky_analysis_schema = SkyAnalysisSchema()
image_analysis_result_schema = ImageAnalysisResultSchema()
consolidated_image_data_schema = ConsolidatedImageDataSchema()
image_analysis_list_response_schema = ImageAnalysisListResponseSchema()
consolidated_data_list_response_schema = ConsolidatedDataListResponseSchema()
analytics_response_schema = AnalyticsResponseSchema()
image_analysis_query_schema = ImageAnalysisQuerySchema()
analytics_query_schema = AnalyticsQuerySchema()
image_analysis_error_schema = ImageAnalysisErrorSchema()

def get_enhanced_model_registry() -> Dict:
    """Get registry of enhanced API models for Flask-RESTX"""
    return {
        'EnhancedBoundingBox': enhanced_bounding_box_schema,
        'EnhancedVehicleDetection': enhanced_vehicle_detection_schema,
        'SkyAnalysis': sky_analysis_schema,
        'ImageAnalysisResult': image_analysis_result_schema,
        'ConsolidatedImageData': consolidated_image_data_schema,
        'ImageAnalysisListResponse': image_analysis_list_response_schema,
        'ConsolidatedDataListResponse': consolidated_data_list_response_schema,
        'AnalyticsResponse': analytics_response_schema,
        'ImageAnalysisQuery': image_analysis_query_schema,
        'AnalyticsQuery': analytics_query_schema,
        'ImageAnalysisError': image_analysis_error_schema,
    }

def create_flask_restx_models(api):
    """Create Flask-RESTX models for Swagger documentation"""
    
    # Enhanced Bounding Box Model
    bounding_box_model = api.model('EnhancedBoundingBox', {
        'x': fields.Integer(required=True, description='X coordinate'),
        'y': fields.Integer(required=True, description='Y coordinate'),
        'width': fields.Integer(required=True, description='Width'),
        'height': fields.Integer(required=True, description='Height'),
        'confidence': fields.Float(required=True, description='Detection confidence')
    })
    
    # Enhanced Vehicle Detection Model
    vehicle_detection_model = api.model('EnhancedVehicleDetection', {
        'detection_id': fields.String(required=True, description='Unique detection ID'),
        'timestamp': fields.DateTime(required=True, description='Detection timestamp'),
        'vehicle_type': fields.String(required=True, description='Vehicle type', 
                                     enum=['pedestrian', 'bicycle', 'motorcycle', 'car', 
                                          'truck', 'bus', 'van', 'delivery_truck', 
                                          'emergency_vehicle', 'unknown']),
        'confidence': fields.Float(required=True, description='Detection confidence'),
        'bounding_box': fields.Nested(bounding_box_model, required=True),
        'additional_metadata': fields.Raw(description='Additional metadata')
    })
    
    # Sky Analysis Model
    sky_analysis_model = api.model('SkyAnalysis', {
        'analysis_id': fields.String(required=True, description='Unique analysis ID'),
        'timestamp': fields.DateTime(required=True, description='Analysis timestamp'),
        'condition': fields.String(required=True, description='Sky condition',
                                  enum=['clear', 'partly_cloudy', 'overcast', 'stormy',
                                       'night_clear', 'night_cloudy', 'dawn_dusk', 'unknown']),
        'confidence': fields.Float(required=True, description='Analysis confidence'),
        'light_level': fields.Float(description='Light level (0-1)'),
        'cloud_coverage': fields.Float(description='Cloud coverage (0-1)'),
        'additional_metadata': fields.Raw(description='Additional metadata')
    })
    
    # Image Analysis Result Model
    image_analysis_model = api.model('ImageAnalysisResult', {
        'image_id': fields.String(required=True, description='Unique image ID'),
        'image_path': fields.String(required=True, description='Path to image'),
        'timestamp': fields.DateTime(required=True, description='Analysis timestamp'),
        'trigger_source': fields.String(required=True, description='Analysis trigger source',
                                       enum=['radar', 'manual', 'scheduled', 'test', 'unknown']),
        'vehicle_detections': fields.List(fields.Nested(vehicle_detection_model)),
        'sky_analysis': fields.Nested(sky_analysis_model),
        'processing_time_ms': fields.Float(description='Processing time in milliseconds'),
        'image_metadata': fields.Raw(description='Image metadata')
    })
    
    # Consolidated Data Model
    consolidated_data_model = api.model('ConsolidatedImageData', {
        'consolidation_id': fields.String(required=True, description='Unique consolidation ID'),
        'timestamp': fields.DateTime(required=True, description='Consolidation timestamp'),
        'image_analysis': fields.Nested(image_analysis_model),
        'weather_data': fields.Raw(description='Weather sensor data'),
        'system_metrics': fields.Raw(description='System performance metrics'),
        'trigger_source': fields.String(description='Analysis trigger source'),
        'processing_metadata': fields.Raw(description='Processing metadata')
    })
    
    # List Response Models
    image_analysis_list_model = api.model('ImageAnalysisListResponse', {
        'results': fields.List(fields.Nested(image_analysis_model)),
        'count': fields.Integer(description='Number of results'),
        'timespan_seconds': fields.Integer(description='Time span covered'),
        'page': fields.Integer(description='Current page number'),
        'per_page': fields.Integer(description='Results per page')
    })
    
    consolidated_data_list_model = api.model('ConsolidatedDataListResponse', {
        'results': fields.List(fields.Nested(consolidated_data_model)),
        'count': fields.Integer(description='Number of results'),
        'timespan_seconds': fields.Integer(description='Time span covered'),
        'page': fields.Integer(description='Current page number'),
        'per_page': fields.Integer(description='Results per page')
    })
    
    # Analytics Models
    analytics_model = api.model('AnalyticsResponse', {
        'vehicle_statistics': fields.Raw(description='Vehicle detection statistics'),
        'sky_statistics': fields.Raw(description='Sky condition statistics'),
        'period_start': fields.DateTime(description='Analysis period start'),
        'period_end': fields.DateTime(description='Analysis period end'),
        'total_images_analyzed': fields.Integer(description='Total images analyzed')
    })
    
    # Error Model
    error_model = api.model('ImageAnalysisError', {
        'error': fields.String(required=True, description='Error type'),
        'message': fields.String(required=True, description='Error message'),
        'timestamp': fields.DateTime(description='Error timestamp'),
        'request_id': fields.String(description='Request ID'),
        'details': fields.Raw(description='Additional error details')
    })
    
    return {
        'EnhancedBoundingBox': bounding_box_model,
        'EnhancedVehicleDetection': vehicle_detection_model,
        'SkyAnalysis': sky_analysis_model,
        'ImageAnalysisResult': image_analysis_model,
        'ConsolidatedImageData': consolidated_data_model,
        'ImageAnalysisListResponse': image_analysis_list_model,
        'ConsolidatedDataListResponse': consolidated_data_list_model,
        'AnalyticsResponse': analytics_model,
        'ImageAnalysisError': error_model
    }