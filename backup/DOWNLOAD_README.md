# Download Backup Script - README

## Quick Start

Run the script from PowerShell:

```powershell
cd C:\Code\CST_590_Computer_Science_Capstone_Project\backup
.\download-backup.ps1
```

## What It Does

1. ✅ Checks if SCP is available
2. ✅ Creates backup directory (`C:\RaspberryPi_Backups`)
3. ✅ Connects to your Raspberry Pi via Tailscale
4. ✅ Lists available backups on the Pi
5. ✅ Identifies the latest backup
6. ✅ Checks if already downloaded
7. ✅ Downloads the backup to your laptop
8. ✅ Shows download progress and statistics

## Requirements

### On Your Laptop (Windows)

**OpenSSH Client** - Usually pre-installed on Windows 10/11:

```powershell
# Check if installed
scp

# If not found, install via:
# Settings > Apps > Optional Features > Add "OpenSSH Client"
```

Or install manually:
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

**Tailscale** - Must be running and connected:
- Download from: https://tailscale.com/download
- Sign in and ensure connected to your tailnet

### On Your Raspberry Pi

**SSH Access** - Should already be enabled

You can either:
1. Use SSH key (no password needed)
2. Enter password when prompted

## Configuration

Edit the script if needed:

```powershell
# Raspberry Pi connection
$PI_HOST = "edge-traffic-monitoring.taild46447.ts.net"
$PI_USER = "pi"
$PI_BACKUP_PATH = "/mnt/samsung-ssd/backups"

# Local storage location
$LOCAL_BACKUP_DIR = "C:\RaspberryPi_Backups"
```

## First-Time Setup

### Option 1: Use SSH Key (Recommended)

Generate SSH key on your laptop:

```powershell
# Generate key (if you don't have one)
ssh-keygen -t ed25519

# Copy to Raspberry Pi
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@edge-traffic-monitoring.taild46447.ts.net "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Option 2: Use Password

Just run the script and enter password when prompted:
```powershell
.\download-backup.ps1
# Enter password: raspberry (or your custom password)
```

## Usage Examples

### Download Latest Backup

```powershell
.\download-backup.ps1
```

Output:
```
=============================================
  Raspberry Pi SD Card Backup Downloader
=============================================

✓ SCP is available
✓ Created backup directory

Source: pi@edge-traffic-monitoring.taild46447.ts.net:/mnt/samsung-ssd/backups
Destination: C:\RaspberryPi_Backups

Available backups (most recent last):
-rw-r--r-- 1 pi pi  98G Oct  5 02:35 pi5-sdcard-20251005_020000.img.gz

Latest backup: pi5-sdcard-20251005_020000.img.gz

Continue with download? (y/N): y

Starting download...
pi5-sdcard-20251005_020000.img.gz  45%  44GB   12.5MB/s   ETA 00:15:23

✓ Download completed successfully!

File: pi5-sdcard-20251005_020000.img.gz
Size: 98.24 GB
Duration: 2h 15m 43s
Location: C:\RaspberryPi_Backups\pi5-sdcard-20251005_020000.img.gz

All local backups:
Name                                    Size      LastWriteTime
----                                    ----      -------------
pi5-sdcard-20251005_020000.img.gz      98.24 GB  10/5/2025 4:50 PM
pi5-sdcard-20251004_020000.img.gz      97.82 GB  10/4/2025 9:20 AM

Total backup storage used: 196.06 GB
```

### Skip Already Downloaded

If the latest backup is already on your laptop:

```
⚠ Backup already exists locally: pi5-sdcard-20251005_020000.img.gz
Do you want to re-download? (y/N): n

Skipping download.
```

## Download Time Estimates

| Network Speed | 100 GB Backup | 150 GB Backup |
|--------------|---------------|---------------|
| 10 Mbps | ~22 hours | ~33 hours |
| 50 Mbps | ~4.5 hours | ~6.5 hours |
| 100 Mbps | ~2.2 hours | ~3.3 hours |
| 1 Gbps | ~13 minutes | ~20 minutes |

**Note**: Tailscale uses direct peer-to-peer connection when possible (fastest) or relays through their servers (slower).

## Storage Management

The script shows total storage used by backups:

```powershell
Total backup storage used: 294.18 GB
```

### Manual Cleanup

Delete old backups from your laptop:

```powershell
# View all backups
Get-ChildItem C:\RaspberryPi_Backups\pi5-sdcard-*.img.gz | Format-Table Name, Length, LastWriteTime

# Delete specific backup
Remove-Item C:\RaspberryPi_Backups\pi5-sdcard-20251001_020000.img.gz

# Keep only last 2 backups
Get-ChildItem C:\RaspberryPi_Backups\pi5-sdcard-*.img.gz | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -Skip 2 | 
    Remove-Item
```

## Troubleshooting

### "SCP not found"

Install OpenSSH Client:
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### "Failed to connect to Raspberry Pi"

Check:
1. Tailscale is running on both devices
2. Pi hostname is correct: `edge-traffic-monitoring.taild46447.ts.net`
3. SSH is enabled on Pi
4. Try manual connection: `ssh pi@edge-traffic-monitoring.taild46447.ts.net`

### "No backups found"

The backup service may not have run yet. Check on Pi:
```bash
ssh pi@edge-traffic-monitoring.taild46447.ts.net "ls -lh /mnt/samsung-ssd/backups/"
```

### "Permission denied"

Set up SSH key or ensure password is correct.

### Download Interrupted

The script removes partial downloads automatically. Just re-run:
```powershell
.\download-backup.ps1
```

## Restore Backup to SD Card

### Using Balena Etcher (Recommended)

1. Download: https://etcher.balena.io/
2. Launch Etcher
3. Select `.img.gz` file (no need to decompress)
4. Select target SD card
5. Click "Flash"

### Using Win32 Disk Imager

1. Decompress `.img.gz` file first
2. Launch Win32 Disk Imager as Administrator
3. Select `.img` file
4. Select SD card drive
5. Click "Write"

### Using Raspberry Pi Imager

1. Download: https://www.raspberrypi.com/software/
2. Launch Raspberry Pi Imager
3. Choose "Use custom" image
4. Select `.img.gz` file
5. Choose SD card
6. Click "Write"

⚠️ **WARNING**: Double-check the target drive! Writing will erase all data on the selected device.

## Automation

### Scheduled Download

Create a Windows Task Scheduler task:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly (Sunday morning)
4. Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-File "C:\Code\CST_590_Computer_Science_Capstone_Project\backup\download-backup.ps1"`
5. Run with highest privileges

## Security Notes

- Uses SSH/SCP over Tailscale (encrypted)
- Backups contain your entire system
- Store in secure location
- Consider encrypting backup directory
- Don't share backup files (contain passwords, keys)

## Best Practices

1. **Regular Schedule**: Download weekly or after major changes
2. **Verify Downloads**: Check file size matches source
3. **Test Restores**: Periodically verify backups can be restored
4. **Off-Site Storage**: Keep one backup on external drive at different location
5. **Monitor Space**: Ensure enough disk space for downloads

## License

Same as parent project.
