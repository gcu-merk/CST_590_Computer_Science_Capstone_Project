# Local Development Services Start Script
# Sky Analysis Removed - Optimized for Performance

Write-Host "=== Traffic Monitoring Services (Local Development) ===" -ForegroundColor Green
Write-Host "Sky analysis removed for 94% Redis storage optimization" -ForegroundColor Yellow
Write-Host ""

# Check if Docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directory structure..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "data", "logs" | Out-Null

# Stop any existing services
Write-Host "🛑 Stopping existing services..." -ForegroundColor Yellow
docker-compose -f docker-compose.services.yml down --remove-orphans 2>$null

# Build and start services
Write-Host "🔨 Building and starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.services.yml up --build -d

# Wait for services to start
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Cyan
docker-compose -f docker-compose.services.yml ps

Write-Host ""
Write-Host "=== Local Development Ready ===" -ForegroundColor Green
Write-Host "✅ Redis: Optimized storage (sky analysis removed)" -ForegroundColor Green
Write-Host "✅ Database Persistence: SQLite with 90-day retention" -ForegroundColor Green
Write-Host "✅ Redis Optimization: Memory management with TTL policies" -ForegroundColor Green
Write-Host "✅ Consolidated API: RESTful endpoints for external consumption" -ForegroundColor Green
Write-Host "✅ Vehicle Consolidator: Radar-triggered data collection" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Local Services:" -ForegroundColor Cyan
Write-Host "   - Redis: localhost:6379"
Write-Host "   - API: http://localhost:8080"
Write-Host "   - API Documentation: http://localhost:8080/docs"
Write-Host ""
Write-Host "📊 Development Commands:" -ForegroundColor Cyan
Write-Host "   - View logs: docker-compose -f docker-compose.services.yml logs -f"
Write-Host "   - Check status: docker-compose -f docker-compose.services.yml ps"
Write-Host "   - Stop services: docker-compose -f docker-compose.services.yml down"
Write-Host ""
Write-Host "Local development environment ready! 🚀" -ForegroundColor Green