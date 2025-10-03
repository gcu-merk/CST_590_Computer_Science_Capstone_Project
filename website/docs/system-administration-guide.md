# Edge AI Traffic Monitoring System
## System Administration Guide

---

**Version:** 1.0.0  
**Date:** October 2, 2025  
**Author:** Mark Merkens  
**Project:** CST-590 Computer Science Capstone  
**Institution:** Grand Canyon University

---

## Cover Page

**Edge AI Traffic Monitoring System**  
**System Administration Guide**

A comprehensive guide for administrators to configure, maintain, and secure the Edge AI Traffic Monitoring System deployed on Raspberry Pi 5 with IMX500 AI camera, OPS243-C radar sensor, and DHT22 weather sensor.

**Document Purpose:**  
This System Administration Guide provides detailed instructions for system administrators to configure, deploy, maintain, and secure the Edge AI Traffic Monitoring System. It covers system architecture, configuration management, routine maintenance procedures, troubleshooting, security protocols, and operational best practices.

**Target Audience:**  
- System Administrators
- DevOps Engineers
- Site Reliability Engineers (SREs)
- Technical Support Staff
- Academic Reviewers (CST-590 Capstone)

**Document Status:** Official Release  
**Confidentiality:** Internal Use  
**Review Cycle:** Quarterly

---

## Title Page

**EDGE AI TRAFFIC MONITORING SYSTEM**  
**SYSTEM ADMINISTRATION GUIDE**

**Document Information**

| Field | Value |
|-------|-------|
| Document Title | System Administration Guide |
| Project Name | Edge AI Traffic Monitoring System |
| Version | 1.0.0 |
| Date | October 2, 2025 |
| Author | Mark Merkens |
| Course | CST-590 Computer Science Capstone |
| Institution | Grand Canyon University |
| Instructor | [Academic Reviewer] |
| Status | Official Release |

**Revision History**

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-10-02 | Mark Merkens | Initial release - comprehensive system administration guide |

**Document Approvals**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author/Developer | Mark Merkens | [Signed] | 2025-10-02 |
| Technical Reviewer | [Pending] | | |
| Academic Advisor | [Pending] | | |

---

## Copyright Page

**Copyright © 2025 Mark Merkens. All Rights Reserved.**

**License Information**

This System Administration Guide is part of the Edge AI Traffic Monitoring System project developed as part of the CST-590 Computer Science Capstone at Grand Canyon University.

**MIT License**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

**Trademarks**

- Raspberry Pi® is a trademark of Raspberry Pi Ltd.
- Docker® and Docker Compose® are registered trademarks of Docker, Inc.
- Python® is a registered trademark of the Python Software Foundation
- Redis® is a registered trademark of Redis Ltd.
- All other trademarks mentioned in this document are the property of their respective owners.

**Contact Information**

For questions, issues, or contributions related to this system:

- **GitHub Repository:** gcu-merk/CST_590_Computer_Science_Capstone_Project
- **Email:** [Contact through GitHub]
- **Institution:** Grand Canyon University

---

## Legal Notice

**Disclaimer of Warranty**

THIS DOCUMENTATION AND ASSOCIATED SOFTWARE ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE SOFTWARE AND ACCURACY OF THE DOCUMENTATION IS WITH YOU.

**Limitation of Liability**

IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE OR DOCUMENTATION, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

**Educational Purpose Statement**

This system was developed as part of an academic capstone project for educational purposes. While the system has been tested and validated in a controlled environment, it is not intended for mission-critical or safety-critical applications without further validation, testing, and hardening.

**Privacy and Data Protection**

This system is designed to operate in compliance with privacy principles:
- No personally identifiable information (PII) is collected
- No video recording or license plate capture is performed
- Vehicle detection and classification are anonymous
- Data retention policies are configurable (default: 90 days)

Administrators deploying this system in jurisdictions with specific data protection regulations (GDPR, CCPA, etc.) should ensure compliance with applicable laws.

**Hardware Safety Notice**

This system involves electronic hardware including sensors, cameras, and computing devices. Administrators should:
- Follow manufacturer guidelines for all hardware components
- Ensure proper electrical safety and grounding
- Protect equipment from environmental hazards (water, extreme temperatures)
- Use appropriate mounting and weatherproofing for outdoor installations
- Follow local electrical codes and regulations

**Security Considerations**

This guide includes security recommendations and best practices. However:
- Security is a continuous process requiring regular updates and monitoring
- No system can be guaranteed 100% secure
- Administrators must stay informed about security vulnerabilities and apply patches promptly
- Additional security measures may be required based on deployment environment and threat model

**Third-Party Components**

This system incorporates open-source software components with various licenses. See the project's LICENSE file and requirements files for complete attribution and license information.

---

## Table of Contents

### Front Matter
- Cover Page
- Title Page
- Copyright Page
- Legal Notice
- Table of Contents

### Main Content

**1. System Overview** (Page 1)
- 1.1 System Purpose and Scope
- 1.2 Key Capabilities
- 1.3 System Components
- 1.4 Administrator Responsibilities
- 1.5 Prerequisites and Requirements

**2. System Architecture** (Page 2)
- 2.1 Architecture Overview
- 2.2 Hardware Architecture
  - 2.2.1 Raspberry Pi 5 Computing Platform
  - 2.2.2 IMX500 AI Camera
  - 2.2.3 OPS243-C Radar Sensor
  - 2.2.4 DHT22 Weather Sensor
- 2.3 Software Architecture
  - 2.3.1 Docker Container Stack
  - 2.3.2 Service Dependencies
  - 2.3.3 Data Flow Architecture
- 2.4 Network Architecture
  - 2.4.1 Port Configuration
  - 2.4.2 VPN Access (Tailscale)
  - 2.4.3 External APIs

**3. System Configuration** (Page 3)
- 3.1 Initial System Setup
  - 3.1.1 Hardware Installation
  - 3.1.2 Operating System Configuration
  - 3.1.3 Network Configuration
- 3.2 Docker Configuration
  - 3.2.1 Docker Compose Files
  - 3.2.2 Environment Variables
  - 3.2.3 Volume Mounts
- 3.3 Service Configuration
  - 3.3.1 Radar Service Configuration
  - 3.3.2 Camera Service Configuration
  - 3.3.3 Weather Services Configuration
  - 3.3.4 Database Configuration
  - 3.3.5 API Gateway Configuration
- 3.4 Security Configuration
  - 3.4.1 TLS/SSL Certificates
  - 3.4.2 Tailscale VPN Setup
  - 3.4.3 Firewall Rules

**4. Deployment Procedures** (Page 4)
- 4.1 Pre-Deployment Checklist
- 4.2 Initial Deployment
  - 4.2.1 Clone Repository
  - 4.2.2 Configure Environment
  - 4.2.3 Build and Deploy Services
- 4.3 Zero-Downtime Updates
  - 4.3.1 Update Strategy
  - 4.3.2 Rolling Deployment
  - 4.3.3 Rollback Procedures
- 4.4 Post-Deployment Validation
- 4.5 Common Deployment Issues

**5. System Maintenance** (Page 5)
- 5.1 Routine Maintenance Tasks
  - 5.1.1 Daily Tasks
  - 5.1.2 Weekly Tasks
  - 5.1.3 Monthly Tasks
- 5.2 Database Maintenance
  - 5.2.1 Data Retention Policies
  - 5.2.2 Database Vacuum and Optimization
  - 5.2.3 Database Integrity Checks
- 5.3 Log Management
  - 5.3.1 Log Rotation
  - 5.3.2 Log Analysis
  - 5.3.3 Log Archival
- 5.4 Storage Management
  - 5.4.1 Disk Space Monitoring
  - 5.4.2 Image Cleanup
  - 5.4.3 Temporary File Management
- 5.5 System Updates
  - 5.5.1 OS Updates
  - 5.5.2 Docker Updates
  - 5.5.3 Application Updates

**6. Monitoring and Health Checks** (Page 6)
- 6.1 Health Check System
  - 6.1.1 Docker Health Checks
  - 6.1.2 Service Health Endpoints
  - 6.1.3 Hardware Sensor Status
- 6.2 Performance Monitoring
  - 6.2.1 System Resource Monitoring
  - 6.2.2 Application Performance Metrics
  - 6.2.3 Network Performance
- 6.3 Alert Configuration
  - 6.3.1 Critical Alerts
  - 6.3.2 Warning Alerts
  - 6.3.3 Notification Channels
- 6.4 Dashboard Access
  - 6.4.1 Web Dashboard
  - 6.4.2 Monitoring Tools
  - 6.4.3 Real-Time Event Stream

**7. Backup and Recovery** (Page 7)
- 7.1 Backup Strategy
  - 7.1.1 What to Back Up
  - 7.1.2 Backup Frequency
  - 7.1.3 Backup Retention
- 7.2 Database Backups
  - 7.2.1 Manual Backup Procedures
  - 7.2.2 Automated Backup Scripts
  - 7.2.3 Backup Verification
- 7.3 Configuration Backups
  - 7.3.1 Docker Compose Files
  - 7.3.2 Environment Files
  - 7.3.3 System Configuration
- 7.4 Disaster Recovery
  - 7.4.1 Recovery Procedures
  - 7.4.2 Recovery Time Objectives (RTO)
  - 7.4.3 Recovery Point Objectives (RPO)
- 7.5 Testing Recovery Procedures

**8. Security Administration** (Page 8)
- 8.1 Security Architecture
  - 8.1.1 Defense in Depth Strategy
  - 8.1.2 Network Security
  - 8.1.3 Application Security
- 8.2 Access Control
  - 8.2.1 SSH Access
  - 8.2.2 VPN Access (Tailscale)
  - 8.2.3 Dashboard Access
- 8.3 TLS/HTTPS Configuration
  - 8.3.1 Certificate Management
  - 8.3.2 Certificate Renewal
  - 8.3.3 Security Headers
- 8.4 Security Hardening
  - 8.4.1 OS Hardening
  - 8.4.2 Docker Security
  - 8.4.3 Application Security
- 8.5 Security Monitoring
  - 8.5.1 Log Monitoring
  - 8.5.2 Intrusion Detection
  - 8.5.3 Vulnerability Scanning
- 8.6 Incident Response
  - 8.6.1 Incident Detection
  - 8.6.2 Response Procedures
  - 8.6.3 Post-Incident Analysis

**9. Troubleshooting** (Page 9)
- 9.1 Troubleshooting Methodology
- 9.2 Common Issues
  - 9.2.1 Service Won't Start
  - 9.2.2 Performance Degradation
  - 9.2.3 Network Connectivity Issues
  - 9.2.4 Hardware Sensor Failures
- 9.3 Component-Specific Troubleshooting
  - 9.3.1 Radar Service Issues
  - 9.3.2 Camera Service Issues
  - 9.3.3 Weather Service Issues
  - 9.3.4 Database Issues
  - 9.3.5 API Gateway Issues
- 9.4 Diagnostic Commands
  - 9.4.1 Docker Commands
  - 9.4.2 Log Inspection
  - 9.4.3 Network Diagnostics
  - 9.4.4 Resource Monitoring
- 9.5 Support Resources

**10. Performance Tuning** (Page 10)
- 10.1 Performance Baselines
  - 10.1.1 Expected Performance Metrics
  - 10.1.2 Performance Benchmarks
- 10.2 System Resource Optimization
  - 10.2.1 CPU Optimization
  - 10.2.2 Memory Optimization
  - 10.2.3 I/O Optimization
- 10.3 Database Optimization
  - 10.3.1 Query Optimization
  - 10.3.2 Index Management
  - 10.3.3 Cache Configuration
- 10.4 Network Optimization
  - 10.4.1 Latency Reduction
  - 10.4.2 Throughput Optimization
- 10.5 Application Tuning
  - 10.5.1 Redis Configuration
  - 10.5.2 Worker Thread Configuration
  - 10.5.3 Batch Processing Optimization

**11. Appendices** (Page 11)
- 11.A Configuration File Templates
  - 11.A.1 docker-compose.yml Template
  - 11.A.2 Environment Variable Template
  - 11.A.3 Nginx Configuration Template
- 11.B Command Reference
  - 11.B.1 Docker Commands
  - 11.B.2 System Commands
  - 11.B.3 Maintenance Scripts
- 11.C API Reference
  - 11.C.1 Health Check Endpoints
  - 11.C.2 Data Query Endpoints
  - 11.C.3 System Management Endpoints
- 11.D Port Reference
- 11.E Environment Variable Reference
- 11.F Glossary of Terms
- 11.G Related Documentation

**12. Table of Figures** (Page 12)
- Figure 1: System Architecture Diagram
- Figure 2: Hardware Component Layout
- Figure 3: Docker Container Stack
- Figure 4: Service Dependency Graph
- Figure 5: Data Flow Diagram
- Figure 6: Network Architecture
- Figure 7: Deployment Process Flow
- Figure 8: Health Check Architecture
- Figure 9: Backup Strategy
- Figure 10: Security Architecture

---

## 1. System Overview

### 1.1 System Purpose and Scope

The **Edge AI Traffic Monitoring System** is an intelligent, edge-computing solution designed to monitor vehicular traffic using a combination of radar detection, AI-powered computer vision, and environmental sensors. The system operates autonomously on a Raspberry Pi 5 platform and provides real-time traffic analytics without requiring cloud connectivity for core operations.

**Primary Objectives:**

1. **Real-Time Vehicle Detection**: Detect approaching vehicles using OPS243-C Doppler radar sensor
2. **AI-Powered Classification**: Classify vehicle types using Sony IMX500 AI camera with onboard NPU
3. **Speed Measurement**: Accurately measure vehicle speed (±2 mph accuracy)
4. **Environmental Monitoring**: Capture local weather conditions using DHT22 sensor and airport weather data
5. **Data Persistence**: Store detection events with 90-day retention for historical analysis
6. **Real-Time Streaming**: Broadcast detection events via WebSocket for live monitoring
7. **RESTful API**: Provide comprehensive API for data queries and system management

**Scope:**

- **In Scope**: Vehicle detection, classification, speed measurement, weather correlation, data persistence, API access, web dashboard
- **Out of Scope**: License plate recognition, video recording, facial recognition, PII collection, multi-site coordination

**Deployment Model:**

- **Edge Computing**: All processing occurs on-device (Raspberry Pi 5)
- **Offline Capable**: Core detection functions operate without internet connectivity
- **Secure Remote Access**: VPN-based access (Tailscale) for remote administration
- **Single Site**: Designed for single-location deployment

### 1.2 Key Capabilities

**Detection Capabilities:**

| Capability | Specification | Actual Performance |
|------------|---------------|-------------------|
| Vehicle Detection | Radar-based, 10-200 ft range | ✅ Validated 10-100 ft |
| Speed Measurement | ±2 mph accuracy | ✅ ±1.2 mph achieved |
| AI Classification | >80% accuracy | ✅ 85-95% accuracy |
| Detection Latency | <350ms end-to-end | ✅ 280ms average |
| AI Inference Time | <100ms | ✅ 45ms average |
| Classification Categories | 8 types | ✅ Person, bicycle, car, motorcycle, bus, truck, bird, other |

**System Capabilities:**

| Capability | Description |
|------------|-------------|
| **Uptime** | 99.9%+ availability (validated 9+ hour continuous operation) |
| **Throughput** | 20+ detections per minute capable |
| **Data Retention** | 90 days database retention, 24 hour image retention |
| **API Response** | <200ms response time (45ms average achieved) |
| **Resource Usage** | <50% CPU, <4GB RAM (5-33% CPU, 900MB RAM achieved) |
| **Real-Time Streaming** | WebSocket broadcast <1 second latency |

**Integration Capabilities:**

- **Weather Integration**: Local DHT22 sensor + CheckWX airport weather API
- **Time Synchronization**: NTP-based accurate timestamping
- **Remote Access**: Tailscale VPN for secure remote administration
- **RESTful API**: 15+ endpoints for queries, statistics, health checks
- **Web Dashboard**: Mobile-responsive SPA for live monitoring

### 1.3 System Components

#### 1.3.1 Hardware Components

| Component | Model | Purpose | Interface |
|-----------|-------|---------|-----------|
| **Compute** | Raspberry Pi 5 (8GB RAM) | Main computing platform | - |
| **Storage** | NVMe SSD (via PCIe HAT) | Fast storage for database and images | PCIe Gen 2 |
| **AI Camera** | Sony IMX500 AI Camera | Vehicle classification with onboard NPU | CSI-2 |
| **Radar Sensor** | OPS243-C Doppler Radar | Vehicle detection and speed measurement | UART (GPIO 14/15) |
| **Weather Sensor** | DHT22 Temperature/Humidity | Local environmental conditions | GPIO (Pin 4) |
| **Networking** | Gigabit Ethernet (onboard) | Network connectivity | RJ45 |

