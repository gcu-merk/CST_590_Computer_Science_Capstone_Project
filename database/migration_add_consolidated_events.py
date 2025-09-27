#!/usr/bin/env python3
"""
Database Migration Script: Add consolidated_events table for dual storage
Adds the missing consolidated_events table to existing databases
"""

import sqlite3
import os
import sys
import json
from datetime import datetime
from pathlib import Path

class DatabaseMigration:
    """Handles adding the consolidated_events table to existing databases"""
    
    def __init__(self, database_path: str = "/app/data/traffic_data.db"):
        self.database_path = database_path
        
    def check_table_exists(self) -> bool:
        """Check if consolidated_events table already exists"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='consolidated_events'
            """)
            
            exists = cursor.fetchone() is not None
            conn.close()
            
            print(f"✓ consolidated_events table exists: {exists}")
            return exists
            
        except Exception as e:
            print(f"❌ Error checking table existence: {e}")
            return False
    
    def create_consolidated_events_table(self) -> bool:
        """Create the consolidated_events table for dual storage"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Create the consolidated_events table
            print("🔧 Creating consolidated_events table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consolidated_events (
                    consolidation_id TEXT PRIMARY KEY,
                    event_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consolidated_id_time 
                ON consolidated_events(consolidation_id, created_at)
            """)
            
            conn.commit()
            conn.close()
            
            print("✅ consolidated_events table created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating consolidated_events table: {e}")
            return False
    
    def verify_schema(self) -> bool:
        """Verify the table schema is correct"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("PRAGMA table_info(consolidated_events)")
            columns = cursor.fetchall()
            
            print("📋 consolidated_events table schema:")
            for column in columns:
                print(f"  - {column[1]} {column[2]} {'(PK)' if column[5] else ''}")
            
            # Check indexes
            cursor.execute("PRAGMA index_list(consolidated_events)")
            indexes = cursor.fetchall()
            
            print("📋 Table indexes:")
            for index in indexes:
                print(f"  - {index[1]}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error verifying schema: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration"""
        print("🚀 Starting database migration for consolidated_events table")
        print(f"📍 Database path: {self.database_path}")
        
        # Check if database exists
        if not os.path.exists(self.database_path):
            print(f"❌ Database file not found: {self.database_path}")
            return False
        
        # Check if table already exists
        if self.check_table_exists():
            print("ℹ️  consolidated_events table already exists, no migration needed")
            return self.verify_schema()
        
        # Create the table
        success = self.create_consolidated_events_table()
        
        if success:
            print("🎉 Migration completed successfully!")
            return self.verify_schema()
        else:
            print("💥 Migration failed!")
            return False

def main():
    """Main migration entry point"""
    # Get database path from environment or use default
    db_path = os.environ.get('DATABASE_PATH', '/app/data/traffic_data.db')
    
    # Also try common paths if the default doesn't exist
    possible_paths = [
        db_path,
        '/mnt/storage/data/traffic_data.db',
        './traffic_data.db',
        '../data/traffic_data.db'
    ]
    
    database_path = None
    for path in possible_paths:
        if os.path.exists(path):
            database_path = path
            break
    
    if not database_path:
        print("❌ No database file found in any of the expected locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    # Run migration
    migration = DatabaseMigration(database_path)
    success = migration.run_migration()
    
    if success:
        print("✅ Database migration completed successfully")
        return True
    else:
        print("❌ Database migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)