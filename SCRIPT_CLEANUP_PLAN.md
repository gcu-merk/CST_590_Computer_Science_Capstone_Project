# Script Directory Cleanup Plan

Based on Docker best practices analysis, this document outlines which scripts to keep vs remove.

## Scripts to KEEP (Essential - 20%)

### Core Python Services
- `container-maintenance.py` - Core maintenance logic
- `data-maintenance-manager.py` - Data cleanup orchestration
- `host-camera-capture.py` - Camera capture service
- `maintenance-status.py` - Status monitoring
- `process_traffic.py` - Traffic processing logic

### Testing & Validation Scripts
- `test_ai_camera_docker.py` - Docker camera testing
- `test_api_registration.py` - API validation
- `test_imx500_camera.py` - Hardware testing
- `test_picamera2_minimal.py` - Camera minimal tests
- `run_ops243_tests.py` - Radar testing

### Utility Scripts (Convert to Python)
- `image-sync-manager.py` - Keep, already Python
- `imx500_ai_host_capture_enhanced.py` - Keep, core functionality

## Scripts to REMOVE (80% - Now handled by Docker/Python orchestration)

### Deployment Scripts (Replaced by CI/CD)
- `deploy-to-pi.sh`
- `deploy_swagger_api.sh`
- `correct_deployment.sh`
- `emergency_redeploy.sh`
- `fix_deployment.sh`
- `pre-deployment-fixes.sh`
- `simple_swagger_deploy.sh`
- `validate-deployment.sh`
- `verify-pi-setup.sh`

### Container Management (Replaced by Docker Compose)
- `check_container_health.sh`
- `cleanup_docker_deployment.sh`
- `fix_container_conflict.sh`
- `docker_camera_test.sh`
- `restart_api.sh`
- `setup-container-cron.sh`
- `setup-docker-cleanup-cron.sh`

### Maintenance Scripts (Replaced by Python orchestrator)
- `start-with-maintenance.sh` - ✅ Already replaced
- `setup-maintenance-scheduler.sh`
- `verify-maintenance-deployment.sh`
- `disk-space-monitor.sh`
- `storage-optimization-monitor.sh`

### API/Service Management (Handled by containers)
- `check_api_status.sh`
- `debug_api_restart.sh`
- `restart_with_swagger_fixes.sh`
- `safe_api_check.sh`
- `deep_api_check.sh`

### Diagnostic Scripts (Integrated into health checks)
- `compose_diagnosis.sh`
- `diagnose_deployment.sh`
- `diagnose_swagger_issue.py`
- `port_5000_diagnostics.sh`
- `swagger_error_check.sh`

### Setup/Configuration (One-time setup, not needed in containers)
- `camera-init.sh`
- `generate-ssl-cert.sh`
- `setup-hybrid-solution.sh`

### Development Scripts (Move to development folder)
- `branch-cleanup-simple.ps1`
- `branch-cleanup.cmd`
- `branch-cleanup.ps1`
- `git-aliases.ps1`
- `smart-push.cmd`
- `smart-push.ps1`

### Legacy/Duplicate Scripts
- `imx500_ai_host_capture.py` - Replaced by enhanced version
- `quick_swagger_fix.sh`
- `apply_socketio_fix.sh`
- `version_check.sh`

## Migration Actions

1. **Create backup**: Move removed scripts to `scripts/deprecated/` 
2. **Update references**: Remove script references from documentation
3. **Test cleanup**: Validate no dependencies on removed scripts
4. **Final cleanup**: Delete deprecated scripts after validation

Total: Keep ~12 scripts, Remove ~50+ scripts (83% reduction)