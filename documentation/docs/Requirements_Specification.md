# Requirements Specification

**Project:** Edge AI Traffic Monitoring System  
**Version:** 1.0.0  
**Date:** October 2, 2025  
**Author:** Michael Merkle  
**Status:** Final

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Document Scope](#12-document-scope)
   - 1.3 [Definitions and Acronyms](#13-definitions-and-acronyms)
   - 1.4 [References](#14-references)
2. [Project Overview](#2-project-overview)
   - 2.1 [Project Vision](#21-project-vision)
   - 2.2 [Project Objectives](#22-project-objectives)
   - 2.3 [Project Scope](#23-project-scope)
   - 2.4 [Out of Scope](#24-out-of-scope)
3. [Stakeholder Requirements](#3-stakeholder-requirements)
   - 3.1 [Primary Stakeholders](#31-primary-stakeholders)
   - 3.2 [User Needs](#32-user-needs)
   - 3.3 [Business Requirements](#33-business-requirements)
4. [System Requirements](#4-system-requirements)
   - 4.1 [Hardware Requirements](#41-hardware-requirements)
   - 4.2 [Software Requirements](#42-software-requirements)
   - 4.3 [Network Requirements](#43-network-requirements)
   - 4.4 [Environmental Requirements](#44-environmental-requirements)
5. [Functional Requirements](#5-functional-requirements)
   - 5.1 [Vehicle Detection and Monitoring](#51-vehicle-detection-and-monitoring)
   - 5.2 [AI-Powered Classification](#52-ai-powered-classification)
   - 5.3 [Environmental Data Collection](#53-environmental-data-collection)
   - 5.4 [Data Fusion and Processing](#54-data-fusion-and-processing)
   - 5.5 [Data Persistence and Retrieval](#55-data-persistence-and-retrieval)
   - 5.6 [Real-Time Event Broadcasting](#56-real-time-event-broadcasting)
   - 5.7 [API and Web Services](#57-api-and-web-services)
   - 5.8 [Security and Access Control](#58-security-and-access-control)
   - 5.9 [System Maintenance and Monitoring](#59-system-maintenance-and-monitoring)
6. [Non-Functional Requirements](#6-non-functional-requirements)
   - 6.1 [Performance Requirements](#61-performance-requirements)
   - 6.2 [Reliability and Availability](#62-reliability-and-availability)
   - 6.3 [Scalability Requirements](#63-scalability-requirements)
   - 6.4 [Security Requirements](#64-security-requirements)
   - 6.5 [Usability Requirements](#65-usability-requirements)
   - 6.6 [Maintainability Requirements](#66-maintainability-requirements)
7. [Use Cases](#7-use-cases)
   - 7.1 [Use Case 1: Real-Time Vehicle Detection](#71-use-case-1-real-time-vehicle-detection)
   - 7.2 [Use Case 2: Historical Data Analysis](#72-use-case-2-historical-data-analysis)
   - 7.3 [Use Case 3: System Administration](#73-use-case-3-system-administration)
8. [Requirements Prioritization](#8-requirements-prioritization)
   - 8.1 [MoSCoW Analysis](#81-moscow-analysis)
   - 8.2 [Critical Path Requirements](#82-critical-path-requirements)
9. [Constraints and Assumptions](#9-constraints-and-assumptions)
   - 9.1 [Technical Constraints](#91-technical-constraints)
   - 9.2 [Business Constraints](#92-business-constraints)
   - 9.3 [Assumptions](#93-assumptions)
10. [Acceptance Criteria](#10-acceptance-criteria)
    - 10.1 [System Acceptance](#101-system-acceptance)
    - 10.2 [Performance Acceptance](#102-performance-acceptance)
    - 10.3 [Quality Acceptance](#103-quality-acceptance)
11. [Requirements Traceability](#11-requirements-traceability)
12. [Appendix](#12-appendix)

---

## 1. Introduction

### 1.1 Purpose

This Requirements Specification document defines the complete set of functional and non-functional requirements for the Edge AI Traffic Monitoring System. It serves as the authoritative reference for:

- System design and implementation
- Testing and validation procedures
- Project scope management
- Stakeholder communication
- Capstone project evaluation

### 1.2 Document Scope

This document covers:

- **Functional Requirements**: What the system must do
- **Non-Functional Requirements**: How well the system must perform
- **System Requirements**: Hardware, software, and environmental prerequisites
- **Use Cases**: Real-world scenarios and user interactions
- **Acceptance Criteria**: Conditions for successful project completion

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **Edge AI** | Artificial intelligence processing performed locally on edge devices (e.g., Raspberry Pi) rather than cloud servers |
| **IMX500** | Sony's AI-enabled camera sensor with integrated Neural Processing Unit (NPU) |
| **NPU** | Neural Processing Unit - dedicated hardware for AI inference |
| **METAR** | Meteorological Aerodrome Report - aviation weather format |
| **API** | Application Programming Interface |
| **REST** | Representational State Transfer |
| **WebSocket** | Protocol for bidirectional real-time communication |
| **Docker** | Containerization platform for deploying applications |
| **Redis** | In-memory data structure store used as message broker and cache |
| **SQLite** | Embedded relational database |
| **TLS/HTTPS** | Transport Layer Security / Secure HTTP protocol |
| **VPN** | Virtual Private Network |
| **CI/CD** | Continuous Integration / Continuous Deployment |

### 1.4 References

- **Technical Design Document**: `Technical_Design.md`
- **Testing Documentation**: `Testing_Documentation.md`
- **User Guide**: `User_Guide.md`
- **Implementation & Deployment Guide**: `Implementation_Deployment.md`

---

## 2. Project Overview

### 2.1 Project Vision

To develop an edge-based AI traffic monitoring solution that leverages modern hardware acceleration (Sony IMX500 NPU) and microservices architecture to provide real-time, accurate vehicle detection and classification without reliance on cloud infrastructure.

**Key Differentiators:**
- On-device AI inference using dedicated NPU (zero CPU overhead)
- Multi-sensor data fusion (radar + camera + weather)
- Real-time processing with sub-350ms latency
- Privacy-focused (no cloud data transmission)
- Production-ready containerized deployment

### 2.2 Project Objectives

1. **Demonstrate Edge AI Capabilities**: Showcase on-device AI inference using Sony IMX500 camera with integrated NPU
2. **Achieve Real-Time Performance**: Process vehicle detections with end-to-end latency < 350ms
3. **Implement Microservices Architecture**: Deploy 12+ containerized services using Docker
4. **Enable Multi-Sensor Fusion**: Correlate data from radar, camera, and weather sensors
5. **Provide Robust API**: Deliver RESTful API with real-time WebSocket event streaming
6. **Ensure Production Quality**: Achieve >99.9% uptime with automated monitoring and recovery
7. **Maintain Security**: Implement TLS encryption and VPN-based remote access

### 2.3 Project Scope

**In Scope:**
- Vehicle detection using Doppler radar sensor
- AI-powered vehicle classification using IMX500 camera
- Environmental data collection (temperature, humidity, weather conditions)
- Multi-sensor data correlation and fusion
- SQLite database with 90-day data retention
- RESTful API with 15+ endpoints
- Real-time WebSocket event broadcasting
- Web-based monitoring dashboard
- Docker containerized deployment
- Automated health monitoring and maintenance
- TLS/HTTPS security
- Tailscale VPN remote access

**Target Environment:**
- Raspberry Pi 5 (8GB RAM)
- Residential street monitoring
- Real-world traffic conditions
- 24/7 operation capability

### 2.4 Out of Scope

- License plate recognition (privacy concerns)
- Video recording/storage (privacy concerns)
- Cloud-based processing or storage
- Multi-location deployment (single-site focus)
- Mobile application development
- User authentication/authorization (private network deployment)
- Advanced traffic analytics (machine learning on historical data)
- Integration with municipal traffic systems

---

## 3. Stakeholder Requirements

### 3.1 Primary Stakeholders

| Stakeholder | Role | Primary Interest |
|------------|------|------------------|
| **Project Developer** | System architect, implementer | Technical excellence, portfolio demonstration |
| **Academic Evaluators** | Capstone reviewers | Meeting degree requirements, technical rigor |
| **End Users** | System operators, data analysts | Ease of use, data accuracy, system reliability |
| **Future Employers** | Potential hiring managers | Real-world skills, production-quality code |

### 3.2 User Needs

**As a system operator, I need:**
1. Real-time visibility into vehicle traffic patterns
2. Accurate vehicle speed measurements
3. Vehicle type classification
4. Historical data access for trend analysis
5. System health monitoring and alerts
6. Simple deployment and maintenance procedures

**As a data analyst, I need:**
7. RESTful API for programmatic data access
8. Historical data with 90-day retention
9. Correlation between traffic and weather conditions
10. Exportable data formats (JSON)

**As a system administrator, I need:**
11. Automated deployment via CI/CD
12. Health monitoring for all services
13. Automated recovery from failures
14. Secure remote access
15. Resource utilization visibility

### 3.3 Business Requirements

**BR-001**: System must operate autonomously with minimal manual intervention  
**BR-002**: System must maintain >99.9% uptime for production readiness demonstration  
**BR-003**: System must use open-source technologies to minimize licensing costs  
**BR-004**: System must be deployable on commodity hardware (Raspberry Pi 5)  
**BR-005**: System must respect privacy (no personally identifiable information collected)  
**BR-006**: System must demonstrate modern DevOps practices (containerization, CI/CD)  

---

## 4. System Requirements

### 4.1 Hardware Requirements

**Edge Computing Device:**
- **Model**: Raspberry Pi 5 (8GB RAM)
- **Storage**: NVMe SSD (Gen 3, minimum 128GB)
- **Network**: Gigabit Ethernet or WiFi 6
- **Power**: 27W USB-C power supply
- **Operating Temperature**: 0°C to 50°C

**Sensors:**
- **Radar**: OPS243-C Doppler radar sensor
  - Interface: UART (via USB)
  - Detection range: 1-100 meters
  - Speed accuracy: ±1 mph
  
- **Camera**: Raspberry Pi AI Camera (IMX500)
  - Resolution: 12.3MP
  - AI Accelerator: Integrated NPU
  - Interface: CSI-2 camera connector
  
- **Weather Sensor**: DHT22 temperature/humidity sensor
  - Interface: GPIO (1-wire protocol)
  - Temperature range: -40°C to 80°C
  - Humidity range: 0-100% RH

**Networking:**
- Tailscale VPN client for secure remote access
- Internet connectivity for weather API and remote access

### 4.2 Software Requirements

**Operating System:**
- Raspberry Pi OS 64-bit (Debian-based)
- Kernel version: 6.1 or higher

**Container Runtime:**
- Docker Engine: 24.0 or higher
- Docker Compose: 2.0 or higher

**Python Environment:**
- Python 3.9 or higher
- Key libraries: picamera2, opencv-python, redis, Flask, SQLAlchemy

**System Services:**
- systemd for service management
- journald for centralized logging

**External Services:**
- CheckWX Aviation Weather API (for METAR data)
- Tailscale VPN service

### 4.3 Network Requirements

**Bandwidth:**
- Minimum: 10 Mbps download, 5 Mbps upload
- Recommended: 50+ Mbps for HD image uploads (if enabled)

**Latency:**
- Internet latency: <100ms (for weather API calls)
- Local network latency: <5ms (for dashboard access)

**Ports:**
- 80: HTTP (redirects to HTTPS)
- 443 or 8443: HTTPS/TLS
- 6379: Redis (internal Docker network only)
- 5000-5005: Internal API services (Docker network)

**Security:**
- Tailscale VPN required for remote access
- No public internet exposure of services
- All external traffic encrypted via TLS

### 4.4 Environmental Requirements

**Physical Location:**
- Clear line of sight for radar sensor (no obstructions)
- Weather-protected installation for outdoor sensors
- Stable mounting for camera (minimal vibration)
- Power source within 2 meters

**Operating Conditions:**
- Temperature: 0°C to 40°C (typical indoor/outdoor)
- Humidity: 20-80% RH (non-condensing)
- Ventilation: Passive cooling for Raspberry Pi 5

---

## 5. Functional Requirements

### 5.1 Vehicle Detection and Monitoring

#### FR-001: Radar-Based Vehicle Detection

**Priority**: MUST HAVE (Critical)

**Description**: The system shall detect vehicle presence using a Doppler radar sensor with continuous monitoring capability.

**Acceptance Criteria:**
- Radar sensor continuously monitors for vehicle motion
- Detection range: 1-100 meters
- Detection triggers within 2 seconds of vehicle entering range
- System logs all detection events with timestamps

**Rationale**: Core functionality for traffic monitoring; provides trigger for camera capture.

**Dependencies**: OPS243-C radar sensor, UART communication, radar-service container

**Test Reference**: Testing_Documentation.md - Component Test CT-002

**Status**: ✅ Implemented and Validated

---

#### FR-002: Vehicle Speed Measurement

**Priority**: MUST HAVE (Critical)

**Description**: The system shall measure vehicle speed using Doppler radar with accuracy of ±2 mph.

**Acceptance Criteria:**
- Speed measured in miles per hour (mph)
- Accuracy: ±2 mph compared to GPS reference
- Speed range: 5-60 mph (residential street typical)
- Speed data logged with each detection event

**Rationale**: Essential for traffic analysis and compliance monitoring.

**Dependencies**: FR-001 (radar detection), calibrated radar sensor

**Test Reference**: Testing_Documentation.md - Requirement Test FR-002

**Status**: ✅ Implemented and Validated (±1.2 mph accuracy achieved)

---

### 5.2 AI-Powered Classification

#### FR-003: Vehicle Classification Using AI Camera

**Priority**: MUST HAVE (Critical)

**Description**: The system shall classify vehicles using the IMX500 AI camera with on-device neural network inference.

**Acceptance Criteria:**
- Vehicle types classified: car, truck, bus, motorcycle, bicycle
- Classification accuracy: >80% (minimum threshold)
- AI inference performed on-device using IMX500 NPU
- Classification confidence score included with results
- Bounding box coordinates captured for detected vehicles

**Rationale**: Demonstrates edge AI capabilities; provides detailed traffic composition data.

**Dependencies**: IMX500 camera, MobileNet SSD model, FR-001 (radar trigger)

**Test Reference**: Testing_Documentation.md - Component Test CT-004

**Status**: ✅ Implemented and Validated (85-95% accuracy achieved)

---

#### FR-004: Sub-100ms AI Inference Performance

**Priority**: MUST HAVE (Critical)

**Description**: The system shall perform AI inference in less than 100ms per frame using the IMX500's integrated NPU.

**Acceptance Criteria:**
- Inference time: <100ms per frame (measured from capture to classification)
- Zero CPU overhead (NPU handles all AI processing)
- Inference latency logged for performance monitoring
- System maintains real-time performance under load

**Rationale**: Demonstrates hardware acceleration benefits; critical for real-time operation.

**Dependencies**: FR-003, IMX500 NPU, optimized AI model

**Test Reference**: Testing_Documentation.md - Performance Test PT-LAT-001

**Status**: ✅ Implemented and Validated (45ms average inference time)

---

### 5.3 Environmental Data Collection

#### FR-005: Local Weather Data Collection (DHT22)

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall collect local temperature and humidity data using a DHT22 sensor every 5 minutes.

**Acceptance Criteria:**
- Temperature reading in Celsius (°C)
- Humidity reading in percentage (% RH)
- Reading interval: 5 minutes
- Data cached in Redis for quick access
- Failed readings handled gracefully with retry logic

**Rationale**: Provides hyper-local environmental context for traffic data correlation.

**Dependencies**: DHT22 sensor, GPIO access, weather-services container

**Test Reference**: Testing_Documentation.md - Component Test CT-003

**Status**: ✅ Implemented and Validated

---

#### FR-006: Airport Weather Data Collection (METAR)

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall retrieve airport weather data (METAR format) from the nearest airport every 10 minutes.

**Acceptance Criteria:**
- METAR data retrieved from CheckWX Aviation Weather API
- Update interval: 10 minutes
- Data includes: temperature, wind speed/direction, visibility, conditions
- Data cached in Redis for quick access
- API failures handled with exponential backoff retry

**Rationale**: Provides regional weather context; supplements local DHT22 data.

**Dependencies**: Internet connectivity, CheckWX API key, weather-services container

**Test Reference**: Testing_Documentation.md - Integration Test IT-EXT-001

**Status**: ✅ Implemented and Validated

---

### 5.4 Data Fusion and Processing

#### FR-007: Multi-Sensor Data Correlation

**Priority**: MUST HAVE (Critical)

**Description**: The system shall correlate data from radar, camera, and weather sensors into unified consolidated events.

**Acceptance Criteria:**
- Each consolidated event includes:
  - Radar data: speed, direction, magnitude
  - Camera data: vehicle type, confidence, bounding box, image path
  - Weather data: airport METAR + DHT22 local conditions
- Correlation completed within 100ms of radar trigger
- Unique correlation ID assigned to each event
- Time window for camera data retrieval: 30 seconds
- Consolidated events published to Redis for downstream processing

**Rationale**: Core value proposition; enables rich multi-dimensional traffic analysis.

**Dependencies**: FR-001, FR-003, FR-005, FR-006, vehicle-consolidator service

**Test Reference**: Testing_Documentation.md - System Test ST-FUSION-001

**Status**: ✅ Implemented and Validated

---

### 5.5 Data Persistence and Retrieval

#### FR-008: SQLite Database Persistence

**Priority**: MUST HAVE (Critical)

**Description**: The system shall persist all consolidated traffic events to a SQLite database with 90-day retention.

**Acceptance Criteria:**
- All consolidated events stored in `traffic_events` table
- Database schema includes all sensor data fields
- Batch insertion for performance (30-second batching window)
- Data retention: 90 days (automatic cleanup of older records)
- Database stored on NVMe SSD for performance
- Database file backed up periodically

**Rationale**: Enables historical analysis; required for trend identification.

**Dependencies**: FR-007 (consolidated events), SQLite, database-persistence service

**Test Reference**: Testing_Documentation.md - Component Test CT-006

**Status**: ✅ Implemented and Validated

---

### 5.6 Real-Time Event Broadcasting

#### FR-009: WebSocket Real-Time Event Streaming

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall broadcast traffic events to connected web clients in real-time using WebSocket (Socket.IO).

**Acceptance Criteria:**
- WebSocket server listens on HTTPS port
- Events broadcast within 1 second of detection
- Multiple concurrent clients supported (minimum 10)
- Connection maintained with automatic reconnection on failure
- Events include full consolidated data (radar + camera + weather)

**Rationale**: Enables live dashboard updates; demonstrates real-time capabilities.

**Dependencies**: FR-007, Socket.IO, realtime-events-broadcaster service

**Test Reference**: Testing_Documentation.md - System Test ST-BROADCAST-001

**Status**: ✅ Implemented and Validated

---

### 5.7 API and Web Services

#### FR-010: RESTful API for Data Access

**Priority**: MUST HAVE (Critical)

**Description**: The system shall provide a comprehensive RESTful API with at least 15 endpoints for data access and system monitoring.

**Acceptance Criteria:**
- **Health Check**: `GET /api/health` - System health status
- **Recent Events**: `GET /api/events/recent` - Latest N events (default 100)
- **Event Statistics**: `GET /api/events/stats` - Aggregate statistics
- **Radar Data**: `GET /api/radar/latest` - Latest radar reading
- **Weather Data**: `GET /api/weather/latest` - Latest weather conditions
- **Time Range Query**: `GET /api/events?start=X&end=Y` - Events in time range
- **API Documentation**: Swagger/OpenAPI documentation available
- All responses in JSON format
- Response times: <200ms for typical queries
- CORS enabled for web dashboard access

**Rationale**: Primary interface for data access; supports dashboard and future integrations.

**Dependencies**: FR-008 (database), Flask, api-gateway service

**Test Reference**: Testing_Documentation.md - Component Test CT-007

**Status**: ✅ Implemented and Validated (15+ endpoints operational)

---

#### FR-011: Web Dashboard Interface

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall provide a web-based dashboard for real-time monitoring and historical data visualization.

**Acceptance Criteria:**
- Single-page application (SPA) interface
- Real-time event updates via WebSocket
- Display latest vehicle detections with speed, type, weather
- Chart visualizations for traffic patterns
- System health indicators (all services status)
- Mobile-responsive design
- Accessible via HTTPS on Tailscale VPN

**Rationale**: User-friendly interface for system monitoring; demonstrates full-stack capabilities.

**Dependencies**: FR-009 (WebSocket), FR-010 (API), NGINX reverse proxy

**Test Reference**: Manual user acceptance testing

**Status**: ✅ Implemented and Validated

---

### 5.8 Security and Access Control

#### FR-012: TLS/HTTPS Encryption

**Priority**: MUST HAVE (Critical)

**Description**: The system shall encrypt all HTTP traffic using TLS 1.2 or higher with valid SSL certificates.

**Acceptance Criteria:**
- HTTPS enabled on port 443 or 8443
- TLS version: 1.2 minimum, 1.3 preferred
- Valid SSL certificate (Let's Encrypt via Tailscale)
- HTTP requests automatically redirected to HTTPS (301 redirect)
- Security headers configured: HSTS, X-Content-Type-Options, X-Frame-Options

**Rationale**: Protects data in transit; industry standard security practice.

**Dependencies**: NGINX reverse proxy, Tailscale TLS certificates

**Test Reference**: Testing_Documentation.md - Security Test SEC-NET-001

**Status**: ✅ Implemented and Validated

---

#### FR-013: Tailscale VPN Secure Access

**Priority**: MUST HAVE (Critical)

**Description**: The system shall be accessible only via Tailscale VPN, preventing public internet exposure.

**Acceptance Criteria:**
- Tailscale VPN client installed and configured
- System accessible via Tailscale hostname (*.ts.net)
- No services exposed on public IP addresses
- VPN connection required for dashboard and API access
- Automatic VPN reconnection on network changes

**Rationale**: Network-level security; prevents unauthorized access.

**Dependencies**: Tailscale service, internet connectivity

**Test Reference**: Testing_Documentation.md - Integration Test (Tailscale connectivity)

**Status**: ✅ Implemented and Validated

---

### 5.9 System Maintenance and Monitoring

#### FR-014: Automated Health Monitoring

**Priority**: MUST HAVE (Critical)

**Description**: The system shall continuously monitor the health of all services with automated recovery from failures.

**Acceptance Criteria:**
- Docker health checks configured for all containers (30-60 second intervals)
- Failed health checks trigger automatic container restart
- Health check endpoints return HTTP 200 for healthy status
- Service recovery time: <2 minutes from failure detection
- Health status visible via API endpoint (`/api/health`)

**Rationale**: Ensures system reliability; demonstrates production-ready operations.

**Dependencies**: Docker health checks, restart policies

**Test Reference**: Testing_Documentation.md - Performance Test PT-REL-002

**Status**: ✅ Implemented and Validated

---

#### FR-015: Automated Data Maintenance

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall automatically clean up old data to prevent storage exhaustion.

**Acceptance Criteria:**
- AI camera images deleted after 24 hours
- Database records retained for 90 days, then purged
- Docker logs rotated (max 10MB per file, 3 files per service)
- Cleanup runs automatically on schedule (hourly for images)
- Cleanup status logged and accessible via API

**Rationale**: Prevents storage exhaustion; reduces manual maintenance burden.

**Dependencies**: maintenance-service container, cron scheduling

**Test Reference**: Testing_Documentation.md - Component Test (Maintenance service)

**Status**: ✅ Implemented and Validated

---

#### FR-016: Zero-Downtime Deployments

**Priority**: SHOULD HAVE (Important)

**Description**: The system shall support zero-downtime deployments using CI/CD pipeline with rolling updates.

**Acceptance Criteria:**
- GitHub Actions CI/CD pipeline configured
- Deployment triggered by push to main branch
- Rolling container restarts (one service at a time)
- Health checks verify service readiness before proceeding
- Deployment completion time: <10 minutes
- No service interruption during deployment

**Rationale**: Enables rapid iteration; demonstrates modern DevOps practices.

**Dependencies**: GitHub Actions, self-hosted runner, Docker Compose

**Test Reference**: Testing_Documentation.md - CI/CD Testing

**Status**: ✅ Implemented and Validated

---

## 6. Non-Functional Requirements

### 6.1 Performance Requirements

#### NFR-001: End-to-End Latency

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall process vehicle detections from radar trigger to API availability in less than 350ms (95th percentile).

**Measurement Method**: Timestamp analysis from logs (radar detection → database write)

**Acceptance Criteria:**
- Average latency: <300ms
- 95th percentile latency: <350ms
- No processing delays during normal operation

**Target Value**: <350ms (95th percentile)  
**Achieved Value**: 280ms average, 320ms (95th percentile) ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-LAT-001

**Status**: ✅ Validated - Exceeds target

---

#### NFR-002: API Response Time

**Priority**: MUST HAVE (Critical)

**Requirement**: The system API shall respond to queries in less than 200ms under typical load.

**Measurement Method**: cURL timing measurements

**Acceptance Criteria:**
- Health check endpoint: <50ms
- Recent events query: <200ms
- Statistics aggregation: <200ms
- Weather/radar latest: <100ms

**Target Value**: <200ms average  
**Achieved Value**: 45ms average ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-LAT-002

**Status**: ✅ Validated - Significantly exceeds target

---

#### NFR-003: AI Inference Speed

**Priority**: MUST HAVE (Critical)

**Requirement**: The IMX500 camera shall complete AI inference in less than 100ms per frame.

**Measurement Method**: NPU inference time logging

**Acceptance Criteria:**
- Inference time: <100ms per frame
- Zero CPU overhead (NPU-accelerated)
- Consistent performance across frame sizes

**Target Value**: <100ms  
**Achieved Value**: 45ms average ✅

**Test Reference**: Testing_Documentation.md - Component Test CT-004

**Status**: ✅ Validated - Exceeds target by 55%

---

### 6.2 Reliability and Availability

#### NFR-004: System Uptime

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall maintain uptime greater than 99.9% over extended operation periods.

**Measurement Method**: Continuous monitoring logs, service restart tracking

**Acceptance Criteria:**
- No unexpected service crashes
- Automated recovery from failures in <2 minutes
- Minimal manual intervention required
- 9+ hours continuous operation demonstrated

**Target Value**: >99.9% uptime  
**Achieved Value**: 100% uptime over 9+ hour test ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-REL-001

**Status**: ✅ Validated

---

#### NFR-005: Data Integrity

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall ensure 100% data integrity with no data loss or corruption.

**Measurement Method**: Database validation, checksum verification

**Acceptance Criteria:**
- All radar detections result in database records
- No data corruption in SQLite database
- Transaction atomicity maintained
- Failed writes logged and retried

**Target Value**: 100% data integrity  
**Achieved Value**: 100% (no data loss observed) ✅

**Test Reference**: Testing_Documentation.md - Component Test CT-006

**Status**: ✅ Validated

---

#### NFR-006: Fault Tolerance

**Priority**: SHOULD HAVE (Important)

**Requirement**: The system shall gracefully handle sensor failures and continue operation with degraded functionality.

**Measurement Method**: Failure injection testing

**Acceptance Criteria:**
- Camera unavailable: system continues with radar-only data
- Weather sensor unavailable: system caches last known values
- Network unavailable: system operates offline (no airport weather)
- Service failures trigger automatic restarts

**Target Value**: Graceful degradation, <2 minute recovery  
**Achieved Value**: All scenarios handled correctly ✅

**Test Reference**: Testing_Documentation.md - System Test ST-E2E-002 (nighttime mode)

**Status**: ✅ Validated

---

### 6.3 Scalability Requirements

#### NFR-007: Resource Utilization - CPU

**Priority**: SHOULD HAVE (Important)

**Requirement**: The system shall maintain CPU utilization below 50% under normal load to allow headroom for scaling.

**Measurement Method**: `docker stats` monitoring

**Acceptance Criteria:**
- Normal load (1 detection per 5 minutes): <10% CPU
- Peak load (5 detections per minute): <50% CPU
- IMX500 AI inference: 0% CPU (NPU-accelerated)

**Target Value**: <50% CPU (peak load)  
**Achieved Value**: 5% normal, 33% peak ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-RES-001

**Status**: ✅ Validated - Significant headroom available

---

#### NFR-008: Resource Utilization - Memory

**Priority**: SHOULD HAVE (Important)

**Requirement**: The system shall use less than 4GB of RAM (of 8GB available) to prevent memory exhaustion.

**Measurement Method**: `docker stats` memory monitoring

**Acceptance Criteria:**
- Total system memory usage: <4GB
- No memory leaks over extended operation (9+ hours)
- Memory growth: <10MB per hour

**Target Value**: <4GB  
**Achieved Value**: ~900MB (11% of 8GB) ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-RES-002

**Status**: ✅ Validated - Excellent efficiency

---

#### NFR-009: Throughput Capacity

**Priority**: COULD HAVE (Nice to have)

**Requirement**: The system shall handle at least 10 vehicle detections per minute without performance degradation.

**Measurement Method**: High-traffic scenario testing

**Acceptance Criteria:**
- Process 10+ detections per minute
- No dropped events
- Latency remains stable under load
- Services remain healthy

**Target Value**: 10 detections/minute  
**Achieved Value**: 20+ detections/minute capable ✅

**Test Reference**: Testing_Documentation.md - Performance Test PT-THR-001

**Status**: ✅ Validated - Exceeds target

---

### 6.4 Security Requirements

#### NFR-010: Data Privacy

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall not collect or store personally identifiable information (PII).

**Acceptance Criteria:**
- No license plate recognition
- No facial recognition
- No video recording/storage
- Images deleted after 24 hours
- No data transmitted to cloud services

**Test Reference**: Design review, code audit

**Status**: ✅ Validated - No PII collected by design

---

#### NFR-011: SQL Injection Prevention

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall prevent SQL injection attacks through parameterized queries.

**Measurement Method**: Code review, security testing

**Acceptance Criteria:**
- All database queries use parameterized statements
- No string concatenation for SQL query construction
- Input validation on API endpoints

**Test Reference**: Testing_Documentation.md - Security Test SEC-VUL-001

**Status**: ✅ Validated - All queries parameterized

---

#### NFR-012: Network Security

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall implement network-level security to prevent unauthorized access.

**Acceptance Criteria:**
- Services not exposed on public internet
- TLS 1.2+ encryption for all HTTP traffic
- Tailscale VPN required for access
- Security headers configured (HSTS, CSP, X-Frame-Options)

**Test Reference**: Testing_Documentation.md - Security Tests SEC-NET-001, SEC-NET-002

**Status**: ✅ Validated

---

### 6.5 Usability Requirements

#### NFR-013: Deployment Simplicity

**Priority**: SHOULD HAVE (Important)

**Requirement**: The system shall be deployable with a single command after initial setup.

**Acceptance Criteria:**
- Single command deployment: `docker-compose up -d`
- Automated CI/CD pipeline for updates
- No manual configuration for normal operation
- Self-documenting setup scripts

**Test Reference**: Implementation_Deployment.md

**Status**: ✅ Validated

---

#### NFR-014: API Usability

**Priority**: SHOULD HAVE (Important)

**Requirement**: The API shall be intuitive and well-documented for ease of integration.

**Acceptance Criteria:**
- RESTful design following industry standards
- Swagger/OpenAPI documentation available
- Consistent JSON response format
- Descriptive error messages
- CORS enabled for web clients

**Test Reference**: API documentation, user testing

**Status**: ✅ Validated

---

### 6.6 Maintainability Requirements

#### NFR-015: Code Quality

**Priority**: SHOULD HAVE (Important)

**Requirement**: The codebase shall follow Python best practices and be well-documented.

**Acceptance Criteria:**
- PEP 8 style compliance
- Type hints for function signatures
- Docstrings for all public functions
- Modular design with single responsibility principle
- Comprehensive comments for complex logic

**Test Reference**: Code review

**Status**: ✅ Validated

---

#### NFR-016: Logging and Observability

**Priority**: MUST HAVE (Critical)

**Requirement**: The system shall provide comprehensive logging for debugging and monitoring.

**Acceptance Criteria:**
- Structured logging with severity levels (INFO, WARNING, ERROR)
- Correlation IDs for tracing requests across services
- Centralized logging via Docker stdout/stderr
- Log retention: 7 days (automatic rotation)
- Performance metrics logged

**Test Reference**: Log analysis report (LOG_ANALYSIS_REPORT_2025-09-27.md)

**Status**: ✅ Validated

---

## 7. Use Cases

### 7.1 Use Case 1: Real-Time Vehicle Detection

**Use Case ID**: UC-001  
**Actor**: System (Automated)  
**Goal**: Detect and classify a passing vehicle with full sensor data correlation

**Preconditions:**
- All services running and healthy
- Sensors operational (radar, camera, weather)
- Network connectivity available

**Main Flow:**
1. Radar sensor detects vehicle motion
2. Radar service measures speed and publishes event to Redis
3. IMX500 camera triggers on radar event
4. Camera performs AI inference (vehicle classification)
5. Camera publishes classification results to Redis
6. Vehicle-consolidator retrieves radar, camera, and weather data
7. Consolidator creates unified event with correlation ID
8. Consolidated event published to database persistence
9. Database persists event to SQLite
10. Realtime broadcaster sends event to connected WebSocket clients
11. Dashboard updates with new detection in real-time

**Postconditions:**
- Vehicle detection stored in database
- Real-time dashboard updated
- Data available via API

**Alternative Flows:**
- **3a. Camera unavailable (nighttime)**: System continues with radar + weather data only
- **4a. AI inference fails**: Event logged, continues with radar data
- **8a. Database write fails**: Event buffered and retried

**Performance Criteria:**
- End-to-end completion: <350ms (95th percentile)
- Real-time dashboard update: <1 second

**Test Reference**: Testing_Documentation.md - System Test ST-E2E-001

---

### 7.2 Use Case 2: Historical Data Analysis

**Use Case ID**: UC-002  
**Actor**: Data Analyst  
**Goal**: Query historical traffic data to identify patterns

**Preconditions:**
- System has collected data for analysis period
- User has access to API (via Tailscale VPN)
- API service operational

**Main Flow:**
1. Analyst opens web browser
2. Navigates to dashboard URL (https://*.ts.net)
3. Dashboard loads and displays recent events
4. Analyst uses API to query specific time range:
   ```
   GET /api/events?start=2025-10-01T00:00:00&end=2025-10-01T23:59:59
   ```
5. API queries SQLite database
6. Database returns matching records
7. API formats results as JSON
8. Analyst receives structured data for analysis
9. Data includes: timestamps, speeds, vehicle types, weather conditions
10. Analyst exports data for further processing

**Postconditions:**
- Analyst has historical data for analysis
- No system state changes

**Alternative Flows:**
- **4a. No data for time range**: API returns empty array with 200 status
- **5a. Database query timeout**: API returns 503 error, logs issue
- **6a. Invalid date format**: API returns 400 error with clear message

**Performance Criteria:**
- Query response time: <200ms for typical date range (1 day)
- Result set size: Up to 10,000 records per query

**Test Reference**: Testing_Documentation.md - Component Test CT-007 (API Gateway)

---

### 7.3 Use Case 3: System Administration

**Use Case ID**: UC-003  
**Actor**: System Administrator  
**Goal**: Deploy system update with zero downtime

**Preconditions:**
- Code changes pushed to GitHub main branch
- Self-hosted runner operational on Raspberry Pi
- System currently running in production

**Main Flow:**
1. Administrator pushes code changes to GitHub
2. GitHub Actions detects push to main branch
3. CI/CD pipeline triggered automatically
4. Pipeline executes on self-hosted runner:
   - Pulls latest code
   - Builds Docker images
   - Runs health checks on current system
   - Deploys containers with rolling restart
5. Docker Compose updates one service at a time
6. Health checks verify each service before proceeding to next
7. All services updated and healthy
8. Pipeline reports success
9. Administrator verifies deployment via dashboard

**Postconditions:**
- System running with updated code
- No service downtime experienced
- All health checks passing

**Alternative Flows:**
- **6a. Health check fails**: Pipeline rolls back to previous version
- **6b. Critical service fails**: Pipeline stops, alerts administrator
- **9a. Manual verification fails**: Administrator can rollback manually

**Performance Criteria:**
- Deployment time: <10 minutes
- Downtime: 0 seconds (rolling restart)

**Test Reference**: Testing_Documentation.md - Continuous Testing (CI/CD)

---

## 8. Requirements Prioritization

### 8.1 MoSCoW Analysis

Requirements prioritized using the MoSCoW method:

#### MUST HAVE (Critical - Project Cannot Succeed Without These)

**Functional:**
- FR-001: Radar-based vehicle detection
- FR-002: Vehicle speed measurement
- FR-003: AI vehicle classification
- FR-004: Sub-100ms AI inference
- FR-007: Multi-sensor data correlation
- FR-008: Database persistence
- FR-010: RESTful API
- FR-012: TLS/HTTPS encryption
- FR-013: Tailscale VPN access
- FR-014: Automated health monitoring

**Non-Functional:**
- NFR-001: End-to-end latency <350ms
- NFR-002: API response time <200ms
- NFR-003: AI inference <100ms
- NFR-004: System uptime >99.9%
- NFR-005: Data integrity 100%
- NFR-010: Data privacy (no PII)
- NFR-011: SQL injection prevention
- NFR-012: Network security
- NFR-016: Logging and observability

#### SHOULD HAVE (Important - Add Significant Value)

**Functional:**
- FR-005: Local weather data (DHT22)
- FR-006: Airport weather data (METAR)
- FR-009: WebSocket real-time streaming
- FR-011: Web dashboard
- FR-015: Automated data maintenance
- FR-016: Zero-downtime deployments

**Non-Functional:**
- NFR-006: Fault tolerance
- NFR-007: CPU utilization <50%
- NFR-008: Memory usage <4GB
- NFR-013: Deployment simplicity
- NFR-014: API usability
- NFR-015: Code quality

#### COULD HAVE (Nice to Have - Desirable but Not Essential)

**Non-Functional:**
- NFR-009: Throughput >10/min (already exceeded with 5/min typical)

#### WON'T HAVE (Out of Scope for This Release)

- License plate recognition
- Video recording/storage
- User authentication (private network deployment)
- Multi-site deployment
- Mobile application
- Advanced ML analytics on historical data

### 8.2 Critical Path Requirements

Requirements on the critical path for project success (dependencies):

1. **Hardware Setup** → FR-001, FR-003, FR-005 (sensors must work)
2. **FR-001** → FR-002, FR-007 (radar enables speed and correlation)
3. **FR-003** → FR-004, FR-007 (camera enables AI and correlation)
4. **FR-007** → FR-008, FR-009 (correlation enables persistence and streaming)
5. **FR-008** → FR-010 (database enables API)
6. **FR-010** → FR-011 (API enables dashboard)
7. **NFR-001, NFR-002, NFR-003** → System performance acceptance

**Critical Path Timeline:**
Hardware Setup → Radar Integration → Camera Integration → Data Fusion → Database → API → Dashboard → Performance Validation

---

## 9. Constraints and Assumptions

### 9.1 Technical Constraints

**TC-001**: Hardware Platform  
- **Constraint**: System must run on Raspberry Pi 5 (ARM64 architecture)
- **Impact**: Limits processing power, requires efficient algorithms
- **Mitigation**: Use hardware acceleration (IMX500 NPU), optimize code

**TC-002**: Edge Computing  
- **Constraint**: All processing must occur on-device (no cloud dependency)
- **Impact**: Limited computational resources compared to cloud
- **Mitigation**: Leverage NPU for AI, use lightweight models

**TC-003**: Single-Site Deployment  
- **Constraint**: System designed for single monitoring location
- **Impact**: No distributed architecture required, simpler design
- **Benefit**: Reduces complexity, easier to maintain

**TC-004**: Open-Source Technologies  
- **Constraint**: Must use free/open-source software (budget limitation)
- **Impact**: Limits vendor-specific features
- **Benefit**: No licensing costs, community support

**TC-005**: Network Dependency  
- **Constraint**: Internet required for weather API and VPN access
- **Impact**: Offline operation limited (no airport weather, no remote access)
- **Mitigation**: Local DHT22 sensor, system continues core function offline

### 9.2 Business Constraints

**BC-001**: Project Timeline  
- **Constraint**: Capstone project timeline (academic semester)
- **Impact**: Limits scope, requires prioritization
- **Mitigation**: MoSCoW prioritization, MVP-first approach

**BC-002**: Budget  
- **Constraint**: Limited budget for hardware/services
- **Impact**: Commodity hardware (Raspberry Pi), no premium services
- **Benefit**: Demonstrates cost-effective solution

**BC-003**: Solo Development  
- **Constraint**: Single developer (no team)
- **Impact**: Limited capacity, focus on core features
- **Mitigation**: Leverage existing libraries, focus on integration

**BC-004**: Privacy Requirements  
- **Constraint**: No personally identifiable information (PII) collection
- **Impact**: No license plates, no facial recognition, no video storage
- **Benefit**: Simpler compliance, ethical design

### 9.3 Assumptions

**AS-001**: Network Availability  
- **Assumption**: Internet connectivity available >95% of the time
- **Risk**: Weather API unavailable during outages
- **Validation**: System continues core function offline (radar + camera)

**AS-002**: Power Stability  
- **Assumption**: Consistent power supply to Raspberry Pi
- **Risk**: Unexpected shutdowns could corrupt database
- **Mitigation**: SQLite transaction safety, UPS recommended

**AS-003**: Sensor Accuracy  
- **Assumption**: Radar sensor provides ±2 mph accuracy as specified
- **Risk**: Inaccurate speed measurements
- **Validation**: Tested against GPS reference (±1.2 mph achieved)

**AS-004**: Traffic Volume  
- **Assumption**: Residential street traffic: 5-20 vehicles per hour
- **Risk**: System may be underutilized in low-traffic areas
- **Validation**: Performance tested up to 20+ detections per minute

**AS-005**: Environmental Conditions  
- **Assumption**: Sensors operate within 0°C to 40°C range
- **Risk**: Extreme temperatures may affect accuracy
- **Mitigation**: Weather-protected housing for outdoor sensors

**AS-006**: Tailscale VPN Service  
- **Assumption**: Tailscale service remains available and free for personal use
- **Risk**: Service changes could affect remote access
- **Mitigation**: System functions independently, VPN only for remote access

---

## 10. Acceptance Criteria

### 10.1 System Acceptance

The system shall be considered acceptable for capstone submission when:

**SA-001**: All MUST HAVE requirements implemented and validated (✅ Achieved)

**SA-002**: System demonstrates 9+ hours of continuous stable operation (✅ Achieved)

**SA-003**: All functional requirements tested with documented results (✅ Achieved)

**SA-004**: Performance metrics meet or exceed targets:
- ✅ End-to-end latency: <350ms (achieved 280ms avg)
- ✅ AI inference: <100ms (achieved 45ms avg)
- ✅ API response: <200ms (achieved 45ms avg)

**SA-005**: Zero major defects or unresolved issues (✅ Achieved)

**SA-006**: Comprehensive documentation complete:
- ✅ Requirements Specification (this document)
- ✅ Technical Design Document
- ✅ Testing Documentation
- ✅ User Guide
- ✅ Implementation & Deployment Guide

### 10.2 Performance Acceptance

**PA-001**: Latency Performance (✅ Achieved)
- End-to-end: <350ms (95th percentile) → Achieved: 320ms
- AI inference: <100ms → Achieved: 45ms
- API response: <200ms → Achieved: 45ms

**PA-002**: Resource Utilization (✅ Achieved)
- CPU: <50% peak → Achieved: 33% peak
- Memory: <4GB → Achieved: 900MB
- Disk: Managed growth → Achieved: <1GB long-term

**PA-003**: Reliability (✅ Achieved)
- Uptime: >99.9% → Achieved: 100% (9+ hours)
- Recovery time: <2 minutes → Achieved: 40-75 seconds
- Data integrity: 100% → Achieved: 100%

### 10.3 Quality Acceptance

**QA-001**: Code Quality (✅ Achieved)
- PEP 8 compliance for Python code
- Comprehensive logging and error handling
- Modular microservices architecture
- Dockerized deployment

**QA-002**: Testing Coverage (✅ Achieved)
- 106 test cases executed
- 100% pass rate
- 25 requirements validated
- 50 component tests
- 10 end-to-end scenarios

**QA-003**: Documentation Quality (✅ Achieved)
- Clear, comprehensive technical documentation
- User guide for operators
- API documentation (Swagger)
- Deployment guides
- Testing procedures and results

**QA-004**: Security (✅ Achieved)
- TLS encryption enabled
- SQL injection prevention verified
- No PII collected
- Network security (Tailscale VPN)

---

## 11. Requirements Traceability

**Full Requirements Traceability Matrix available in:**  
`Testing_Documentation.md` - Section 3.1

**Summary:**
- **Total Requirements**: 25 (15 Functional + 10 Non-Functional)
- **Requirements Tested**: 25 (100% coverage)
- **Requirements Passed**: 25 (100% pass rate)
- **Test Cases**: 106 total
- **Pass Rate**: 100%

**Traceability Links:**

| Requirement | Test Case ID | Test Document Section | Status |
|-------------|-------------|----------------------|---------|
| FR-001 | CT-002 | Component Test - Radar Service | ✅ PASS |
| FR-002 | FR-002 | Requirements Test | ✅ PASS |
| FR-003 | CT-004 | Component Test - IMX500 | ✅ PASS |
| FR-004 | PT-LAT-001 | Performance Test - Inference | ✅ PASS |
| FR-005 | CT-003 | Component Test - Weather | ✅ PASS |
| FR-006 | IT-EXT-001 | Integration Test - Airport API | ✅ PASS |
| FR-007 | ST-FUSION-001 | System Test - Data Fusion | ✅ PASS |
| FR-008 | CT-006 | Component Test - Database | ✅ PASS |
| FR-009 | ST-BROADCAST-001 | System Test - WebSocket | ✅ PASS |
| FR-010 | CT-007 | Component Test - API Gateway | ✅ PASS |
| FR-011 | Manual UAT | User Acceptance Testing | ✅ PASS |
| FR-012 | SEC-NET-001 | Security Test - TLS | ✅ PASS |
| FR-013 | Manual Test | Tailscale Connectivity | ✅ PASS |
| FR-014 | PT-REL-002 | Performance Test - Recovery | ✅ PASS |
| FR-015 | Manual Test | Maintenance Service | ✅ PASS |
| FR-016 | CI/CD Test | Deployment Pipeline | ✅ PASS |
| NFR-001 | PT-LAT-001 | Performance Test - E2E Latency | ✅ PASS |
| NFR-002 | PT-LAT-002 | Performance Test - API Response | ✅ PASS |
| NFR-003 | PT-LAT-001 | Performance Test - AI Inference | ✅ PASS |
| NFR-004 | PT-REL-001 | Performance Test - Uptime | ✅ PASS |
| NFR-005 | CT-006 | Component Test - Data Integrity | ✅ PASS |
| NFR-006 | ST-E2E-002 | System Test - Fault Tolerance | ✅ PASS |
| NFR-007 | PT-RES-001 | Performance Test - CPU | ✅ PASS |
| NFR-008 | PT-RES-002 | Performance Test - Memory | ✅ PASS |
| NFR-009 | PT-THR-001 | Performance Test - Throughput | ✅ PASS |
| NFR-010 | Design Review | Privacy by Design | ✅ PASS |
| NFR-011 | SEC-VUL-001 | Security Test - SQL Injection | ✅ PASS |
| NFR-012 | SEC-NET-001/002 | Security Test - Network | ✅ PASS |

---

## 12. Appendix

### 12.1 Requirement Change Log

| Date | Requirement | Change | Reason |
|------|------------|--------|--------|
| 2025-09-24 | NFR-003 | Updated target: <100ms inference | IMX500 NPU exceeds initial expectations (45ms achieved) |
| 2025-09-27 | NFR-004 | Updated validation: 9+ hours continuous | Extended stability testing completed |
| 2025-10-02 | All | Formalized in Requirements Specification | Capstone documentation requirement |

### 12.2 Related Documents

- **Technical_Design.md**: System architecture and design decisions
- **Testing_Documentation.md**: Comprehensive testing procedures and results
- **User_Guide.md**: End-user operational documentation
- **Implementation_Deployment.md**: Deployment procedures and configuration
- **LOG_ANALYSIS_REPORT_2025-09-27.md**: Production system validation results

### 12.3 Approval

**Requirements Specification Approved By:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Developer | Michael Merkle | [Digital Signature] | October 2, 2025 |
| Academic Advisor | [To be signed] | | |
| Capstone Committee | [To be signed] | | |

---

**Document Version**: 1.0.0  
**Last Updated**: October 2, 2025  
**Status**: Final for Capstone Submission

**END OF REQUIREMENTS SPECIFICATION**
