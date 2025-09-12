# SSH connection info: ssh merk@100.121.231.16

## Documentation

This folder contains all project documentation, guides, and related resources for the Raspberry Pi 5 Edge ML Traffic Monitoring System. Use these documents to install, configure, deploy, and maintain the system.

## Included Documents

- **docs/User_Guide.md** – End-user guide for system features, dashboard, and troubleshooting
- **docs/Implementation_Deployment.md** – Step-by-step setup, installation, and deployment instructions
- **docs/Technical_Design.md** – System architecture, hardware design, database schema, and API specifications
- **docs/Project_Management.md** – Project plan, timeline, risk management, and QA
- **docs/References_Appendices.md** – References, glossary, and appendices
- **docs/Documentation_TODO.md** – Living list of outstanding, in-progress, and completed documentation tasks

## Host-Capture Architecture Documentation

Due to OpenCV 4.12.0 compatibility issues with the Sony IMX500 AI camera in Docker containers, a specialized **Host-Capture/Container-Process Architecture** has been implemented. This solution separates image capture (host-side) from processing (container-side) via shared volume mounting.

### Host-Capture Architecture Documents

- **HOST_CAPTURE_ARCHITECTURE.md** – Complete technical architecture overview, components, data flow, and performance characteristics
- **HOST_CAPTURE_DEPLOYMENT.md** – Step-by-step deployment guide with prerequisites, installation, and verification procedures
- **HOST_CAPTURE_API.md** – Comprehensive API reference for all components including usage examples and integration patterns
- **HOST_CAPTURE_TROUBLESHOOTING.md** – Systematic troubleshooting guide covering common issues, diagnostics, and recovery procedures

## Quick Links

- [User Guide](./docs/User_Guide.md)
- [Implementation & Deployment Guide](./docs/Implementation_Deployment.md)
- [Technical Design Document](./docs/Technical_Design.md)
- [Project Management Summary](./docs/Project_Management.md)
- [References & Appendices](./docs/References_Appendices.md)
- [Documentation TODO List](./docs/Documentation_TODO.md)

For questions or suggestions, please see the User Guide or contact the project team.