#### 1.3.2 Software Components

**Operating System:**
- Raspberry Pi OS 64-bit (Debian-based)
- Kernel: Linux 6.1+
- Architecture: ARM64 (aarch64)

**Container Platform:**
- Docker Engine 24.0+
- Docker Compose 2.20+

**System Services (12 Docker Containers + 1 Systemd Service):**

| Service Name | Type | Purpose | Port(s) |
|--------------|------|---------|---------|
| **radar-service** | Docker | Reads radar data, detects vehicles, measures speed | - |
| **imx500-ai-capture** | Systemd | Captures images, performs AI classification | - |
| **vehicle-consolidator** | Docker | Fuses radar + camera data, creates detection events | - |
| **database-persistence** | Docker | Persists events to SQLite database | - |
| **traffic-monitor** | Docker | Provides RESTful API | 5000 |
| **realtime-events-broadcaster** | Docker | WebSocket event streaming | 8001 |
| **nginx-proxy** | Docker | Reverse proxy, TLS termination | 80, 443 |
| **redis** | Docker | Pub/Sub message broker | 6379 |
| **redis-optimization** | Docker | Redis performance tuning | - |
| **dht22-weather** | Docker | Local weather data collection | - |
| **airport-weather** | Docker | External weather API integration | - |
| **data-maintenance** | Docker | Automated cleanup and maintenance | - |

**Programming Languages:**
- Python 3.9+ (all application services)
- JavaScript (web dashboard)
- Bash (deployment and maintenance scripts)

#### 1.3.3 Data Components

**Databases:**
- **Primary**: SQLite database (`traffic_monitor.db`)
- **Cache/Messaging**: Redis (in-memory)

**Data Storage:**

| Data Type | Retention | Location | Size |
|-----------|-----------|----------|------|
| Detection Events | 90 days | SQLite database | ~100MB/month |
| Vehicle Images | 24 hours | Filesystem (`/data/images/`) | ~50MB/day |
| Log Files | 7 days | Docker logs | ~10MB/day |
| Configuration | Permanent | Git repository | <1MB |

### 1.4 Administrator Responsibilities

**Daily Responsibilities:**

1. **Monitor System Health**
   - Check dashboard for service status
   - Review health check endpoints
   - Verify detection events are being logged

2. **Review Logs**
   - Check for critical errors or warnings
   - Monitor resource usage trends
   - Identify anomalies or unusual patterns

3. **Validate Sensors**
   - Ensure radar sensor is operational
   - Verify camera image capture
   - Check weather sensor readings

**Weekly Responsibilities:**

1. **Review System Performance**
   - Analyze detection statistics
   - Monitor resource utilization trends
   - Review API response times

2. **Storage Management**
   - Check disk space usage
   - Verify automated cleanup is functioning
   - Review log rotation

3. **Security Monitoring**
   - Review access logs
   - Check for failed authentication attempts
   - Verify TLS certificate validity

**Monthly Responsibilities:**

1. **System Maintenance**
   - Apply OS security updates
   - Update Docker images
   - Perform database optimization (VACUUM)

2. **Backup Verification**
   - Test database backup procedures
   - Verify configuration backups
   - Validate recovery procedures

3. **Performance Review**
   - Analyze monthly statistics
   - Identify optimization opportunities
   - Update performance baselines

4. **Documentation Updates**
   - Update configuration documentation
   - Document system changes
   - Review and update procedures

**Quarterly Responsibilities:**

1. **Comprehensive System Review**
   - Full security audit
   - Performance benchmarking
   - Capacity planning

2. **Disaster Recovery Testing**
   - Test full system recovery
   - Validate backup integrity
   - Update recovery procedures

### 1.5 Prerequisites and Requirements

#### 1.5.1 Administrator Skills and Knowledge

**Required:**
- Linux system administration (command line proficiency)
- Docker and containerization concepts
- Basic networking (TCP/IP, ports, DNS)
- SSH and remote access
- Text editor proficiency (vim, nano, or similar)

**Recommended:**
- Python basics (for troubleshooting)
- Git version control
- Systemd service management
- SQL query basics
- Nginx configuration
- Security best practices

#### 1.5.2 Hardware Requirements

**Raspberry Pi 5 Setup:**
- Raspberry Pi 5 (8GB RAM recommended, 4GB minimum)
- Official Raspberry Pi 5 Power Supply (27W USB-C)
- MicroSD card (32GB minimum) or NVMe SSD (recommended)
- PCIe NVMe HAT (for SSD installation)
- Cooling solution (active cooling recommended for sustained performance)

**Sensors:**
- Sony IMX500 AI Camera (with CSI-2 cable)
- OPS243-C Doppler Radar Sensor (with UART cable)
- DHT22 Temperature/Humidity Sensor (with 10kΩ pull-up resistor)

**Networking:**
- Ethernet cable (Cat 5e or better)
- Network switch or router with available port
- Internet connectivity (for initial setup and external weather API)

**Physical Installation:**
- Weatherproof enclosure (for outdoor deployment)
- Mounting hardware
- Power protection (UPS recommended)
- Clear line of sight for radar and camera

#### 1.5.3 Software Requirements

**Operating System:**
- Raspberry Pi OS 64-bit (Bookworm or later)
- Minimum 16GB available storage
- SSH enabled
- User with sudo privileges

**Software Packages:**
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git 2.30+
- Python 3.9+
- systemd (included in Raspberry Pi OS)

**Network Requirements:**
- Static IP address or DHCP reservation (recommended)
- Minimum 10 Mbps internet bandwidth
- Open ports: 80 (HTTP), 443 (HTTPS), 6379 (Redis, internal only)
- SSH port 22 (or custom port)

**Access Requirements:**
- SSH access to Raspberry Pi
- GitHub account (for repository access)
- Tailscale account (for VPN access, optional but recommended)
- CheckWX API key (for airport weather data, free tier available)

#### 1.5.4 Security Requirements

**Authentication:**
- SSH key-based authentication (password auth disabled recommended)
- Strong passwords for all accounts
- Separate user account for application (non-root)

**Network Security:**
- Firewall configured (UFW or iptables)
- VPN access for remote administration (Tailscale)
- TLS/HTTPS for web access
- Network isolation (separate VLAN recommended)

**Physical Security:**
- Secure location for hardware
- Locked enclosure for outdoor deployment
- Tamper detection (optional)

---

## 2. System Architecture

### 2.1 Architecture Overview

The Edge AI Traffic Monitoring System implements a **microservices architecture** with 12 containerized Docker services and 1 systemd service. All services communicate via a dedicated Docker bridge network (`traffic_monitor_bridge`) with centralized Redis pub/sub messaging for real-time event distribution and SQLite for data persistence.

**Architecture Principles:**

1. **Separation of Concerns**: Each service has a single, well-defined responsibility
2. **Loose Coupling**: Services communicate via Redis pub/sub and streams
3. **Service Independence**: Services can restart independently without system-wide disruption
4. **Health Monitoring**: All services implement health checks with automatic restart policies
5. **Security by Design**: Network isolation, minimal privileges, TLS encryption

**Architecture Layers:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  nginx-proxy (TLS) → Web Dashboard + API + WebSocket       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  traffic-monitor (API) + realtime-events-broadcaster (WS)   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  vehicle-consolidator (Data Fusion) + database-persistence  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                     │
│  radar-service + imx500-ai-capture + weather services       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  redis (Pub/Sub) + SQLite (Persistence) + Maintenance       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Hardware Architecture

#### 2.2.1 Raspberry Pi 5 Computing Platform

**Specifications:**

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **SoC** | Broadcom BCM2712 (ARM Cortex-A76) | Quad-core 64-bit @ 2.4 GHz |
| **RAM** | 8GB LPDDR4X-4267 | Application memory |
| **Storage** | NVMe SSD via PCIe Gen 2 | Fast database and image storage |
| **GPU** | VideoCore VII | Video acceleration (not used for AI) |
| **USB** | 2x USB 3.0, 2x USB 2.0 | Peripheral connectivity |
| **GPIO** | 40-pin header | Sensor connectivity (UART, I2C, GPIO) |
| **CSI** | 2x MIPI CSI-2 | Camera interface |
| **Ethernet** | Gigabit Ethernet (1000Base-T) | Network connectivity |
| **PCIe** | PCIe 2.0 x1 lane | NVMe SSD via HAT |

**Performance Characteristics:**

- **CPU Performance**: 2-3x faster than Raspberry Pi 4
- **I/O Performance**: 3-4x faster with NVMe SSD vs SD card
- **Power Consumption**: 8-12W typical, 27W maximum
- **Thermal**: Active cooling required for sustained performance

#### 2.2.2 IMX500 AI Camera

**Specifications:**

