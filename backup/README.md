# SD Card Backup Service

Automated SD card backup service that creates compressed images of the Raspberry Pi's SD card and stores them on the SSD.

## Features

- **Scheduled Backups**: Automatically backs up SD card daily at 2 AM (configurable)
- **Compression**: Uses parallel gzip (pigz) for fast compression
- **Space Management**: Automatically removes old backups, keeping only the most recent
- **Safety Checks**: Verifies available space before starting backup
- **Progress Monitoring**: Real-time status updates during backup
- **Docker Integration**: Runs as a containerized service

## Quick Start

### 1. Build and Run with Docker Compose

Add to your `docker-compose.yml`:

```yaml
  sd-backup:
    build:
      context: ./backup
      dockerfile: Dockerfile
    container_name: sd-backup
    restart: unless-stopped
    privileged: true  # Required for block device access
    volumes:
      - /dev:/dev  # Access to block devices
      - ${SSD_MOUNT}/backups:/mnt/backups  # Backup storage on SSD
    environment:
      - BACKUP_DIR=/mnt/backups
      - SD_DEVICE=/dev/mmcblk0
      - MAX_BACKUPS=3
      - BACKUP_SCHEDULE=02:00  # 2 AM daily
      - COMPRESSION_LEVEL=6
      - RUN_ON_STARTUP=false
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 2. Start the Service

```bash
docker-compose up -d sd-backup
```

### 3. Monitor Logs

```bash
docker logs -f sd-backup
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | `/mnt/backups` | Directory to store backups |
| `SD_DEVICE` | `/dev/mmcblk0` | SD card block device |
| `MAX_BACKUPS` | `3` | Number of backups to keep |
| `BACKUP_SCHEDULE` | `02:00` | Daily backup time (24h format) |
| `COMPRESSION_LEVEL` | `6` | Compression level 1-9 (higher = smaller, slower) |
| `RUN_ON_STARTUP` | `false` | Run backup immediately on service start |

## Manual Backup

Trigger a backup manually:

```bash
# Enter the container
docker exec -it sd-backup bash

# Run backup script
python sd_card_backup.py
```

Or trigger from outside:

```bash
docker exec sd-backup python sd_card_backup.py
```

## Backup Process

1. **Space Check**: Verifies sufficient space on SSD (needs ~1.5x SD card size)
2. **Image Creation**: Uses `dd` to read entire SD card
3. **Compression**: Parallel compression with `pigz` for speed
4. **Storage**: Saves compressed image to SSD with timestamp
5. **Cleanup**: Removes old backups beyond `MAX_BACKUPS` limit

## Backup Files

Backups are named with timestamps:
```
pi5-sdcard-20251005_020000.img.gz
pi5-sdcard-20251006_020000.img.gz
pi5-sdcard-20251007_020000.img.gz
```

## Restore from Backup

To restore from a backup (on another machine):

```bash
# Decompress and write to SD card
gunzip -c pi5-sdcard-20251005_020000.img.gz | sudo dd of=/dev/sdX bs=4M status=progress

# Replace /dev/sdX with your SD card device (check with lsblk)
```

⚠️ **WARNING**: Double-check the device name! `dd` will overwrite the target device.

## Performance

- **Backup Time**: 30-60 minutes for 256GB SD card (depends on data)
- **Compression Ratio**: ~40-60% size reduction
- **CPU Impact**: Low (scheduled during off-peak hours)
- **Disk I/O**: Moderate (reads entire SD card)

## Disk Space Requirements

For a 256GB SD card:
- **Uncompressed**: 256 GB
- **Compressed**: 100-150 GB (typical)
- **Required Free Space**: 1.5x compressed size for safety

With 3 backups retained, expect to use ~450 GB on your SSD.

## Scheduling Options

Change backup frequency by modifying `BACKUP_SCHEDULE`:

```yaml
# Daily at 2 AM (default)
BACKUP_SCHEDULE=02:00

# Daily at 3:30 AM
BACKUP_SCHEDULE=03:30

# For custom schedules, modify sd_card_backup.py
```

## Troubleshooting

### "SD card device not found"
- Verify device path: `ls -l /dev/mmcblk*`
- Update `SD_DEVICE` environment variable

### "Insufficient space"
- Check available space: `df -h /mnt/backups`
- Reduce `MAX_BACKUPS` or add more storage
- Increase `COMPRESSION_LEVEL` (slower but smaller)

### "Permission denied"
- Ensure container runs with `privileged: true`
- Container must run as root for block device access

### Backup is slow
- Reduce `COMPRESSION_LEVEL` (e.g., 3 instead of 6)
- Ensure SSD is healthy (check SMART data)
- Monitor I/O: `docker stats sd-backup`

## Security Considerations

- Container runs as **root** (required for block device access)
- Container has **privileged** access (required for `/dev` access)
- Backups contain **entire system** including sensitive data
- Secure backup directory permissions
- Consider encrypting backups for sensitive deployments

## Integration with Monitoring

Add health check to docker-compose:

```yaml
  sd-backup:
    # ... other config ...
    healthcheck:
      test: ["CMD", "test", "-f", "/mnt/backups/pi5-sdcard-*.img.gz"]
      interval: 24h
      timeout: 10s
      retries: 1
```

## Best Practices

1. **Test Restores**: Periodically verify backups can be restored
2. **Off-site Copies**: Copy backups to remote storage for disaster recovery
3. **Monitor Space**: Watch SSD usage to prevent backup failures
4. **Schedule Wisely**: Run during low-traffic periods (e.g., 2-4 AM)
5. **Document Procedure**: Keep restore instructions accessible

## Future Enhancements

Potential improvements:
- [ ] Incremental backups to save space
- [ ] Backup verification (checksum)
- [ ] Remote upload to cloud storage
- [ ] Email/webhook notifications
- [ ] Backup encryption
- [ ] Web UI for backup management

## License

Same as parent project.
