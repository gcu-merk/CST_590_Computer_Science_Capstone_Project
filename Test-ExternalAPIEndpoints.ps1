#Requires -Version 5.1
<#
.SYNOPSIS
    Comprehensive External API Endpoint Testing Script
.DESCRIPTION
    Tests all API endpoints that the dashboard will actually use via HTTPS
    Tests both external (dashboard access) and internal (SSH to Pi) endpoints
.EXAMPLE
    .\Test-ExternalAPIEndpoints.ps1
#>

[CmdletBinding()]
param(
    [string]$PiHost = "100.121.231.16",
    [int]$ExternalPort = 8443,
    [int]$InternalPort = 5000,
    [string]$SSHUser = "merk",
    [int]$TimeoutSeconds = 10
)

# Function to test external endpoints
function Test-ExternalEndpoint {
    param(
        [string]$Url,
        [string]$Description
    )
    
    Write-Host "`n🔍 Testing: $Description" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    
    try {
        # Create web request with timeout and SSL bypass
        $webRequest = [System.Net.WebRequest]::Create($Url)
        $webRequest.Timeout = $TimeoutSeconds * 1000
        $webRequest.Method = "GET"
        
        # Bypass SSL certificate validation for self-signed certs
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
        
        $response = $webRequest.GetResponse()
        $statusCode = [int]$response.StatusCode
        $statusDescription = $response.StatusDescription
        
        # Read response content
        $responseStream = $response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($responseStream)
        $content = $reader.ReadToEnd()
        $reader.Close()
        $response.Close()
        
        if ($statusCode -eq 200) {
            Write-Host "   ✅ Status: $statusCode ($statusDescription)" -ForegroundColor Green
            
            # Try to format JSON if possible
            try {
                $jsonObject = $content | ConvertFrom-Json
                $formattedJson = $jsonObject | ConvertTo-Json -Depth 3 -Compress
                if ($formattedJson.Length -gt 200) {
                    Write-Host "   📄 Response: $($formattedJson.Substring(0, 200))..." -ForegroundColor White
                } else {
                    Write-Host "   📄 Response: $formattedJson" -ForegroundColor White
                }
            } catch {
                # Not JSON, show as text
                if ($content.Length -gt 200) {
                    Write-Host "   📄 Response: $($content.Substring(0, 200))..." -ForegroundColor White
                } else {
                    Write-Host "   📄 Response: $content" -ForegroundColor White
                }
            }
        } elseif ($statusCode -eq 404) {
            Write-Host "   ❌ Status: $statusCode (Not Found)" -ForegroundColor Red
        } elseif ($statusCode -eq 500) {
            Write-Host "   💥 Status: $statusCode (Server Error)" -ForegroundColor Red
        } else {
            Write-Host "   ⚠️  Status: $statusCode ($statusDescription)" -ForegroundColor Yellow
        }
        
        return @{
            Status = $statusCode
            Content = $content
            Success = ($statusCode -eq 200)
        }
        
    } catch [System.Net.WebException] {
        $ex = $_.Exception
        if ($ex.Response) {
            $statusCode = [int]$ex.Response.StatusCode
            Write-Host "   ❌ Status: $statusCode ($($ex.Response.StatusDescription))" -ForegroundColor Red
            return @{ Status = $statusCode; Content = ""; Success = $false }
        } else {
            Write-Host "   💀 Connection Failed: $($ex.Message)" -ForegroundColor Red
            return @{ Status = 0; Content = ""; Success = $false }
        }
    } catch {
        Write-Host "   💀 Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Status = 0; Content = ""; Success = $false }
    }
}