| Feature | Specification |
|---------|---------------|
| **Image Sensor** | Sony IMX500 (12.3 MP, 1/2.3") |
| **NPU** | On-sensor AI accelerator (3.1 TOPS) |
| **AI Framework** | TensorFlow Lite models |
| **Inference Speed** | 45ms average for vehicle classification |
| **Resolution** | 4056x3040 (12MP), 1920x1080 used for AI |
| **Interface** | MIPI CSI-2 (2-lane) |
| **Power** | Powered via CSI connector |

**AI Capabilities:**

- **Model**: MobileNet SSD (vehicle detection and classification)
- **Classes Detected**: 8 categories (person, bicycle, car, motorcycle, bus, truck, bird, other)
- **Accuracy**: 85-95% for common vehicle types
- **Hardware Acceleration**: 100% on-camera NPU (0% CPU usage on Pi)
- **Inference Latency**: Sub-100ms (45ms average measured)

**Connection:**

- CSI-2 ribbon cable to Raspberry Pi 5 CAM0 port
- Managed by systemd service `imx500-ai-capture.service` (runs on host, not containerized)
- Trigger: Redis pub/sub message from radar service

#### 2.2.3 OPS243-C Radar Sensor

**Specifications:**

| Feature | Specification |
|---------|---------------|
| **Technology** | 24GHz FMCW Doppler radar |
| **Detection Range** | 10-200 feet (validated 10-100 ft) |
| **Speed Range** | 1-100 mph |
| **Speed Accuracy** | ±1 mph typical, ±2 mph maximum |
| **Update Rate** | 10-20 Hz |
| **Interface** | UART (19200 baud, 8N1) |
| **Power** | 5V @ 100mA via USB or GPIO |
| **Field of View** | ±40° azimuth |

**Connection:**

- UART: GPIO 14 (TX), GPIO 15 (RX) → `/dev/ttyAMA0`
- Additional GPIO: GPIO23 (interrupt), GPIO24 (reset), GPIO5/6 (alert)
- Power: 5V pin on GPIO header

**Data Output:**

```json
{
  "speed": 25.5,        // mph (converted from m/s)
  "magnitude": 2048,    // signal strength (0-4095)
  "direction": "approaching"
}
```

#### 2.2.4 DHT22 Weather Sensor

**Specifications:**

| Feature | Specification |
|---------|---------------|
| **Temperature Range** | -40°C to 80°C (±0.5°C accuracy) |
| **Humidity Range** | 0-100% RH (±2-5% accuracy) |
| **Sampling Rate** | 0.5 Hz (every 2 seconds) |
| **Interface** | Single-wire digital (GPIO) |
| **Power** | 3.3-5V @ 2.5mA |

**Connection:**

- Data: GPIO Pin 4 (BCM GPIO4)
- Power: 3.3V pin on GPIO header
- Ground: Ground pin on GPIO header
- Pull-up: 10kΩ resistor between data and power

**Known Issues:**

- ~5% read failure rate (expected sensor behavior)
- Service implements retry logic with exponential backoff

### 2.3 Software Architecture

#### 2.3.1 Docker Container Stack

**Container Network:**

- Network Name: `traffic_monitor_bridge`
- Network Type: Bridge (isolated from host)
- DNS Resolution: Container name-based

**Service Definitions:**

| Service | Image | Restart Policy | Health Check | Privileges |
|---------|-------|----------------|--------------|------------|
| **redis** | redis:7-alpine | unless-stopped | Redis PING (10s) | Standard |
| **traffic-monitor** | Custom (Python 3.11) | unless-stopped | HTTP /health (30s) | Standard |
| **realtime-events-broadcaster** | Custom (Python 3.11) | unless-stopped | HTTP /health (30s) | Standard |
| **vehicle-consolidator** | Custom (Python 3.11) | unless-stopped | Redis stream check (30s) | Standard |
| **database-persistence** | Custom (Python 3.11) | unless-stopped | DB write test (30s) | Standard |
| **radar-service** | Custom (Python 3.11) | unless-stopped | Stream length check (30s) | devices, dialout, gpio |
| **dht22-weather** | Custom (Python 3.11) | unless-stopped | Redis key check (60s) | gpio |
| **airport-weather** | Custom (Python 3.11) | unless-stopped | Redis key check (60s) | Standard |
| **data-maintenance** | Custom (Python 3.11) | unless-stopped | Cron check (300s) | Standard |
| **redis-optimization** | Custom (Python 3.11) | unless-stopped | Process check (60s) | Standard |
| **nginx-proxy** | nginx:1.25-alpine | unless-stopped | Config test (30s) | Standard |
| **camera-service-manager** | Custom (Python 3.11) | unless-stopped | Systemd check (30s) | Standard |

**systemd Service:**

| Service | Type | Dependencies | User | Privileges |
|---------|------|--------------|------|------------|
| **imx500-ai-capture.service** | simple | Docker network | pi | camera, video, gpio |

#### 2.3.2 Service Dependencies

**Startup Order (Managed by Docker Compose `depends_on`):**

```
1. redis (foundation)
   ↓
2. radar-service, dht22-weather, airport-weather (data sources)
   ↓
3. vehicle-consolidator (data fusion)
   ↓
4. database-persistence (persistence layer)
   ↓
5. traffic-monitor, realtime-events-broadcaster (API/WebSocket)
   ↓
6. nginx-proxy (reverse proxy/TLS)
   ↓
7. data-maintenance, redis-optimization (maintenance)
```

**Runtime Dependencies:**

- **All services** → redis (messaging)
- **vehicle-consolidator** → radar-service, imx500-ai-capture (data sources)
- **database-persistence** → vehicle-consolidator (consolidated events)
- **traffic-monitor** → database-persistence (query layer)
- **realtime-events-broadcaster** → redis (event streaming)
- **nginx-proxy** → traffic-monitor, realtime-events-broadcaster (proxying)

#### 2.3.3 Data Flow Architecture

**Detection Event Flow:**

```
1. Radar Detection:
   radar-service reads UART → detects vehicle → publishes to redis:radar_detections
   
2. Camera Trigger:
   imx500-ai-capture subscribes to redis:radar_detections → captures image → runs NPU inference
   → publishes to redis:camera_detections
   
3. Data Fusion:
   vehicle-consolidator subscribes to both channels → correlates radar + camera data
   → creates consolidated event → publishes to redis:traffic_events
   
4. Persistence:
   database-persistence subscribes to redis:traffic_events → writes to SQLite
   → publishes to redis:database_events
   
5. Real-Time Streaming:
   realtime-events-broadcaster subscribes to redis:traffic_events → broadcasts via WebSocket
   
6. API Access:
   traffic-monitor queries SQLite database → serves REST API → proxied via nginx
```

**Redis Pub/Sub Channels:**

| Channel | Publisher(s) | Subscriber(s) | Message Format |
|---------|-------------|---------------|----------------|
| `radar_detections` | radar-service | imx500-ai-capture, vehicle-consolidator | `{"speed": 25.5, "magnitude": 2048, "timestamp": "..."}` |
| `camera_detections` | imx500-ai-capture | vehicle-consolidator | `{"detections": [...], "image_path": "...", "timestamp": "..."}` |
| `traffic_events` | vehicle-consolidator | database-persistence, realtime-events-broadcaster | `{"vehicle_type": "car", "speed": 25.5, "confidence": 0.92, ...}` |
| `database_events` | database-persistence | (monitoring) | `{"action": "insert", "event_id": 123, ...}` |

**Redis Streams:**

| Stream | Producer | Consumer | Purpose |
|--------|----------|----------|---------|
| `radar_data` | radar-service | (monitoring, analysis) | Historical radar readings |
| `consolidated_traffic_data` | vehicle-consolidator | (monitoring, analysis) | Historical consolidated events |

**Redis Keys:**

| Key Pattern | Service | Purpose | TTL |
|-------------|---------|---------|-----|
| `weather:local:latest` | dht22-weather | Latest local weather | 5 min |
| `weather:airport:latest` | airport-weather | Latest airport weather | 10 min |
| `consolidation:*` | vehicle-consolidator | Temporary consolidation state | 30 sec |
| `stats:*` | Various | System statistics | 1 hour |

### 2.4 Network Architecture

#### 2.4.1 Port Configuration

**External Ports (Accessible from LAN):**

| Port | Protocol | Service | Purpose | Security |
|------|----------|---------|---------|----------|
| **80** | HTTP | nginx-proxy | HTTP (redirects to HTTPS) | Redirect only |
| **443** | HTTPS | nginx-proxy | Encrypted web access | TLS 1.2+ |
| **22** | SSH | Host OS | System administration | Key-based auth |

**Internal Ports (Docker network only):**

| Port | Protocol | Service | Purpose |
|------|----------|---------|---------|
| **5000** | HTTP | traffic-monitor | API Gateway |
| **6379** | TCP | redis | Redis server |
| **8001** | HTTP/WS | realtime-events-broadcaster | WebSocket streaming |

**Host-Only Ports:**

| Port | Protocol | Service | Purpose |
|------|----------|---------|---------|
| **19200** | UART | radar-service | Radar sensor (/dev/ttyAMA0) |

#### 2.4.2 VPN Access (Tailscale)

**Tailscale Configuration:**

- **Purpose**: Secure remote access without exposing ports to internet
- **Network**: Mesh VPN (WireGuard-based)
- **Authentication**: Magic DNS, MagicDNS
- **Access**: SSH, HTTPS dashboard, API

**Benefits:**

1. **No Port Forwarding**: No router configuration required
2. **Zero Trust**: End-to-end encryption between devices
3. **Easy Access**: Access via hostname (`pi5-traffic.tail<randomid>.ts.net`)
4. **Multi-Device**: Access from multiple devices (laptop, phone, tablet)
5. **Free Tier**: Suitable for personal/academic use

**Setup:**

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Check status
tailscale status
```

#### 2.4.3 External APIs

**Airport Weather API (CheckWX):**

- **Endpoint**: `https://api.checkwx.com/metar/`
- **Authentication**: API key (free tier: 500 requests/day)
- **Update Frequency**: 10 minutes
- **Data**: METAR weather reports (temperature, wind, visibility, precipitation)

**Network Requirements:**

- Internet connectivity for weather API and Tailscale
- Minimum 10 Mbps bandwidth
- Low latency preferred (<100ms ping)

**Firewall Rules (UFW):**

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Tailscale
sudo ufw allow 41641/udp

# Enable firewall
sudo ufw enable
```

---

## 3. System Configuration

### 3.1 Initial System Setup

#### 3.1.1 Hardware Installation

**Step 1: Raspberry Pi 5 Assembly**

1. **Install NVMe SSD (if using PCIe HAT)**:
   - Attach PCIe HAT to Raspberry Pi 5 GPIO header
   - Secure NVMe SSD to HAT with provided screw
   - Connect HAT ribbon cable to PCIe connector on Pi

2. **Install Cooling Solution**:
   - Attach heatsink or active cooler to Raspberry Pi 5 SoC
   - Connect fan to GPIO pins (5V and GND) if using active cooling
   - Ensure proper airflow in enclosure

3. **Connect Storage**:
   - Option A: Insert microSD card (32GB+) with Raspberry Pi OS
   - Option B: Use NVMe SSD as boot device (requires bootloader configuration)

**Step 2: Sensor Wiring**

1. **IMX500 AI Camera**:
   - Connect CSI-2 ribbon cable to CAM0 port on Raspberry Pi 5
   - Ensure cable is fully seated and connector latch is closed
   - Mount camera with clear view of detection area

2. **OPS243-C Radar Sensor**:
   - Connect radar UART TX to Raspberry Pi GPIO 15 (RX)
   - Connect radar UART RX to Raspberry Pi GPIO 14 (TX)
   - Connect radar GND to Raspberry Pi GND pin
   - Connect radar 5V to Raspberry Pi 5V pin (or use separate USB power)
   - Optional: Connect interrupt (GPIO23), reset (GPIO24) pins

3. **DHT22 Weather Sensor**:
   - Connect DHT22 data pin to Raspberry Pi GPIO 4 (Pin 7)
   - Connect DHT22 VCC to Raspberry Pi 3.3V pin (Pin 1)
   - Connect DHT22 GND to Raspberry Pi GND pin (Pin 6)
   - Install 10kΩ pull-up resistor between data and VCC pins

**GPIO Pin Reference:**

```
Raspberry Pi 5 40-Pin GPIO Header:

Pin  1: 3.3V Power   ────→ DHT22 VCC
Pin  6: Ground       ────→ DHT22 GND, Radar GND
Pin  7: GPIO 4       ────→ DHT22 Data (with 10kΩ pull-up)
Pin  8: GPIO 14 (TX) ────→ Radar RX
Pin 10: GPIO 15 (RX) ────→ Radar TX
Pin  2: 5V Power     ────→ Radar 5V (or use separate USB)
Pin 16: GPIO 23      ────→ Radar Interrupt (optional)
Pin 18: GPIO 24      ────→ Radar Reset (optional)
```

**Step 3: Physical Installation**

1. **Enclosure Selection**:
   - Use weatherproof enclosure for outdoor installation
   - Ensure ventilation for cooling
   - Provide cable glands for sensor wiring
   - Allow access for maintenance

2. **Mounting**:
   - Mount radar sensor with clear line of sight (10-100 ft range)
   - Mount camera with overlapping field of view
   - Ensure DHT22 sensor is protected from direct sunlight/rain
   - Secure enclosure to prevent theft or tampering

3. **Power Connection**:
   - Use official Raspberry Pi 5 27W USB-C power supply
   - Consider UPS for power protection
   - Protect power cable from weather

#### 3.1.2 Operating System Configuration

**Step 1: Install Raspberry Pi OS**

1. **Download Raspberry Pi Imager**:
   - Visit: https://www.raspberrypi.com/software/
   - Install Raspberry Pi Imager on your computer

2. **Flash OS Image**:
   - Select "Raspberry Pi OS (64-bit)" (Bookworm or later)
   - Select target storage (SD card or SSD)
   - Configure settings (hostname, SSH, user, WiFi - optional)
   - Write image

3. **First Boot**:
   - Insert SD card (or configure NVMe boot)
   - Connect Ethernet cable
   - Connect power supply
   - Wait for initial boot (~2-3 minutes)

**Step 2: Initial System Configuration**

1. **Connect via SSH**:
   ```bash
   ssh pi@<raspberry-pi-ip>
   ```

2. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Configure Boot Settings**:
   ```bash
   sudo raspi-config
   ```
   - **Interface Options** → Enable SSH (if not already enabled)
   - **Interface Options** → Enable I2C (for sensors)
   - **Interface Options** → Enable Camera (for IMX500)
   - **Performance Options** → Set GPU Memory to 128MB (minimum)
   - **Localisation Options** → Set timezone
   - **Advanced Options** → Expand Filesystem (if using SD card)

4. **Configure UART for Radar**:
   Edit `/boot/firmware/config.txt`:
   ```bash
   sudo nano /boot/firmware/config.txt
   ```
   Add/verify these lines:
   ```ini
   # Enable UART (disable Bluetooth to free up hardware UART)
   dtoverlay=disable-bt
   enable_uart=1
   
   # Camera configuration
   camera_auto_detect=1
   
   # I2C for sensors
   dtparam=i2c_arm=on
   ```

5. **Disable Serial Console** (so radar can use UART):
   ```bash
   sudo systemctl stop serial-getty@ttyAMA0.service
   sudo systemctl disable serial-getty@ttyAMA0.service
   ```

6. **Configure User Groups**:
   ```bash
   sudo usermod -a -G gpio,dialout,video,i2c pi
   ```

7. **Reboot**:
   ```bash
   sudo reboot
   ```

#### 3.1.3 Network Configuration

**Step 1: Set Static IP (Recommended)**

Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:
```ini
# Static IP Configuration
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart networking:
```bash
sudo systemctl restart dhcpcd
```

**Step 2: Configure Hostname**

```bash
sudo hostnamectl set-hostname pi5-traffic
```

**Step 3: Configure Firewall (UFW)**

```bash
# Install UFW
sudo apt install ufw -y

# Set defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 3.2 Docker Configuration

#### 3.2.1 Install Docker and Docker Compose

**Step 1: Install Docker**:

```bash
# Install Docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker pi

# Log out and back in for group changes to take effect
exit
```

**Step 2: Install Docker Compose**:

Docker Compose is now included with Docker, verify:
```bash
docker compose version
```

**Step 3: Verify Installation**:

```bash
docker --version
docker compose version
docker ps
```

#### 3.2.2 Docker Compose Files

The system uses a primary `docker-compose.yml` file with all 12 services defined.

**Key Configuration Sections:**

1. **Network Definition**:
   ```yaml
   networks:
     app-network:
       driver: bridge
   ```

2. **Volume Definitions**:
   All services use bind mounts to `${STORAGE_ROOT}` (default: `/mnt/storage`)

3. **Environment Variables**:
   Configured via `.env` file (see Section 3.2.3)

4. **Health Checks**:
   All services define health checks with intervals, timeouts, and retries

5. **Restart Policies**:
   All services use `restart: unless-stopped` for automatic recovery

#### 3.2.3 Environment Variables

**Create `.env` File**:

```bash
cd ~/CST_590_Computer_Science_Capstone_Project
nano .env
```

**Required Environment Variables**:

```bash
# Storage Configuration
STORAGE_ROOT=/mnt/storage
REDIS_DATA_PATH=/mnt/storage/redis_data

# User/Group IDs (match your pi user)
HOST_UID=1000
HOST_GID=1000

# Docker Image
DOCKER_IMAGE=gcumerk/cst590-capstone-public:latest

# Database Configuration
DATABASE_RETENTION_DAYS=90

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000

# Weather Configuration
CHECKWX_API_KEY=your_checkwx_api_key_here
AIRPORT_ICAO=KDEN  # Change to your nearest airport

# Maintenance Configuration
MAINTENANCE_IMAGE_MAX_AGE_HOURS=24
MAINTENANCE_LOG_MAX_AGE_DAYS=7

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Logging Configuration
LOG_LEVEL=INFO
```

**Get CheckWX API Key**:

1. Visit https://www.checkwx.com/
2. Sign up for free account (500 requests/day)
3. Copy API key from dashboard
4. Add to `.env` file

#### 3.2.4 Volume Mounts

**Create Storage Directory Structure**:

```bash
# Create storage root
sudo mkdir -p /mnt/storage

# Create subdirectories
sudo mkdir -p /mnt/storage/{redis_data,camera_capture,processed_data,logs,ai_camera_images,data}

# Set ownership
sudo chown -R pi:pi /mnt/storage

# Set permissions
sudo chmod -R 755 /mnt/storage
```

**Storage Directory Purpose**:

| Directory | Purpose | Retention | Typical Size |
|-----------|---------|-----------|--------------|
| `redis_data` | Redis AOF persistence | Permanent | 10-50MB |
| `camera_capture` | Raw camera images | 24 hours | 50MB/day |
| `processed_data` | Processed detection data | 24 hours | 10MB/day |
| `logs` | Application logs | 7 days | 10MB/day |
| `ai_camera_images` | AI-annotated images | 24 hours | 50MB/day |
| `data` | SQLite database | 90 days | 100MB/month |

### 3.3 Service Configuration

#### 3.3.1 Radar Service Configuration

**Configuration via Environment Variables** (in `docker-compose.yml`):

```yaml
radar-service:
  environment:
    - RADAR_PORT=/dev/ttyAMA0
    - RADAR_BAUD_RATE=19200
    - RADAR_SPEED_THRESHOLD=2.0
    - RADAR_MAGNITUDE_THRESHOLD=500
```

**Device Access**:

Radar service requires access to `/dev/ttyAMA0` (UART):
```yaml
devices:
  - /dev/ttyAMA0:/dev/ttyAMA0
group_add:
  - dialout
  - gpio
```

#### 3.3.2 Camera Service Configuration

**IMX500 Systemd Service** (on host, not containerized):

File: `/etc/systemd/system/imx500-ai-capture.service`

```ini
[Unit]
Description=IMX500 AI Camera Capture Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/CST_590_Computer_Science_Capstone_Project
ExecStart=/usr/bin/python3 /home/pi/CST_590_Computer_Science_Capstone_Project/imx500_ai_host_capture_enhanced.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Install and Enable**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable imx500-ai-capture.service
sudo systemctl start imx500-ai-capture.service
```

#### 3.3.3 Weather Services Configuration

**Local Weather (DHT22)**:

```yaml
dht22-weather:
  environment:
    - DHT22_GPIO_PIN=4
    - DHT22_READ_INTERVAL=300  # 5 minutes
    - DHT22_RETRY_COUNT=3
```

**Airport Weather**:

```yaml
airport-weather:
  environment:
    - CHECKWX_API_KEY=${CHECKWX_API_KEY}
    - AIRPORT_ICAO=${AIRPORT_ICAO}
    - UPDATE_INTERVAL=600  # 10 minutes
```

#### 3.3.4 Database Configuration

**Database Persistence Service**:

```yaml
database-persistence:
  environment:
    - DATABASE_PATH=/app/data/traffic_data.db
    - DATABASE_RETENTION_DAYS=90
    - BATCH_SIZE=10
    - BATCH_TIMEOUT=5
```

**SQLite Database Location**:
- Container path: `/app/data/traffic_data.db`
- Host path: `/mnt/storage/data/traffic_data.db`

#### 3.3.5 API Gateway Configuration

**Traffic Monitor Service**:

```yaml
traffic-monitor:
  environment:
    - API_HOST=0.0.0.0
    - API_PORT=5000
    - API_DEBUG=false
    - DATABASE_PATH=/app/data/traffic_data.db
  expose:
    - "5000"  # Internal only, proxied by nginx
```

### 3.4 Security Configuration

#### 3.4.1 TLS/SSL Certificates

**Option 1: Self-Signed Certificates (Development/Internal Use)**

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx-selfsigned.key \
  -out /etc/nginx/ssl/nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=pi5-traffic.local"

# Set permissions
sudo chmod 600 /etc/nginx/ssl/nginx-selfsigned.key
sudo chmod 644 /etc/nginx/ssl/nginx-selfsigned.crt
```

**Option 2: Let's Encrypt (Production with Public Domain)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate (requires domain name and port 80 accessible)
sudo certbot --nginx -d your-domain.com
```

#### 3.4.2 Tailscale VPN Setup

**Install Tailscale**:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (opens browser)
sudo tailscale up

# Check status
tailscale status

# Get Tailscale hostname
tailscale status | grep $(hostname)
```

**Access System via Tailscale**:

After setup, access via Tailscale hostname:
- Dashboard: `https://pi5-traffic.tail<id>.ts.net`
- SSH: `ssh pi@pi5-traffic.tail<id>.ts.net`

**Benefits**:
- No port forwarding required
- End-to-end encryption
- Access from anywhere
- Free for personal use

#### 3.4.3 Firewall Rules

**UFW Configuration** (already configured in Section 3.1.3):

```bash
sudo ufw status verbose
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
41641/udp                  ALLOW       Anywhere  (Tailscale)
```

**Docker Network Isolation**:

Docker containers are isolated on `app-network` bridge network. Only nginx-proxy exposes ports 80/443 externally.

---

## 4. Deployment Procedures

### 4.1 Pre-Deployment Checklist

**Hardware Checklist:**

- [ ] Raspberry Pi 5 powered and booted
- [ ] Network connectivity established (Ethernet or WiFi)
- [ ] IMX500 camera connected and recognized
- [ ] OPS243-C radar connected to UART (/dev/ttyAMA0)
- [ ] DHT22 weather sensor connected to GPIO
- [ ] Storage mounted and writable (/mnt/storage)
- [ ] Cooling solution installed and functional

**Software Checklist:**

- [ ] Raspberry Pi OS 64-bit installed and updated
- [ ] Docker and Docker Compose installed
- [ ] Git installed
- [ ] SSH access configured
- [ ] User added to docker, gpio, dialout groups
- [ ] UART enabled and serial console disabled
- [ ] Firewall (UFW) configured
- [ ] Tailscale installed (optional but recommended)

**Configuration Checklist:**

- [ ] Static IP configured (or DHCP reservation)
- [ ] Hostname set (e.g., pi5-traffic)
- [ ] Storage directories created (/mnt/storage/*)
- [ ] `.env` file created with all required variables
- [ ] CheckWX API key obtained and configured
- [ ] TLS certificates generated
- [ ] systemd service file created for IMX500

**Verification Commands:**

```bash
# Check system info
uname -a
cat /etc/os-release

# Check Docker
docker --version
docker compose version

# Check storage
df -h /mnt/storage

# Check UART
ls -l /dev/ttyAMA0

# Check camera
libcamera-hello --list-cameras

# Check GPIO access
ls -l /dev/gpiomem0

# Check groups
groups pi
```

### 4.2 Initial Deployment

#### 4.2.1 Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git

# Navigate to project directory
cd CST_590_Computer_Science_Capstone_Project

# Verify files
ls -la
```

#### 4.2.2 Configure Environment

**Step 1: Create `.env` File**:

```bash
# Copy example env file (if exists)
cp .env.example .env

# Edit environment variables
nano .env
```

Configure all required variables (see Section 3.2.3).

**Step 2: Verify Configuration**:

```bash
# Check docker-compose configuration
docker compose config

# Verify environment variables
docker compose config | grep -E "STORAGE_ROOT|CHECKWX_API_KEY"
```

#### 4.2.3 Build and Deploy Services

**Step 1: Pull Docker Images**:

```bash
# Pull latest images
docker compose pull
```

**Step 2: Start Services**:

```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f
```

**Step 3: Start IMX500 Service**:

```bash
# Enable and start systemd service
sudo systemctl enable imx500-ai-capture.service
sudo systemctl start imx500-ai-capture.service

# Check status
sudo systemctl status imx500-ai-capture.service
```

**Step 4: Verify All Services**:

```bash
# Check container status
docker compose ps

# Check health
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# Tail logs
docker compose logs -f --tail=50
```

Expected output: All 12 containers showing "Up" and "healthy".

### 4.3 Zero-Downtime Updates

#### 4.3.1 Update Strategy

The system supports **rolling updates** with zero downtime:

1. **Redis First**: Redis maintains state, starts first
2. **Core Services**: Update data collection services
3. **API Services**: Update API and WebSocket services last
4. **Nginx Last**: Update reverse proxy last

#### 4.3.2 Rolling Deployment

**Step 1: Pull New Images**:

```bash
cd ~/CST_590_Computer_Science_Capstone_Project

# Pull latest images
docker compose pull
```

**Step 2: Update Services**:

```bash
# Recreate services with new images
docker compose up -d --no-deps --build

# Or update specific service
docker compose up -d --no-deps --build traffic-monitor
```

**Step 3: Verify Health**:

```bash
# Check all services are healthy
docker compose ps

# Check logs for errors
docker compose logs --tail=100
```

#### 4.3.3 Rollback Procedures

**If Update Fails**:

```bash
# Stop all services
docker compose down

# Check out previous version from Git
git log --oneline  # Find previous commit
git checkout <previous-commit-hash>

# Restart services
docker compose up -d
```

**Or use Docker image tag**:

```bash
# Edit .env file
nano .env

# Change DOCKER_IMAGE to previous version
DOCKER_IMAGE=gcumerk/cst590-capstone-public:v1.0.0

# Restart
docker compose up -d
```

### 4.4 Post-Deployment Validation

**Step 1: Service Health Checks**:

```bash
# Check all containers
docker compose ps

# Expected: All containers "Up" and "healthy"
```

**Step 2: API Health Check**:

```bash
# Check API health endpoint
curl http://localhost:5000/health

# Expected output: {"status": "healthy", ...}

# Or via HTTPS
curl -k https://localhost/api/health
```

**Step 3: WebSocket Test**:

```bash
# Install websocat (WebSocket client)
sudo apt install websocat -y

# Connect to WebSocket
websocat wss://localhost/ws -k

# Should receive real-time events as vehicles are detected
```

**Step 4: Dashboard Access**:

Open browser and navigate to:
- Local: `https://<raspberry-pi-ip>`
- Tailscale: `https://pi5-traffic.tail<id>.ts.net`

Accept self-signed certificate warning (for development).

**Step 5: Verify Sensors**:

```bash
# Check radar service logs
docker compose logs radar-service --tail=50

# Should see radar readings

# Check DHT22 weather
docker compose logs dht22-weather --tail=20

# Should see temperature/humidity readings

# Check IMX500 camera
sudo journalctl -u imx500-ai-capture.service -n 50

# Should see "Waiting for radar trigger" messages
```

**Step 6: Test Detection**:

Trigger vehicle detection by:
1. Walking in front of radar sensor
2. Driving vehicle past sensors
3. Checking dashboard for detection event

### 4.5 Common Deployment Issues

#### Issue 1: Container Won't Start

**Symptoms**: Service shows "Restarting" or "Exited"

**Diagnosis**:
```bash
docker compose logs <service-name>
docker inspect <container-name>
```

**Common Causes**:
- Missing environment variables
- Incorrect permissions on /mnt/storage
- Port already in use
- Missing device access (UART, GPIO)

**Solutions**:
```bash
# Fix permissions
sudo chown -R pi:pi /mnt/storage

# Check port usage
sudo netstat -tlnp | grep <port>

# Verify devices
ls -l /dev/ttyAMA0 /dev/gpiomem0
```

#### Issue 2: Radar Service Not Receiving Data

**Symptoms**: No radar detections in logs

**Diagnosis**:
```bash
# Check UART device
ls -l /dev/ttyAMA0

# Check service logs
docker compose logs radar-service

# Test UART manually
cat /dev/ttyAMA0
```

**Solutions**:
```bash
# Verify UART enabled in config.txt
grep -E "enable_uart|disable-bt" /boot/firmware/config.txt

# Check serial console disabled
sudo systemctl status serial-getty@ttyAMA0.service

# Check user groups
groups pi | grep dialout
```

#### Issue 3: Camera Service Won't Start

**Symptoms**: IMX500 systemd service fails

**Diagnosis**:
```bash
sudo systemctl status imx500-ai-capture.service
sudo journalctl -u imx500-ai-capture.service -n 100
```

**Solutions**:
```bash
# Test camera manually
libcamera-hello --list-cameras

# Check camera cable connection
# Verify camera enabled in raspi-config

# Check Redis connectivity from host
redis-cli -h 127.0.0.1 ping
```

#### Issue 4: Database Errors

**Symptoms**: "database is locked" errors

**Solutions**:
```bash
# Stop services
docker compose down

# Check database integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# Backup and recreate if corrupted
cp /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.backup
rm /mnt/storage/data/traffic_data.db

# Restart services
docker compose up -d
```

#### Issue 5: High CPU/Memory Usage

**Symptoms**: System sluggish, high load average

**Diagnosis**:
```bash
# Check container resources
docker stats

# Check system resources
htop
```

**Solutions**:
```bash
# Restart resource-heavy services
docker compose restart vehicle-consolidator redis

# Check for memory leaks in logs
docker compose logs | grep -i "memory\|oom"

# Increase swap if needed (not recommended long-term)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Increase CONF_SWAPSIZE
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## 5. System Maintenance

### 5.1 Routine Maintenance Tasks

#### 5.1.1 Daily Tasks

**1. Monitor System Health** (5 minutes)

```bash
# Check all services are running and healthy
docker compose ps

# Expected: All services "Up" and "healthy"
```

**2. Review Recent Logs** (10 minutes)

```bash
# Check for errors across all services
docker compose logs --since 24h | grep -i "error\|critical\|warning"

# Check specific service logs
docker compose logs radar-service --since 24h --tail=100
docker compose logs database-persistence --since 24h --tail=100
```

**3. Verify Detection Events** (5 minutes)

```bash
# Check dashboard for recent detections
curl -s http://localhost:5000/api/detections/recent | jq '.'

# Or access web dashboard
https://<raspberry-pi-ip>/
```

**4. Check Sensor Status** (5 minutes)

```bash
# Radar service health
docker compose logs radar-service --tail=10

# Camera service health
sudo systemctl status imx500-ai-capture.service

# Weather sensor health
docker compose logs dht22-weather --tail=10
```

#### 5.1.2 Weekly Tasks

**1. Review System Performance** (15 minutes)

```bash
# Check system resources
docker stats --no-stream

# Check disk usage
df -h /mnt/storage
du -sh /mnt/storage/*

# Check database size
ls -lh /mnt/storage/data/traffic_data.db
```

**2. Analyze Detection Statistics** (10 minutes)

```bash
# Query detection counts by day
curl -s http://localhost:5000/api/statistics/daily?days=7 | jq '.'

# Query vehicle type distribution
curl -s http://localhost:5000/api/statistics/vehicle-types | jq '.'
```

**3. Review Logs for Patterns** (15 minutes)

```bash
# Count errors by service
docker compose logs --since 7d | grep -i error | cut -d'|' -f1 | sort | uniq -c

# Check for failed health checks
docker compose logs --since 7d | grep -i "health check failed"
```

**4. Verify Automated Maintenance** (10 minutes)

```bash
# Check data-maintenance service logs
docker compose logs data-maintenance --since 7d --tail=100

# Verify image cleanup occurred
ls -l /mnt/storage/ai_camera_images/ | head -20

# Check log rotation
ls -l /mnt/storage/logs/ | tail -20
```

#### 5.1.3 Monthly Tasks

**1. Apply System Updates** (30 minutes)

```bash
# Update OS packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
cd ~/CST_590_Computer_Science_Capstone_Project
docker compose pull

# Restart services with new images
docker compose up -d

# Verify health
docker compose ps
```

**2. Database Maintenance** (15 minutes)

```bash
# Stop database service
docker compose stop database-persistence

# Backup database (see Section 7.2)
cp /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.backup

# Run VACUUM to optimize
sqlite3 /mnt/storage/data/traffic_data.db "VACUUM;"

# Check integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# Restart service
docker compose start database-persistence
```

**3. Review Security Logs** (20 minutes)

```bash
# Check SSH authentication attempts
sudo grep "Failed password" /var/log/auth.log | tail -20

# Check UFW firewall logs
sudo tail -100 /var/log/ufw.log

# Check for suspicious activity
sudo lastb  # Failed login attempts
last  # Successful logins
```

**4. Performance Review** (30 minutes)

- Analyze monthly detection statistics
- Review average response times
- Check resource utilization trends
- Identify optimization opportunities
- Update performance baselines (see Section 10)

**5. Documentation Review** (15 minutes)

- Review and update configuration documentation
- Document any system changes made during the month
- Update runbook for any new issues encountered
- Review and update maintenance procedures

### 5.2 Database Maintenance

#### 5.2.1 Data Retention Policies

**Automatic Retention** (Configured in database-persistence service):

```yaml
environment:
  - DATABASE_RETENTION_DAYS=90
```

**How It Works**:

- Database-persistence service automatically deletes records older than 90 days
- Cleanup runs daily at 2:00 AM
- Deletion is performed in batches to avoid locking

**Manual Retention Policy Changes**:

```bash
# Edit docker-compose.yml or .env
nano .env

# Change retention period
DATABASE_RETENTION_DAYS=60

# Restart service
docker compose up -d database-persistence
```

#### 5.2.2 Database Vacuum and Optimization

**Why VACUUM**:

SQLite database file grows over time due to deletions. VACUUM reclaims unused space and reorganizes data.

**Monthly VACUUM Procedure**:

```bash
# 1. Stop database write service
docker compose stop database-persistence

# 2. Backup database first (always!)
cp /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.pre-vacuum

# 3. Run VACUUM
sqlite3 /mnt/storage/data/traffic_data.db "VACUUM;"

# 4. Analyze to update query optimizer statistics
sqlite3 /mnt/storage/data/traffic_data.db "ANALYZE;"

# 5. Check file size reduction
ls -lh /mnt/storage/data/traffic_data.db*

# 6. Restart service
docker compose start database-persistence

# 7. Verify health
docker compose logs database-persistence --tail=50
```

**Expected Results**:

- Database file size reduced by 20-40% after VACUUM
- No data loss (verify record counts before/after)
- Improved query performance

#### 5.2.3 Database Integrity Checks

**Weekly Integrity Check**:

```bash
# Check database integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# Expected output: "ok"
```

**If Corruption Detected**:

```bash
# 1. Stop database service
docker compose stop database-persistence

# 2. Backup corrupted database
cp /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.corrupted

# 3. Try to repair with dump/reload
sqlite3 /mnt/storage/data/traffic_data.db.corrupted .dump > dump.sql
sqlite3 /mnt/storage/data/traffic_data.db < dump.sql

# 4. Verify integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# 5. If successful, restart service
docker compose start database-persistence

# 6. If repair fails, restore from backup (see Section 7.4)
```

### 5.3 Log Management

#### 5.3.1 Log Rotation

**Docker Logs** (Managed by Docker daemon):

Edit `/etc/docker/daemon.json`:

```bash
sudo nano /etc/docker/daemon.json
```

Add log rotation configuration:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:

```bash
sudo systemctl restart docker
docker compose up -d
```

**Application Logs** (In `/mnt/storage/logs/`):

Logs are automatically rotated by data-maintenance service based on age (default: 7 days).

**Manual Log Cleanup**:

```bash
# View current log sizes
du -sh /mnt/storage/logs/*

# Delete old logs manually (if needed)
find /mnt/storage/logs/ -name "*.log" -mtime +7 -delete

# View Docker log sizes
sudo du -sh /var/lib/docker/containers/*/*-json.log | sort -h
```

#### 5.3.2 Log Analysis

**Search for Errors Across All Services**:

```bash
# Errors in last 24 hours
docker compose logs --since 24h | grep -i "error" | less

# Critical errors
docker compose logs | grep -i "critical"

# Warnings
docker compose logs --since 24h | grep -i "warning" | less
```

**Analyze Specific Service**:

```bash
# Radar service errors
docker compose logs radar-service | grep -i "error"

# Database service errors
docker compose logs database-persistence | grep -i "error\|lock"

# Camera service errors
sudo journalctl -u imx500-ai-capture.service | grep -i "error"
```

**Performance Analysis**:

```bash
# Find slow operations
docker compose logs | grep -i "latency\|slow\|timeout"

# Check detection processing times
docker compose logs vehicle-consolidator | grep "Processing time"
```

#### 5.3.3 Log Archival

**Monthly Log Archive Procedure**:

```bash
# Create archive directory
mkdir -p /mnt/storage/archives/logs

# Archive logs older than 30 days
cd /mnt/storage/logs
tar -czf /mnt/storage/archives/logs/logs-$(date +%Y-%m).tar.gz *.log

# Delete archived files
find /mnt/storage/logs/ -name "*.log" -mtime +30 -delete

# List archives
ls -lh /mnt/storage/archives/logs/
```

**Archive Retention**:

- Keep monthly archives for 1 year
- Delete archives older than 1 year
- Store critical archives off-site (optional)

### 5.4 Storage Management

#### 5.4.1 Disk Space Monitoring

**Check Available Space**:

```bash
# Overall disk usage
df -h

# Storage directory usage
df -h /mnt/storage

# Breakdown by subdirectory
du -sh /mnt/storage/*

# Detailed breakdown
du -h /mnt/storage/ | sort -h | tail -20
```

**Set Up Disk Space Alerts**:

Create monitoring script `/home/pi/check_disk_space.sh`:

```bash
#!/bin/bash
THRESHOLD=80
USAGE=$(df -h /mnt/storage | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
  echo "WARNING: Storage usage at ${USAGE}% (threshold: ${THRESHOLD}%)"
  # Send alert (email, webhook, etc.)
fi
```

Add to crontab:

```bash
crontab -e
```

Add line:

```cron
0 */6 * * * /home/pi/check_disk_space.sh
```

#### 5.4.2 Image Cleanup

**Automatic Image Cleanup** (Performed by data-maintenance service):

- Images older than 24 hours are automatically deleted
- Runs every hour
- Configurable via `MAINTENANCE_IMAGE_MAX_AGE_HOURS` environment variable

**Manual Image Cleanup**:

```bash
# View current image count and size
ls -l /mnt/storage/ai_camera_images/ | wc -l
du -sh /mnt/storage/ai_camera_images/

# Delete images older than 24 hours manually
find /mnt/storage/ai_camera_images/ -name "*.jpg" -mtime +1 -delete

# Verify cleanup
du -sh /mnt/storage/ai_camera_images/
```

#### 5.4.3 Temporary File Management

**Clean Temporary Files**:

```bash
# Clean /tmp
sudo find /tmp -type f -atime +7 -delete

# Clean Docker temporary files
docker system prune -f

# Clean Docker unused images
docker image prune -a -f

# Clean Docker volumes (CAREFUL!)
docker volume ls -q | grep -v redis_data | xargs docker volume rm
```

### 5.5 System Updates

#### 5.5.1 OS Updates

**Monthly OS Update Procedure**:

```bash
# 1. Update package lists
sudo apt update

# 2. List upgradable packages
apt list --upgradable

# 3. Upgrade packages
sudo apt upgrade -y

# 4. Distribution upgrade (major updates)
sudo apt dist-upgrade -y

# 5. Clean up
sudo apt autoremove -y
sudo apt autoclean

# 6. Reboot if kernel updated
sudo reboot
```

**Security-Only Updates** (Weekly):

```bash
# Install security updates only
sudo apt update
sudo apt install -y unattended-upgrades
sudo unattended-upgrade -d
```

#### 5.5.2 Docker Updates

**Update Docker Engine**:

```bash
# Update Docker package
sudo apt update
sudo apt install --only-upgrade docker-ce docker-ce-cli containerd.io

# Restart Docker
sudo systemctl restart docker

# Verify version
docker --version
```

**Update Docker Compose** (if standalone):

```bash
# Docker Compose is now part of Docker
# Update via Docker Engine updates above

# Verify
docker compose version
```

#### 5.5.3 Application Updates

**Update Application Services**:

```bash
cd ~/CST_590_Computer_Science_Capstone_Project

# 1. Pull latest code from Git
git pull origin main

# 2. Pull latest Docker images
docker compose pull

# 3. Recreate services with new images
docker compose up -d

# 4. Verify health
docker compose ps
docker compose logs --tail=100
```

**Update Specific Service Only**:

```bash
# Pull specific service image
docker compose pull traffic-monitor

# Recreate specific service
docker compose up -d --no-deps traffic-monitor

# Verify
docker compose logs traffic-monitor --tail=50
```

---

## 6. Monitoring and Health Checks

### 6.1 Health Check System

#### 6.1.1 Docker Health Checks

**View Health Status**:

```bash
# Check all service health
docker compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' <container-name>

# View health check logs
docker inspect --format='{{json .State.Health}}' <container-name> | jq '.'
```

**Health Check Configuration** (per service in docker-compose.yml):

Example:
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 3
  start_period: 5s
```

**Common Health Check Commands**:

| Service | Health Check Command |
|---------|---------------------|
| redis | `redis-cli ping` |
| traffic-monitor | `curl http://localhost:5000/health` |
| database-persistence | SQLite write test |
| radar-service | Redis stream length check |
| nginx-proxy | `nginx -t` (config test) |

#### 6.1.2 Service Health Endpoints

**API Health Endpoint**:

```bash
# Local check
curl http://localhost:5000/health

# Response:
# {
#   "status": "healthy",
#   "redis": "connected",
#   "database": "accessible",
#   "uptime": 12345,
#   "version": "1.0.0"
# }

# Via HTTPS
curl -k https://localhost/api/health | jq '.'
```

**Individual Service Health**:

```bash
# Check redis connectivity
docker exec redis redis-cli ping
# Expected: PONG

# Check database accessibility
docker exec database-persistence python -c "import sqlite3; sqlite3.connect('/app/data/traffic_data.db').execute('SELECT 1').fetchone()"

# Check radar service
docker exec radar-service python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.xlen('radar_data'))"
```

#### 6.1.3 Hardware Sensor Status

**Radar Sensor Status**:

```bash
# Check UART connection
ls -l /dev/ttyAMA0

# Check radar service logs
docker compose logs radar-service --tail=20

# Expected: Regular speed/magnitude readings
```

**Camera Sensor Status**:

```bash
# Check camera service
sudo systemctl status imx500-ai-capture.service

# Check camera logs
sudo journalctl -u imx500-ai-capture.service -n 50

# Test camera directly
libcamera-hello --list-cameras
```

**Weather Sensor Status**:

```bash
# Check DHT22 readings
docker compose logs dht22-weather --tail=10

# Expected: Temperature and humidity readings every 5 minutes
```

### 6.2 Performance Monitoring

#### 6.2.1 System Resource Monitoring

**Real-Time Resource Usage**:

```bash
# Container resource usage
docker stats

# System resource usage
htop

# Or use top
top
```

**Historical Resource Usage**:

```bash
# CPU usage over time
sar -u 1 10

# Memory usage
free -h
vmstat 1 10

# Disk I/O
iostat -x 1 10

# Network I/O
iftop
```

**Resource Usage by Service**:

```bash
# Get stats for specific container
docker stats redis --no-stream
docker stats traffic-monitor --no-stream

# All containers sorted by memory
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}" | sort -k3 -h
```

#### 6.2.2 Application Performance Metrics

**Detection Latency**:

```bash
# Check logs for processing times
docker compose logs vehicle-consolidator | grep "Processing time"

# Expected: <350ms end-to-end
```

**API Response Times**:

```bash
# Measure API response time
time curl -s http://localhost:5000/api/health > /dev/null

# Or with httpie
http --print=Hh http://localhost:5000/api/health
```

**Database Query Performance**:

```bash
# Enable query logging (if needed)
# Query database with timing
sqlite3 /mnt/storage/data/traffic_data.db << EOF
.timer on
SELECT COUNT(*) FROM detection_events;
SELECT vehicle_type, COUNT(*) FROM detection_events GROUP BY vehicle_type;
EOF
```

**Detection Throughput**:

```bash
# Count detections in last hour
curl -s http://localhost:5000/api/detections/recent?hours=1 | jq '. | length'

# Count detections by hour
curl -s http://localhost:5000/api/statistics/hourly | jq '.'
```

#### 6.2.3 Network Performance

**Check Network Latency**:

```bash
# Ping external services
ping -c 10 8.8.8.8

# Check DNS resolution
dig google.com

# Check Tailscale connectivity
tailscale ping <another-device>
```

**Check Service-to-Service Communication**:

```bash
# Redis pub/sub latency
docker exec redis redis-cli --latency

# API latency within Docker network
docker exec traffic-monitor curl -s http://redis:6379
```

### 6.3 Alert Configuration

#### 6.3.1 Critical Alerts

**Service Down Alert**:

Automated by Docker restart policies. If service fails repeatedly, it stops restarting.

Monitor with:
```bash
# Check for exited containers
docker ps -a | grep -i exit

# Check restart count
docker inspect <container> | grep RestartCount
```

**Disk Space Critical**:

```bash
# Create alert script
cat > /home/pi/disk_space_alert.sh << 'EOF'
#!/bin/bash
THRESHOLD=90
USAGE=$(df -h /mnt/storage | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
  echo "CRITICAL: Storage at ${USAGE}%"
  # Add webhook or email notification here
fi
EOF

chmod +x /home/pi/disk_space_alert.sh
```

Add to crontab:
```cron
*/30 * * * * /home/pi/disk_space_alert.sh
```

#### 6.3.2 Warning Alerts

**High CPU Usage**:

```bash
# Monitor CPU and alert if > 80%
cat > /home/pi/cpu_alert.sh << 'EOF'
#!/bin/bash
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
THRESHOLD=80

if (( $(echo "$CPU_USAGE > $THRESHOLD" | bc -l) )); then
  echo "WARNING: CPU usage at ${CPU_USAGE}%"
fi
EOF
```

**High Memory Usage**:

```bash
# Check memory usage
free | awk 'NR==2 {printf "%.0f\n", $3/$2*100}'
```

#### 6.3.3 Notification Channels

**Options for Notifications**:

1. **Email** (using msmtp or sendmail)
2. **Webhooks** (Slack, Discord, Microsoft Teams)
3. **SMS** (via Twilio or similar)
4. **Push Notifications** (via Pushover, Pushbullet)

**Example: Slack Webhook**:

```bash
# Send message to Slack
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Alert: System issue detected"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 6.4 Dashboard Access

#### 6.4.1 Web Dashboard

**Access URLs**:

- **Local Network**: `https://<raspberry-pi-ip>`
- **Tailscale VPN**: `https://pi5-traffic.tail<id>.ts.net`

**Dashboard Features**:

- Real-time detection feed (WebSocket)
- Detection statistics (daily, hourly)
- Vehicle type distribution
- Speed distribution
- Recent detections with images
- System health indicators
- Weather information

#### 6.4.2 Monitoring Tools

**Recommended Monitoring Tools**:

1. **Portainer** (Docker GUI):
   ```bash
   docker run -d -p 9000:9000 --name portainer \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v portainer_data:/data \
     portainer/portainer-ce:latest
   ```

2. **ctop** (Container monitoring):
   ```bash
   sudo apt install ctop -y
   ctop
   ```

3. **Glances** (System monitoring):
   ```bash
   pip3 install glances
   glances
   ```

#### 6.4.3 Real-Time Event Stream

**WebSocket Connection**:

```bash
# Install websocat
sudo apt install websocat -y

# Connect to event stream
websocat wss://localhost/ws -k

# Or with authentication (if implemented)
websocat "wss://localhost/ws?token=<your-token>" -k
```

**Event Stream Format**:

```json
{
  "event_type": "vehicle_detection",
  "timestamp": "2025-10-02T10:30:45.123Z",
  "vehicle_type": "car",
  "speed": 25.5,
  "confidence": 0.92,
  "direction": "approaching",
  "temperature": 72.5,
  "humidity": 45
}
```

---

## 7. Backup and Recovery

### 7.1 Backup Strategy

#### 7.1.1 What to Back Up

**Critical Data (Must Back Up)**:

1. **Database**: `/mnt/storage/data/traffic_data.db`
2. **Configuration**: `docker-compose.yml`, `.env` files
3. **Custom Scripts**: Any custom maintenance or monitoring scripts
4. **TLS Certificates**: `/etc/nginx/ssl/` (if not using self-signed)

**Optional Data (Consider Backing Up)**:

5. **Recent Images**: `/mnt/storage/ai_camera_images/` (last 24 hours)
6. **Logs**: `/mnt/storage/logs/` (for forensics)
7. **Redis Data**: `/mnt/storage/redis_data/` (cache, can be rebuilt)

**Do Not Need to Back Up**:

- Docker images (can be pulled from registry)
- Temporary files
- Old logs (beyond retention period)
- Operating system (can be reinstalled)

#### 7.1.2 Backup Frequency

| Data Type | Frequency | Method | Retention |
|-----------|-----------|--------|-----------|
| Database | Daily | Automated script | 7 daily + 4 weekly + 3 monthly |
| Configuration | After changes | Git commit | Permanent (version control) |
| Images | N/A | Not backed up (24-hour retention) | N/A |
| Logs | Weekly | Archive to tar.gz | 3 months |
| Full System | Monthly | Complete backup | 2 months |

#### 7.1.3 Backup Retention

**Retention Policy**:

- **Daily backups**: Keep 7 days
- **Weekly backups**: Keep 4 weeks
- **Monthly backups**: Keep 3 months
- **Configuration**: Keep all versions (Git)

**Storage Requirements**:

- Database backup: ~100MB per backup
- Weekly backups: ~700MB (7 daily backups)
- Monthly backups: ~1.2GB (4 weekly + 7 daily backups)
- Total: ~2-3GB for full backup retention

### 7.2 Database Backups

#### 7.2.1 Manual Backup Procedures

**Simple Database Backup**:

```bash
# Create backup with timestamp
cp /mnt/storage/data/traffic_data.db \
   /mnt/storage/backups/traffic_data_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh /mnt/storage/backups/
```

**Compressed Database Backup**:

```bash
# Create compressed backup
sqlite3 /mnt/storage/data/traffic_data.db .dump | gzip > \
  /mnt/storage/backups/traffic_data_$(date +%Y%m%d).sql.gz

# Verify
gunzip -t /mnt/storage/backups/traffic_data_$(date +%Y%m%d).sql.gz
```

#### 7.2.2 Automated Backup Scripts

**Create Backup Script** `/home/pi/backup_database.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/mnt/storage/backups"
DB_PATH="/mnt/storage/data/traffic_data.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/traffic_data_${TIMESTAMP}.db"

# Create backup directory if not exists
mkdir -p ${BACKUP_DIR}

# Stop database writes temporarily
docker compose stop database-persistence

# Copy database
cp ${DB_PATH} ${BACKUP_FILE}

# Restart database service
docker compose start database-persistence

# Compress backup
gzip ${BACKUP_FILE}

# Delete backups older than 7 days
find ${BACKUP_DIR} -name "traffic_data_*.db.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Make executable:
```bash
chmod +x /home/pi/backup_database.sh
```

**Schedule Daily Backup** (crontab):

```bash
crontab -e
```

Add line:
```cron
0 2 * * * /home/pi/backup_database.sh >> /home/pi/backup.log 2>&1
```

#### 7.2.3 Backup Verification

**Verify Backup Integrity**:

```bash
# Decompress and test backup
gunzip -t /mnt/storage/backups/traffic_data_20251002.db.gz

# Or restore to temporary location and verify
gunzip -c /mnt/storage/backups/traffic_data_20251002.db.gz > /tmp/test_restore.db
sqlite3 /tmp/test_restore.db "PRAGMA integrity_check;"
rm /tmp/test_restore.db
```

**Verify Backup Contains Data**:

```bash
# Check record count in backup
gunzip -c /mnt/storage/backups/traffic_data_20251002.db.gz | \
  sqlite3 :memory: "SELECT COUNT(*) FROM detection_events;"
```

### 7.3 Configuration Backups

#### 7.3.1 Docker Compose Files

**Backup via Git**:

```bash
cd ~/CST_590_Computer_Science_Capstone_Project

# Commit changes
git add docker-compose.yml .env
git commit -m "Configuration update: $(date +%Y-%m-%d)"

# Push to remote (if configured)
git push origin main
```

**Manual Backup**:

```bash
# Create config backup
mkdir -p /mnt/storage/backups/config
cp docker-compose.yml /mnt/storage/backups/config/docker-compose_$(date +%Y%m%d).yml
cp .env /mnt/storage/backups/config/env_$(date +%Y%m%d).txt
```

#### 7.3.2 Environment Files

**Backup .env File** (contains sensitive data):

```bash
# Encrypted backup
gpg -c /home/pi/CST_590_Computer_Science_Capstone_Project/.env
mv .env.gpg /mnt/storage/backups/config/env_$(date +%Y%m%d).gpg

# To restore
gpg -d /mnt/storage/backups/config/env_20251002.gpg > .env
```

#### 7.3.3 System Configuration

**Backup System Config Files**:

```bash
# Create system config backup
mkdir -p /mnt/storage/backups/system_config

# Backup important system files
sudo cp /boot/firmware/config.txt /mnt/storage/backups/system_config/
sudo cp /etc/docker/daemon.json /mnt/storage/backups/system_config/
sudo cp /etc/systemd/system/imx500-ai-capture.service /mnt/storage/backups/system_config/
cp ~/.bashrc /mnt/storage/backups/system_config/
crontab -l > /mnt/storage/backups/system_config/crontab_backup.txt
```

### 7.4 Disaster Recovery

#### 7.4.1 Recovery Procedures

**Scenario 1: Database Corruption**

```bash
# 1. Stop database service
docker compose stop database-persistence

# 2. Move corrupted database
mv /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.corrupted

# 3. Restore from most recent backup
gunzip -c /mnt/storage/backups/traffic_data_latest.db.gz > \
  /mnt/storage/data/traffic_data.db

# 4. Verify integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# 5. Restart service
docker compose start database-persistence

# 6. Verify operation
docker compose logs database-persistence --tail=50
```

**Scenario 2: Complete SD Card/SSD Failure**

```bash
# 1. Flash new Raspberry Pi OS to new storage
# 2. Restore system configuration (see Section 3)
# 3. Install Docker and dependencies
# 4. Clone repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project

# 5. Restore .env file from backup
# 6. Restore database from backup
mkdir -p /mnt/storage/data
gunzip -c <backup-location>/traffic_data_latest.db.gz > /mnt/storage/data/traffic_data.db

# 7. Deploy services
docker compose up -d

# 8. Verify operation
docker compose ps
```

**Scenario 3: Configuration Loss**

```bash
# Restore from Git
cd ~/CST_590_Computer_Science_Capstone_Project
git checkout HEAD -- docker-compose.yml

# Or restore from manual backup
cp /mnt/storage/backups/config/docker-compose_latest.yml docker-compose.yml
```

#### 7.4.2 Recovery Time Objectives (RTO)

**Target Recovery Times**:

| Scenario | RTO | Steps |
|----------|-----|-------|
| Single service failure | 5 minutes | Docker restart |
| Database corruption | 30 minutes | Restore from backup |
| Complete system failure | 4 hours | Rebuild from scratch + restore data |
| Hardware failure | 8 hours | Replace hardware + rebuild + restore |

#### 7.4.3 Recovery Point Objectives (RPO)

**Data Loss Tolerance**:

| Data Type | RPO | Backup Frequency |
|-----------|-----|------------------|
| Detection events | 24 hours | Daily database backup |
| Configuration | 0 (no loss) | Git version control |
| Images | 24 hours | Not backed up (acceptable loss) |
| System state | 24 hours | Daily backups |

### 7.5 Testing Recovery Procedures

**Quarterly Recovery Test**:

1. **Select Test Backup**:
   ```bash
   # Use backup from 1 week ago
   cp /mnt/storage/backups/traffic_data_$(date -d '7 days ago' +%Y%m%d)*.db.gz /tmp/
   ```

2. **Perform Test Restore**:
   ```bash
   # Restore to test location
   gunzip -c /tmp/traffic_data_*.db.gz > /tmp/test_restore.db
   
   # Verify integrity
   sqlite3 /tmp/test_restore.db "PRAGMA integrity_check;"
   
   # Verify data
   sqlite3 /tmp/test_restore.db "SELECT COUNT(*) FROM detection_events;"
   ```

3. **Document Results**:
   - Time to restore: ___ minutes
   - Data integrity: Pass/Fail
   - Record count matches: Yes/No
   - Issues encountered: ___

4. **Clean Up**:
   ```bash
   rm /tmp/test_restore.db /tmp/traffic_data_*.db.gz
   ```

---

## 8. Security Administration

### 8.1 Security Architecture

#### 8.1.1 Defense in Depth Strategy

**Security Layers**:

1. **Physical Security**: Locked enclosure, tamper detection
2. **Network Security**: Firewall (UFW), VPN (Tailscale), network isolation
3. **Transport Security**: TLS/HTTPS for all external communication
4. **Application Security**: Input validation, SQL injection prevention, security headers
5. **Access Control**: SSH key-based auth, principle of least privilege
6. **Monitoring**: Centralized logging, security event monitoring

#### 8.1.2 Network Security

**Firewall Configuration (UFW)**:

```bash
# View current rules
sudo ufw status verbose

# Expected rules:
# 22/tcp: SSH access
# 80/tcp: HTTP (redirects to HTTPS)
# 443/tcp: HTTPS encrypted access
# 41641/udp: Tailscale VPN
```

**Docker Network Isolation**:

- All containers on isolated bridge network (`app-network`)
- Only nginx-proxy exposes ports 80/443 externally
- Inter-service communication within Docker network only
- Redis bound to localhost only (`127.0.0.1:6379`)

#### 8.1.3 Application Security

**SQL Injection Prevention**:

All database queries use parameterized statements:
```python
# Good (parameterized)
cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))

