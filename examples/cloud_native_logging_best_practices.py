#!/usr/bin/env python3
"""
Cloud-Native Logging Best Practices Implementation
Follows 12-factor app and Kubernetes logging standards
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Any
import traceback
import uuid
from contextlib import contextmanager


class CloudNativeLogger:
    """
    Cloud-native logging following industry best practices:
    - Stdout/stderr only (no file handlers)
    - Structured JSON logs
    - Correlation tracking
    - External log aggregation ready
    """
    
    def __init__(self, 
                 service_name: str,
                 service_version: str = "1.0.0",
                 environment: str = "production",
                 log_level: str = "INFO"):
        
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        
        # Setup structured logger (stdout only)
        self.logger = self._setup_cloud_native_logger(log_level)
        
        # Service metadata
        self.service_metadata = {
            "service": service_name,
            "version": service_version,
            "environment": environment,
            "host": os.environ.get('HOSTNAME', 'unknown'),
            "pod_name": os.environ.get('HOSTNAME', 'unknown'),  # Kubernetes pod name
            "namespace": os.environ.get('NAMESPACE', 'default')
        }
    
    def _setup_cloud_native_logger(self, log_level: str) -> logging.Logger:
        """Setup cloud-native logger (stdout/stderr only)"""
        
        logger = logging.getLogger(self.service_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        logger.handlers = []
        
        # Single structured handler to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(CloudNativeFormatter())
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    def log_structured(self, 
                      level: str,
                      message: str, 
                      event_type: str = None,
                      correlation_id: str = None,
                      **kwargs) -> None:
        """Log structured event with metadata"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "message": message,
            "event_type": event_type,
            **self.service_metadata
        }
        
        # Add correlation tracking
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add custom fields
        if kwargs:
            log_entry["details"] = kwargs
        
        # Log based on level
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))
    
    def log_business_event(self, event_type: str, message: str, 
                          correlation_id: str = None, **details):
        """Log business/domain events"""
        self.log_structured(
            level="info",
            message=message,
            event_type=event_type,
            correlation_id=correlation_id,
            business_event=True,
            **details
        )
    
    def log_performance(self, operation: str, duration_ms: float, 
                       correlation_id: str = None, **details):
        """Log performance metrics"""
        self.log_structured(
            level="info",
            message=f"Performance: {operation} completed in {duration_ms:.2f}ms",
            event_type="performance_metric",
            correlation_id=correlation_id,
            operation=operation,
            duration_ms=duration_ms,
            **details
        )
    
    def log_error(self, error: Exception, context: str = None, 
                  correlation_id: str = None, **details):
        """Log errors with stack trace"""
        self.log_structured(
            level="error",
            message=f"Error: {str(error)}",
            event_type="error",
            correlation_id=correlation_id,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context,
            **details
        )


class CloudNativeFormatter(logging.Formatter):
    """Formatter that expects JSON strings"""
    
    def format(self, record):
        # If the message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, AttributeError):
            # Fallback for non-JSON messages
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            })


@contextmanager
def correlation_context(operation_name: str = None):
    """Create correlation context for request tracing"""
    correlation_id = str(uuid.uuid4())[:8]
    
    # Could integrate with OpenTelemetry here
    print(f"Starting operation: {operation_name} (correlation_id: {correlation_id})")
    
    try:
        yield correlation_id
    finally:
        print(f"Completed operation: {operation_name} (correlation_id: {correlation_id})")


# Example usage in radar service
def example_radar_service_usage():
    """Example of cloud-native logging in radar service"""
    
    logger = CloudNativeLogger(
        service_name="radar-service",
        service_version="2.1.0",
        environment=os.environ.get("ENVIRONMENT", "production")
    )
    
    with correlation_context("vehicle_detection") as correlation_id:
        # Business event
        logger.log_business_event(
            event_type="vehicle_detected",
            message="Vehicle detected at high speed",
            correlation_id=correlation_id,
            speed_mph=45.2,
            location="sensor_1"
        )
        
        # Performance metric
        logger.log_performance(
            operation="radar_data_processing",
            duration_ms=12.5,
            correlation_id=correlation_id,
            records_processed=1
        )


if __name__ == "__main__":
    example_radar_service_usage()