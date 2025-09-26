# External API Endpoint Testing Script
# Tests all available endpoints at edge-traffic-monitoring.taild46447.ts.net
# PowerShell version - no additional dependencies required

param(
    [string]$BaseUrl = "https://edge-traffic-monitoring.taild46447.ts.net",
    [int]$TimeoutSeconds = 10,
    [switch]$Verbose
)

function Test-APIEndpoint {
    param(
        [string]$Path,
        [string]$Description,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    $url = "$BaseUrl$Path"
    
    Write-Host "`n🔍 Testing: $Description" -ForegroundColor Cyan
    Write-Host "   URL: $url" -ForegroundColor Gray
    Write-Host "   Method: $Method" -ForegroundColor Gray
    
    try {
        $requestParams = @{
            Uri = $url
            Method = $Method
            TimeoutSec = $TimeoutSeconds
            UseBasicParsing = $true
            SkipCertificateCheck = $true
        }
        
        if ($Headers.Count -gt 0) {
            $requestParams.Headers = $Headers
        }
        
        if ($null -ne $Body) {
            if ($Body -is [hashtable]) {
                $requestParams.Body = ($Body | ConvertTo-Json)
                $requestParams.ContentType = "application/json"
            } else {
                $requestParams.Body = $Body
            }
        }
        
        $response = Invoke-WebRequest @requestParams
        $status = $response.StatusCode
        $content = $response.Content
        
        switch ($status) {
            200 {
                Write-Host "   ✅ Status: $status (Success)" -ForegroundColor Green
                if ($content.Length -lt 500) {
                    Write-Host "   📄 Response: $content" -ForegroundColor Gray
                } else {
                    Write-Host "   📄 Response: $($content.Substring(0, 200))... (truncated)" -ForegroundColor Gray
                }
                
                # Try to parse as JSON
                try {
                    $jsonData = $content | ConvertFrom-Json
                    if ($jsonData -is [PSCustomObject]) {
                        $keys = ($jsonData | Get-Member -MemberType NoteProperty).Name -join ", "
                        Write-Host "   📊 JSON Keys: $keys" -ForegroundColor Gray
                    } elseif ($jsonData -is [array]) {
                        Write-Host "   📊 JSON: Array with $($jsonData.Count) items" -ForegroundColor Gray
                    }
                } catch {
                    # Not JSON, that's fine
                }
            }
            404 { Write-Host "   ❌ Status: $status (Not Found)" -ForegroundColor Red }
            500 { 
                Write-Host "   💥 Status: $status (Server Error)" -ForegroundColor Red
                Write-Host "   📄 Error: $($content.Substring(0, [Math]::Min(200, $content.Length)))" -ForegroundColor Gray
            }
            { $_ -in @(301, 302, 308) } {
                Write-Host "   🔄 Status: $status (Redirect)" -ForegroundColor Yellow
                $location = $response.Headers.Location
                if ($location) {
                    Write-Host "   📍 Location: $location" -ForegroundColor Gray
                }
            }
            403 { Write-Host "   🚫 Status: $status (Forbidden)" -ForegroundColor Red }
            default { 
                Write-Host "   ⚠️  Status: $status" -ForegroundColor Yellow
                if ($content -and $content.Length -gt 0) {
                    Write-Host "   📄 Response: $($content.Substring(0, [Math]::Min(200, $content.Length)))" -ForegroundColor Gray
                }
            }
        }
        
        return @{
            Url = $url
            Description = $Description
            Method = $Method
            Status = $status
            Success = ($status -eq 200)
            ResponseSize = $content.Length
            Headers = $response.Headers
        }
        
    } catch [System.Net.WebException] {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -match "timeout|timed out") {
            Write-Host "   ⏰ Timeout after $TimeoutSeconds seconds" -ForegroundColor Red
            $errorType = "timeout"
        } elseif ($errorMsg -match "SSL|certificate") {
            Write-Host "   🔒 SSL Error: $errorMsg" -ForegroundColor Red
            $errorType = "ssl_error"
        } else {
            Write-Host "   💀 Connection Failed: $errorMsg" -ForegroundColor Red
            $errorType = "connection_error"
        }
        
        return @{
            Url = $url
            Description = $Description
            Status = $errorType
            Success = $false
        }
    } catch {
        Write-Host "   💥 Unexpected Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            Url = $url
            Description = $Description
            Status = "error"
            Success = $false
        }
    }
}