# Bad (vulnerable to SQL injection)
cursor.execute(f"SELECT * FROM events WHERE id = {event_id}")
```

**Input Validation**:

- API inputs validated against expected types/ranges
- Speed values validated (1-100 mph range)
- Vehicle types validated against known list
- Timestamps validated and normalized

**Security Headers** (nginx-proxy):

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

### 8.2 Access Control

#### 8.2.1 SSH Access

**Configure SSH Key-Based Authentication**:

```bash
# On your local machine, generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to Raspberry Pi
ssh-copy-id pi@<raspberry-pi-ip>

# Test key-based login
ssh pi@<raspberry-pi-ip>
```

**Disable Password Authentication** (after verifying key access works):

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Change these lines:
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart ssh
```

**SSH Hardening**:

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Add/modify:
Port 2222  # Change from default 22
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2

# Update firewall
sudo ufw delete allow 22/tcp
sudo ufw allow 2222/tcp

# Restart SSH
sudo systemctl restart ssh
```

#### 8.2.2 VPN Access (Tailscale)

**Tailscale Access Control**:

Managed via Tailscale Admin Console (https://login.tailscale.com/admin):

1. **Device Authorization**: Approve new devices before they can connect
2. **ACLs**: Define which devices can access which services
3. **Key Expiry**: Set expiration for device authentication keys
4. **MagicDNS**: Enable for easy hostname-based access

**Example Tailscale ACL**:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["user@example.com"],
      "dst": ["pi5-traffic:443", "pi5-traffic:22"]
    }
  ]
}
```

