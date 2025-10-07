# Project Documentation

**Edge AI Traffic Monitoring System**  
**Grand Canyon University - CST 590 Capstone Project**

---

## 📚 Documentation Structure

This directory contains all project documentation organized by category:

### 🚀 [Deployment](./deployment/)
Deployment guides and setup instructions for production systems:
- [API Gateway Deployment](./deployment/API_GATEWAY_DEPLOYMENT_GUIDE.md)
- [Camera Service Deployment](./deployment/CAMERA_SERVICE_DEPLOYMENT_GUIDE.md)
- [Weather Services Deployment](./deployment/WEATHER_SERVICES_DEPLOYMENT_GUIDE.md)
- [Containerization Guide](./deployment/CONTAINERIZATION_GUIDE.md)
- [Pi5 Camera Docker Guide](./deployment/PI5_CAMERA_DOCKER_GUIDE.md)

### 🏗️ [Architecture](./architecture/)
System architecture and design documentation:
- [IMX500 & Radar Integration](./architecture/IMX500_RADAR_INTEGRATION_GUIDE.md)
- [DHT22 Architecture Evolution](./architecture/DHT22_ARCHITECTURE_EVOLUTION.md)
- [Motion Detection Strategy](./architecture/MOTION_DETECTION_STRATEGY.md)

### ⚙️ [Operations](./operations/)
Operational guides for running and maintaining the system:
- [Logging & Debugging Guide](./operations/LOGGING_AND_DEBUGGING_GUIDE.md)
- [Quick Logging Reference](./operations/QUICK_LOGGING_REFERENCE.md)
- [Logging Error Fixes](./operations/LOGGING_ERROR_FIXES.md)
- [Docker Best Practices](./operations/DOCKER_BEST_PRACTICES.md)
- [Deployment Notes](./operations/DEPLOYMENT_NOTES.md)

### 📝 [Implementation](./implementation/)
Implementation summaries and cleanup documentation:
- [Cleanup Implementation Summary](./implementation/CLEANUP_IMPLEMENTATION_SUMMARY.md)
- [Project Cleanup & Hardening Executive Summary](./implementation/PROJECT_CLEANUP_AND_HARDENING_EXECUTIVE_SUMMARY.md)
- [Phase 3 Cleanup Analysis](./implementation/PHASE_3_CLEANUP_ANALYSIS.md)
- [Docker Best Practices Implementation](./implementation/DOCKER_BEST_PRACTICES_IMPLEMENTATION_SUMMARY.md)
- [IMX500 Implementation Summary](./implementation/IMX500_IMPLEMENTATION_SUMMARY.md)
- [Service Standardization Summary](./implementation/SERVICE_STANDARDIZATION_SUMMARY.md)
- [Docker Build Trigger](./implementation/DOCKER_BUILD_TRIGGER.md)
- [Script Cleanup Plan](./implementation/SCRIPT_CLEANUP_PLAN.md)

### ✅ [Checklists](./checklists/)
Deployment checklists and changelogs:
- [IMX500 Deployment Checklist](./checklists/IMX500_DEPLOYMENT_CHECKLIST.md)
- [Radar Service Changelog](./checklists/RADAR_SERVICE_CHANGELOG.md)

---

## 🔗 Quick Links

### Getting Started
- **Project README**: [../README.md](../README.md)
- **License**: [../LICENSE](../LICENSE)

### External Documentation
- **Project Website**: [https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/](https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/)
- **Capstone Presentation**: [website/docs/capstone-presentation.mp4](../website/docs/capstone-presentation.mp4)

### API Documentation
- **Swagger/OpenAPI**: Available at `http://localhost:5000/api/docs` when running

---

## 📖 Documentation Standards

### File Naming
- Use descriptive, uppercase names with underscores: `SERVICE_NAME_GUIDE.md`
- Deployment guides end with `_DEPLOYMENT_GUIDE.md`
- Implementation notes end with `_SUMMARY.md`
- Checklists end with `_CHECKLIST.md`

### Organization
- **Deployment**: Step-by-step setup and deployment procedures
- **Architecture**: System design and technical decisions
- **Operations**: Day-to-day operational procedures
- **Implementation**: Historical implementation notes and summaries
- **Checklists**: Pre-deployment validation and tracking

### Markdown Standards
- Include table of contents for documents > 200 lines
- Use consistent heading hierarchy (# Title, ## Section, ### Subsection)
- Include code examples with proper syntax highlighting
- Link to related documentation where relevant

---

## 🔄 Document Updates

### Recent Changes
- **Oct 7, 2025**: Reorganized all documentation into structured `docs/` directory
- **Oct 7, 2025**: Completed Phase 1 & 2 cleanup (security + organization)
- **Oct 7, 2025**: Created Phase 3 cleanup analysis

### Contributing
When adding new documentation:
1. Choose the appropriate category directory
2. Follow naming conventions
3. Update this README index
4. Link from related documents

---

## 📞 Support

For questions about documentation:
- **Issues**: [GitHub Issues](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/issues)
- **Project Owner**: @gcu-merk

---

**Last Updated**: October 7, 2025  
**Organization**: Grand Canyon University  
**Course**: CST 590 - Computer Science Capstone
