# Project Structure Documentation

## Reorganized Code Structure

The repository has been reorganized to properly align with the documented traffic monitoring system architecture:

### New Structure

```text
CST_590_Computer_Science_Capstone_Project/
├── edge_processing/              # Core edge processing services
│   ├── vehicle-detection/        # AI camera + TensorFlow vehicle detection
│   │   └── vehicle_detection_service.py
│   ├── speed-analysis/           # OPS243-C radar speed measurement  
│   │   └── speed_analysis_service.py
│   ├── data-fusion/              # Kalman filter fusion engine
│   │   └── data_fusion_engine.py
│   ├── tracking/                 # Multi-vehicle tracking (SORT)
│   ├── system-health/            # System monitoring and alerts
│   │   └── system_health_monitor.py
│   └── requirements.txt
├── edge-api/                     # Flask-SocketIO API gateway
│   ├── edge_api_gateway.py
│   └── requirements.txt
├── edge-ui/                      # Local web dashboard (future)
├── data-collection/              # Legacy data collection modules (updated)
│   ├── data-consolidator/        # Data consolidation service
│   ├── data-persister/           # Database persistence service
│   ├── speed-data-collection/    # Legacy speed module (redirects to new)
│   ├── license-plate-data-collection/
│   ├── stop-sign-data-collection/
│   └── utils/
├── database/                     # Database schemas and scripts
├── webserver/                    # Backend services (existing)
├── website/                      # Frontend UI (existing)
├── raspberry-pi/                 # Pi-specific deployment scripts
├── main_edge_app.py             # Main orchestrator application
└── documentation/               # Project documentation
```

### Key Changes Made

1. **New Edge Processing Layer**: Created modular services for:
   - Vehicle detection (Sony IMX500 AI camera + TensorFlow)
   - Speed analysis (OPS243-C radar processing)
   - Data fusion (Kalman filtering for camera+radar fusion)
   - System health monitoring (Pi 5 performance monitoring)

2. **Edge API Gateway**: Flask-SocketIO server providing:
   - REST endpoints for data access
   - WebSocket for real-time updates
   - Integration with all processing services

3. **Main Orchestrator**: `main_edge_app.py` coordinates all services:
   - Service initialization and shutdown
   - Health monitoring
   - Graceful error handling

4. **Updated Legacy Modules**:
   - Data consolidator for multi-source data aggregation
   - Data persister with SQLite database integration
   - Backward compatibility for existing speed collection

5. **Proper Dependencies**: Requirements files for each module

### Architecture Alignment

This structure now properly implements the documented system architecture:

- **Physical Sensing Layer**: Hardware interfaces (camera, radar)
- **Edge Processing Layer**: ML/AI services, data fusion, tracking
- **Network & Communication Layer**: API gateway, WebSocket communication  
- **Cloud Services Layer**: (Future cloud integration points)

### Next Steps

1. Implement multi-vehicle tracking service (SORT algorithm)
2. Create edge UI web dashboard
3. Add cloud integration services
4. Implement comprehensive testing suite
5. Add deployment scripts and Docker containers

The code is now properly modularized and follows the architectural design documented in the docs folder.