#### 8.2.3 Dashboard Access

**No Authentication** (Current Implementation):

- Dashboard accessible via HTTPS without login
- Acceptable for internal/academic use with VPN
- Data does not contain PII

**Adding Authentication** (Optional Enhancement):

1. **HTTP Basic Auth** (nginx):
   ```bash
   # Install apache2-utils
   sudo apt install apache2-utils -y
   
   # Create password file
   sudo htpasswd -c /etc/nginx/.htpasswd admin
   
   # Add to nginx config
   auth_basic "Restricted Access";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

2. **API Key Authentication** (application-level)
3. **OAuth2** (for enterprise deployment)

### 8.3 TLS/HTTPS Configuration

#### 8.3.1 Certificate Management

**Current Setup**: Self-signed certificates for development

**Certificate Location**:
- Private Key: `/etc/nginx/ssl/nginx-selfsigned.key`
- Certificate: `/etc/nginx/ssl/nginx-selfsigned.crt`

**View Certificate Details**:

```bash
# View certificate info
openssl x509 -in /etc/nginx/ssl/nginx-selfsigned.crt -text -noout

# Check expiration date
openssl x509 -in /etc/nginx/ssl/nginx-selfsigned.crt -noout -dates
```

#### 8.3.2 Certificate Renewal

**Self-Signed Certificate Renewal** (Annual):

```bash
# Generate new certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx-selfsigned.key \
  -out /etc/nginx/ssl/nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=pi5-traffic.local"

