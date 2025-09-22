#!/bin/bash
"""
Complete Persistence Layer Deployment
Deploys database persistence and Redis optimization services

This script completes the traffic monitoring data pipeline:
1. Database Persistence Service - stores consolidated data long-term
2. Redis Optimization Service - manages Redis memory efficiently
3. Enhanced API Gateway - serves consolidated data to external systems

Architecture Flow:
Radar Motion -> Consolidator -> Database Persistence -> API -> External Website
                              -> Redis Optimization (memory management)
"""

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="/etc/systemd/system"
STORAGE_DIR="/mnt/storage"
LOG_DIR="/var/log/traffic-monitoring"

echo "=== Complete Persistence Layer Deployment ==="
echo "Project root: $PROJECT_ROOT"
echo "Storage directory: $STORAGE_DIR"

# Create required directories
echo "📁 Creating required directories..."
sudo mkdir -p "$STORAGE_DIR"
sudo mkdir -p "$LOG_DIR"
sudo chown pi:pi "$STORAGE_DIR"
sudo chown pi:pi "$LOG_DIR"

# Install Python dependencies for new services
echo "📦 Installing Python dependencies..."
pip3 install --user redis sqlite3 flask flask-cors

# Copy service files
echo "🚀 Installing systemd services..."

# Database persistence service
sudo cp "$PROJECT_ROOT/deployment/database-persistence.service" "$SERVICES_DIR/"
sudo systemctl daemon-reload

# Create Redis optimization service file
cat > /tmp/redis-optimization.service << 'EOF'
[Unit]
Description=Redis Optimization Service - Memory Management
Documentation=https://github.com/project/traffic-monitoring
After=network.target redis.service
Wants=redis.service
PartOf=traffic-monitoring.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/traffic-monitoring
ExecStart=/usr/bin/python3 -u edge_processing/data_persistence/redis_optimization_service.py
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Environment variables
Environment=REDIS_HOST=localhost
Environment=REDIS_PORT=6379
Environment=OPTIMIZATION_INTERVAL=3600

# Resource limits
MemoryMax=256M
CPUQuota=15%

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=redis-optimization

[Install]
WantedBy=multi-user.target
WantedBy=traffic-monitoring.target
EOF

sudo mv /tmp/redis-optimization.service "$SERVICES_DIR/"

# Create enhanced API service file
cat > /tmp/consolidated-api.service << 'EOF'
[Unit]
Description=Consolidated Data API - Enhanced Traffic API
Documentation=https://github.com/project/traffic-monitoring
After=network.target database-persistence.service
Wants=database-persistence.service
PartOf=traffic-monitoring.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/traffic-monitoring
ExecStart=/usr/bin/python3 -u edge_api/consolidated_data_api.py
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Environment variables
Environment=DB_PATH=/mnt/storage/traffic_monitoring.db
Environment=API_HOST=0.0.0.0
Environment=API_PORT=5000
Environment=API_DEBUG=false

# Resource limits
MemoryMax=512M
CPUQuota=30%

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadOnlyPaths=/mnt/storage

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=consolidated-api

[Install]
WantedBy=multi-user.target
WantedBy=traffic-monitoring.target
EOF

sudo mv /tmp/consolidated-api.service "$SERVICES_DIR/"

# Reload systemd
sudo systemctl daemon-reload

# Enable services
echo "⚡ Enabling persistence services..."
sudo systemctl enable database-persistence.service
sudo systemctl enable redis-optimization.service
sudo systemctl enable consolidated-api.service

# Create database initialization script
echo "🗄️ Setting up database..."
cat > /tmp/init_database.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os
from pathlib import Path

DB_PATH = "/mnt/storage/traffic_monitoring.db"