# Function to test internal endpoints via SSH
function Test-InternalEndpoint {
    param(
        [string]$Url,
        [string]$Description
    )
    
    Write-Host "`n🔍 Testing (SSH): $Description" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    
    try {
        # Test HTTP status via SSH
        $sshCommand = "ssh $SSHUser@$PiHost `"curl -s -o /dev/null -w '%{http_code}' $Url`""
        $statusResult = Invoke-Expression $sshCommand 2>$null
        
        if ($statusResult -and $statusResult -match '^\d+$') {
            $statusCode = [int]$statusResult
            
            if ($statusCode -eq 200) {
                Write-Host "   ✅ Status: $statusCode (Success)" -ForegroundColor Green
                
                # Get content via SSH
                $contentCommand = "ssh $SSHUser@$PiHost `"curl -s $Url`""
                $content = Invoke-Expression $contentCommand 2>$null
                
                if ($content -and $content.Length -gt 0) {
                    if ($content.Length -gt 200) {
                        Write-Host "   📄 Response: $($content.Substring(0, 200))..." -ForegroundColor White
                    } else {
                        Write-Host "   📄 Response: $content" -ForegroundColor White
                    }
                }
            } elseif ($statusCode -eq 404) {
                Write-Host "   ❌ Status: $statusCode (Not Found)" -ForegroundColor Red
            } elseif ($statusCode -eq 500) {
                Write-Host "   💥 Status: $statusCode (Server Error)" -ForegroundColor Red
            } else {
                Write-Host "   ⚠️  Status: $statusCode" -ForegroundColor Yellow
            }
            
            return @{
                Status = $statusCode
                Success = ($statusCode -eq 200)
            }
        } else {
            Write-Host "   💀 SSH Connection Failed" -ForegroundColor Red
            return @{ Status = 0; Success = $false }
        }
        
    } catch {
        Write-Host "   💀 SSH Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Status = 0; Success = $false }
    }
}