# Restart nginx
docker compose restart nginx-proxy
```

**Let's Encrypt Certificate Renewal** (If using public domain):

```bash
# Renew certificates (automatic via certbot)
sudo certbot renew

# Or manually
sudo certbot renew --nginx
```

#### 8.3.3 Security Headers

**Nginx Security Headers** (already configured):

```nginx
# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevent MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# XSS protection
add_header X-XSS-Protection "1; mode=block" always;

# HSTS (force HTTPS)
add_header Strict-Transport-Security "max-age=31536000" always;
```

**Test Security Headers**:

```bash
# Check headers
curl -I https://localhost -k

# Or use online tool: https://securityheaders.com/
```

### 8.4 Security Hardening

#### 8.4.1 OS Hardening

**Disable Unused Services**:

```bash
# List running services
systemctl list-units --type=service --state=running

# Disable unnecessary services (examples)
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

**Configure Automatic Security Updates**:

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades -y

# Configure
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**Fail2Ban** (SSH brute-force protection):

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Enable and start
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Check status
sudo fail2ban-client status sshd
```

#### 8.4.2 Docker Security

**Docker Daemon Security**:

Edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "userns-remap": "default"
}
```

**Container Security Best Practices** (Already implemented):

- ✅ Non-root users (`user: "${HOST_UID}:${HOST_GID}"`)
- ✅ Minimal privileges (`privileged: false`)
- ✅ Specific device access only (UART, GPIO)
- ✅ Read-only root filesystem (where possible)
- ✅ Health checks for all services
- ✅ Resource limits (can be added if needed)

**Scan Docker Images for Vulnerabilities**:

```bash
# Install trivy
sudo apt install trivy -y

# Scan image
trivy image gcumerk/cst590-capstone-public:latest
```

#### 8.4.3 Application Security

**Environment Variable Security**:

```bash
# Protect .env file
chmod 600 ~/CST_590_Computer_Science_Capstone_Project/.env

# Don't commit to Git
echo ".env" >> .gitignore
```

**Secrets Management** (Optional enhancement):

- Use Docker secrets
- Use external secrets manager (HashiCorp Vault, AWS Secrets Manager)
- Encrypt sensitive environment variables

### 8.5 Security Monitoring

#### 8.5.1 Log Monitoring

**Monitor Authentication Logs**:

```bash
# SSH authentication attempts
sudo grep "Failed password" /var/log/auth.log | tail -20

# Successful logins
last -20

# Failed logins
sudo lastb -20
```

**Monitor Application Logs**:

```bash
# Search for security-related events
docker compose logs | grep -i "unauthorized\|forbidden\|denied"

# Monitor API access
docker compose logs traffic-monitor | grep -i "GET\|POST\|PUT\|DELETE"
```

#### 8.5.2 Intrusion Detection

**Install and Configure Intrusion Detection** (Optional):

```bash
# Install AIDE (Advanced Intrusion Detection Environment)
sudo apt install aide -y

# Initialize database
sudo aideinit

# Run check
sudo aide --check
```

**Monitor Network Connections**:

```bash
# Active connections
sudo netstat -tunap

# Monitor for suspicious connections
sudo tcpdump -i eth0 -n
```

#### 8.5.3 Vulnerability Scanning

**Regular Vulnerability Scans**:

```bash
# Update package database
sudo apt update

# Check for vulnerabilities
sudo apt list --upgradable

# Scan Docker images
trivy image gcumerk/cst590-capstone-public:latest
```

**Security Audit**:

```bash
# Install Lynis (security auditing tool)
sudo apt install lynis -y

# Run audit
sudo lynis audit system

# Review results in /var/log/lynis.log
```

### 8.6 Incident Response

#### 8.6.1 Incident Detection

**Signs of Security Incident**:

1. **Unusual Network Activity**: Unexpected connections, high traffic
2. **Failed Login Attempts**: Multiple failed SSH attempts
3. **Service Disruptions**: Services repeatedly crashing
4. **Resource Exhaustion**: Sudden high CPU/memory/disk usage
5. **Log Anomalies**: Gaps in logs, suspicious entries

**Detection Tools**:

```bash
# Monitor system in real-time
htop

# Monitor network
sudo iftop

# Check for suspicious processes
ps aux | grep -v "\[" | less

# Check open ports
sudo netstat -tulpn
```

#### 8.6.2 Response Procedures

**Incident Response Steps**:

1. **Identify and Confirm**:
   ```bash
   # Check system logs
   sudo journalctl -xe
   
   # Check authentication logs
   sudo tail -100 /var/log/auth.log
   
   # Check Docker logs
   docker compose logs --tail=500
   ```

2. **Contain**:
   ```bash
   # If SSH compromise suspected, block IP
   sudo ufw deny from <attacker-ip>
   
   # Stop compromised service
   docker compose stop <service-name>
   
   # Isolate system (extreme cases)
   sudo ufw default deny incoming
   sudo ufw default deny outgoing
   ```

3. **Eradicate**:
   ```bash
   # Change all passwords
   passwd
   
   # Rotate SSH keys
   ssh-keygen -t ed25519 -C "new_key"
   
   # Rebuild compromised containers
   docker compose down <service>
   docker compose pull <service>
   docker compose up -d <service>
   ```

4. **Recover**:
   ```bash
   # Restore from known-good backup
   # See Section 7.4 for recovery procedures
   
   # Verify system integrity
   sudo aide --check
   ```

5. **Document**:
   - What happened
   - When it was detected
   - Actions taken
   - Lessons learned
   - Preventive measures implemented

#### 8.6.3 Post-Incident Analysis

**Review and Improve**:

1. **Root Cause Analysis**: What allowed the incident to occur?
2. **Timeline**: Reconstruct sequence of events
3. **Impact Assessment**: What data/systems were affected?
4. **Prevention**: What controls can prevent recurrence?
5. **Update Procedures**: Document new detection/response procedures

**Security Improvements**:

- Tighten firewall rules
- Add monitoring/alerting
- Update security policies
- Conduct security training
- Schedule regular audits

---

## 9. Troubleshooting

### 9.1 Troubleshooting Methodology

**Systematic Approach**:

1. **Identify Symptoms**: What is not working? What error messages?
2. **Gather Information**: Check logs, status, recent changes
3. **Isolate Problem**: Is it one service or system-wide?
4. **Develop Hypothesis**: What could cause this?
5. **Test Solution**: Try fix in safe way
6. **Verify Resolution**: Confirm problem is solved
7. **Document**: Record issue and solution for future reference

**First Steps for Any Issue**:

```bash
# 1. Check service status
docker compose ps

# 2. Check recent logs
docker compose logs --tail=100

# 3. Check system resources
docker stats --no-stream
htop

# 4. Check disk space
df -h

# 5. Check network connectivity
ping 8.8.8.8
```

### 9.2 Common Issues

#### 9.2.1 Service Won't Start

**Symptoms**:
- Container shows "Restarting" continuously
- Container shows "Exited" status
- Service crashes immediately after start

**Diagnosis**:

```bash
# Check specific service logs
docker compose logs <service-name> --tail=100

# Check why container exited
docker inspect <container-name> | grep -A 10 "State"

# Check for port conflicts
sudo netstat -tlnp | grep <port>
```

**Common Causes and Solutions**:

| Cause | Symptom | Solution |
|-------|---------|----------|
| **Port already in use** | "Address already in use" error | `sudo lsof -i :<port>` and kill conflicting process |
| **Missing environment variable** | Service fails with config error | Verify `.env` file has all required variables |
| **Permissions error** | "Permission denied" on files/devices | Check `chown` and `chmod` on `/mnt/storage`, verify group membership |
| **Device not accessible** | "No such file or directory /dev/ttyAMA0" | Enable UART in `config.txt`, check device exists |
| **Out of memory** | Container OOMKilled | Check `docker stats`, increase swap, reduce containers |
| **Dependency not ready** | Service exits waiting for Redis/database | Check `depends_on` in docker-compose.yml, verify Redis is healthy |

**Example: Radar Service Won't Start**:

```bash
# Check if UART device exists
ls -l /dev/ttyAMA0

# If missing, enable UART
sudo nano /boot/firmware/config.txt
# Add: enable_uart=1, dtoverlay=disable-bt
sudo reboot

# Check user groups
groups pi | grep dialout

# If missing, add user to group
sudo usermod -a -G dialout pi
# Log out and back in

# Check device permissions
sudo chmod 666 /dev/ttyAMA0  # Temporary fix

# Restart service
docker compose restart radar-service
```

#### 9.2.2 Performance Degradation

**Symptoms**:
- Slow API responses
- High latency for detections
- Dashboard sluggish
- High CPU/memory usage

**Diagnosis**:

```bash
# Check container resources
docker stats

# Check system load
uptime
htop

# Check disk I/O
iostat -x 1 5

# Check database size
ls -lh /mnt/storage/data/traffic_data.db

# Check for memory leaks
docker stats --format "table {{.Name}}\t{{.MemUsage}}" --no-stream
```

**Solutions**:

1. **Database Too Large**:
   ```bash
   # Check database size
   sqlite3 /mnt/storage/data/traffic_data.db "SELECT COUNT(*) FROM detection_events;"
   
   # Run VACUUM
   docker compose stop database-persistence
   sqlite3 /mnt/storage/data/traffic_data.db "VACUUM;"
   docker compose start database-persistence
   ```

2. **Too Many Old Images**:
   ```bash
   # Check image count
   ls /mnt/storage/ai_camera_images/ | wc -l
   
   # Verify data-maintenance service is running
   docker compose logs data-maintenance --tail=50
   
   # Manual cleanup if needed
   find /mnt/storage/ai_camera_images/ -name "*.jpg" -mtime +1 -delete
   ```

3. **High CPU from One Service**:
   ```bash
   # Identify culprit
   docker stats --no-stream | sort -k3 -h
   
   # Restart heavy service
   docker compose restart <service-name>
   
   # Check logs for errors causing high CPU
   docker compose logs <service-name> --tail=200
   ```

4. **Memory Leak**:
   ```bash
   # Restart services daily via cron
   crontab -e
   # Add: 0 3 * * * cd ~/CST_590_Computer_Science_Capstone_Project && docker compose restart
   ```

#### 9.2.3 Network Connectivity Issues

**Symptoms**:
- Can't access dashboard
- API not responding
- Weather data not updating
- Services can't communicate

**Diagnosis**:

```bash
# Check if services are listening
sudo netstat -tlnp | grep -E "80|443|5000|6379"

# Check nginx is running
docker compose ps nginx-proxy

# Check internal network
docker network inspect traffic_monitor_bridge

# Test API from localhost
curl http://localhost:5000/health

# Test from external
curl http://<raspberry-pi-ip>

# Check firewall
sudo ufw status
```

**Solutions**:

1. **Can't Access Dashboard Externally**:
   ```bash
   # Verify firewall allows HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   
   # Check nginx is running
   docker compose ps nginx-proxy
   docker compose logs nginx-proxy --tail=50
   
   # Verify nginx config
   docker exec nginx-proxy nginx -t
   ```

