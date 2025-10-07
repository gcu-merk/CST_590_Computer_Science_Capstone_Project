# Deprecated Scripts Archive

This directory contains scripts that have been deprecated as part of the project cleanup and hardening initiative (October 2025).

## Why These Scripts Were Deprecated

These scripts represent ~80% of the original script collection and were deprecated because:

1. **Replaced by Docker Orchestration**: Container management is now handled by docker-compose
2. **Replaced by Python Services**: Shell scripts converted to more maintainable Python services
3. **Replaced by CI/CD**: Deployment scripts replaced by automated pipelines
4. **One-time Use**: Migration scripts that are no longer needed
5. **Redundant Functionality**: Duplicate or overlapping functionality with active scripts

## Deprecated Categories

### Deployment Scripts (Replaced by CI/CD)
- ✗ Multiple manual deployment scripts replaced by automated docker-compose deployment

### Container Management (Replaced by Docker Compose)
- ✗ Manual container health checks replaced by Docker healthchecks
- ✗ Manual container restart scripts replaced by Docker restart policies

### Monitoring Scripts (Replaced by Python Services)
- `pi_workflow_monitor.sh` - Replaced by system monitoring service
- `pi_workflow_monitor.py` - Integrated into monitoring infrastructure
- `last_detection_analyzer.sh` - Functionality integrated into API
- `last_detection_analyzer_fixed.sh` - Obsolete after API integration

### Development/Testing Scripts
- `camera_free_api.py` - Development testing script
- `simple_detection_check.py` - Replaced by comprehensive health checks
- `radar_service.py` - Duplicate of production service

### Migration Scripts (One-time use)
- `migrate_to_normalized_schema.py` - One-time database migration (already executed)
- `realtime_events_broadcaster.py` - Functionality integrated into main services

## Retention Policy

These scripts are retained for:
- **Historical reference**: Understanding system evolution
- **Recovery**: In case functionality needs to be restored
- **Documentation**: Examples of past approaches

**Retention Period**: 6 months from deprecation date (October 2025 - April 2026)

**After April 2026**: These scripts may be permanently deleted after final review.

## If You Need to Use a Deprecated Script

⚠️ **Warning**: These scripts may not work with current system architecture.

If you believe you need functionality from a deprecated script:

1. **First**: Check if the functionality exists in current services
2. **Document**: Create an issue explaining why it's needed
3. **Modernize**: Port the functionality to current architecture rather than using the old script
4. **Test**: Thoroughly test any restored functionality

## Migration Notes

Scripts were deprecated as part of:
- **Project**: CST_590 Capstone Project Cleanup and Hardening
- **Branch**: feature/project-cleanup-and-hardening
- **Date**: October 7, 2025
- **Reference**: See PROJECT_CLEANUP_AND_HARDENING_EXECUTIVE_SUMMARY.md

## Active Script Locations

Current production scripts are located in:
- `scripts/operations/` - Operational scripts (maintenance, monitoring)
- `scripts/hardware/` - Hardware interface scripts (camera, radar)
- `scripts/system/` - System management scripts
- `deployment/` - Deployment scripts

---

**Last Updated**: October 7, 2025  
**Status**: Deprecated - Retained for reference
