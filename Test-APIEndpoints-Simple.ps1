# Comprehensive External API Endpoint Testing Script for PowerShell
# Tests all API endpoints that the dashboard will use

param(
    [string]$PiHost = "100.121.231.16",
    [int]$ExternalPort = 8443,
    [string]$SSHUser = "merk"
)

Write-Host "=================================================================================" -ForegroundColor Blue
Write-Host "🚦 COMPREHENSIVE EXTERNAL API ENDPOINT TESTING" -ForegroundColor Blue
Write-Host "📅 Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')" -ForegroundColor Blue
Write-Host "=================================================================================" -ForegroundColor Blue

# Function to test external endpoint
function Test-Endpoint($url, $description) {
    Write-Host "`n🔍 Testing: $description" -ForegroundColor Cyan
    Write-Host "   URL: $url" -ForegroundColor Gray
    
    try {
        # Bypass SSL certificate validation
        add-type @"
            using System.Net;
            using System.Security.Cryptography.X509Certificates;
            public class TrustAllCertsPolicy : ICertificatePolicy {
                public bool CheckValidationResult(
                    ServicePoint srvPoint, X509Certificate certificate,
                    WebRequest request, int certificateProblem) {
                    return true;
                }
            }
"@
        [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
        
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200) {
            Write-Host "   ✅ Status: $statusCode (Success)" -ForegroundColor Green
            $content = $response.Content
            if ($content.Length -gt 200) {
                Write-Host "   📄 Response: $($content.Substring(0, 200))..." -ForegroundColor White
            } else {
                Write-Host "   📄 Response: $content" -ForegroundColor White
            }
            return @{ Success = $true; Status = $statusCode }
        } else {
            Write-Host "   ⚠️  Status: $statusCode" -ForegroundColor Yellow
            return @{ Success = $false; Status = $statusCode }
        }
    } catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            if ($statusCode -eq 404) {
                Write-Host "   ❌ Status: $statusCode (Not Found)" -ForegroundColor Red
            } elseif ($statusCode -eq 500) {
                Write-Host "   💥 Status: $statusCode (Server Error)" -ForegroundColor Red
            } else {
                Write-Host "   ⚠️  Status: $statusCode" -ForegroundColor Yellow
            }
            return @{ Success = $false; Status = $statusCode }
        } else {
            Write-Host "   💀 Connection Failed: $($_.Exception.Message)" -ForegroundColor Red
            return @{ Success = $false; Status = 0 }
        }
    }
}

