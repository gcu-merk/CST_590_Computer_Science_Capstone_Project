#!/usr/bin/env python3
"""
Error Handling and Exception Management for Edge API
Standardized error responses and exception handling
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from functools import wraps
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException
import redis
from datetime import datetime

# Optional PostgreSQL support - only import if available
try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    psycopg2 = None
    POSTGRESQL_AVAILABLE = False

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception class for API errors"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            'error': {
                'message': self.message,
                'status_code': self.status_code,
                'details': self.details,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'path': getattr(request, 'path', 'unknown') if request else 'unknown'
            }
        }


class ValidationError(APIError):
    """Exception for input validation errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['invalid_value'] = str(value)
        super().__init__(message, status_code=400, details=details)


class DataSourceError(APIError):
    """Exception for data source connection/query errors"""
    
    def __init__(self, message: str, source: str, operation: str = None):
        details = {'data_source': source}
        if operation:
            details['operation'] = operation
        super().__init__(message, status_code=503, details=details)


class NotFoundError(APIError):
    """Exception for resource not found errors"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        details = {'resource_type': resource_type}
        if resource_id:
            details['resource_id'] = resource_id
        super().__init__(message, status_code=404, details=details)


class RateLimitError(APIError):
    """Exception for rate limiting errors"""
    
    def __init__(self, limit: str, retry_after: int = None):
        message = f"Rate limit exceeded: {limit}"
        details = {'rate_limit': limit}
        if retry_after:
            details['retry_after_seconds'] = retry_after
        super().__init__(message, status_code=429, details=details)


def handle_api_error(error: APIError):
    """Handle APIError exceptions and return JSON response"""
    logger.warning(f"API Error: {error.message} (Status: {error.status_code})")
    if error.details:
        logger.debug(f"Error details: {error.details}")
    
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_http_error(error: HTTPException):
    """Handle standard HTTP exceptions"""
    logger.warning(f"HTTP Error: {error.description} (Status: {error.code})")
    
    api_error = APIError(
        message=error.description or f"HTTP {error.code} Error",
        status_code=error.code,
        details={'http_exception': error.name}
    )
    
    response = jsonify(api_error.to_dict())
    response.status_code = error.code
    return response


def handle_generic_error(error: Exception):
    """Handle unexpected exceptions"""
    error_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    
    logger.error(f"Unexpected error [{error_id}]: {str(error)}")
    logger.error(f"Traceback [{error_id}]:\n{traceback.format_exc()}")
    
    # Don't expose internal errors in production
    if current_app and current_app.config.get('ENV') == 'production':
        message = "An internal server error occurred"
        details = {'error_id': error_id}
    else:
        message = str(error)
        details = {
            'error_id': error_id,
            'exception_type': type(error).__name__,
            'traceback': traceback.format_exc().split('\n')
        }
    
    api_error = APIError(message=message, status_code=500, details=details)
    response = jsonify(api_error.to_dict())
    response.status_code = 500
    return response


def safe_redis_operation(operation_name: str = "Redis operation"):
    """Decorator to safely handle Redis operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error in {operation_name}: {e}")
                raise DataSourceError(
                    "Database connection unavailable", 
                    source="Redis",
                    operation=operation_name
                )
            except redis.TimeoutError as e:
                logger.error(f"Redis timeout in {operation_name}: {e}")
                raise DataSourceError(
                    "Database operation timed out",
                    source="Redis", 
                    operation=operation_name
                )
            except redis.RedisError as e:
                logger.error(f"Redis error in {operation_name}: {e}")
                raise DataSourceError(
                    f"Database operation failed: {str(e)}",
                    source="Redis",
                    operation=operation_name
                )
        return wrapper
    return decorator


