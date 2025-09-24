#!/usr/bin/env python3
"""
Configuration Management for Edge API
Centralized configuration with environment-based overrides and validation
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    redis_host: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    redis_port: int = field(default_factory=lambda: int(os.getenv('REDIS_PORT', '6379')))
    redis_db: int = field(default_factory=lambda: int(os.getenv('REDIS_DB', '0')))
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv('REDIS_PASSWORD'))
    
    postgres_host: str = field(default_factory=lambda: os.getenv('POSTGRES_HOST', 'localhost'))
    postgres_port: int = field(default_factory=lambda: int(os.getenv('POSTGRES_PORT', '5432')))
    postgres_db: str = field(default_factory=lambda: os.getenv('POSTGRES_DB', 'traffic_monitoring'))
    postgres_user: str = field(default_factory=lambda: os.getenv('POSTGRES_USER', 'traffic_user'))
    postgres_password: str = field(default_factory=lambda: os.getenv('POSTGRES_PASSWORD', 'password'))


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = field(default_factory=lambda: os.getenv('API_HOST', '0.0.0.0'))
    port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '5010')))
    debug: bool = field(default_factory=lambda: os.getenv('API_DEBUG', 'false').lower() == 'true')
    cors_enabled: bool = field(default_factory=lambda: os.getenv('CORS_ENABLED', 'true').lower() == 'true')
    cors_origins: str = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*'))
    rate_limit: str = field(default_factory=lambda: os.getenv('RATE_LIMIT', '100 per minute'))


@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'change-me-in-production'))
    jwt_secret: str = field(default_factory=lambda: os.getenv('JWT_SECRET', 'change-jwt-secret'))
    api_key_required: bool = field(default_factory=lambda: os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true')
    trusted_ips: list = field(default_factory=lambda: os.getenv('TRUSTED_IPS', '').split(',') if os.getenv('TRUSTED_IPS') else [])


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_path: Optional[str] = field(default_factory=lambda: os.getenv('LOG_FILE'))
    max_bytes: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_BYTES', '10485760')))  # 10MB
    backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))


@dataclass
class RadarConfig:
    """Radar data processing configuration"""
    stream_name: str = field(default_factory=lambda: os.getenv('RADAR_STREAM', 'radar_data'))
    detection_window_seconds: int = field(default_factory=lambda: int(os.getenv('RADAR_DETECTION_WINDOW', '5')))
    min_pings_per_vehicle: int = field(default_factory=lambda: int(os.getenv('RADAR_MIN_PINGS', '3')))
    max_speed_mph: float = field(default_factory=lambda: float(os.getenv('RADAR_MAX_SPEED', '100.0')))
    min_speed_mph: float = field(default_factory=lambda: float(os.getenv('RADAR_MIN_SPEED', '1.0')))
    speed_limit_mph: float = field(default_factory=lambda: float(os.getenv('SPEED_LIMIT', '25.0')))


@dataclass
class AppConfig:
    """Main application configuration container"""
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    radar: RadarConfig = field(default_factory=RadarConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
        
    def _validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate port ranges
        if not (1 <= self.api.port <= 65535):
            errors.append(f"Invalid API port: {self.api.port}")
            
        if not (1 <= self.database.redis_port <= 65535):
            errors.append(f"Invalid Redis port: {self.database.redis_port}")
            
        # Validate radar settings
        if self.radar.min_speed_mph >= self.radar.max_speed_mph:
            errors.append("Radar min_speed must be less than max_speed")
            
        # Validate security in production
        if self.environment == 'production':
            if self.security.secret_key == 'change-me-in-production':
                errors.append("SECRET_KEY must be changed in production")
                
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for logging/debugging)"""
        config_dict = {}
        for field_name, field_def in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if hasattr(value, '__dataclass_fields__'):
                # Nested dataclass
                config_dict[field_name] = value.__dict__.copy()
                # Redact sensitive information
                if field_name == 'security':
                    for key in ['secret_key', 'jwt_secret']:
                        if key in config_dict[field_name]:
                            config_dict[field_name][key] = '***REDACTED***'
                elif field_name == 'database':
                    if 'redis_password' in config_dict[field_name]:
                        config_dict[field_name]['redis_password'] = '***REDACTED***' if config_dict[field_name]['redis_password'] else None
                    if 'postgres_password' in config_dict[field_name]:
                        config_dict[field_name]['postgres_password'] = '***REDACTED***'
            else:
                config_dict[field_name] = value
        return config_dict


# Global configuration instance
config = AppConfig()


def load_config_from_file(config_path: str) -> AppConfig:
    """Load configuration from JSON file with environment overrides"""
    import json
    
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
            
            # Set environment variables from file (if not already set)
            for section, values in file_config.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        env_key = f"{section.upper()}_{key.upper()}"
                        if env_key not in os.environ:
                            os.environ[env_key] = str(value)
            
            logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
    
    return AppConfig()


def setup_logging(config: LoggingConfig):
    """Configure application logging based on configuration"""
    import logging.handlers
    
    # Set logging level
    level = getattr(logging, config.level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    # File handler (if specified)
    if config.file_path:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                config.file_path,
                maxBytes=config.max_bytes,
                backupCount=config.backup_count
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
            logger.info(f"Logging to file: {config.file_path}")
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")


# Initialize logging with current configuration
setup_logging(config.logging)

logger.info("Configuration loaded successfully")
if config.debug:
    logger.debug(f"Configuration: {config.to_dict()}")