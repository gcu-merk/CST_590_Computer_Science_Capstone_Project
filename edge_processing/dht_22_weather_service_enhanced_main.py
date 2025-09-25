#!/usr/bin/env python3
"""
DHT22 Weather Service Enhanced - Module Entry Point
Allows execution via: python -m edge_processing.dht_22_weather_service_enhanced_main
"""

if __name__ == "__main__":
    from .dht_22_weather_service_enhanced import EnhancedDHT22Service
    import sys
    
    # Import centralized logging
    from .shared_logging import ServiceLogger
    logger = ServiceLogger("dht22_weather_service")
    
    try:
        logger.info("Starting DHT22 weather service via module entry point", extra={
            "business_event": "service_startup_module",
            "entry_point": "dht_22_weather_service_enhanced_main"
        })
        
        service = EnhancedDHT22Service()
        service.run()
    except Exception as e:
        logger.error("Failed to start DHT22 service via module", extra={
            "business_event": "startup_failure_module",
            "error": str(e),
            "entry_point": "dht_22_weather_service_enhanced_main"
        })
        sys.exit(1)