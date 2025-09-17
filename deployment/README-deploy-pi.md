# Raspberry Pi: Freeing port 5000 and pre-deploy checks

When deploying to the Raspberry Pi, the deployment scripts now attempt to automatically stop any containers or processes binding host port 5000 (the API port). If automatic cleanup fails, use the commands below on the Pi to diagnose and free the port manually.

## Check what is listening on port 5000

Use `ss` (preferred):

```bash
ss -tulpn | grep ':5000\b' || true
```

Fallback to `netstat`:

```bash
sudo netstat -tulpn | grep ':5000\b' || true
```

## If a Docker container is binding the port

List containers and identify the one with `5000` in the Ports column:

```bash
docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Ports}}'
```

Stop and remove the conflicting container by ID or name:

```bash
docker stop <CONTAINER_ID_OR_NAME>
docker rm <CONTAINER_ID_OR_NAME>
```

## If a non-container process is binding the port

Identify its PID from the `ss`/`netstat` output and kill it (use with caution):

```bash
# Example: sudo kill 12345
sudo kill <PID>
# Or be more forceful if needed
sudo kill -9 <PID>
```

## Re-run the deployment script

From the project root on the Pi:

```bash
./scripts/deploy-to-pi.sh
```

Notes:

- The deployment scripts now attempt to stop/remove containers that map host port 5000 and will attempt to kill non-container processes if a PID can be determined.
- If the PID cannot be extracted automatically, manual intervention is required.
- Stopping system services that intentionally provide other apps on port 5000 should be considered carefully.

## Quick verification checklist (after deployment)

1. Check container status:

```bash
cd /mnt/storage/traffic-monitor-deploy || true
docker compose ps || docker-compose ps
```

1. Confirm API responds:

```bash
curl -f http://localhost:5000/api/health
```

1. Confirm DHT22 service (if used) has access to /dev/gpiomem:

```bash
ls -l /dev/gpiomem || echo "/dev/gpiomem not present"
```

If the device is missing and you're on a real Raspberry Pi, enable GPIO in `raspi-config` and reboot. If running in a VM or non-Raspberry hardware, the DHT22 service will fail to start unless you mock the device or adjust the compose file.
