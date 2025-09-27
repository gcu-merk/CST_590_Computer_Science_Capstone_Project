#!/usr/bin/env pwsh
<#
.SYNOPSIS
Check DHT22 weather service status and verify GPIO library installation

.DESCRIPTION
This script helps verify that the DHT22 service is working correctly with the
entrypoint-based GPIO library installation approach.
#>

param(
    [Parameter()]
    [string]$PiAddress = "192.168.1.100",
    
    [Parameter()]
    [int]$ApiPort = 5000
)

Write-Host "DHT22 Service Status Check" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Test API connectivity
Write-Host "1. Testing API connectivity..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri "http://${PiAddress}:${ApiPort}/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✓ API Gateway is responding" -ForegroundColor Green
    
    # Test weather endpoint
    Write-Host "2. Testing weather endpoint..." -ForegroundColor Yellow
    $weatherResponse = Invoke-WebRequest -Uri "http://${PiAddress}:${ApiPort}/weather/current" -UseBasicParsing -TimeoutSec 10
    $weatherData = $weatherResponse.Content | ConvertFrom-Json
    
    Write-Host "   ✓ Weather data retrieved successfully" -ForegroundColor Green
    Write-Host "   Temperature: $($weatherData.temperature)°C" -ForegroundColor Cyan
    Write-Host "   Humidity: $($weatherData.humidity)%" -ForegroundColor Cyan
    Write-Host "   Last Updated: $($weatherData.timestamp)" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ✗ Unable to connect to Pi at $PiAddress" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual verification steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to Pi: ssh pi@$PiAddress" -ForegroundColor White
    Write-Host "2. Check service status: docker ps | grep dht22" -ForegroundColor White
    Write-Host "3. Check logs: docker logs dht22-weather" -ForegroundColor White
    Write-Host "4. Check entrypoint logs: docker logs dht22-weather 2>&1 | grep -i gpio" -ForegroundColor White
    Write-Host "5. Test Redis data: docker exec redis redis-cli HGETALL weather:dht22" -ForegroundColor White
}

Write-Host ""
Write-Host "Expected Entrypoint Behavior:" -ForegroundColor Yellow
Write-Host "- Detects Pi hardware via /proc/cpuinfo" -ForegroundColor White
Write-Host "- Installs lgpio>=0.2.2.0 and gpiozero>=1.6.2" -ForegroundColor White
Write-Host "- Executes: python -m edge_processing.dht_22_weather_service_enhanced" -ForegroundColor White
Write-Host "- Should show 'GPIO libraries installed successfully' in logs" -ForegroundColor White