def init_database():
    print(f"Initializing database: {DB_PATH}")
    
    # Ensure directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Enable optimizations
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    
    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traffic_records (
            id TEXT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            trigger_source TEXT NOT NULL,
            radar_speed REAL,
            radar_direction TEXT,
            radar_magnitude REAL,
            air_temperature REAL,
            humidity REAL,
            airport_weather TEXT,
            vehicle_count INTEGER,
            primary_vehicle_type TEXT,
            detection_confidence REAL,
            processing_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_records(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trigger_source ON traffic_records(trigger_source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_radar_speed ON traffic_records(radar_speed) WHERE radar_speed IS NOT NULL")
    
    # Create summary table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date DATE PRIMARY KEY,
            total_detections INTEGER DEFAULT 0,
            avg_speed REAL,
            max_speed REAL,
            vehicle_types TEXT,
            weather_conditions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully")

if __name__ == '__main__':
    init_database()
EOF

python3 /tmp/init_database.py
rm /tmp/init_database.py

# Test Redis connection
echo "🔧 Testing Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis not available - starting Redis..."
    sudo systemctl start redis
    sleep 2
fi

# Start services in order
echo "🚀 Starting persistence services..."

echo "Starting database persistence service..."
sudo systemctl start database-persistence.service
sleep 3

echo "Starting Redis optimization service..."
sudo systemctl start redis-optimization.service
sleep 2

echo "Starting consolidated API service..."
sudo systemctl start consolidated-api.service
sleep 2

# Check service status
echo "📊 Service Status:"
services=("database-persistence" "redis-optimization" "consolidated-api")

for service in "${services[@]}"; do
    if sudo systemctl is-active --quiet "$service.service"; then
        echo "  ✅ $service: RUNNING"
    else
        echo "  ❌ $service: FAILED"
        sudo systemctl status "$service.service" --no-pager -l
    fi
done

# Show current data status
echo ""
echo "📈 Current Data Status:"

# Check database
if [ -f "$STORAGE_DIR/traffic_monitoring.db" ]; then
    db_size=$(du -h "$STORAGE_DIR/traffic_monitoring.db" | cut -f1)
    echo "  Database size: $db_size"
else
    echo "  Database: Not yet created"
fi

# Check Redis keys
if command -v redis-cli > /dev/null 2>&1; then
    total_keys=$(redis-cli dbsize 2>/dev/null || echo "0")
    echo "  Redis keys: $total_keys"
    
    # Show key distribution
    if [ "$total_keys" -gt "0" ]; then
        echo "  Key patterns:"
        redis-cli --scan --pattern "sky_analysis:*" 2>/dev/null | wc -l | xargs echo "    Sky analysis:"
        redis-cli --scan --pattern "vehicle_detection:*" 2>/dev/null | wc -l | xargs echo "    Vehicle detection:"
        redis-cli --scan --pattern "weather:*" 2>/dev/null | wc -l | xargs echo "    Weather:"
        redis-cli --scan --pattern "consolidation:*" 2>/dev/null | wc -l | xargs echo "    Consolidation:"
    fi
fi

echo ""
echo "🎯 Deployment Complete!"
echo ""
echo "Architecture Pipeline:"
echo "  Radar Motion Detection"
echo "    ↓"
echo "  Consolidator Service (collects comprehensive data)"
echo "    ↓"
echo "  Database Persistence (stores structured records)"
echo "    ↓"
echo "  Enhanced API (serves data to external systems)"
echo ""
echo "Parallel Services:"
echo "  Redis Optimization (manages memory efficiently)"
echo ""
echo "API Endpoints Available:"
echo "  http://localhost:5000/api/v1/traffic/recent"
echo "  http://localhost:5000/api/v1/traffic/summary"
echo "  http://localhost:5000/api/v1/traffic/analytics"
echo "  http://localhost:5000/api/v1/traffic/search"
echo "  http://localhost:5000/api/v1/health/database"
echo ""
echo "Monitor with:"
echo "  sudo journalctl -u database-persistence.service -f"
echo "  sudo journalctl -u redis-optimization.service -f"
echo "  sudo journalctl -u consolidated-api.service -f"
echo ""
echo "Next Steps:"
echo "  1. Monitor service logs for successful data processing"
echo "  2. Test API endpoints with traffic data"
echo "  3. Create external website to consume API data"
echo "  4. Configure alerts for service health monitoring"