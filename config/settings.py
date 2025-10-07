"""
Centralized Configuration Management for Vehicle Detection System

This module provides environment-based configuration with validation,
type checking, and clear documentation of all settings.

Usage:
    from config.settings import get_config
    
    config = get_config()
    redis_host = config.redis.host
    db_path = config.database.path
"""

import os
from typing import Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RedisConfig:
    """Redis connection and caching configuration"""
    host: str = field(default="redis")
    port: int = field(default=6379)
    db: int = field(default=0)
    password: Optional[str] = field(default=None)
    socket_timeout: int = field(default=5)
    socket_connect_timeout: int = field(default=5)
    max_connections: int = field(default=50)
    
    # Redis key patterns
    weather_key: str = field(default="weather:dht22")
    radar_channel: str = field(default="radar:detections")
    camera_channel: str = field(default="camera:detections")
    consolidated_channel: str = field(default="consolidated:detections")
    
    # Redis optimization settings
    optimization_interval: int = field(default=3600)  # 1 hour
    memory_threshold_mb: int = field(default=1000)  # 1GB threshold
    
    def __post_init__(self):
        """Validate Redis configuration"""
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid Redis port: {self.port}")
        if not 0 <= self.db <= 15:
            raise ValueError(f"Invalid Redis DB index: {self.db}")
        if self.optimization_interval < 60:
            raise ValueError(f"Optimization interval must be >= 60 seconds, got {self.optimization_interval}")
        if self.memory_threshold_mb < 100:
            raise ValueError(f"Memory threshold must be >= 100 MB, got {self.memory_threshold_mb}")


@dataclass
class DatabaseConfig:
    """Database configuration for SQLite"""
    path: str = field(default="/app/data/traffic_data.db")
    batch_size: int = field(default=100)
    commit_interval_seconds: int = field(default=30)
    retention_days: int = field(default=90)
    backup_enabled: bool = field(default=True)
    backup_interval_hours: int = field(default=24)
    
    def __post_init__(self):
        """Validate database configuration"""
        if self.batch_size < 1:
            raise ValueError(f"Batch size must be >= 1, got {self.batch_size}")
        if self.commit_interval_seconds < 1:
            raise ValueError(f"Commit interval must be >= 1, got {self.commit_interval_seconds}")
        if self.retention_days < 1:
            raise ValueError(f"Retention days must be >= 1, got {self.retention_days}")


@dataclass
class APIConfig:
    """API Gateway configuration"""
    host: str = field(default="0.0.0.0")
    port: int = field(default=5000)
    debug: bool = field(default=False)
    workers: int = field(default=4)
    cors_enabled: bool = field(default=True)
    cors_origins: str = field(default="*")
    rate_limit_enabled: bool = field(default=True)
    rate_limit_per_minute: int = field(default=60)
    
    # API endpoints
    swagger_enabled: bool = field(default=True)
    swagger_url: str = field(default="/docs")
    
    def __post_init__(self):
        """Validate API configuration"""
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid API port: {self.port}")
        if self.workers < 1:
            raise ValueError(f"Workers must be >= 1, got {self.workers}")


@dataclass
class CameraConfig:
    """IMX500 Camera configuration"""
    capture_dir: str = field(default="/mnt/storage/camera_capture")
    model_path: str = field(default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    capture_interval: float = field(default=1.0)
    confidence_threshold: float = field(default=0.5)
    max_stored_images: int = field(default=100)
    
    # Region of Interest (ROI) for street view
    roi_x_start: float = field(default=0.15)  # 15% from left
    roi_x_end: float = field(default=0.85)    # 85% from left
    roi_y_start: float = field(default=0.5)   # 50% from top (exclude cross street)
    roi_y_end: float = field(default=0.9)     # 90% from top
    
    # Snapshot configuration
    snapshot_enabled: bool = field(default=True)
    snapshot_interval_minutes: int = field(default=10)
    snapshot_path: Optional[str] = field(default=None)
    
    def __post_init__(self):
        """Validate camera configuration"""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"Confidence threshold must be 0.0-1.0, got {self.confidence_threshold}")
        if self.capture_interval < 0.1:
            raise ValueError(f"Capture interval must be >= 0.1, got {self.capture_interval}")
        if not (0.0 <= self.roi_x_start < self.roi_x_end <= 1.0):
            raise ValueError(f"Invalid ROI X coordinates: {self.roi_x_start} to {self.roi_x_end}")
        if not (0.0 <= self.roi_y_start < self.roi_y_end <= 1.0):
            raise ValueError(f"Invalid ROI Y coordinates: {self.roi_y_start} to {self.roi_y_end}")


