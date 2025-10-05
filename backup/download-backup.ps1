# SD Card Backup Download Script for Windows
# 
# This script downloads the latest SD card backup from your Raspberry Pi to your laptop
# Uses SCP over Tailscale for secure transfer
#
# Usage: .\download-backup.ps1

# Configuration
$PI_HOST = "edge-traffic-monitoring.taild46447.ts.net"
$PI_USER = "pi"
$PI_BACKUP_PATH = "/mnt/samsung-ssd/backups"
$LOCAL_BACKUP_DIR = "C:\RaspberryPi_Backups"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Raspberry Pi SD Card Backup Downloader" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if SCP is available
try {
    $scpVersion = scp 2>&1
    if ($LASTEXITCODE -eq 0 -or $scpVersion -match "usage") {
        Write-ColorOutput Green "✓ SCP is available"
    }
} catch {
    Write-ColorOutput Red "✗ SCP not found. Please install OpenSSH Client."
    Write-Host "To install: Settings > Apps > Optional Features > Add OpenSSH Client"
    exit 1
}

# Create local backup directory if it doesn't exist
if (-not (Test-Path $LOCAL_BACKUP_DIR)) {
    Write-Host "Creating backup directory: $LOCAL_BACKUP_DIR"
    New-Item -ItemType Directory -Path $LOCAL_BACKUP_DIR | Out-Null
    Write-ColorOutput Green "✓ Created backup directory"
}

Write-Host ""
Write-Host "Source: $PI_USER@$PI_HOST`:$PI_BACKUP_PATH" -ForegroundColor Yellow
Write-Host "Destination: $LOCAL_BACKUP_DIR" -ForegroundColor Yellow
Write-Host ""

# List available backups on Pi
Write-Host "Checking available backups on Raspberry Pi..." -ForegroundColor Cyan
$availableBackups = ssh "$PI_USER@$PI_HOST" "ls -lh $PI_BACKUP_PATH/pi5-sdcard-*.img.gz 2>/dev/null | tail -5"

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "✗ Failed to connect to Raspberry Pi"
    Write-Host "Please check:"
    Write-Host "  1. Tailscale is running on both devices"
    Write-Host "  2. SSH key is set up or password is available"
    Write-Host "  3. Backup directory exists on Pi"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($availableBackups)) {
    Write-ColorOutput Red "✗ No backups found on Raspberry Pi"
    Write-Host "The backup service may not have run yet."
    exit 1
}

Write-Host ""
Write-Host "Available backups (most recent last):" -ForegroundColor Green
Write-Host $availableBackups
Write-Host ""

# Get the latest backup filename
$latestBackup = ssh "$PI_USER@$PI_HOST" "ls -t $PI_BACKUP_PATH/pi5-sdcard-*.img.gz | head -1"
$backupFilename = Split-Path $latestBackup -Leaf

Write-Host "Latest backup: $backupFilename" -ForegroundColor Green
Write-Host ""

# Check if backup already exists locally
$localBackupPath = Join-Path $LOCAL_BACKUP_DIR $backupFilename
if (Test-Path $localBackupPath) {
    Write-ColorOutput Yellow "⚠ Backup already exists locally: $backupFilename"
    $response = Read-Host "Do you want to re-download? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Skipping download."
        Write-Host ""
        Write-Host "Local backups:" -ForegroundColor Cyan
        Get-ChildItem $LOCAL_BACKUP_DIR -Filter "pi5-sdcard-*.img.gz" | 
            Sort-Object LastWriteTime -Descending |
            Format-Table Name, @{Label="Size";Expression={"{0:N2} GB" -f ($_.Length/1GB)}}, LastWriteTime -AutoSize
        exit 0
    }
}

# Ask for confirmation before downloading
Write-Host "This will download the backup file (may be 50-150 GB)." -ForegroundColor Yellow
Write-Host "Download time depends on your network speed." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue with download? (y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Download cancelled."
    exit 0
}

# Download the backup
Write-Host ""
Write-Host "Starting download..." -ForegroundColor Cyan
Write-Host "Source: $PI_USER@$PI_HOST`:$latestBackup" -ForegroundColor Gray
Write-Host "Destination: $localBackupPath" -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

# Use SCP to download the backup
scp "$PI_USER@$PI_HOST`:$latestBackup" "$localBackupPath"

if ($LASTEXITCODE -eq 0) {
    $endTime = Get-Date
    $duration = $endTime - $startTime
    $fileSize = (Get-Item $localBackupPath).Length / 1GB
    
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-ColorOutput Green "✓ Download completed successfully!"
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "File: $backupFilename"
    Write-Host "Size: $("{0:N2}" -f $fileSize) GB"
    Write-Host "Duration: $($duration.Hours)h $($duration.Minutes)m $($duration.Seconds)s"
    Write-Host "Location: $localBackupPath"
    Write-Host ""
    
    # Show all local backups
    Write-Host "All local backups:" -ForegroundColor Cyan
    Get-ChildItem $LOCAL_BACKUP_DIR -Filter "pi5-sdcard-*.img.gz" | 
        Sort-Object LastWriteTime -Descending |
        Format-Table Name, @{Label="Size";Expression={"{0:N2} GB" -f ($_.Length/1GB)}}, LastWriteTime -AutoSize
    
    # Calculate total space used
    $totalSize = (Get-ChildItem $LOCAL_BACKUP_DIR -Filter "pi5-sdcard-*.img.gz" | 
        Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "Total backup storage used: $("{0:N2}" -f $totalSize) GB" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "To restore this backup to an SD card:" -ForegroundColor Cyan
    Write-Host "  1. Use balenaEtcher, Raspberry Pi Imager, or Win32DiskImager" -ForegroundColor Gray
    Write-Host "  2. Select the .img.gz file (decompress first if needed)" -ForegroundColor Gray
    Write-Host "  3. Choose your SD card device" -ForegroundColor Gray
    Write-Host "  4. Write the image" -ForegroundColor Gray
    
} else {
    Write-Host ""
    Write-ColorOutput Red "✗ Download failed!"
    Write-Host "Please check your network connection and try again."
    
    # Clean up partial download
    if (Test-Path $localBackupPath) {
        Write-Host "Removing partial download..."
        Remove-Item $localBackupPath -Force
    }
    exit 1
}
