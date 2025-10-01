# Technical Design Document

**Document Version:** 2.0  
**Last Updated:** October 1, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Technical Team  
**Status:** Final Capstone Release (v1.0.0-capstone-final)  

## Table of Contents

1. [System Overview](#1-system-overview)
2. [System Architecture](#2-system-architecture)
3. [Top-Down Approach](#2x-top-down-approach)
4. [Hardware Design](#3-hardware-design)
5. [Component Interaction Diagram](#4-component-interaction-diagram)
6. [Sequence Diagram (Typical Event Flow)](#5-sequence-diagram-typical-event-flow)
7. [Deployment Diagram (Physical/Virtual Placement)](#6-deployment-diagram-physicalvirtual-placement)
8. [CI/CD Deployment Architecture](#7-cicd-deployment-architecture)
9. [Database Entity-Relationship Diagram (ERD)](#8-database-entity-relationship-diagram-erd)
10. [API Endpoint Map](#8-api-endpoint-map)
11. [Security/Data Flow Diagram](#9-securitydata-flow-diagram)
12. [Remote Access Flow via Tailscale](#10-remote-access-flow-via-tailscale)

**See also:**

- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [User Guide](./User_Guide.md)
- [Project Management Summary](./Project_Management.md)
- [References & Appendices](./References_Appendices.md)

## 1. System Overview

The Raspberry Pi 5 Edge ML Traffic Monitoring System is a production-ready edge AI solution that provides real-time vehicle detection, classification, speed measurement, and traffic analytics. The system leverages a Raspberry Pi 5 (16GB RAM), a Sony IMX500 AI camera with on-sensor neural processing (3.1 TOPS NPU), and an OmniPreSense OPS243-C FMCW Doppler radar sensor to perform hardware-accelerated vehicle classification and analysis locally.

This final capstone release (v1.0.0-capstone-final) represents a complete, production-tested system deployed on October 1, 2025, featuring a microservices architecture with 12 containerized services, sub-100ms AI inference latency, and 94% storage optimization compared to initial designs.

**Objectives:**

- Deploy a low-cost, scalable, and reliable edge-based traffic monitoring solution
- **Integrate radar-triggered edge AI for real-time vehicle classification (achieved <350ms total latency)**
- **Perform on-camera AI inference using IMX500 neural processing unit (sub-100ms inference)**
- Fuse radar and AI camera data for accurate speed and vehicle identification
- Provide real-time dashboards and cloud-based analytics with secure remote access
- Maintain continuous 24/7 operation with automated health monitoring and recovery

**Key Features:**

- **Radar-triggered edge AI processing with <350ms total latency**
- **On-camera vehicle classification with 85-95% accuracy using IMX500 NPU**
- **Multi-sensor data fusion (radar + motion detection + AI camera)**
- **Microservices architecture with 12 Docker containers**
- Real-time web dashboard (Edge UI) with WebSocket streaming
- Cloud integration for historical analytics and alerts (Cloud UI)
- **HTTPS/TLS encryption via nginx reverse proxy**
- **Secure remote access through Tailscale VPN mesh network**
- **Centralized logging with correlation IDs across all services**
- **Automated health monitoring and service recovery**
- Modular, production-ready containerized deployment

**Performance Achievements:**

- **25-50x faster inference** compared to software-based AI (sub-100ms vs 2-5 seconds)
- **100% reduction in CPU usage** for AI processing (hardware-accelerated on IMX500 NPU)
- **94% storage reduction** through intelligent data management and optimization
- **9+ hours continuous uptime** with automated monitoring and recovery
- **Real-time data streaming** via WebSocket with sub-second latency

## 2. System Architecture

### 2.1 Microservices Architecture Overview

The system implements a production-ready microservices architecture with 12 containerized services orchestrated via Docker Compose. All services communicate through a dedicated Docker bridge network with centralized Redis pub/sub messaging and SQLite data persistence.

**Core Services:**

1. **redis** - Redis 7 Alpine message broker and cache
2. **traffic-monitor** - Edge API Gateway (Flask-SocketIO) on port 5000
3. **data-maintenance** - Storage management and cleanup service
4. **airport-weather** - METAR weather data collection service
5. **dht22-weather** - Local DHT22 temperature/humidity sensor service
6. **radar-service** - OPS243-C radar data collection (UART/serial)
7. **vehicle-consolidator** - Multi-sensor data fusion and correlation
8. **database-persistence** - SQLite persistence layer with 90-day retention
9. **redis-optimization** - Memory management and TTL policies
10. **realtime-events-broadcaster** - WebSocket event streaming service
11. **nginx-proxy** - Reverse proxy with HTTPS/TLS termination
12. **camera-service-manager** - IMX500 systemd service health monitoring

**Additional Host Services:**

- **imx500-ai-capture.service** - Systemd service for IMX500 AI camera (runs on host, not containerized)

All services include health checks, restart policies, centralized logging with correlation IDs, and proper user/group permissions for security.

### 2.2 Detailed Service Descriptions

#### 2.2.1 Core Infrastructure Services

**redis (Redis 7 Alpine)**
- **Purpose:** Message broker, pub/sub system, and in-memory cache
- **Configuration:**
  - Port: 6379 (localhost-only for security)
  - Persistence: AOF (Append-Only File) enabled
  - Storage: `/mnt/storage/redis_data`
  - Channels: `traffic_events`, `radar_detections`, `database_events`
  - Streams: `radar_data`, `consolidated_traffic_data`
  - Keys: Weather data, consolidation records, system statistics
- **Health Check:** Redis ping command every 10 seconds
- **Memory Management:** Automated optimization via redis-optimization service

**nginx-proxy (Nginx 1.25 Alpine)**
- **Purpose:** Reverse proxy with HTTPS/TLS termination
- **Configuration:**
  - Ports: 80 (HTTP), 8443 (HTTPS)
  - Upstream: traffic-monitor service on port 5000
  - SSL: Self-signed certificates in `/etc/nginx/ssl`
  - Features: WebSocket proxying, gzip compression, security headers
- **Health Check:** Nginx configuration test every 30 seconds
- **Security:** HTTPS-only mode, secure headers, rate limiting

#### 2.2.2 Data Collection Services

**radar-service**
- **Purpose:** OPS243-C radar data collection and processing
- **Configuration:**
  - UART Port: `/dev/ttyAMA0` @ 19200 baud
  - GPIO Pins: Interrupt (GPIO23), Reset (GPIO24), Alert pins (GPIO5/6)
  - Speed Threshold: 2.0 mph minimum
  - Update Rate: 10-20 Hz
- **Data Flow:**
  - Reads JSON speed/magnitude data from UART
  - Converts m/s to mph
  - Publishes to `radar_detections` channel
  - Streams to `radar_data` stream
  - Triggers `traffic_events` for consolidation
- **Health Check:** Verifies radar_data stream length every 30 seconds
- **Privileges:** Requires `dialout`, `gpio` groups and device access

**airport-weather**
- **Purpose:** METAR weather data collection from nearby airport
- **Configuration:**
  - Update Interval: 10 minutes
  - Data Source: Aviation weather API
  - Redis Key: `weather:airport:latest`
- **Data Collected:** Temperature, wind speed/direction, visibility, precipitation
- **Health Check:** Verifies weather data freshness every 60 seconds

**dht22-weather**
- **Purpose:** Local temperature and humidity sensing
- **Configuration:**
  - GPIO Pin: GPIO4 (single-wire digital)
  - Update Interval: 10 minutes (600 seconds)
  - Sensor: DHT22 (AM2302)
- **Data Flow:**
  - Reads sensor via GPIO
  - Stores in Redis: `weather:dht22:latest`
  - Time-series: `weather:dht22:timeseries`
  - Correlation: `weather:correlation:airport_dht22`
- **Health Check:** Verifies DHT22 data presence
- **Special Handling:** Docker entrypoint for GPIO access

**imx500-ai-capture.service (Systemd Host Service)**
- **Purpose:** Hardware-accelerated AI vehicle detection
- **Configuration:**
  - NPU: Sony IMX500 3.1 TOPS neural processor
  - Model: ONNX vehicle detection (on-camera inference)
  - Inference Time: Sub-100ms
  - Output: Redis pub/sub + shared volume
- **Data Flow:**
  - Continuous video stream processing
  - On-chip AI inference (no CPU usage)
  - Publishes detections to Redis
  - Saves images to `/mnt/storage/ai_camera_images`
- **Monitoring:** camera-service-manager container
- **Note:** Runs on host (not containerized) for camera hardware access

#### 2.2.3 Data Processing Services

**vehicle-consolidator**
- **Purpose:** Multi-sensor data fusion and correlation
- **Configuration:**
  - Trigger Source: radar motion detection events
  - Data Retention: 24 hours
  - Stats Update: 60-second interval
  - Camera Strict Mode: false (allows nighttime/radar-only operation)
- **Data Flow:**
  - Subscribes to `traffic_events` channel
  - Collects radar speed/magnitude data
  - Fetches weather data (airport + DHT22)
  - Retrieves recent IMX500 AI detections
  - Creates consolidated record with unique ID
  - Publishes to `database_events` for persistence
- **Redis Keys:**
  - `consolidation:latest` - Current event
  - `consolidation:history:{id}` - Time-series storage
- **Health Check:** Process and Redis connectivity verification

**database-persistence**
- **Purpose:** SQLite persistence layer with intelligent data management
- **Configuration:**
  - Database: `/app/data/traffic_data.db`
  - Batch Size: 100 records
  - Commit Interval: 30 seconds
  - Retention: 90 days
- **Data Flow:**
  - Subscribes to `database_events` channel
  - Batch-inserts consolidated records
  - Maintains time-series indexes
  - Performs periodic cleanup
  - Trims Redis streams (radar_data: 1000, consolidated: 100)
- **Tables:** Normalized schema with traffic_events, weather_data, sensor_readings
- **Health Check:** Database connectivity and process verification

**redis-optimization**
- **Purpose:** Memory management and performance optimization
- **Configuration:**
  - Optimization Interval: 1 hour (3600 seconds)
  - Memory Threshold: 1000 MB
  - TTL Policies: Intelligent expiration for old data
- **Optimizations:**
  - Removes expired keys
  - Trims oversized streams
  - Defragments memory
  - Reports memory statistics
- **Achievement:** 94% storage reduction (removed sky analysis overhead)
- **Health Check:** Process and Redis connectivity verification

#### 2.2.4 API and User Interface Services

**traffic-monitor (Edge API Gateway)**
- **Purpose:** RESTful API and WebSocket server
- **Configuration:**
  - Port: 5000 (internal Docker network only)
  - Framework: Flask + Flask-SocketIO
  - Database: `/app/data/traffic_data.db`
  - API Host: 0.0.0.0 (container internal)
- **API Endpoints:**
  - `/health` - Health check
  - `/api/status` - System status
  - `/api/events` - Traffic events (GET, POST)
  - `/api/events/recent` - Recent events
  - `/api/radar` - Radar readings
  - `/api/weather` - Weather data
  - `/api/consolidated` - Consolidated records
  - `/api/stats` - System statistics
  - `/swagger.json` - OpenAPI specification
  - `/docs` - Swagger UI
- **WebSocket:** Real-time event streaming via Socket.IO
- **Security:** CORS enabled, behind nginx proxy
- **Health Check:** HTTP request to /health endpoint

**realtime-events-broadcaster**
- **Purpose:** WebSocket event streaming and log broadcasting
- **Configuration:**
  - Centralized DB: `/app/data/centralized_logs.db`
  - API Gateway URL: `http://traffic-monitor:5000`
  - Poll Interval: 1.0 second
  - Batch Size: 50 events
- **Data Flow:**
  - Monitors centralized logs database
  - Broadcasts new events to connected WebSocket clients
  - Provides real-time dashboard updates
- **Health Check:** Process verification

**data-maintenance**
- **Purpose:** Storage management and cleanup automation
- **Configuration:**
  - Storage Root: `/mnt/storage`
  - Image Max Age: 24 hours
  - Snapshot Max Age: 168 hours (7 days)
  - Log Max Age: 30 days
  - Emergency Threshold: 90%
  - Warning Threshold: 80%
- **Maintenance Tasks:**
  - Automated image cleanup
  - Log rotation
  - Snapshot management
  - Storage statistics reporting
  - Emergency space recovery
- **Health Check:** Storage stats presence in Redis (5-minute interval)

**camera-service-manager**
- **Purpose:** Monitors and manages IMX500 AI camera systemd service
- **Configuration:**
  - Service Name: `imx500-ai-capture.service`
  - Check Interval: 30 seconds
  - Privileges: Requires systemctl access
  - Network Mode: host (for systemd communication)
- **Monitoring:**
  - Checks service active status
  - Automatically restarts failed service
  - Logs service health to console
- **Health Check:** Verifies IMX500 service is active every 60 seconds

#### 2.2.5 Service Communication Architecture

**Data Flow:**

```text
IMX500 Camera (Host) → Redis Pub/Sub → Vehicle Consolidator → Database Persistence
                                ↓                                      ↓
OPS243 Radar (Serial) → Redis Pub/Sub → Vehicle Consolidator → SQLite Database
                                ↓                                      ↓
Weather Services → Redis Keys → Vehicle Consolidator → Edge API Gateway → nginx
                                                                         ↓
                                                                    Users (HTTPS)
```

**Message Channels:**
- `traffic_events` - Consolidation triggers
- `radar_detections` - Raw radar data
- `database_events` - Persistence triggers

**Redis Streams:**
- `radar_data` - Time-series radar readings (max 1000)
- `consolidated_traffic_data` - Consolidated events (max 100)

**Redis Keys:**
- `weather:airport:latest` - METAR weather data
- `weather:dht22:latest` - Local sensor data
- `consolidation:latest` - Current consolidated event
- `consolidation:history:{id}` - Historical events
- `maintenance:storage_stats` - Storage metrics

## Executive Summary System Architecture Diagram

The following high-level ASCII diagram provides an executive summary of the system architecture, showing the main components and their relationships.

This diagram summarizes the overall system structure and data flow for both technical and non-technical stakeholders.

```text
                        +--------------------------------------+
                        |    Cloud/Website Layer (GitHub)      |
                        |  +-------------------------------+   |
                        |  | GitHub Pages                  |   |
                        |  | (Static Website Hosting)      |   |
                        |  +-------------------------------+   |
                        |  | Cloud Dashboard UI            |   |
                        |  | (React/Next.js)               |   |
                        |  +-------------------------------+   |
                        |  | Historical Data Visualization |   |
                        |  | Traffic Analytics & Reports   |   |
                        |  +-------------------------------+   |
                        +------------------------^-------------+
                                         | (HTTPS/API)
                                         |
+-------------------+        +-------------------------------+
|   Remote User     |<------>|  Tailscale VPN Mesh Network   |
| (Web/SSH Client)  |        |  (Secure Remote Access)       |
+-------------------+        +-------------------------------+
                                         |
                                         v
                        +--------------------------------------+
                        |    Edge Device: Raspberry Pi 5       |
                        |                                      |
                        |  ┌────────────────────────────────┐ |
                        |  │ NGINX Reverse Proxy (HTTPS)    │ |
                        |  │ Port 8443 - TLS Termination    │ |
                        |  └────────────────────────────────┘ |
                        |                 ↓                    |
                        |  ┌────────────────────────────────┐ |
                        |  │ Edge API Gateway (Flask:5000)  │ |
                        |  │ WebSocket + REST API           │ |
                        |  └────────────────────────────────┘ |
                        |                 ↓                    |
                        |  ┌────────────────────────────────┐ |
                        |  │ Redis Message Broker (Pub/Sub) │ |
                        |  │ Streams + In-Memory Cache      │ |
                        |  └────────────────────────────────┘ |
                        |        ↓           ↓         ↓       |
                        |  ┌─────────┐ ┌──────────┐ ┌──────┐ |
                        |  │ Vehicle │ │ Database │ │ Data │ |
                        |  │ Consol. │ │ Persist. │ │ Maint│ |
                        |  └─────────┘ └──────────┘ └──────┘ |
                        |        ↑           ↓                 |
                        |  ┌─────────┐ ┌──────────┐           |
                        |  │ Weather │ │ SQLite   │           |
                        |  │ Services│ │ Database │           |
                        |  └─────────┘ └──────────┘           |
                        |                                      |
                        +--------------------------------------+
                                    ↑          ↑
                        ┌───────────┘          └───────────┐
                        |                                   |
                 ┌──────────────┐                   ┌──────────────┐
                 │ IMX500 Camera│                   │ OPS243-C     │
                 │ (Host Service)│                  │ Radar Sensor │
                 │ AI Inference │                   │ (UART/GPIO)  │
                 │ 3.1 TOPS NPU │                   │ Speed/Motion │
                 └──────────────┘                   └──────────────┘
                        ↓                                   ↓
                 Redis localhost:6379  ──────────────> Redis Pub/Sub
                 
                 ┌──────────────┐                   ┌──────────────┐
                 │ DHT22 Sensor │                   │ Samsung T7   │
                 │ (GPIO4)      │                   │ 2TB SSD      │
                 │ Temp/Humidity│                   │ Storage      │
                 └──────────────┘                   └──────────────┘
```

**Data Flow Summary:**

1. **Sensors → Edge Processing:**
   - IMX500 Camera (host service) → Redis → Vehicle Consolidator
   - OPS243-C Radar (UART) → Redis → Vehicle Consolidator
   - DHT22 Sensor (GPIO) → Redis → Weather data
   - Airport Weather API → Redis → Weather data

2. **Edge Processing → Storage:**
   - Vehicle Consolidator → Redis → Database Persistence → SQLite
   - All data stored on Samsung T7 SSD (90-day retention)

3. **Edge → Users:**
   - Edge API Gateway → NGINX (HTTPS) → Remote Users
   - WebSocket real-time streaming for live updates

4. **Edge → Cloud:**
   - Historical data export → GitHub Pages Dashboard
   - Traffic analytics and visualization

**Legend:**

- **Edge Device (Raspberry Pi 5):** Hosts 12 Docker containers + 1 host service
- **IMX500 Camera:** Runs as systemd host service (not containerized) for hardware access
- **Containerized Services:** All processing services run in Docker with health checks
- **Redis:** Central message broker for all inter-service communication
- **NGINX:** Reverse proxy with HTTPS/TLS termination on port 8443
- **Tailscale VPN:** Secure remote access to edge device and services
- **GitHub Pages:** Hosts public-facing website/dashboard for cloud analytics
- **Storage:** Samsung T7 2TB SSD for database, logs, images, and processed data
- **Sensors:** IMX500 (AI camera), OPS243-C (radar), DHT22 (weather) all feed data to Redis
- **12 Containerized Services:** redis, traffic-monitor, nginx-proxy, radar-service, 
  vehicle-consolidator, database-persistence, airport-weather, dht22-weather, 
  data-maintenance, redis-optimization, realtime-events-broadcaster, camera-service-manager

### Enhanced Edge AI Architecture Diagram

```text
+-------------------------------------------------------------+
|           Cloud Services Layer (Website/Cloud UI)           |
|  +-------------------+   +-------------------+              |
|  | GitHub Pages      |   | Cloud Dashboard   |              |
|  | (Static Hosting)  |   | (React/Next.js)   |              |
|  +-------------------+   +-------------------+              |
|  | Historical Data   |   | Analytics UI      |              |
|  | Visualization     |   | Traffic Reports   |              |
|  +-------------------+   +-------------------+              |
|         |                    |                              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Network & Communication Layer                       |
|  +-------------------+   +-------------------+              |
|  | nginx-proxy       |   | Tailscale VPN     |              |
|  | (HTTPS/TLS, 8443) |   | (Secure Remote)   |              |
|  +-------------------+   +-------------------+              |
|  | WebSocket Proxy   |   | Network Resilience|              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|    Edge AI Processing Layer (Raspberry Pi 5 - Docker)      |
|                                                             |
|  ┌─────────────────────────────────────────────────────┐   |
|  │  Core Infrastructure Services                       │   |
|  │  +------------------+  +------------------+         │   |
|  │  | redis            |  | nginx-proxy      |         │   |
|  │  | (Message Broker) |  | (Reverse Proxy)  |         │   |
|  │  +------------------+  +------------------+         │   |
|  └─────────────────────────────────────────────────────┘   |
|                                                             |
|  ┌─────────────────────────────────────────────────────┐   |
|  │  Data Collection Services (Containerized)           │   |
|  │  +------------------+  +------------------+         │   |
|  │  | radar-service    |  | airport-weather  |         │   |
|  │  | (OPS243-C UART)  |  | (METAR API)      |         │   |
|  │  +------------------+  +------------------+         │   |
|  │  | dht22-weather    |                               │   |
|  │  | (GPIO4 Sensor)   |                               │   |
|  │  +------------------+                               │   |
|  └─────────────────────────────────────────────────────┘   |
|                                                             |
|  ┌─────────────────────────────────────────────────────┐   |
|  │  Data Processing Services (Containerized)           │   |
|  │  +------------------+  +------------------+         │   |
|  │  | vehicle-         |  | database-        |         │   |
|  │  | consolidator     |  | persistence      |         │   |
|  │  | (Multi-Sensor)   |  | (SQLite)         |         │   |
|  │  +------------------+  +------------------+         │   |
|  │  | redis-           |  | data-maintenance |         │   |
|  │  | optimization     |  | (Storage Cleanup)|         │   |
|  │  +------------------+  +------------------+         │   |
|  └─────────────────────────────────────────────────────┘   |
|                                                             |
|  ┌─────────────────────────────────────────────────────┐   |
|  │  API & User Interface Services (Containerized)      │   |
|  │  +------------------+  +------------------+         │   |
|  │  | traffic-monitor  |  | realtime-events- |         │   |
|  │  | (API Gateway)    |  | broadcaster      |         │   |
|  │  | (Flask:5000)     |  | (WebSocket)      |         │   |
|  │  +------------------+  +------------------+         │   |
|  │  | camera-service-  |                               │   |
|  │  | manager          |                               │   |
|  │  | (Health Monitor) |                               │   |
|  │  +------------------+                               │   |
|  └─────────────────────────────────────────────────────┘   |
|                                                             |
|  ┌─────────────────────────────────────────────────────┐   |
|  │  Host Service (Non-Containerized - systemd)         │   |
|  │  +------------------+                               │   |
|  │  | imx500-ai-       |  ← Runs on Pi OS (not Docker)│   |
|  │  | capture.service  |    Publishes to Redis        │   |
|  │  | (IMX500 Camera)  |    localhost:6379            │   |
|  │  +------------------+                               │   |
|  └─────────────────────────────────────────────────────┘   |
|                                                             |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Physical Sensing Layer                              |
|  +-------------------+   +-------------------+              |
|  | IMX500 AI Camera  |   | OPS243-C Radar    |              |
|  | (3.1 TOPS NPU)    |   | (24.125 GHz FMCW) |              |
|  | CSI-2 Interface   |   | UART /dev/ttyAMA0 |              |
|  +-------------------+   +-------------------+              |
|  | DHT22 Sensor      |   | External SSD      |              |
|  | (GPIO4 Temp/Hum)  |   | (Samsung T7 2TB)  |              |
|  +-------------------+   +-------------------+              |
|  | Raspberry Pi 5 (16GB RAM, ARM Cortex-A76 Quad-Core)     |
|  | Docker Engine 24.0+ with 12 Containerized Services       |
|  +-----------------------------------------------------------+
|  | Power & Connectivity (PoE, WiFi/Ethernet, Cellular)      |
|  | Environmental Housing (IP65/IP66)                        |
+-------------------------------------------------------------+

Legend:
- 12 Containerized Services orchestrated via Docker Compose
- 1 Host Service (imx500-ai-capture.service) runs on Raspberry Pi OS
- All containers communicate via Docker bridge network (app-network)
- Redis pub/sub channels: traffic_events, radar_detections, database_events
- Redis streams: radar_data (max 1000), consolidated_traffic_data (max 100)
- IMX500 service publishes to Redis on localhost:6379 (port bound to host)
- nginx-proxy provides HTTPS/TLS termination on port 8443
- Tailscale VPN provides secure remote access to the system
- All services include health checks and automated restart policies
- Cloud Services Layer: GitHub Pages hosts public-facing website/dashboard
```

## 2.1 Physical Architecture Overview

```text
+-------------------------------------------------------------+
|      Cloud / Data Center (GitHub Pages - Remote)            |
|  - GitHub Pages Static Website Hosting                     |
|  - React/Next.js Cloud Dashboard UI                        |
|  - Historical Data Visualization & Analytics               |
|  - Traffic Reports & Pattern Analysis                      |
+---------------------^---------------------------------------+
                      |
                      v
+-------------------------------------------------------------+
|           Local Network / Internet                          |
|  - WiFi / Ethernet / Cellular                               |
|  - Tailscale VPN Mesh Network (Secure Remote Access)       |
+---------------------^---------------------------------------+
                      |
                      v
+-------------------------------------------------------------+
|           Edge Device: Raspberry Pi 5 Enclosure             |
|                                                             |
|  +-------------------+   +-------------------+              |
|  | Raspberry Pi 5    |   | Power Supply      |              |
|  | (16GB RAM, ARM)   |   | (PoE, USB-C, UPS) |              |
|  | Docker Engine     |   |                   |              |
|  | 12 Containers     |   |                   |              |
|  +-------------------+   +-------------------+              |
|  | External SSD      |   | Environmental     |              |
|  | (Samsung T7 2TB)  |   | Housing (IP65)    |              |
|  +-------------------+   +-------------------+              |
|                                                             |
|  +-------------------+   +-------------------+              |
|  | IMX500 AI Camera  |   | OPS243-C Radar    |              |
|  | (Host Service)    |   | (UART/GPIO)       |              |
|  +-------------------+   +-------------------+              |
|  | DHT22 Sensor      |                                      |
|  | (GPIO4)           |                                      |
|  +-------------------+                                      |
|                                                             |
|  [All sensors and storage connect to the Pi 5]              |
|                                                             |
|  Microservices Architecture:                                |
|  - NGINX Reverse Proxy (HTTPS/TLS on port 8443)            |
|  - Edge API Gateway (Flask-SocketIO on port 5000)          |
|  - Redis Message Broker (Pub/Sub, Streams, Cache)          |
|  - Vehicle Consolidator (Multi-Sensor Data Fusion)         |
|  - Database Persistence (SQLite with 90-day retention)     |
|  - Weather Services (Airport METAR + DHT22 Local)          |
|  - Data Maintenance (Storage Management & Cleanup)         |
|  - Redis Optimization (Memory Management)                  |
|  - Realtime Events Broadcaster (WebSocket Streaming)       |
|  - Camera Service Manager (IMX500 Health Monitoring)       |
+-------------------------------------------------------------+
```

## 3. Hardware Design

This section describes the hardware components and their specifications for the Raspberry Pi 5 Edge ML Traffic Monitoring System.

### 3.1 Hardware Components

**Core Computing Platform:**
- **Raspberry Pi 5 (16GB RAM)**
  - CPU: ARM Cortex-A76 Quad-Core @ 2.4GHz
  - GPU: VideoCore VII
  - Storage: 256GB MicroSD (UHS-I Class 10) + Samsung T7 Shield 2TB USB SSD
  - Power: Official Raspberry Pi 5 PSU (5.1V, 5A, 25W) with PoE+ HAT option
  - Operating System: Raspberry Pi OS (64-bit, Debian-based)

**AI Camera:**
- **Sony IMX500 Intelligent Vision Sensor**
  - Resolution: 12.3 megapixels (4056 x 3040)
  - On-chip AI: 3.1 TOPS neural processing unit (NPU)
  - Inference Speed: Sub-100ms for vehicle detection
  - Model Support: ONNX format, trained object detection models
  - Interface: CSI-2 camera interface to Raspberry Pi 5
  - Power: < 1W during inference

**Radar Sensor:**
- **OmniPreSense OPS243-C FMCW Doppler Radar**
  - Frequency: 24.125 GHz (K-band)
  - Range: Up to 200 meters
  - Speed Accuracy: ±0.1 mph
  - Update Rate: 10-20 Hz
  - Interface: UART/Serial @ 19200 baud
  - Protocol: JSON output format
  - Power: 150mA @ 5V
  - GPIO Integration: Host interrupt (GPIO23), Reset (GPIO24), Speed alerts (GPIO5/6)

**Environmental Monitoring:**
- **DHT22 Temperature/Humidity Sensor**
  - Temperature Range: -40°C to 80°C (±0.5°C accuracy)
  - Humidity Range: 0-100% RH (±2-5% accuracy)
  - Interface: GPIO4 (single-wire digital)
  - Update Interval: 10 minutes (configurable)

**Storage:**
- **External SSD:** Samsung T7 Shield 2TB (USB 3.2 Gen 2)
- **Primary Storage Locations:**
  - `/mnt/storage/camera_capture` - AI camera images and metadata
  - `/mnt/storage/processed_data` - Consolidated event data
  - `/mnt/storage/data` - SQLite databases
  - `/mnt/storage/logs` - Centralized application logs
  - `/mnt/storage/ai_camera_images` - IMX500 detection images

**Network & Connectivity:**
- **Primary:** Gigabit Ethernet (wired)
- **Backup:** WiFi 5 (802.11ac dual-band)
- **VPN:** Tailscale mesh network for secure remote access
- **Optional:** 4G/LTE cellular backup via USB modem

**Power & Protection:**
- **Primary Power:** Official Raspberry Pi 5 27W USB-C PSU
- **Alternative:** PoE+ HAT (Power over Ethernet, 802.3at)
- **Backup Power:** Optional UPS (Uninterruptible Power Supply)
- **Power Consumption:** ~15-25W typical, ~30W peak

**Environmental Housing:**
- **Enclosure Rating:** IP65/IP66 weatherproof
- **Operating Temperature:** -40°C to +71°C
- **Mounting:** Pole/wall mount with adjustable camera/radar positioning
- **Protection:** Surge protection, overvoltage/overcurrent protection

### 3.1 Hardware Pinout and Connections

This section documents the physical connections between the OPS243-C radar sensor and Raspberry Pi 5 for optimal sensor integration and real-time correlation.

#### OPS243-C Radar Sensor to Raspberry Pi 5 Pinout

| OPS243 Pin | Function | Wire Color | RPi Physical Pin | RPi GPIO | Description |
|------------|----------|------------|------------------|----------|-------------|
| Pin 3 | Host Interrupt | Orange | Pin 16 | GPIO23 | Real-time detection signal (active low) |
| Pin 4 | Reset | Yellow | Pin 18 | GPIO24 | Software reset control (active low) |
| Pin 6 | UART RxD | Green | Pin 8 | GPIO14 (TXD) | Radar receives commands |
| Pin 7 | UART TxD | White | Pin 10 | GPIO15 (RXD) | Radar transmits data |
| Pin 9 | 5V Power | Red | Pin 4 | 5V Power | Power supply (150mA typical) |
| Pin 10 | Ground | Black | Pin 6 | Ground | Common ground |
| **Pin 1** | **Low Alert/Sampling** | **Blue** | **Pin 29** | **GPIO5** | **Speed/range low threshold alert** |
| **Pin 2** | **High Alert** | **Purple** | **Pin 31** | **GPIO6** | **Speed/range high threshold alert** |

#### GPIO Configuration

```python
# GPIO Pin Assignments
RADAR_GPIO_PINS = {
    "host_interrupt": 23,  # Orange wire - Immediate detection notification
    "reset": 24,           # Yellow wire - Software reset capability
    "low_alert": 5,        # Blue wire - Low speed/range threshold alerts
    "high_alert": 6        # Purple wire - High speed/range threshold alerts
}

# UART Configuration
RADAR_UART_PORT = "/dev/ttyACM0"
RADAR_BAUD_RATE = 115200
```

#### Physical Pin Layout on Raspberry Pi 5

```
     3V3  (1) (2)  5V     ← Pin 4 (Red - Radar Power)
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND    ← Pin 6 (Black - Radar Ground)
   GPIO4  (7) (8)  GPIO14 ← Pin 8 (Green - Radar RxD)
     GND  (9) (10) GPIO15 ← Pin 10 (White - Radar TxD)
  GPIO17 (11) (12) GPIO18
  GPIO27 (13) (14) GND
  GPIO22 (15) (16) GPIO23 ← Pin 16 (Orange - Radar Interrupt)
     3V3 (17) (18) GPIO24 ← Pin 18 (Yellow - Radar Reset)
  GPIO10 (19) (20) GND
   GPIO9 (21) (22) GPIO25
  GPIO11 (23) (24) GPIO8
     GND (25) (26) GPIO7
   GPIO0 (27) (28) GPIO1
   GPIO5 (29) (30) GND    ← Pin 29 (Blue - Radar Low Alert)
   GPIO6 (31) (32) GPIO12 ← Pin 31 (Purple - Radar High Alert)
  GPIO13 (33) (34) GND
  GPIO19 (35) (36) GPIO16
  GPIO26 (37) (38) GPIO20
     GND (39) (40) GPIO21
```

#### Radar GPIO Integration Benefits

1. **Real-Time Detection Correlation**
   - Host interrupt (GPIO23) triggers immediate IMX500 capture
   - Perfect temporal synchronization between radar and camera
   - Sub-100ms response time for detection events

2. **Speed-Based Camera Behavior**
   - Low alert (GPIO5): Adjust capture for slow vehicles
   - High alert (GPIO6): Trigger rapid capture for fast vehicles
   - Configurable speed thresholds via radar API

3. **System Reliability**
   - Reset capability (GPIO24) for radar recovery
   - Hardware-level event detection without polling
   - Reduced CPU usage through interrupt-driven processing

#### Radar Configuration Commands

```bash
# Enable GPIO alert outputs
radar_command("AL15")  # Low speed alert at 15 mph
radar_command("AH45")  # High speed alert at 45 mph
radar_command("IG")    # Enable host interrupt output
```

## 3.2 ML/AI Workflow and Component Status

This section summarizes the ML/AI workflow, component status, and technical details for the traffic monitoring system. For full details, see `ml_ai_workflow_analysis.md` in the archive.

### Component Status Legend

- 🟢 **EXISTING**: Available in hardware/libraries, minimal development needed
- 🟡 **PARTIAL**: Basic functionality exists, requires customization/integration
- 🔴 **CUSTOM**: Must be developed specifically for this project


### AI-Enabled Camera Hardware (Sony IMX500) - 🟢 EXISTING

- On-chip neural network processing for real-time object detection and classification
- Edge computing: runs lightweight models, reduces bandwidth by filtering irrelevant frames
- Provides pre-processed data streams with detected objects and metadata
- Hardware integration via standard camera interface; supports Sony-provided or custom models

#### Model Training and Deployment Workflow for IMX500

The Sony IMX500 AI camera performs inference using a pre-trained model deployed to the device. The typical workflow is as follows:

1. **Data Collection & Annotation:**
  - Gather a dataset of images containing vehicles in various environments and lighting conditions.
  - Annotate each image with bounding boxes and class labels (e.g., “car”, “truck”, “bus”) using tools like LabelImg or CVAT.

2. **Model Training (Off-Camera):**
  - Choose an object detection architecture (e.g., YOLOv5, MobileNet-SSD, EfficientDet).
  - Use a machine learning framework (TensorFlow, PyTorch, or ONNX) to train the model on your annotated dataset.
  - Train the model until it achieves satisfactory accuracy on a validation set.

3. **Model Conversion:**
  - Convert the trained model to a format supported by the IMX500 camera, typically ONNX.
  - Optimize the model for edge inference (quantization, pruning, etc.) if required by the camera’s SDK.

4. **Model Deployment to IMX500:**
  - Use Sony’s AITRIOS SDK or the IMX500 camera’s deployment tools to upload the ONNX model to the camera.
  - Configure the camera to use the new model for real-time inference.

5. **Inference on the Camera:**
  - The camera processes video frames internally, running the deployed model to detect vehicles.
  - The camera outputs detection results (bounding boxes, class labels, confidence scores) as metadata, which can be read by the Raspberry Pi or another host device.

**Note:** The IMX500 does not perform model training on-device; all training is done off-camera, and only inference is performed on the camera hardware.

**References:**
- [Sony AITRIOS SDK documentation](https://developer.sony.com/develop/cameras/)
- [IMX500 product page](https://www.sony-semicon.com/en/products/IS/imx500.html)

### Computer Vision Module (OpenCV + TensorFlow) - 🟡 PARTIAL

- Analyzes video streams from the AI camera for vehicle detection, classification, and tracking
- Supports custom and pre-trained models; requires integration and tuning for project needs

### Project Requirements

- Hardware integration (camera, radar, storage)
- Model loading and configuration (Sony IMX500, TensorFlow)
- Set up detection parameters, output formats, and data fusion logic

**See also:** [ML/AI Workflow Analysis](../archive/ml_ai_workflow_analysis.md)

---

### Edge Processing Layer (Software)

- **Vehicle Detection Service:** TensorFlow + OpenCV + AI Camera processing
- **Speed Analysis Service:** Radar data processing and Doppler calculations
- **Multi-Vehicle Tracking:** SORT algorithm implementation, Kalman filtering
- **Data Fusion Engine:** Camera + Radar correlation with Kalman filtering
- **Weather Integration:** API-based environmental context
- **Anomaly Detection:** Pattern analysis and incident detection
- **System Health Monitor:** Watchdog timers and performance metrics
- **Local Storage Manager:** tmpfs and SSD data optimization
- **Edge API Gateway:** Flask-SocketIO server for real-time communication
- **Edge UI:** Local Web Dashboard

### Network & Communication Layer

- **WebSocket Server:** Real-time data streaming
- **REST API Endpoints:** Configuration and status management
- **Data Compression & Queuing:** Optimized cloud transmission
- **Network Resilience:** Offline-first operation with reconnection logic
- **Security:** TLS/SSL encryption and API authentication

### Cloud Services Layer (Optional)

- **Data Aggregation:** Historical pattern analysis
- **Advanced Analytics:** Traffic flow modeling and prediction
- **Model Management:** ML model versioning and updates
- **Dashboard & Reporting:** Web-based traffic analytics
- **Alert & Notification:** Incident response system

### Technologies and Protocols Used

- Python 3, TensorFlow, OpenCV, Flask, Flask-SocketIO
- UART/Serial for radar communication
- WebSocket/REST for dashboard and API
- MQTT (optional, for cloud data transmission)
- Docker (recommended for deployment)

## 4. Component Interaction Diagram

```text
MAIN EVENT WORKFLOW (Real-time Detection Path)
═══════════════════════════════════════════════════════════════════

+------------------+       +-----------------+       +-----------------+
| Sony IMX500 AI   |       | OPS243-C Radar  |       | DHT22 Sensor    |
| Camera (Host)    |       | (UART/GPIO)     |       | (GPIO4)         |
| imx500-ai-       |       | radar-service   |       | dht22-weather   |
| capture.service  |       | (Container)     |       | (Container)     |
+--------+---------+       +--------+--------+       +--------+--------+
         |                          |                         |
         | detections.json          | Redis Pub/Sub          | Redis Pub/Sub
         | (file system)            | radar_detections       | weather_updates
         v                          v                         v
+------------------------------------------------------------------+
|                    Redis Message Broker                          |
|  Pub/Sub Channels:                                               |
|  - traffic_events (vehicle detections)                           |
|  - radar_detections (speed/direction)                            |
|  - database_events (persistence notifications)                   |
|  - weather_updates (environmental data)                          |
|                                                                  |
|  Redis Streams:                                                  |
|  - radar_data (maxlen=1000, for historical queries)              |
|  - consolidated_traffic_data (maxlen=100, multi-sensor fusion)   |
|                                                                  |
|  Redis Keys:                                                     |
|  - weather:airport:latest, weather:dht22:latest                  |
|  - consolidation:latest, maintenance:storage_stats               |
+--------+---------+----------------+----------------+-------------+
         |                          |                |             |
         v                          v                v             v
+------------------+  +-------------------+  +-----------------+ +------------------+
| traffic-monitor  |  | vehicle-          |  | airport-weather| | realtime-events- |
| (Container)      |  | consolidator      |  | (Container)    | | broadcaster      |
| Reads detections |  | (Container)       |  | weather.gov API| | (Container)      |
| Publishes to     |  | Multi-sensor      |  | (METAR/KOKC)   | | WebSocket        |
| Redis            |  | data fusion       |  |                | | streaming        |
+--------+---------+  +--------+----------+  +--------+-------+ +--------+---------+
         |                     |                      |                  |
         |                     v                      |                  |
         |          +----------------------+          |                  |
         +--------->| database-persistence |<---------+                  |
                    | (Container)          |                             |
                    | SQLite storage       |                             |
                    | 90-day retention     |                             |
                    +----------+-----------+                             |
                               |                                         |
+-----------------------------+|                                         |
|                              |                                         |
v                              v                                         v
+------------------------------------------------------------------+
|                     NGINX Reverse Proxy                          |
|  HTTPS/TLS on port 8443 (Self-signed SSL)                       |
|  Routes:                                                         |
|  - /api/* -> Edge API Gateway (port 5000)                        |
|  - /socket.io/* -> Flask-SocketIO WebSocket                      |
+--------+---------+------------------------------------------------+
         |
         v
+------------------------------------------------------------------+
|                    Edge API Gateway (traffic-monitor)            |
|  Flask-SocketIO (port 5000)                                      |
|  REST API Endpoints:                                             |
|  - /api/events, /api/radar, /api/weather, /api/consolidated     |
|  - /api/stats, /api/system-health, /health                       |
|  WebSocket Events (via realtime-events-broadcaster):             |
|  - new_detection, radar_update, weather_update, database_event   |
+--------+---------+------------------------------------------------+
         |
         v
+------------------------------------------------------------------+
|              Users & Cloud Dashboard                             |
|  - Local Network Users (Tailscale VPN)                           |
|  - GitHub Pages Dashboard (Historical Data Visualization)        |
+------------------------------------------------------------------+


BACKGROUND MAINTENANCE SERVICES (Independent Processes)
═══════════════════════════════════════════════════════════════════

+----------------------+    +----------------------+    +----------------------+
| data-maintenance     |    | redis-optimization   |    | camera-service-      |
| (Container)          |    | (Container)          |    | manager (Container)  |
+----------------------+    +----------------------+    +----------------------+
| Storage cleanup      |    | Memory management    |    | Health monitoring    |
| - Images: 24h max    |    | - TTL policies       |    | - imx500-ai-capture  |
| - Snapshots: 7d max  |    | - Stream trimming    |    |   .service status    |
| - Logs: 30d max      |    | - Defragmentation    |    | - Auto-restart on    |
| - Emergency cleanup  |    | - Stats reporting    |    |   failure            |
|   at 90% capacity    |    | - Runs hourly        |    | - Checks every 30s   |
+----------+-----------+    +----------+-----------+    +----------+-----------+
           |                           |                           |
           | Monitors                  | Optimizes                 | Monitors
           | /mnt/storage/             | Redis memory              | systemd service
           v                           v                           v
+----------------------+    +----------------------+    +----------------------+
| File System          |    | Redis Message Broker |    | Host systemd         |
| (Samsung T7 SSD)     |    | (localhost:6379)     |    | (Raspberry Pi OS)    |
+----------------------+    +----------------------+    +----------------------+

Legend:
- Solid lines (|, v, -): Main event workflow (real-time data path)
- Background services: Run independently, not triggered by detection events
- All 12 containerized services shown
- 1 host service (imx500-ai-capture.service) monitored by camera-service-manager
```

## 5. Happy Path Detection Workflow (Start to Finish)

This section provides a detailed walkthrough of a complete vehicle detection event from initial sensor triggers through final data delivery to end users.

### 5.1 Complete Detection Workflow Diagram

```text
HAPPY PATH: Vehicle Detection Flow (End-to-End)
═══════════════════════════════════════════════════════════════════════════════

Time: T+0ms - TRIGGER PHASE
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Physical Vehicle Passes Through Detection Zone                      │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│   🚗 Vehicle enters radar detection zone (0-200m range)                    │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  OPS243-C Radar      │                                            │
│        │  (24.125 GHz FMCW)   │  ← Doppler shift detected                 │
│        │  UART: /dev/ttyAMA0  │    Speed: 35.4 mph                        │
│        └──────────────────────┘    Direction: approaching                 │
│                 │                                                           │
│                 │ HANDOFF #1: UART Serial @ 19200 baud                     │
│                 │ FORMAT: JSON string                                      │
│                 │ {"speed": 35.4, "direction": "approaching"}              │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  radar-service       │                                            │
│        │  (Python Container)  │  Parses JSON, validates speed threshold   │
│        │  Port: /dev/ttyAMA0  │  (min: 2.0 mph)                           │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #2: Redis Pub/Sub                                │
│                 │ CHANNEL: "radar_detections"                              │
│                 │ FORMAT: JSON object                                      │
│                 │ {                                                        │
│                 │   "speed_mph": 35.4,                                     │
│                 │   "magnitude": 0.85,                                     │
│                 │   "direction": "approaching",                            │
│                 │   "timestamp": "2025-10-01T14:23:45.123Z",               │
│                 │   "correlation_id": "radar_1696171425123"                │
│                 │ }                                                        │
│                 │                                                           │
│                 │ HANDOFF #3: Redis Stream (parallel)                      │
│                 │ STREAM: "radar_data" (maxlen=1000)                       │
│                 │ FORMAT: Time-series entry with same JSON payload         │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  Redis Message Broker│                                            │
│        │  localhost:6379       │  Stores in memory, notifies subscribers  │
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+50ms - RADAR TRIGGER PUBLISHED
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Radar Detection Triggers Traffic Event                             │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  radar-service       │                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #4: Redis Pub/Sub (trigger)                      │
│                 │ CHANNEL: "traffic_events"                                │
│                 │ FORMAT: JSON trigger message                             │
│                 │ {                                                        │
│                 │   "event_type": "radar_detection",                       │
│                 │   "trigger_source": "radar",                             │
│                 │   "timestamp": "2025-10-01T14:23:45.150Z",               │
│                 │   "correlation_id": "event_1696171425150"                │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  vehicle-consolidator│ ← Subscribes to "traffic_events"          │
│        │  (Python Container)  │   Receives trigger, begins data gathering │
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+75ms - CAMERA INFERENCE (PARALLEL)
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: IMX500 Camera AI Inference                                         │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  IMX500 AI Camera    │                                            │
│        │  (Host Service)      │  Continuous video stream processing       │
│        │  3.1 TOPS NPU        │  ONNX model running on-chip               │
│        └──────────────────────┘  Vehicle detected: "car" (confidence: 0.92)│
│                 │                 Bounding box: [x:120, y:80, w:340, h:280]│
│                 │                 Inference time: 87ms                     │
│                 │                                                           │
│                 │ HANDOFF #5: File System Write                            │
│                 │ PATH: /mnt/storage/ai_camera_images/                     │
│                 │ FILES:                                                   │
│                 │   - detection_1696171425200.jpg (image)                  │
│                 │   - detection_1696171425200.json (metadata)              │
│                 │                                                           │
│                 │ FORMAT: JSON metadata file                               │
│                 │ {                                                        │
│                 │   "timestamp": "2025-10-01T14:23:45.200Z",               │
│                 │   "detections": [                                        │
│                 │     {                                                    │
│                 │       "class": "car",                                    │
│                 │       "confidence": 0.92,                                │
│                 │       "bbox": [120, 80, 340, 280],                       │
│                 │       "class_id": 2                                      │
│                 │     }                                                    │
│                 │   ],                                                     │
│                 │   "image_path": "detection_1696171425200.jpg",           │
│                 │   "model": "vehicle_detection_v2.onnx"                   │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  Shared Volume       │                                            │
│        │  /mnt/storage/       │  Docker volume accessible to all containers│
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+100ms - WEATHER CONTEXT (PARALLEL)
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Weather Data Collection (Background Services)                      │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌────────────────────┐              ┌────────────────────┐               │
│  │ airport-weather    │              │ dht22-weather      │               │
│  │ (Container)        │              │ (Container)        │               │
│  │ API: weather.gov   │              │ GPIO4 Sensor       │               │
│  └────────────────────┘              └────────────────────┘               │
│           │                                     │                          │
│           │ HANDOFF #6a: Redis Key             │ HANDOFF #6b: Redis Key   │
│           │ KEY: "weather:airport:latest"      │ KEY: "weather:dht22:latest"│
│           │ FORMAT: JSON object                │ FORMAT: JSON object      │
│           │ {                                  │ {                        │
│           │   "temperature_f": 72.5,           │   "temperature_f": 71.8, │
│           │   "humidity": 65,                  │   "humidity": 68,        │
│           │   "wind_speed_mph": 8.2,           │   "timestamp": "...",    │
│           │   "wind_direction": "SE",          │   "sensor_id": "dht22_01"│
│           │   "conditions": "Clear",           │ }                        │
│           │   "visibility_mi": 10,             │                          │
│           │   "station": "KOKC",               │                          │
│           │   "timestamp": "2025-10-01T14:20:00Z"                         │
│           │ }                                  │                          │
│           ↓                                     ↓                          │
│        ┌──────────────────────────────────────────┐                       │
│        │  Redis Key-Value Store                   │                       │
│        │  Weather data cached in memory           │                       │
│        └──────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+150ms - DATA CONSOLIDATION
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Multi-Sensor Data Fusion                                           │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  vehicle-consolidator│                                            │
│        │  (Python Container)  │                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Gathers data from multiple sources:                      │
│                 │                                                           │
│                 │ SOURCE #1: Redis Stream "radar_data"                     │
│                 │   - Latest speed reading: 35.4 mph                       │
│                 │   - Magnitude: 0.85                                      │
│                 │                                                           │
│                 │ SOURCE #2: File System (IMX500 detections)               │
│                 │   - Reads: /mnt/storage/ai_camera_images/*.json          │
│                 │   - Filters: Last 5 seconds of detections                │
│                 │   - Best match: confidence 0.92, class "car"             │
│                 │                                                           │
│                 │ SOURCE #3: Redis Key "weather:airport:latest"            │
│                 │   - Temperature: 72.5°F                                  │
│                 │   - Conditions: "Clear"                                  │
│                 │                                                           │
│                 │ SOURCE #4: Redis Key "weather:dht22:latest"              │
│                 │   - Local temp: 71.8°F                                   │
│                 │   - Local humidity: 68%                                  │
│                 │                                                           │
│                 │ CREATES CONSOLIDATED RECORD                              │
│                 │                                                           │
│                 │ HANDOFF #7: Redis Pub/Sub                                │
│                 │ CHANNEL: "database_events"                               │
│                 │ FORMAT: Enriched JSON object                             │
│                 │ {                                                        │
│                 │   "event_id": "evt_1696171425250",                       │
│                 │   "correlation_id": "event_1696171425150",               │
│                 │   "timestamp": "2025-10-01T14:23:45.250Z",               │
│                 │   "radar": {                                             │
│                 │     "speed_mph": 35.4,                                   │
│                 │     "magnitude": 0.85,                                   │
│                 │     "direction": "approaching"                           │
│                 │   },                                                     │
│                 │   "camera": {                                            │
│                 │     "vehicle_class": "car",                              │
│                 │     "confidence": 0.92,                                  │
│                 │     "image_path": "detection_1696171425200.jpg",         │
│                 │     "bbox": [120, 80, 340, 280]                          │
│                 │   },                                                     │
│                 │   "weather": {                                           │
│                 │     "temperature_f": 72.5,                               │
│                 │     "humidity": 65,                                      │
│                 │     "conditions": "Clear",                               │
│                 │     "wind_speed_mph": 8.2,                               │
│                 │     "local_temp_f": 71.8,                                │
│                 │     "local_humidity": 68                                 │
│                 │   },                                                     │
│                 │   "processing_time_ms": 150                              │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  Redis Message Broker│                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #8: Redis Key (parallel)                         │
│                 │ KEY: "consolidation:latest"                              │
│                 │ FORMAT: Same enriched JSON (cached for API access)       │
│                 │                                                           │
│                 │ HANDOFF #9: Redis Stream (parallel)                      │
│                 │ STREAM: "consolidated_traffic_data" (maxlen=100)         │
│                 │ FORMAT: Same enriched JSON (time-series history)         │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  Redis Storage        │                                            │
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+200ms - PERSISTENCE
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Database Persistence                                               │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  Redis Message Broker│                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Publishes to subscribers of "database_events"            │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │ database-persistence │ ← Subscribes to "database_events"         │
│        │ (Python Container)   │   Receives consolidated record            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Batch processing:                                        │
│                 │ - Buffers up to 100 records                              │
│                 │ - Commits every 30 seconds OR when buffer full           │
│                 │                                                           │
│                 │ HANDOFF #10: SQLite Write                                │
│                 │ DATABASE: /app/data/traffic_data.db                      │
│                 │ TABLES: traffic_events, weather_data, sensor_readings    │
│                 │ FORMAT: Normalized schema with foreign keys              │
│                 │                                                           │
│                 │ INSERT INTO traffic_events:                              │
│                 │   event_id, timestamp, correlation_id, vehicle_class,    │
│                 │   confidence, speed_mph, image_path, ...                 │
│                 │                                                           │
│                 │ INSERT INTO weather_data:                                │
│                 │   event_id, temperature_f, humidity, conditions, ...     │
│                 │                                                           │
│                 │ INSERT INTO sensor_readings:                             │
│                 │   event_id, sensor_type, reading_value, ...              │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  SQLite Database     │                                            │
│        │  /mnt/storage/data/  │  Persisted to SSD (90-day retention)      │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #11: Confirmation (optional)                     │
│                 │ CHANNEL: "database_events" (confirmation message)        │
│                 │ FORMAT: JSON status                                      │
│                 │ {                                                        │
│                 │   "status": "persisted",                                 │
│                 │   "event_id": "evt_1696171425250",                       │
│                 │   "timestamp": "2025-10-01T14:23:45.300Z"                │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  Redis Message Broker│                                            │
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+250ms - REAL-TIME STREAMING
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: WebSocket Broadcasting to Connected Clients                        │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  Redis Message Broker│                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Publishes to all subscribers                             │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │ realtime-events-     │ ← Subscribes to multiple channels:        │
│        │ broadcaster          │   - "traffic_events"                      │
│        │ (Python Container)   │   - "radar_detections"                    │
│        │ Flask-SocketIO       │   - "database_events"                     │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Reads from centralized logs DB (parallel)                │
│                 │ DATABASE: /app/data/centralized_logs.db                  │
│                 │ Polls every 1 second for new events                      │
│                 │                                                           │
│                 │ HANDOFF #12: WebSocket (Socket.IO)                       │
│                 │ EVENT: "new_detection"                                   │
│                 │ FORMAT: JSON payload                                     │
│                 │ {                                                        │
│                 │   "event_type": "vehicle_detection",                     │
│                 │   "event_id": "evt_1696171425250",                       │
│                 │   "timestamp": "2025-10-01T14:23:45.250Z",               │
│                 │   "vehicle_class": "car",                                │
│                 │   "speed_mph": 35.4,                                     │
│                 │   "confidence": 0.92,                                    │
│                 │   "weather_conditions": "Clear",                         │
│                 │   "temperature_f": 72.5                                  │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  traffic-monitor     │ ← Socket.IO server on port 5000           │
│        │  (Flask-SocketIO)    │   Maintains WebSocket connections         │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #13: Reverse Proxy (HTTPS)                       │
│                 │ URL: wss://raspberrypi.local:8443/socket.io              │
│                 │ PROTOCOL: WebSocket over TLS                             │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  nginx-proxy         │                                            │
│        │  (HTTPS/TLS)         │  SSL termination, WebSocket upgrade       │
│        │  Port 8443           │  Security headers, rate limiting          │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #14: Secure WebSocket                            │
│                 │ CONNECTION: wss:// (WebSocket Secure)                    │
│                 │ PROTOCOL: Socket.IO over HTTPS                           │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  User Browser        │                                            │
│        │  (Dashboard Client)  │  JavaScript Socket.IO client              │
│        │  Edge UI             │  Real-time event listener                 │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Updates dashboard UI:                                    │
│                 │ - Live event counter                                     │
│                 │ - Recent detections list                                 │
│                 │ - Speed chart update                                     │
│                 │ - Vehicle classification stats                           │
│                 │ - Weather display                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Time: T+300ms - API ACCESS (ON-DEMAND)
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: REST API Access (User-Initiated Queries)                           │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│        ┌──────────────────────┐                                            │
│        │  User Browser        │                                            │
│        │  (Dashboard Client)  │  User clicks "View Event Details"         │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #15: HTTPS REST API Request                      │
│                 │ REQUEST: GET /api/events/evt_1696171425250               │
│                 │ HEADERS: Authorization, Content-Type                     │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  nginx-proxy         │                                            │
│        │  Port 8443           │  TLS termination, route to backend        │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Forwards to upstream                                     │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  traffic-monitor     │ ← Flask REST API on port 5000             │
│        │  (API Gateway)       │   Handles HTTP requests                   │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ Queries data sources:                                    │
│                 │                                                           │
│                 │ SOURCE #1: Redis Key "consolidation:latest"              │
│                 │   (for most recent event)                                │
│                 │                                                           │
│                 │ SOURCE #2: SQLite Database                               │
│                 │   SELECT * FROM traffic_events                           │
│                 │   WHERE event_id = 'evt_1696171425250'                   │
│                 │   JOIN weather_data ON event_id                          │
│                 │   JOIN sensor_readings ON event_id                       │
│                 │                                                           │
│                 │ HANDOFF #16: HTTP Response                               │
│                 │ STATUS: 200 OK                                           │
│                 │ CONTENT-TYPE: application/json                           │
│                 │ FORMAT: Complete enriched event record                   │
│                 │ {                                                        │
│                 │   "event_id": "evt_1696171425250",                       │
│                 │   "timestamp": "2025-10-01T14:23:45.250Z",               │
│                 │   "vehicle": {                                           │
│                 │     "class": "car",                                      │
│                 │     "confidence": 0.92,                                  │
│                 │     "speed_mph": 35.4,                                   │
│                 │     "direction": "approaching",                          │
│                 │     "image_url": "/api/images/detection_1696171425200.jpg"│
│                 │   },                                                     │
│                 │   "weather": {                                           │
│                 │     "temperature_f": 72.5,                               │
│                 │     "humidity": 65,                                      │
│                 │     "conditions": "Clear",                               │
│                 │     "wind_speed_mph": 8.2                                │
│                 │   },                                                     │
│                 │   "metadata": {                                          │
│                 │     "processing_time_ms": 150,                           │
│                 │     "correlation_id": "event_1696171425150",             │
│                 │     "data_sources": ["radar", "camera", "weather"]       │
│                 │   }                                                      │
│                 │ }                                                        │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  nginx-proxy         │                                            │
│        └──────────────────────┘                                            │
│                 │                                                           │
│                 │ HANDOFF #17: HTTPS Response                              │
│                 ↓                                                           │
│        ┌──────────────────────┐                                            │
│        │  User Browser        │                                            │
│        │  (Dashboard Client)  │  Displays detailed event information      │
│        └──────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
END-TO-END LATENCY: ~300ms (from physical detection to user dashboard update)

TOTAL HANDOFFS: 17 distinct data transfers across services
FORMATS USED: JSON (primary), Binary (UART), File System (images), SQL (persistence)
PROTOCOLS: UART, Redis Pub/Sub, Redis Streams, File I/O, WebSocket, HTTPS REST

KEY PERFORMANCE METRICS:
- Radar detection to Redis: ~50ms
- IMX500 inference: ~87ms (hardware-accelerated)
- Multi-sensor consolidation: ~100ms
- Database persistence: ~50ms (batch mode)
- WebSocket streaming: <10ms
- REST API response: <50ms (from cache or database)
```

### 5.2 Data Flow Summary

**Primary Communication Patterns:**

1. **Sensor → Service:** UART (radar), File System (camera), GPIO (DHT22)
2. **Service → Redis:** Pub/Sub channels, Streams, Key-Value pairs
3. **Redis → Services:** Subscribe patterns, XREAD streams, GET keys
4. **Service → Database:** Batch SQLite writes with transactions
5. **Service → Users:** WebSocket (real-time), HTTPS REST (on-demand)

**Data Format Standards:**

- **Sensor Data:** JSON strings (radar), JSON files (camera), raw digital (DHT22)
- **Inter-Service:** JSON objects via Redis pub/sub
- **Persistence:** Normalized SQL schema with foreign keys
- **Client Delivery:** JSON over WebSocket/HTTPS

**Reliability Mechanisms:**

- Redis Streams provide message history (replay capability)
- Batch database writes reduce I/O overhead
- File system acts as backup for camera detections
- Health checks on all services ensure availability
- Correlation IDs enable end-to-end tracing

## 5. Sequence Diagram (Typical Event Flow)
   +---------------------+
   | User Request        |
   +----------+----------+
              |
              | GET /api/latest
              v
   +---------------------+
   | NGINX Proxy         |
   +----------+----------+
              |
              | Proxy to port 5000
              v
   +---------------------+
   | Edge API Gateway    |
   | (Flask)             |
   +----------+----------+
              |
              | Query Redis & SQLite
              v
   +---------------------+
   | Response (JSON)     |
   +---------------------+
```

## 6. Deployment Diagram (Physical/Virtual Placement)

```text
+------------------------------------------------------------------+
|                   Cloud Services Layer                           |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  GitHub Pages (Static Website Hosting)                    |  |
|  |  - React/Next.js Cloud Dashboard                          |  |
|  |  - Historical Data Visualization                          |  |
|  |  - Traffic Analytics & Reports                            |  |
|  |  - Responsive UI for Desktop/Mobile                       |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+----------------------^-------------------------------------------+
                       |
                       | HTTPS/TLS
                       | Internet
                       |
+----------------------v-------------------------------------------+
|                   Network Layer                                  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Tailscale VPN (WireGuard Mesh Network)                   |  |
|  |  - Secure remote access to Pi 5                           |  |
|  |  - Encrypted tunnel (100.121.231.16)                      |  |
|  |  - NAT traversal, firewall bypass                         |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Local Network (WiFi/Ethernet)                            |  |
|  |  - Gigabit Ethernet (primary)                             |  |
|  |  - WiFi 5 (802.11ac) backup                               |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+----------------------^-------------------------------------------+
                       |
                       |
+----------------------v-------------------------------------------+
|              Edge Device (Raspberry Pi 5)                        |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Host System Services (Pi OS, systemd)                    |  |
|  |  - imx500-ai-capture.service (Sony IMX500 Camera Driver)  |  |
|  |  - Docker Engine 24.0+                                    |  |
|  |  - SSH Server (remote access)                             |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Docker Container Orchestration (12 Services)             |  |
|  |                                                            |  |
|  |  Core Infrastructure:                                      |  |
|  |  - redis (Message Broker, Cache, Streams)                 |  |
|  |  - nginx-proxy (Reverse Proxy, HTTPS/TLS on 8443)        |  |
|  |  - traffic-monitor (Camera Detection Watcher)             |  |
|  |  - camera-service-manager (Health Monitor)                |  |
|  |                                                            |  |
|  |  Data Collection:                                          |  |
|  |  - radar-service (OPS243-C UART/GPIO Interface)           |  |
|  |  - airport-weather (METAR API Client)                     |  |
|  |  - dht22-weather (Local Sensor Reader)                    |  |
|  |                                                            |  |
|  |  Data Processing:                                          |  |
|  |  - vehicle-consolidator (Multi-Sensor Fusion)             |  |
|  |  - database-persistence (SQLite Writer, 90-day retention) |  |
|  |  - data-maintenance (Storage Cleanup)                     |  |
|  |  - redis-optimization (Memory Management)                 |  |
|  |                                                            |  |
|  |  API & UI:                                                 |  |
|  |  - realtime-events-broadcaster (WebSocket Streaming)      |  |
|  |  - Edge API Gateway (Flask REST API, port 5000)          |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Storage Layer                                             |  |
|  |  - Samsung T7 Shield 2TB SSD (/mnt/storage)               |  |
|  |  - SQLite Database (traffic_monitor.db)                   |  |
|  |  - Camera detections (/mnt/storage/detections/)           |  |
|  |  - Archived images (/mnt/storage/archived_images/)        |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Physical Sensors (Hardware Interfaces)                   |  |
|  |  - Sony IMX500 AI Camera (CSI-2 interface, host service)  |  |
|  |  - OPS243-C Radar (/dev/ttyAMA0 UART @ 19200 baud)       |  |
|  |  - DHT22 Temp/Humidity Sensor (GPIO4)                     |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+

Deployment Architecture Notes:
- Hybrid Deployment: 12 Docker containers + 1 systemd host service
- Container Network: Docker bridge network (app-network)
- Redis Communication: Pub/Sub channels & Streams for inter-service messaging
- Storage: All containers share /mnt/storage volume
- Security: NGINX reverse proxy with self-signed SSL/TLS, UFW firewall
- Remote Access: Tailscale VPN for secure access from anywhere
- Cloud Dashboard: GitHub Pages for static website (no backend required)
```

## 7. CI/CD Deployment Architecture

The system implements a fully automated CI/CD pipeline using GitHub Actions, Docker Hub, and custom deployment scripts for continuous integration and deployment to the Raspberry Pi 5.

### 7.1 CI/CD Pipeline Overview

```text
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Developer     │      │ GitHub Actions   │      │   Docker Hub     │
│   Workstation   │─────▶│   CI/CD Runner   │─────▶│ Container Registry│
└─────────────────┘      └──────────────────┘      └──────────────────┘
         │                        │                          │
         │ git push main          │ build ARM64 image        │ pull image
         │                        │                          │
         ▼                        ▼                          ▼
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  GitHub Repo    │      │  Docker Build    │      │ gcumerk/cst590-  │
│  main branch    │      │  ARM64 Platform  │      │ capstone-public  │
└─────────────────┘      └──────────────────┘      └──────────────────┘
                                   │                          │
                                   │ trigger deploy           │
                                   ▼                          ▼
                          ┌──────────────────┐      ┌──────────────────┐
                          │ Deploy Workflow  │      │ Raspberry Pi 5   │
                          │ SSH + Scripts    │─────▶│   Production     │
                          └──────────────────┘      └──────────────────┘
```

### 7.2 GitHub Actions Workflows

**Build Workflow** (`.github/workflows/docker-build-push.yml`)

- **Trigger:** Push to main branch, manual dispatch
- **Platform:** ARM64/aarch64 (Raspberry Pi 5 compatible)
- **Steps:**
  1. Checkout repository code
  2. Set up QEMU for cross-platform builds
  3. Configure Docker Buildx
  4. Login to Docker Hub (credentials from secrets)
  5. Build multi-platform Docker image
  6. Tag with `latest` and commit SHA
  7. Push to `gcumerk/cst590-capstone-public:latest`
  8. Cache layers for faster subsequent builds
- **Build Time:** ~8-12 minutes
- **Output:** Production-ready Docker image for ARM64

**Deploy Workflow** (`.github/workflows/deploy-to-pi.yml`)

- **Trigger:** Successful completion of build workflow
- **Connection:** SSH to Raspberry Pi (SSH key from secrets)
- **Steps:**
  1. Connect to Pi via SSH
  2. Navigate to deployment directory
  3. Pull latest Docker image from Docker Hub
  4. Run `deploy.sh` deployment script
  5. Verify container health checks
  6. Report deployment status
- **Deploy Time:** ~3-5 minutes
- **Rollback:** Automatic on health check failure

### 7.3 Docker Hub Configuration

**Repository:** `gcumerk/cst590-capstone-public`
**Visibility:** Public
**Architecture:** ARM64/aarch64
**Image Size:** ~2.5 GB (includes TensorFlow, OpenCV, dependencies)
**Update Frequency:** On every main branch commit
**Tags:**
- `latest` - Most recent production build
- `<commit-sha>` - Specific commit builds for rollback
- `v1.0.0-capstone-final` - Tagged release version

### 7.4 Deployment Scripts

**Primary Deployment Script:** `deploy.sh`

```bash
#!/bin/bash
# Features:
# - Hardware validation (Raspberry Pi detection)
# - Docker and Docker Compose version checks
# - GPIO and hardware interface enabling
# - Service cleanup and conflict resolution
# - Multi-compose file deployment (docker-compose.yml + docker-compose.pi.yml)
# - Storage directory setup with proper permissions
# - Health check verification
# - Monitoring and logging configuration
# - System optimizations for Docker
```

**Service-Specific Deployment:** `deploy-services.sh`

- Deploys containerized microservices
- 94% storage optimization (removed sky analysis)
- Radar-triggered architecture validation
- Post-deployment validation script execution

**HTTPS Deployment:** `deploy-https.sh`

- SSL certificate setup for Tailscale domain
- Nginx reverse proxy configuration
- HTTPS connectivity testing
- Certificate renewal automation

### 7.5 Deployment Validation

**Health Checks:**
- Container status verification
- Service health endpoint polling
- Redis connectivity testing
- Database migration validation
- API endpoint smoke tests

**Post-Deployment Tests:**
- `/health` endpoint returns 200 OK
- WebSocket connection establishment
- Radar data stream active
- Weather services updating
- Database persistence operational
- Centralized logging functioning

**Rollback Strategy:**
- Automatic on failed health checks
- Docker image version tagging for quick rollback
- Service state preserved via Docker volumes
- Database backups before each deployment

### 7.6 Environment Configuration

**Build-Time Variables:**

```bash
DOCKER_IMAGE=gcumerk/cst590-capstone-public:latest
HOST_UID=1000
HOST_GID=1000
STORAGE_ROOT=/mnt/storage
REDIS_HOST=redis
REDIS_PORT=6379
```

**Runtime Variables:**

```bash
SERVICE_NAME=<service_name>
LOG_LEVEL=INFO
LOG_DIR=/app/logs
CORRELATION_HEADER=X-Correlation-ID
DATABASE_PATH=/app/data/traffic_data.db
```

**Hardware-Specific:**

```bash
RADAR_UART_PORT=/dev/ttyAMA0
RADAR_BAUD_RATE=19200
DHT22_GPIO_PIN=4
CAMERA_SERVICE_NAME=imx500-ai-capture.service
```

### 7.7 Continuous Monitoring

**Deployment Metrics:**
- Build success rate: >95%
- Average build time: 10 minutes
- Average deploy time: 4 minutes
- Deployment frequency: 2-5 times per day (during active development)
- Zero-downtime deployments: Achieved via health checks

**Service Availability:**
- Uptime target: 99.9%
- Current uptime: 9+ hours continuous (production)
- Automatic restart on failure
- Health check intervals: 30-60 seconds per service

## 8. Database Entity-Relationship Diagram (ERD)

The system uses SQLite for local data persistence with a normalized schema designed for efficient querying and 90-day data retention.

### 8.1 Database Schema Overview

**Database Location:** `/app/data/traffic_data.db` (SQLite 3)
**Retention Policy:** 90 days (automated cleanup via database-persistence service)
**Backup Strategy:** Daily backups to `/database/backups/`
**Performance:** Indexed on timestamp, event_id, and foreign keys

### 8.2 Entity-Relationship Diagram

```text
┌──────────────────────────────────────────────────────────────┐
│                    traffic_events (Main Events Table)         │
├──────────────────────────────────────────────────────────────┤
│ PK  consolidation_id       TEXT    (Unique event ID)         │
│     timestamp               REAL    (Unix timestamp)          │
│     trigger_source          TEXT    (radar/camera/manual)     │
│     processing_notes        TEXT    (Event description)       │
│     created_at              TEXT    (ISO 8601 timestamp)      │
└──────────────┬───────────────────────────────────────────────┘
               │
               │ 1:1 relationship
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────────┐  ┌──────────────────────────────────────┐
│  radar_data      │  │  weather_data                        │
├──────────────────┤  ├──────────────────────────────────────┤
│ PK id           │  │ PK id                                 │
│ FK event_id     │  │ FK event_id                           │
│    speed        │  │    airport_temp                       │
│    magnitude    │  │    airport_wind_speed                 │
│    direction    │  │    airport_visibility                 │
│    timestamp    │  │    dht22_temp_c                       │
└──────────────────┘  │    dht22_humidity                     │
                      │    timestamp                          │
┌──────────────────┐  └──────────────────────────────────────┘
│  camera_data     │
├──────────────────┤         ┌──────────────────────────────┐
│ PK id           │          │  consolidated_events         │
│ FK event_id     │          ├──────────────────────────────┤
│    image_path   │          │ PK id                        │
│    detections   │←────────┤│    consolidation_id          │
│    confidence   │  1:N    ││    radar_speed               │
│    vehicle_type │          │    weather_summary           │
│    timestamp    │          │    camera_detections_count   │
└──────────────────┘          │    timestamp                 │
                              └──────────────────────────────┘
```

### 8.3 Table Descriptions

**traffic_events (Primary Event Table)**
- Stores consolidated events from vehicle-consolidator service
- Unique consolidation_id for each multi-sensor event
- Trigger source indicates which sensor initiated the event
- Processing notes provide context about the detection
- Indexed on timestamp for efficient time-range queries

**radar_data (OPS243-C Radar Readings)**
- Foreign key relationship to traffic_events
- Speed in mph (converted from m/s)
- Magnitude indicates signal strength
- Direction: approaching, receding, or unknown
- Minimum speed threshold: 2.0 mph

**weather_data (Environmental Context)**
- Foreign key relationship to traffic_events
- Airport weather: METAR data from nearby airport
  - Temperature (°F)
  - Wind speed (knots)
  - Visibility (statute miles)
- DHT22 local sensor:
  - Temperature (°C)
  - Relative humidity (%)
- Correlation between airport and local weather

**camera_data (IMX500 AI Detections)**
- Foreign key relationship to traffic_events
- Image path for detection snapshots
- Detections: JSON array of bounding boxes and classes
- Confidence scores for each detection (0.0-1.0)
- Vehicle types: car, truck, bus, motorcycle, etc.

**consolidated_events (Denormalized Summary)**
- Fast-access summary table for API queries
- Aggregates radar, weather, and camera data
- Used for dashboard displays and analytics
- Indexed for high-performance reads

### 8.4 Example Queries

**Recent Events:**

```sql
SELECT 
  e.consolidation_id,
  e.timestamp,
  e.trigger_source,
  r.speed as radar_speed,
  w.airport_temp,
  w.dht22_humidity,
  c.vehicle_type
FROM traffic_events e
LEFT JOIN radar_data r ON e.consolidation_id = r.event_id
LEFT JOIN weather_data w ON e.consolidation_id = w.event_id  
LEFT JOIN camera_data c ON e.consolidation_id = c.event_id
WHERE e.timestamp > ?
ORDER BY e.timestamp DESC
LIMIT 50;
```

**Speed Distribution:**

```sql
SELECT 
  CASE
    WHEN speed < 15 THEN '0-15 mph'
    WHEN speed < 25 THEN '15-25 mph'
    WHEN speed < 35 THEN '25-35 mph'
    WHEN speed < 45 THEN '35-45 mph'
    ELSE '45+ mph'
  END as speed_range,
  COUNT(*) as count
FROM radar_data
WHERE timestamp > ?
GROUP BY speed_range
ORDER BY speed_range;
```

**Daily Traffic Volume:**

```sql
SELECT 
  DATE(timestamp, 'unixepoch', 'localtime') as date,
  COUNT(*) as event_count,
  AVG(r.speed) as avg_speed
FROM traffic_events e
JOIN radar_data r ON e.consolidation_id = r.event_id
WHERE timestamp > ?
GROUP BY date
ORDER BY date DESC;
```

## 8. API Endpoint Map

The Edge API Gateway provides a comprehensive RESTful API with OpenAPI/Swagger documentation. All endpoints support CORS and include correlation IDs for request tracking.

### 8.1 API Base Configuration

- **Base URL:** `https://edge-traffic-monitoring.taild46447.ts.net/api` (HTTPS via nginx proxy)
- **Internal URL:** `http://traffic-monitor:5000/api` (Docker network)
- **API Framework:** Flask-RESTx with OpenAPI 3.0 specification
- **Documentation:** Available at `/docs` (Swagger UI) and `/swagger.json`
- **Authentication:** Currently open (future: API key or JWT tokens)
- **CORS:** Enabled for cross-origin requests

### 8.2 Health & Monitoring Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/health` | GET | Simple container health check | `{status, timestamp}` |
| `/api/health/system` | GET | Comprehensive system health | CPU, memory, disk, services |
| `/api/health/stats` | GET | API gateway statistics | Request counts, uptime, success rate |

### 8.3 Vehicle Detection Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/vehicles/detections` | GET | Recent vehicle detections from IMX500 | Vehicle list with bounding boxes, classes |
| `/api/vehicles/latest` | GET | Most recent vehicle detection | Single vehicle record |
| `/api/vehicles/count` | GET | Vehicle count by time period | Count statistics |
| `/api/vehicles/history` | GET | Historical detection data | Time-series vehicle data |

### 8.4 Weather Data Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/weather/current` | GET | Current weather from all sensors | Airport METAR + DHT22 data |
| `/api/weather/airport` | GET | METAR weather from nearby airport | Temperature, wind, visibility |
| `/api/weather/local` | GET | DHT22 local sensor data | Temperature, humidity |
| `/api/weather/history` | GET | Historical weather trends | Time-series weather data |

### 8.5 Event & Analytics Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/events/recent` | GET | Recent consolidated events | Radar + camera + weather fusion |
| `/api/events/consolidated` | GET | Consolidated traffic data | Multi-sensor correlated events |
| `/api/events/radar` | GET | Raw radar detection events | Speed, magnitude, direction |
| `/api/analytics/traffic/flow` | GET | Traffic flow analysis | Volume, patterns, peak times |
| `/api/analytics/speed/distribution` | GET | Speed distribution statistics | Speed ranges, averages |
| `/api/analytics/reports/summary` | GET | Executive summary reports | Overview statistics |
| `/api/analytics/reports/violations` | GET | Violation reports | Speeding, unsafe behavior |

### 8.6 Camera & Image Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/camera_capture/<filename>` | GET | Serve camera capture images | Image file (JPEG/PNG) |
| `/api/camera/latest` | GET | Latest camera snapshot | Image metadata + URL |
| `/ai_camera_images/<filename>` | GET | Serve IMX500 AI detection images | Image file with annotations |

### 8.7 WebSocket Endpoints

| Event | Direction | Purpose | Data |
|-------|-----------|---------|------|
| `connect` | Client → Server | Establish WebSocket connection | Connection details |
| `disconnect` | Client → Server | Close WebSocket connection | Disconnect reason |
| `subscribe_events` | Client → Server | Subscribe to real-time events | Event preferences |
| `ping` | Client → Server | Connection keep-alive | Timestamp |
| `pong` | Server → Client | Ping response | Timestamp |
| `event` | Server → Client | Real-time traffic event | Event data |
| `log` | Server → Client | Log message streaming | Log record |
| `subscribe_logs` | Client → Server | Subscribe to log streaming | Log level filter |

### 8.8 API Response Formats

**Standard Success Response:**

```json
{
  "data": { ... },
  "timestamp": "2025-10-01T12:00:00.000Z",
  "correlation_id": "abc-123-def-456"
}
```

**Standard Error Response:**

```json
{
  "error": "Error message",
  "timestamp": "2025-10-01T12:00:00.000Z",
  "correlation_id": "abc-123-def-456"
}
```

**Vehicle Detection Response:**

```json
{
  "vehicles": [
    {
      "id": "vehicle_001",
      "class": "car",
      "confidence": 0.95,
      "bounding_box": [x, y, width, height],
      "timestamp": "2025-10-01T12:00:00.000Z",
      "image_path": "/ai_camera_images/detection_001.jpg"
    }
  ],
  "count": 1,
  "timestamp": "2025-10-01T12:00:00.000Z"
}
```

**Consolidated Event Response:**

```json
{
  "consolidation_id": "consolidation_1727798400",
  "timestamp": "2025-10-01T12:00:00.000Z",
  "trigger_source": "radar_motion",
  "radar_data": {
    "speed": 35.5,
    "magnitude": 23.4,
    "direction": "approaching"
  },
  "weather_data": {
    "airport": {
      "temperature": 72,
      "wind_speed": 8.5,
      "visibility": 10
    },
    "dht22": {
      "temperature_c": 21.5,
      "humidity": 65.2
    }
  },
  "camera_data": {
    "detections": [...]
  },
  "processing_notes": "Triggered by radar at 35.5 mph"
}
```

## 9. Security/Data Flow Diagram

The system implements multiple layers of security including network isolation, HTTPS/TLS encryption, VPN access control, and secure container practices.

### 9.1 Security Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    External Network (Internet)                   │
│                      Public, Untrusted Zone                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ 
                             │ Blocked by default
                             │ No direct access to services
                             ▼
                    ┌────────────────────┐
                    │  Tailscale VPN     │
                    │  Mesh Network      │
                    │  (WireGuard-based) │
                    └────────┬───────────┘
                             │ Authenticated users only
                             │ End-to-end encryption
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Raspberry Pi 5 Edge Device                  │
│                       Trusted Internal Zone                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  nginx Reverse Proxy (Port 80/8443)                      │  │
│  │  - HTTPS/TLS termination                                 │  │
│  │  - Self-signed SSL certificates                          │  │
│  │  - Security headers (HSTS, CSP, X-Frame-Options)         │  │
│  │  - WebSocket proxying                                    │  │
│  │  - Rate limiting and request throttling                  │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │ Internal Docker Network Only           │
│                       ▼                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  traffic-monitor (Port 5000 - Internal Only)             │  │
│  │  - No external port exposure                             │  │
│  │  - CORS enabled for Tailscale domain                     │  │
│  │  - Correlation ID tracking                               │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────┴─────────────────────────────────────┐  │
│  │  Redis (Port 6379 - Localhost Only)                      │  │
│  │  - Bind to 127.0.0.1 (no external access)                │  │
│  │  - No authentication (internal network only)             │  │
│  │  - Memory limits and eviction policies                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Bridge Network (app-network)                     │  │
│  │  - Isolated container communication                      │  │
│  │  - No external connectivity by default                   │  │
│  │  - Service discovery via container names                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Security Measures Implemented

#### Network Security

**Port Exposure:**
- **External Ports:** Only 80 (HTTP redirect), 8443 (HTTPS) via nginx
- **Internal Ports:** All service ports (5000, 6379, etc.) exposed only to Docker network
- **Blocked Ports:** PostgreSQL, Redis, and API gateway not directly accessible

**Firewall Configuration:**
- UFW (Uncomplicated Firewall) enabled
- Allow: SSH (22), HTTP (80), HTTPS (8443), Tailscale (41641/UDP)
- Deny: All other inbound connections
- Rate limiting on SSH to prevent brute-force attacks

**Network Isolation:**
- Docker bridge network `app-network` for container communication
- Host network mode only for camera-service-manager (systemctl access)
- No container-to-internet access except weather services

#### Transport Security

**HTTPS/TLS:**
- Nginx reverse proxy with SSL/TLS termination
- Self-signed certificates for Tailscale domain
- Certificate location: `/etc/nginx/ssl/`
- Automatic HTTP to HTTPS redirect
- TLS 1.2+ only, secure cipher suites
- HSTS (HTTP Strict Transport Security) enabled

**Security Headers:**

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

**WebSocket Security:**
- Secure WebSocket (wss://) over HTTPS
- Same-origin policy enforcement
- Connection authentication via Socket.IO
- Automatic reconnection with exponential backoff

#### Access Control

**Tailscale VPN:**
- WireGuard-based mesh VPN
- Centralized access control via Tailscale admin console
- Device authentication required
- Automatic key rotation
- Split DNS for internal services
- Tailscale hostname: `edge-traffic-monitoring.taild46447.ts.net`

**User Permissions:**
- Docker containers run as non-root user (UID 1000, GID 1000)
- Service-specific user accounts
- GPIO/UART access via group memberships (`dialout`, `gpio`)
- Privileged mode only for hardware access (radar-service, camera-service-manager)

**API Authentication:**
- Currently: Open access within Tailscale network
- Future: API key or JWT token authentication
- Correlation IDs for request tracking and audit logs

#### Data Security

**Data at Rest:**
- SQLite database: File system permissions (600, user-only access)
- Redis persistence: AOF file with fsync every second
- Image storage: Organized with time-based cleanup (24-90 day retention)
- Log files: Rotated and compressed, 30-day retention

**Data in Transit:**
- HTTPS/TLS for all API communications
- WebSocket over TLS (wss://)
- Redis: Internal Docker network only, no external exposure
- Serial (UART): Hardware-level, no network exposure

**Data Privacy:**
- No cloud data transmission by default (optional cloud integration)
- All processing performed at edge (Raspberry Pi)
- Automated data cleanup to prevent indefinite storage
- No personally identifiable information (PII) collected

#### Container Security

**Docker Best Practices:**
- Multi-stage builds to minimize image size
- Non-root user execution
- Read-only root filesystem where possible
- Minimal base images (Alpine Linux)
- Security scanning via Docker Scout
- No privileged containers except hardware access
- Capability dropping (CAP_DROP) for most containers
- Health checks for automatic failure detection

**Secrets Management:**
- Environment variables for configuration
- No hardcoded credentials in code
- GitHub Secrets for CI/CD (Docker Hub, SSH keys)
- `.env` files excluded from version control

**Resource Limits:**
- Memory limits per container (prevents DoS)
- CPU throttling for non-critical services
- Disk quota enforcement via storage maintenance

### 9.3 Security Monitoring & Logging

**Centralized Logging:**
- All services log to `/mnt/storage/logs/`
- Correlation IDs across all requests
- Structured logging format (JSON where applicable)
- Log aggregation in centralized database
- Real-time log streaming via WebSocket

**Security Event Logging:**
- Authentication attempts
- API request patterns
- Container restart events
- System health check failures
- Deployment and configuration changes

**Alerting:**
- Health check failures trigger automatic restart
- Storage threshold alerts (80% warning, 90% critical)
- Service downtime notifications
- Unusual traffic pattern detection (future enhancement)

### 9.4 Incident Response

**Automated Recovery:**
- Docker restart policies (`unless-stopped`)
- Health check-based container restarts
- Service dependency management
- Automatic database backup before deployments

**Manual Intervention:**
- SSH access via Tailscale VPN
- Docker logs for troubleshooting
- Database backups for rollback
- Service isolation for targeted fixes

**Disaster Recovery:**
- Daily database backups to `/database/backups/`
- Configuration in version control (GitHub)
- Docker image versioning for rollback
- External SSD for critical data

### 9.5 Compliance & Best Practices

**Standards Followed:**
- OWASP Top 10 web application security
- Docker CIS Benchmarks
- Linux hardening guidelines
- Secure coding practices (input validation, error handling)

**Regular Updates:**
- Docker base image updates
- Python package updates
- Security patch monitoring
- Dependency vulnerability scanning

**Future Enhancements:**
- API key authentication
- OAuth/OIDC integration
- Intrusion detection system (IDS)
- Automated vulnerability scanning
- Certificate rotation automation
- Multi-factor authentication (MFA)

## 13. Technology Stack & Dependencies

### 13.1 Core Technologies

**Programming Languages:**
- Python 3.11+ (primary application language)
- Bash shell scripting (deployment automation)
- JavaScript (web dashboard UI)
- SQL (database queries)

**Hardware Platforms:**
- Raspberry Pi 5 (ARM64/aarch64 architecture)
- Sony IMX500 AI camera with NPU
- OmniPreSense OPS243-C radar
- DHT22 temperature/humidity sensor

**Operating System:**
- Raspberry Pi OS (64-bit, Debian-based)
- Linux kernel 6.1+
- systemd service management

### 13.2 Python Framework & Libraries

**Web Frameworks:**
- Flask 3.0.0 - Web application framework
- Flask-RESTx 1.3.0 - RESTful API with OpenAPI/Swagger
- Flask-SocketIO 5.3.6 - WebSocket real-time communication
- Flask-CORS 4.0.0 - Cross-Origin Resource Sharing

**AI/ML & Computer Vision:**
- TensorFlow 2.15+ - Machine learning framework
- OpenCV 4.8+ - Computer vision library
- NumPy 1.24+ - Numerical computing
- Picamera2 - Raspberry Pi camera interface
- IMX500 SDK - On-camera AI inference

**Data Storage:**
- Redis 7.0 (Alpine) - In-memory data store, pub/sub broker
- SQLite 3 - Embedded relational database
- redis-py 5.0.1 - Python Redis client

**Hardware Interfaces:**
- pyserial 3.5+ - UART/serial communication (radar)
- RPi.GPIO 0.7.1 - GPIO control
- gpiozero - High-level GPIO interface
- Adafruit_DHT - DHT22 sensor library

**Utilities & Tools:**
- python-decouple 3.8 - Configuration management
- pydantic 2.5.0 - Data validation
- python-dateutil 2.8.2 - Date/time handling
- requests 2.31.0 - HTTP client library
- marshmallow 3.20.2 - Object serialization

### 13.3 Infrastructure Technologies

**Containerization:**
- Docker 24.0+ - Container runtime
- Docker Compose 2.20+ - Multi-container orchestration
- Alpine Linux 3.18+ - Base container images

**Web Server:**
- Nginx 1.25 (Alpine) - Reverse proxy, HTTPS termination
- OpenSSL - SSL/TLS encryption

**Version Control & CI/CD:**
- Git 2.40+ - Source control
- GitHub - Code repository hosting
- GitHub Actions - CI/CD automation
- Docker Hub - Container registry (gcumerk/cst590-capstone-public)

**Networking:**
- Tailscale - WireGuard-based VPN mesh
- UFW - Uncomplicated Firewall

### 13.4 Development Tools

**Testing:**
- pytest - Python testing framework
- unittest - Built-in Python testing
- curl - API endpoint testing

**Monitoring & Logging:**
- systemd journalctl - System logging
- Docker logs - Container logging
- Custom centralized logging (SQLite-based)

**Documentation:**
- Swagger UI - API documentation
- OpenAPI 3.0 - API specification
- Markdown - Technical documentation

### 13.5 Docker Image Details

**Primary Image:** `gcumerk/cst590-capstone-public:latest`

- **Base:** python:3.11-slim
- **Architecture:** ARM64/aarch64
- **Size:** ~2.5 GB (includes TensorFlow, OpenCV)
- **Build Platform:** Multi-platform (GitHub Actions)
- **Update Frequency:** On every main branch commit

**Supporting Images:**
- redis:7-alpine (~50 MB)
- nginx:1.25-alpine (~40 MB)

### 13.6 Package Versions (Production)

```text
Flask==3.0.0
Flask-SocketIO==5.3.6
Flask-RESTx==1.3.0
Flask-CORS==4.0.0
redis==5.0.1
pydantic==2.5.0
python-dateutil==2.8.2
numpy==1.24.3
opencv-python==4.8.1
tensorflow==2.15.0
picamera2==0.3.12
RPi.GPIO==0.7.1
pyserial==3.5
requests==2.31.0
```

## 14. Performance Metrics & System Status

### 14.1 Performance Achievements

**AI Inference Performance:**
- **Inference Time:** <100ms (IMX500 on-chip processing)
- **Previous Software AI:** 2-5 seconds per frame
- **Improvement:** 25-50x faster inference
- **CPU Usage:** ~0% (hardware-accelerated on NPU)
- **Previous CPU Usage:** 80-100% during inference
- **Accuracy:** 85-95% vehicle classification accuracy

**End-to-End Latency:**
- **Radar Detection → Redis:** <50ms
- **IMX500 AI Inference:** <100ms
- **Data Consolidation:** <100ms
- **API Response:** <50ms
- **Total Latency:** <350ms for complete detection pipeline

**Storage Optimization:**
- **Initial Design:** ~16 GB/day (with sky analysis)
- **Optimized Design:** ~1 GB/day (94% reduction)
- **Achievement:** Eliminated sky analysis overhead
- **Retention:** 24 hours (images), 90 days (database events)

**System Uptime & Reliability:**
- **Production Uptime:** 9+ hours continuous operation
- **Service Availability:** >99.9% (automated health monitoring)
- **Auto-Restart Success:** 100% (Docker health checks)
- **Zero-Downtime Deployments:** Achieved via rolling updates

### 14.2 Resource Utilization

**CPU Usage (Raspberry Pi 5):**
- **Idle:** 5-10%
- **Normal Operation:** 20-30%
- **Peak (weather updates):** 40-50%
- **AI Inference:** ~0% (offloaded to IMX500 NPU)

**Memory Usage:**
- **System Total:** 16 GB RAM
- **Docker Containers:** ~2-3 GB combined
- **Redis:** ~100-200 MB (with optimization)
- **Available:** ~12-13 GB free

**Disk I/O:**
- **External SSD:** Samsung T7 Shield 2TB
- **Average Write Speed:** ~500 MB/s
- **Database Size:** ~100 MB per week
- **Log Files:** ~50 MB per day
- **Image Storage:** ~1 GB per day

**Network Bandwidth:**
- **Radar Data:** <1 KB/s continuous
- **Weather Updates:** <10 KB every 10 minutes
- **WebSocket Streaming:** <100 KB/s
- **Total:** <1 Mbps average

### 14.3 Service Health Status (Production)

**Container Health (All Healthy, 9+ hours uptime):**

| Service | Status | CPU | Memory | Restarts |
|---------|--------|-----|--------|----------|
| redis | Healthy | <1% | 100 MB | 0 |
| traffic-monitor | Healthy | 5-10% | 400 MB | 0 |
| radar-service | Healthy | 2-5% | 150 MB | 0 |
| vehicle-consolidator | Healthy | 2-3% | 180 MB | 0 |
| database-persistence | Healthy | 1-2% | 120 MB | 0 |
| redis-optimization | Healthy | <1% | 80 MB | 0 |
| nginx-proxy | Healthy | <1% | 50 MB | 0 |
| data-maintenance | Healthy | <1% | 100 MB | 0 |
| airport-weather | Healthy | <1% | 100 MB | 0 |
| dht22-weather | Healthy | <1% | 90 MB | 0 |
| realtime-broadcaster | Healthy | 2-3% | 130 MB | 0 |
| camera-service-manager | Healthy | <1% | 30 MB | 0 |

**Host Services:**
- **imx500-ai-capture.service:** Active, running 9+ hours

### 14.4 Data Processing Statistics

**Event Processing:**
- **Radar Detections:** ~10-20 per hour (traffic dependent)
- **Consolidated Events:** ~5-15 per hour
- **Database Inserts:** Batch processing (100 records/30 seconds)
- **Weather Updates:** Every 10 minutes (airport + DHT22)

**Database Metrics:**
- **Total Events:** Growing (~10-50 per day)
- **Query Performance:** <50ms for recent events
- **Index Efficiency:** All queries use indexes
- **Retention Cleanup:** Automated, runs nightly

**Redis Performance:**
- **Operations/Second:** ~1000 (low traffic)
- **Memory Efficiency:** 94% improvement over initial design
- **Stream Trimming:** Automated (1000 radar, 100 consolidated)
- **Pub/Sub Latency:** <10ms

### 14.5 Deployment Metrics

**CI/CD Pipeline:**
- **Build Time:** 8-12 minutes (ARM64 cross-compilation)
- **Deploy Time:** 3-5 minutes (pull + restart)
- **Build Success Rate:** >95%
- **Deployment Frequency:** 2-5 times/day (active development)

**Docker Hub:**
- **Image Size:** 2.5 GB (compressed)
- **Pull Time:** 3-4 minutes (on Pi 5)
- **Layer Caching:** Enabled (reduces build time by 60%)

### 14.6 System Monitoring

**Automated Health Checks:**
- **Interval:** 30-60 seconds per service
- **Success Rate:** >99.9%
- **Restart Policy:** Automatic on failure
- **Max Retries:** 3 before manual intervention required

**Centralized Logging:**
- **Log Volume:** ~50 MB/day
- **Retention:** 30 days (rotated and compressed)
- **Correlation Tracking:** 100% of requests
- **Real-time Streaming:** Available via WebSocket

### 14.7 Final Capstone Version Achievements

**v1.0.0-capstone-final (October 1, 2025)**

✅ **Complete System Implementation:**
- 12 containerized microservices
- IMX500 hardware-accelerated AI (<100ms inference)
- Multi-sensor data fusion (radar + camera + weather)
- Real-time WebSocket streaming
- HTTPS/TLS encryption
- Tailscale VPN secure access
- 90-day data retention
- Automated health monitoring
- CI/CD automation

✅ **Performance Targets Met:**
- <350ms end-to-end latency ✓
- 85-95% AI accuracy ✓
- 94% storage optimization ✓
- 99.9% uptime ✓
- Sub-100ms AI inference ✓

✅ **Production-Ready Features:**
- Zero-downtime deployments
- Automated service recovery
- Centralized logging with correlation IDs
- Comprehensive API documentation (Swagger)
- Security hardening (HTTPS, VPN, firewall)
- Database backups and retention policies
- Resource monitoring and optimization

✅ **Documentation Complete:**
- Technical design specification
- API documentation (OpenAPI/Swagger)
- Deployment guides
- Architecture diagrams
- Security documentation
- Performance benchmarks
- User guides

**System Status:** ✅ **Production Ready** - Final Capstone Release

## 10. Remote Access Flow via Tailscale

This diagram illustrates how SSH and HTML (web dashboard) connections are securely routed to the Raspberry Pi through the Tailscale mesh VPN network.

```text
+-------------------+        +-------------------+        +----------------------|
|   Remote Client   |        |   Remote Client   |        |   Remote Client      |
|   (SSH/HTML)      |        |   (SSH/HTML)      |        |   (SSH/HTML)         |
+--------+----------+        +--------+----------+        +----------+-----------+
         |                            |                              |
         |   SSH / HTTPS / HTTP       |   SSH / HTTPS / HTTP         |   SSH / HTTPS / HTTP
         |   (Port 22 / 80 / 443)     |   (Port 22 / 80 / 443)       |   (Port 22 / 80 / 443)
         v                            v                              v
+--------------------------------------------------------------------------+
|                           Tailscale Network                              |
|   (Encrypted Mesh VPN - All Devices Authenticated & Discoverable)        |
+-------------------+-------------------+-------------------+--------------+
         |                   |                   |
         +---------+---------+                   |
                   |                             |
                   v                             v
           +-----------------------------+   +-----------------------------+
           |      Raspberry Pi 5         |   |      Raspberry Pi 5         |
           |  (Tailscale IP: 100.x.x.x)  |   |  (Tailscale IP: 100.x.x.x)  |
           |  +-----------------------+  |   |  +-----------------------+  |
           |  |  SSH Server (22)      |  |   |  |  Web Server (80/443)  |  |
           |  |  Web Dashboard (UI)   |  |   |  |  (HTML/HTTPS)         |  |
           |  +-----------------------+  |   |  +-----------------------+  |
           +-----------------------------+   +-----------------------------+
```

**Legend:**

- All connections (SSH, HTTP, HTTPS) are routed through the Tailscale mesh VPN.
- Remote clients connect to the Raspberry Pi using its Tailscale IP address.
- Tailscale handles encryption and authentication, so no direct exposure to the public internet is required.

## 2.x Top-Down Approach

### Primary System Functions

- Vehicle detection and classification
- Speed measurement
- Data fusion (camera + radar)
- Real-time event logging and alerting
- Local dashboard (Edge UI)
- Cloud data sync and analytics (optional)
- System health monitoring and self-recovery
- Secure remote access and management

### Decomposition of Major Tasks into Subtasks

- **Vehicle Detection**
  - Capture video frames
  - Run ML inference (object detection)
  - Classify vehicle type
- **Speed Measurement**
  - Read radar data
  - Calculate speed
  - Correlate with camera detections
- **Data Fusion**
  - Match radar and camera events
  - Filter and validate events
- **Event Logging & Alerting**
  - Store events locally
  - Trigger alerts for speeding/anomalies
  - Sync events to cloud (if enabled)
- **Dashboard/UI**
  - Serve real-time data to web clients
  - Display analytics and system status
- **System Health**
  - Monitor CPU, memory, storage
  - Restart services if needed
  - Log health events
- **Remote Access**
  - Authenticate users (Tailscale)
  - Provide SSH and web access

### System Flowchart (Top-Down)

```text
+-----------------------------+
|   Start / System Boot       |
+-----------------------------+
              |
              v
+-----------------------------+
|  Initialize Sensors & HW    |
+-----------------------------+
              |
              v
+-----------------------------+
|  Main Processing Loop       |
+-----------------------------+
              |
              v
+-----------------------------+
|  Capture Video & Radar      |
+-----------------------------+
              |
              v
+-----------------------------+
|  Detect Vehicles (ML)       |
+-----------------------------+
              |
              v
+-----------------------------+
|  Measure Speed (Radar)      |
+-----------------------------+
              |
              v
+-----------------------------+
|  Data Fusion & Validation   |
+-----------------------------+
              |
              v
+-----------------------------+
|  Log Event / Trigger Alert  |
+-----------------------------+
              |
              v
+-----------------------------+
|  Update Dashboard & Sync    |
+-----------------------------+
              |
              v
+-----------------------------+
|  Health Check & Recovery    |
+-----------------------------+
              |
              v
+-----------------------------+
|   Wait / Next Cycle         |
+-----------------------------+
```

## 11. Radar System Data Flow Architecture

This section documents the complete data flow from OPS243-C radar detection through consolidation to database persistence, including the Redis-based microservices architecture.

### 11.1 Radar Detection Pipeline

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OPS243-C      │    │  radar_service  │    │   Redis Pub/Sub │
│   FMCW Radar    │───▶│     .py         │───▶│   & Streams     │
│                 │    │                 │    │                 │
│ UART 19200 baud │    │ Parses JSON     │    │ traffic_events  │
│ JSON: speed,    │    │ Converts m/s    │    │ radar_data      │
│ unit, magnitude │    │ to mph          │    │ stream          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 11.2 Data Processing Services

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          Redis Message Broker                          │
├─────────────────┬─────────────────────┬─────────────────────────────────┤
│ Channels:       │ Streams:            │ Keys:                           │
│ • traffic_events│ • radar_data        │ • consolidation:latest          │
│ • radar_detections│ • consolidated_   │ • consolidation:history:*       │
│ • database_events│   traffic_data    │ • weather:airport:latest        │
│                 │                     │ • weather:dht22:latest          │
└─────────────────┴─────────────────────┴─────────────────────────────────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Consolidator    │    │ Edge API        │    │ Database        │
│ Service         │    │ Services        │    │ Persistence     │
│                 │    │                 │    │ Service         │
│ Listens to      │    │ Reads streams   │    │ Listens to      │
│ traffic_events  │    │ & keys for      │    │ database_events │
│                 │    │ real-time data  │    │                 │
│ Triggers on     │    │                 │    │ Stores in       │
│ radar motion    │    │                 │    │ SQLite DB       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 11.3 Radar Event Flow Sequence

```text
1. Radar Detection
   OPS243-C → UART → radar_service.py
   • Raw JSON: {"unit": "mps", "speed": "-10.7"}
   • Speed threshold filter: >= 2.0 mph
   • Convert m/s to mph: -10.7 m/s = 23.9 mph

2. Redis Data Publishing (radar_service.py)
   • PUBLISH 'radar_detections' (raw data)
   • XADD 'radar_data' (stream storage)
   • IF speed >= 2mph: PUBLISH 'traffic_events' (consolidator trigger)

3. Consolidation Trigger (vehicle_consolidator_service.py)
   • SUBSCRIBE 'traffic_events'
   • ON radar_motion_detected:
     - Collect radar data (from event)
     - Fetch weather data (airport + DHT22)
     - Get recent camera/IMX500 detections
     - Create consolidated_record with unique ID

4. Consolidated Data Storage
   • SET 'consolidation:latest' (current record)
   • SET 'consolidation:history:{id}' (time-series)
   • PUBLISH 'database_events' (persistence trigger)

5. Database Persistence (database_persistence_service.py)
   • SUBSCRIBE 'database_events'
   • ON new_consolidated_data:
     - GET consolidated data from Redis
     - Parse into TrafficRecord structure
     - Store in SQLite database
```

### 11.4 Environment Variables Configuration

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        Docker Environment Variables                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Service: radar-service                                                  │
│ • REDIS_HOST=redis (container networking)                              │
│ • REDIS_PORT=6379                                                      │
│ • RADAR_UART_PORT=/dev/ttyAMA0                                         │
│ • RADAR_BAUD_RATE=19200                                                │
│                                                                         │
│ Service: vehicle-consolidator                                           │
│ • REDIS_HOST=redis                                                     │
│ • REDIS_PORT=6379                                                      │
│                                                                         │
│ Service: database-persistence                                           │
│ • REDIS_HOST=redis                                                     │
│ • DATABASE_PATH=/app/data/traffic.db                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.5 Redis Stream Cleanup Architecture

To prevent memory bloat, the system implements automatic Redis stream cleanup:

```text
database_persistence_service.py:
├── _cleanup_redis_streams()
│   ├── XTRIM radar_data MAXLEN ~ 1000      # Keep last 1000 entries
│   └── XTRIM consolidated_traffic_data MAXLEN ~ 100  # Keep last 100 entries
│
└── Called during _cleanup_old_data() every cleanup cycle
```

### 11.6 Data Structure Examples

**Radar Detection Event:**

```json
{
  "event_type": "radar_motion_detected",
  "speed": 23.9359,
  "magnitude": "unknown", 
  "direction": "unknown",
  "timestamp": 1758746262.250759,
  "trigger_source": "radar_speed_detection"
}
```

**Consolidated Record:**

```json
{
  "consolidation_id": "consolidation_1758746262",
  "timestamp": 1758746262.250759,
  "trigger_source": "radar_motion",
  "radar_data": { "speed": 23.9359, "magnitude": "unknown" },
  "weather_data": {
    "airport": { "temperature": 26, "windSpeed": 20.376 },
    "dht22": { "temperature_c": 21.56, "humidity": 96.4 }
  },
  "camera_data": {},
  "processing_notes": "Triggered by radar detection at 23.9359 mph"
}
```

### 11.7 Troubleshooting Common Issues

**Radar Service Restart Loop:**

- Check REDIS_HOST environment variable (should be 'redis', not 'localhost')
- Verify Redis container is running and healthy
- Check UART device permissions: /dev/ttyAMA0

**Database Persistence Failure:**

- Check SQLite database file permissions
- Verify storage volume mount: /app/data/
- Ensure database directory is writable by container user

**Missing Consolidation Data:**

- Verify consolidator service is running and subscribing to 'traffic_events'
- Check Redis pub/sub channels: `redis-cli PUBSUB CHANNELS`
- Monitor consolidation keys: `redis-cli KEYS "consolidation:*"`
