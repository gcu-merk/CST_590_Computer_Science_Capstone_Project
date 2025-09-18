#!/usr/bin/env python3
"""
Standalone API server for Swagger access
Bypasses all GPIO and sensor imports to provide API access while containers are being fixed
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for API modules
sys.path.append(str(Path(__file__).parent / "edge_api"))

try:
    # Import Swagger-enabled API gateway directly
    from edge_api.swagger_api_gateway import SwaggerAPIGateway as EdgeAPIGateway
    logger.info("Using Swagger-enabled API gateway")
    SWAGGER_ENABLED = True
except ImportError as e:
    logger.warning(f"Swagger API import failed: {e}")
    try:
        # Fallback to original API gateway
        from edge_api.edge_api_gateway import EdgeAPIGateway
        logger.info("Using original API gateway")
        SWAGGER_ENABLED = False
    except ImportError as e2:
        logger.error(f"Both API gateways failed to import: {e2}")
        sys.exit(1)

def main():
    """Run standalone API server"""
    logger.info("=" * 60)
    logger.info("Standalone Traffic Monitoring API Server")
    logger.info("=" * 60)
    logger.info("Starting API-only mode for Swagger access")
    
    # Initialize API gateway
    api_gateway = EdgeAPIGateway(host='0.0.0.0', port=5000)
    
    # Set minimal services (no GPIO dependencies)
    api_gateway.set_services(
        system_health=None,  # Skip health monitoring to avoid GPIO
        vehicle_detection=None,
        speed_analysis=None,
        data_fusion=None
    )
    
    try:
        # Start API server
        if SWAGGER_ENABLED:
            logger.info("Swagger API available at: http://0.0.0.0:5000/docs/")
        logger.info("API available at: http://0.0.0.0:5000")
        logger.info("Health check: http://0.0.0.0:5000/api/health")
        api_gateway.start_server()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"API server error: {e}")
        raise

if __name__ == "__main__":
    main()