# Project Management Summary

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Project Team  

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Implementation Timeline](#1-implementation-timeline)
3. [Budget & Cost Estimates](#2-budget--cost-estimates)
4. [Risk Management Matrix](#3-risk-management-matrix)
5. [Quality Assurance](#4-quality-assurance)

**See also:**
- [Technical Design Document](./Technical_Design.md)
- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [User Guide](./User_Guide.md)
- [References & Appendices](./References_Appendices.md)

## Executive Summary

The Raspberry Pi 5 Edge ML Traffic Monitoring System is a comprehensive, edge-based solution for real-time vehicle detection, speed measurement, and traffic analytics. Leveraging a Raspberry Pi 5, AI-enabled camera, and radar sensor, the system processes data locally to reduce bandwidth, enhance privacy, and enable rapid response to traffic events. This documentation provides a clear roadmap for implementation, risk management, and quality assurance, ensuring the project is delivered on time, robustly tested, and aligned with best practices for smart city and transportation applications.

## 1. Implementation Timeline

Below is a milestone-based implementation timeline for the Raspberry Pi 5 Edge ML Traffic Monitoring System. Actual dates may vary based on project scope and resource availability.

| Milestone | Description & Sub-Tasks | Target Completion |
|-----------|-------------------------|------------------|
| Project Planning | Define requirements, select hardware, finalize architecture, identify MVP, create detailed task lists | Week 1 |
| Hardware Setup | Assemble Raspberry Pi, camera, radar sensor, storage; verify hardware; allocate buffer for hardware issues | Week 2 |
| Software Environment | Install OS, Python, dependencies, database; set up version control; test environment; buffer for integration issues | Week 2 |
| Core Development | Implement vehicle detection, radar integration, data fusion; frequent testing; break into sub-tasks (e.g., camera, radar, fusion); prioritize MVP features | Weeks 3-4 |
| Dashboard & API | Develop Edge UI, REST/WebSocket APIs, Cloud UI (if needed); incremental delivery; buffer for UI/API blockers | Weeks 5-6 |
| Testing & Validation | System integration, field testing, bug fixes, contingency for simulated data if sensors unavailable; regular backups | Weeks 7-8 |
| Documentation | Prepare technical docs, user guide, deployment instructions; update as features evolve; buffer for review | Week 8 |
| Final Review & Deployment | Final QA, stakeholder review, production deployment, contingency for last-minute issues | Week 9 |

**Iterative Development & MVP:**
This project follows an agile, milestone-based approach. The initial focus is on delivering a Minimal Viable Product (MVP) with core features, followed by iterative improvements based on feedback and testing. Each milestone includes buffer time for unforeseen issues and is broken into actionable sub-tasks to ensure steady progress and risk mitigation.

**Note:** For a visual Gantt chart, use project management tools like Trello, Asana, or GanttProject.

## 2. Budget & Cost Estimates

### Hardware Costs (Per Unit)
| Component | Model/Description | Unit Cost (USD) | Quantity | Total Cost |
|-----------|-------------------|----------------|----------|------------|
| Raspberry Pi 5 | 16GB RAM model | $120 | 1 | $120 |
| AI Camera | Sony IMX500 (Raspberry Pi AI Camera) | $70 | 1 | $70 |
| Radar Sensor | OmniPreSense OPS243-C | $89 | 1 | $89 |
| Storage | Samsung T7 SSD (256GB) | $40 | 1 | $40 |
| MicroSD Card | 64GB Class 10 | $15 | 1 | $15 |
| Power Supply | PoE+ Splitter or USB-C adapter | $25 | 1 | $25 |
| Enclosure | Weather-resistant housing | $50 | 1 | $50 |
| Mounting Hardware | Pole/wall mount kit | $30 | 1 | $30 |
| **Hardware Subtotal** | | | | **$439** |

### Software & Development Costs
| Category | Description | Cost (USD) |
|----------|-------------|------------|
| Software Licenses | Open source (PostgreSQL, Python, TensorFlow) | $0 |
| Cloud Services | Optional cloud hosting (monthly) | $20-50 |
| Development Tools | VS Code, Git, testing tools | $0 |
| **Software Subtotal** | | **$0-50** |

### Implementation & Deployment Costs
| Activity | Description | Hours | Rate | Total Cost |
|----------|-------------|-------|------|------------|
| System Integration | Hardware assembly and configuration | 8 | $75 | $600 |
| Software Deployment | OS setup, application installation | 4 | $75 | $300 |
| Testing & Validation | Field testing and calibration | 6 | $75 | $450 |
| Documentation | User training and documentation | 4 | $75 | $300 |
| **Implementation Subtotal** | | | | **$1,650** |

### Total Project Cost
- **Per Unit Hardware:** $439
- **Implementation (One-time):** $1,650
- **Monthly Operating:** $20-50 (if using cloud services)
- **Total First Unit:** $2,089 + monthly costs

*Note: Costs may vary based on supplier, location, and bulk purchasing agreements.*



## 3. Risk Management Matrix & Contingency Planning

| Risk | Impact | Likelihood | Mitigation Strategy | Monitoring/Alerting | Contingency Plan |
|------|--------|------------|---------------------|---------------------|------------------|
| Hardware failure (Pi, camera, radar) | High | Medium | Use quality components, keep spares | Health indicators, system logs | Allocate buffer time, keep spare parts, simulate data if needed |
| Data loss (storage failure) | High | Low | Regular backups, use SSD, monitor storage | Storage usage alerts, backup logs | Restore from backup, rollback to last known good state |
| ML model inaccuracy | Medium | Medium | Diverse training data, real-world validation | Model performance metrics | Retrain model, fallback to previous version |
| Network outage | Medium | Medium | Offline-first design, local storage | Network status monitoring | Operate in offline mode, auto-reconnect logic |
| Power loss | High | Low | UPS or PoE with backup, monitor power | Power status alerts | Resume on power restore, buffer for downtime |
| Security breach (API, dashboard) | High | Low | Auth, HTTPS, updates, firewall | Security logs, intrusion detection | Revoke credentials, patch vulnerabilities |
| Integration bugs (sensor fusion, API) | Medium | Medium | Incremental testing, code reviews | Automated test results, error logs | Isolate faulty module, use simulated data |
| Regulatory/compliance issues | Medium | Low | Review laws, anonymize data | Compliance checklist | Remove/modify non-compliant features |

**Contingency Planning:**
- Prioritize core MVP features to ensure essential delivery if time is tight
- Allocate buffer time in each milestone for unforeseen issues
- Plan regular backups and use version control for rollback
- Use simulated data if live sensor data is unavailable
- Monitor for hardware, network, and security risks with alerts


---


## 4. Quality Assurance & Testing Protocols

### Testing Protocols
- Break down development into small, testable sub-tasks for each milestone
- Perform frequent, incremental testing during development (unit, integration, system)
- Use automated tests and code reviews to catch issues early
- Track blockers and issues in a project management tool
- Validate MVP features first, then expand to additional features

### ML/AI Evaluation Metrics
- Track model accuracy, precision, recall, and real-world performance
- Use field testing feedback to improve models

### Documentation & Review
- Update documentation iteratively as features evolve
- Schedule regular documentation reviews before each milestone

## 5. Future Work & Clarifications

### Future Work
- **Stop Sign Violation Detection:** Planned for future implementation. The current system focuses on speed and general vehicle detection. Stop sign violation detection is a key roadmap feature (see [GitHub repo](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)).
- **Alert/Notification System:** Customizable alerting is planned. Current documentation describes the architecture; implementation is in progress.
- **Cloud/Remote Monitoring:** Cloud UI and analytics are described in the documentation. Full cloud integration and remote monitoring are planned enhancements.
- **User Interface Enhancements:** Ongoing improvements to dashboard usability and configuration options.
- **Detection Accuracy:** Improve performance in challenging lighting and weather conditions.
- **Advanced Deep Learning:** Explore new ML models for better detection/classification.
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

- Use feedback from field testing to improve models and system reliability
