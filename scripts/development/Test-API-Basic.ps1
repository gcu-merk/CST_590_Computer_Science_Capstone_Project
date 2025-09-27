# Simple API Endpoint Testing Script
param(
    [string]$PiHost = "100.121.231.16",
    [int]$ExternalPort = 8443,
    [string]$SSHUser = "merk"
)

Write-Host "=================================================================================" -ForegroundColor Blue
Write-Host "API ENDPOINT TESTING" -ForegroundColor Blue
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Blue
Write-Host "=================================================================================" -ForegroundColor Blue

# Bypass SSL certificate validation
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

Write-Host "`nTesting External Endpoints (Dashboard Access):" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Yellow

$externalUrls = @(
    "https://$PiHost`:$ExternalPort/api/health/system",
    "https://$PiHost`:$ExternalPort/api/health/stats", 
    "https://$PiHost`:$ExternalPort/api/vehicles/detections",
    "https://$PiHost`:$ExternalPort/api/weather/current",
    "https://$PiHost`:$ExternalPort/api/events/recent",
    "https://$PiHost`:$ExternalPort/api/analytics",
    "https://$PiHost`:$ExternalPort/api",
    "https://$PiHost`:$ExternalPort/docs",
    "https://$PiHost`:$ExternalPort/swagger.json"
)

$workingExternal = 0
$failedExternal = 0

foreach ($url in $externalUrls) {
    Write-Host "`nTesting: $url" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        Write-Host "  Status: $($response.StatusCode) - SUCCESS" -ForegroundColor Green
        $workingExternal++
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "  Status: $statusCode - FAILED" -ForegroundColor Red
        } else {
            Write-Host "  Connection Failed" -ForegroundColor Red
        }
        $failedExternal++
    }
}

Write-Host "`nTesting Internal Endpoints via SSH:" -ForegroundColor Yellow
Write-Host "=" * 40 -ForegroundColor Yellow

$internalUrls = @(
    "http://localhost:5000/api/health/system",
    "http://localhost:5000/api/health/stats",
    "http://localhost:5000/api/vehicles/detections", 
    "http://localhost:5000/api/weather/current",
    "http://localhost:5000/api/events/recent",
    "http://localhost:5000/api/analytics",
    "http://localhost:5000/api",
    "http://localhost:5000/docs",
    "http://localhost:5000/swagger.json",
    "http://localhost:5000/health"
)

$workingInternal = 0
$failedInternal = 0

foreach ($url in $internalUrls) {
    Write-Host "`nTesting SSH: $url" -ForegroundColor Cyan
    try {
        $sshCommand = "ssh $SSHUser@$PiHost curl -s -o /dev/null -w %{http_code} $url"
        $statusCode = cmd /c $sshCommand 2>$null
        
        if ($statusCode -eq "200") {
            Write-Host "  Status: $statusCode - SUCCESS" -ForegroundColor Green
            $workingInternal++
        } else {
            Write-Host "  Status: $statusCode - FAILED" -ForegroundColor Red
            $failedInternal++
        }
    }
    catch {
        Write-Host "  SSH Connection Failed" -ForegroundColor Red
        $failedInternal++
    }
}

Write-Host "`nContainer Status:" -ForegroundColor Cyan
try {
    $containerCommand = "ssh $SSHUser@$PiHost docker ps --format table {{.Names}}\t{{.Status}}"
    $containerStatus = cmd /c $containerCommand 2>$null
    Write-Host $containerStatus -ForegroundColor White
} catch {
    Write-Host "Failed to get container status" -ForegroundColor Red
}

Write-Host "`n=================================================================================" -ForegroundColor Blue
Write-Host "SUMMARY" -ForegroundColor Blue
Write-Host "=================================================================================" -ForegroundColor Blue

Write-Host "`nExternal Endpoints (Dashboard Access):" -ForegroundColor Cyan
Write-Host "  Working: $workingExternal" -ForegroundColor Green
Write-Host "  Failed:  $failedExternal" -ForegroundColor Red

Write-Host "`nInternal Endpoints (Pi localhost):" -ForegroundColor Cyan  
Write-Host "  Working: $workingInternal" -ForegroundColor Green
Write-Host "  Failed:  $failedInternal" -ForegroundColor Red

if ($workingExternal -gt 0) {
    Write-Host "`nDASHBOARD STATUS: READY - $workingExternal external endpoints working" -ForegroundColor Green
} else {
    Write-Host "`nDASHBOARD STATUS: ISSUE - No external endpoints accessible" -ForegroundColor Red
    if ($workingInternal -gt 0) {
        Write-Host "Internal endpoints work - likely nginx/SSL issue" -ForegroundColor Yellow
    } else {
        Write-Host "No internal endpoints work - API service may be down" -ForegroundColor Red
    }
}

Write-Host "`n=================================================================================" -ForegroundColor Blue