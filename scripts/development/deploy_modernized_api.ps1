#!/usr/bin/env powershell
# Deploy Modernized API to Raspberry Pi
# This script copies the updated best practices API architecture to the Pi

param(
    [string]$PiHost = "100.121.231.16",
    [string]$PiUser = "pi",
    [switch]$Test = $false
)

Write-Host "🚀 Deploying Modernized API to Pi..." -ForegroundColor Green
Write-Host "Target: $PiUser@$PiHost (Tailscale)" -ForegroundColor Cyan

# Check if we can reach the Pi via Tailscale
Write-Host "`n📡 Testing Pi connectivity via Tailscale..." -ForegroundColor Yellow
$pingResult = Test-NetConnection -ComputerName $PiHost -Port 22 -WarningAction SilentlyContinue

if (-not $pingResult.TcpTestSucceeded) {
    Write-Host "❌ Cannot reach Pi at $PiHost on port 22" -ForegroundColor Red
    Write-Host "   Make sure Pi is powered on and Tailscale is running" -ForegroundColor Yellow
    Write-Host "   Check Tailscale status: tailscale status" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Pi is reachable!" -ForegroundColor Green

# Files to deploy
$filesToDeploy = @(
    "edge_api/config.py",
    "edge_api/error_handling.py", 
    "edge_api/data_access.py",
    "edge_api/services.py",
    "edge_api/swagger_api_gateway.py",
    "camera_free_api.py",
    "requirements-api.txt",
    "API_ARCHITECTURE.md"
)

Write-Host "`n📦 Files to deploy:" -ForegroundColor Yellow
foreach ($file in $filesToDeploy) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file (missing)" -ForegroundColor Red
    }
}

if ($Test) {
    Write-Host "`n🧪 Test mode - no actual deployment" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n🔄 Starting deployment..." -ForegroundColor Yellow

# Create backup on Pi
Write-Host "Creating backup of existing API..." -ForegroundColor Cyan
ssh $PiUser@$PiHost "
    if [ -d ~/edge_api ]; then
        cp -r ~/edge_api ~/edge_api_backup_$(date +%Y%m%d_%H%M%S)
        echo 'Backup created'
    fi
    mkdir -p ~/edge_api
"

# Copy modernized files
Write-Host "Copying modernized API files..." -ForegroundColor Cyan
foreach ($file in $filesToDeploy) {
    if (Test-Path $file) {
        $targetPath = if ($file.StartsWith("edge_api/")) { 
            "~/edge_api/" + (Split-Path $file -Leaf)
        } else { 
            "~/" + (Split-Path $file -Leaf) 
        }
        
        Write-Host "   📄 $file -> $targetPath" -ForegroundColor Gray
        scp $file "${PiUser}@${PiHost}:$targetPath"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Copied $file" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to copy $file" -ForegroundColor Red
        }
    }
}

# Update permissions and install requirements
Write-Host "`n🔧 Setting up on Pi..." -ForegroundColor Cyan
ssh $PiUser@$PiHost "
    # Make API executable
    chmod +x ~/camera_free_api.py
    chmod +x ~/edge_api/*.py
    
    # Install/update Python requirements
    if [ -f ~/requirements-api.txt ]; then
        echo 'Installing Python requirements...'
        pip3 install -r ~/requirements-api.txt --user
    fi
    
    # Check Docker services status
    echo 'Docker services status:'
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    
    # Test Redis connection
    echo 'Testing Redis connection:'
    redis-cli ping 2>/dev/null || echo 'Redis not responding'
    
    # Get radar data count
    echo 'Radar data entries:'
    redis-cli XLEN radar_data 2>/dev/null || echo 'Could not get radar data count'
"

Write-Host "`n🧪 Testing modernized API on Pi..." -ForegroundColor Yellow
ssh $PiUser@$PiHost "
    cd ~
    python3 -c \"
try:
    from edge_api.config import config
    print('✅ Config module imported')
    print(f'   Redis: {config.database.redis_host}:{config.database.redis_port}')
except Exception as e:
    print(f'❌ Config import failed: {e}')

try:
    from edge_api.services import get_detection_service
    print('✅ Services module imported')
except Exception as e:
    print(f'❌ Services import failed: {e}')

print('\\n🎯 Modernized API modules ready!')
\"
"

Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. SSH to Pi: ssh $PiUser@$PiHost" -ForegroundColor White
Write-Host "   2. Test API: python3 camera_free_api.py" -ForegroundColor White
Write-Host "   3. View in browser: http://$PiHost:5000/api/docs" -ForegroundColor White
Write-Host "   4. Test endpoints via Tailscale:" -ForegroundColor White
Write-Host "      • http://$PiHost:5000/api/detections" -ForegroundColor Gray
Write-Host "      • http://$PiHost:5000/api/speeds" -ForegroundColor Gray  
Write-Host "      • http://$PiHost:5000/api/analytics" -ForegroundColor Gray

Write-Host "`n📊 The modernized API includes:" -ForegroundColor Cyan
Write-Host "   • Environment-based configuration" -ForegroundColor White
Write-Host "   • Standardized error handling" -ForegroundColor White
Write-Host "   • Redis connection pooling" -ForegroundColor White
Write-Host "   • Service layer architecture" -ForegroundColor White
Write-Host "   • Performance monitoring" -ForegroundColor White
Write-Host "   • Real radar data processing (46K+ entries)" -ForegroundColor White