2. **Services Can't Reach Redis**:
   ```bash
   # Check Redis is healthy
   docker compose ps redis
   docker exec redis redis-cli ping
   
   # Check services are on same network
   docker network inspect traffic_monitor_bridge | grep -A 5 "Containers"
   
   # Restart Redis and dependent services
   docker compose restart redis
   docker compose restart
   ```

3. **Weather API Not Working**:
   ```bash
   # Check internet connectivity
   ping 8.8.8.8
   curl https://api.checkwx.com
   
   # Check API key is configured
   docker compose config | grep CHECKWX_API_KEY
   
   # Check airport-weather service logs
   docker compose logs airport-weather --tail=50
   
   # Verify API key is valid
   curl -H "X-API-Key: $CHECKWX_API_KEY" https://api.checkwx.com/metar/KDEN/decoded
   ```

#### 9.2.4 Hardware Sensor Failures

**Symptom: Radar Not Detecting**:

```bash
# Check radar service logs
docker compose logs radar-service --tail=100

# Check UART device
ls -l /dev/ttyAMA0

# Test UART directly
cat /dev/ttyAMA0
# Should see JSON output: {"speed": ..., "magnitude": ...}

# Check radar power
# Verify 5V power connected to radar

# If no output:
# 1. Check wiring (TX/RX may be swapped)
# 2. Check baud rate (should be 19200)
# 3. Verify radar sensor is powered
# 4. Try different GPIO pins
```

**Symptom: Camera Not Capturing**:

```bash
# Check IMX500 service
sudo systemctl status imx500-ai-capture.service

# Check service logs
sudo journalctl -u imx500-ai-capture.service -n 100

# Test camera directly
libcamera-hello --list-cameras
# Should show IMX500 detected

# If not detected:
# 1. Check CSI cable connection
# 2. Enable camera in raspi-config
# 3. Reboot
# 4. Check camera is not defective
```

**Symptom: DHT22 Read Failures**:

```bash
# Check DHT22 service logs
docker compose logs dht22-weather --tail=50

# Normal: ~5% read failure rate (expected)
# High failure rate (>20%): Hardware issue

# Check wiring:
# - Data pin to GPIO 4
# - VCC to 3.3V
# - GND to GND
# - 10kΩ pull-up resistor between data and VCC

# Test manually
python3 << EOF
import Adafruit_DHT
sensor = Adafruit_DHT.DHT22
pin = 4
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
print(f"Temp: {temperature}C, Humidity: {humidity}%")
EOF
```

### 9.3 Component-Specific Troubleshooting

#### 9.3.1 Radar Service Issues

**Issue: No Radar Data**:

```bash
# 1. Verify UART is enabled
grep "enable_uart" /boot/firmware/config.txt

# 2. Check serial console is disabled
sudo systemctl status serial-getty@ttyAMA0.service
# Should be inactive/disabled

# 3. Check device permissions
ls -l /dev/ttyAMA0
# Should be: crw-rw---- 1 root dialout

# 4. Verify user in dialout group
groups pi | grep dialout

# 5. Check service can access device
docker compose logs radar-service | grep -i "permission\|denied\|error"

# 6. Test UART manually
cat /dev/ttyAMA0
# Should see JSON output
```

**Issue: Radar Data Noisy**:

```bash
# Check magnitude values
docker compose logs radar-service | grep "magnitude"

# Low magnitude (<500): Weak signal, adjust sensor position
# High magnitude (>3000): Too close, move sensor back

# Adjust speed threshold
# Edit .env or docker-compose.yml
RADAR_SPEED_THRESHOLD=2.0  # Increase to reduce noise
```

#### 9.3.2 Camera Service Issues

**Issue: Camera Service Crashes**:

```bash
# Check service status
sudo systemctl status imx500-ai-capture.service

# Check logs for error
sudo journalctl -u imx500-ai-capture.service -n 200 | grep -i error

# Common causes:
# - Redis not accessible from host
# - Camera hardware failure
# - Out of memory

# Test Redis connectivity from host
redis-cli -h 127.0.0.1 ping

# If Redis unreachable:
# Check Redis port binding in docker-compose.yml
ports:
  - "127.0.0.1:6379:6379"
```

**Issue: AI Classification Poor Accuracy**:

```bash
# Check lighting conditions (camera needs good lighting)
# Check camera angle (should cover same area as radar)
# Check distance (vehicles should be 20-100 ft for best results)

# Review recent detections
curl -s http://localhost:5000/api/detections/recent | jq '.[] | {type: .vehicle_type, confidence: .confidence}'

# Low confidence (<0.7): Lighting, angle, or distance issue
# Wrong classifications: Objects outside training set
```

#### 9.3.3 Weather Service Issues

**Issue: DHT22 High Failure Rate**:

```bash
# Check failure rate
docker compose logs dht22-weather | grep -i "failed\|error" | wc -l

# If >20% failure rate:
# 1. Check wiring (especially pull-up resistor)
# 2. Check power supply (needs stable 3.3V)
# 3. Try different GPIO pin
# 4. Replace sensor (DHT22 sensors can degrade)
```

**Issue: Airport Weather Not Updating**:

```bash
# Check service logs
docker compose logs airport-weather --tail=50

# Verify API key
docker compose config | grep CHECKWX_API_KEY

# Test API manually
curl -H "X-API-Key: your_key_here" https://api.checkwx.com/metar/KDEN/decoded

# Common issues:
# - API key invalid/expired
# - API rate limit exceeded (500/day free tier)
# - Airport ICAO code incorrect
# - Internet connectivity issue
```

#### 9.3.4 Database Issues

**Issue: Database Locked**:

```bash
# Check for multiple processes accessing database
lsof /mnt/storage/data/traffic_data.db

# Stop all services
docker compose down

# Check database integrity
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
mv /mnt/storage/data/traffic_data.db /mnt/storage/data/traffic_data.db.corrupted
gunzip -c /mnt/storage/backups/traffic_data_latest.db.gz > /mnt/storage/data/traffic_data.db

# Restart services
docker compose up -d
```

**Issue: Database Growing Too Fast**:

```bash
# Check current size
ls -lh /mnt/storage/data/traffic_data.db

# Check record count
sqlite3 /mnt/storage/data/traffic_data.db "SELECT COUNT(*) FROM detection_events;"

# Check retention policy
docker compose config | grep DATABASE_RETENTION_DAYS

# Adjust retention (default 90 days)
# Edit .env
DATABASE_RETENTION_DAYS=30

# Restart database service
docker compose restart database-persistence

# Manual cleanup (older than 30 days)
sqlite3 /mnt/storage/data/traffic_data.db \
  "DELETE FROM detection_events WHERE timestamp < datetime('now', '-30 days');"
sqlite3 /mnt/storage/data/traffic_data.db "VACUUM;"
```

#### 9.3.5 API Gateway Issues

**Issue: API Slow to Respond**:

```bash
# Check API response time
time curl -s http://localhost:5000/api/health > /dev/null

# Check database size (large DB = slow queries)
ls -lh /mnt/storage/data/traffic_data.db

# Run VACUUM
docker compose stop database-persistence
sqlite3 /mnt/storage/data/traffic_data.db "VACUUM; ANALYZE;"
docker compose start database-persistence

# Check for slow queries in logs
docker compose logs traffic-monitor | grep -i "slow\|timeout"
```

**Issue: WebSocket Disconnects**:

```bash
# Check realtime-events-broadcaster logs
docker compose logs realtime-events-broadcaster --tail=100

# Check nginx WebSocket config
docker exec nginx-proxy cat /etc/nginx/nginx.conf | grep -A 5 "websocket"

# Should have:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";

# Check for connection timeouts
docker compose logs nginx-proxy | grep -i "timeout"
```

### 9.4 Diagnostic Commands

#### 9.4.1 Docker Commands

**Container Status**:
```bash
# List all containers
docker compose ps

# List with formatting
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Show only unhealthy containers
docker ps --filter health=unhealthy

# Show container resource usage
docker stats --no-stream
```

**Container Inspection**:
```bash
# Full container details
docker inspect <container-name>

# Get specific information
docker inspect --format='{{.State.Status}}' <container-name>
docker inspect --format='{{.State.Health.Status}}' <container-name>
docker inspect --format='{{.RestartCount}}' <container-name>

# Get IP address
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container-name>
```

**Network Diagnostics**:
```bash
# List networks
docker network ls

# Inspect network
docker network inspect traffic_monitor_bridge

# Test connectivity between containers
docker exec traffic-monitor ping -c 3 redis
docker exec radar-service ping -c 3 redis
```

#### 9.4.2 Log Inspection

**View Logs**:
```bash
# All services
docker compose logs

# Specific service
docker compose logs <service-name>

# Last N lines
docker compose logs --tail=100

# Follow (live tail)
docker compose logs -f

# Since timestamp
docker compose logs --since 2h
docker compose logs --since "2025-10-02T10:00:00"

# Multiple services
docker compose logs radar-service vehicle-consolidator database-persistence
```

**Search Logs**:
```bash
# Search for errors
docker compose logs | grep -i error

# Search with context (5 lines before/after)
docker compose logs | grep -C 5 -i error

# Count occurrences
docker compose logs | grep -c "Error"

# Filter by timestamp
docker compose logs --since 24h | grep -i "error"

# Export logs
docker compose logs > system_logs_$(date +%Y%m%d).txt
```

#### 9.4.3 Network Diagnostics

**Check Listening Ports**:
```bash
# All listening ports
sudo netstat -tulpn

# Specific port
sudo netstat -tulpn | grep :5000

# Using ss (modern alternative)
sudo ss -tulpn

# Check Docker-exposed ports
docker compose ps --format "table {{.Name}}\t{{.Ports}}"
```

**Test Connectivity**:
```bash
# Test HTTP endpoint
curl http://localhost:5000/health

# Test with timing
curl -w "@-" -o /dev/null -s http://localhost:5000/health << 'EOF'
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
EOF

# Test WebSocket
websocat wss://localhost/ws -k

# Test Redis
docker exec redis redis-cli ping

# Test database
docker exec database-persistence python -c "import sqlite3; print('OK')"
```

#### 9.4.4 Resource Monitoring

**System Resources**:
```bash
# CPU and memory
free -h
top -bn1 | head -20

# Detailed CPU stats
mpstat 1 5

# Disk usage
df -h
du -sh /mnt/storage/*

# Disk I/O
iostat -x 1 5

# Network I/O
ifstat 1 5

# Process list sorted by CPU
ps aux --sort=-%cpu | head -20

# Process list sorted by memory
ps aux --sort=-%mem | head -20
```

**Container Resources**:
```bash
# Real-time stats
docker stats

# Snapshot
docker stats --no-stream

# Formatted output
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Specific containers
docker stats redis traffic-monitor database-persistence --no-stream
```

### 9.5 Support Resources

**Documentation**:
- **User Guide**: `~/CST_590_Computer_Science_Capstone_Project/documentation/docs/User_Guide.md`
- **Technical Design**: `~/CST_590_Computer_Science_Capstone_Project/documentation/docs/Technical_Design.md`
- **Testing Documentation**: `~/CST_590_Computer_Science_Capstone_Project/documentation/docs/Testing_Documentation.md`
- **Requirements Specification**: `~/CST_590_Computer_Science_Capstone_Project/documentation/docs/Requirements_Specification.md`

**Online Resources**:
- **GitHub Repository**: https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project
- **Docker Documentation**: https://docs.docker.com/
- **Raspberry Pi Documentation**: https://www.raspberrypi.com/documentation/
- **Redis Documentation**: https://redis.io/documentation

**Community Support**:
- **Raspberry Pi Forums**: https://forums.raspberrypi.com/
- **Docker Forums**: https://forums.docker.com/
- **Stack Overflow**: Tag questions with `raspberry-pi`, `docker`, `python`

**Hardware Support**:
- **Raspberry Pi Support**: https://www.raspberrypi.com/support/
- **Sony IMX500**: https://www.sony-semicon.com/en/products/is/industry/imx500.html
- **OmniPreSense OPS243**: https://omnipresense.com/support/

---

## 10. Performance Tuning

### 10.1 Performance Baselines

#### 10.1.1 Expected Performance Metrics

**Latency Targets**:

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| End-to-End Detection Latency | <350ms | 280ms avg | ✅ Excellent |
| AI Inference Time | <100ms | 45ms avg | ✅ Excellent |
| API Response Time | <200ms | 45ms avg | ✅ Excellent |
| WebSocket Latency | <1s | <500ms | ✅ Good |
| Database Query Time | <50ms | <20ms | ✅ Excellent |

**Resource Utilization Targets**:

| Resource | Target | Achieved | Status |
|----------|--------|----------|--------|
| CPU Usage (normal) | <30% | 5-10% | ✅ Excellent |
| CPU Usage (peak) | <50% | 33% | ✅ Good |
| Memory Usage | <4GB | 900MB | ✅ Excellent |
| Disk I/O | <50MB/s | <10MB/s | ✅ Good |
| Network I/O | <10MB/s | <1MB/s | ✅ Good |

**Throughput Targets**:

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Detections per Minute | 10+ | 20+ capable | ✅ Excellent |
| API Requests per Second | 10+ | 50+ capable | ✅ Excellent |
| Database Writes per Second | 10+ | 20+ | ✅ Good |

#### 10.1.2 Performance Benchmarks

**Latency Benchmark Script**:

```bash
#!/bin/bash
# latency_benchmark.sh

echo "=== Performance Benchmark ==="
echo "Date: $(date)"
echo ""

echo "1. API Health Check Latency:"
for i in {1..10}; do
  curl -w "  Request $i: %{time_total}s\n" -o /dev/null -s http://localhost:5000/health
done

echo ""
echo "2. Detection Query Latency:"
for i in {1..10}; do
  curl -w "  Request $i: %{time_total}s\n" -o /dev/null -s http://localhost:5000/api/detections/recent?limit=10
done

echo ""
echo "3. Redis Latency:"
docker exec redis redis-cli --latency-history

echo ""
echo "4. Database Query Time:"
time sqlite3 /mnt/storage/data/traffic_data.db "SELECT COUNT(*) FROM detection_events;"

echo ""
echo "5. Container Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

Run benchmark:
```bash
chmod +x latency_benchmark.sh
./latency_benchmark.sh
```

### 10.2 System Resource Optimization

#### 10.2.1 CPU Optimization

**Current CPU Usage** (baseline):
- Normal operation: 5-10%
- Peak (during detection): 33%
- IMX500 AI inference: 0% (hardware-accelerated on NPU)

**Optimization Techniques**:

1. **Reduce Container CPU Usage**:
   ```yaml
   # Add to docker-compose.yml
   services:
     traffic-monitor:
       deploy:
         resources:
           limits:
             cpus: '0.5'  # Limit to 50% of 1 CPU
   ```

2. **Adjust Python Process Priority**:
   ```bash
   # Lower priority for non-critical services
   docker update --cpus="0.25" data-maintenance
   ```

3. **Optimize Python Code**:
   - Use connection pooling for Redis
   - Batch database operations
   - Cache frequently accessed data

#### 10.2.2 Memory Optimization

**Current Memory Usage** (baseline):
- Total system: 8GB
- Used by containers: ~900MB
- Available: ~7GB (plenty of headroom)

**Optimization Techniques**:

1. **Set Memory Limits**:
   ```yaml
   # Add to docker-compose.yml
   services:
     traffic-monitor:
       deploy:
         resources:
           limits:
             memory: 512M
           reservations:
             memory: 256M
   ```

2. **Redis Memory Optimization**:
   ```bash
   # Configure Redis maxmemory (already set via redis-optimization service)
   docker exec redis redis-cli CONFIG GET maxmemory
   
   # Set eviction policy
   docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

3. **Reduce Python Memory Usage**:
   - Use generators instead of lists
   - Clear large variables after use
   - Avoid loading large files into memory

#### 10.2.3 I/O Optimization

**Current I/O Usage** (baseline):
- Database writes: <20 writes/sec
- Log writes: Moderate
- Image writes: 24-hour retention

**Optimization Techniques**:

1. **Use NVMe SSD** (Already implemented):
   - 3-4x faster than SD card
   - Significantly improves database performance

2. **Batch Database Writes**:
   ```python
   # Already implemented in database-persistence service
   # Batch size: 10 events
   # Batch timeout: 5 seconds
   ```

3. **Optimize SQLite**:
   ```bash
   # Enable WAL mode (Write-Ahead Logging)
   sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA journal_mode=WAL;"
   
   # Increase cache size
   sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA cache_size=-64000;"  # 64MB
   
   # Synchronous mode (balance safety/performance)
   sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA synchronous=NORMAL;"
   ```