def safe_postgres_operation(operation_name: str = "PostgreSQL operation"):
    """Decorator to safely handle PostgreSQL operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Handle PostgreSQL errors if psycopg2 is available
                if POSTGRESQL_AVAILABLE and psycopg2:
                    if isinstance(e, psycopg2.OperationalError):
                        logger.error(f"PostgreSQL connection error in {operation_name}: {e}")
                        raise DataSourceError(
                            "Database connection unavailable",
                            source="PostgreSQL",
                            operation=operation_name
                        )
                    elif isinstance(e, psycopg2.DatabaseError):
                        logger.error(f"PostgreSQL error in {operation_name}: {e}")
                        raise DataSourceError(
                            f"Database operation failed: {str(e)}",
                            source="PostgreSQL",
                            operation=operation_name
                        )
                
                # Re-raise other exceptions
                raise
        return wrapper
    return decorator


def validate_time_period(period: Union[str, int], min_seconds: int = 60, max_seconds: int = 604800) -> int:
    """Validate and convert time period parameter to seconds
    
    Args:
        period: Time period as string ('hour', 'day', 'week') or integer (seconds)
        min_seconds: Minimum allowed period in seconds (default: 1 minute)
        max_seconds: Maximum allowed period in seconds (default: 1 week)
        
    Returns:
        int: Period in seconds
        
    Raises:
        ValidationError: If period is invalid
    """
    try:
        if isinstance(period, str):
            period_map = {
                'hour': 3600,
                'day': 86400,
                'week': 604800,
                'minute': 60
            }
            if period.lower() not in period_map:
                raise ValidationError(
                    f"Invalid time period '{period}'. Must be one of: {', '.join(period_map.keys())}",
                    field='period',
                    value=period
                )
            seconds = period_map[period.lower()]
        else:
            seconds = int(period)
            
        if seconds < min_seconds:
            raise ValidationError(
                f"Time period too short. Minimum: {min_seconds} seconds",
                field='period',
                value=period
            )
            
        if seconds > max_seconds:
            raise ValidationError(
                f"Time period too long. Maximum: {max_seconds} seconds",
                field='period', 
                value=period
            )
            
        return seconds
        
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid time period format: {period}",
            field='period',
            value=period
        )


def validate_pagination(page: Any = None, per_page: Any = None, max_per_page: int = 1000) -> tuple:
    """Validate pagination parameters
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum items per page allowed
        
    Returns:
        tuple: (page, per_page) as integers
        
    Raises:
        ValidationError: If pagination parameters are invalid
    """
    # Default values
    page = page or 1
    per_page = per_page or 50
    
    try:
        page = int(page)
        per_page = int(per_page)
    except (ValueError, TypeError):
        raise ValidationError("Page and per_page must be integers")
    
    if page < 1:
        raise ValidationError("Page must be >= 1", field='page', value=page)
        
    if per_page < 1:
        raise ValidationError("Per_page must be >= 1", field='per_page', value=per_page)
        
    if per_page > max_per_page:
        raise ValidationError(
            f"Per_page too large. Maximum: {max_per_page}",
            field='per_page',
            value=per_page
        )
    
    return page, per_page


def validate_speed_range(min_speed: Any = None, max_speed: Any = None) -> tuple:
    """Validate speed range parameters
    
    Args:
        min_speed: Minimum speed in mph
        max_speed: Maximum speed in mph
        
    Returns:
        tuple: (min_speed, max_speed) as floats or None
        
    Raises:
        ValidationError: If speed range is invalid
    """
    if min_speed is not None:
        try:
            min_speed = float(min_speed)
            if min_speed < 0:
                raise ValidationError("Minimum speed cannot be negative", field='min_speed', value=min_speed)
        except (ValueError, TypeError):
            raise ValidationError("Invalid minimum speed format", field='min_speed', value=min_speed)
    
    if max_speed is not None:
        try:
            max_speed = float(max_speed)
            if max_speed < 0:
                raise ValidationError("Maximum speed cannot be negative", field='max_speed', value=max_speed)
        except (ValueError, TypeError):
            raise ValidationError("Invalid maximum speed format", field='max_speed', value=max_speed)
    
    if min_speed is not None and max_speed is not None:
        if min_speed >= max_speed:
            raise ValidationError(
                "Minimum speed must be less than maximum speed",
                field='speed_range'
            )
    
    return min_speed, max_speed


def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_exception(error):
        return handle_api_error(error)
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return handle_http_error(error)
    
    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        return handle_generic_error(error)
    
    logger.info("Error handlers registered successfully")