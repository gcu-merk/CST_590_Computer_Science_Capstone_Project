# Simple External API Test for Tailscale Domain
# Tests key endpoints at edge-traffic-monitoring.taild46447.ts.net

$BaseUrl = "https://edge-traffic-monitoring.taild46447.ts.net"

Write-Host "🌐 Testing External Access to Tailscale Domain" -ForegroundColor Green
Write-Host "🎯 Target: edge-traffic-monitoring.taild46447.ts.net" -ForegroundColor Green
Write-Host "=" * 80

# Test key endpoints
$endpoints = @(
    "/",
    "/health", 
    "/docs",
    "/swagger.json",
    "/api",
    "/api/health/system",
    "/api/vehicles/detections",
    "/api/weather/current"
)

$workingEndpoints = @()

foreach ($endpoint in $endpoints) {
    $url = "$BaseUrl$endpoint"
    Write-Host "`n🔍 Testing: $url" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing -SkipCertificateCheck
        $status = $response.StatusCode
        
        if ($status -eq 200) {
            Write-Host "   ✅ Status: $status (Success)" -ForegroundColor Green
            $workingEndpoints += $endpoint
            
            # Show response preview
            $content = $response.Content
            if ($content.Length -lt 200) {
                Write-Host "   📄 Response: $content" -ForegroundColor Gray
            } else {
                Write-Host "   📄 Response: $($content.Substring(0, 200))... (truncated)" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️ Status: $status" -ForegroundColor Yellow
        }
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -match "404") {
            Write-Host "   ❌ Status: 404 (Not Found)" -ForegroundColor Red
        } elseif ($errorMsg -match "500") {
            Write-Host "   💥 Status: 500 (Server Error)" -ForegroundColor Red
        } elseif ($errorMsg -match "timeout") {
            Write-Host "   ⏰ Timeout" -ForegroundColor Red
        } else {
            Write-Host "   💀 Error: $errorMsg" -ForegroundColor Red
        }
    }
}

Write-Host "`n" + ("=" * 80)
Write-Host "📊 SUMMARY" -ForegroundColor Blue
Write-Host "=" * 80

Write-Host "`n✅ WORKING ENDPOINTS ($($workingEndpoints.Count)):" -ForegroundColor Green
foreach ($ep in $workingEndpoints) {
    Write-Host "   • $BaseUrl$ep" -ForegroundColor Green
}

$failedCount = $endpoints.Count - $workingEndpoints.Count
Write-Host "`n❌ FAILED ENDPOINTS ($failedCount):" -ForegroundColor Red

Write-Host "`n🔗 EXTERNAL ACCESS STATUS:" -ForegroundColor Cyan
if ($workingEndpoints.Count -gt 0) {
    Write-Host "   ✅ External access is WORKING via Tailscale domain" -ForegroundColor Green
    Write-Host "   🌐 Public URL: $BaseUrl" -ForegroundColor Green
} else {
    Write-Host "   ❌ No endpoints are externally accessible" -ForegroundColor Red
}

Write-Host "`nTest completed at $(Get-Date)" -ForegroundColor Blue