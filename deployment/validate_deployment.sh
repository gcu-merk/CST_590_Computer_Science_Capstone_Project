#!/usr/bin/env bash
# Deployment validation script intended to be executed on the Raspberry Pi
# This script performs the host-side validation previously in the GitHub Actions YAML.

set -euo pipefail

echo "🔍 Starting host-side deployment validation"

# Detect Docker Compose command to use (prefer `docker compose` plugin)
if docker compose version >/dev/null 2>&1; then
  DC='docker compose'
elif command -v docker-compose >/dev/null 2>&1; then
  DC='docker-compose'
else
  echo "❌ Neither 'docker compose' nor 'docker-compose' found on host"
  exit 1
fi

DEBUG_DIR_BASE="/mnt/storage/deployment-staging/deployment-debug-$(date +%Y%m%dT%H%M%S)"

# Failure handler collects diagnostics into a timestamped debug directory under staging
collect_failure_debug() {
  echo "Collecting debug information into ${DEBUG_DIR_BASE}..."
  mkdir -p "${DEBUG_DIR_BASE}" || true
  # Save docker ps and docker info
  ${DC} ps --all > "${DEBUG_DIR_BASE}/docker_ps.txt" 2>&1 || true
  docker info > "${DEBUG_DIR_BASE}/docker_info.txt" 2>&1 || true
  # Capture inspect and logs for all containers in compose project
  CONTAINERS=$( ${DC} ps -q || true )
  if [ -z "${CONTAINERS}" ]; then
    echo "No containers found to inspect" > "${DEBUG_DIR_BASE}/note.txt"
  else
    for cid in ${CONTAINERS}; do
      name=$(docker inspect --format='{{.Name}}' "${cid}" 2>/dev/null | sed 's|/||') || name="${cid}"
      echo "Collecting for container: ${name} (${cid})"
      docker inspect "${cid}" > "${DEBUG_DIR_BASE}/${name}-${cid}-inspect.json" 2>&1 || true
      docker logs "${cid}" --tail=500 > "${DEBUG_DIR_BASE}/${name}-${cid}-logs.txt" 2>&1 || true
    done
  fi
  echo "Debug collection complete: ${DEBUG_DIR_BASE}"
}

# Retry helper: run command up to max attempts with exponential backoff
retry() {
  local max=${RETRY_MAX:-5}
  local n=0
  local delay=${RETRY_DELAY:-2}
  until [ $n -ge $max ]; do
    "$@" && return 0
    n=$((n+1))
    echo "⏳ Retry $n/$max for: $*"
    sleep $delay
    delay=$((delay * 2))
  done
  return 1
}

echo "Checking host systemd service: host-camera-capture"
if ! systemctl is-active --quiet host-camera-capture; then
  echo "❌ Host camera service not running"
  systemctl status host-camera-capture --no-pager || true
  exit 1
fi
echo "✅ Host camera service is running"

# Ensure we're in staging directory
if [ ! -d "/mnt/storage/deployment-staging" ]; then
  echo "❌ Staging directory /mnt/storage/deployment-staging not found"
  exit 1
fi
cd /mnt/storage/deployment-staging

echo "🔍 Checking container status (showing all containers)"
# Show containers for debugging
${DC} ps --all || true

echo "Waiting for containers to reach 'Up' state (with retries)"
if ! retry sh -c "${DC} ps | grep -q 'Up'"; then
  echo "❌ Containers not running properly"
  ${DC} ps --all || true
  collect_failure_debug
  exit 1
fi
echo "✅ At least one container is Up"

echo "🔍 Checking Redis service (PING)"
if ! retry sh -c "${DC} exec -T redis redis-cli ping | grep -q PONG"; then
  echo "❌ Redis service not responding"
  ${DC} logs redis --tail=200 || true
  collect_failure_debug
  exit 1
fi
echo "✅ Redis service is responding"

echo "🔍 Checking traffic-monitor for Redis connectivity messages"
sleep 5
if ! ${DC} logs traffic-monitor | grep -q "Connected to Redis\|Redis"; then
  echo "⚠️ No Redis connection logs found in traffic-monitor (may still be connecting)"
else
  echo "✅ Traffic monitor shows Redis connectivity logs"
fi

echo "🔍 Validating weather service containers are running"
for svc in dht22-weather airport-weather; do
  attempts=0
  until [ $attempts -ge 10 ]; do
    if ${DC} ps --services --filter "status=running" | grep -q "^$svc$"; then
      echo "✅ $svc is running"
      break
    fi
    attempts=$((attempts+1))
    echo "⏳ Waiting for $svc to start (attempt: $attempts)..."
    sleep 3
  done
  if [ $attempts -ge 10 ]; then
    echo "⚠️ $svc did not reach running state after multiple attempts"
    ${DC} logs $svc --tail=50 || true
  fi
done

echo "🔍 Validating weather data keys in Redis"
check_redis_key() {
  local key="$1"
  local attempt=0
  local max=10
  while [ $attempt -lt $max ]; do
    if ${DC} exec -T redis redis-cli GET "$key" 2>/dev/null | grep -q .; then
      echo "✅ Redis key '$key' has data"
      return 0
    fi
    attempt=$((attempt+1))
    echo "⏳ Waiting for Redis key '$key' (attempt: $attempt/$max)..."
    sleep 3
  done
  echo "⚠️ Redis key '$key' was not populated after $max attempts"
  return 1
}

if ! check_redis_key "weather:dht22:latest"; then
  echo "⚠️ DHT22 weather data not available in Redis"
  DHT_MISSING=1
else
  DHT_MISSING=0
fi
if ! check_redis_key "weather:airport:latest"; then
  echo "⚠️ Airport weather data not available in Redis"
  AIRPORT_MISSING=1
else
  AIRPORT_MISSING=0
fi
if [ "${DHT_MISSING}" -eq 1 ] && [ "${AIRPORT_MISSING}" -eq 1 ]; then
  echo "⚠️ Both weather Redis keys missing; collecting debug info"
  collect_failure_debug
fi

echo "🔍 Testing API health endpoint with retries"
if ! retry sh -c "curl -f -s http://localhost:5000/api/health >/dev/null"; then
  echo "⚠️ API not responding after retries (may need more time)"
  collect_failure_debug
else
  echo "✅ API is responding"
fi

echo "🎉 Host-side deployment validation completed"

exit 0