# Function to get container status
function Get-ContainerStatus {
    try {
        $sshCommand = "ssh $SSHUser@$PiHost `"docker ps --format 'table {{.Names}}\t{{.Status}}'`""
        $result = Invoke-Expression $sshCommand 2>$null
        return $result
    } catch {
        return "SSH connection failed: $($_.Exception.Message)"
    }
}

# Main execution
Write-Host "=" * 80 -ForegroundColor Blue
Write-Host "🚦 COMPREHENSIVE EXTERNAL API ENDPOINT TESTING" -ForegroundColor Blue
Write-Host "📅 Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')" -ForegroundColor Blue
Write-Host "=" * 80 -ForegroundColor Blue

# Define endpoints to test
$externalEndpoints = @(
    @{ Url = "https://$PiHost`:$ExternalPort/api/health/system"; Description = "External API System Health" },
    @{ Url = "https://$PiHost`:$ExternalPort/api/health/stats"; Description = "External API Stats" },
    @{ Url = "https://$PiHost`:$ExternalPort/api/vehicles/detections"; Description = "External Vehicle Detections" },
    @{ Url = "https://$PiHost`:$ExternalPort/api/weather/current"; Description = "External Current Weather" },
    @{ Url = "https://$PiHost`:$ExternalPort/api/events/recent"; Description = "External Recent Events" },
    @{ Url = "https://$PiHost`:$ExternalPort/api/analytics"; Description = "External Traffic Analytics" },
    @{ Url = "https://$PiHost`:$ExternalPort/api"; Description = "External API Root" },
    @{ Url = "https://$PiHost`:$ExternalPort/docs"; Description = "External Swagger UI" },
    @{ Url = "https://$PiHost`:$ExternalPort/swagger.json"; Description = "External Swagger JSON" }
)

$internalEndpoints = @(
    @{ Url = "http://localhost:$InternalPort/api/health/system"; Description = "Internal API System Health" },
    @{ Url = "http://localhost:$InternalPort/api/health/stats"; Description = "Internal API Stats" },
    @{ Url = "http://localhost:$InternalPort/api/vehicles/detections"; Description = "Internal Vehicle Detections" },
    @{ Url = "http://localhost:$InternalPort/api/weather/current"; Description = "Internal Current Weather" },
    @{ Url = "http://localhost:$InternalPort/api/events/recent"; Description = "Internal Recent Events" },
    @{ Url = "http://localhost:$InternalPort/api/analytics"; Description = "Internal Traffic Analytics" },
    @{ Url = "http://localhost:$InternalPort/api"; Description = "Internal API Root" },
    @{ Url = "http://localhost:$InternalPort/docs"; Description = "Internal Swagger UI" },
    @{ Url = "http://localhost:$InternalPort/swagger.json"; Description = "Internal Swagger JSON" },
    @{ Url = "http://localhost:$InternalPort/health"; Description = "Internal Basic Health" }
)

# Test external endpoints
Write-Host "`n🌐 TESTING EXTERNAL ENDPOINTS (Dashboard Access)" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Yellow

$externalResults = @()
foreach ($endpoint in $externalEndpoints) {
    $result = Test-ExternalEndpoint -Url $endpoint.Url -Description $endpoint.Description
    $externalResults += @{
        Url = $endpoint.Url
        Description = $endpoint.Description
        Result = $result
    }
}

# Test internal endpoints via SSH
Write-Host "`n🏠 TESTING INTERNAL ENDPOINTS (Pi localhost)" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Yellow

$internalResults = @()
foreach ($endpoint in $internalEndpoints) {
    $result = Test-InternalEndpoint -Url $endpoint.Url -Description $endpoint.Description
    $internalResults += @{
        Url = $endpoint.Url
        Description = $endpoint.Description
        Result = $result
    }
}

# Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Blue
Write-Host "📊 TEST SUMMARY" -ForegroundColor Blue
Write-Host "=" * 80 -ForegroundColor Blue

$externalWorking = $externalResults | Where-Object { $_.Result.Success }
$externalFailed = $externalResults | Where-Object { -not $_.Result.Success }
$internalWorking = $internalResults | Where-Object { $_.Result.Success }
$internalFailed = $internalResults | Where-Object { -not $_.Result.Success }

Write-Host "`n🌐 EXTERNAL ENDPOINTS (Dashboard Access):" -ForegroundColor Cyan
Write-Host "✅ Working: $($externalWorking.Count), ❌ Failed: $($externalFailed.Count)" -ForegroundColor White

if ($externalWorking.Count -gt 0) {
    Write-Host "   ✅ WORKING:" -ForegroundColor Green
    foreach ($item in $externalWorking) {
        Write-Host "      • $($item.Description)" -ForegroundColor Green
    }
}

if ($externalFailed.Count -gt 0) {
    Write-Host "   ❌ FAILED:" -ForegroundColor Red
    foreach ($item in $externalFailed) {
        Write-Host "      • $($item.Description) (Status: $($item.Result.Status))" -ForegroundColor Red
    }
}

Write-Host "`n🏠 INTERNAL ENDPOINTS (Pi localhost):" -ForegroundColor Cyan
Write-Host "✅ Working: $($internalWorking.Count), ❌ Failed: $($internalFailed.Count)" -ForegroundColor White

if ($internalWorking.Count -gt 0) {
    Write-Host "   ✅ WORKING:" -ForegroundColor Green
    foreach ($item in $internalWorking) {
        Write-Host "      • $($item.Description)" -ForegroundColor Green
    }
}

if ($internalFailed.Count -gt 0) {
    Write-Host "   ❌ FAILED:" -ForegroundColor Red
    foreach ($item in $internalFailed) {
        Write-Host "      • $($item.Description) (Status: $($item.Result.Status))" -ForegroundColor Red
    }
}

# Container status
Write-Host "`n🐳 CONTAINER STATUS:" -ForegroundColor Cyan
$containerStatus = Get-ContainerStatus
Write-Host $containerStatus -ForegroundColor White

# Final summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Blue
Write-Host "🏁 Testing completed." -ForegroundColor Blue
Write-Host "🌐 External: $($externalWorking.Count) working, $($externalFailed.Count) failed" -ForegroundColor White
Write-Host "🏠 Internal: $($internalWorking.Count) working, $($internalFailed.Count) failed" -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Blue

# Analysis and recommendations
if ($externalWorking.Count -gt 0) {
    Write-Host "`n✅ DASHBOARD READY: $($externalWorking.Count) external endpoints working" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  DASHBOARD ISSUE: No external endpoints accessible" -ForegroundColor Yellow
    if ($internalWorking.Count -gt 0) {
        Write-Host "   Internal endpoints work - likely nginx/SSL configuration issue" -ForegroundColor Yellow
    } else {
        Write-Host "   No internal endpoints work - API service may be down" -ForegroundColor Red
    }
}

Write-Host "`n📋 RECOMMENDATIONS:" -ForegroundColor Magenta
if ($externalFailed.Count -gt 0) {
    Write-Host "   • Check nginx proxy configuration for external access" -ForegroundColor White
    Write-Host "   • Verify SSL certificates are properly configured" -ForegroundColor White
    Write-Host "   • Ensure all Docker containers are healthy and running" -ForegroundColor White
}
if ($internalFailed.Count -gt 0) {
    Write-Host "   • Check Flask-RESTX API service is running on port $InternalPort" -ForegroundColor White
    Write-Host "   • Verify API prefix configuration is correct" -ForegroundColor White
}