function Main {
    Write-Host "=" * 90 -ForegroundColor Blue
    Write-Host "🌐 EXTERNAL API ENDPOINT TESTING" -ForegroundColor Blue
    Write-Host "🎯 Target: edge-traffic-monitoring.taild46447.ts.net" -ForegroundColor Blue
    Write-Host "📅 Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')" -ForegroundColor Blue
    Write-Host "=" * 90 -ForegroundColor Blue
    
    $results = @()
    
    # Define endpoints to test
    $endpoints = @(
        @{ Path = "/"; Description = "Root/Home Page"; Method = "GET" },
        @{ Path = "/health"; Description = "Basic Health Check"; Method = "GET" },
        @{ Path = "/docs"; Description = "Swagger UI Documentation"; Method = "GET" },
        @{ Path = "/docs/"; Description = "Swagger UI Documentation (trailing slash)"; Method = "GET" },
        @{ Path = "/swagger.json"; Description = "OpenAPI/Swagger Specification"; Method = "GET" },
        @{ Path = "/openapi.json"; Description = "Alternative OpenAPI Spec"; Method = "GET" },
        @{ Path = "/api"; Description = "API Root"; Method = "GET" },
        @{ Path = "/api/"; Description = "API Root (trailing slash)"; Method = "GET" },
        @{ Path = "/api/health/system"; Description = "Enhanced System Health"; Method = "GET" },
        @{ Path = "/api/health/stats"; Description = "System Statistics"; Method = "GET" },
        @{ Path = "/api/vehicles/detections"; Description = "Vehicle Detections"; Method = "GET" },
        @{ Path = "/api/vehicles/detections?seconds=30"; Description = "Vehicle Detections (30s)"; Method = "GET" },
        @{ Path = "/api/weather/current"; Description = "Current Weather"; Method = "GET" },
        @{ Path = "/api/weather"; Description = "Weather Data"; Method = "GET" },
        @{ Path = "/api/events/recent"; Description = "Recent Events"; Method = "GET" },
        @{ Path = "/api/analytics"; Description = "Traffic Analytics"; Method = "GET" },
        @{ Path = "/detections"; Description = "Direct Vehicle Detections"; Method = "GET" },
        @{ Path = "/weather"; Description = "Direct Weather"; Method = "GET" },
        @{ Path = "/tracks"; Description = "Vehicle Tracks"; Method = "GET" },
        @{ Path = "/speeds"; Description = "Speed Detections"; Method = "GET" },
        @{ Path = "/hello"; Description = "Hello Endpoint"; Method = "GET" }
    )
    
    # Test each endpoint
    foreach ($endpoint in $endpoints) {
        $result = Test-APIEndpoint -Path $endpoint.Path -Description $endpoint.Description -Method $endpoint.Method
        $results += $result
    }
    
    # CORS preflight test
    $corsHeaders = @{
        "Access-Control-Request-Method" = "GET"
        "Access-Control-Request-Headers" = "Content-Type"
        "Origin" = "https://gcu-merk.github.io"
    }
    $corsResult = Test-APIEndpoint -Path "/api/health/system" -Description "CORS Preflight Test" -Method "OPTIONS" -Headers $corsHeaders
    $results += $corsResult
    
    # Summary
    Write-Host "`n" + ("=" * 90) -ForegroundColor Blue
    Write-Host "📊 EXTERNAL API TEST SUMMARY" -ForegroundColor Blue
    Write-Host "=" * 90 -ForegroundColor Blue
    
    $workingEndpoints = $results | Where-Object { $_.Success -eq $true }
    $failedEndpoints = $results | Where-Object { $_.Success -ne $true }
    
    Write-Host "`n✅ WORKING ENDPOINTS ($($workingEndpoints.Count)):" -ForegroundColor Green
    foreach ($result in $workingEndpoints) {
        Write-Host "   • $($result.Description): $($result.Url) (Status: $($result.Status))" -ForegroundColor Green
    }
    
    Write-Host "`n❌ FAILED/UNAVAILABLE ENDPOINTS ($($failedEndpoints.Count)):" -ForegroundColor Red
    foreach ($result in $failedEndpoints) {
        Write-Host "   • $($result.Description): $($result.Url) (Status: $($result.Status))" -ForegroundColor Red
    }
    
    # Analysis
    if ($workingEndpoints.Count -gt 0) {
        Write-Host "`n📈 EXTERNAL ACCESS ANALYSIS:" -ForegroundColor Cyan
        Write-Host "   • Total endpoints tested: $($results.Count)" -ForegroundColor Gray
        $successRate = [math]::Round(($workingEndpoints.Count / $results.Count) * 100, 1)
        Write-Host "   • Success rate: $($workingEndpoints.Count)/$($results.Count) ($successRate%)" -ForegroundColor Gray
        
        $workingUrls = $workingEndpoints | ForEach-Object { $_.Url }
        if ($workingUrls -match "/health") {
            Write-Host "   • ✅ Health monitoring accessible externally" -ForegroundColor Green
        }
        if ($workingUrls -match "/api/") {
            Write-Host "   • ✅ REST API endpoints accessible externally" -ForegroundColor Green
        }
        if ($workingUrls -match "/docs") {
            Write-Host "   • ✅ API documentation accessible externally" -ForegroundColor Green
        }
        if ($workingUrls -match "swagger") {
            Write-Host "   • ✅ Swagger specification accessible externally" -ForegroundColor Green
        }
    }
    
    Write-Host "`n🔐 SECURITY CONSIDERATIONS:" -ForegroundColor Yellow
    Write-Host "   • Using HTTPS with Tailscale SSL certificates" -ForegroundColor Gray
    Write-Host "   • CORS configured for https://gcu-merk.github.io" -ForegroundColor Gray
    Write-Host "   • External access via Tailscale network (100.121.231.16)" -ForegroundColor Gray
    
    Write-Host "`n" + ("=" * 90) -ForegroundColor Blue
    Write-Host "🏁 External API testing completed." -ForegroundColor Blue
    Write-Host "🌐 Domain: edge-traffic-monitoring.taild46447.ts.net" -ForegroundColor Blue
    Write-Host "📡 Results: $($workingEndpoints.Count) working, $($failedEndpoints.Count) failed/unavailable" -ForegroundColor Blue
    Write-Host "=" * 90 -ForegroundColor Blue
    
    # Save results
    $resultsFile = "external_api_test_results.json"
    $outputData = @{
        "timestamp" = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
        "base_url" = $BaseUrl
        "total_tests" = $results.Count
        "successful_tests" = $workingEndpoints.Count
        "results" = $results
    }
    
    $outputData | ConvertTo-Json -Depth 10 | Out-File -FilePath $resultsFile -Encoding UTF8
    Write-Host "`n💾 Results saved to: $resultsFile" -ForegroundColor Cyan
    
    return $results
}

# Run the main function
Main