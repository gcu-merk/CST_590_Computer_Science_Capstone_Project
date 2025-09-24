# PowerShell script to deploy HTTPS configuration
Write-Host "🚀 Preparing HTTPS deployment for Raspberry Pi..." -ForegroundColor Green

# Check if we have the required files
$requiredFiles = @("nginx/nginx.conf", "setup-https.sh", "docker-compose.yml")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Missing required files:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Instructions for manual deployment
Write-Host ""
Write-Host "📋 Manual Deployment Instructions:" -ForegroundColor Yellow
Write-Host "Please run these commands on your Raspberry Pi:" -ForegroundColor White
Write-Host ""

# Show the Pi's hostname
$hostname = "edge-traffic-monitoring.taild46447.ts.net"
Write-Host "🏠 Pi Hostname: $hostname" -ForegroundColor Cyan

Write-Host ""
Write-Host "1️⃣ Generate Tailscale SSL certificate:" -ForegroundColor Yellow
Write-Host "   tailscale cert $hostname" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣ Create SSL directory and move certificates:" -ForegroundColor Yellow
Write-Host "   sudo mkdir -p /etc/nginx/ssl" -ForegroundColor White
Write-Host "   sudo mv $hostname.crt /etc/nginx/ssl/" -ForegroundColor White
Write-Host "   sudo mv $hostname.key /etc/nginx/ssl/" -ForegroundColor White
Write-Host ""

Write-Host "3️⃣ Update docker-compose.yml and nginx configuration:" -ForegroundColor Yellow
Write-Host "   # Copy the new docker-compose.yml to your Pi" -ForegroundColor White
Write-Host "   # Copy the nginx/ directory to your Pi" -ForegroundColor White
Write-Host ""

Write-Host "4️⃣ Deploy nginx proxy:" -ForegroundColor Yellow
Write-Host "   docker compose up -d nginx-proxy" -ForegroundColor White
Write-Host ""

Write-Host "5️⃣ Test HTTPS connectivity:" -ForegroundColor Yellow
Write-Host "   curl https://$hostname/api/health" -ForegroundColor White
Write-Host ""

Write-Host "🌐 Once deployed, update your website to use:" -ForegroundColor Green
Write-Host "   https://$hostname" -ForegroundColor Cyan

# Also show current file contents for reference
Write-Host ""
Write-Host "📄 Current configuration summary:" -ForegroundColor Yellow
Write-Host "   - nginx.conf: Configured for $hostname" -ForegroundColor White
Write-Host "   - docker-compose.yml: nginx-proxy service added" -ForegroundColor White
Write-Host "   - SSL certificates: Will be at /etc/nginx/ssl/" -ForegroundColor White