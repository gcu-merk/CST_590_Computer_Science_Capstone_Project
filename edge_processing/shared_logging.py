#!/usr/bin/env python3
"""
Centralized Logging Configuration for Traffic Monitoring System
Provides consistent logging setup across all services
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import traceback


class ServiceLogger:
    """Centralized logging configuration for all services"""
    
    def __init__(self, 
                 service_name: str,
                 log_level: str = "INFO",
                 log_dir: str = "/mnt/storage/logs/applications",
                 enable_correlation: bool = True):
        
        self.service_name = service_name
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.enable_correlation = enable_correlation
        self.correlation_id = None
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file rotation and structured format"""
        
        logger = logging.getLogger(self.service_name)
        logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        logger.handlers = []
        
        # Custom formatter with correlation support
        formatter = StructuredFormatter(
            service_name=self.service_name,
            enable_correlation=self.enable_correlation
        )
        
        # File handler with rotation
        log_file = self.log_dir / f"{self.service_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler for Docker logs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(formatter)
        
        # Error handler for critical issues
        error_file = self.log_dir / f"{self.service_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler) 
        logger.addHandler(error_handler)
        
        return logger
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id
        
        # Update formatter
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, StructuredFormatter):
                handler.formatter.correlation_id = correlation_id
    
    def get_logger(self) -> logging.Logger:
        """Get configured logger instance"""
        return self.logger
    
    def log_service_start(self, config: Dict[str, Any] = None):
        """Log service startup with configuration"""
        self.logger.info("🚀 Service starting", extra={
            'event_type': 'service_start',
            'config': config or {},
            'pid': os.getpid()
        })
    
    def log_service_stop(self):
        """Log service shutdown"""
        self.logger.info("🛑 Service stopping", extra={
            'event_type': 'service_stop',
            'pid': os.getpid()
        })
    
    def log_performance(self, operation: str, duration_ms: float, metadata: Dict = None):
        """Log performance metrics"""
        self.logger.info(f"⏱️ {operation} completed in {duration_ms:.2f}ms", extra={
            'event_type': 'performance',
            'operation': operation,
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        })
    
    def log_error_with_context(self, error: Exception, context: Dict = None):
        """Log error with full context and traceback"""
        self.logger.error(f"❌ {error.__class__.__name__}: {str(error)}", extra={
            'event_type': 'error',
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc()
        })


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with correlation support"""
    
    def __init__(self, service_name: str, enable_correlation: bool = True):
        super().__init__()
        self.service_name = service_name
        self.enable_correlation = enable_correlation
        self.correlation_id = None
    
    def format(self, record):
        """Format log record with structure and correlation"""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'service': self.service_name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add correlation ID if available
        if self.enable_correlation and self.correlation_id:
            log_entry['correlation_id'] = self.correlation_id
        
        # Add extra fields from log call
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        
        if hasattr(record, 'metadata'):
            log_entry.update(record.metadata)
        
        # For console output (human readable)
        console_format = f"[{log_entry['timestamp']}] {log_entry['level']} | {log_entry['service']}"
        
        if self.correlation_id:
            console_format += f" | {self.correlation_id[:8]}"
        
        console_format += f" | {log_entry['message']}"
        
        # For file output (JSON structured)
        if any(isinstance(h, logging.handlers.RotatingFileHandler) 
               for h in logging.getLogger(self.service_name).handlers):
            return json.dumps(log_entry)
        
        return console_format


class CorrelationContext:
    """Context manager for correlation ID tracking"""
    
    def __init__(self, logger: ServiceLogger, correlation_id: str = None):
        self.logger = logger
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.previous_id = None
    
    def __enter__(self):
        self.previous_id = self.logger.correlation_id
        self.logger.set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.set_correlation_id(self.previous_id)
    
    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# Global logger instances for each service
_loggers = {}

def get_service_logger(service_name: str, **kwargs) -> ServiceLogger:
    """Get or create service logger instance"""
    if service_name not in _loggers:
        _loggers[service_name] = ServiceLogger(service_name, **kwargs)
    return _loggers[service_name]


# Convenience functions for common services
def get_radar_logger() -> ServiceLogger:
    """Get radar service logger"""
    return get_service_logger("radar_service")

def get_camera_logger() -> ServiceLogger:
    """Get camera service logger"""  
    return get_service_logger("camera_service")

def get_consolidator_logger() -> ServiceLogger:
    """Get consolidator service logger"""
    return get_service_logger("vehicle_consolidator")

def get_api_logger() -> ServiceLogger:
    """Get API service logger"""
    return get_service_logger("api_service")

def get_weather_logger() -> ServiceLogger:
    """Get weather service logger"""
    return get_service_logger("weather_service")


if __name__ == "__main__":
    # Demo usage
    logger = get_service_logger("demo_service")
    
    logger.log_service_start({"port": 5000, "debug": True})
    
    with CorrelationContext(logger) as correlation_id:
        logger.get_logger().info(f"Processing request with ID: {correlation_id}")
        logger.log_performance("data_processing", 245.5, {"records": 100})
    
    try:
        raise ValueError("Demo error")
    except Exception as e:
        logger.log_error_with_context(e, {"user_id": "test", "action": "demo"})
    
    logger.log_service_stop()