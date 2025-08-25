# Automation & Development Tools

**Document Version:** 1.0  
**Last Updated:** August 24, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Development Team  

## Table of Contents

1. [Overview](#1-overview)
2. [Smart Push Tool](#2-smart-push-tool)
3. [Branch Cleanup Tool](#3-branch-cleanup-tool)
4. [CI/CD Pipeline](#4-cicd-pipeline)
5. [Deployment Automation](#5-deployment-automation)
6. [Best Practices](#6-best-practices)
7. [Troubleshooting](#7-troubleshooting)

## 1. Overview

This document describes the comprehensive automation tools developed to streamline the development, testing, and deployment workflow for the traffic monitoring system. These tools provide intelligent Git workflow automation, automated testing, and reliable deployment to Raspberry Pi devices.

### Available Tools

| Tool | Purpose | Location | Usage |
|------|---------|----------|-------|
| **Smart Push** | Intelligent Git commit/push automation | `smart-push.cmd` | `smart-push [options]` |
| **Branch Cleanup** | Automated cleanup of merged branches | `branch-cleanup.cmd` | `branch-cleanup [options]` |
| **Pi Deploy** | Raspberry Pi deployment script | `scripts/deploy-to-pi.sh` | `bash scripts/deploy-to-pi.sh` |
| **Pi Troubleshoot** | Deployment diagnostics | `scripts/pi-troubleshoot.sh` | `bash scripts/pi-troubleshoot.sh` |
| **GitHub Actions** | CI/CD pipeline | `.github/workflows/` | Automatic |

## 2. Smart Push Tool

### 2.1. Overview

The Smart Push tool provides intelligent automation for the Git commit and push workflow, including automatic branch creation, intelligent commit message generation, and conventional commit format compliance.

### 2.2. Key Features

#### Automatic Branch Creation

When working on `main` or `master`, the tool automatically creates feature branches:

```bash
# Current branch: main
smart-push

# Result: Creates branch like "docs-api-updates-0824" and switches to it
```

#### Intelligent Commit Message Generation

Analyzes file changes to suggest appropriate commit messages:

| File Pattern | Commit Type | Example Message |
|--------------|-------------|-----------------|
| `*.md`, `docs/` | `docs` | `docs: update API documentation` |
| `test_*.py` | `test` | `test: add camera integration tests` |
| `src/*.py` | `feat` | `feat: implement speed detection` |
| `requirements.txt` | `deps` | `deps: update opencv dependencies` |
| `Dockerfile` | `ci` | `ci: update container configuration` |
| `*.js`, `*.ts` | `feat` | `feat: add dashboard components` |

#### Conventional Commit Format

Automatically generates messages following the conventional commit specification:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 2.3. Usage Examples

#### Basic Usage

```bash
# Auto-commit and push with intelligent message
smart-push

# Example output:
# Creating auto-generated branch: feat-camera-integration-0824
# Auto-generated commit message: feat: implement camera module support
# Would you like to use this message? (Y/n/e to edit): Y
```

#### Advanced Options

```bash
# Create custom branch name
smart-push -b "feature/radar-sensor"

# Use custom commit message
smart-push -m "feat: add radar sensor calibration"

# Preview without executing
smart-push -dry

# Stage all changes first
smart-push -all

# Interactive commit message creation
smart-push -interactive
```

#### Workflow Integration

```bash
# Typical development workflow
smart-push -b "feature/new-api"     # Start feature
# ... make changes ...
smart-push                          # Commit with auto-message
# ... more changes ...
smart-push -m "fix: handle edge case" # Custom message
# ... create PR and merge ...
branch-cleanup                      # Clean up merged branches
```

### 2.4. Configuration

The tool can be customized through command-line parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-dry` | Preview actions without executing | `smart-push -dry` |
| `-all` | Stage all changes before committing | `smart-push -all` |
| `-branch` / `-b` | Custom branch name | `smart-push -b "feature/api"` |
| `-message` / `-m` | Custom commit message | `smart-push -m "fix: bug"` |
| `-force` | Force push with lease | `smart-push -force` |
| `-interactive` | Interactive message creation | `smart-push -interactive` |

## 3. Branch Cleanup Tool

### 3.1. Overview

The Branch Cleanup tool automates the removal of Git branches that have been merged into the main branch, keeping the repository clean and organized.

### 3.2. Features

#### Safe Branch Detection

- Identifies branches merged into `main`
- Distinguishes between local and remote branches
- Excludes protected branches (`main`, `master`, `develop`)

#### Interactive Confirmation

- Shows which branches will be deleted
- Asks for confirmation before deletion
- Provides detailed status reports

#### Remote Synchronization

- Removes local merged branches
- Removes remote merged branches
- Prunes stale remote tracking references

### 3.3. Usage Examples

#### Basic Cleanup

```bash
# Interactive cleanup with confirmation
branch-cleanup

# Example output:
# Current branch: main
# Updating main branch...
# 
# Local branches merged into main:
#   - feature/camera-integration
#   - fix/sensor-calibration
# 
# Remote branches merged into main:
#   - origin/feature/camera-integration
#   - origin/fix/sensor-calibration
# 
# Do you want to proceed with cleanup? (y/N): y
```

#### Advanced Options

```bash
# Preview cleanup without executing
branch-cleanup -dry

# Force cleanup without confirmation (use with caution)
branch-cleanup -force

# Clean up only local branches
branch-cleanup -local

# Clean up only remote branches
branch-cleanup -remote
```

### 3.4. Safety Features

- **Branch Protection**: Never deletes `main`, `master`, or `develop`
- **Current Branch Check**: Switches to `main` if on a branch to be deleted
- **Confirmation Prompts**: Always asks before destructive operations
- **Status Reporting**: Shows before/after repository state

## 4. CI/CD Pipeline

### 4.1. Pipeline Overview

The CI/CD pipeline consists of two GitHub Actions workflows:

```text
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD PIPELINE                          │
└─────────────────────────────────────────────────────────────────┘

Feature Branch Push
       │
       ▼
┌─────────────────────┐
│  Build & Test       │  ◄─── docker-build-push.yml
│  - Build Docker     │
│  - Push to Hub      │
│  - Run Tests        │
└─────────────────────┘
       │
       │ merge to main
       ▼
┌─────────────────────┐
│  Deploy to Pi       │  ◄─── deploy-to-pi.yml
│  - Pull Image       │
│  - Update Container │
│  - Health Check     │
└─────────────────────┘
```

### 4.2. Build Workflow (`docker-build-push.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Actions:**
1. Checkout code
2. Set up Docker Buildx
3. Login to Docker Hub
4. Build ARM64 image for Raspberry Pi
5. Push to `gcumerk/cst590-capstone:latest`

### 4.3. Deploy Workflow (`deploy-to-pi.yml`)

**Triggers:**
- Successful completion of build workflow on `main` branch

**Actions:**
1. Verify deployment environment
2. Setup deployment directory
3. Stop existing containers
4. Pull latest Docker image
5. Deploy new containers
6. Install Pi-specific packages
7. Verify deployment health
8. Cleanup resources

### 4.4. Monitoring

#### GitHub Actions Dashboard

Monitor workflow runs in your repository's Actions tab:
- Build status and logs
- Deployment success/failure
- Error details and diagnostics

#### Docker Hub Integration

Track image builds and deployments:
- Image push timestamps
- Download statistics
- Tag management

## 5. Deployment Automation

### 5.1. Raspberry Pi Deployment

#### Automated GitHub Actions Deployment

Fully automated deployment triggered by main branch updates:

```yaml
# Automatic deployment on main branch
on:
  workflow_run:
    workflows: ["Build and Push Docker Image"]
    types: [completed]
```

#### Manual Script Deployment

For testing and troubleshooting:

```bash
# Full deployment script
bash scripts/deploy-to-pi.sh

# With options
bash scripts/deploy-to-pi.sh --dry-run        # Preview only
bash scripts/deploy-to-pi.sh --skip-verification  # Skip checks
```

#### Direct Docker Deployment

Minimal deployment for quick testing:

```bash
# Quick Docker Compose deployment
mkdir -p ~/traffic-monitor-deploy
cd ~/traffic-monitor-deploy
wget https://raw.githubusercontent.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/main/docker-compose.yml
docker-compose up -d
```

### 5.2. Deployment Architecture

```text
Development Machine          GitHub Actions           Raspberry Pi
┌─────────────────┐         ┌─────────────────┐      ┌─────────────────┐
│                 │         │                 │      │                 │
│  smart-push     │────────▶│  Build Pipeline │─────▶│  Deploy Script  │
│  branch-cleanup │         │                 │      │                 │
│                 │         │  ┌─────────────┐│      │  ┌─────────────┐│
│  Local Dev      │         │  │Docker Build ││      │  │   Container │││
│  Environment    │         │  │& Push       ││      │  │   Update    │││
│                 │         │  └─────────────┘│      │  └─────────────┘│
│                 │         │                 │      │                 │
└─────────────────┘         └─────────────────┘      └─────────────────┘
        │                                                       │
        └─────────────────────────────────────────────────────┘
                        Troubleshooting & Monitoring
```

### 5.3. Health Monitoring

#### Automated Health Checks

The deployment pipeline includes comprehensive health verification:

```bash
# API endpoint testing
curl -f http://localhost:5000/api/health

# Container status verification
docker-compose ps

# Log analysis
docker-compose logs --tail 20 traffic-monitor
```

#### Troubleshooting Tools

```bash
# Comprehensive diagnostics
bash scripts/pi-troubleshoot.sh

# Quick health check
curl http://localhost:5000/api/health

# Container inspection
docker inspect traffic-monitoring-edge
```

## 6. Best Practices

### 6.1. Development Workflow

#### Recommended Development Cycle

1. **Start Feature Development**
   ```bash
   smart-push -b "feature/descriptive-name"
   ```

2. **Iterative Development**
   ```bash
   # Make changes
   smart-push  # Auto-commit with intelligent message
   ```

3. **Create Pull Request**
   - Use GitHub web interface
   - Ensure CI passes
   - Request code review

4. **Post-Merge Cleanup**
   ```bash
   branch-cleanup  # Remove merged branches
   ```

#### Branch Naming Conventions

- **Features**: `feature/component-description`
- **Bug Fixes**: `fix/issue-description`
- **Documentation**: `docs/section-update`
- **CI/CD**: `ci/pipeline-improvement`

#### Commit Message Guidelines

Follow conventional commit format:
- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation updates
- **test**: Test additions/modifications
- **refactor**: Code refactoring
- **ci**: CI/CD changes
- **deps**: Dependency updates

### 6.2. Deployment Best Practices

#### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Docker image builds successfully
- [ ] No security vulnerabilities

#### Post-Deployment Verification

```bash
# Health check
curl http://localhost:5000/api/health

# Container status
docker-compose ps

# Recent logs
docker-compose logs --tail 50 traffic-monitor

# Resource usage
docker stats --no-stream
```

### 6.3. Maintenance Recommendations

#### Regular Maintenance Tasks

1. **Weekly**
   - Review and merge feature branches
   - Run branch cleanup
   - Monitor deployment health

2. **Monthly**
   - Update dependencies
   - Review Docker image sizes
   - Clean up old Docker resources

3. **Quarterly**
   - Security audit
   - Performance optimization
   - Documentation review

## 7. Troubleshooting

### 7.1. Common Issues

#### Smart Push Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Not in docker group | `sudo usermod -aG docker $USER` |
| Branch creation fails | Git not configured | `git config --global user.name "Name"` |
| Commit message rejected | Invalid format | Use `-m` flag with proper format |

#### Branch Cleanup Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't delete branch | Branch not merged | Verify merge status with `git branch --merged` |
| Remote deletion fails | No permissions | Check repository access rights |

#### Deployment Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Container won't start | Image pull failed | Check Docker Hub connectivity |
| API not responding | Port conflict | Check port 5000 availability |
| Hardware access denied | Device permissions | Verify device mount points |

### 7.2. Diagnostic Commands

#### Git Workflow Diagnostics

```bash
# Check Git status
git status
git branch -a
git log --oneline -10

# Check remote configuration
git remote -v
git fetch --all
```

#### Deployment Diagnostics

```bash
# Full system diagnostics
bash scripts/pi-troubleshoot.sh

# Docker diagnostics
docker info
docker-compose ps
docker-compose logs traffic-monitor

# Network diagnostics
netstat -tlnp | grep 5000
curl -v http://localhost:5000/api/health
```

#### Resource Monitoring

```bash
# System resources
htop
df -h
free -h

# Docker resources
docker stats
docker system df
docker images
```

### 7.3. Getting Help

#### Log Locations

- **Application Logs**: `~/traffic-monitor-deploy/logs/`
- **Container Logs**: `docker-compose logs traffic-monitor`
- **System Logs**: `/var/log/syslog`

#### Support Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides in `documentation/docs/`
- **Troubleshooting Scripts**: Automated diagnostics tools

#### Emergency Recovery

```bash
# Complete system reset
cd ~/traffic-monitor-deploy
docker-compose down
docker system prune -f
bash scripts/deploy-to-pi.sh
```

For additional support, refer to the main project documentation and create GitHub issues for specific problems.
