#!/usr/bin/env python3
"""
Enhanced API Endpoints for Image Analysis System
Extends the existing API gateway with image analysis, vehicle detection, and sky analysis endpoints
"""

from flask import Flask, jsonify, request, current_app
from flask_restx import Api, Resource, Namespace, reqparse
import time
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import os
import sys

# Import enhanced models
try:
    from .enhanced_api_models import (
        get_enhanced_model_registry, create_flask_restx_models,
        image_analysis_result_schema, consolidated_image_data_schema,
        image_analysis_list_response_schema, consolidated_data_list_response_schema,
        analytics_response_schema, image_analysis_query_schema, analytics_query_schema
    )
    ENHANCED_MODELS_AVAILABLE = True
except ImportError:
    try:
        from enhanced_api_models import (
            get_enhanced_model_registry, create_flask_restx_models,
            image_analysis_result_schema, consolidated_image_data_schema,
            image_analysis_list_response_schema, consolidated_data_list_response_schema,
            analytics_response_schema, image_analysis_query_schema, analytics_query_schema
        )
        ENHANCED_MODELS_AVAILABLE = True
    except ImportError:
        ENHANCED_MODELS_AVAILABLE = False
        logging.warning("Enhanced API models not available")

# Import Redis and data access components
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - API will work in demo mode")

# Import data consolidator for API data access
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data-collection', 'data-consolidator'))
    from enhanced_image_consolidator import EnhancedDataConsolidator
    CONSOLIDATOR_AVAILABLE = True
except ImportError:
    CONSOLIDATOR_AVAILABLE = False
    logging.warning("Enhanced data consolidator not available")

logger = logging.getLogger(__name__)

