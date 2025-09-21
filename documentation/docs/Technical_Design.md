# Technical Design Document

**Document Version:** 1.0  
**Last Updated:** December 11, 2025  
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

The Raspberry Pi 5 Edge ML Traffic Monitoring System is designed to provide real-time vehicle detection, classification, speed measurement, and traffic analytics at the edge. The system leverages a Raspberry Pi 5, an AI-enabled IMX500 camera with on-sensor processing, and an OmniPreSense OPS243-C radar sensor to perform radar-triggered vehicle classification and analysis locally, sending only processed results and metadata to cloud services for aggregation and reporting. This approach reduces bandwidth, increases privacy, and enables rapid response to traffic events.

**Objectives:**

- Deploy a low-cost, scalable, and reliable edge-based traffic monitoring solution
- **Integrate radar-triggered edge AI for real-time vehicle classification**
- **Perform on-camera AI inference using IMX500 neural processing unit**
- Fuse radar and AI camera data for accurate speed and vehicle identification
- Provide real-time dashboards and cloud-based analytics

**Key Features:**

- **Radar-triggered edge AI processing with <350ms total latency**
- **On-camera vehicle classification with 85-95% accuracy**
- **Multi-sensor data fusion (radar + motion detection + AI)**
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
                                |   Edge UI (Web)   |<---------------|  IMX500 AI Camera |
                                +-------------------+                +-------------------+
                                |   Edge API        |                | (Edge AI Inference)|
                                +-------------------+                +-------------------+
                                |   Data Fusion     |<---------------|  OPS243-C Radar   |
                                +-------------------+                +-------------------+
                                |  AI Correlation   |                |  External SSD     |
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
The Edge Device (Raspberry Pi 5) hosts all core services, with radar-triggered edge AI processing.
IMX500 AI Camera performs real-time vehicle classification on-sensor.
OPS243-C Radar provides continuous motion detection and speed measurement.
Data Fusion layer correlates radar and AI data for enhanced accuracy.
All sensors and storage are directly attached to the Pi.
The network layer (Tailscale, WiFi/Ethernet/Cellular) secures and routes all connections.

### Enhanced Edge AI Architecture Diagram

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
|         Edge AI Processing Layer (Raspberry Pi 5)           |
|  +-------------------+   +-------------------+              |
|  | Radar Detection   |   | IMX500 AI Camera  |              |
|  |  (OPS243-C, UART)|   |  (Edge Inference) |              |
|  +-------------------+   +-------------------+              |
|  | Multi-Sensor Data |   | Vehicle Class.    |              |
|  | Fusion Engine     |   | (On-Camera AI)    |              |
|  +-------------------+   +-------------------+              |
|  | Edge API Gateway  |   | Edge UI (Web Dash)|              |
|  +-------------------+   +-------------------+              |
|  | System Health/    |   | Enhanced Storage  |              |
|  | AI Performance   |   | w/ AI Metadata    |              |
+---------|--------------------|------------------------------+
          |                    |
          v                    v
+-------------------------------------------------------------+
|         Physical Sensing Layer                              |
|  +-------------------+   +-------------------+              |
|  | IMX500 AI Camera  |   | OPS243-C Radar    |              |
|  | (3.1 TOPS NPU)    |   | (Doppler, UART)   |              |
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
  +-------------------+
  | Sony IMX500 AI    |
  | Camera (on-chip   |
  | inference,        |
  | real-time object  |
  | detection)        |
  +---------+---------+
         |
         v
  +-------------------+
  | Detection Results |
  | (bounding boxes,  |
  | class labels,     |
  | confidence scores)|
  +---------+---------+
         |
         v
 +-------------------+      +-------------------+      +-------------------+
 | Vehicle Detection |----->| Data Fusion Engine|----->| Local Storage     |
 |  (Raspberry Pi:   |      |   (Python)        |      |  (SSD, tmpfs)     |
 |   TensorFlow,     |      +-------------------+      +-------------------+
 |   OpenCV,         |               |                        ^
 |   AI Cam input)   |               v                        |
 +-------------------+      +-------------------+             |
        |                | Edge API Gateway  |-------------+
        |                | (Flask-SocketIO)  |
        |                +-------------------+
        |                        |
        v                        v
   (Optional)              +-------------------+
   Cloud Sync <------------| Edge UI (Web Dash)|
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

## 7. CI/CD Deployment Architecture

The system uses an automated CI/CD pipeline for consistent, reliable deployments:

```text
+-------------------+      +-------------------+      +-------------------+
|   Developer       |      | GitHub Actions   |      | Docker Hub        |
|   Workstation     |      | CI/CD Pipeline    |      | Container Registry|
+-------------------+      +-------------------+      +-------------------+
         |                          |                          |
         | git push                 | build & push             | pull image
         |                          |                          |
         v                          v                          v
+-------------------+      +-------------------+      +-------------------+
|   GitHub Repo     |----->| Build Workflow    |----->| Docker Image      |
|   (Source Code)   |      | (ARM64 Build)     |      | (ARM64/Pi Ready)  |
+-------------------+      +-------------------+      +-------------------+
                                   |
                                   | trigger deploy
                                   |
                                   v
                          +-------------------+      +-------------------+
                          | Deploy Workflow   |----->| Raspberry Pi      |
                          | (SSH + Docker)    |      | (Production)      |
                          +-------------------+      +-------------------+
```

### CI/CD Pipeline Components

1. **Build Workflow** (`docker-build-push.yml`)
   - Triggered on push to main branch
   - Builds Docker image for ARM64 architecture
   - Pushes image to Docker Hub registry
   - Uses cloud-compatible package requirements

2. **Deploy Workflow** (`deploy-to-pi.yml`)
   - Triggered after successful build completion
   - Connects to Raspberry Pi via SSH
   - Pulls latest Docker image
   - Restarts container with new image
   - Installs Pi-specific packages at runtime

3. **Package Management Strategy**
   - **Cloud Build**: General packages (tensorflow, opencv, flask, etc.)
   - **Pi Runtime**: Hardware-specific packages (picamera2, gpiozero, RPi.GPIO)

## 8. Database Entity-Relationship Diagram (ERD)

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
