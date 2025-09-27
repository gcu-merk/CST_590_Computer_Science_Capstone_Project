#!/usr/bin/env python3
"""
API Gateway Enhancement - Consolidated Data Endpoints

Enhanced API to serve consolidated traffic monitoring data from the database
persistence layer. Provides structured access to traffic records, analytics,
and summary data for external consumption.

New Endpoints:
- /api/v1/traffic/recent - Recent consolidated traffic records
- /api/v1/traffic/summary - Daily/weekly traffic summaries
- /api/v1/traffic/analytics - Speed analytics and trends
- /api/v1/traffic/search - Search traffic records by criteria

Architecture Integration:
Radar Motion -> Consolidator -> Database Persistence -> API -> External Website
"""

import time
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

from flask import Flask, jsonify, request

# Optional CORS support
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConsolidatedDataAPI:
    """
    Enhanced API for consolidated traffic monitoring data
    Serves structured data from database persistence layer
    """
    
    def __init__(self, db_path: str = "/app/data/traffic_data.db"):
        self.db_path = db_path
        self.db_connection = None
        
        # Flask app setup
        self.app = Flask(__name__)
        
        # Enable CORS if available
        if CORS_AVAILABLE:
            CORS(self.app)
        
        # Register routes
        self._register_routes()
        
        logger.info("Consolidated Data API initialized")
    
    def connect_database(self) -> bool:
        """Connect to the traffic monitoring database"""
        try:
            if not Path(self.db_path).exists():
                logger.error(f"Database not found: {self.db_path}")
                return False
            
            self.db_connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            
            # Enable row factory for dict-like access
            self.db_connection.row_factory = sqlite3.Row
            
            logger.info(f"✅ Connected to database: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.route('/api/v1/traffic/recent', methods=['GET'])
        def get_recent_traffic():
            """Get recent consolidated traffic records"""
            try:
                # Parse query parameters
                hours = request.args.get('hours', default=24, type=int)
                limit = request.args.get('limit', default=100, type=int)
                
                # Validate parameters
                hours = max(1, min(hours, 168))  # 1 hour to 1 week
                limit = max(1, min(limit, 1000))  # 1 to 1000 records
                
                records = self._get_recent_records(hours, limit)
                
                return jsonify({
                    'success': True,
                    'data': records,
                    'metadata': {
                        'hours': hours,
                        'limit': limit,
                        'count': len(records),
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error fetching recent traffic: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/traffic/summary', methods=['GET'])
        def get_traffic_summary():
            """Get daily traffic summaries"""
            try:
                days = request.args.get('days', default=7, type=int)
                days = max(1, min(days, 30))  # 1 to 30 days
                
                summaries = self._get_daily_summaries(days)
                
                return jsonify({
                    'success': True,
                    'data': summaries,
                    'metadata': {
                        'days': days,
                        'count': len(summaries),
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error fetching traffic summary: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/traffic/analytics', methods=['GET'])
        def get_traffic_analytics():
            """Get traffic analytics and trends"""
            try:
                period = request.args.get('period', default='week')
                
                analytics = self._get_traffic_analytics(period)
                
                return jsonify({
                    'success': True,
                    'data': analytics,
                    'metadata': {
                        'period': period,
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error fetching traffic analytics: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/traffic/search', methods=['GET'])
        def search_traffic():
            """Search traffic records by criteria"""
            try:
                # Parse search criteria
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                min_speed = request.args.get('min_speed', type=float)
                max_speed = request.args.get('max_speed', type=float)
                vehicle_type = request.args.get('vehicle_type')
                limit = request.args.get('limit', default=100, type=int)
                
                records = self._search_traffic_records(
                    start_date=start_date,
                    end_date=end_date,
                    min_speed=min_speed,
                    max_speed=max_speed,
                    vehicle_type=vehicle_type,
                    limit=limit
                )
                
                return jsonify({
                    'success': True,
                    'data': records,
                    'metadata': {
                        'count': len(records),
                        'criteria': {
                            'start_date': start_date,
                            'end_date': end_date,
                            'min_speed': min_speed,
                            'max_speed': max_speed,
                            'vehicle_type': vehicle_type,
                            'limit': limit
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error searching traffic records: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/health/database', methods=['GET'])
        def database_health():
            """Database health check"""
            try:
                if not self.db_connection:
                    return jsonify({
                        'success': False,
                        'status': 'disconnected'
                    }), 503
                
                # Test database connection
                cursor = self.db_connection.execute("SELECT COUNT(*) as count FROM traffic_records")
                record_count = cursor.fetchone()['count']
                
                # Get database size
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                
                return jsonify({
                    'success': True,
                    'status': 'connected',
                    'database': {
                        'path': self.db_path,
                        'size_mb': round(db_size / (1024 * 1024), 2),
                        'record_count': record_count,
                        'last_check': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return jsonify({
                    'success': False,
                    'status': 'error',
                    'error': str(e)
                }), 500
    
    def _get_recent_records(self, hours: int, limit: int) -> List[Dict[str, Any]]:
        """Get recent traffic records from normalized 3NF schema"""
        if not self.db_connection:
            return []
        
        # Check if we have normalized schema, fallback to legacy if needed
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_detections'"
        )
        has_normalized_schema = cursor.fetchone() is not None
        
        if has_normalized_schema:
            return self._get_recent_records_normalized(hours, limit)
        else:
            return self._get_recent_records_legacy(hours, limit)
    
    def _get_recent_records_normalized(self, hours: int, limit: int) -> List[Dict[str, Any]]:
        """Get recent records from normalized 3NF schema using JOINs"""
        import time
        cutoff_timestamp = time.time() - (hours * 3600)  # Convert hours to seconds
        
        cursor = self.db_connection.execute("""
            SELECT 
                -- Core detection info
                td.id,
                td.correlation_id,
                td.timestamp,
                td.trigger_source,
                td.location_id,
                td.processing_metadata,
                
                -- Radar detection data
                rd.speed_mph,
                rd.speed_mps,
                rd.confidence as radar_confidence,
                rd.alert_level,
                rd.direction,
                rd.distance,
                
                -- Camera detection data
                cd.vehicle_count,
                cd.vehicle_types,
                cd.detection_confidence,
                cd.image_path,
                cd.inference_time_ms,
                
                -- Weather data (aggregated from multiple sources)
                GROUP_CONCAT(DISTINCT wc.source) as weather_sources,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as dht22_temperature,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.humidity END) as dht22_humidity,
                MAX(CASE WHEN wc.source = 'airport' THEN wc.temperature END) as airport_temperature,
                MAX(CASE WHEN wc.source = 'airport' THEN wc.conditions END) as airport_conditions,
                MAX(CASE WHEN wc.source = 'airport' THEN wc.wind_speed END) as wind_speed
                
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            LEFT JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            LEFT JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE td.timestamp >= ?
            GROUP BY td.id, td.correlation_id, td.timestamp, td.trigger_source, td.location_id,
                     rd.speed_mph, rd.speed_mps, rd.confidence, rd.alert_level, rd.direction, rd.distance,
                     cd.vehicle_count, cd.vehicle_types, cd.detection_confidence, cd.image_path, cd.inference_time_ms
            ORDER BY td.timestamp DESC
            LIMIT ?
        """, (cutoff_timestamp, limit))
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            
            # Convert timestamp to ISO format
            if record['timestamp']:
                record['timestamp_iso'] = datetime.fromtimestamp(record['timestamp']).isoformat()
            
            # Parse JSON fields safely
            for field in ['processing_metadata', 'vehicle_types']:
                if record.get(field):
                    try:
                        record[field] = json.loads(record[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Structure weather data
            record['weather_data'] = {
                'sources': record['weather_sources'].split(',') if record['weather_sources'] else [],
                'dht22': {
                    'temperature': record['dht22_temperature'],
                    'humidity': record['dht22_humidity']
                } if record['dht22_temperature'] is not None else None,
                'airport': {
                    'temperature': record['airport_temperature'],
                    'conditions': record['airport_conditions'],
                    'wind_speed': record['wind_speed']
                } if record['airport_temperature'] is not None else None
            }
            
            # Clean up individual weather fields from top level
            for field in ['weather_sources', 'dht22_temperature', 'dht22_humidity', 
                         'airport_temperature', 'airport_conditions', 'wind_speed']:
                record.pop(field, None)
            
            records.append(record)
        
        return records
    
    def _get_recent_records_legacy(self, hours: int, limit: int) -> List[Dict[str, Any]]:
        """Fallback for legacy denormalized schema"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Check if legacy table exists
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_records'"
        )
        if not cursor.fetchone():
            return []
        
        cursor = self.db_connection.execute("""
            SELECT 
                id, timestamp, trigger_source,
                radar_speed, vehicle_count, detection_confidence,
                temperature, humidity, weather_condition,
                created_at
            FROM traffic_records 
            WHERE datetime(timestamp) >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (cutoff_time, limit))
        
        records = []
        for row in cursor.fetchall():
            records.append(dict(row))
        
        return records
    
    def _get_daily_summaries(self, days: int) -> List[Dict[str, Any]]:
        """Get daily traffic summaries from normalized 3NF schema"""
        if not self.db_connection:
            return []
        
        # Check if we have normalized schema
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_detections'"
        )
        has_normalized_schema = cursor.fetchone() is not None
        
        if has_normalized_schema:
            return self._get_daily_summaries_normalized(days)
        else:
            return self._get_daily_summaries_legacy(days)
    
    def _get_daily_summaries_normalized(self, days: int) -> List[Dict[str, Any]]:
        """Generate daily summaries from normalized data using analytical queries"""
        import time
        
        # Calculate time range (days ago to now)
        end_timestamp = time.time()
        start_timestamp = end_timestamp - (days * 24 * 3600)
        
        cursor = self.db_connection.execute("""
            SELECT 
                -- Date grouping (convert timestamp to date)
                date(td.timestamp, 'unixepoch', 'localtime') as date,
                
                -- Traffic statistics
                COUNT(td.id) as total_detections,
                COUNT(rd.detection_id) as radar_detections,
                COUNT(cd.detection_id) as camera_detections,
                
                -- Speed analytics (from radar data)
                AVG(rd.speed_mph) as avg_speed_mph,
                MIN(rd.speed_mph) as min_speed_mph,
                MAX(rd.speed_mph) as max_speed_mph,
                COUNT(CASE WHEN rd.speed_mph > 25 THEN 1 END) as speed_violations,
                
                -- Vehicle analytics (from camera data)
                AVG(cd.vehicle_count) as avg_vehicle_count,
                SUM(cd.vehicle_count) as total_vehicles,
                
                -- Weather summary (aggregated from weather conditions)
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as avg_temperature,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.humidity END) as avg_humidity,
                GROUP_CONCAT(DISTINCT CASE WHEN wc.source = 'airport' THEN wc.conditions END) as weather_conditions,
                
                -- Alert level distribution
                COUNT(CASE WHEN rd.alert_level = 'high' THEN 1 END) as high_alerts,
                COUNT(CASE WHEN rd.alert_level = 'medium' THEN 1 END) as medium_alerts,
                COUNT(CASE WHEN rd.alert_level = 'low' THEN 1 END) as low_alerts,
                
                -- Source breakdown
                COUNT(CASE WHEN td.trigger_source = 'radar' THEN 1 END) as radar_triggers,
                COUNT(CASE WHEN td.trigger_source = 'camera' THEN 1 END) as camera_triggers
                
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            LEFT JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            LEFT JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE td.timestamp >= ? AND td.timestamp <= ?
            GROUP BY date(td.timestamp, 'unixepoch', 'localtime')
            ORDER BY date DESC
        """, (start_timestamp, end_timestamp))
        
        summaries = []
        for row in cursor.fetchall():
            summary = dict(row)
            
            # Calculate additional metrics
            summary['speed_stats'] = {
                'avg_mph': round(summary['avg_speed_mph'], 1) if summary['avg_speed_mph'] else 0,
                'min_mph': summary['min_speed_mph'],
                'max_mph': summary['max_speed_mph'],
                'violations': summary['speed_violations']
            }
            
            summary['weather_summary'] = {
                'avg_temperature': round(summary['avg_temperature'], 1) if summary['avg_temperature'] else None,
                'avg_humidity': round(summary['avg_humidity'], 1) if summary['avg_humidity'] else None,
                'conditions': summary['weather_conditions'].split(',') if summary['weather_conditions'] else []
            }
            
            summary['alert_distribution'] = {
                'high': summary['high_alerts'],
                'medium': summary['medium_alerts'], 
                'low': summary['low_alerts']
            }
            
            summary['trigger_sources'] = {
                'radar': summary['radar_triggers'],
                'camera': summary['camera_triggers']
            }
            
            # Clean up individual fields that are now in structured objects
            cleanup_fields = ['avg_speed_mph', 'min_speed_mph', 'max_speed_mph', 'speed_violations',
                            'avg_temperature', 'avg_humidity', 'weather_conditions',
                            'high_alerts', 'medium_alerts', 'low_alerts',
                            'radar_triggers', 'camera_triggers']
            
            for field in cleanup_fields:
                summary.pop(field, None)
            
            summaries.append(summary)
        
        return summaries
    
    def _get_daily_summaries_legacy(self, days: int) -> List[Dict[str, Any]]:
        """Fallback for legacy schema if it exists"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        # Check if daily_summaries table exists  
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_summaries'"
        )
        if cursor.fetchone():
            # Use existing summaries table
            cursor = self.db_connection.execute("""
                SELECT * FROM daily_summaries 
                WHERE date >= ?
                ORDER BY date DESC
            """, (cutoff_date,))
        else:
            # Generate summaries from traffic_records if available
            cursor = self.db_connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_records'"
            )
            if not cursor.fetchone():
                return []
            
            cursor = self.db_connection.execute("""
                SELECT 
                    date(timestamp) as date,
                    COUNT(*) as total_detections,
                    AVG(radar_speed) as avg_speed,
                    MAX(radar_speed) as max_speed,
                    AVG(vehicle_count) as avg_vehicles
                FROM traffic_records 
                WHERE date(timestamp) >= ?
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """, (cutoff_date,))
        
        summaries = []
        for row in cursor.fetchall():
            summaries.append(dict(row))
        
        return summaries
    
    def _get_traffic_analytics(self, period: str) -> Dict[str, Any]:
        """Get traffic analytics from normalized 3NF schema"""
        if not self.db_connection:
            return {}
        
        # Check if we have normalized schema
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_detections'"
        )
        has_normalized_schema = cursor.fetchone() is not None
        
        if has_normalized_schema:
            return self._get_analytics_normalized(period)
        else:
            return self._get_analytics_legacy(period)
    
    def _get_analytics_normalized(self, period: str) -> Dict[str, Any]:
        """Generate comprehensive analytics from normalized 3NF schema"""
        import time
        
        # Determine time range based on period
        current_time = time.time()
        if period == 'day':
            cutoff_timestamp = current_time - (24 * 3600)
        elif period == 'week':
            cutoff_timestamp = current_time - (7 * 24 * 3600)
        elif period == 'month':
            cutoff_timestamp = current_time - (30 * 24 * 3600)
        else:
            cutoff_timestamp = current_time - (7 * 24 * 3600)  # Default to week
        
        # 1. Basic traffic statistics with comprehensive JOINs
        cursor = self.db_connection.execute("""
            SELECT 
                COUNT(DISTINCT td.id) as total_detections,
                COUNT(DISTINCT rd.detection_id) as radar_detections,
                COUNT(DISTINCT cd.detection_id) as camera_detections,
                
                -- Speed analytics
                AVG(rd.speed_mph) as avg_speed_mph,
                MIN(rd.speed_mph) as min_speed_mph,
                MAX(rd.speed_mph) as max_speed_mph,
                MEDIAN(rd.speed_mph) as median_speed_mph,
                COUNT(CASE WHEN rd.speed_mph > 25 THEN 1 END) as speed_violations_25,
                COUNT(CASE WHEN rd.speed_mph > 35 THEN 1 END) as speed_violations_35,
                
                -- Vehicle analytics
                AVG(cd.vehicle_count) as avg_vehicle_count,
                SUM(cd.vehicle_count) as total_vehicles_detected,
                AVG(cd.detection_confidence) as avg_detection_confidence,
                
                -- Weather analytics
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as avg_temperature,
                MIN(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as min_temperature,
                MAX(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as max_temperature,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.humidity END) as avg_humidity,
                
                -- Alert level distribution
                COUNT(CASE WHEN rd.alert_level = 'high' THEN 1 END) as high_alerts,
                COUNT(CASE WHEN rd.alert_level = 'medium' THEN 1 END) as medium_alerts,
                COUNT(CASE WHEN rd.alert_level = 'low' THEN 1 END) as low_alerts,
                
                -- Direction analysis
                COUNT(CASE WHEN rd.direction = 'approaching' THEN 1 END) as approaching_vehicles,
                COUNT(CASE WHEN rd.direction = 'receding' THEN 1 END) as receding_vehicles
                
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            LEFT JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            LEFT JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE td.timestamp >= ?
        """, (cutoff_timestamp,))
        
        basic_stats = dict(cursor.fetchone())
        
        # 2. Hourly distribution analysis
        cursor = self.db_connection.execute("""
            SELECT 
                strftime('%H', datetime(td.timestamp, 'unixepoch', 'localtime')) as hour,
                COUNT(DISTINCT td.id) as detection_count,
                AVG(rd.speed_mph) as avg_speed,
                MAX(rd.speed_mph) as max_speed,
                AVG(cd.vehicle_count) as avg_vehicles,
                COUNT(CASE WHEN rd.alert_level IN ('high', 'medium') THEN 1 END) as alerts
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            WHERE td.timestamp >= ?
            GROUP BY strftime('%H', datetime(td.timestamp, 'unixepoch', 'localtime'))
            ORDER BY hour
        """, (cutoff_timestamp,))
        
        hourly_data = [dict(row) for row in cursor.fetchall()]
        
        # 3. Vehicle type distribution (from camera data)
        cursor = self.db_connection.execute("""
            SELECT 
                cd.vehicle_types,
                COUNT(*) as detection_count,
                AVG(rd.speed_mph) as avg_speed_for_type
            FROM camera_detections cd
            JOIN traffic_detections td ON cd.detection_id = td.id
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            WHERE td.timestamp >= ? AND cd.vehicle_types IS NOT NULL
            GROUP BY cd.vehicle_types
            ORDER BY detection_count DESC
            LIMIT 10
        """, (cutoff_timestamp,))
        
        vehicle_type_data = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse vehicle types JSON
            try:
                if row_dict['vehicle_types']:
                    row_dict['vehicle_types'] = json.loads(row_dict['vehicle_types'])
            except (json.JSONDecodeError, TypeError):
                pass
            vehicle_type_data.append(row_dict)
        
        # 4. Weather correlation analysis
        cursor = self.db_connection.execute("""
            SELECT 
                CASE 
                    WHEN wc.temperature < 32 THEN 'freezing'
                    WHEN wc.temperature < 50 THEN 'cold'
                    WHEN wc.temperature < 70 THEN 'cool'
                    WHEN wc.temperature < 85 THEN 'warm'
                    ELSE 'hot'
                END as temp_range,
                wc.conditions as weather_condition,
                COUNT(DISTINCT td.id) as detection_count,
                AVG(rd.speed_mph) as avg_speed,
                AVG(cd.vehicle_count) as avg_vehicles
            FROM traffic_detections td
            JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            JOIN weather_conditions wc ON twc.weather_id = wc.id
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            WHERE td.timestamp >= ? AND wc.temperature IS NOT NULL
            GROUP BY temp_range, wc.conditions
            ORDER BY detection_count DESC
        """, (cutoff_timestamp,))
        
        weather_correlation = [dict(row) for row in cursor.fetchall()]
        
        # 5. Speed distribution analysis
        cursor = self.db_connection.execute("""
            SELECT 
                CASE 
                    WHEN rd.speed_mph < 10 THEN '0-10 mph'
                    WHEN rd.speed_mph < 20 THEN '10-20 mph'
                    WHEN rd.speed_mph < 30 THEN '20-30 mph'
                    WHEN rd.speed_mph < 40 THEN '30-40 mph'
                    WHEN rd.speed_mph < 50 THEN '40-50 mph'
                    ELSE '50+ mph'
                END as speed_range,
                COUNT(*) as count,
                AVG(cd.vehicle_count) as avg_vehicles_in_range
            FROM radar_detections rd
            JOIN traffic_detections td ON rd.detection_id = td.id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            WHERE td.timestamp >= ? AND rd.speed_mph IS NOT NULL
            GROUP BY speed_range
            ORDER BY MIN(rd.speed_mph)
        """, (cutoff_timestamp,))
        
        speed_distribution = [dict(row) for row in cursor.fetchall()]
        
        return {
            'period': period,
            'time_range': {
                'start': datetime.fromtimestamp(cutoff_timestamp).isoformat(),
                'end': datetime.fromtimestamp(current_time).isoformat(),
                'duration_hours': (current_time - cutoff_timestamp) / 3600
            },
            'basic_statistics': {
                'total_detections': basic_stats['total_detections'],
                'radar_detections': basic_stats['radar_detections'], 
                'camera_detections': basic_stats['camera_detections'],
                'detection_rate_per_hour': round((basic_stats['total_detections'] or 0) / ((current_time - cutoff_timestamp) / 3600), 2)
            },
            'speed_analytics': {
                'avg_mph': round(basic_stats['avg_speed_mph'], 1) if basic_stats['avg_speed_mph'] else 0,
                'min_mph': basic_stats['min_speed_mph'],
                'max_mph': basic_stats['max_speed_mph'],
                'median_mph': basic_stats['median_speed_mph'],
                'violations_25mph': basic_stats['speed_violations_25'],
                'violations_35mph': basic_stats['speed_violations_35'],
                'distribution': speed_distribution
            },
            'vehicle_analytics': {
                'avg_count_per_detection': round(basic_stats['avg_vehicle_count'], 2) if basic_stats['avg_vehicle_count'] else 0,
                'total_vehicles': basic_stats['total_vehicles_detected'],
                'avg_detection_confidence': round(basic_stats['avg_detection_confidence'], 3) if basic_stats['avg_detection_confidence'] else 0,
                'type_distribution': vehicle_type_data
            },
            'weather_analytics': {
                'avg_temperature': round(basic_stats['avg_temperature'], 1) if basic_stats['avg_temperature'] else None,
                'temperature_range': {
                    'min': basic_stats['min_temperature'],
                    'max': basic_stats['max_temperature']
                },
                'avg_humidity': round(basic_stats['avg_humidity'], 1) if basic_stats['avg_humidity'] else None,
                'weather_correlation': weather_correlation
            },
            'temporal_patterns': {
                'hourly_distribution': hourly_data,
                'peak_hour': max(hourly_data, key=lambda x: x['detection_count'])['hour'] if hourly_data else None
            },
            'alert_distribution': {
                'high': basic_stats['high_alerts'],
                'medium': basic_stats['medium_alerts'],
                'low': basic_stats['low_alerts']
            },
            'direction_analysis': {
                'approaching': basic_stats['approaching_vehicles'],
                'receding': basic_stats['receding_vehicles']
            },
            'schema_type': '3NF_normalized'
        }
    
    def _get_analytics_legacy(self, period: str) -> Dict[str, Any]:
        """Fallback analytics for legacy schema"""
        # Determine time range
        if period == 'day':
            cutoff_time = datetime.now() - timedelta(days=1)
        elif period == 'week':
            cutoff_time = datetime.now() - timedelta(days=7)
        elif period == 'month':
            cutoff_time = datetime.now() - timedelta(days=30)
        else:
            cutoff_time = datetime.now() - timedelta(days=7)
        
        # Check if legacy table exists
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_records'"
        )
        if not cursor.fetchone():
            return {'error': 'No traffic data tables found', 'schema_type': 'none'}
        
        # Basic stats from legacy schema
        cursor = self.db_connection.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(radar_speed) as avg_speed,
                MAX(radar_speed) as max_speed,
                MIN(radar_speed) as min_speed,
                COUNT(CASE WHEN radar_speed > 25 THEN 1 END) as speed_violations
            FROM traffic_records 
            WHERE datetime(timestamp) >= ? AND radar_speed IS NOT NULL
        """, (cutoff_time,))
        
        stats = dict(cursor.fetchone())
        
        return {
            'period': period,
            'basic_statistics': stats,
            'schema_type': 'legacy_denormalized'
        }
    
    def _search_traffic_records(self, **criteria) -> List[Dict[str, Any]]:
        """Search traffic records with normalized schema support"""
        if not self.db_connection:
            return []
        
        # Check if we have normalized schema
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_detections'"
        )
        has_normalized_schema = cursor.fetchone() is not None
        
        if has_normalized_schema:
            return self._search_normalized_records(**criteria)
        else:
            return self._search_legacy_records(**criteria)
    
    def _search_normalized_records(self, **criteria) -> List[Dict[str, Any]]:
        """Search records from normalized 3NF schema with dynamic criteria"""
        where_clauses = []
        params = []
        
        # Handle time-based criteria
        if criteria.get('start_date'):
            try:
                # Convert to timestamp if it's a string
                if isinstance(criteria['start_date'], str):
                    start_ts = datetime.fromisoformat(criteria['start_date']).timestamp()
                else:
                    start_ts = criteria['start_date']
                where_clauses.append("td.timestamp >= ?")
                params.append(start_ts)
            except ValueError:
                logger.warning(f"Invalid start_date format: {criteria['start_date']}")
        
        if criteria.get('end_date'):
            try:
                if isinstance(criteria['end_date'], str):
                    end_ts = datetime.fromisoformat(criteria['end_date']).timestamp()
                else:
                    end_ts = criteria['end_date']
                where_clauses.append("td.timestamp <= ?")
                params.append(end_ts)
            except ValueError:
                logger.warning(f"Invalid end_date format: {criteria['end_date']}")
        
        # Handle speed criteria (radar data)
        if criteria.get('min_speed') is not None:
            where_clauses.append("rd.speed_mph >= ?")
            params.append(criteria['min_speed'])
        
        if criteria.get('max_speed') is not None:
            where_clauses.append("rd.speed_mph <= ?")
            params.append(criteria['max_speed'])
        
        # Handle alert level
        if criteria.get('alert_level'):
            where_clauses.append("rd.alert_level = ?")
            params.append(criteria['alert_level'])
        
        # Handle direction filter
        if criteria.get('direction'):
            where_clauses.append("rd.direction = ?")
            params.append(criteria['direction'])
        
        # Handle vehicle count criteria
        if criteria.get('min_vehicles') is not None:
            where_clauses.append("cd.vehicle_count >= ?")
            params.append(criteria['min_vehicles'])
        
        # Handle trigger source
        if criteria.get('trigger_source'):
            where_clauses.append("td.trigger_source = ?")
            params.append(criteria['trigger_source'])
        
        # Handle location filter
        if criteria.get('location_id'):
            where_clauses.append("td.location_id = ?")
            params.append(criteria['location_id'])
        
        # Handle detection confidence
        if criteria.get('min_confidence') is not None:
            where_clauses.append("cd.detection_confidence >= ?")
            params.append(criteria['min_confidence'])
        
        # Construct WHERE clause
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit = criteria.get('limit', 100)
        
        # Complex JOIN query with all related data
        query = f"""
            SELECT DISTINCT
                td.id,
                td.correlation_id,
                td.timestamp,
                td.trigger_source,
                td.location_id,
                td.processing_metadata,
                
                -- Radar data
                rd.speed_mph,
                rd.speed_mps,
                rd.confidence as radar_confidence,
                rd.alert_level,
                rd.direction,
                rd.distance,
                
                -- Camera data
                cd.vehicle_count,
                cd.vehicle_types,
                cd.detection_confidence,
                cd.image_path,
                cd.inference_time_ms,
                
                -- Weather data aggregated from all sources
                GROUP_CONCAT(DISTINCT wc.source || ':' || wc.temperature || '°F') as temperatures,
                GROUP_CONCAT(DISTINCT wc.source || ':' || COALESCE(wc.humidity, 'N/A') || '%') as humidity_readings,
                GROUP_CONCAT(DISTINCT wc.conditions) as weather_conditions,
                MAX(wc.wind_speed) as max_wind_speed,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.temperature END) as local_temperature,
                AVG(CASE WHEN wc.source = 'dht22' THEN wc.humidity END) as local_humidity
                
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            LEFT JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            LEFT JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE {where_sql}
            GROUP BY td.id, td.correlation_id, td.timestamp, td.trigger_source, td.location_id,
                     rd.speed_mph, rd.speed_mps, rd.confidence, rd.alert_level, rd.direction, rd.distance,
                     cd.vehicle_count, cd.vehicle_types, cd.detection_confidence, cd.image_path, cd.inference_time_ms
            ORDER BY td.timestamp DESC
            LIMIT ?
        """
        
        params.append(limit)
        
        cursor = self.db_connection.execute(query, params)
        records = []
        
        for row in cursor.fetchall():
            record = dict(row)
            
            # Convert timestamp to readable format
            if record['timestamp']:
                record['timestamp_readable'] = datetime.fromtimestamp(record['timestamp']).isoformat()
            
            # Parse JSON fields
            for json_field in ['vehicle_types', 'processing_metadata']:
                if record.get(json_field):
                    try:
                        record[json_field] = json.loads(record[json_field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Process aggregated weather data
            if record.get('temperatures'):
                temp_data = {}
                for temp_reading in record['temperatures'].split(','):
                    if ':' in temp_reading:
                        source, temp_val = temp_reading.split(':', 1)
                        temp_data[source] = temp_val
                record['weather_by_source'] = temp_data
            
            records.append(record)
        
        return records
    
    def _search_legacy_records(self, **criteria) -> List[Dict[str, Any]]:
        """Fallback search for legacy schema"""
        where_clauses = []
        params = []
        
        # Check if legacy table exists
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_records'"
        )
        if not cursor.fetchone():
            return []
        
        if criteria.get('start_date'):
            where_clauses.append("timestamp >= ?")
            params.append(criteria['start_date'])
        
        if criteria.get('end_date'):
            where_clauses.append("timestamp <= ?")
            params.append(criteria['end_date'])
        
        if criteria.get('min_speed') is not None:
            where_clauses.append("radar_speed >= ?")
            params.append(criteria['min_speed'])
        
        if criteria.get('max_speed') is not None:
            where_clauses.append("radar_speed <= ?")
            params.append(criteria['max_speed'])
        
        if criteria.get('vehicle_type'):
            where_clauses.append("primary_vehicle_type = ?")
            params.append(criteria['vehicle_type'])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit = criteria.get('limit', 100)
        
        query = f"""
            SELECT 
                id, timestamp, trigger_source,
                radar_speed, radar_direction, radar_magnitude,
                air_temperature, humidity, airport_weather,
                vehicle_count, primary_vehicle_type, detection_confidence,
                processing_notes, created_at
            FROM traffic_records 
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        params.append(limit)
        cursor = self.db_connection.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            
            # Parse airport weather JSON if present
            if record.get('airport_weather'):
                try:
                    record['airport_weather'] = json.loads(record['airport_weather'])
                except json.JSONDecodeError:
                    pass
            
            records.append(record)
        
        return records
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the API server"""
        if not self.connect_database():
            logger.error("Cannot start API without database connection")
            return False
        
        logger.info(f"🚀 Starting Consolidated Data API on {host}:{port}")
        logger.info("Available endpoints:")
        logger.info("  GET /api/v1/traffic/recent - Recent traffic records")
        logger.info("  GET /api/v1/traffic/summary - Daily summaries")
        logger.info("  GET /api/v1/traffic/analytics - Traffic analytics")
        logger.info("  GET /api/v1/traffic/search - Search traffic records")
        logger.info("  GET /api/v1/health/database - Database health")
        
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
            return True
        except Exception as e:
            logger.error(f"API server failed: {e}")
            return False

def main():
    """Main entry point"""
    # Configuration
    config = {
        'db_path': os.getenv('DB_PATH', '/app/data/traffic_data.db'),
        'host': os.getenv('API_HOST', '0.0.0.0'),
        'port': int(os.getenv('API_PORT', '5000')),
        'debug': os.getenv('API_DEBUG', 'false').lower() == 'true'
    }
    
    logger.info("=== Consolidated Data API ===")
    logger.info("Enhanced API for traffic monitoring database")
    
    try:
        api = ConsolidatedDataAPI(db_path=config['db_path'])
        api.run(
            host=config['host'],
            port=config['port'],
            debug=config['debug']
        )
        
    except KeyboardInterrupt:
        logger.info("API server stopped by user")
    except Exception as e:
        logger.error(f"API server failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())