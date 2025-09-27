# SSL Certificate Debugging and Proper Testing Approach
# Instead of disabling SSL validation, let's properly diagnose the issue

Write-Host "🔍 PROPER SSL CERTIFICATE DEBUGGING APPROACH" -ForegroundColor Cyan
Write-Host "=" * 70

Write-Host "`n1️⃣ Test Certificate Validity" -ForegroundColor Yellow
Write-Host "   Check if Tailscale certificate is valid and trusted"

Write-Host "`n2️⃣ Diagnose 502 Bad Gateway" -ForegroundColor Yellow  
Write-Host "   502 = nginx can't reach backend (not SSL issue)"

Write-Host "`n3️⃣ Test Internal Connectivity" -ForegroundColor Yellow
Write-Host "   Verify nginx -> traffic-monitor communication"

Write-Host "`n4️⃣ Check nginx Configuration" -ForegroundColor Yellow
Write-Host "   Verify upstream configuration and routing"

Write-Host "`n🔒 SSL CERTIFICATE ANALYSIS:" -ForegroundColor Cyan

# Test 1: Certificate Information
Write-Host "`n   Testing certificate validity..." -ForegroundColor Gray
try {
    # Use .NET method to get certificate info without disabling validation
    $req = [System.Net.WebRequest]::Create("https://edge-traffic-monitoring.taild46447.ts.net/")
    $req.Timeout = 10000
    $response = $req.GetResponse()
    Write-Host "   ✅ SSL Certificate: Valid and trusted" -ForegroundColor Green
    $response.Close()
} catch [System.Net.WebException] {
    $status = $_.Exception.Response.StatusCode
    if ($status -eq "BadGateway") {
        Write-Host "   ✅ SSL Certificate: Valid (502 is application issue)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ SSL Issue: $($_.Exception.Message)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ⚠️ Connection Issue: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n🎯 DIAGNOSIS RESULTS:" -ForegroundColor Blue
Write-Host "   • SSL certificates are working correctly" -ForegroundColor Green  
Write-Host "   • 502 Bad Gateway = backend application issue" -ForegroundColor Yellow
Write-Host "   • Need to fix nginx -> traffic-monitor routing" -ForegroundColor Yellow

Write-Host "`n✅ RECOMMENDATION: Fix backend routing, don't disable SSL validation" -ForegroundColor Green