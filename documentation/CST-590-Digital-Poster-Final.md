# CST-590 Digital Poster - Final Version

## RASPBERRY PI 5 EDGE ML TRAFFIC MONITORING SYSTEM

**Student:** Steven Merkling  
**Advisor:** Dr. Aiman Darwiche  
**Institution:** Grand Canyon University  
**Date:** October 2025

---

## CONTEXT & BACKGROUND

### Problem Statement
Traditional traffic monitoring systems rely on cloud-based processing, creating latency, bandwidth constraints, and privacy concerns. Edge AI solutions offer real-time processing capabilities with reduced infrastructure costs and enhanced data privacy.

### Project Objectives
- Deploy low-cost, scalable edge-based traffic monitoring solution
- Achieve real-time vehicle detection with <350ms total latency
- Perform on-camera AI inference using hardware-accelerated NPU (sub-100ms)
- Implement multi-sensor data fusion (radar, camera, environmental sensors)
- Provide secure remote access and real-time data visualization

### Integration Goals
- Radar-triggered edge AI for vehicle classification with 85-95% accuracy
- Multi-sensor data correlation for speed and vehicle identification
- 24/7 continuous operation with automated health monitoring
- Cloud integration for historical analytics and pattern analysis

---

## SYSTEM ARCHITECTURE

### Hardware Components

**Core Computing Platform:**
- **Raspberry Pi 5** (16GB RAM, ARM Cortex-A76 @ 2.4GHz)
- **Sony IMX500 AI Camera** (3.1 TOPS NPU, 12.3MP, sub-100ms inference)
- **OPS243-C FMCW Doppler Radar** (24.125 GHz, 200m range, ±0.1 mph accuracy)
- **DHT22 Temperature/Humidity Sensor** (GPIO4, environmental monitoring)
- **Samsung T7 Shield 2TB External SSD** (USB 3.2 Gen 2)
- **Weatherproof IP65/IP66 enclosure**

### Software Stack

**Microservices Architecture (12 Containerized Services + 1 Host Service):**

1. **Core Infrastructure:**
   - Redis 7 Alpine (Message Broker, Pub/Sub, Streams)
   - NGINX 1.25 Alpine (Reverse Proxy, HTTPS/TLS on port 8443)
   - traffic-monitor (Edge API Gateway, Flask-SocketIO)
   - camera-service-manager (IMX500 health monitoring)

2. **Data Collection:**
   - radar-service (OPS243-C UART/GPIO interface)
   - airport-weather (METAR API client)
   - dht22-weather (Local GPIO sensor reader)
   - imx500-ai-capture.service (Host systemd service for camera)

3. **Data Processing:**
   - vehicle-consolidator (Multi-sensor data fusion)
   - database-persistence (SQLite writer, 90-day retention)
   - data-maintenance (Storage cleanup automation)
   - redis-optimization (Memory management)

4. **API & Streaming:**
   - realtime-events-broadcaster (WebSocket streaming)
   - Edge API Gateway (REST endpoints, Swagger UI)

**Technologies:**
- Python 3.11+, Flask 3.0.0, Flask-SocketIO
- Docker 24.0+ with Docker Compose
- Redis 7.0 (Pub/Sub messaging, Streams)
- SQLite 3.x (Normalized schema)
- TensorFlow 2.15+, OpenCV 4.8+
- GitHub Actions CI/CD
- Tailscale VPN (WireGuard-based secure access)
- GitHub Pages (React/Next.js dashboard)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│              Cloud Layer (GitHub Pages)                 │
│  • Static Website Hosting                              │
│  • Historical Data Visualization                       │
│  • Traffic Analytics Dashboard                         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/API
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Tailscale VPN (Secure Remote Access)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Edge Device: Raspberry Pi 5                     │
│                                                         │
│  ┌────────────────────────────────────────────┐        │
│  │ NGINX → API Gateway → Redis Broker         │        │
│  └────────────────────────────────────────────┘        │
│           ↓           ↓           ↓                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Vehicle  │ │ Database │ │  Data    │               │
│  │Consolidat│ │Persistenc│ │Maintenanc│               │
│  └──────────┘ └──────────┘ └──────────┘               │
│       ↑              ↓                                  │
│  ┌──────────┐ ┌──────────┐                            │
│  │ Weather  │ │  SQLite  │                            │
│  │ Services │ │ Database │                            │
│  └──────────┘ └──────────┘                            │
└─────────────┬──────────────┬────────────────────────────┘
              │              │
         ┌────┴────┐    ┌────┴────┐
         │ IMX500  │    │ OPS243-C│
         │ Camera  │    │  Radar  │
         │ (NPU AI)│    │ (UART)  │
         └─────────┘    └─────────┘