@dataclass
class RadarConfig:
    """OPS243 Radar configuration"""
    uart_port: str = field(default="/dev/ttyAMA0")
    baud_rate: int = field(default=19200)
    timeout: float = field(default=1.0)
    
    # Detection settings
    speed_units: Literal["mph", "kph", "mps"] = field(default="mph")
    direction_control: bool = field(default=True)
    min_speed_threshold: float = field(default=5.0)  # Minimum speed to report
    max_speed_threshold: float = field(default=100.0)  # Maximum reasonable speed
    
    def __post_init__(self):
        """Validate radar configuration"""
        if self.baud_rate not in [9600, 19200, 38400, 57600, 115200]:
            raise ValueError(f"Invalid baud rate: {self.baud_rate}")
        if not 0 < self.min_speed_threshold < self.max_speed_threshold:
            raise ValueError(f"Invalid speed thresholds: {self.min_speed_threshold} to {self.max_speed_threshold}")


@dataclass
class WeatherConfig:
    """DHT22 Weather Sensor configuration"""
    gpio_pin: int = field(default=4)
    update_interval_seconds: int = field(default=600)  # 10 minutes
    temperature_unit: Literal["celsius", "fahrenheit"] = field(default="celsius")
    
    # Validation ranges
    temp_min_celsius: float = field(default=-40.0)
    temp_max_celsius: float = field(default=80.0)
    humidity_min: float = field(default=0.0)
    humidity_max: float = field(default=100.0)
    
    def __post_init__(self):
        """Validate weather configuration"""
        if not 1 <= self.gpio_pin <= 27:
            raise ValueError(f"Invalid GPIO pin: {self.gpio_pin}")
        if self.update_interval_seconds < 60:
            raise ValueError(f"Update interval must be >= 60 seconds, got {self.update_interval_seconds}")


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = field(default="INFO")
    format: str = field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # File logging
    file_enabled: bool = field(default=True)
    file_path: str = field(default="/var/log/vehicle-detection")
    file_max_bytes: int = field(default=10485760)  # 10MB
    file_backup_count: int = field(default=5)
    
    # Centralized logging (optional)
    central_logging_enabled: bool = field(default=False)
    central_logging_url: Optional[str] = field(default=None)
    
    # Business event logging
    business_events_enabled: bool = field(default=True)
    
    def __post_init__(self):
        """Validate logging configuration"""
        if self.file_max_bytes < 1024:
            raise ValueError(f"File max bytes must be >= 1024, got {self.file_max_bytes}")


@dataclass
class MaintenanceConfig:
    """System maintenance configuration"""
    # Disk space thresholds
    warning_threshold_percent: float = field(default=80.0)
    emergency_threshold_percent: float = field(default=90.0)
    
    # File retention (hours unless specified)
    image_max_age_hours: float = field(default=24.0)
    snapshot_max_age_hours: float = field(default=168.0)  # 1 week
    processed_max_age_hours: float = field(default=48.0)
    log_max_age_days: int = field(default=30)
    log_max_size_mb: int = field(default=50)
    
    # Count limits
    max_live_images: int = field(default=500)
    max_processed_images: int = field(default=200)
    max_snapshots: int = field(default=100)
    
    def __post_init__(self):
        """Validate maintenance configuration"""
        if not 0 < self.warning_threshold_percent < self.emergency_threshold_percent <= 100:
            raise ValueError(f"Invalid threshold percentages")


@dataclass
class SecurityConfig:
    """Security configuration"""
    # JWT settings
    jwt_secret: Optional[str] = field(default=None)
    jwt_algorithm: str = field(default="HS256")
    jwt_expiration_hours: int = field(default=24)
    
    # Flask secret
    secret_key: Optional[str] = field(default=None)
    
    # HTTPS settings
    https_enabled: bool = field(default=False)
    cert_path: Optional[str] = field(default=None)
    key_path: Optional[str] = field(default=None)
    
    def __post_init__(self):
        """Validate security configuration - secrets checked at runtime"""
        pass


