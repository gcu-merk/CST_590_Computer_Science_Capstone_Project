#!/usr/bin/env python3
"""
Modern API startup script with best practices architecture
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the modernized API server"""
    
    # Import after path setup
    try:
        from edge_api.swagger_api_gateway import SwaggerAPIGateway
        from edge_api.config import config
    except ImportError as e:
        print(f"Error importing API modules: {e}")
        print("Make sure you're in the project directory and all dependencies are installed")
        return 1
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Traffic Monitoring API with Best Practices Architecture")
    logger.info(f"Configuration loaded - Host: {config.api.host}, Port: {config.api.port}")
    logger.info(f"Redis: {config.database.redis_host}:{config.database.redis_port}")
    logger.info(f"Debug Mode: {config.api.debug_mode}")
    
    try:
        # Create and run the API gateway
        gateway = SwaggerAPIGateway(
            host=config.api.host,
            port=config.api.port
        )
        
        logger.info("API Gateway initialized successfully")
        logger.info(f"Swagger documentation available at: http://{config.api.host}:{config.api.port}/swagger")
        logger.info(f"API endpoints available at: http://{config.api.host}:{config.api.port}/api/")
        
        # Run the server
        gateway.run(debug=config.api.debug_mode, use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())