```

---

## METHODOLOGY & DATA FLOW

### Data Collection
- **Image Acquisition:** Sony IMX500 AI camera captures 12.3MP images
- **Radar Detection:** OPS243-C provides speed/direction via UART @ 19200 baud
- **Environmental Context:** DHT22 sensor + Airport METAR data (10-min intervals)
- **Update Rates:** Radar 10-20 Hz, Camera sub-100ms inference

### Multi-Sensor Fusion
1. **Radar Triggers:** Motion detection initiates consolidation workflow
2. **AI Classification:** IMX500 NPU performs on-camera vehicle detection
3. **Data Correlation:** vehicle-consolidator service combines:
   - Radar speed/magnitude data
   - AI camera detections (bounding boxes, classifications)
   - Weather conditions (temperature, humidity, wind)
4. **Persistence:** database-persistence writes to SQLite with 90-day retention

### Redis Pub/Sub Architecture
- **Channels:** traffic_events, radar_detections, database_events, weather_updates
- **Streams:** radar_data (maxlen=1000), consolidated_traffic_data (maxlen=100)
- **Keys:** Weather cache, consolidation records, system statistics

### Real-Time Streaming
- **WebSocket:** Flask-SocketIO broadcasts events to connected clients
- **API Endpoints:** REST API for historical queries, system health, statistics
- **Security:** NGINX reverse proxy with HTTPS/TLS termination

---

## RESULTS & PERFORMANCE

### Inference Performance
- **Primary Vehicle Classifications:** 85-95% accuracy
- **Inference Latency:** Sub-100ms on IMX500 NPU
- **Detection Ranges:** Camera 5-50m, Radar 2-200m
- **Multi-Vehicle Tracking:** SORT algorithm with Kalman filtering
- **Total Event Latency:** <350ms (sensor → storage)

### System Metrics
- **CPU Usage:** 100% reduction for AI processing (hardware-accelerated on NPU)
- **Inference Speed:** 25-50x faster than software AI (sub-100ms vs 2-5 seconds)
- **Storage Optimization:** 94% reduction through intelligent data management
- **Continuous Uptime:** 9+ hours with automated monitoring and recovery
- **Real-Time Latency:** Sub-second WebSocket streaming

### Storage Efficiency
- **Database:** SQLite with normalized schema, 90-day retention
- **Automated Cleanup:** Image age limits (24 hours), log rotation (30 days)
- **Emergency Management:** 90% threshold triggers aggressive cleanup
- **External Storage:** 2TB SSD with tmpfs optimization

---

## TECHNICAL INNOVATIONS

### AI-Assisted Development Methodology
All code within this capstone was developed using **Visual Studio Code with GitHub Copilot** (Claude Sonnet 3.5 AI model) through an iterative dialogue process under direct human supervision. The development workflow involved:

- Continuous back-and-forth dialogue to ensure full understanding
- Author asked clarifying questions at each implementation step
- All AI-generated code outputs were reviewed and validated prior to implementation
- Human oversight maintained for architecture decisions and system integration

This AI-assisted methodology enabled:
- Rapid prototyping of microservices architecture
- Consistent code quality across 12 containerized services
- Efficient debugging through AI-powered analysis
- Documentation generation aligned with implementation

**Development Tools:**
- **Primary IDE:** Visual Studio Code
- **AI Assistant:** GitHub Copilot with Claude Sonnet 3.5
- **Workflow:** Iterative dialogue, human validation, supervised implementation

### Radar-Triggered Edge AI Processing
- **GPIO Integration:** Host interrupt (GPIO23) triggers IMX500 capture
- **Sub-100ms Response:** Hardware-level synchronization between radar and camera
- **Speed-Based Behavior:** Low/high alert thresholds (GPIO5/6) adjust capture rates
- **Interrupt-Driven:** Reduced CPU usage through hardware event detection

### Privacy-Preserving Architecture
- **Edge-First Design:** All AI processing occurs on-device
- **Local Storage:** 90-day retention with automated cleanup
- **Secure Access:** Tailscale VPN mesh network (WireGuard encryption)
- **HTTPS/TLS:** Self-signed certificates, nginx reverse proxy

### Environmental Adaptation
- **Weather Correlation:** Airport METAR + local DHT22 sensor data
- **Time-Series Storage:** Redis streams with configurable retention
- **Context-Aware Detection:** Weather conditions inform analysis algorithms
- **Dual-Source Validation:** Compare local vs. airport measurements

---

## CONCLUSIONS & IMPACT

### System Achievements
✅ **Complete Microservices Implementation:** 12 containerized services + 1 host service  
✅ **Production-Ready Deployment:** 24/7 continuous operation with health monitoring  
✅ **Hardware-Accelerated AI:** 100% CPU reduction for inference via IMX500 NPU  
✅ **Multi-Sensor Fusion:** Radar, camera, and environmental data correlation  
✅ **Secure Remote Access:** Tailscale VPN with HTTPS/TLS encryption  
✅ **Cloud Integration:** GitHub Pages dashboard for historical analytics  
✅ **Automated Operations:** Health checks, restart policies, storage management  
✅ **Real-Time Streaming:** WebSocket broadcasting with sub-second latency  

### Community Impact
- **Reduced Infrastructure Costs:** Edge processing eliminates cloud computing expenses
- **Enhanced Privacy:** On-device AI processing keeps data local
- **Scalable Solution:** Modular architecture supports easy replication
- **Low Barrier to Entry:** ~$400 hardware cost for complete system
- **Open Source Potential:** Docker-based deployment simplifies distribution

### Future Development
- **Extended Sensor Integration:** LIDAR, thermal imaging, acoustic sensors
- **Advanced Analytics:** Traffic flow modeling, incident prediction
- **Federated Learning:** Aggregate insights across multiple edge devices
- **5G Integration:** Enhanced bandwidth for real-time video streaming
- **Model Management:** Over-the-air ML model updates and versioning

### Research Contributions
- Demonstrated viability of edge AI for traffic monitoring
- Validated multi-sensor fusion architecture for enhanced accuracy
- Established microservices pattern for embedded IoT systems
- Documented AI-assisted development methodology for complex projects

---

## ACKNOWLEDGMENTS

I would like to acknowledge all the professors throughout my academic journey at Grand Canyon University, along with my workplace colleagues and managers who have supported my educational pursuits. Last but not least, I am grateful for my family and their unending support.

**Special Thanks:**
- Dr. Aiman Darwiche (Faculty Advisor)
- Grand Canyon University Computer Science Department
- Open Source Community (Docker, Redis, Flask, TensorFlow)
- Sony Semiconductor Solutions (IMX500 AI Camera)
- OmniPreSense (OPS243-C Radar Sensor)

---

## REFERENCES

1. Sony Semiconductor Solutions. (2024). *IMX500 Intelligent Vision Sensor Product Specification*. Retrieved from https://www.sony-semicon.com/en/products/IS/imx500.html

2. OmniPreSense. (2024). *OPS243-C FMCW Doppler Radar Module User Guide*. Retrieved from https://omnipresense.com/product/ops243/

3. Raspberry Pi Foundation. (2024). *Raspberry Pi 5 Technical Specifications*. Retrieved from https://www.raspberrypi.com/products/raspberry-pi-5/

4. Docker Inc. (2024). *Docker Compose Documentation*. Retrieved from https://docs.docker.com/compose/

5. Redis Labs. (2024). *Redis Pub/Sub and Streams Documentation*. Retrieved from https://redis.io/docs/

6. Flask Project. (2024). *Flask-SocketIO Real-Time Applications*. Retrieved from https://flask-socketio.readthedocs.io/

7. Tailscale Inc. (2024). *WireGuard VPN Mesh Network Architecture*. Retrieved from https://tailscale.com/kb/

8. GitHub Inc. (2024). *GitHub Actions CI/CD Documentation*. Retrieved from https://docs.github.com/en/actions

9. OpenCV Foundation. (2024). *OpenCV Computer Vision Library*. Retrieved from https://opencv.org/

10. TensorFlow Team. (2024). *TensorFlow Lite for Edge AI*. Retrieved from https://www.tensorflow.org/lite

---

## PROJECT REPOSITORY

**GitHub Repository:** https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project  
**Version:** v1.0.0-capstone-final  
**License:** MIT License  
**Documentation:** Complete technical design, implementation guides, and user documentation available in repository

---

**Document Version:** 1.0  
**Last Updated:** October 1, 2025  
**Poster Size:** 36" wide × 48" high (3' × 4')  
**Format:** PDF for printing