@dataclass
class Config:
    """Main configuration object containing all subsystems"""
    environment: Literal["development", "production", "testing"] = field(default="production")
    
    # Subsystem configurations
    redis: RedisConfig = field(default_factory=RedisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    radar: RadarConfig = field(default_factory=RadarConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    maintenance: MaintenanceConfig = field(default_factory=MaintenanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # System info
    location_id: str = field(default="default_location")
    timezone: str = field(default="America/Phoenix")
    
    def validate(self) -> list[str]:
        """
        Validate the entire configuration and return list of errors.
        Returns empty list if valid.
        """
        errors = []
        
        # Check required secrets in production
        if self.environment == "production":
            if not self.security.secret_key:
                errors.append("SECRET_KEY is required in production")
            if not self.security.jwt_secret:
                errors.append("JWT_SECRET is required in production")
        
        # Validate paths exist or are writable
        if self.logging.file_enabled:
            log_dir = Path(self.logging.file_path).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory {log_dir}: {e}")
        
        return errors


def load_config_from_env() -> Config:
    """
    Load configuration from environment variables.
    Uses sensible defaults for all values.
    """
    
    def get_bool(key: str, default: bool) -> bool:
        """Parse boolean from environment"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_int(key: str, default: int) -> int:
        """Parse integer from environment"""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_float(key: str, default: float) -> float:
        """Parse float from environment"""
        try:
            return float(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    # Build configuration from environment
    config = Config(
        environment=os.getenv("ENVIRONMENT", "production"),
        location_id=os.getenv("LOCATION_ID", "default_location"),
        timezone=os.getenv("TIMEZONE", "America/Phoenix"),
        
        redis=RedisConfig(
            host=os.getenv("REDIS_HOST", "redis"),
            port=get_int("REDIS_PORT", 6379),
            db=get_int("REDIS_DB", 0),
            password=os.getenv("REDIS_PASSWORD"),
            max_connections=get_int("REDIS_MAX_CONNECTIONS", 50),
            weather_key=os.getenv("DHT22_REDIS_KEY", "weather:dht22"),
            optimization_interval=get_int("OPTIMIZATION_INTERVAL", 3600),
            memory_threshold_mb=get_int("MEMORY_THRESHOLD_MB", 1000),
        ),
        
        database=DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "/app/data/traffic_data.db"),
            batch_size=get_int("BATCH_SIZE", 100),
            commit_interval_seconds=get_int("COMMIT_INTERVAL_SEC", 30),
            retention_days=get_int("RETENTION_DAYS", 90),
        ),
        
        api=APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=get_int("API_PORT", 5000),
            debug=get_bool("API_DEBUG", False),
            workers=get_int("API_WORKERS", 4),
            swagger_enabled=get_bool("SWAGGER_ENABLED", True),
        ),
        
        camera=CameraConfig(
            capture_dir=os.getenv("CAMERA_CAPTURE_DIR", "/mnt/storage/camera_capture"),
            model_path=os.getenv("IMX500_MODEL_PATH", "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"),
            capture_interval=get_float("CAPTURE_INTERVAL", 1.0),
            confidence_threshold=get_float("AI_CONFIDENCE_THRESHOLD", 0.5),
            max_stored_images=get_int("MAX_STORED_IMAGES", 100),
            roi_x_start=get_float("STREET_ROI_X_START", 0.15),
            roi_x_end=get_float("STREET_ROI_X_END", 0.85),
            roi_y_start=get_float("STREET_ROI_Y_START", 0.5),
            roi_y_end=get_float("STREET_ROI_Y_END", 0.9),
            snapshot_interval_minutes=get_int("SNAPSHOT_INTERVAL_MINUTES", 10),
            snapshot_path=os.getenv("PERIODIC_SNAPSHOT_PATH"),
        ),
        
        radar=RadarConfig(
            uart_port=os.getenv("RADAR_UART_PORT", "/dev/ttyAMA0"),
            baud_rate=get_int("RADAR_BAUD_RATE", 19200),
            speed_units=os.getenv("RADAR_SPEED_UNITS", "mph"),
        ),
        
        weather=WeatherConfig(
            gpio_pin=get_int("DHT22_GPIO_PIN", 4),
            update_interval_seconds=get_int("DHT22_UPDATE_INTERVAL", 600),
        ),
        
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_DIR", "/var/log/vehicle-detection"),
            central_logging_enabled=get_bool("ENABLE_LOG_SHIPPING", False),
            central_logging_url=os.getenv("CENTRAL_LOG_URL"),
        ),
        
        maintenance=MaintenanceConfig(
            warning_threshold_percent=get_float("MAINTENANCE_WARNING_THRESHOLD", 80.0),
            emergency_threshold_percent=get_float("MAINTENANCE_EMERGENCY_THRESHOLD", 90.0),
            image_max_age_hours=get_float("MAINTENANCE_IMAGE_MAX_AGE_HOURS", 24.0),
            snapshot_max_age_hours=get_float("MAINTENANCE_SNAPSHOT_MAX_AGE_HOURS", 168.0),
            max_live_images=get_int("MAINTENANCE_MAX_LIVE_IMAGES", 500),
        ),
        
        security=SecurityConfig(
            secret_key=os.getenv("SECRET_KEY"),
            jwt_secret=os.getenv("JWT_SECRET"),
            https_enabled=get_bool("HTTPS_ENABLED", False),
            cert_path=os.getenv("HTTPS_CERT_PATH"),
            key_path=os.getenv("HTTPS_KEY_PATH"),
        ),
    )
    
    return config


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    Loads from environment on first call.
    """
    global _config
    if _config is None:
        _config = load_config_from_env()
        
        # Validate and warn about issues
        errors = _config.validate()
        if errors:
            import sys
            print("⚠️  Configuration Errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            if _config.environment == "production":
                print("❌ Cannot start in production with configuration errors", file=sys.stderr)
                sys.exit(1)
    
    return _config


def reload_config():
    """
    Force reload of configuration from environment.
    Useful for testing or when environment changes.
    """
    global _config
    _config = None
    return get_config()


if __name__ == "__main__":
    # Test configuration loading
    print("Loading configuration...")
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Redis: {config.redis.host}:{config.redis.port}")
    print(f"Database: {config.database.path}")
    print(f"API: {config.api.host}:{config.api.port}")
    print("✅ Configuration loaded successfully!")
