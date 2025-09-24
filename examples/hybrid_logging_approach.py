#!/usr/bin/env python3
"""
Hybrid Logging Approach - Best of Both Worlds
Embedded reliability + Optional centralized aggregation
"""

import logging
import json
import os
import sys
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from queue import Queue
import threading


class HybridLogger:
    """
    Hybrid logging approach:
    1. Always log locally (reliable)
    2. Optionally ship to centralized service (best effort)
    3. Graceful degradation when centralized logging fails
    """
    
    def __init__(self, 
                 service_name: str,
                 local_log_dir: str = "/app/logs",
                 central_logging_url: Optional[str] = None,
                 enable_shipping: bool = True):
        
        self.service_name = service_name
        self.local_log_dir = Path(local_log_dir)
        self.central_logging_url = central_logging_url
        self.enable_shipping = enable_shipping
        
        # Setup local logging (always works)
        self.local_logger = self._setup_local_logger()
        
        # Setup optional log shipping (non-blocking)
        self.log_queue = Queue(maxsize=1000) if enable_shipping else None
        self.shipping_thread = None
        
        if enable_shipping and central_logging_url:
            self._start_log_shipping()
    
    def _setup_local_logger(self) -> logging.Logger:
        """Setup reliable local logging (embedded approach)"""
        
        # Ensure log directory exists
        self.local_log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(f"{self.service_name}_local")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []
        
        # Structured formatter
        formatter = logging.Formatter(
            json.dumps({
                "timestamp": "%(asctime)s",
                "service": self.service_name,
                "level": "%(levelname)s",
                "message": "%(message)s"
            })
        )
        
        # Local file handler (always reliable)
        file_handler = logging.handlers.RotatingFileHandler(
            self.local_log_dir / f"{self.service_name}.log",
            maxBytes=10*1024*1024,
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        
        # Console handler for Docker logs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _start_log_shipping(self):
        """Start background thread for optional log shipping"""
        self.shipping_thread = threading.Thread(
            target=self._log_shipping_worker,
            daemon=True
        )
        self.shipping_thread.start()
    
    def _log_shipping_worker(self):
        """Background worker that ships logs (best effort)"""
        while True:
            try:
                # Get log entry from queue (blocking)
                log_entry = self.log_queue.get(timeout=5)
                
                # Try to ship to central service
                asyncio.run(self._ship_log_entry(log_entry))
                
            except Exception as e:
                # Shipping failed - log locally but don't crash
                self.local_logger.error(f"Log shipping failed: {e}")
                continue
    
    async def _ship_log_entry(self, log_entry: Dict):
        """Ship log entry to central service (async, non-blocking)"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                async with session.post(
                    self.central_logging_url,
                    json=log_entry,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Central logging returned {response.status}")
        
        except Exception as e:
            # Central logging failed - just continue
            # Don't let this affect the main application!
            pass
    
    def log_event(self, 
                  level: str,
                  message: str,
                  correlation_id: str = None,
                  **details):
        """
        Log event with hybrid approach:
        1. Always log locally (reliable)
        2. Queue for central shipping (best effort)
        """
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level.upper(),
            "message": message,
            "correlation_id": correlation_id,
            **details
        }
        
        # 1. ALWAYS log locally first (never fails)
        self.local_logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_entry)
        )
        
        # 2. Queue for optional central shipping (non-blocking)
        if self.enable_shipping and self.log_queue:
            try:
                self.log_queue.put_nowait(log_entry)
            except:
                # Queue full - drop the central log but keep local
                pass
    
    def log_vehicle_detection(self, speed_mph: float, correlation_id: str):
        """Critical business event - must never fail"""
        self.log_event(
            level="info",
            message=f"🚗 Vehicle detected: {speed_mph} mph",
            correlation_id=correlation_id,
            event_type="vehicle_detected",
            speed_mph=speed_mph,
            business_critical=True
        )
    
    def log_error(self, error: Exception, context: str, correlation_id: str = None):
        """Error logging - must never fail"""
        self.log_event(
            level="error",
            message=f"Error in {context}: {str(error)}",
            correlation_id=correlation_id,
            event_type="error",
            error_type=type(error).__name__,
            context=context
        )


# Usage in radar service
def radar_service_example():
    """Example usage in radar service"""
    
    # Setup hybrid logger
    logger = HybridLogger(
        service_name="radar-service",
        local_log_dir="/app/logs/radar-service",
        central_logging_url=os.environ.get("CENTRAL_LOG_URL"),  # Optional
        enable_shipping=os.environ.get("ENABLE_LOG_SHIPPING", "false").lower() == "true"
    )
    
    # Vehicle detection - ALWAYS works locally
    correlation_id = "abc123"
    
    try:
        # Business logic
        speed_mph = 45.2
        
        # This NEVER fails (local logging always works)
        logger.log_vehicle_detection(speed_mph, correlation_id)
        
        # Even if central logging service is down, this still works!
        
    except Exception as e:
        # Error logging also never fails
        logger.log_error(e, "radar_detection_loop", correlation_id)


if __name__ == "__main__":
    radar_service_example()