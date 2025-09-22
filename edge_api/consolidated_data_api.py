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
    
    def __init__(self, db_path: str = "/mnt/storage/traffic_monitoring.db"):
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
        """Get recent traffic records"""
        if not self.db_connection:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor = self.db_connection.execute("""
            SELECT 
                id, timestamp, trigger_source,
                radar_speed, radar_direction, radar_magnitude,
                air_temperature, humidity, airport_weather,
                vehicle_count, primary_vehicle_type, detection_confidence,
                processing_notes, created_at
            FROM traffic_records 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (cutoff_time, limit))
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            
            # Parse airport weather JSON if present
            if record['airport_weather']:
                try:
                    record['airport_weather'] = json.loads(record['airport_weather'])
                except json.JSONDecodeError:
                    pass
            
            records.append(record)
        
        return records
    
    def _get_daily_summaries(self, days: int) -> List[Dict[str, Any]]:
        """Get daily traffic summaries"""
        if not self.db_connection:
            return []
        
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        cursor = self.db_connection.execute("""
            SELECT 
                date, total_detections, avg_speed, max_speed,
                vehicle_types, weather_conditions, created_at
            FROM daily_summary 
            WHERE date >= ?
            ORDER BY date DESC
        """, (cutoff_date,))
        
        summaries = []
        for row in cursor.fetchall():
            summary = dict(row)
            
            # Parse JSON fields if present
            for field in ['vehicle_types', 'weather_conditions']:
                if summary[field]:
                    try:
                        summary[field] = json.loads(summary[field])
                    except json.JSONDecodeError:
                        pass
            
            summaries.append(summary)
        
        return summaries
    
    def _get_traffic_analytics(self, period: str) -> Dict[str, Any]:
        """Get traffic analytics for specified period"""
        if not self.db_connection:
            return {}
        
        # Determine time range based on period
        if period == 'day':
            cutoff_time = datetime.now() - timedelta(days=1)
        elif period == 'week':
            cutoff_time = datetime.now() - timedelta(days=7)
        elif period == 'month':
            cutoff_time = datetime.now() - timedelta(days=30)
        else:
            cutoff_time = datetime.now() - timedelta(days=7)  # Default to week
        
        # Get basic statistics
        cursor = self.db_connection.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(radar_speed) as avg_speed,
                MAX(radar_speed) as max_speed,
                MIN(radar_speed) as min_speed,
                COUNT(CASE WHEN radar_speed > 25 THEN 1 END) as speed_violations,
                AVG(air_temperature) as avg_temperature,
                AVG(humidity) as avg_humidity
            FROM traffic_records 
            WHERE timestamp >= ? AND radar_speed IS NOT NULL
        """, (cutoff_time,))
        
        stats = dict(cursor.fetchone())
        
        # Get hourly distribution
        cursor = self.db_connection.execute("""
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as count,
                AVG(radar_speed) as avg_speed
            FROM traffic_records 
            WHERE timestamp >= ? AND radar_speed IS NOT NULL
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        """, (cutoff_time,))
        
        hourly_data = [dict(row) for row in cursor.fetchall()]
        
        # Get vehicle type distribution
        cursor = self.db_connection.execute("""
            SELECT 
                primary_vehicle_type,
                COUNT(*) as count
            FROM traffic_records 
            WHERE timestamp >= ? AND primary_vehicle_type IS NOT NULL
            GROUP BY primary_vehicle_type
            ORDER BY count DESC
        """, (cutoff_time,))
        
        vehicle_types = [dict(row) for row in cursor.fetchall()]
        
        return {
            'period': period,
            'time_range': {
                'start': cutoff_time.isoformat(),
                'end': datetime.now().isoformat()
            },
            'statistics': stats,
            'hourly_distribution': hourly_data,
            'vehicle_types': vehicle_types
        }
    
    def _search_traffic_records(self, **criteria) -> List[Dict[str, Any]]:
        """Search traffic records by criteria"""
        if not self.db_connection:
            return []
        
        # Build dynamic query
        where_clauses = []
        params = []
        
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
        
        # Construct query
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
            if record['airport_weather']:
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
        'db_path': os.getenv('DB_PATH', '/mnt/storage/traffic_monitoring.db'),
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