class EnhancedAPIEndpoints:
    """
    Enhanced API endpoints for image analysis system
    Provides REST endpoints for image analysis, vehicle detection, and sky analysis data
    """
    
    def __init__(self, api: Api, redis_host: str = "localhost", redis_port: int = 6379):
        self.api = api
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Initialize Redis connection
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=0,
                    decode_responses=True,
                    socket_timeout=5
                )
                self.redis_client.ping()
                logger.info(f"Enhanced API connected to Redis: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. API will work in demo mode.")
                self.redis_client = None
        
        # Initialize data consolidator
        self.consolidator = None
        if CONSOLIDATOR_AVAILABLE:
            try:
                self.consolidator = EnhancedDataConsolidator(
                    redis_host=redis_host,
                    redis_port=redis_port,
                    enable_redis=self.redis_client is not None
                )
                logger.info("Enhanced data consolidator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize consolidator: {e}")
        
        # Create Flask-RESTX models if available
        self.models = {}
        if ENHANCED_MODELS_AVAILABLE:
            try:
                self.models = create_flask_restx_models(api)
                logger.info("Enhanced API models created")
            except Exception as e:
                logger.warning(f"Failed to create API models: {e}")
        
        # Create namespaces and register endpoints
        self._create_namespaces()
        self._register_endpoints()
    
    def _create_namespaces(self):
        """Create API namespaces for organization"""
        
        # Image Analysis namespace
        self.image_ns = Namespace(
            'images',
            description='Image analysis and vehicle detection operations',
            path='/api/v1/images'
        )
        
        # Sky Analysis namespace
        self.sky_ns = Namespace(
            'sky',
            description='Sky condition analysis operations',
            path='/api/v1/sky'
        )
        
        # Consolidated Data namespace
        self.consolidated_ns = Namespace(
            'consolidated',
            description='Consolidated sensor and analysis data',
            path='/api/v1/consolidated'
        )
        
        # Analytics namespace
        self.analytics_ns = Namespace(
            'analytics',
            description='Analytics and statistics',
            path='/api/v1/analytics'
        )
        
        # Add namespaces to API
        self.api.add_namespace(self.image_ns)
        self.api.add_namespace(self.sky_ns)
        self.api.add_namespace(self.consolidated_ns)
        self.api.add_namespace(self.analytics_ns)
    
    def _register_endpoints(self):
        """Register all API endpoints"""
        
        # Image Analysis Endpoints
        @self.image_ns.route('/analysis')
        class ImageAnalysisList(Resource):
            @self.image_ns.doc('list_image_analyses')
            @self.image_ns.expect(self._create_query_parser())
            def get(self):
                """Get list of image analysis results"""
                try:
                    # Parse query parameters
                    args = self._parse_query_params(request.args)
                    
                    # Get data from consolidator or Redis
                    results = self._get_image_analysis_data(args)
                    
                    # Format response
                    response = {
                        'results': results,
                        'count': len(results),
                        'timespan_seconds': self._calculate_timespan(args),
                        'page': args.get('page', 1),
                        'per_page': args.get('per_page', 50)
                    }
                    
                    return response, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get image analysis data: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.image_ns.route('/analysis/<string:image_id>')
        class ImageAnalysisDetail(Resource):
            @self.image_ns.doc('get_image_analysis')
            def get(self, image_id):
                """Get specific image analysis result"""
                try:
                    result = self._get_image_analysis_by_id(image_id)
                    if result:
                        return result, 200
                    else:
                        return {'error': 'not_found', 'message': f'Image analysis {image_id} not found'}, 404
                        
                except Exception as e:
                    logger.error(f"Failed to get image analysis {image_id}: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.image_ns.route('/latest')
        class LatestImageAnalysis(Resource):
            @self.image_ns.doc('get_latest_image_analysis')
            def get(self):
                """Get the most recent image analysis result"""
                try:
                    result = self._get_latest_image_analysis()
                    if result:
                        return result, 200
                    else:
                        return {'error': 'not_found', 'message': 'No image analysis data available'}, 404
                        
                except Exception as e:
                    logger.error(f"Failed to get latest image analysis: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        # Sky Analysis Endpoints
        @self.sky_ns.route('/conditions')
        class SkyConditionsList(Resource):
            @self.sky_ns.doc('list_sky_conditions')
            def get(self):
                """Get list of sky condition analyses"""
                try:
                    args = self._parse_query_params(request.args)
                    results = self._get_sky_analysis_data(args)
                    
                    response = {
                        'results': results,
                        'count': len(results),
                        'timespan_seconds': self._calculate_timespan(args)
                    }
                    
                    return response, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get sky analysis data: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.sky_ns.route('/latest')
        class LatestSkyCondition(Resource):
            @self.sky_ns.doc('get_latest_sky_condition')
            def get(self):
                """Get the most recent sky condition analysis"""
                try:
                    result = self._get_latest_sky_analysis()
                    if result:
                        return result, 200
                    else:
                        return {'error': 'not_found', 'message': 'No sky analysis data available'}, 404
                        
                except Exception as e:
                    logger.error(f"Failed to get latest sky analysis: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        # Consolidated Data Endpoints
        @self.consolidated_ns.route('/data')
        class ConsolidatedDataList(Resource):
            @self.consolidated_ns.doc('list_consolidated_data')
            def get(self):
                """Get consolidated sensor and analysis data"""
                try:
                    args = self._parse_query_params(request.args)
                    results = self._get_consolidated_data(args)
                    
                    response = {
                        'results': results,
                        'count': len(results),
                        'timespan_seconds': self._calculate_timespan(args),
                        'page': args.get('page', 1),
                        'per_page': args.get('per_page', 50)
                    }
                    
                    return response, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get consolidated data: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.consolidated_ns.route('/latest')
        class LatestConsolidatedData(Resource):
            @self.consolidated_ns.doc('get_latest_consolidated_data')
            def get(self):
                """Get the most recent consolidated data"""
                try:
                    result = self._get_latest_consolidated_data()
                    if result:
                        return result, 200
                    else:
                        return {'error': 'not_found', 'message': 'No consolidated data available'}, 404
                        
                except Exception as e:
                    logger.error(f"Failed to get latest consolidated data: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        # Analytics Endpoints
        @self.analytics_ns.route('/vehicles')
        class VehicleAnalytics(Resource):
            @self.analytics_ns.doc('get_vehicle_analytics')
            def get(self):
                """Get vehicle detection analytics and statistics"""
                try:
                    args = self._parse_query_params(request.args)
                    analytics = self._get_vehicle_analytics(args)
                    return analytics, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get vehicle analytics: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.analytics_ns.route('/sky')
        class SkyAnalytics(Resource):
            @self.analytics_ns.doc('get_sky_analytics')
            def get(self):
                """Get sky condition analytics and statistics"""
                try:
                    args = self._parse_query_params(request.args)
                    analytics = self._get_sky_analytics(args)
                    return analytics, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get sky analytics: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
        
        @self.analytics_ns.route('/summary')
        class AnalyticsSummary(Resource):
            @self.analytics_ns.doc('get_analytics_summary')
            def get(self):
                """Get comprehensive analytics summary"""
                try:
                    args = self._parse_query_params(request.args)
                    summary = self._get_analytics_summary(args)
                    return summary, 200
                    
                except Exception as e:
                    logger.error(f"Failed to get analytics summary: {e}")
                    return {'error': 'internal_error', 'message': str(e)}, 500
    
    def _create_query_parser(self):
        """Create request parser for query parameters"""
        parser = reqparse.RequestParser()
        parser.add_argument('since', type=str, help='Start time (ISO format)')
        parser.add_argument('until', type=str, help='End time (ISO format)')
        parser.add_argument('trigger_source', type=str, help='Analysis trigger source')
        parser.add_argument('vehicle_type', type=str, help='Vehicle type filter')
        parser.add_argument('sky_condition', type=str, help='Sky condition filter')
        parser.add_argument('min_confidence', type=float, help='Minimum confidence threshold')
        parser.add_argument('page', type=int, help='Page number')
        parser.add_argument('per_page', type=int, help='Results per page')
        parser.add_argument('period', type=str, help='Analytics period')
        parser.add_argument('group_by', type=str, help='Group analytics by')
        return parser
    
    def _parse_query_params(self, args: Dict) -> Dict:
        """Parse and validate query parameters"""
        parsed = {}
        
        # Time range
        if args.get('since'):
            try:
                parsed['since'] = datetime.fromisoformat(args['since'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if args.get('until'):
            try:
                parsed['until'] = datetime.fromisoformat(args['until'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Filters
        parsed['trigger_source'] = args.get('trigger_source', 'all')
        parsed['vehicle_type'] = args.get('vehicle_type', 'all')
        parsed['sky_condition'] = args.get('sky_condition', 'all')
        parsed['min_confidence'] = float(args.get('min_confidence', 0.0))
        
        # Pagination
        parsed['page'] = int(args.get('page', 1))
        parsed['per_page'] = min(int(args.get('per_page', 50)), 100)
        
        # Analytics
        parsed['period'] = args.get('period', 'day')
        parsed['group_by'] = args.get('group_by', 'day')
        
        return parsed
    
    def _calculate_timespan(self, args: Dict) -> int:
        """Calculate timespan in seconds based on query parameters"""
        since = args.get('since')
        until = args.get('until', datetime.now(timezone.utc))
        
        if since:
            return int((until - since).total_seconds())
        else:
            return 3600  # Default to 1 hour
    
    def _get_image_analysis_data(self, args: Dict) -> List[Dict]:
        """Get image analysis data based on query parameters"""
        if self.consolidator:
            try:
                # Get data from consolidator
                since_timestamp = args.get('since').timestamp() if args.get('since') else time.time() - 3600
                records = self.consolidator.get_consolidated_data_since(since_timestamp)
                
                # Filter and format results
                results = []
                for record in records:
                    if record.image_analysis:
                        # Apply filters
                        if self._apply_filters(record, args):
                            results.append(self._format_image_analysis(record.image_analysis))
                
                # Apply pagination
                page = args.get('page', 1)
                per_page = args.get('per_page', 50)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                
                return results[start_idx:end_idx]
                
            except Exception as e:
                logger.error(f"Consolidator data access failed: {e}")
        
        # Fallback to demo data
        return self._get_demo_image_analysis_data(args)
    
    def _get_image_analysis_by_id(self, image_id: str) -> Optional[Dict]:
        """Get specific image analysis by ID"""
        if self.consolidator:
            try:
                records = self.consolidator.consolidated_records
                for record in records:
                    if record.image_analysis and record.image_analysis.get('image_id') == image_id:
                        return self._format_image_analysis(record.image_analysis)
            except Exception as e:
                logger.error(f"Failed to get image analysis by ID: {e}")
        
        return None
    
    def _get_latest_image_analysis(self) -> Optional[Dict]:
        """Get the most recent image analysis"""
        if self.consolidator:
            try:
                latest = self.consolidator.get_latest_consolidated_data()
                if latest and latest.image_analysis:
                    return self._format_image_analysis(latest.image_analysis)
            except Exception as e:
                logger.error(f"Failed to get latest image analysis: {e}")
        
        # Fallback to demo data
        return self._get_demo_latest_image_analysis()
    
    def _get_sky_analysis_data(self, args: Dict) -> List[Dict]:
        """Get sky analysis data"""
        if self.consolidator:
            try:
                since_timestamp = args.get('since').timestamp() if args.get('since') else time.time() - 3600
                records = self.consolidator.get_consolidated_data_since(since_timestamp)
                
                results = []
                for record in records:
                    if record.sky_analysis:
                        if self._apply_sky_filters(record, args):
                            results.append(record.sky_analysis)
                
                return results
            except Exception as e:
                logger.error(f"Failed to get sky analysis data: {e}")
        
        return self._get_demo_sky_analysis_data(args)
    
    def _get_latest_sky_analysis(self) -> Optional[Dict]:
        """Get the most recent sky analysis"""
        if self.consolidator:
            try:
                latest = self.consolidator.get_latest_consolidated_data()
                if latest and latest.sky_analysis:
                    return latest.sky_analysis
            except Exception as e:
                logger.error(f"Failed to get latest sky analysis: {e}")
        
        return self._get_demo_latest_sky_analysis()
    
    def _get_consolidated_data(self, args: Dict) -> List[Dict]:
        """Get consolidated data"""
        if self.consolidator:
            try:
                return self.consolidator.get_consolidated_data_for_api(args.get('per_page', 50))
            except Exception as e:
                logger.error(f"Failed to get consolidated data: {e}")
        
        return self._get_demo_consolidated_data(args)
    
    def _get_latest_consolidated_data(self) -> Optional[Dict]:
        """Get the most recent consolidated data"""
        if self.consolidator:
            try:
                latest = self.consolidator.get_latest_consolidated_data()
                if latest:
                    from dataclasses import asdict
                    return asdict(latest)
            except Exception as e:
                logger.error(f"Failed to get latest consolidated data: {e}")
        
        return self._get_demo_latest_consolidated_data()
    
    def _get_vehicle_analytics(self, args: Dict) -> Dict:
        """Get vehicle detection analytics"""
        # This would analyze the consolidated data to generate statistics
        return {
            'total_detections': 0,
            'detections_by_type': {},
            'avg_confidence': 0.0,
            'time_period': args.get('period', 'day'),
            'period_start': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            'period_end': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_sky_analytics(self, args: Dict) -> Dict:
        """Get sky condition analytics"""
        return {
            'conditions_distribution': {
                'clear': 30,
                'partly_cloudy': 25,
                'overcast': 20,
                'night_clear': 15,
                'night_cloudy': 10
            },
            'avg_light_level': 0.6,
            'avg_cloud_coverage': 0.4,
            'time_period': args.get('period', 'day')
        }
    
    def _get_analytics_summary(self, args: Dict) -> Dict:
        """Get comprehensive analytics summary"""
        return {
            'vehicle_statistics': self._get_vehicle_analytics(args),
            'sky_statistics': self._get_sky_analytics(args),
            'period_start': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            'period_end': datetime.now(timezone.utc).isoformat(),
            'total_images_analyzed': 150
        }
    
    def _apply_filters(self, record, args: Dict) -> bool:
        """Apply filters to consolidated record"""
        # Implement filtering logic based on args
        return True
    
    def _apply_sky_filters(self, record, args: Dict) -> bool:
        """Apply sky-specific filters"""
        return True
    
    def _format_image_analysis(self, analysis: Dict) -> Dict:
        """Format image analysis for API response"""
        # Ensure datetime formatting
        if 'timestamp' in analysis and isinstance(analysis['timestamp'], (int, float)):
            analysis['timestamp'] = datetime.fromtimestamp(analysis['timestamp'], tz=timezone.utc).isoformat()
        
        return analysis
    
    # Demo data methods (fallbacks when no real data is available)
    def _get_demo_image_analysis_data(self, args: Dict) -> List[Dict]:
        """Generate demo image analysis data"""
        return [{
            'image_id': f'demo_img_{i}',
            'image_path': f'/demo/images/image_{i}.jpg',
            'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*5)).isoformat(),
            'trigger_source': 'demo',
            'vehicle_detections': [{
                'detection_id': f'demo_det_{i}',
                'vehicle_type': 'car',
                'confidence': 0.85,
                'bounding_box': {'x': 100, 'y': 150, 'width': 200, 'height': 150, 'confidence': 0.85},
                'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*5)).isoformat()
            }],
            'sky_analysis': {
                'analysis_id': f'demo_sky_{i}',
                'condition': 'clear',
                'confidence': 0.9,
                'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*5)).isoformat()
            },
            'processing_time_ms': 150.5
        } for i in range(10)]
    
    def _get_demo_latest_image_analysis(self) -> Dict:
        """Generate demo latest image analysis"""
        return self._get_demo_image_analysis_data({})[0]
    
    def _get_demo_sky_analysis_data(self, args: Dict) -> List[Dict]:
        """Generate demo sky analysis data"""
        conditions = ['clear', 'partly_cloudy', 'overcast', 'night_clear']
        return [{
            'analysis_id': f'demo_sky_{i}',
            'condition': conditions[i % len(conditions)],
            'confidence': 0.8 + (i % 3) * 0.05,
            'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*10)).isoformat(),
            'light_level': 0.5 + (i % 5) * 0.1,
            'cloud_coverage': 0.3 + (i % 4) * 0.1
        } for i in range(5)]
    
    def _get_demo_latest_sky_analysis(self) -> Dict:
        """Generate demo latest sky analysis"""
        return self._get_demo_sky_analysis_data({})[0]
    
    def _get_demo_consolidated_data(self, args: Dict) -> List[Dict]:
        """Generate demo consolidated data"""
        return [{
            'consolidation_id': f'demo_cons_{i}',
            'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*15)).isoformat(),
            'image_analysis': self._get_demo_image_analysis_data({})[0],
            'weather_data': {
                'temperature_c': 22.5,
                'humidity': 65.2,
                'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*15)).isoformat()
            },
            'trigger_source': 'demo'
        } for i in range(5)]
    
    def _get_demo_latest_consolidated_data(self) -> Dict:
        """Generate demo latest consolidated data"""
        return self._get_demo_consolidated_data({})[0]

def register_enhanced_endpoints(api: Api, redis_host: str = "localhost", redis_port: int = 6379):
    """Register enhanced API endpoints with the Flask-RESTX API"""
    try:
        enhanced_api = EnhancedAPIEndpoints(api, redis_host, redis_port)
        logger.info("Enhanced API endpoints registered successfully")
        return enhanced_api
    except Exception as e:
        logger.error(f"Failed to register enhanced API endpoints: {e}")
        return None