# Function to test internal endpoint via SSH
function Test-SSHEndpoint($url, $description) {
    Write-Host "`n🔍 Testing (SSH): $description" -ForegroundColor Cyan
    Write-Host "   URL: $url" -ForegroundColor Gray
    
    try {
        $sshCmd = "ssh $SSHUser@$PiHost `"curl -s -o /dev/null -w '%{http_code}' $url`""
        $statusResult = cmd /c $sshCmd 2>$null
        
        if ($statusResult -match '^\d+$') {
            $statusCode = [int]$statusResult
            
            if ($statusCode -eq 200) {
                Write-Host "   ✅ Status: $statusCode (Success)" -ForegroundColor Green
                return @{ Success = $true; Status = $statusCode }
            } elseif ($statusCode -eq 404) {
                Write-Host "   ❌ Status: $statusCode (Not Found)" -ForegroundColor Red
                return @{ Success = $false; Status = $statusCode }
            } elseif ($statusCode -eq 500) {
                Write-Host "   💥 Status: $statusCode (Server Error)" -ForegroundColor Red
                return @{ Success = $false; Status = $statusCode }
            } else {
                Write-Host "   ⚠️  Status: $statusCode" -ForegroundColor Yellow
                return @{ Success = $false; Status = $statusCode }
            }
        } else {
            Write-Host "   💀 SSH Connection Failed" -ForegroundColor Red
            return @{ Success = $false; Status = 0 }
        }
    } catch {
        Write-Host "   💀 SSH Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Success = $false; Status = 0 }
    }
}

# Define endpoints to test
$externalEndpoints = @(
    @("https://$PiHost`:$ExternalPort/api/health/system", "External API System Health"),
    @("https://$PiHost`:$ExternalPort/api/health/stats", "External API Stats"),
    @("https://$PiHost`:$ExternalPort/api/vehicles/detections", "External Vehicle Detections"),
    @("https://$PiHost`:$ExternalPort/api/weather/current", "External Current Weather"),
    @("https://$PiHost`:$ExternalPort/api/events/recent", "External Recent Events"),
    @("https://$PiHost`:$ExternalPort/api/analytics", "External Traffic Analytics"),
    @("https://$PiHost`:$ExternalPort/api", "External API Root"),
    @("https://$PiHost`:$ExternalPort/docs", "External Swagger UI"),
    @("https://$PiHost`:$ExternalPort/swagger.json", "External Swagger JSON")
)

$internalEndpoints = @(
    @("http://localhost:5000/api/health/system", "Internal API System Health"),
    @("http://localhost:5000/api/health/stats", "Internal API Stats"),
    @("http://localhost:5000/api/vehicles/detections", "Internal Vehicle Detections"),
    @("http://localhost:5000/api/weather/current", "Internal Current Weather"),
    @("http://localhost:5000/api/events/recent", "Internal Recent Events"),
    @("http://localhost:5000/api/analytics", "Internal Traffic Analytics"),
    @("http://localhost:5000/api", "Internal API Root"),
    @("http://localhost:5000/docs", "Internal Swagger UI"),
    @("http://localhost:5000/swagger.json", "Internal Swagger JSON"),
    @("http://localhost:5000/health", "Internal Basic Health")
)

# Test external endpoints
Write-Host "`n🌐 TESTING EXTERNAL ENDPOINTS (Dashboard Access)" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow

$externalResults = @()
foreach ($endpoint in $externalEndpoints) {
    $result = Test-Endpoint -url $endpoint[0] -description $endpoint[1]
    $externalResults += @{ Url = $endpoint[0]; Description = $endpoint[1]; Result = $result }
}

# Test internal endpoints via SSH
Write-Host "`n🏠 TESTING INTERNAL ENDPOINTS (Pi localhost)" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow

$internalResults = @()
foreach ($endpoint in $internalEndpoints) {
    $result = Test-SSHEndpoint -url $endpoint[0] -description $endpoint[1]
    $internalResults += @{ Url = $endpoint[0]; Description = $endpoint[1]; Result = $result }
}

# Get container status
Write-Host "`n🐳 CONTAINER STATUS:" -ForegroundColor Cyan
try {
    $containerCmd = "ssh $SSHUser@$PiHost `"docker ps --format 'table {{.Names}}\t{{.Status}}'`""
    $containerStatus = cmd /c $containerCmd 2>$null
    Write-Host $containerStatus -ForegroundColor White
} catch {
    Write-Host "Failed to get container status: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n=================================================================================" -ForegroundColor Blue
Write-Host "📊 TEST SUMMARY" -ForegroundColor Blue
Write-Host "=================================================================================" -ForegroundColor Blue

$externalWorking = ($externalResults | Where-Object { $_.Result.Success }).Count
$externalFailed = ($externalResults | Where-Object { -not $_.Result.Success }).Count
$internalWorking = ($internalResults | Where-Object { $_.Result.Success }).Count
$internalFailed = ($internalResults | Where-Object { -not $_.Result.Success }).Count

Write-Host "`n🌐 EXTERNAL ENDPOINTS (Dashboard Access):" -ForegroundColor Cyan
Write-Host "✅ Working: $externalWorking, ❌ Failed: $externalFailed" -ForegroundColor White

if ($externalWorking -gt 0) {
    Write-Host "   ✅ WORKING:" -ForegroundColor Green
    $externalResults | Where-Object { $_.Result.Success } | ForEach-Object {
        Write-Host "      • $($_.Description)" -ForegroundColor Green
    }
}

if ($externalFailed -gt 0) {
    Write-Host "   ❌ FAILED:" -ForegroundColor Red
    $externalResults | Where-Object { -not $_.Result.Success } | ForEach-Object {
        Write-Host "      • $($_.Description) (Status: $($_.Result.Status))" -ForegroundColor Red
    }
}

Write-Host "`n🏠 INTERNAL ENDPOINTS (Pi localhost):" -ForegroundColor Cyan
Write-Host "✅ Working: $internalWorking, ❌ Failed: $internalFailed" -ForegroundColor White

if ($internalWorking -gt 0) {
    Write-Host "   ✅ WORKING:" -ForegroundColor Green
    $internalResults | Where-Object { $_.Result.Success } | ForEach-Object {
        Write-Host "      • $($_.Description)" -ForegroundColor Green
    }
}

if ($internalFailed -gt 0) {
    Write-Host "   ❌ FAILED:" -ForegroundColor Red
    $internalResults | Where-Object { -not $_.Result.Success } | ForEach-Object {
        Write-Host "      • $($_.Description) (Status: $($_.Result.Status))" -ForegroundColor Red
    }
}

# Final analysis
Write-Host "`n=================================================================================" -ForegroundColor Blue
Write-Host "🏁 Testing completed." -ForegroundColor Blue
Write-Host "🌐 External: $externalWorking working, $externalFailed failed" -ForegroundColor White
Write-Host "🏠 Internal: $internalWorking working, $internalFailed failed" -ForegroundColor White
Write-Host "=================================================================================" -ForegroundColor Blue

if ($externalWorking -gt 0) {
    Write-Host "`n✅ DASHBOARD READY: $externalWorking external endpoints working" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  DASHBOARD ISSUE: No external endpoints accessible" -ForegroundColor Yellow
    if ($internalWorking -gt 0) {
        Write-Host "   Internal endpoints work - likely nginx/SSL configuration issue" -ForegroundColor Yellow
    } else {
        Write-Host "   No internal endpoints work - API service may be down" -ForegroundColor Red
    }
}

Write-Host "`n📋 RECOMMENDATIONS:" -ForegroundColor Magenta
if ($externalFailed -gt 0) {
    Write-Host "   • Check nginx proxy configuration for external access" -ForegroundColor White
    Write-Host "   • Verify SSL certificates are properly configured" -ForegroundColor White
    Write-Host "   • Ensure all Docker containers are healthy and running" -ForegroundColor White
}
if ($internalFailed -gt 0) {
    Write-Host "   • Check Flask-RESTX API service is running on port 5000" -ForegroundColor White
    Write-Host "   • Verify API prefix configuration is correct" -ForegroundColor White
}