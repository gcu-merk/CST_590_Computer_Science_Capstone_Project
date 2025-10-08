#!/usr/bin/env python3
"""
Configuration Validation Script
================================

Validates the centralized configuration system before deployment.
This script can be run:
1. During Docker build to catch config errors early
2. Before starting services to ensure valid configuration
3. As a standalone CLI tool for config debugging

Usage:
    python config/validate_config.py                    # Validate all
    python config/validate_config.py --service radar    # Validate specific service
    python config/validate_config.py --category redis   # Validate specific category
    python config/validate_config.py --verbose          # Detailed output
    python config/validate_config.py --json             # JSON output

Exit Codes:
    0  - All validations passed
    1  - Configuration validation failed
    2  - Missing required environment variables
    3  - Invalid configuration values
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    get_config,
    RedisConfig,
    DatabaseConfig,
    APIConfig,
    CameraConfig,
    RadarConfig,
    WeatherConfig,
    LoggingConfig,
    ConsolidatorConfig,
    MaintenanceConfig,
    SecurityConfig,
)


class ValidationResult:
    """Stores validation result with details"""
    
    def __init__(self, category: str, passed: bool, message: str, details: Optional[Dict] = None):
        self.category = category
        self.passed = passed
        self.message = message
        self.details = details or {}
        
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "passed": self.passed,
            "message": self.message,
            "details": self.details
        }


class ConfigValidator:
    """Validates centralized configuration"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[ValidationResult] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode enabled"""
        if self.verbose:
            prefix = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "ERROR": "❌",
                "WARNING": "⚠️"
            }.get(level, "•")
            print(f"{prefix} {message}")
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        self.log("Starting comprehensive configuration validation...", "INFO")
        
        try:
            # Load configuration
            config = get_config()
            self.log("Configuration loaded successfully", "SUCCESS")
            
            # Validate each category
            self.validate_redis(config.redis)
            self.validate_database(config.database)
            self.validate_api(config.api)
            self.validate_camera(config.camera)
            self.validate_radar(config.radar)
            self.validate_weather(config.weather)
            self.validate_logging(config.logging)
            self.validate_consolidator(config.consolidator)
            self.validate_maintenance(config.maintenance)
            self.validate_security(config.security)
            
            # Check for failures
            failed = [r for r in self.results if not r.passed]
            if failed:
                self.log(f"Validation failed: {len(failed)} errors found", "ERROR")
                return False
            
            self.log(f"All validations passed! {len(self.results)} checks completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.results.append(ValidationResult(
                category="system",
                passed=False,
                message=f"Fatal error during validation: {str(e)}",
                details={"exception": type(e).__name__}
            ))
            self.log(f"Fatal error: {str(e)}", "ERROR")
            return False
    
    def validate_redis(self, redis: RedisConfig):
        """Validate Redis configuration"""
        self.log("Validating Redis configuration...", "INFO")
        
        # Check host
        if not redis.host or redis.host.strip() == "":
            self.results.append(ValidationResult(
                "redis", False, "Redis host cannot be empty",
                {"host": redis.host}
            ))
            return
        
        # Check port range
        if not (1 <= redis.port <= 65535):
            self.results.append(ValidationResult(
                "redis", False, f"Redis port {redis.port} out of valid range (1-65535)",
                {"port": redis.port}
            ))
            return
        
        # Check database number
        if not (0 <= redis.db <= 15):
            self.results.append(ValidationResult(
                "redis", False, f"Redis DB {redis.db} out of range (0-15)",
                {"db": redis.db}
            ))
            return
        
        # Check max connections
        if redis.max_connections < 1:
            self.results.append(ValidationResult(
                "redis", False, f"Invalid max_connections: {redis.max_connections}",
                {"max_connections": redis.max_connections}
            ))
            return
        
        # Check optimization settings
        if redis.optimization_interval < 60:
            self.results.append(ValidationResult(
                "redis", False, f"Optimization interval too short: {redis.optimization_interval}s (min 60s)",
                {"optimization_interval": redis.optimization_interval}
            ))
            return
        
        if redis.memory_threshold_mb < 100:
            self.results.append(ValidationResult(
                "redis", False, f"Memory threshold too low: {redis.memory_threshold_mb}MB (min 100MB)",
                {"memory_threshold_mb": redis.memory_threshold_mb}
            ))
            return
        
        self.results.append(ValidationResult(
            "redis", True, "Redis configuration valid",
            {
                "host": redis.host,
                "port": redis.port,
                "db": redis.db,
                "max_connections": redis.max_connections
            }
        ))
        self.log(f"Redis: {redis.host}:{redis.port} (DB {redis.db})", "SUCCESS")
    
    def validate_database(self, db: DatabaseConfig):
        """Validate Database configuration"""
        self.log("Validating Database configuration...", "INFO")
        
        # Check path is not empty
        if not db.path or db.path.strip() == "":
            self.results.append(ValidationResult(
                "database", False, "Database path cannot be empty",
                {"path": db.path}
            ))
            return
        
        # Check batch size
        if not (1 <= db.batch_size <= 10000):
            self.results.append(ValidationResult(
                "database", False, f"Invalid batch_size: {db.batch_size} (range: 1-10000)",
                {"batch_size": db.batch_size}
            ))
            return
        
        # Check commit interval
        if not (1 <= db.commit_interval_seconds <= 3600):
            self.results.append(ValidationResult(
                "database", False, f"Invalid commit_interval: {db.commit_interval_seconds}s (range: 1-3600)",
                {"commit_interval_seconds": db.commit_interval_seconds}
            ))
            return
        
        # Check retention days
        if not (1 <= db.retention_days <= 3650):
            self.results.append(ValidationResult(
                "database", False, f"Invalid retention_days: {db.retention_days} (range: 1-3650)",
                {"retention_days": db.retention_days}
            ))
            return
        
        self.results.append(ValidationResult(
            "database", True, "Database configuration valid",
            {
                "path": db.path,
                "batch_size": db.batch_size,
                "commit_interval_seconds": db.commit_interval_seconds,
                "retention_days": db.retention_days
            }
        ))
        self.log(f"Database: {db.path} (retention: {db.retention_days} days)", "SUCCESS")
    
    def validate_api(self, api: APIConfig):
        """Validate API configuration"""
        self.log("Validating API configuration...", "INFO")
        
        # Check host
        if not api.host:
            self.results.append(ValidationResult(
                "api", False, "API host cannot be empty",
                {"host": api.host}
            ))
            return
        
        # Check port
        if not (1 <= api.port <= 65535):
            self.results.append(ValidationResult(
                "api", False, f"API port {api.port} out of range (1-65535)",
                {"port": api.port}
            ))
            return
        
        # Check workers
        if not (1 <= api.workers <= 32):
            self.results.append(ValidationResult(
                "api", False, f"Invalid worker count: {api.workers} (range: 1-32)",
                {"workers": api.workers}
            ))
            return
        
        # Warning if debug in production
        if api.debug:
            self.log("WARNING: API debug mode enabled", "WARNING")
        
        self.results.append(ValidationResult(
            "api", True, "API configuration valid",
            {
                "host": api.host,
                "port": api.port,
                "debug": api.debug,
                "workers": api.workers
            }
        ))
        self.log(f"API: {api.host}:{api.port} (workers: {api.workers})", "SUCCESS")
    
    def validate_camera(self, camera: CameraConfig):
        """Validate Camera configuration"""
        self.log("Validating Camera configuration...", "INFO")
        
        # Check capture directory
        if not camera.capture_dir:
            self.results.append(ValidationResult(
                "camera", False, "Camera capture_dir cannot be empty",
                {"capture_dir": camera.capture_dir}
            ))
            return
        
        # Check model path
        if not camera.model_path:
            self.results.append(ValidationResult(
                "camera", False, "Camera model_path cannot be empty",
                {"model_path": camera.model_path}
            ))
            return
        
        # Check capture interval
        if not (0.1 <= camera.capture_interval <= 60.0):
            self.results.append(ValidationResult(
                "camera", False, f"Invalid capture_interval: {camera.capture_interval}s (range: 0.1-60)",
                {"capture_interval": camera.capture_interval}
            ))
            return
        
        # Check confidence threshold
        if not (0.0 <= camera.confidence_threshold <= 1.0):
            self.results.append(ValidationResult(
                "camera", False, f"Invalid confidence_threshold: {camera.confidence_threshold} (range: 0.0-1.0)",
                {"confidence_threshold": camera.confidence_threshold}
            ))
            return
        
        # Check ROI coordinates
        roi_checks = [
            ("roi_x_start", camera.roi_x_start),
            ("roi_x_end", camera.roi_x_end),
            ("roi_y_start", camera.roi_y_start),
            ("roi_y_end", camera.roi_y_end),
        ]
        
        for name, value in roi_checks:
            if not (0.0 <= value <= 1.0):
                self.results.append(ValidationResult(
                    "camera", False, f"Invalid {name}: {value} (range: 0.0-1.0)",
                    {name: value}
                ))
                return
        
        # Check ROI logic
        if camera.roi_x_start >= camera.roi_x_end:
            self.results.append(ValidationResult(
                "camera", False, "ROI x_start must be < x_end",
                {
                    "x_start": camera.roi_x_start,
                    "x_end": camera.roi_x_end
                }
            ))
            return
        
        if camera.roi_y_start >= camera.roi_y_end:
            self.results.append(ValidationResult(
                "camera", False, "ROI y_start must be < y_end",
                {
                    "y_start": camera.roi_y_start,
                    "y_end": camera.roi_y_end
                }
            ))
            return
        
        self.results.append(ValidationResult(
            "camera", True, "Camera configuration valid",
            {
                "capture_dir": camera.capture_dir,
                "model_path": camera.model_path,
                "capture_interval": camera.capture_interval,
                "confidence_threshold": camera.confidence_threshold
            }
        ))
        self.log(f"Camera: interval={camera.capture_interval}s, confidence={camera.confidence_threshold}", "SUCCESS")
    
    def validate_radar(self, radar: RadarConfig):
        """Validate Radar configuration"""
        self.log("Validating Radar configuration...", "INFO")
        
        # Check UART port
        if not radar.uart_port:
            self.results.append(ValidationResult(
                "radar", False, "Radar uart_port cannot be empty",
                {"uart_port": radar.uart_port}
            ))
            return
        
        # Check baud rate
        valid_baud_rates = [9600, 19200, 38400, 57600, 115200]
        if radar.baud_rate not in valid_baud_rates:
            self.results.append(ValidationResult(
                "radar", False, f"Invalid baud_rate: {radar.baud_rate} (valid: {valid_baud_rates})",
                {"baud_rate": radar.baud_rate}
            ))
            return
        
        self.results.append(ValidationResult(
            "radar", True, "Radar configuration valid",
            {
                "uart_port": radar.uart_port,
                "baud_rate": radar.baud_rate
            }
        ))
        self.log(f"Radar: {radar.uart_port} @ {radar.baud_rate} baud", "SUCCESS")
    
    def validate_weather(self, weather: WeatherConfig):
        """Validate Weather configuration"""
        self.log("Validating Weather configuration...", "INFO")
        
        # Check DHT22 GPIO pin
        if not (0 <= weather.gpio_pin <= 27):
            self.results.append(ValidationResult(
                "weather", False, f"Invalid DHT22 GPIO pin: {weather.gpio_pin} (range: 0-27)",
                {"gpio_pin": weather.gpio_pin}
            ))
            return
        
        # Check update intervals
        if not (60 <= weather.update_interval_seconds <= 86400):
            self.results.append(ValidationResult(
                "weather", False, f"Invalid DHT22 update interval: {weather.update_interval_seconds}s (range: 60-86400)",
                {"update_interval_seconds": weather.update_interval_seconds}
            ))
            return
        
        # Check airport weather settings
        if weather.api_url and not weather.api_url.startswith("http"):
            self.results.append(ValidationResult(
                "weather", False, f"Invalid API URL: {weather.api_url}",
                {"api_url": weather.api_url}
            ))
            return
        
        if not (5 <= weather.api_timeout <= 300):
            self.results.append(ValidationResult(
                "weather", False, f"Invalid API timeout: {weather.api_timeout}s (range: 5-300)",
                {"api_timeout": weather.api_timeout}
            ))
            return
        
        if not (1 <= weather.fetch_interval_minutes <= 1440):
            self.results.append(ValidationResult(
                "weather", False, f"Invalid fetch interval: {weather.fetch_interval_minutes} minutes (range: 1-1440)",
                {"fetch_interval_minutes": weather.fetch_interval_minutes}
            ))
            return
        
        self.results.append(ValidationResult(
            "weather", True, "Weather configuration valid",
            {
                "gpio_pin": weather.gpio_pin,
                "update_interval_seconds": weather.update_interval_seconds,
                "fetch_interval_minutes": weather.fetch_interval_minutes
            }
        ))
        self.log(f"Weather: DHT22 on GPIO {weather.gpio_pin}, fetch interval {weather.fetch_interval_minutes}min", "SUCCESS")
    
    def validate_logging(self, logging: LoggingConfig):
        """Validate Logging configuration"""
        self.log("Validating Logging configuration...", "INFO")
        
        # Check log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if logging.level not in valid_levels:
            self.results.append(ValidationResult(
                "logging", False, f"Invalid log level: {logging.level} (valid: {valid_levels})",
                {"level": logging.level}
            ))
            return
        
        # Check log file path
        if not logging.file_path:
            self.results.append(ValidationResult(
                "logging", False, "Log file path cannot be empty",
                {"file_path": logging.file_path}
            ))
            return
        
        # Check file max bytes
        if logging.file_max_bytes < 1024:
            self.results.append(ValidationResult(
                "logging", False, f"File max bytes too small: {logging.file_max_bytes} (min 1024)",
                {"file_max_bytes": logging.file_max_bytes}
            ))
            return
        
        self.results.append(ValidationResult(
            "logging", True, "Logging configuration valid",
            {
                "level": logging.level,
                "file_path": logging.file_path,
                "file_enabled": logging.file_enabled
            }
        ))
        self.log(f"Logging: {logging.level} level, path={logging.file_path}", "SUCCESS")
    
    def validate_consolidator(self, consolidator: ConsolidatorConfig):
        """Validate Consolidator configuration"""
        self.log("Validating Consolidator configuration...", "INFO")
        
        # Check data retention
        if not (1 <= consolidator.data_retention_hours <= 8760):
            self.results.append(ValidationResult(
                "consolidator", False, f"Invalid data_retention_hours: {consolidator.data_retention_hours} (range: 1-8760)",
                {"data_retention_hours": consolidator.data_retention_hours}
            ))
            return
        
        # Check stats update interval
        if not (10 <= consolidator.stats_update_interval <= 3600):
            self.results.append(ValidationResult(
                "consolidator", False, f"Invalid stats_update_interval: {consolidator.stats_update_interval}s (range: 10-3600)",
                {"stats_update_interval": consolidator.stats_update_interval}
            ))
            return
        
        self.results.append(ValidationResult(
            "consolidator", True, "Consolidator configuration valid",
            {
                "data_retention_hours": consolidator.data_retention_hours,
                "stats_update_interval": consolidator.stats_update_interval,
                "camera_strict_mode": consolidator.camera_strict_mode
            }
        ))
        self.log(f"Consolidator: retention={consolidator.data_retention_hours}h, strict_mode={consolidator.camera_strict_mode}", "SUCCESS")
    
    def validate_maintenance(self, maintenance: MaintenanceConfig):
        """Validate Maintenance configuration"""
        self.log("Validating Maintenance configuration...", "INFO")
        
        # Check thresholds
        if not (50 <= maintenance.warning_threshold_percent <= 100):
            self.results.append(ValidationResult(
                "maintenance", False, f"Invalid warning_threshold: {maintenance.warning_threshold_percent}% (range: 50-100)",
                {"warning_threshold_percent": maintenance.warning_threshold_percent}
            ))
            return
        
        if not (70 <= maintenance.emergency_threshold_percent <= 100):
            self.results.append(ValidationResult(
                "maintenance", False, f"Invalid emergency_threshold: {maintenance.emergency_threshold_percent}% (range: 70-100)",
                {"emergency_threshold_percent": maintenance.emergency_threshold_percent}
            ))
            return
        
        # Check threshold logic
        if maintenance.warning_threshold_percent >= maintenance.emergency_threshold_percent:
            self.results.append(ValidationResult(
                "maintenance", False, "warning_threshold must be < emergency_threshold",
                {
                    "warning_threshold_percent": maintenance.warning_threshold_percent,
                    "emergency_threshold_percent": maintenance.emergency_threshold_percent
                }
            ))
            return
        
        # Check retention periods
        if not (1 <= maintenance.image_max_age_hours <= 8760):
            self.results.append(ValidationResult(
                "maintenance", False, f"Invalid image_max_age_hours: {maintenance.image_max_age_hours} (range: 1-8760)",
                {"image_max_age_hours": maintenance.image_max_age_hours}
            ))
            return
        
        self.results.append(ValidationResult(
            "maintenance", True, "Maintenance configuration valid",
            {
                "warning_threshold_percent": maintenance.warning_threshold_percent,
                "emergency_threshold_percent": maintenance.emergency_threshold_percent,
                "image_max_age_hours": maintenance.image_max_age_hours
            }
        ))
        self.log(f"Maintenance: warning={maintenance.warning_threshold_percent}%, emergency={maintenance.emergency_threshold_percent}%", "SUCCESS")
    
    def validate_security(self, security: SecurityConfig):
        """Validate Security configuration"""
        self.log("Validating Security configuration...", "INFO")
        
        # Check JWT algorithm
        valid_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if security.jwt_algorithm not in valid_algorithms:
            self.results.append(ValidationResult(
                "security", False, f"Invalid JWT algorithm: {security.jwt_algorithm} (valid: {valid_algorithms})",
                {"jwt_algorithm": security.jwt_algorithm}
            ))
            return
        
        # Check JWT expiration
        if not (1 <= security.jwt_expiration_hours <= 720):
            self.results.append(ValidationResult(
                "security", False, f"Invalid JWT expiration: {security.jwt_expiration_hours}h (range: 1-720)",
                {"jwt_expiration_hours": security.jwt_expiration_hours}
            ))
            return
        
        # Check HTTPS configuration if enabled
        if security.https_enabled:
            if not security.cert_path:
                self.results.append(ValidationResult(
                    "security", False, "HTTPS enabled but cert_path not set",
                    {"https_enabled": security.https_enabled, "cert_path": security.cert_path}
                ))
                return
            if not security.key_path:
                self.results.append(ValidationResult(
                    "security", False, "HTTPS enabled but key_path not set",
                    {"https_enabled": security.https_enabled, "key_path": security.key_path}
                ))
                return
        
        self.results.append(ValidationResult(
            "security", True, "Security configuration valid",
            {
                "jwt_algorithm": security.jwt_algorithm,
                "jwt_expiration_hours": security.jwt_expiration_hours,
                "https_enabled": security.https_enabled
            }
        ))
        self.log(f"Security: JWT algo={security.jwt_algorithm}, HTTPS={security.https_enabled}", "SUCCESS")
    
    def validate_category(self, category: str) -> bool:
        """Validate a specific configuration category"""
        self.log(f"Validating specific category: {category}", "INFO")
        
        try:
            config = get_config()
            
            validators = {
                "redis": lambda: self.validate_redis(config.redis),
                "database": lambda: self.validate_database(config.database),
                "api": lambda: self.validate_api(config.api),
                "camera": lambda: self.validate_camera(config.camera),
                "radar": lambda: self.validate_radar(config.radar),
                "weather": lambda: self.validate_weather(config.weather),
                "logging": lambda: self.validate_logging(config.logging),
                "consolidator": lambda: self.validate_consolidator(config.consolidator),
                "maintenance": lambda: self.validate_maintenance(config.maintenance),
                "security": lambda: self.validate_security(config.security),
            }
            
            if category not in validators:
                self.log(f"Unknown category: {category}", "ERROR")
                return False
            
            validators[category]()
            
            failed = [r for r in self.results if not r.passed]
            return len(failed) == 0
            
        except Exception as e:
            self.log(f"Error validating {category}: {str(e)}", "ERROR")
            return False
    
    def print_summary(self, json_output: bool = False):
        """Print validation summary"""
        if json_output:
            summary = {
                "total_checks": len(self.results),
                "passed": len([r for r in self.results if r.passed]),
                "failed": len([r for r in self.results if not r.passed]),
                "results": [r.to_dict() for r in self.results]
            }
            print(json.dumps(summary, indent=2))
        else:
            print("\n" + "="*70)
            print("Configuration Validation Summary")
            print("="*70)
            
            passed = [r for r in self.results if r.passed]
            failed = [r for r in self.results if not r.passed]
            
            print(f"\n✅ Passed: {len(passed)}")
            print(f"❌ Failed: {len(failed)}")
            print(f"📊 Total:  {len(self.results)}")
            
            if failed:
                print("\n❌ Failed Checks:")
                print("-" * 70)
                for result in failed:
                    print(f"\n  Category: {result.category}")
                    print(f"  Message:  {result.message}")
                    if result.details:
                        print(f"  Details:  {result.details}")
            
            if passed and not self.verbose:
                print("\n✅ Passed Categories:")
                categories = set(r.category for r in passed)
                for cat in sorted(categories):
                    print(f"  • {cat}")
            
            print("\n" + "="*70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate centralized configuration system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--category",
        "-c",
        help="Validate specific category only (redis, database, api, camera, radar, weather, logging, consolidator, maintenance, security)",
        choices=["redis", "database", "api", "camera", "radar", "weather", "logging", "consolidator", "maintenance", "security"]
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with detailed checks"
    )
    
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = ConfigValidator(verbose=args.verbose)
    
    # Run validation
    if args.category:
        success = validator.validate_category(args.category)
    else:
        success = validator.validate_all()
    
    # Print summary
    validator.print_summary(json_output=args.json)
    
    # Exit with appropriate code
    if success:
        sys.exit(0)
    else:
        failed = [r for r in validator.results if not r.passed]
        if any("empty" in r.message or "cannot be" in r.message for r in failed):
            sys.exit(2)  # Missing required variables
        else:
            sys.exit(3)  # Invalid configuration values


if __name__ == "__main__":
    main()