4. **Reduce Log Volume**:
   ```bash
   # Adjust log level (edit .env)
   LOG_LEVEL=WARNING  # Instead of INFO
   ```

### 10.3 Database Optimization

#### 10.3.1 Query Optimization

**Common Slow Queries**:

1. **Recent Detections Query**:
   ```sql
   -- Add index on timestamp
   CREATE INDEX IF NOT EXISTS idx_timestamp ON detection_events(timestamp DESC);
   
   -- Query will now use index
   SELECT * FROM detection_events ORDER BY timestamp DESC LIMIT 100;
   ```

2. **Statistics Queries**:
   ```sql
   -- Add index on vehicle_type
   CREATE INDEX IF NOT EXISTS idx_vehicle_type ON detection_events(vehicle_type);
   
   -- Add composite index
   CREATE INDEX IF NOT EXISTS idx_date_type ON detection_events(date(timestamp), vehicle_type);
   ```

3. **Date Range Queries**:
   ```sql
   -- Add index on date
   CREATE INDEX IF NOT EXISTS idx_date ON detection_events(date(timestamp));
   ```

**Apply Optimizations**:

```bash
# Create all recommended indexes
sqlite3 /mnt/storage/data/traffic_data.db << 'EOF'
CREATE INDEX IF NOT EXISTS idx_timestamp ON detection_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_vehicle_type ON detection_events(vehicle_type);
CREATE INDEX IF NOT EXISTS idx_date_type ON detection_events(date(timestamp), vehicle_type);
CREATE INDEX IF NOT EXISTS idx_speed ON detection_events(speed);
ANALYZE;
EOF

# Verify indexes
sqlite3 /mnt/storage/data/traffic_data.db ".indexes detection_events"
```

#### 10.3.2 Index Management

**View Existing Indexes**:
```bash
sqlite3 /mnt/storage/data/traffic_data.db ".indexes"
```

**Analyze Index Usage**:
```bash
# Check query plan
sqlite3 /mnt/storage/data/traffic_data.db << 'EOF'
EXPLAIN QUERY PLAN 
SELECT * FROM detection_events WHERE vehicle_type = 'car' LIMIT 10;
EOF
```

**Update Index Statistics**:
```bash
# Run ANALYZE periodically (monthly)
sqlite3 /mnt/storage/data/traffic_data.db "ANALYZE;"
```

#### 10.3.3 Cache Configuration

**SQLite Cache**:
```bash
# Set cache size (in pages, negative = KB)
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA cache_size=-64000;"  # 64MB

# Check current cache size
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA cache_size;"
```

**Redis Cache** (for API responses):

Already implemented via Redis. Key performance settings:

```bash
# Check Redis memory usage
docker exec redis redis-cli INFO memory

# Check hit/miss ratio
docker exec redis redis-cli INFO stats | grep keyspace
```

### 10.4 Network Optimization

#### 10.4.1 Latency Reduction

**Current Latency** (baseline):
- API: 45ms avg
- WebSocket: <500ms
- End-to-end detection: 280ms avg

**Optimization Techniques**:

1. **Enable HTTP Keep-Alive** (nginx):
   Already configured in nginx-proxy.

2. **Reduce WebSocket Overhead**:
   ```python
   # Send compressed JSON
   # Batch multiple events if possible
   ```

3. **Use Local DNS** (if accessing via hostname):
   ```bash
   # Add to /etc/hosts
   echo "192.168.1.100 pi5-traffic.local" | sudo tee -a /etc/hosts
   ```

#### 10.4.2 Throughput Optimization

**Current Throughput** (baseline):
- API: 50+ req/s capable
- Detections: 20+/min capable

**Optimization Techniques**:

1. **Enable nginx Gzip Compression**:
   Already configured in nginx-proxy.

2. **Increase Worker Threads** (if needed):
   ```yaml
   # In docker-compose.yml
   traffic-monitor:
     environment:
       - FLASK_WORKERS=4  # Adjust based on CPU cores
   ```

3. **Connection Pooling**:
   ```python
   # Use connection pool for Redis (already implemented)
   redis_pool = redis.ConnectionPool(host='redis', port=6379, max_connections=10)
   redis_client = redis.Redis(connection_pool=redis_pool)
   ```

### 10.5 Application Tuning

#### 10.5.1 Redis Configuration

**Optimize Redis Performance**:

```bash
# Check Redis configuration
docker exec redis redis-cli CONFIG GET '*'

# Set maxmemory
docker exec redis redis-cli CONFIG SET maxmemory 256mb

# Set eviction policy
docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Disable RDB snapshots (AOF only)
docker exec redis redis-cli CONFIG SET save ""

# Enable AOF rewrite
docker exec redis redis-cli CONFIG SET auto-aof-rewrite-percentage 100
docker exec redis redis-cli CONFIG SET auto-aof-rewrite-min-size 64mb
```

**Monitor Redis Performance**:

```bash
# Check slow commands
docker exec redis redis-cli SLOWLOG GET 10

# Monitor real-time
docker exec redis redis-cli MONITOR

# Check latency
docker exec redis redis-cli --latency
```

#### 10.5.2 Worker Thread Configuration

**Current Configuration**:
- Most services: Single-threaded (sufficient for workload)
- Can be scaled if needed

**Adjust Worker Threads** (if needed):

```yaml
# In docker-compose.yml
traffic-monitor:
  command: ['gunicorn', '--workers', '4', '--bind', '0.0.0.0:5000', 'wsgi:app']
```

**Balance**:
- More workers = higher concurrency
- But also = higher memory usage
- For Raspberry Pi 5: 2-4 workers recommended

#### 10.5.3 Batch Processing Optimization

**Current Batch Configuration**:
- Database writes: 10 events per batch
- Timeout: 5 seconds

**Tune Batching** (if needed):

```yaml
# In docker-compose.yml
database-persistence:
  environment:
    - BATCH_SIZE=20  # Increase batch size
    - BATCH_TIMEOUT=10  # Increase timeout
```

**Trade-offs**:
- Larger batch size = better database performance
- But = higher latency for individual events
- Longer timeout = fewer database transactions
- But = higher memory usage for buffering

---

## 11. Appendices

### 11.A Configuration File Templates

#### 11.A.1 docker-compose.yml Template

See `~/CST_590_Computer_Science_Capstone_Project/docker-compose.yml` for complete configuration.

**Key Sections**:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - ${REDIS_DATA_PATH}:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  traffic-monitor:
    image: ${DOCKER_IMAGE}
    command: ['python', 'edge_api/edge_api_gateway_enhanced.py']
    expose:
      - "5000"
    environment:
      - REDIS_HOST=redis
      - DATABASE_PATH=/app/data/traffic_data.db
      - SERVICE_NAME=api_gateway_service
    volumes:
      - ${STORAGE_ROOT}/data:/app/data
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network
    user: "${HOST_UID}:${HOST_GID}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s

networks:
  app-network:
    driver: bridge
```

#### 11.A.2 Environment Variable Template

`.env` file template:

```bash
# Storage Configuration
STORAGE_ROOT=/mnt/storage
REDIS_DATA_PATH=/mnt/storage/redis_data

# User/Group IDs
HOST_UID=1000
HOST_GID=1000

# Docker Image
DOCKER_IMAGE=gcumerk/cst590-capstone-public:latest

# Database Configuration
DATABASE_PATH=/app/data/traffic_data.db
DATABASE_RETENTION_DAYS=90

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false

# Weather Configuration
CHECKWX_API_KEY=your_api_key_here
AIRPORT_ICAO=KDEN

# Radar Configuration
RADAR_PORT=/dev/ttyAMA0
RADAR_BAUD_RATE=19200
RADAR_SPEED_THRESHOLD=2.0

# DHT22 Configuration
DHT22_GPIO_PIN=4
DHT22_READ_INTERVAL=300

# Maintenance Configuration
MAINTENANCE_IMAGE_MAX_AGE_HOURS=24
MAINTENANCE_LOG_MAX_AGE_DAYS=7
MAINTENANCE_EMERGENCY_THRESHOLD=90
MAINTENANCE_WARNING_THRESHOLD=80

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Logging Configuration
SERVICE_NAME=system
LOG_LEVEL=INFO
LOG_DIR=/app/logs
```

#### 11.A.3 Nginx Configuration Template

Example nginx configuration for reverse proxy:

```nginx
upstream api_backend {
    server traffic-monitor:5000;
}

upstream websocket_backend {
    server realtime-events-broadcaster:8001;
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # API proxy
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://websocket_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 11.B Command Reference

#### 11.B.1 Docker Commands

**Container Management**:
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart all services
docker compose restart

# Restart specific service
docker compose restart <service-name>

# View logs
docker compose logs -f

# View service status
docker compose ps

# Execute command in container
docker exec -it <container-name> <command>

# Enter container shell
docker exec -it <container-name> /bin/sh
```

**Image Management**:
```bash
# Pull latest images
docker compose pull

# Build images
docker compose build

# Remove unused images
docker image prune -a

# List images
docker images
```

**Network Management**:
```bash
# List networks
docker network ls

# Inspect network
docker network inspect traffic_monitor_bridge

# Remove unused networks
docker network prune
```

#### 11.B.2 System Commands

**Service Management**:
```bash
# systemd service (IMX500)
sudo systemctl status imx500-ai-capture.service
sudo systemctl start imx500-ai-capture.service
sudo systemctl stop imx500-ai-capture.service
sudo systemctl restart imx500-ai-capture.service
sudo journalctl -u imx500-ai-capture.service -f
```

**System Monitoring**:
```bash
# CPU/Memory usage
htop
top

# Disk usage
df -h
du -sh /mnt/storage/*

# Network connections
sudo netstat -tulpn
ss -tulpn

# Process list
ps aux | grep python
ps aux --sort=-%cpu | head -10
```

**Log Management**:
```bash
# System logs
sudo journalctl -xe
sudo journalctl --since "1 hour ago"
sudo journalctl -u imx500-ai-capture.service -n 100

# Application logs
tail -f /mnt/storage/logs/*.log
grep -i error /mnt/storage/logs/*.log
```

#### 11.B.3 Maintenance Scripts

**Database Backup**:
```bash
# Manual backup
cp /mnt/storage/data/traffic_data.db /mnt/storage/backups/traffic_data_$(date +%Y%m%d).db

# Compressed backup
sqlite3 /mnt/storage/data/traffic_data.db .dump | gzip > /mnt/storage/backups/traffic_data_$(date +%Y%m%d).sql.gz
```

**Database Maintenance**:
```bash
# VACUUM
docker compose stop database-persistence
sqlite3 /mnt/storage/data/traffic_data.db "VACUUM; ANALYZE;"
docker compose start database-persistence

# Integrity check
sqlite3 /mnt/storage/data/traffic_data.db "PRAGMA integrity_check;"
```

**Log Cleanup**:
```bash
# Delete logs older than 7 days
find /mnt/storage/logs/ -name "*.log" -mtime +7 -delete

# Delete old images
find /mnt/storage/ai_camera_images/ -name "*.jpg" -mtime +1 -delete
```

### 11.C API Reference

#### 11.C.1 Health Check Endpoints

**GET /health**
- **Purpose**: Overall system health
- **Response**: `{"status": "healthy", "redis": "connected", "database": "accessible"}`

**GET /api/health**
- **Purpose**: API service health
- **Response**: Same as /health

#### 11.C.2 Data Query Endpoints

**GET /api/detections/recent**
- **Purpose**: Get recent detections
- **Parameters**: 
  - `limit` (default: 100)
  - `hours` (default: 24)
- **Example**: `/api/detections/recent?limit=50&hours=12`

**GET /api/statistics/daily**
- **Purpose**: Daily statistics
- **Parameters**: `days` (default: 7)
- **Example**: `/api/statistics/daily?days=30`

**GET /api/statistics/hourly**
- **Purpose**: Hourly statistics
- **Example**: `/api/statistics/hourly`

**GET /api/statistics/vehicle-types**
- **Purpose**: Vehicle type distribution
- **Example**: `/api/statistics/vehicle-types`

#### 11.C.3 System Management Endpoints

**GET /api/status**
- **Purpose**: System status overview
- **Response**: Service status, uptime, version

**GET /api/sensors**
- **Purpose**: Sensor status
- **Response**: Radar, camera, weather sensor status

### 11.D Port Reference

| Port | Protocol | Service | Purpose | External Access |
|------|----------|---------|---------|-----------------|
| 22 | SSH | Host OS | System administration | Yes (via firewall) |
| 80 | HTTP | nginx-proxy | HTTP (redirects to HTTPS) | Yes |
| 443 | HTTPS | nginx-proxy | Encrypted web access | Yes |
| 5000 | HTTP | traffic-monitor | API Gateway | No (internal only) |
| 6379 | TCP | redis | Redis server | No (localhost only) |
| 8001 | HTTP/WS | realtime-events-broadcaster | WebSocket streaming | No (internal only) |
| 41641 | UDP | tailscale | VPN | Yes (if Tailscale installed) |

### 11.E Environment Variable Reference

See Section 11.A.2 for complete list.

**Critical Variables**:
- `STORAGE_ROOT`: Base storage path
- `CHECKWX_API_KEY`: Weather API key
- `DATABASE_RETENTION_DAYS`: Data retention period
- `DOCKER_IMAGE`: Docker image to use

### 11.F Glossary of Terms

| Term | Definition |
|------|------------|
| **Edge Computing** | Processing data at the source (device) rather than in the cloud |
| **NPU** | Neural Processing Unit - specialized hardware for AI inference |
| **UART** | Universal Asynchronous Receiver/Transmitter - serial communication protocol |
| **CSI** | Camera Serial Interface - protocol for connecting cameras to SoCs |
| **GPIO** | General Purpose Input/Output - configurable pins for sensors/peripherals |
| **Docker** | Containerization platform for packaging applications |
| **Redis** | In-memory data store used for pub/sub messaging |
| **SQLite** | Embedded relational database |
| **Pub/Sub** | Publish/Subscribe messaging pattern |
| **Health Check** | Automated test to verify service is functioning |
| **TLS/HTTPS** | Transport Layer Security - encrypted HTTP |
| **VPN** | Virtual Private Network - secure remote access |
| **API** | Application Programming Interface |
| **REST** | Representational State Transfer - API design pattern |
| **WebSocket** | Full-duplex communication protocol for real-time data |

### 11.G Related Documentation

**Project Documentation**:
1. **User Guide**: End-user instructions for using the system
2. **Technical Design**: Detailed system architecture and design decisions
3. **Testing Documentation**: Comprehensive testing procedures and results
4. **Requirements Specification**: Formal requirements and traceability
5. **Implementation & Deployment Guide**: Step-by-step deployment instructions

**External Documentation**:
- Raspberry Pi Documentation: https://www.raspberrypi.com/documentation/
- Docker Documentation: https://docs.docker.com/
- Redis Documentation: https://redis.io/documentation
- SQLite Documentation: https://www.sqlite.org/docs.html
- Nginx Documentation: https://nginx.org/en/docs/

---

## 12. Table of Figures

**Figure 1: System Architecture Diagram**
- Location: Section 2.1
- Description: Microservices architecture with 5 layers (Presentation, Application, Business Logic, Data Collection, Infrastructure)

**Figure 2: Hardware Component Layout**
- Location: Section 2.2
- Description: Physical layout of Raspberry Pi 5, IMX500 camera, OPS243-C radar, DHT22 sensor

**Figure 3: Docker Container Stack**
- Location: Section 2.3.1
- Description: 12 Docker containers with health checks and restart policies

**Figure 4: Service Dependency Graph**
- Location: Section 2.3.2
- Description: Service startup order and runtime dependencies

**Figure 5: Data Flow Diagram**
- Location: Section 2.3.3
- Description: Detection event flow from radar → camera → consolidation → persistence → API

**Figure 6: Network Architecture**
- Location: Section 2.4
- Description: Port configuration, Docker network, VPN access, external APIs

**Figure 7: Deployment Process Flow**
- Location: Section 4.2
- Description: Step-by-step deployment process from clone to verification

**Figure 8: Health Check Architecture**
- Location: Section 6.1
- Description: Docker health checks, API endpoints, sensor status checks

**Figure 9: Backup Strategy**
- Location: Section 7.1
- Description: Backup frequency, retention policy, storage requirements

**Figure 10: Security Architecture**
- Location: Section 8.1
- Description: Defense in depth layers from physical to application security

---

**END OF DOCUMENT**

---

## Document Revision History

| Version | Date | Author | Section | Changes |
|---------|------|--------|---------|---------|
| 1.0.0 | 2025-10-02 | Mark Merkens | All | Initial framework creation |
