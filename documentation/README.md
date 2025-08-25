# SSH connection info: ssh merk@100.121.231.16

## Documentation

This folder contains all project documentation, guides, and related resources for the Raspberry Pi 5 Edge ML Traffic Monitoring System. Use these documents to install, configure, deploy, and maintain the system.

## Included Documents

- **docs/User_Guide.md** – End-user guide for system features, dashboard, and troubleshooting
- **docs/Implementation_Deployment.md** – Step-by-step setup, installation, and deployment instructions
- **docs/Automation_Tools.md** – Comprehensive guide to development workflow automation tools
- **docs/Technical_Design.md** – System architecture, hardware design, database schema, and API specifications
- **docs/Project_Management.md** – Project plan, timeline, risk management, and QA
- **docs/References_Appendices.md** – References, glossary, and appendices
- **docs/Documentation_TODO.md** – Living list of outstanding, in-progress, and completed documentation tasks

## Quick Links

- [User Guide](./docs/User_Guide.md) - Start here for end users
- [Implementation & Deployment Guide](./docs/Implementation_Deployment.md) - Complete deployment instructions
- [Automation Tools Guide](./docs/Automation_Tools.md) - Development workflow automation
- [Technical Design Document](./docs/Technical_Design.md) - Architecture and design
- [Project Management Summary](./docs/Project_Management.md) - Project overview
- [References & Appendices](./docs/References_Appendices.md) - Additional resources
- [Documentation TODO List](./docs/Documentation_TODO.md) - Task tracking

## Development Quick Start

```bash
# For new developers - complete setup
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project
bash scripts/deploy-to-pi.sh

# For daily development - intelligent workflow
smart-push -b "feature/new-enhancement"  # Create branch and auto-commit
branch-cleanup                           # Clean up merged branches
```

## Key Features Documented

- **🚀 Automated CI/CD Pipeline** - GitHub Actions with multi-architecture builds
- **🛠️ Intelligent Development Tools** - Smart push, branch cleanup, deployment automation
- **📱 Real-time Monitoring** - Web dashboard with live video and metrics
- **🔧 Edge ML Processing** - AI-powered vehicle detection with radar fusion
- **📊 Comprehensive APIs** - REST and WebSocket for integration

For questions or suggestions, please see the User Guide or contact the project team.
