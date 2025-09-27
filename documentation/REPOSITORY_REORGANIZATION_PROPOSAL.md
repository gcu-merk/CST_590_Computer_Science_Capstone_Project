# Repository Reorganization Proposal

**Document Version:** 1.0  
**Date:** September 27, 2025  
**Author:** System Architecture Team  
**Status:** Proposal - Pending Approval  

## Executive Summary

This document outlines a comprehensive proposal to reorganize the CST 590 Capstone Project repository structure to align with modern software engineering best practices. The current repository has grown organically, resulting in scattered files, inconsistent organization, and maintenance challenges. This proposal provides a structured approach to improve code organization, maintainability, and scalability.

## Table of Contents

- [Current State Analysis](#current-state-analysis)
- [Proposed Structure](#proposed-structure)
- [Detailed Migration Plan](#detailed-migration-plan)
- [Benefits Analysis](#benefits-analysis)
- [Risk Assessment](#risk-assessment)
- [Implementation Strategy](#implementation-strategy)
- [Success Metrics](#success-metrics)
- [Appendices](#appendices)

## Current State Analysis

### Existing Repository Structure Issues

The current repository structure exhibits several organizational challenges:

#### 1. **Root Directory Sprawl**
- **Configuration Files**: Mixed at root level with varying formats
- **Documentation**: Scattered `.md` files alongside `documentation/` folder
- **Docker Files**: Multiple `Dockerfile.*` variants without clear organization
- **Deployment Scripts**: Mixed with configuration and source files
- **Service Files**: System service definitions intermixed with application code

#### 2. **Inconsistent Naming Conventions**
- **snake_case**: `camera_free_api.py`, `radar_service.py`
- **kebab-case**: `docker-compose.yml`, `deploy-services.sh`
- **PascalCase**: `API_GATEWAY_DEPLOYMENT_GUIDE.md`
- **Mixed Formats**: Inconsistent file naming across similar file types

#### 3. **Source Code Distribution**
- **API Code**: Concentrated in `edge_api/` but with spillover to root
- **Services**: Core services scattered between directories
- **Processing Logic**: Mixed between `edge_processing/` and standalone files
- **UI Components**: Distributed across `edge-ui/`, `mobile/`, `website/`

#### 4. **Configuration Management Challenges**
- **Docker Configurations**: Multiple compose files at root level
- **Service Configurations**: Split between `config/` and deployment files
- **Environment Settings**: JSON files scattered throughout project
- **Nginx Configurations**: Multiple versions without version control

#### 5. **Testing Infrastructure Gaps**
- **Test Location**: Tests buried in `scripts/development/`
- **Test Organization**: No clear separation of unit, integration, and e2e tests
- **Test Data**: Fixtures and sample data not clearly organized

## Proposed Structure

### Target Directory Layout

```
CST_590_Computer_Science_Capstone_Project/
├── src/                                    # Source Code Repository
│   ├── api/                               # API Services Layer
│   │   ├── edge_gateway/                  # Main API gateway
│   │   ├── data_access/                   # Data access APIs
│   │   ├── weather/                       # Weather service APIs
│   │   └── models/                        # Shared API models
│   ├── services/                          # Core Business Services
│   │   ├── camera/                        # Camera capture services
│   │   ├── radar/                         # Radar detection services
│   │   ├── weather/                       # Weather monitoring
│   │   ├── storage/                       # Data persistence
│   │   └── messaging/                     # Event broadcasting
│   ├── ui/                                # User Interface Applications
│   │   ├── web/                          # Web dashboard
│   │   ├── mobile/                       # Mobile applications
│   │   └── edge/                         # Edge device interfaces
│   ├── processing/                        # Data Processing Modules
│   │   ├── image/                        # Image processing pipelines
│   │   ├── analytics/                    # Data analytics
│   │   └── ml/                           # Machine learning models
│   └── shared/                            # Common Utilities
│       ├── utils/                        # Utility functions
│       ├── models/                       # Shared data models
│       └── config/                       # Configuration management
├── config/                                # Configuration Management
│   ├── docker/                           # Container Configurations
│   │   ├── images/                       # Dockerfile collection
│   │   │   ├── api.Dockerfile
│   │   │   ├── services.Dockerfile
│   │   │   └── processing.Dockerfile
│   │   └── compose/                      # Docker Compose files
│   │       ├── development.yml
│   │       ├── production.yml
│   │       └── testing.yml
│   ├── nginx/                            # Web Server Configuration
│   │   ├── production.conf
│   │   ├── development.conf
│   │   └── ssl/                          # SSL certificates
│   ├── services/                         # System Service Definitions
│   │   ├── camera-capture.service
│   │   ├── radar-monitoring.service
│   │   └── data-persistence.service
│   └── environments/                     # Environment-Specific Settings
│       ├── production.json
│       ├── development.json
│       └── testing.json
├── deployment/                            # Deployment & Infrastructure
│   ├── docker-compose/                   # Orchestration Files (deprecated - moved to config/)
│   ├── scripts/                          # Deployment Automation
│   │   ├── deploy.sh
│   │   ├── rollback.sh
│   │   └── health-check.sh
│   ├── kubernetes/                       # Future: K8s Manifests
│   │   ├── manifests/
│   │   └── helm/
│   └── terraform/                        # Future: Infrastructure as Code
│       ├── aws/
│       └── local/
├── docs/                                 # Documentation Repository
│   ├── api/                              # API Documentation
│   │   ├── endpoints.md
│   │   ├── authentication.md
│   │   └── swagger/
│   ├── deployment/                       # Deployment Guides
│   │   ├── production-deployment.md
│   │   ├── development-setup.md
│   │   └── troubleshooting.md
│   ├── architecture/                     # System Design
│   │   ├── system-overview.md
│   │   ├── data-flow.md
│   │   └── security-model.md
│   ├── user/                             # User Documentation
│   │   ├── user-guide.md
│   │   ├── dashboard-guide.md
│   │   └── mobile-app-guide.md
│   └── development/                      # Developer Documentation
│       ├── contributing.md
│       ├── coding-standards.md
│       └── testing-guidelines.md
├── tests/                                # Testing Infrastructure
│   ├── unit/                            # Unit Tests
│   │   ├── api/
│   │   ├── services/
│   │   └── processing/
│   ├── integration/                      # Integration Tests
│   │   ├── api-integration/
│   │   ├── service-integration/
│   │   └── database-integration/
│   ├── e2e/                             # End-to-End Tests
│   │   ├── user-workflows/
│   │   ├── system-scenarios/
│   │   └── performance/
│   └── fixtures/                         # Test Data & Fixtures
│       ├── sample-data/
│       ├── mock-responses/
│       └── test-configs/
├── tools/                                # Development & Utility Tools
│   ├── migration/                        # Database Migration Scripts
│   │   ├── schema-migrations/
│   │   └── data-migrations/
│   ├── monitoring/                       # Monitoring & Alerting
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   └── alerts/
│   ├── maintenance/                      # Maintenance Utilities
│   │   ├── cleanup-scripts/
│   │   ├── backup-scripts/
│   │   └── health-checks/
│   └── development/                      # Development Tools
│       ├── code-generators/
│       ├── linters/
│       └── formatters/
├── data/                                 # Data Storage & Samples
│   ├── samples/                          # Sample Data Sets
│   │   ├── camera-images/
│   │   ├── radar-data/
│   │   └── weather-data/
│   ├── fixtures/                         # Test Fixtures
│   │   ├── unit-test-data/
│   │   └── integration-test-data/
│   └── templates/                        # Configuration Templates
│       ├── docker-templates/
│       └── service-templates/
├── scripts/                              # Utility Scripts (Current)
│   ├── hardware/                         # Hardware interaction scripts
│   ├── operations/                       # Operational scripts
│   ├── system/                           # System configuration
│   ├── development/                      # Development utilities
│   └── archive/                          # Legacy scripts
├── .github/                              # GitHub Workflows & Templates
│   ├── workflows/                        # CI/CD Pipelines
│   ├── ISSUE_TEMPLATE/                   # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md          # PR template
├── .gitignore                            # Git ignore rules
├── README.md                             # Project overview
├── LICENSE                               # Project license
├── requirements.txt                      # Main dependencies
├── setup.py                              # Project installation
└── CHANGELOG.md                          # Version history
```

## Detailed Migration Plan

### Phase 1: Documentation & Configuration (Low Risk)

#### Duration: 1-2 days
#### Risk Level: Low

**Objectives:**
- Consolidate scattered documentation
- Organize configuration files
- No impact on running services

**Actions:**

1. **Documentation Migration**
   ```bash
   # Create new docs structure
   mkdir -p docs/{api,deployment,architecture,user,development}
   
   # Move existing documentation
   mv API_GATEWAY_DEPLOYMENT_GUIDE.md docs/deployment/
   mv CAMERA_SERVICE_DEPLOYMENT_GUIDE.md docs/deployment/
   mv CONTAINERIZATION_GUIDE.md docs/deployment/
   mv DEPLOYMENT_NOTES.md docs/deployment/
   mv DHT22_ARCHITECTURE_EVOLUTION.md docs/architecture/
   mv DOCKER_BEST_PRACTICES*.md docs/development/
   mv IMX500_*.md docs/architecture/
   mv LOGGING_*.md docs/development/
   mv MOTION_DETECTION_STRATEGY.md docs/architecture/
   mv PI5_CAMERA_DOCKER_GUIDE.md docs/deployment/
   mv QUICK_LOGGING_REFERENCE.md docs/development/
   mv RADAR_SERVICE_CHANGELOG.md docs/development/
   mv SCRIPT_CLEANUP_PLAN.md docs/development/
   mv SERVICE_STANDARDIZATION_SUMMARY.md docs/development/
   mv WEATHER_SERVICES_DEPLOYMENT_GUIDE.md docs/deployment/
   ```

2. **Configuration Organization**
   ```bash
   # Create config structure
   mkdir -p config/{docker/{images,compose},nginx,services,environments}
   
   # Move Docker configurations
   mv Dockerfile* config/docker/images/
   mv docker-compose*.yml config/docker/compose/
   
   # Move nginx configurations
   mv nginx*.conf config/nginx/
   mv nginx/ config/nginx/legacy/
   
   # Move service files
   mv *.service config/services/
   
   # Move environment configurations
   mv *roi*.json config/environments/
   mv centralized_logging_validation_report.json config/environments/
   mv sqlite_database_services_validation_results.json config/environments/
   ```

### Phase 2: Non-Critical Source Code (Medium Risk)

#### Duration: 2-3 days
#### Risk Level: Medium

**Objectives:**
- Move standalone utility scripts
- Organize UI components
- Minimal service disruption

**Actions:**

1. **Create Source Structure**
   ```bash
   mkdir -p src/{api,services,ui,processing,shared}
   mkdir -p src/ui/{web,mobile,edge}
   mkdir -p src/services/{camera,radar,weather,storage,messaging}
   mkdir -p src/shared/{utils,models,config}
   ```

2. **Move UI Components**
   ```bash
   mv edge-ui/ src/ui/edge/
   mv mobile/ src/ui/mobile/
   mv website/ src/ui/web/
   mv webserver/ src/ui/web/server/
   ```

3. **Move Processing Modules**
   ```bash
   mv edge_processing/ src/processing/
   ```

### Phase 3: Core Services & APIs (High Risk)

#### Duration: 3-5 days
#### Risk Level: High

**Objectives:**
- Move critical service code
- Update all import statements
- Ensure service continuity

**Actions:**

1. **Move API Services**
   ```bash
   mv edge_api/ src/api/edge_gateway/
   ```

2. **Move Core Services**
   ```bash
   mv radar_service.py src/services/radar/
   mv camera_free_api.py src/services/camera/
   mv realtime_events_broadcaster.py src/services/messaging/
   mv docker_entrypoint.py src/services/
   ```

3. **Update Import Statements**
   - Scan all Python files for import statements
   - Update relative and absolute imports
   - Update Docker build contexts
   - Update systemd service file paths

### Phase 4: Testing Infrastructure (Medium Risk)

#### Duration: 2-3 days
#### Risk Level: Medium

**Objectives:**
- Establish proper testing structure
- Move existing tests
- Create test organization

**Actions:**

1. **Create Testing Structure**
   ```bash
   mkdir -p tests/{unit,integration,e2e,fixtures}
   mkdir -p tests/unit/{api,services,processing}
   mkdir -p tests/integration/{api-integration,service-integration,database-integration}
   mkdir -p tests/e2e/{user-workflows,system-scenarios,performance}
   ```

2. **Move Existing Tests**
   ```bash
   # Move tests from scripts/development/
   find scripts/development/ -name "test_*.py" -exec mv {} tests/unit/ \;
   find scripts/development/ -name "*test*.sh" -exec mv {} tests/integration/ \;
   ```

### Phase 5: Deployment & Tools (High Risk)

#### Duration: 2-4 days
#### Risk Level: High

**Objectives:**
- Organize deployment scripts
- Update deployment automation
- Ensure deployment continuity

**Actions:**

1. **Move Deployment Scripts**
   ```bash
   mkdir -p deployment/scripts
   mv deploy*.sh deployment/scripts/
   mv deployment/ deployment/legacy/
   ```

2. **Create Tools Structure**
   ```bash
   mkdir -p tools/{migration,monitoring,maintenance,development}
   mv grafana/ tools/monitoring/
   ```

## Benefits Analysis

### 1. **Improved Code Organization**

**Current State Issues:**
- Developers struggle to locate related files
- Similar functionality scattered across directories
- No clear separation between production and development code

**Proposed Benefits:**
- **Clear Separation of Concerns**: Source code, configuration, documentation, and tests in dedicated directories
- **Logical Grouping**: Related functionality grouped together (API services, UI components, etc.)
- **Scalability**: Structure supports growth from monolith to microservices architecture

**Quantifiable Improvements:**
- **Reduced File Search Time**: Estimated 40% reduction in time to locate specific files
- **Faster Onboarding**: New developers can understand structure in 30 minutes vs. 2+ hours currently
- **Code Navigation**: IDE navigation improvements with logical folder structure

### 2. **Enhanced Development Workflow**

**Current Challenges:**
- Unclear where to place new files
- Difficulty setting up development environment
- Inconsistent testing practices

**Proposed Solutions:**
- **Clear Conventions**: Defined locations for different types of files
- **Standardized Structure**: Follows industry best practices familiar to developers
- **Improved Tooling**: Better IDE support and automated tooling integration

**Developer Experience Improvements:**
- **Reduced Decision Fatigue**: Clear guidelines on file placement
- **Faster Feature Development**: Logical structure reduces cognitive overhead
- **Better Code Reviews**: Clearer file organization improves review efficiency

### 3. **Superior Deployment Management**

**Current Deployment Issues:**
- Configuration files scattered across project
- Multiple Docker compose files without clear purpose
- Deployment scripts mixed with source code

**Proposed Improvements:**
- **Centralized Configuration**: All deployment configs in dedicated directory
- **Environment Separation**: Clear distinction between dev, test, and production
- **Infrastructure as Code**: Foundation for advanced deployment practices

**Operational Benefits:**
- **Reduced Deployment Errors**: Organized configurations reduce mistakes
- **Faster Troubleshooting**: Clear separation makes issue diagnosis easier
- **Better Disaster Recovery**: Organized backups and recovery procedures

### 4. **Improved Testing Practices**

**Current Testing Limitations:**
- Tests buried in scripts directory
- No clear distinction between test types
- Test data mixed with production code

**Proposed Testing Structure:**
- **Dedicated Test Directory**: All tests in logical hierarchy
- **Test Type Separation**: Unit, integration, and e2e tests clearly separated
- **Fixture Management**: Test data and fixtures properly organized

**Quality Improvements:**
- **Increased Test Coverage**: Easier to identify untested areas
- **Faster Test Execution**: Better test organization enables selective test runs
- **Improved Test Maintenance**: Clear structure makes test updates easier

## Risk Assessment

### High-Risk Areas

#### 1. **Service Disruption**

**Risk Level:** High  
**Impact:** Critical system downtime  
**Probability:** Medium  

**Description:**
Moving core service files (`radar_service.py`, `camera_free_api.py`) could break active deployments if import paths or service configurations are not properly updated.

**Mitigation Strategies:**
- **Phased Migration**: Move non-critical files first
- **Symlink Strategy**: Create temporary symlinks during transition
- **Rollback Plan**: Maintain ability to quickly revert changes
- **Testing Environment**: Validate all changes in test environment first

**Contingency Plan:**
```bash
# Emergency rollback procedure
git checkout HEAD~1  # Revert to previous commit
systemctl restart all-services  # Restart all services
./deployment/scripts/health-check.sh  # Verify system health
```

#### 2. **Import Statement Failures**

**Risk Level:** High  
**Impact:** Application crashes and errors  
**Probability:** High  

**Description:**
Python import statements throughout the codebase reference current file locations. Moving files will break these imports.

**Mitigation Strategies:**
- **Comprehensive Search**: Use automated tools to find all import statements
- **Gradual Migration**: Update imports in small batches
- **Import Testing**: Automated testing of all import statements
- **IDE Refactoring**: Use IDE refactoring tools where possible

**Detection and Remediation:**
```python
# Automated import detection script
import ast
import os

def find_imports(directory):
    """Find all import statements in Python files"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                # Parse and analyze imports
                pass
```

#### 3. **Docker Build Context Issues**

**Risk Level:** Medium  
**Impact:** Failed container builds  
**Probability:** Medium  

**Description:**
Moving Dockerfiles and changing directory structure will affect Docker build contexts and COPY/ADD commands in Dockerfiles.

**Mitigation Strategies:**
- **Build Context Review**: Audit all Dockerfile COPY/ADD commands
- **Multi-Stage Build Updates**: Update multi-stage build references
- **Volume Mount Updates**: Update docker-compose volume mappings
- **Registry Testing**: Test container builds in isolated environment

**Validation Process:**
```bash
# Docker build validation
for dockerfile in config/docker/images/*.Dockerfile; do
    docker build -f $dockerfile -t test-build .
    if [ $? -eq 0 ]; then
        echo "$dockerfile: BUILD SUCCESS"
    else
        echo "$dockerfile: BUILD FAILED"
    fi
done
```

### Medium-Risk Areas

#### 1. **Configuration Path Updates**

**Risk Level:** Medium  
**Impact:** Service configuration failures  
**Probability:** Low  

**Description:**
Hardcoded paths in configuration files may reference old file locations.

**Mitigation:**
- Automated scanning for hardcoded paths
- Configuration validation scripts
- Gradual configuration updates with testing

#### 2. **CI/CD Pipeline Disruption**

**Risk Level:** Medium  
**Impact:** Broken automation pipelines  
**Probability:** Medium  

**Description:**
GitHub Actions and other CI/CD pipelines may reference specific file paths that will change.

**Mitigation:**
- Update .github/workflows/ files
- Test pipeline changes in feature branches
- Gradual pipeline migration

### Low-Risk Areas

#### 1. **Documentation Links**

**Risk Level:** Low  
**Impact:** Broken internal documentation links  
**Probability:** High  

**Description:**
Internal documentation links will break when files are moved.

**Mitigation:**
- Automated link checking
- Systematic documentation updates
- Redirect strategies for external links

## Implementation Strategy

### Pre-Implementation Phase

#### 1. **Stakeholder Alignment**
- **Development Team Review**: Present proposal to development team
- **Operations Team Approval**: Ensure operations team understands changes
- **Timeline Coordination**: Align with deployment schedules and deadlines

#### 2. **Environment Preparation**
- **Backup Strategy**: Full repository backup before starting
- **Test Environment**: Set up isolated test environment for validation
- **Rollback Procedures**: Document and test rollback procedures

#### 3. **Automated Tooling**
```python
# Migration utility script
class RepositoryMigrator:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.migration_log = []
    
    def scan_imports(self):
        """Scan all Python files for import statements"""
        pass
    
    def update_imports(self, old_path, new_path):
        """Update import statements across codebase"""
        pass
    
    def validate_moves(self):
        """Validate that file moves don't break functionality"""
        pass
    
    def create_migration_plan(self):
        """Generate detailed migration plan"""
        pass
```

### Implementation Phases

#### Phase 1: Foundation Setup (Days 1-2)
- Create new directory structure
- Move documentation files
- Update documentation internal links
- No service impact

#### Phase 2: Configuration Organization (Days 3-4)
- Move configuration files to config/ directory
- Update docker-compose file references
- Test configuration loading
- Minimal service impact

#### Phase 3: Source Code Migration (Days 5-9)
- Move source code to src/ directory
- Update import statements systematically
- Update Docker build contexts
- High coordination required

#### Phase 4: Testing & Validation (Days 10-12)
- Move and organize test files
- Update test imports and references
- Validate entire test suite
- Performance and functionality testing

#### Phase 5: Deployment Updates (Days 13-15)
- Update deployment scripts
- Modify CI/CD pipelines
- Update service file paths
- Full system integration testing

### Post-Implementation Phase

#### 1. **Validation and Testing**
- **Comprehensive Testing**: Run full test suite
- **Performance Validation**: Ensure no performance degradation
- **Security Review**: Verify security configurations remain intact
- **Documentation Updates**: Update all references to new structure

#### 2. **Team Training and Onboarding**
- **Developer Training**: Train team on new structure
- **Documentation Updates**: Update development guidelines
- **Best Practice Guidelines**: Establish conventions for new structure

#### 3. **Monitoring and Optimization**
- **Performance Monitoring**: Watch for any issues in production
- **Developer Feedback**: Collect feedback on new structure
- **Continuous Improvement**: Refine structure based on usage patterns

## Success Metrics

### Technical Metrics

#### 1. **Code Organization Metrics**
- **File Location Time**: Time to locate specific files (Target: <30 seconds)
- **Import Statement Errors**: Zero broken imports after migration
- **Build Success Rate**: 100% successful Docker builds
- **Test Suite Pass Rate**: 100% test pass rate post-migration

#### 2. **Development Efficiency Metrics**
- **Onboarding Time**: New developer setup time (Target: <2 hours)
- **Feature Development Time**: Time to implement new features
- **Code Review Time**: Time to conduct thorough code reviews
- **Deployment Frequency**: Maintain or improve deployment frequency

#### 3. **Operational Metrics**
- **Deployment Success Rate**: Maintain 99%+ deployment success
- **System Uptime**: Zero downtime during migration
- **Configuration Error Rate**: Reduce configuration-related errors by 50%
- **Recovery Time**: Faster system recovery from issues

### Qualitative Metrics

#### 1. **Developer Experience**
- **Developer Satisfaction**: Survey-based satisfaction scores
- **Code Navigation Ease**: Subjective ease of finding and editing code
- **New Feature Implementation**: Clarity of where to place new features
- **Documentation Usability**: Ease of finding relevant documentation

#### 2. **Maintainability**
- **Code Comprehension**: Ease of understanding system architecture
- **Bug Fix Efficiency**: Speed of identifying and fixing issues
- **Refactoring Confidence**: Confidence in making structural changes
- **Technical Debt Reduction**: Overall reduction in technical debt

### Measurement Timeline

- **Baseline Measurement**: Before migration starts
- **Phase Completion**: After each migration phase
- **30-Day Post-Migration**: Comprehensive assessment
- **90-Day Review**: Long-term impact evaluation

## Appendices

### Appendix A: File Inventory

#### Current Root Directory Files (Selected)
```
Configuration Files:
- docker-compose.yml (Main orchestration)
- docker-compose.https.yml (HTTPS configuration)
- docker-compose.logging.yml (Logging setup)
- docker-compose.pi.yml (Raspberry Pi specific)
- docker-compose.quick-api.yml (Quick API testing)
- docker-compose.services.yml (Service definitions)

Dockerfile Variants:
- Dockerfile (Base image)
- Dockerfile.api (API service)
- Dockerfile.best-practices (Best practices implementation)
- Dockerfile.consolidator (Data consolidation)
- Dockerfile.maintenance-additions (Maintenance features)
- Dockerfile.persistence (Data persistence)
- Dockerfile.redis_optimization (Redis optimization)

Service Files:
- imx500-ai-capture.service (AI capture service)
- radar-service.service (Radar monitoring service)

Core Services:
- camera_free_api.py (Camera API service)
- radar_service.py (Main radar service)
- realtime_events_broadcaster.py (Event broadcasting)
- docker_entrypoint.py (Container entry point)

Configuration Data:
- custom_red_area_roi_config.json
- expanded_left_roi.json
- expanded_roi_config.json
- new_location_roi_config.json
- optimized_roi_config.json
- precise_red_area_roi.json
- updated_roi_config.json

Nginx Configurations:
- nginx_dual_config.conf
- nginx_fixed.conf
- nginx_funnel_config.conf
- nginx_funnel_final.conf
- nginx_original_working.conf
- nginx_websocket.conf

Deployment Scripts:
- deploy.sh (Main deployment)
- deploy-https.sh (HTTPS deployment)
- deploy-services.sh (Service deployment)

Documentation:
- API_ENDPOINTS_WITH_LINKS.html
- API_GATEWAY_DEPLOYMENT_GUIDE.md
- CAMERA_SERVICE_DEPLOYMENT_GUIDE.md
- CONTAINERIZATION_GUIDE.md
- DEPLOYMENT_NOTES.md
- DHT22_ARCHITECTURE_EVOLUTION.md
- DOCKER_BEST_PRACTICES.md
- DOCKER_BEST_PRACTICES_IMPLEMENTATION_SUMMARY.md
- DOCKER_BUILD_TRIGGER.md
- IMX500_DEPLOYMENT_CHECKLIST.md
- IMX500_IMPLEMENTATION_SUMMARY.md
- IMX500_RADAR_INTEGRATION_GUIDE.md
- LOGGING_AND_DEBUGGING_GUIDE.md
- LOGGING_ERROR_FIXES.md
- MOTION_DETECTION_STRATEGY.md
- PI5_CAMERA_DOCKER_GUIDE.md
- QUICK_LOGGING_REFERENCE.md
- RADAR_SERVICE_CHANGELOG.md
- SCRIPT_CLEANUP_PLAN.md
- SERVICE_STANDARDIZATION_SUMMARY.md
- WEATHER_SERVICES_DEPLOYMENT_GUIDE.md

Data and Reports:
- centralized_logging_validation_report.json
- LOG_ANALYSIS_REPORT_2025-09-27.json
- LOG_ANALYSIS_REPORT_2025-09-27.md
- LOG_ANALYSIS_REPORT_2025-09-27.txt
- sqlite_database_services_validation_results.json
```

### Appendix B: Import Statement Patterns

#### Common Import Patterns to Update
```python
# Current patterns that will break:
from edge_api import *
import radar_service
from camera_free_api import CameraAPI
import docker_entrypoint

# Updated patterns after migration:
from src.api.edge_gateway import *
from src.services.radar import radar_service
from src.services.camera import CameraAPI
from src.services import docker_entrypoint
```

### Appendix C: Docker Build Context Updates

#### Dockerfile Changes Required
```dockerfile
# Current Dockerfile patterns:
COPY edge_api/ /app/edge_api/
COPY radar_service.py /app/
COPY requirements*.txt /app/

# Updated patterns:
COPY src/api/ /app/src/api/
COPY src/services/ /app/src/services/
COPY requirements*.txt /app/
```

### Appendix D: CI/CD Pipeline Updates

#### GitHub Actions Workflow Changes
```yaml
# Current workflow patterns:
- name: Test API
  run: python -m pytest scripts/development/test_*.py

- name: Build Docker
  run: docker build -f Dockerfile .

# Updated patterns:
- name: Test API
  run: python -m pytest tests/unit/api/

- name: Build Docker
  run: docker build -f config/docker/images/api.Dockerfile .
```

### Appendix E: Migration Checklist

#### Pre-Migration Checklist
- [ ] Full repository backup created
- [ ] Test environment configured
- [ ] Team notification sent
- [ ] Rollback procedure documented and tested
- [ ] Migration tools prepared and tested

#### Phase 1 Checklist (Documentation & Configuration)
- [ ] New directory structure created
- [ ] Documentation files moved
- [ ] Configuration files organized
- [ ] Internal documentation links updated
- [ ] Configuration loading tested

#### Phase 2 Checklist (Non-Critical Source Code)
- [ ] UI components moved to src/ui/
- [ ] Processing modules moved to src/processing/
- [ ] Utility scripts relocated
- [ ] Basic functionality testing completed

#### Phase 3 Checklist (Core Services & APIs)
- [ ] API services moved to src/api/
- [ ] Core services relocated to src/services/
- [ ] Import statements updated
- [ ] Docker build contexts updated
- [ ] Service files path updates completed
- [ ] Full system testing completed

#### Phase 4 Checklist (Testing Infrastructure)
- [ ] Test files moved to tests/ directory
- [ ] Test organization implemented
- [ ] Test imports updated
- [ ] Test suite execution verified

#### Phase 5 Checklist (Deployment & Tools)
- [ ] Deployment scripts relocated
- [ ] CI/CD pipelines updated
- [ ] Monitoring tools relocated
- [ ] Full deployment testing completed

#### Post-Migration Checklist
- [ ] All services functioning correctly
- [ ] Performance metrics within acceptable ranges
- [ ] Team training completed
- [ ] Documentation updated
- [ ] Success metrics recorded
- [ ] Lessons learned documented

---

**Document Control:**
- **Created:** September 27, 2025
- **Last Modified:** September 27, 2025
- **Version:** 1.0
- **Next Review Date:** October 27, 2025
- **Approved By:** [Pending]
- **Implementation Status:** Proposal Phase