# Technical Design Document

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Technical Team  

## Table of Contents

1. [System Overview](#1-system-overview)
2. [System Architecture](#2-system-architecture)
3. [Top-Down Approach](#2x-top-down-approach)
4. [Hardware Design](#3-hardware-design)
5. [Component Interaction Diagram](#4-component-interaction-diagram)
6. [Sequence Diagram (Typical Event Flow)](#5-sequence-diagram-typical-event-flow)
7. [Deployment Diagram (Physical/Virtual Placement)](#6-deployment-diagram-physicalvirtual-placement)
8. [Database Entity-Relationship Diagram (ERD)](#7-database-entity-relationship-diagram-erd)
9. [API Endpoint Map](#8-api-endpoint-map)
10. [Security/Data Flow Diagram](#9-securitydata-flow-diagram)
11. [Remote Access Flow via Tailscale](#10-remote-access-flow-via-tailscale)

**See also:**

- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [User Guide](./User_Guide.md)
- [Project Management Summary](./Project_Management.md)
- [References & Appendices](./References_Appendices.md)

## 1. System Overview

The Raspberry Pi 5 Edge ML Traffic Monitoring System is designed to provide real-time vehicle detection, speed measurement, and traffic analytics at the edge. The system leverages a Raspberry Pi 5, an AI-enabled camera, and an OmniPreSense OPS243-C radar sensor to process video and radar data locally, sending only processed results to cloud services for aggregation and reporting. This approach reduces bandwidth, increases privacy, and enables rapid response to traffic events.

**Objectives:**

- Deploy a low-cost, scalable, and reliable edge-based traffic monitoring solution
- Integrate ML/AI for vehicle detection, classification, and anomaly detection
- Fuse camera and radar data for accurate speed and event measurement
- Provide real-time dashboards and cloud-based analytics

**Key Features:**

- Local ML inference and data fusion
- Real-time web dashboard (Edge UI)
- Cloud integration for historical analytics and alerts (Cloud UI)
- Modular, container-friendly architecture

## 2. System Architecture

## Executive Summary System Architecture Diagram

The following high-level ASCII diagram provides an executive summary of the system architecture, showing the main components and their relationships.

This diagram summarizes the overall system structure and data flow for both technical and non-technical stakeholders.

```text
                        +--------------------------------------+
                        |         Cloud Services (Optional)     |
                        |  +-------------------------------+   |
                        |  | Data Aggregation / Analytics  |   |
                        |  |   (AWS, DynamoDB, Lambda)     |   |
                        |  +-------------------------------+   |
                        |  |   Cloud UI / Alerts           |   |
                        |  +-------------------------------+   |
                        +------------------------^-------------+
                                         | (MQTT/REST, TLS)
                                         v
+-------------------+        +-------------------------------+        +-------------------+
|   Remote User     |<------>|  Local Network / Tailscale    |<------>|   Edge Device     |
| (Web/SSH Client)  |        |  (WiFi/Ethernet/Cellular)     |        | (Raspberry Pi 5)  |
+-------------------+        +-------------------------------+        +-------------------+
                                         |                                    |
                                         |                                    |
                                         v                                    v
                                +-------------------+                +-------------------+
                                |   Edge UI (Web)   |<---------------|  AI Camera        |
                                +-------------------+                +-------------------+
                                |   Edge API        |                | (Sony IMX500)     |
                                +-------------------+                +-------------------+
                                |   Data Fusion     |<---------------|  OPS243-C Radar   |
                                +-------------------+                +-------------------+
                                |   Speed Analysis  |                |  External SSD     |
                                +-------------------+                | (Samsung T7)      |
                                |   Local Storage   |                +-------------------+
                                +-------------------+                |  Power/PoE/UPS    |
                                +-------------------+
                                |   Health Monitor  |
                                +-------------------+
```

Legend:

Cloud Services are optional and only receive processed data/events.
Remote users connect via Tailscale VPN for secure SSH and web access.
The Edge Device (Raspberry Pi 5) hosts all core services, fusing data from the AI camera and radar, and provides a local dashboard.
All sensors and storage are directly attached to the Pi.
The network layer (Tailscale, WiFi/Ethernet/Cellular) secures and routes all connections.

### Unified Architecture Diagram

```text
+-------------------------------------------------------------+
|                Cloud Services Layer (Optional)              |
|  +-------------------+   +-------------------+              |
|  | Data Aggregation  |   | Analytics Engine  |              |
|  |   (AWS Lambda,    |   |  (Time Series DB) |              |
|  |   DynamoDB, etc.) |   +-------------------+              |
|  +-------------------+   | Cloud UI, Alerts  |              |
|         |                    |                              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Network & Communication Layer                       |
|  +-------------------+   +-------------------+              |
|  | WebSocket Server  |   | REST API Endpoints|              |
|  +-------------------+   +-------------------+              |
|  | Data Compression  |   | Network Resilience|              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Edge Processing Layer (Raspberry Pi 5)              |
|  +-------------------+   +-------------------+              |
|  | Vehicle Detection |   | Speed Analysis    |              |
|  |  (TensorFlow,     |   |  (OPS243-C Radar) |              |
|  |   OpenCV, AI Cam) |   +-------------------+              |
|  +-------------------+   | Multi-Vehicle     |              |
|  | Data Fusion Engine|   | Tracking (SORT)   |              |
|  +-------------------+   +-------------------+              |
|  | Edge API Gateway  |   | Edge UI (Web Dash)|              |
|  +-------------------+   +-------------------+              |
|  | System Health/    |   | Local Storage     |              |
|  | Watchdog/Weather  |   | Manager           |              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Physical Sensing Layer                              |
|  +-------------------+   +-------------------+              |
|  | AI Camera         |   | OPS243-C Radar    |              |
|  | (Sony IMX500)     |   | (Doppler, UART)   |              |
|  +-------------------+   +-------------------+              |
|  | Raspberry Pi 5    |   | External SSD      |              |
|  | (16GB RAM, ARM)   |   | (Samsung T7)      |              |
|  +-------------------+   +-------------------+              |
|  | Power & Connectivity (PoE, WiFi/Ethernet, Cellular)      |
|  | Environmental Housing (IP65/IP66)                        |
+-------------------------------------------------------------+
```

## 2.1 Physical Architecture Overview

```text
+-------------------------------------------------------------+
|           Cloud / Data Center (Optional, Remote)            |
|  - Cloud UI (Web Dashboard)                                 |
|  - Data Aggregation, Analytics Engine, Alert Service        |
|  - Long-term Storage, Model Management                      |
+---------------------^---------------------------------------+
                      |
                      v
+-------------------------------------------------------------+
|           Local Network / Internet                          |
|  - WiFi / Ethernet / Cellular                               |
+---------------------^---------------------------------------+
                      |
                      v
+-------------------------------------------------------------+
|           Edge Device: Raspberry Pi 5 Enclosure             |
|                                                             |
|  +-------------------+   +-------------------+              |
|  | Raspberry Pi 5    |   | Power Supply      |              |
|  | (16GB RAM, ARM)   |   | (PoE, USB-C, UPS) |              |
|  +-------------------+   +-------------------+              |
|  | External SSD      |   | Environmental     |              |
|  | (Samsung T7)      |   | Housing (IP65)    |              |
|  +-------------------+   +-------------------+              |
|                                                             |
|  +-------------------+   +-------------------+              |
|  | AI Camera         |   | OPS243-C Radar    |              |
|  | (Sony IMX500)     |   | (UART, Doppler)   |              |
|  +-------------------+   +-------------------+              |
|                                                             |
|  [All sensors and storage connect to the Pi 5]              |
|                                                             |
|  - Edge UI (Web Dashboard runs on Pi 5)                     |
|  - Vehicle Detection (TensorFlow/OpenCV on Pi 5)            |
|  - Speed Analysis (Radar on Pi 5)                           |
|  - Data Fusion, Local Storage, Health Monitoring (on Pi 5)  |
+-------------------------------------------------------------+
```

## 3. Hardware Design

This section describes the hardware components and their specifications for the Raspberry Pi 5 Edge ML Traffic Monitoring System.

- **Raspberry Pi 5 (16GB RAM, ARM Cortex-A76 CPU, VideoCore VII GPU)**
- **AI Camera (Sony IMX500 sensor, 12MP, on-chip AI processing)**
- **OPS243-C FMCW Doppler Radar Sensor (24.125 GHz, UART/Serial, 200m range)**
- **External USB SSD (Samsung T7 Shield 2TB) + 256GB MicroSD (UHS-I Class 10)**
- **Power & Connectivity:** Official Raspberry Pi 5 PSU (5.1V, 5A, 25W), PoE+ HAT, WiFi/Ethernet, optional cellular backup, UPS for continuous operation
- **Environmental Housing:** IP65/IP66 weatherproof enclosure (-40°C to +71°C)


## 3.1 ML/AI Workflow and Component Status

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
+-------------------+      +-------------------+      +-------------------+
| Vehicle Detection |----->| Data Fusion Engine|----->| Local Storage     |
|  (TensorFlow,     |      | (Python)          |      |  (SSD, tmpfs)     |
|   OpenCV, AI Cam) |      +-------------------+      +-------------------+
+-------------------+               |                        ^
        |                           v                        |
        |                +-------------------+               |
        +--------------->| Edge API Gateway  |---------------+
                         | (Flask-SocketIO)  |
                         +-------------------+
                                 |
                                 v
                         +-------------------+
                         | Edge UI (Web Dash)|
                         +-------------------+
```

## 5. Sequence Diagram (Typical Event Flow)

```text
Vehicle Detected
    |
    v
+-------------------+      +-------------------+      +-------------------+      +-------------------+
| AI Camera/Radar   |----->| Vehicle Detection |----->| Data Fusion Engine|----->| Edge UI/Storage   |
+-------------------+      +-------------------+      +-------------------+      +-------------------+
    |                                                                                  |
    |                                                                                  v
    |----------------------------------------------------------------------------> Cloud Sync (optional)
```

## 6. Deployment Diagram (Physical/Virtual Placement)

```text
+-------------------+         +-------------------+         +-------------------+
|  Cloud Services   |<------->| Local Network     |<------->| Edge Device       |
|  (AWS, Web UI)    |         | (WiFi/Ethernet)   |         | (Raspberry Pi 5)  |
+-------------------+         +-------------------+         +-------------------+
```

## 7. Database Entity-Relationship Diagram (ERD)

```text
+-------------------+      +-------------------+      +-------------------+
| VehicleEvent      |<-----| RadarReading      |      | CameraDetection   |
| id (PK)           |      | id (PK)           |      | id (PK)           |
| timestamp         |      | event_id (FK)     |      | event_id (FK)     |
| vehicle_type      |      | speed             |      | image_path        |
| speed             |      | ...               |      | ...               |
| ...               |      +-------------------+      +-------------------+
+-------------------+
```

## 8. API Endpoint Map

```text
+---------------------+-------------------+-----------------------------+
| Endpoint            | Method            | Purpose                     |
+---------------------+-------------------+-----------------------------+
| /api/events         | GET, POST         | Retrieve or add events      |
| /api/radar          | GET               | Get radar readings          |
| /api/camera         | GET               | Get camera detections       |
| /ws/stream          | WebSocket         | Real-time event streaming   |
+---------------------+-------------------+-----------------------------+
```

## 9. Security/Data Flow Diagram

```text
+-------------------+      +-------------------+      +-------------------+
| Edge Device       |<====>| Local Network     |<====>| Cloud Services    |
| (TLS/SSL, Auth)   |      | (Encrypted)       |      | (TLS/SSL, Auth)   |
+-------------------+      +-------------------+      +-------------------+
```

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
