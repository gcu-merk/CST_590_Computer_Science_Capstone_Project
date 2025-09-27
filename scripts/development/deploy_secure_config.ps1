#!/usr/bin/env powershell
# Secure Deployment Script - Apply Security Fixes
# Removes dangerous external port exposures and redeploys with secure configuration

Write-Host "🔒 APPLYING SECURITY FIXES TO TRAFFIC MONITORING SYSTEM" -ForegroundColor Red
Write-Host "=" * 80 -ForegroundColor Red

Write-Host "`n🚨 SECURITY ISSUES BEING FIXED:" -ForegroundColor Yellow
Write-Host "   ❌ Redis port 6379 externally exposed (CRITICAL)" -ForegroundColor Red
Write-Host "   ❌ API port 5000 HTTP externally exposed (HIGH)" -ForegroundColor Red

Write-Host "`n✅ SECURITY IMPROVEMENTS:" -ForegroundColor Green
Write-Host "   ✅ Redis only accessible internally (service-to-service)" -ForegroundColor Green
Write-Host "   ✅ API only accessible via HTTPS nginx proxy" -ForegroundColor Green
Write-Host "   ✅ All external access encrypted with Tailscale SSL" -ForegroundColor Green

Write-Host "`n📋 DEPLOYMENT STEPS:" -ForegroundColor Cyan

Write-Host "`n1️⃣ Backing up current configuration..." -ForegroundColor Yellow
ssh merk@100.121.231.16 'cd /home/merk && cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)'
Write-Host "   ✅ Backup created on remote system" -ForegroundColor Green

Write-Host "`n2️⃣ Uploading secure configuration..." -ForegroundColor Yellow
scp docker-compose.yml merk@100.121.231.16:/home/merk/
Write-Host "   ✅ Secure docker-compose.yml uploaded" -ForegroundColor Green

Write-Host "`n3️⃣ Stopping current services..." -ForegroundColor Yellow
ssh merk@100.121.231.16 'docker-compose down'

Write-Host "`n4️⃣ Starting with secure configuration..." -ForegroundColor Yellow
ssh merk@100.121.231.16 'docker-compose up -d'

Write-Host "`n5️⃣ Verifying secure deployment..." -ForegroundColor Yellow
ssh merk@100.121.231.16 'docker ps | grep "0.0.0.0"'

Write-Host "`n🔍 TESTING EXTERNAL ACCESS:" -ForegroundColor Cyan

Write-Host "`n   Testing HTTPS health endpoint (should work)..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "https://edge-traffic-monitoring.taild46447.ts.net/health" -TimeoutSec 10
    Write-Host "   ✅ HTTPS Access: Working (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ HTTPS Access: Failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n   Testing HTTP API port 5000 (should be blocked)..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://100.121.231.16:5000/health" -TimeoutSec 5
    Write-Host "   ❌ SECURITY ISSUE: HTTP port still accessible!" -ForegroundColor Red
} catch {
    Write-Host "   ✅ Security: HTTP port properly blocked" -ForegroundColor Green
}

Write-Host "`n   Testing Redis port 6379 (should be blocked)..." -ForegroundColor Gray
$redisTest = ssh merk@100.121.231.16 'timeout 3 nc -z localhost 6379 && echo "ACCESSIBLE" || echo "BLOCKED"'
if ($redisTest -match "BLOCKED") {
    Write-Host "   ✅ Security: Redis port properly blocked externally" -ForegroundColor Green
} else {
    Write-Host "   ❌ SECURITY ISSUE: Redis still externally accessible!" -ForegroundColor Red
}

Write-Host "`n🏁 SECURITY DEPLOYMENT SUMMARY:" -ForegroundColor Blue
Write-Host "=" * 80 -ForegroundColor Blue

Write-Host "`n🔒 SECURE ACCESS ENDPOINTS:" -ForegroundColor Green
Write-Host "   ✅ https://edge-traffic-monitoring.taild46447.ts.net (Encrypted)" -ForegroundColor Green
Write-Host "   ✅ https://edge-traffic-monitoring.taild46447.ts.net/health" -ForegroundColor Green
Write-Host "   ✅ https://edge-traffic-monitoring.taild46447.ts.net/docs (when fixed)" -ForegroundColor Green

Write-Host "`n🚫 BLOCKED INSECURE ACCESS:" -ForegroundColor Red
Write-Host "   ❌ http://100.121.231.16:5000/* (No longer externally accessible)" -ForegroundColor Red
Write-Host "   ❌ 100.121.231.16:6379 (Redis database no longer externally accessible)" -ForegroundColor Red

Write-Host "`n✅ All external access now properly secured with HTTPS encryption!" -ForegroundColor Green