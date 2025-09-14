#!/bin/bash
# Enhanced deployment script for host camera capture integration

set -e  # Exit on error

echo "🚀 Deploying Traffic Monitoring System with Host Camera Service..."
echo "================================================================="

DEPLOY_DIR="/home/merk/traffic-monitor-deploy"
SERVICE_NAME="host-camera-capture"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# 1. Pre-deployment checks
echo "🔍 Pre-deployment validation..."

# Check if camera is available
if ! rpicam-still --list-cameras >/dev/null 2>&1; then
    echo "❌ Camera not detected - deployment aborted"
    exit 1
fi

# Check storage mount
if [ ! -d "/mnt/storage" ]; then
    echo "❌ Storage mount not found - deployment aborted"
    exit 1
fi

echo "✅ Pre-deployment checks passed"

# 2. Backup current deployment
echo "📦 Creating deployment backup..."
if [ -f "$DEPLOY_DIR/host-camera-capture.py" ]; then
    cp "$DEPLOY_DIR/host-camera-capture.py" "$DEPLOY_DIR/host-camera-capture.py.backup.$TIMESTAMP"
fi

# 3. Deploy host camera capture service
echo "📷 Deploying host camera capture service..."

# Copy the host camera capture script
cp host-camera-capture.py "$DEPLOY_DIR/"
chown merk:merk "$DEPLOY_DIR/host-camera-capture.py"
chmod +x "$DEPLOY_DIR/host-camera-capture.py"

# Test the camera capture script
echo "🧪 Testing camera capture functionality..."
cd "$DEPLOY_DIR"
if ! python3 host-camera-capture.py --test-only; then
    echo "❌ Camera test failed - deployment aborted"
    exit 1
fi

# 4. Install/update systemd service
echo "⚙️ Installing systemd service..."

# Copy service file
sudo cp deployment/host-camera-capture.service /etc/systemd/system/
sudo systemctl daemon-reload

# Stop existing service if running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🛑 Stopping existing camera service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

# Enable and start the service
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# 5. Deploy Docker services
echo "🐳 Deploying Docker services..."

# Stop existing containers
docker-compose down || true

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# 6. Post-deployment verification
echo "✅ Verifying deployment..."

# Wait for services to start
sleep 15

# Check host camera service
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "❌ Host camera service failed to start"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

# Check Docker services
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker services failed to start"
    docker-compose ps
    exit 1
fi

# Test image capture
echo "📸 Testing image capture pipeline..."
sleep 65  # Wait for at least one capture

LATEST_IMAGE=$(find /mnt/storage/camera_capture/live/ -name "capture_*.jpg" -mtime -1 | head -1)
if [ -z "$LATEST_IMAGE" ]; then
    echo "❌ No recent images found"
    exit 1
fi

echo "✅ Found recent capture: $(basename "$LATEST_IMAGE")"

# Test weather API (if containers are healthy)
if curl -f -s http://localhost:5000/api/health >/dev/null 2>&1; then
    echo "✅ Weather API responding"
else
    echo "⚠️ Weather API not responding (may need more time to start)"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "==============================================="
echo "Services Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -5
echo ""
docker-compose ps
echo ""
echo "📊 Recent captures:"
ls -la /mnt/storage/camera_capture/live/ | tail -3