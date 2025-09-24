# HTTPS and Tailscale Integration Guide

## Overview

This document describes the HTTPS implementation for the Traffic Monitoring System using Tailscale certificates and Funnel for public access. This setup resolves mixed content security issues and enables secure API access from GitHub Pages.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Implementation Steps](#implementation-steps)
4. [Network Configuration](#network-configuration)
5. [Tailscale Funnel Setup](#tailscale-funnel-setup)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## Architecture Overview

### Before HTTPS Implementation

```text
GitHub Pages (HTTPS) → ❌ Mixed Content Error → Raspberry Pi API (HTTP)
```

### After HTTPS Implementation

```text
GitHub Pages (HTTPS) 
    ↓
Tailscale Funnel (Public Internet Gateway)
    ↓  
https://edge-traffic-monitoring.taild46447.ts.net/
    ↓
nginx-proxy (SSL Termination with Tailscale Certificate)
    ↓
traffic-monitor API (Port 5000)
```

## Prerequisites

- Raspberry Pi 5 with Tailscale installed
- Docker and Docker Compose
- GitHub Pages website deployment
- Tailscale account with MagicDNS enabled

## Implementation Steps

### 1. Enable MagicDNS

```bash
# Enable MagicDNS for proper hostname resolution
tailscale up --accept-dns
```

### 2. Generate Tailscale SSL Certificate

```bash
# Request Let's Encrypt certificate via Tailscale
sudo tailscale cert edge-traffic-monitoring.taild46447.ts.net

# Create SSL directory and move certificates
sudo mkdir -p /etc/nginx/ssl
sudo mv edge-traffic-monitoring.taild46447.ts.net.crt /etc/nginx/ssl/
sudo mv edge-traffic-monitoring.taild46447.ts.net.key /etc/nginx/ssl/
```

### 3. Configure Nginx Reverse Proxy

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server traffic-monitor:5000;
    }

    server {
        listen 80;
        server_name edge-traffic-monitoring.taild46447.ts.net 100.121.231.16;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name edge-traffic-monitoring.taild46447.ts.net 100.121.231.16;

        # Tailscale SSL certificate (trusted by browsers)
        ssl_certificate /etc/nginx/ssl/edge-traffic-monitoring.taild46447.ts.net.crt;
        ssl_certificate_key /etc/nginx/ssl/edge-traffic-monitoring.taild46447.ts.net.key;
        
        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://gcu-merk.github.io' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type' always;

        location / {
            # Handle preflight OPTIONS requests
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' 'https://gcu-merk.github.io';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type';
                add_header 'Content-Length' 0;
                add_header 'Content-Type' 'text/plain';
                return 204;
            }

            # Proxy to API
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. Update Docker Compose

Add nginx-proxy service to `docker-compose.yml`:

```yaml
  nginx-proxy:
    image: nginx:1.25-alpine
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      traffic-monitor:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Network Configuration

### Unified Network Architecture

All services use a single network: `app-network`

When deployed with `COMPOSE_PROJECT_NAME=traffic_monitoring`, this becomes:

- Network: `traffic_monitoring_app-network`

### Services on Network

1. `redis` - Data cache
2. `postgres` - Database
3. `traffic-monitor` - Main API service
4. `data-maintenance` - Data cleanup
5. `airport-weather` - Weather data service
6. `dht22-weather` - Local weather sensor
7. `vehicle-consolidator` - Data processing
8. `nginx-proxy` - HTTPS reverse proxy

## Tailscale Funnel Setup

### Purpose

Tailscale Funnel enables public internet access to the HTTPS API, allowing GitHub Pages to connect without being on the Tailscale network.

### Configuration

```bash
# Enable Funnel to proxy HTTPS requests to local API
sudo tailscale funnel --bg --https=443 http://127.0.0.1:5000

# Check status
sudo tailscale funnel status

# Expected output:
# https://edge-traffic-monitoring.taild46447.ts.net (Funnel on)
# |-- / proxy http://127.0.0.1:5000
```

### Benefits

- **Public Access**: API accessible from any internet connection
- **SSL Termination**: Tailscale handles SSL/TLS with valid certificates
- **No Port Forwarding**: No need to configure router/firewall
- **Automatic HTTPS**: All traffic encrypted end-to-end

## Website Configuration

### API URL Migration

Update website to use HTTPS Tailscale hostname:

```javascript
// Old (HTTP, caused mixed content errors)
const oldApiUrl = 'http://100.121.231.16:5000/api';

// New (HTTPS, secure)
const newApiUrl = 'https://edge-traffic-monitoring.taild46447.ts.net/api';
```

### Automatic Migration Code

```javascript
constructor() {
    // Check for old HTTP URL and update to HTTPS
    const storedUrl = localStorage.getItem('api-url');
    if (storedUrl && storedUrl.includes('http://100.121.231.16:5000')) {
        localStorage.setItem('api-url', 'https://edge-traffic-monitoring.taild46447.ts.net/api');
    }
    
    this.apiBaseUrl = localStorage.getItem('api-url') || 'https://edge-traffic-monitoring.taild46447.ts.net/api';
}
```

## Security Benefits

### SSL/TLS Encryption

- **Valid Certificate**: Let's Encrypt certificate via Tailscale
- **No Browser Warnings**: Trusted certificate authority
- **Modern TLS**: Supports TLSv1.2 and TLSv1.3
- **Perfect Forward Secrecy**: ECDHE cipher suites

### Access Control

- **CORS Configuration**: Restricts cross-origin requests
- **Tailscale Network**: API server protected by Tailscale mesh network
- **Funnel Control**: Public access controllable via Tailscale admin

## Troubleshooting

### Common Issues

#### 1. "Connection failed: Failed to fetch"

**Cause**: Tailscale Funnel not configured or SSL certificate issues  
**Solution**: 

```bash
# Reset and reconfigure Funnel
sudo tailscale funnel reset
sudo tailscale funnel --bg --https=443 http://127.0.0.1:5000
```

#### 2. "Mixed Content Error"

**Cause**: Website using HTTP API URL from HTTPS page  
**Solution**: Ensure website uses HTTPS API URL

#### 3. nginx "upstream not found"

**Cause**: Container network connectivity issue  
**Solution**: 

```bash
# Check containers are on same network
docker network ls
docker ps --format "table {{.Names}}\t{{.Networks}}"
```

#### 4. SSL Certificate Expired

**Cause**: Tailscale certificates auto-renew but may need refresh  
**Solution**: 

```bash
# Regenerate certificate
sudo tailscale cert edge-traffic-monitoring.taild46447.ts.net --force
sudo systemctl restart docker  # or docker compose restart nginx-proxy
```

### Verification Commands

```bash
# Test local HTTPS
curl -k https://127.0.0.1:443/api/health

# Test public HTTPS via Funnel
curl https://edge-traffic-monitoring.taild46447.ts.net/api/health

# Check nginx configuration
docker exec nginx-proxy nginx -t

# Verify SSL certificate
openssl x509 -in /etc/nginx/ssl/edge-traffic-monitoring.taild46447.ts.net.crt -text -noout
```

## Maintenance

### Certificate Renewal

Tailscale automatically renews Let's Encrypt certificates. No manual intervention required.

### Monitoring

```bash
# Check Funnel status
sudo tailscale funnel status

# Monitor nginx logs
docker logs nginx-proxy -f

# Check API health
curl https://edge-traffic-monitoring.taild46447.ts.net/api/health
```

### Backup Configuration

```bash
# Backup nginx configuration
cp nginx/nginx.conf nginx/nginx.conf.backup

# Backup SSL certificates (stored in Tailscale)
sudo tailscale cert --backup edge-traffic-monitoring.taild46447.ts.net
```

## Performance Considerations

### Latency

- **Direct Connection**: ~5ms (Tailscale mesh)
- **Via Funnel**: ~15-25ms (through Tailscale relay)

### Bandwidth

- **No Throttling**: Funnel supports full bandwidth
- **Caching**: nginx can cache static responses

### Scaling

- **Multiple Endpoints**: Can expose multiple services via Funnel
- **Load Balancing**: nginx can load balance to multiple backend instances

## Deployment Integration

The HTTPS configuration is integrated into the GitHub Actions deployment workflow:

1. **Validation**: Ensures `app-network` exists in docker-compose.yml
2. **Deployment**: Automatically deploys nginx-proxy service
3. **SSL Setup**: Certificates must be manually generated once per machine
4. **Funnel Config**: Persists across container restarts

## Endpoints

After implementation, the following endpoints are available:

- **Main Website**: https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/website/
- **API Base**: https://edge-traffic-monitoring.taild46447.ts.net/api/
- **Health Check**: https://edge-traffic-monitoring.taild46447.ts.net/api/health
- **Documentation**: https://edge-traffic-monitoring.taild46447.ts.net/docs/
- **Swagger JSON**: https://edge-traffic-monitoring.taild46447.ts.net/swagger.json

## References

- [Tailscale Funnel Documentation](https://tailscale.com/kb/1247/funnel-serve-use-cases)
- [Tailscale HTTPS Certificates](https://tailscale.com/kb/1153/enabling-https)
- [nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [MDN Mixed Content Guide](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)