# Technical Design Document

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Technical Team  

## Table of Contents
1. [System Overview](#1-system-overview)
2. [System Architecture](#2-system-architecture)
3. [Hardware Design](#3-hardware-design)
4. [Database Schema](#4-database-schema)
5. [API Specifications](#5-api-specifications)
6. [Data Processing Pipeline](#6-data-processing-pipeline)
7. [Security Considerations](#7-security-considerations)
8. [Performance Specifications](#8-performance-specifications)

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

### Unified Architecture Diagram
![System Architecture Diagram](../traffic_monitoring_architecture.svg)

*Figure 1: System Architecture Diagram*

![Data Flow Diagram](../traffic_algorithms_data_diagram.svg)

*Figure 2: Data Flow from Sensors to Analytics and Dashboards*

### Architecture Layers
**Layer 1: Physical Sensing Layer**
- Raspberry Pi AI Camera (Sony IMX500 sensor)
- OPS243-C FMCW Doppler Radar Sensor
- Raspberry Pi 5 (16GB RAM, ARM Cortex-A76 CPU)
- External USB SSD (Samsung T7 or similar)
- Power & Connectivity (PoE, WiFi/Ethernet, optional cellular backup)

**Layer 2: Edge Processing Layer (Raspberry Pi 5)**
- Vehicle Detection Service (TensorFlow + OpenCV + AI Camera)
- Speed Analysis Service (OPS243-C radar data processing)
- Multi-Vehicle Tracking (SORT algorithm)
- Data Fusion Engine (Camera + Radar correlation)
- Edge API Gateway (Flask/Flask-SocketIO server)
- Edge UI (Local Web Dashboard)
- System Health Monitor, Local Storage Manager

**Layer 3: Network & Communication Layer**
- Local Network Interface (WiFi/Ethernet)
- WebSocket Server (real-time streaming)
- REST API Endpoints (configuration/status)
- Data Compression & Queuing
- Network Resilience (offline-first, reconnection logic)

**Layer 4: Cloud Services Layer (Optional)**
- Data Aggregation Service (AWS Lambda, DynamoDB, or similar)
- Time Series Database, Analytics Engine
- Cloud UI (Web Dashboard), Alert Service, API Gateway

### Technologies and Protocols Used
- Python 3, TensorFlow, OpenCV, Flask, Flask-SocketIO
- UART/Serial for radar communication
- WebSocket/REST for dashboard and API
- MQTT (optional, for cloud data transmission)
- Docker (recommended for deployment)

## 3. Hardware Design

### Component Selection Justification
| Component | Model/Type | Justification |
|-----------|------------|--------------|
| Raspberry Pi | 5 (16GB RAM, ARM Cortex-A76) | High performance, low power, supports edge ML workloads |
| AI Camera | Sony IMX500 | Integrated AI processing, efficient for real-time vehicle detection |
| Radar Sensor | OmniPreSense OPS243-C | Accurate Doppler-based speed measurement, UART interface compatible with Pi |
| Storage | Samsung T7 SSD, 256GB MicroSD | Fast, reliable local storage for buffering and logging |
| Power | PoE, USB-C | Flexible deployment, supports remote locations |

### GPIO Pin Mapping (Raspberry Pi 5 ↔ OPS243-C Radar Sensor)
| OPS243-C Pin | Function | Connects to Pi Pin | Pi GPIO | Description |
|--------------|----------|--------------------|---------|-------------|
| 9            | Power (5V)| 2 or 4 (5V)        | -       | Regulated 5V power supply |
| 10           | Ground   | 6, 9, 14, 20, etc. | -       | Common ground connection |
| 6            | UART RxD | 8 (TXD)            | GPIO 14 | Data transmission from Pi to sensor |
| 7            | UART TxD | 10 (RXD)           | GPIO 15 | Data reception from sensor to Pi |
| 3 (optional) | Interrupt| 12 (GPIO 18)       | GPIO 18 | Hardware interrupt for event notification |
| 4 (optional) | Reset    | 16 (GPIO 23)       | GPIO 23 | Hardware reset control |

#### Enclosure and Pinout Visuals
![Enclosure Inside](../ResidentialRadarEnclosureInside.jpg)
*Figure 3: Inside View of Residential Radar Enclosure*

![Enclosure Installed](../ResidentialRadarEnclosureInstalled.jpg)
*Figure 4: Installed Enclosure on Site*

![Radar Sensor Board Pinout](../ResidentialRadarEnclosureRadarSensorBoardPinout.jpg)
*Figure 5: Radar Sensor Board Pinout*

![Radar Sensor Pinout](../ResidentialRadarEnclosureRadarSensorPinout.jpg)
*Figure 6: Radar Sensor Pinout Reference*

![Enclosure External View](../ResidentialRadarEnclosureView.jpg)
*Figure 7: External View of Enclosure*
### Additional Hardware Connections
| Component | Interface | Connection Details |
|-----------|-----------|-------------------|
| AI Camera | CSI-2 Ribbon | Connect to Camera port on Pi 5 |
| USB SSD | USB 3.0 | Any available USB 3.0 port for high-speed storage |
| Power | PoE+ or USB-C | 5V/5A minimum, PoE+ preferred for remote deployment |
| Network | Ethernet/WiFi | Built-in Gigabit Ethernet or WiFi 6 |

### UART Configuration Requirements
- Enable UART in `/boot/firmware/config.txt`: `enable_uart=1`
- Disable console on serial: `console=tty1` (remove `console=serial0,115200`)
- Set UART parameters: 9600 baud, 8N1 (8 data bits, no parity, 1 stop bit)
- Install required Python packages: `pyserial`, `RPi.GPIO`

**Note:** UART must be enabled on the Pi. See [Implementation Guide](./Implementation_Deployment.md) for detailed setup instructions.

## 4. Database Schema

### Entity Relationship Diagram (ERD)
The system uses a relational database (PostgreSQL) to store detected vehicles, radar events, and system logs. The ERD includes the following main entities:

### Table Specifications

#### VehicleEvent
Stores each detected vehicle event with fused camera and radar data.
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique event identifier |
| timestamp | TIMESTAMP | NOT NULL | Event occurrence time (UTC) |
| location | VARCHAR(100) | | Installation location identifier |
| vehicle_type | VARCHAR(20) | | Car, truck, motorcycle, etc. |
| speed_mph | DECIMAL(5,2) | | Vehicle speed in miles per hour |
| confidence | DECIMAL(3,2) | 0.00-1.00 | Detection confidence score |
| radar_reading_id | INTEGER | FOREIGN KEY | Reference to RadarReading |
| camera_detection_id | INTEGER | FOREIGN KEY | Reference to CameraDetection |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

#### RadarReading
Stores raw and processed radar sensor data.
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique reading identifier |
| event_time | TIMESTAMP | NOT NULL | Sensor reading timestamp |
| speed_mph | DECIMAL(5,2) | | Measured speed in mph |
| range_feet | DECIMAL(6,2) | | Distance to detected object |
| raw_json | JSONB | | Complete raw sensor data |
| processed | BOOLEAN | DEFAULT FALSE | Processing status flag |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

#### CameraDetection
Stores AI camera detection results with bounding box data.
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique detection identifier |
| event_time | TIMESTAMP | NOT NULL | Detection timestamp |
| vehicle_type | VARCHAR(20) | | Detected vehicle classification |
| confidence | DECIMAL(3,2) | 0.00-1.00 | Classification confidence |
| bbox_x | INTEGER | | Bounding box X coordinate |
| bbox_y | INTEGER | | Bounding box Y coordinate |
| bbox_width | INTEGER | | Bounding box width |
| bbox_height | INTEGER | | Bounding box height |
| image_path | VARCHAR(255) | | Path to captured image (optional) |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

#### SystemLog
Records system health, errors, and operational events.
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique log entry identifier |
| log_time | TIMESTAMP | NOT NULL | Log entry timestamp |
| level | VARCHAR(10) | NOT NULL | DEBUG, INFO, WARN, ERROR |
| component | VARCHAR(50) | | System component name |
| message | TEXT | | Log message content |
| details | JSONB | | Additional structured data |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

### Database Indexes
```sql
-- Performance indexes for common queries
CREATE INDEX idx_vehicle_event_timestamp ON VehicleEvent(timestamp);
CREATE INDEX idx_radar_reading_event_time ON RadarReading(event_time);
CREATE INDEX idx_camera_detection_event_time ON CameraDetection(event_time);
CREATE INDEX idx_system_log_level_time ON SystemLog(level, log_time);
```

### Table Structures and Key Fields

**VehicleEvent**
- id (PK)
- timestamp (UTC)
- location (text or coordinates)
- source (camera, radar, fusion)
- radar_reading_id (FK)
- camera_detection_id (FK)

**RadarReading**
- id (PK)
- event_time (UTC)
- speed (float, m/s)
- range (float, m)
- raw_json (JSONB, full sensor output)

**CameraDetection**
- id (PK)
- event_time (UTC)
- vehicle_type (text)
- confidence (float)
- bbox_x, bbox_y, bbox_w, bbox_h (int, bounding box coordinates)

**SystemLog**
- id (PK)
- log_time (UTC)
- level (info, warning, error)
- message (text)

## 5. Key API Specifications

The system exposes REST and WebSocket APIs for local dashboard access, system configuration, and cloud integration. Below are the main endpoints and their purposes.

### Backend (Flask/Flask-SocketIO)

**REST Endpoints:**

- `GET /api/vehicle_events` — Retrieve recent vehicle events
- `GET /api/radar_readings` — Retrieve recent radar readings
- `GET /api/camera_detections` — Retrieve recent camera detections
- `POST /api/config` — Update system configuration (e.g., thresholds, network)
- `GET /api/health` — System health/status check

**WebSocket Events:**
- `vehicle_event` — Real-time push of new vehicle events
- `system_status` — Real-time system health updates

**Example REST Request:**
```
GET /api/vehicle_events?limit=10
Response:
[
  {
    "id": 123,
    "timestamp": "2025-08-07T14:32:00Z",
    "location": "Maple St & 5th Ave",
    "source": "fusion",
    "radar_reading_id": 456,
    "camera_detection_id": 789
  },
  ...
]
```

**Example WebSocket Event:**
```
{
  "event": "vehicle_event",
  "data": {
    "timestamp": "2025-08-07T14:32:00Z",
    "vehicle_type": "car",
    "speed": 12.3,
    "location": "Maple St & 5th Ave"
  }
}
```

### Dashboard (Edge UI & Cloud UI)

- Consumes the above APIs for real-time and historical data display
- Provides user authentication (Cloud UI)
- Allows configuration and monitoring of edge devices

**Note:** Mobile app (if implemented) would use the same API endpoints as the dashboard.

## 6. Data Processing Pipeline

### Data Flow: Sensor to Dashboard
1. **Sensing:**
   - The AI Camera captures video frames; the OPS243-C radar sensor measures vehicle speed and range.
2. **Edge Processing:**
   - Video frames are processed by a TensorFlow/OpenCV pipeline for vehicle detection and classification.
   - Radar data is parsed and filtered for valid speed events.
3. **Data Fusion:**
   - Detected vehicles from the camera are correlated with radar speed readings using timestamp and spatial proximity.
   - Fused events are created, combining vehicle type, speed, and location.
4. **Event Logging:**
   - Fused events, raw radar readings, and camera detections are stored in the local database.
5. **Visualization & API:**
   - Real-time events are streamed to the Edge UI dashboard via WebSocket.
   - Historical and summary data is available via REST API.
6. **Cloud Sync (Optional):**
   - Processed events are periodically uploaded to the cloud for aggregation, analytics, and alerting.

### ML/AI Integration
- **Vehicle Detection:** TensorFlow (object detection model) and OpenCV are used to identify and classify vehicles in real time.
- **Tracking:** SORT (Simple Online and Realtime Tracking) algorithm is used for multi-vehicle tracking across frames.
- **Anomaly Detection:** Optional ML models can flag unusual traffic patterns or events.

### Data Fusion & Analytics
- **Fusion Logic:** Combines camera and radar data to improve accuracy of speed and vehicle type assignment.
- **Analytics:**
  - Real-time: Vehicle counts, speed distributions, violation detection (e.g., speeding)
  - Historical: Aggregated traffic trends, anomaly reports, and system health metrics

## 7. Security Considerations

### Edge Device Security
- **Physical Security:** Secure enclosure with tamper detection, locked access panels
- **Boot Security:** Secure boot process, encrypted file system (LUKS)
- **Network Security:** VPN tunneling for cloud communication, firewall configuration
- **Access Control:** SSH key-based authentication, disabled default passwords

### API Security
- **Authentication:** JWT tokens or API keys for all endpoints
- **Authorization:** Role-based access control (RBAC) for different user types
- **Encryption:** HTTPS/TLS 1.3 for all API communication
- **Rate Limiting:** Prevent DoS attacks with request throttling

### Data Privacy & Compliance
- **Data Minimization:** Store only necessary metadata, avoid personal identification
- **Anonymization:** Blur license plates, faces in stored video data
- **Retention Policy:** Automatic deletion of old data per privacy requirements
- **Compliance:** GDPR, CCPA, and local privacy law adherence

### System Monitoring
- **Intrusion Detection:** Monitor for unauthorized access attempts
- **Audit Logging:** Comprehensive logs of all system activities
- **Security Updates:** Automated security patching and vulnerability management
- **Backup Security:** Encrypted backups with secure key management

## 8. Performance Specifications

### Processing Performance
- **Video Processing:** 30 FPS at 1080p resolution
- **Detection Latency:** < 100ms from frame capture to detection result
- **API Response Time:** < 50ms for GET requests, < 200ms for POST requests
- **Database Query Performance:** < 10ms for typical queries

### Accuracy Metrics
- **Vehicle Detection:** > 95% precision, > 90% recall
- **Speed Measurement:** ± 2 mph accuracy at speeds up to 60 mph
- **Vehicle Classification:** > 85% accuracy for car/truck/motorcycle
- **System Uptime:** > 99.5% availability target

### Resource Utilization
- **CPU Usage:** < 70% average during normal operation
- **Memory Usage:** < 12GB of 16GB available RAM
- **Storage I/O:** < 50MB/s sustained write rate
- **Network Bandwidth:** < 1 Mbps for cloud synchronization

### Environmental Specifications
- **Operating Temperature:** -20°C to +60°C (-4°F to +140°F)
- **Humidity:** 5% to 95% non-condensing
- **Power Consumption:** < 25W including all peripherals
- **MTBF (Mean Time Between Failures):** > 8760 hours (1 year)

## 9. Future Work & Clarifications

### Future Work
- **Stop Sign Violation Detection:** Planned for future implementation. The current system focuses on speed and general vehicle detection. Stop sign violation detection is a key roadmap feature (see [GitHub repo](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)).
- **Alert/Notification System:** Customizable alerting is planned. Current documentation describes the architecture; implementation is in progress.
- **Cloud/Remote Monitoring:** Cloud UI and analytics are described in the documentation. Full cloud integration and remote monitoring are planned enhancements.
- **User Interface Enhancements:** Ongoing improvements to dashboard usability and configuration options.
- **Detection Accuracy:** Improve performance in challenging lighting and weather conditions.
- **Advanced Deep Learning:** Explore new ML models for better detection/classification.

### Contradictions & Clarifications
- The GitHub repository emphasizes stop sign violation detection and customizable alerts as core features. The current deployed system focuses on speed and vehicle detection; stop sign and advanced alerting are future work.
- Both sources mention cloud/remote monitoring. The documentation describes the intended architecture; some features may be in development.
- The dashboard is described as implemented in the documentation, but the GitHub repo lists it as future work. Clarify the current status in project updates.

### Repository Reference
- For code, structure, and contribution guidelines, see: [CST_590_Computer_Science_Capstone_Project GitHub](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)
