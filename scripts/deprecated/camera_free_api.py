#!/usr/bin/env python3
"""
Quick Camera-Free API Launcher
Bypasses camera and GPIO initialization to get Swagger API running immediately
"""

import os
import sys
import logging
from flask import Flask

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_camera_free_app():
    """Create a minimal Flask app with just the Swagger API"""
    app = Flask(__name__)
    
    # Basic health endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'healthy', 'mode': 'camera-free', 'timestamp': '2025-09-18T21:50:00Z'}
    
    @app.route('/api/status', methods=['GET'])
    def status():
        return {'status': 'running', 'services': ['api'], 'camera': 'disabled', 'gpio': 'disabled'}
    
    # Try to import and configure Swagger if available
    try:
        from edge_api.swagger_api_gateway import create_swagger_app
        logger.info("Loading full Swagger API...")
        return create_swagger_app()
    except Exception as e:
        logger.warning(f"Swagger API not available: {e}")
        logger.info("Running minimal API only")
        return app

if __name__ == '__main__':
    logger.info("Starting camera-free API service...")
    
    # Override environment variables to disable hardware
    os.environ['DISABLE_CAMERA'] = 'true'
    os.environ['DISABLE_GPIO'] = 'true'
    os.environ['MOCK_HARDWARE'] = 'true'
    
    app = create_camera_free_app()
    
    # Run the server
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info("API will be available at http://100.121.231.16:5000/api/")
    logger.info("Health check: http://100.121.231.16:5000/api/health")
    logger.info("Status check: http://100.121.231.16:5000/api/status")
    
    app.run(host=host, port=port, debug=False)