#!/usr/bin/env python3
"""
Database Migration Script: Legacy to 3NF Normalization
=====================================================

This script migrates existing denormalized traffic_records data to 
the new normalized 3NF schema with separate tables for:
- traffic_detections (core detection events)
- radar_detections (radar-specific data)
- camera_detections (camera/AI vision data) 
- weather_conditions (weather measurements)
- traffic_weather_correlation (linking detections to weather)

Usage:
    python migrate_to_normalized_schema.py --database_path /path/to/traffic.db [--dry_run] [--batch_size 1000]

Features:
- Comprehensive data validation and error handling
- Dry run mode for testing migration without changes
- Batch processing for large datasets
- Progress reporting and detailed logging
- Automatic backup creation before migration
- Foreign key constraint validation
- Rollback capability on errors
"""

import sqlite3
import json
import logging
import argparse
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import time

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Track migration statistics"""
    legacy_records_found: int = 0
    records_processed: int = 0
    traffic_detections_created: int = 0
    radar_detections_created: int = 0
    camera_detections_created: int = 0
    weather_conditions_created: int = 0
    correlations_created: int = 0
    errors: int = 0
    warnings: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def records_per_second(self) -> float:
        duration = self.duration_seconds()
        return self.records_processed / duration if duration > 0 else 0.0

class DatabaseMigrator:
    """Handles migration from legacy to normalized schema"""
    
    def __init__(self, database_path: str, dry_run: bool = False, batch_size: int = 1000):
        self.database_path = database_path
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.backup_path = f"{database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = MigrationStats()
        self.connection: Optional[sqlite3.Connection] = None
        
        # Weather cache to deduplicate weather conditions
        self.weather_cache: Dict[str, int] = {}
        self.next_weather_id = 1
    
    def create_backup(self) -> bool:
        """Create backup of original database"""
        try:
            if not self.dry_run:
                shutil.copy2(self.database_path, self.backup_path)
                logger.info(f"✅ Database backup created: {self.backup_path}")
            else:
                logger.info(f"🔍 [DRY RUN] Would create backup: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def connect_database(self) -> bool:
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(
                self.database_path,
                timeout=30.0,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            
            # Enable foreign keys and WAL mode for better performance
            if not self.dry_run:
                self.connection.execute("PRAGMA foreign_keys = ON")
                self.connection.execute("PRAGMA journal_mode = WAL")
                self.connection.execute("PRAGMA synchronous = NORMAL")
                self.connection.execute("PRAGMA cache_size = 10000")
            
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def check_legacy_schema(self) -> Tuple[bool, int]:
        """Check if legacy traffic_records table exists and count records"""
        try:
            cursor = self.connection.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='traffic_records'
            """)
            
            if not cursor.fetchone():
                logger.warning("⚠️  No legacy traffic_records table found")
                return False, 0
            
            # Count legacy records
            cursor = self.connection.execute("SELECT COUNT(*) FROM traffic_records")
            count = cursor.fetchone()[0]
            
            logger.info(f"📊 Found {count:,} legacy records to migrate")
            return True, count
        except Exception as e:
            logger.error(f"❌ Error checking legacy schema: {e}")
            return False, 0
    
    def check_normalized_schema(self) -> bool:
        """Check if normalized schema already exists"""
        try:
            required_tables = [
                'traffic_detections', 'radar_detections', 
                'camera_detections', 'weather_conditions',
                'traffic_weather_correlation'
            ]
            
            for table in required_tables:
                cursor = self.connection.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                
                if cursor.fetchone():
                    logger.warning(f"⚠️  Normalized table '{table}' already exists")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Error checking normalized schema: {e}")
            return False
    
    def create_normalized_schema(self) -> bool:
        """Create normalized 3NF schema tables"""
        try:
            schema_sql = """
            -- Core traffic detection events
            CREATE TABLE IF NOT EXISTS traffic_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correlation_id TEXT UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                trigger_source TEXT NOT NULL,
                location_id TEXT DEFAULT 'default_location',
                processing_metadata TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );
            
            -- Radar-specific detection data
            CREATE TABLE IF NOT EXISTS radar_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                speed_mph REAL,
                speed_mps REAL,
                confidence REAL,
                alert_level TEXT,
                direction TEXT,
                distance REAL,
                FOREIGN KEY (detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE
            );
            
            -- Camera/AI detection data
            CREATE TABLE IF NOT EXISTS camera_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                vehicle_count INTEGER,
                vehicle_types TEXT,  -- JSON array
                detection_confidence REAL,
                image_path TEXT,
                inference_time_ms REAL,
                FOREIGN KEY (detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE
            );
            
            -- Weather condition measurements
            CREATE TABLE IF NOT EXISTS weather_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                timestamp REAL NOT NULL,
                temperature REAL,
                humidity REAL,
                conditions TEXT,
                wind_speed REAL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );
            
            -- Many-to-many correlation between traffic and weather
            CREATE TABLE IF NOT EXISTS traffic_weather_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                weather_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE,
                FOREIGN KEY (weather_id) REFERENCES weather_conditions(id) ON DELETE CASCADE,
                UNIQUE(detection_id, weather_id)
            );
            
            -- Performance indexes
            CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_detections(timestamp);
            CREATE INDEX IF NOT EXISTS idx_traffic_correlation ON traffic_detections(correlation_id);
            CREATE INDEX IF NOT EXISTS idx_radar_detection ON radar_detections(detection_id);
            CREATE INDEX IF NOT EXISTS idx_camera_detection ON camera_detections(detection_id);
            CREATE INDEX IF NOT EXISTS idx_weather_source_time ON weather_conditions(source, timestamp);
            CREATE INDEX IF NOT EXISTS idx_traffic_weather_detection ON traffic_weather_correlation(detection_id);
            CREATE INDEX IF NOT EXISTS idx_traffic_weather_weather ON traffic_weather_correlation(weather_id);
            """
            
            if not self.dry_run:
                self.connection.executescript(schema_sql)
                self.connection.commit()
                logger.info("✅ Normalized schema created successfully")
            else:
                logger.info("🔍 [DRY RUN] Would create normalized schema")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create normalized schema: {e}")
            return False
    
    def parse_legacy_record(self, record: sqlite3.Row) -> Dict[str, Any]:
        """Parse and validate a legacy traffic record"""
        try:
            # Convert row to dict for easier handling
            data = dict(record)
            
            # Parse JSON fields safely
            for json_field in ['airport_weather', 'processing_notes']:
                if data.get(json_field):
                    try:
                        data[json_field] = json.loads(data[json_field])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"⚠️  Invalid JSON in {json_field}: {data[json_field]}")
                        data[json_field] = None
            
            # Generate correlation ID if missing
            if not data.get('id'):
                data['correlation_id'] = f"legacy_{int(time.time() * 1000000)}"
            else:
                data['correlation_id'] = f"legacy_{data['id']}"
            
            # Convert timestamp to Unix timestamp if needed
            if isinstance(data.get('timestamp'), str):
                try:
                    dt = datetime.fromisoformat(data['timestamp'])
                    data['timestamp'] = dt.timestamp()
                except ValueError:
                    logger.warning(f"⚠️  Invalid timestamp format: {data['timestamp']}")
                    data['timestamp'] = time.time()
            
            return data
        except Exception as e:
            logger.error(f"❌ Error parsing legacy record: {e}")
            self.stats.errors += 1
            return {}
    
    def get_or_create_weather_condition(self, source: str, temperature: Optional[float], 
                                      humidity: Optional[float], conditions: Optional[str],
                                      timestamp: float, wind_speed: Optional[float] = None) -> Optional[int]:
        """Get or create weather condition entry (deduplication)"""
        
        # Create cache key for deduplication
        cache_key = f"{source}_{temperature}_{humidity}_{conditions}_{wind_speed}"
        
        if cache_key in self.weather_cache:
            return self.weather_cache[cache_key]
        
        try:
            if not self.dry_run:
                cursor = self.connection.execute("""
                    INSERT INTO weather_conditions 
                    (source, timestamp, temperature, humidity, conditions, wind_speed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (source, timestamp, temperature, humidity, conditions, wind_speed))
                
                weather_id = cursor.lastrowid
                self.weather_cache[cache_key] = weather_id
                self.stats.weather_conditions_created += 1
                return weather_id
            else:
                # Dry run - simulate ID generation
                weather_id = self.next_weather_id
                self.next_weather_id += 1
                self.weather_cache[cache_key] = weather_id
                return weather_id
                
        except Exception as e:
            logger.warning(f"⚠️  Error creating weather condition: {e}")
            self.stats.warnings += 1
            return None
    
    def migrate_record(self, legacy_data: Dict[str, Any]) -> bool:
        """Migrate a single legacy record to normalized schema"""
        try:
            if not legacy_data:
                return False
            
            # 1. Create traffic detection entry
            traffic_detection_sql = """
                INSERT INTO traffic_detections 
                (correlation_id, timestamp, trigger_source, location_id, processing_metadata)
                VALUES (?, ?, ?, ?, ?)
            """
            
            processing_metadata = json.dumps(legacy_data.get('processing_notes', {})) if legacy_data.get('processing_notes') else None
            
            if not self.dry_run:
                cursor = self.connection.execute(traffic_detection_sql, (
                    legacy_data['correlation_id'],
                    legacy_data.get('timestamp', time.time()),
                    legacy_data.get('trigger_source', 'legacy_migration'),
                    'default_location',
                    processing_metadata
                ))
                detection_id = cursor.lastrowid
            else:
                detection_id = self.stats.traffic_detections_created + 1
            
            self.stats.traffic_detections_created += 1
            
            # 2. Create radar detection if radar data exists
            if any(legacy_data.get(field) is not None for field in ['radar_speed', 'radar_direction', 'radar_magnitude']):
                radar_sql = """
                    INSERT INTO radar_detections 
                    (detection_id, speed_mph, speed_mps, confidence, alert_level, direction, distance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                # Convert radar_magnitude to confidence score (0-1)
                confidence = min(1.0, (legacy_data.get('radar_magnitude', 0) / 100.0)) if legacy_data.get('radar_magnitude') else None
                
                # Determine alert level based on speed
                speed = legacy_data.get('radar_speed')
                if speed:
                    if speed > 35:
                        alert_level = 'high'
                    elif speed > 25:
                        alert_level = 'medium' 
                    else:
                        alert_level = 'low'
                else:
                    alert_level = 'unknown'
                
                if not self.dry_run:
                    self.connection.execute(radar_sql, (
                        detection_id,
                        legacy_data.get('radar_speed'),
                        legacy_data.get('radar_speed') * 0.44704 if legacy_data.get('radar_speed') else None,  # mph to m/s
                        confidence,
                        alert_level,
                        legacy_data.get('radar_direction'),
                        None  # Distance not available in legacy data
                    ))
                
                self.stats.radar_detections_created += 1
            
            # 3. Create camera detection if camera data exists
            if any(legacy_data.get(field) is not None for field in ['vehicle_count', 'primary_vehicle_type', 'detection_confidence']):
                camera_sql = """
                    INSERT INTO camera_detections 
                    (detection_id, vehicle_count, vehicle_types, detection_confidence, image_path, inference_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                
                # Convert single vehicle type to JSON array
                vehicle_types = None
                if legacy_data.get('primary_vehicle_type'):
                    vehicle_types = json.dumps([legacy_data['primary_vehicle_type']])
                
                if not self.dry_run:
                    self.connection.execute(camera_sql, (
                        detection_id,
                        legacy_data.get('vehicle_count'),
                        vehicle_types,
                        legacy_data.get('detection_confidence'),
                        None,  # Image path not available in legacy data
                        None   # Inference time not available
                    ))
                
                self.stats.camera_detections_created += 1
            
            # 4. Create weather conditions and correlations
            timestamp = legacy_data.get('timestamp', time.time())
            
            # DHT22 local weather
            if legacy_data.get('air_temperature') is not None or legacy_data.get('humidity') is not None:
                weather_id = self.get_or_create_weather_condition(
                    source='dht22',
                    temperature=legacy_data.get('air_temperature'),
                    humidity=legacy_data.get('humidity'),
                    conditions=None,
                    timestamp=timestamp
                )
                
                if weather_id and not self.dry_run:
                    self.connection.execute("""
                        INSERT OR IGNORE INTO traffic_weather_correlation (detection_id, weather_id)
                        VALUES (?, ?)
                    """, (detection_id, weather_id))
                    self.stats.correlations_created += 1
            
            # Airport weather data
            if legacy_data.get('airport_weather') and isinstance(legacy_data['airport_weather'], dict):
                airport_data = legacy_data['airport_weather']
                weather_id = self.get_or_create_weather_condition(
                    source='airport',
                    temperature=airport_data.get('temperature'),
                    humidity=airport_data.get('humidity'),
                    conditions=airport_data.get('conditions'),
                    timestamp=timestamp,
                    wind_speed=airport_data.get('wind_speed')
                )
                
                if weather_id and not self.dry_run:
                    self.connection.execute("""
                        INSERT OR IGNORE INTO traffic_weather_correlation (detection_id, weather_id)
                        VALUES (?, ?)
                    """, (detection_id, weather_id))
                    self.stats.correlations_created += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating record {legacy_data.get('correlation_id', 'unknown')}: {e}")
            self.stats.errors += 1
            return False
    
    def migrate_data(self) -> bool:
        """Migrate all legacy data in batches"""
        try:
            # Get total record count for progress tracking
            cursor = self.connection.execute("SELECT COUNT(*) FROM traffic_records")
            total_records = cursor.fetchone()[0]
            self.stats.legacy_records_found = total_records
            
            if total_records == 0:
                logger.info("ℹ️  No legacy records to migrate - normalized schema already created")
                return True
            
            logger.info(f"🔄 Starting migration of {total_records:,} records in batches of {self.batch_size}")
            
            offset = 0
            
            while offset < total_records:
                # Fetch batch of records
                cursor = self.connection.execute("""
                    SELECT * FROM traffic_records 
                    ORDER BY id 
                    LIMIT ? OFFSET ?
                """, (self.batch_size, offset))
                
                batch = cursor.fetchall()
                if not batch:
                    break
                
                # Begin transaction for batch
                if not self.dry_run:
                    self.connection.execute("BEGIN")
                
                batch_success = True
                
                # Process each record in batch
                for record in batch:
                    legacy_data = self.parse_legacy_record(record)
                    if self.migrate_record(legacy_data):
                        self.stats.records_processed += 1
                    else:
                        batch_success = False
                        break
                
                # Commit or rollback batch
                if not self.dry_run:
                    if batch_success:
                        self.connection.execute("COMMIT")
                    else:
                        self.connection.execute("ROLLBACK")
                        logger.error(f"❌ Batch starting at offset {offset} failed, rolled back")
                        return False
                
                offset += self.batch_size
                
                # Progress reporting
                progress = (offset / total_records) * 100
                logger.info(f"📊 Progress: {progress:.1f}% ({offset:,}/{total_records:,} records)")
            
            logger.info(f"✅ Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            if not self.dry_run and self.connection:
                self.connection.execute("ROLLBACK")
            return False
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful"""
        try:
            # Count records in each table
            validation_queries = {
                'traffic_detections': "SELECT COUNT(*) FROM traffic_detections",
                'radar_detections': "SELECT COUNT(*) FROM radar_detections", 
                'camera_detections': "SELECT COUNT(*) FROM camera_detections",
                'weather_conditions': "SELECT COUNT(*) FROM weather_conditions",
                'traffic_weather_correlation': "SELECT COUNT(*) FROM traffic_weather_correlation"
            }
            
            logger.info("🔍 Validating migration results...")
            
            for table, query in validation_queries.items():
                cursor = self.connection.execute(query)
                count = cursor.fetchone()[0]
                logger.info(f"  📋 {table}: {count:,} records")
            
            # Validate foreign key constraints
            if not self.dry_run:
                cursor = self.connection.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    logger.error(f"❌ Found {len(fk_violations)} foreign key violations:")
                    for violation in fk_violations:
                        logger.error(f"   {violation}")
                    return False
                else:
                    logger.info("✅ All foreign key constraints valid")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False
    
    def print_migration_summary(self):
        """Print comprehensive migration summary"""
        logger.info("="*60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Legacy records found: {self.stats.legacy_records_found:,}")
        logger.info(f"Records processed: {self.stats.records_processed:,}")
        logger.info(f"Processing time: {self.stats.duration_seconds():.2f} seconds")
        logger.info(f"Processing rate: {self.stats.records_per_second():.1f} records/sec")
        logger.info("")
        logger.info("📋 NORMALIZED RECORDS CREATED:")
        logger.info(f"  Traffic detections: {self.stats.traffic_detections_created:,}")
        logger.info(f"  Radar detections: {self.stats.radar_detections_created:,}")
        logger.info(f"  Camera detections: {self.stats.camera_detections_created:,}")
        logger.info(f"  Weather conditions: {self.stats.weather_conditions_created:,}")
        logger.info(f"  Weather correlations: {self.stats.correlations_created:,}")
        logger.info("")
        logger.info(f"⚠️  Warnings: {self.stats.warnings}")
        logger.info(f"❌ Errors: {self.stats.errors}")
        logger.info("")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN COMPLETED - No changes made to database")
        else:
            logger.info(f"💾 Backup created: {self.backup_path}")
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
        
        logger.info("="*60)
    
    def run_migration(self) -> bool:
        """Execute complete migration process"""
        self.stats.start_time = time.time()
        
        try:
            # 1. Create backup
            if not self.create_backup():
                return False
            
            # 2. Connect to database
            if not self.connect_database():
                return False
            
            # 3. Check legacy schema
            has_legacy, record_count = self.check_legacy_schema()
            if not has_legacy:
                logger.info("ℹ️  No legacy table found - creating normalized schema for new database")
            elif record_count == 0:
                logger.info("ℹ️  Legacy table is empty - will create normalized schema")
            else:
                logger.info(f"📊 Found {record_count:,} legacy records to migrate")
            
            # 4. Check if normalized schema already exists
            if self.check_normalized_schema():
                if record_count > 0:  # Only ask if there's actual data to migrate
                    user_input = input("⚠️  Normalized schema already exists. Continue? (y/N): ")
                    if user_input.lower() != 'y':
                        logger.info("Migration cancelled by user")
                        return False
                else:
                    logger.info("✅ Normalized schema already exists - no migration needed")
                    return True
            
            # 5. Create normalized schema
            if not self.create_normalized_schema():
                return False
            
            # 6. Migrate data
            if not self.migrate_data():
                return False
            
            # 7. Validate migration
            if not self.validate_migration():
                return False
            
            self.stats.end_time = time.time()
            self.print_migration_summary()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("⚠️  Migration interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate traffic monitoring database from legacy to normalized 3NF schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to test migration without changes
  python migrate_to_normalized_schema.py --database_path traffic.db --dry_run
  
  # Full migration with custom batch size
  python migrate_to_normalized_schema.py --database_path traffic.db --batch_size 500
  
  # Production migration
  python migrate_to_normalized_schema.py --database_path /path/to/production/traffic.db
        """
    )
    
    parser.add_argument(
        '--database_path',
        required=True,
        help='Path to SQLite database file'
    )
    
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Test migration without making changes'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=1000,
        help='Number of records to process per batch (default: 1000)'
    )
    
    args = parser.parse_args()
    
    # Validate database path
    if not os.path.exists(args.database_path):
        logger.error(f"❌ Database file not found: {args.database_path}")
        return False
    
    # Run migration
    migrator = DatabaseMigrator(
        database_path=args.database_path,
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    success = migrator.run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        return True
    else:
        logger.error("💥 Migration failed!")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)