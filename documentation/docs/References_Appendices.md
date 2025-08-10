

# References & Appendices

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Research Team  

## Table of Contents
1. References
2. Additional Visuals
3. Glossary
4. Code Review Summary
1. [References](#1-references)
2. [Additional Visuals](#2-additional-visuals)
3. [Glossary](#3-glossary)

**See also:**
- [Technical Design Document](./Technical_Design.md)
- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [User Guide](./User_Guide.md)
- [Project Management Summary](./Project_Management.md)

## 1. References

- **OmniPreSense OPS243-C Radar Sensor Datasheet:** [OPS-DS-003-M_OPS243.pdf](../archive/OPS-DS-003-M_OPS243.pdf)
- **Raspberry Pi 5 Documentation:** [Official Raspberry Pi Docs](https://www.raspberrypi.com/documentation/computers/)
- **Sony IMX500 AI Camera Documentation:** [Sony IMX500 Product Page](https://www.sony-semicon.com/en/products/IS/sensor/IMX500.html)
- **TensorFlow Documentation:** [https://www.tensorflow.org/](https://www.tensorflow.org/)
- **OpenCV Documentation:** [https://docs.opencv.org/](https://docs.opencv.org/)
- **Flask Documentation:** [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **Flask-SocketIO Documentation:** [https://flask-socketio.readthedocs.io/](https://flask-socketio.readthedocs.io/)
- **PostgreSQL Documentation:** [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
- **Relevant Academic Papers:**
  - Edge ML for Smart Cities: [example link]
  - Traffic Monitoring with Sensor Fusion: [example link]
- **Project Standards:**
  - IEEE 802.3af (PoE)
  - GDPR/CCPA (data privacy compliance)

## 2. Additional Visuals


### Visual References

![System Architecture Diagram](../archive/traffic_monitoring_architecture.svg)
*Figure 1: System Architecture Diagram*

![Data Flow Diagram](../archive/traffic_algorithms_data_diagram.svg)
*Figure 2: Data Flow from Sensors to Analytics and Dashboards*

![Cloud Dashboard 1](../archive/CloudUI_1.jpg)
*Figure 3: Cloud Dashboard - Main Analytics View*

![Cloud Dashboard 2](../archive/CloudUI_2.jpg)
*Figure 4: Cloud Dashboard - Event Table*

![Cloud Dashboard 3](../archive/CloudUI_3.jpg)
*Figure 5: Cloud Dashboard - System Status*

![Cloud Dashboard 4](../archive/CloudUI_4.jpg)
*Figure 6: Cloud Dashboard - Settings Panel*

![Cloud Dashboard 5](../archive/CloudUI_5.jpg)
*Figure 7: Cloud Dashboard - Historical Trends*

![Local Dashboard 1](../LocalUI.jpg)
*Figure 8: Local Edge UI - Live View*

![Local Dashboard 2](../LocalUI2.jpg)
*Figure 9: Local Edge UI - Analytics Panel*

![Enclosure Inside](../archive/ResidentialRadarEnclosureInside.jpg)
*Figure 10: Inside View of Residential Radar Enclosure*

![Enclosure Installed](../archive/ResidentialRadarEnclosureInstalled.jpg)
*Figure 11: Installed Enclosure on Site*

![Radar Sensor Board Pinout](../archive/ResidentialRadarEnclosureRadarSensorBoardPinout.jpg)
*Figure 12: Radar Sensor Board Pinout*

![Radar Sensor Pinout](../archive/ResidentialRadarEnclosureRadarSensorPinout.jpg)
*Figure 13: Radar Sensor Pinout Reference*

![Enclosure External View](../archive/ResidentialRadarEnclosureView.jpg)
*Figure 14: External View of Enclosure*

![Standard Data Flow](../archive/Traffic Monitoring System - Standard Data Flow.jpeg)
*Figure 15: Standard Data Flow Overview*

## 3. Glossary

**Edge ML:** Machine learning performed on local devices rather than in the cloud.
**OPS243-C:** A Doppler radar sensor used for speed measurement.
**YOLOv8:** A real-time object detection algorithm.
**REST API:** An interface for communication between systems using HTTP requests.
**SocketIO:** A library for real-time web communication.
**SSD:** Solid State Drive, used for fast data storage.
**PoE:** Power over Ethernet, a method for delivering power and data over a single cable.
**HDF5:** A file format for storing large scientific data.
**CSV:** Comma-Separated Values, a simple file format for tabular data.
**JSON:** JavaScript Object Notation, a lightweight data-interchange format.
# 4. Code Review Summary
The source code for this project was reviewed by a peer developer to identify bugs and improve code quality. All feedback was addressed and changes were made as appropriate. (If code is added, update this section with reviewer details and feedback summary.)

| Term | Definition |
|------|------------|
| Edge ML | Machine learning performed locally on the device (not in the cloud) |
| REST API | Web service using HTTP methods for communication |
| WebSocket | Protocol for real-time, two-way communication |
| Data Fusion | Combining data from multiple sensors for improved accuracy |
| SORT | Simple Online and Realtime Tracking algorithm |
| PoE | Power over Ethernet |
| SSD | Solid State Drive |
| PWA | Progressive Web App |
| ERD | Entity Relationship Diagram |
| ML | Machine Learning |
| AI | Artificial Intelligence |
| GDPR | General Data Protection Regulation |
| CCPA | California Consumer Privacy Act |
| API | Application Programming Interface |
| UART | Universal Asynchronous Receiver-Transmitter |
| NTP | Network Time Protocol |

## 4. Future Work & Clarifications

### Future Work
- **Reference Expansion:** Add more academic papers, standards, and regulatory references as the system evolves.
- **Visual Documentation:** Continue to update and expand the visual appendix as new diagrams and photos are produced.
- **Glossary Growth:** Expand glossary to include new terms as features and technologies are added.

### Contradictions & Clarifications
- The GitHub repository may reference additional standards, visuals, or documentation not yet included here. These will be added in future updates.
- Some referenced documents or visuals may be in draft or planned status; clarify in future revisions.

### Repository Reference
- For the latest references, visuals, and glossary updates, see: [CST_590_Computer_Science_Capstone_Project GitHub](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)
