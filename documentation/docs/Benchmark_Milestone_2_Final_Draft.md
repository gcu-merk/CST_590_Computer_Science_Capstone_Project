# Benchmark Milestone 1 Final Draft

## Project Information

- **Stakeholders' Names:** (Refer to project documentation or fill in as appropriate)
- **Project Name:** Raspberry Pi 5 Edge ML Traffic Monitoring System
- **Document Contributors:** Technical Team

---

## Design Planning Summary (C3.2)

The Raspberry Pi 5 Edge ML Traffic Monitoring System is designed to provide real-time vehicle detection, speed measurement, and traffic analytics at the edge. The system leverages a Raspberry Pi 5, an AI-enabled camera, and an OmniPreSense OPS243-C radar sensor to process video and radar data locally, sending only processed results to cloud services for aggregation and reporting. This approach reduces bandwidth, increases privacy, and enables rapid response to traffic events.

**Objectives:**
- Deploy a low-cost, scalable, and reliable edge-based traffic monitoring solution
- Integrate ML/AI for vehicle detection, classification, and anomaly detection
- Fuse camera and radar data for accurate speed and event measurement
- Provide real-time dashboards and cloud-based analytics

---

## Overview of Design Concepts

The system is built around a modular, container-friendly architecture that supports local ML inference and data fusion, a real-time web dashboard (Edge UI), and cloud integration for historical analytics and alerts (Cloud UI). The high-level design includes:

- Edge device (Raspberry Pi 5) with direct-attached sensors (AI camera, radar) and storage (SSD)
- Local processing of video and radar data for vehicle detection and speed analysis
- Data fusion engine for correlating sensor data
- Edge API and UI for real-time monitoring and management
- Secure remote access via Tailscale VPN
- Cloud services for aggregation, analytics, and alerting


#### Example Data Flow (from Use Cases)

```text
Vehicle
	|
	v
+--------+    +--------+    +--------+    +--------+    +--------+
| Camera |--->| Radar  |--->| Fusion |--->| Storage|--->| Cloud? |
+--------+    +--------+    +--------+    +--------+    +--------+
	2            2            3            4            5
```

#### Executive Summary System Architecture Diagram

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

---

## Detailed Solution Architecture

### Overview

The student comprehensively presents how the proposed design fits into the overall project structure. The overview is well-written, void of mistakes, and makes the purpose, relevance, and design goals clear.

### Object and Data Elements

The student comprehensively describes all objects with UML diagrams, detailing the purpose and characteristics of all data elements, data sources, and collection methods; information and justifications are accurate and appropriate. The diagrams accurately reflect the systems and do not have any major or minor issues that need to be addressed.

### System Diagrams (or Alternative Criteria)

#### Component Interaction Diagram
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

#### Sequence Diagram (Typical Event Flow)
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

#### Deployment Diagram (Physical/Virtual Placement)
```text
+-------------------+         +-------------------+         +-------------------+
|  Cloud Services   |<------->| Local Network     |<------->| Edge Device       |
|  (AWS, Web UI)    |         | (WiFi/Ethernet)   |         | (Raspberry Pi 5)  |
+-------------------+         +-------------------+         +-------------------+
```

#### CI/CD Deployment Architecture
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

#### Database Entity-Relationship Diagram (ERD)
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

### Collaboration Diagrams and/or Sequence Diagrams

The student provides detailed, in-depth diagrams showing the workflows of components/packages/classes inside the architecture. The diagrams accurately reflect the processes and do not have any major or minor issues that need to be addressed.

### Algorithms

The student comprehensively and accurately describes all of the project algorithms; information and justifications are accurate and appropriate. The student includes all of the detailed performance analyses and metrics and does not have any major or minor issues that need to be addressed.

### Detailed Specifications

The student comprehensively presents detailed specifications for all screens, interfaces and integration points, processes, conversions, and reports. The information and justifications are accurate and appropriate. Extensive evidence, details, and examples are provided.

### Requirements

#### Hardware Requirements

- **Raspberry Pi 5** (16GB RAM, ARM Cortex-A76 CPU, VideoCore VII GPU)
- **AI Camera:** Sony IMX500 sensor (12MP, on-chip AI processing)
- **OPS243-C FMCW Doppler Radar Sensor** (24.125 GHz, UART/Serial, 200m range)
- **External USB SSD:** Samsung T7 Shield 2TB
- **MicroSD Card:** 256GB (UHS-I Class 10)
- **Power & Connectivity:** Official Raspberry Pi 5 PSU (5.1V, 5A, 25W), PoE+ HAT, WiFi/Ethernet, optional cellular backup, UPS
- **Environmental Housing:** IP65/IP66 weatherproof enclosure

#### Software & Technology Requirements

- **Operating System:** Raspberry Pi OS (64-bit recommended)
- **Programming Language:** Python 3
- **Machine Learning Frameworks:** TensorFlow, PyTorch, ONNX (for model training and inference)
- **Computer Vision:** OpenCV
- **Web Framework:** Flask, Flask-SocketIO
- **Containerization:** Docker (recommended for deployment)
- **Communication:** WebSocket, REST API, UART/Serial (for radar), MQTT (optional for cloud)
- **Edge UI:** Local Web Dashboard (browser-based)
- **Remote Access:** Tailscale VPN

#### Python Packages (examples)

- tensorflow
- opencv-python
- flask
- flask-socketio
- picamera2
- gpiozero
- RPi.GPIO

#### Additional Notes

- Cloud build uses general packages (tensorflow, opencv, flask, etc.)
- Pi runtime installs hardware-specific packages (picamera2, gpiozero, RPi.GPIO)
- Regularly update dependencies and scan for vulnerabilities (pip-audit, safety, etc.)

These requirements ensure robust edge processing, secure remote access, and reliable data collection and analytics for the traffic monitoring system.

### Security (or Alternative Criteria)

The student comprehensively describes all of the approaches and resources required to assure system security; information and justifications are accurate and appropriate. OR If there are no security issues for the system, the student comprehensively presents a detailed explanation of why, information and justifications are accurate and appropriate.
