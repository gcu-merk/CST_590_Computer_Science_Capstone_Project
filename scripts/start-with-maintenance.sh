#!/bin/bash
# Startup script for data-maintenance service
# Starts both main application and maintenance daemon

set -e

echo "Starting data-maintenance service with maintenance daemon..."

# Wait for system to be ready
echo "Waiting for system initialization..."
sleep 10

# Ensure required directories exist
mkdir -p /mnt/storage/logs/maintenance
mkdir -p /mnt/storage/scripts

# Copy maintenance scripts to expected location if they don't exist
if [ ! -f "/mnt/storage/scripts/container-maintenance.py" ] && [ -f "/app/scripts/container-maintenance.py" ]; then
    echo "Copying maintenance scripts to storage location..."
    cp /app/scripts/container-maintenance.py /mnt/storage/scripts/
    chmod +x /mnt/storage/scripts/container-maintenance.py
fi

# Start maintenance daemon in background
echo "Starting maintenance daemon..."
python3 /app/scripts/container-maintenance.py --daemon &
MAINTENANCE_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    if [ ! -z "$MAINTENANCE_PID" ]; then
        kill $MAINTENANCE_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start main application
echo "Starting main application..."
exec python main_edge_app.py