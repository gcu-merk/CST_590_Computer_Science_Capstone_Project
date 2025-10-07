#!/usr/bin/env python3
"""
Weather Database Consolidation Validation Script

This script validates that the weather analysis database has been successfully 
consolidated with the main traffic database. It checks:

1. Weather analysis tables exist in the main traffic database
2. Weather data storage service uses the correct database path
3. Table schemas match expected structure
4. Data can be written and read from consolidated database

Usage:
    python validate_weather_database_consolidation.py [--database-path /path/to/traffic_data.db]
"""

import sqlite3
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from edge_processing.weather_analysis.weather_data_storage import WeatherDataStorage
    from edge_processing.data_persistence.database_persistence_service_simplified import SimplifiedEnhancedDatabasePersistenceService
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class WeatherDatabaseConsolidationValidator:
    """Validates weather database consolidation with main traffic database"""
    
    def __init__(self, database_path: str = None):
        """Initialize validator with database path"""
        if database_path is None:
            # For development environment, use a temporary database
            # In production, this would be /app/data/traffic_data.db
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            database_path = str(data_dir / "traffic_data.db")
        
        self.database_path = database_path
        self.validation_results = {}
        
    def validate_database_schema(self) -> bool:
        """Validate that weather tables exist in main database with correct schema"""
        print("🔍 Validating database schema...")
        
        expected_tables = [
            'traffic_records',
            'daily_summaries', 
            'service_health',
            'weather_analysis',
            'weather_traffic_events',
            'weather_summaries'
        ]
        
        expected_weather_indexes = [
            'idx_weather_analysis_timestamp',
            'idx_weather_traffic_events_timestamp',
            'idx_weather_traffic_events_weather_id',
            'idx_weather_summaries_period'
        ]
        
        try:
            # Initialize the database with proper schema first
            print(f"Initializing database at: {self.database_path}")
            persistence_service = SimplifiedEnhancedDatabasePersistenceService(
                database_path=self.database_path
            )
            
            # Actually initialize the database schema
            if persistence_service.initialize_database():
                print("✅ Database schema initialized successfully")
            else:
                print("❌ Failed to initialize database schema")
                self.validation_results['schema_validation'] = False
                return False
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = []
                for table in expected_tables:
                    if table not in existing_tables:
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"❌ Missing tables: {missing_tables}")
                    self.validation_results['schema_validation'] = False
                    return False
                
                print(f"✅ All expected tables exist: {expected_tables}")
                
                # Check weather table schemas
                weather_schema_checks = [
                    ("weather_analysis", ["id", "timestamp", "condition", "confidence", "visibility_estimate", "analysis_methods", "system_temperature", "frame_info", "created_at"]),
                    ("weather_traffic_events", ["id", "timestamp", "event_type", "event_data", "weather_id", "created_at"]),
                    ("weather_summaries", ["id", "period_start", "period_end", "period_type", "clear_count", "partly_cloudy_count", "cloudy_count", "unknown_count", "avg_confidence", "total_analyses", "created_at"])
                ]
                
                for table_name, expected_columns in weather_schema_checks:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    actual_columns = [row[1] for row in cursor.fetchall()]
                    
                    missing_columns = [col for col in expected_columns if col not in actual_columns]
                    if missing_columns:
                        print(f"❌ Table {table_name} missing columns: {missing_columns}")
                        self.validation_results['schema_validation'] = False
                        return False
                
                # Check indexes exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                existing_indexes = [row[0] for row in cursor.fetchall()]
                
                missing_indexes = []
                for index in expected_weather_indexes:
                    if index not in existing_indexes:
                        missing_indexes.append(index)
                
                if missing_indexes:
                    print(f"⚠️  Missing indexes (performance impact): {missing_indexes}")
                else:
                    print("✅ All expected indexes exist")
                
                print("✅ Database schema validation passed")
                self.validation_results['schema_validation'] = True
                return True
                
        except Exception as e:
            print(f"❌ Database schema validation failed: {e}")
            self.validation_results['schema_validation'] = False
            return False
    
    def validate_weather_storage_service(self) -> bool:
        """Validate WeatherDataStorage service uses consolidated database"""
        print("\n🔍 Validating WeatherDataStorage service configuration...")
        
        try:
            # Test with temporary database to avoid affecting production
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
                temp_db_path = temp_db.name
            
            # Create persistence service first to initialize schema
            persistence_service = SimplifiedEnhancedDatabasePersistenceService(
                database_path=temp_db_path
            )
            persistence_service.initialize_database()
            
            # Create weather storage service with same database path
            weather_storage = WeatherDataStorage(db_path=temp_db_path)
            
            # Test data insertion
            test_weather_data = {
                'timestamp': datetime.now().isoformat(),
                'sky_condition': {
                    'condition': 'clear',
                    'confidence': 0.95
                },
                'visibility_estimate': 'good',
                'weather_metrics': {
                    'analysis_methods': ['visual', 'statistical']
                },
                'system_temperature': 22.5,
                'frame_info': {
                    'frame_count': 100,
                    'processing_time': 1.2
                }
            }
            
            # Store weather analysis
            weather_id = weather_storage.store_weather_analysis(test_weather_data)
            print(f"✅ Weather analysis stored with ID: {weather_id}")
            
            # Store traffic event
            test_traffic_event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'detection',
                'event_data': {
                    'vehicle_count': 2,
                    'confidence': 0.88
                },
                'weather_id': weather_id
            }
            
            weather_storage.store_traffic_event(test_traffic_event)
            print("✅ Weather traffic event stored successfully")
            
            # Verify data exists in consolidated database
            with sqlite3.connect(temp_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM weather_analysis")
                weather_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM weather_traffic_events") 
                events_count = cursor.fetchone()[0]
                
                if weather_count > 0 and events_count > 0:
                    print(f"✅ Data verification passed: {weather_count} weather records, {events_count} traffic events")
                    self.validation_results['service_validation'] = True
                    return True
                else:
                    print(f"❌ Data verification failed: {weather_count} weather records, {events_count} traffic events")
                    self.validation_results['service_validation'] = False
                    return False
            
        except Exception as e:
            print(f"❌ WeatherDataStorage service validation failed: {e}")
            self.validation_results['service_validation'] = False
            return False
        finally:
            # Clean up temporary database
            try:
                os.unlink(temp_db_path)
            except (OSError, PermissionError, FileNotFoundError) as e:
                pass
    
    def validate_environment_configuration(self) -> bool:
        """Validate environment variables and configuration"""
        print("\n🔍 Validating environment configuration...")
        
        try:
            # For development environment, create a temporary database to test configuration
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
                temp_db_path = temp_db.name
            
            # Initialize the database schema first
            persistence_service = SimplifiedEnhancedDatabasePersistenceService(
                database_path=temp_db_path
            )
            persistence_service.initialize_database()
            
            # Test WeatherDataStorage with explicit database path
            weather_storage = WeatherDataStorage(db_path=temp_db_path)
            
            if weather_storage.db_path == temp_db_path:
                print(f"✅ WeatherDataStorage uses correct database path: {weather_storage.db_path}")
                
                # Test that it uses environment variable when available
                original_env = os.environ.get('DATABASE_PATH')
                try:
                    os.environ['DATABASE_PATH'] = temp_db_path
                    env_weather_storage = WeatherDataStorage()
                    
                    if env_weather_storage.db_path == temp_db_path:
                        print(f"✅ WeatherDataStorage respects DATABASE_PATH environment variable")
                        self.validation_results['environment_validation'] = True
                        return True
                    else:
                        print(f"❌ WeatherDataStorage ignores DATABASE_PATH environment variable")
                        self.validation_results['environment_validation'] = False
                        return False
                        
                finally:
                    # Restore original environment
                    if original_env is not None:
                        os.environ['DATABASE_PATH'] = original_env
                    elif 'DATABASE_PATH' in os.environ:
                        del os.environ['DATABASE_PATH']
            else:
                print(f"❌ WeatherDataStorage using wrong path: {weather_storage.db_path}, expected: {temp_db_path}")
                self.validation_results['environment_validation'] = False
                return False
                
        except Exception as e:
            print(f"❌ Environment configuration validation failed: {e}")
            self.validation_results['environment_validation'] = False
            return False
        finally:
            # Clean up temporary database
            try:
                os.unlink(temp_db_path)
            except (OSError, PermissionError, FileNotFoundError) as e:
                pass
    
    def run_comprehensive_validation(self) -> Dict:
        """Run all validation tests and return results"""
        print("🚀 Starting Weather Database Consolidation Validation")
        print("=" * 60)
        
        validations = [
            ("Database Schema", self.validate_database_schema),
            ("Weather Storage Service", self.validate_weather_storage_service),
            ("Environment Configuration", self.validate_environment_configuration)
        ]
        
        all_passed = True
        
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {validation_name} validation failed with exception: {e}")
                all_passed = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        for key, result in self.validation_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{key:.<40} {status}")
        
        overall_status = "✅ SUCCESS" if all_passed else "❌ FAILURE"
        print(f"{'Overall Status':.<40} {overall_status}")
        
        if all_passed:
            print("\n🎉 Weather database consolidation validation completed successfully!")
            print("The weather analysis system is now using the consolidated traffic database.")
        else:
            print("\n⚠️  Weather database consolidation validation failed!")
            print("Please review the errors above and fix the issues.")
        
        return {
            'overall_success': all_passed,
            'individual_results': self.validation_results,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Main function to run validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate weather database consolidation')
    parser.add_argument('--database-path', 
                       default=None,
                       help='Path to the consolidated traffic database')
    parser.add_argument('--output-json',
                       help='Output results to JSON file')
    
    args = parser.parse_args()
    
    # Run validation
    validator = WeatherDatabaseConsolidationValidator(args.database_path)
    results = validator.run_comprehensive_validation()
    
    # Output results to JSON if requested
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {args.output_json}")
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)


if __name__ == '__main__':
    main()