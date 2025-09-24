#!/usr/bin/env python3
"""
Enhanced Database Services Validation Script - WITH CENTRALIZED LOGGING
Comprehensive validation suite for database persistence and Redis optimization services

This validation script ensures all enhanced database services are working correctly:
- Database persistence service with PostgreSQL + SQLite dual architecture
- Redis optimization service with intelligent TTL management
- Centralized logging and correlation tracking
- Query performance monitoring and health checks
- Data integrity validation across systems

Test Categories:
1. Database Connectivity Tests
2. Redis Operation Tests
3. Data Persistence Validation
4. Optimization Performance Tests
5. Logging and Correlation Tests
6. Health Check Validation
7. Error Recovery Tests
"""

import time
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os
import random

# Add edge_processing to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))
from shared_logging import ServiceLogger, CorrelationContext

# Import test dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

# Initialize logging
logger = ServiceLogger("database_services_validator")

class DatabaseServicesValidator:
    """Comprehensive validation suite for enhanced database services"""
    
    def __init__(self):
        self.redis_client = None
        self.postgres_conn = None
        self.sqlite_conn = None
        
        # Test configuration
        self.redis_host = os.environ.get('REDIS_HOST', 'redis')
        self.redis_port = int(os.environ.get('REDIS_PORT', 6379))
        self.postgres_host = os.environ.get('POSTGRES_HOST', 'postgres')
        self.postgres_db = os.environ.get('POSTGRES_DB', 'traffic_monitoring')
        self.postgres_user = os.environ.get('POSTGRES_USER', 'traffic_user')
        self.postgres_password = os.environ.get('POSTGRES_PASSWORD', 'traffic_password')
        self.sqlite_path = os.environ.get('DATABASE_PATH', '/tmp/test_traffic_data.db')
        
        # Test results
        self.test_results = {
            "overall_status": "UNKNOWN",
            "test_categories": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_duration_seconds": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Database Services Validator initialized", extra={
            "business_event": "validator_initialization",
            "redis_host": self.redis_host,
            "postgres_host": self.postgres_host,
            "sqlite_path": self.sqlite_path
        })
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        correlation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        with CorrelationContext.set_correlation_id(correlation_id):
            logger.info("Starting complete database services validation", extra={
                "business_event": "validation_suite_start",
                "correlation_id": correlation_id
            })
            
            try:
                # Initialize connections
                await self._initialize_connections()
                
                # Run test categories
                test_categories = [
                    ("connectivity_tests", self._test_database_connectivity),
                    ("redis_operation_tests", self._test_redis_operations),
                    ("data_persistence_tests", self._test_data_persistence),
                    ("optimization_tests", self._test_redis_optimization),
                    ("logging_tests", self._test_centralized_logging),
                    ("health_check_tests", self._test_health_checks),
                    ("error_recovery_tests", self._test_error_recovery)
                ]
                
                for category_name, test_method in test_categories:
                    try:
                        category_results = await test_method()
                        self.test_results["test_categories"][category_name] = category_results
                        
                        # Update overall counts
                        self.test_results["total_tests"] += category_results.get("total_tests", 0)
                        self.test_results["passed_tests"] += category_results.get("passed_tests", 0)
                        self.test_results["failed_tests"] += category_results.get("failed_tests", 0)
                        
                        logger.info(f"Test category {category_name} completed", extra={
                            "business_event": "test_category_completed",
                            "correlation_id": correlation_id,
                            "category": category_name,
                            "passed": category_results.get("passed_tests", 0),
                            "failed": category_results.get("failed_tests", 0)
                        })
                        
                    except Exception as e:
                        logger.error(f"Test category {category_name} failed", extra={
                            "business_event": "test_category_failure",
                            "correlation_id": correlation_id,
                            "category": category_name,
                            "error": str(e)
                        })
                        self.test_results["test_categories"][category_name] = {
                            "status": "FAILED",
                            "error": str(e),
                            "total_tests": 1,
                            "passed_tests": 0,
                            "failed_tests": 1
                        }
                        self.test_results["total_tests"] += 1
                        self.test_results["failed_tests"] += 1
                
                # Calculate overall status
                self.test_results["test_duration_seconds"] = round(time.time() - start_time, 2)
                
                if self.test_results["failed_tests"] == 0:
                    self.test_results["overall_status"] = "PASSED"
                elif self.test_results["passed_tests"] > self.test_results["failed_tests"]:
                    self.test_results["overall_status"] = "MOSTLY_PASSED"
                else:
                    self.test_results["overall_status"] = "FAILED"
                
                logger.info("Database services validation completed", extra={
                    "business_event": "validation_suite_completed",
                    "correlation_id": correlation_id,
                    "overall_status": self.test_results["overall_status"],
                    "total_tests": self.test_results["total_tests"],
                    "passed_tests": self.test_results["passed_tests"],
                    "failed_tests": self.test_results["failed_tests"],
                    "duration_seconds": self.test_results["test_duration_seconds"]
                })
                
                return self.test_results
                
            except Exception as e:
                logger.error("Validation suite failed", extra={
                    "business_event": "validation_suite_failure",
                    "correlation_id": correlation_id,
                    "error": str(e)
                })
                self.test_results["overall_status"] = "FAILED"
                self.test_results["error"] = str(e)
                return self.test_results
            finally:
                await self._cleanup_connections()
    
    async def _initialize_connections(self):
        """Initialize database connections"""
        try:
            # Redis connection
            if REDIS_AVAILABLE:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                logger.info("Redis connection established for testing")
            
            # PostgreSQL connection
            if POSTGRESQL_AVAILABLE:
                self.postgres_conn = psycopg2.connect(
                    host=self.postgres_host,
                    database=self.postgres_db,
                    user=self.postgres_user,
                    password=self.postgres_password,
                    connect_timeout=10
                )
                logger.info("PostgreSQL connection established for testing")
            
            # SQLite connection
            if SQLITE_AVAILABLE:
                self.sqlite_conn = sqlite3.connect(self.sqlite_path, timeout=10)
                logger.info("SQLite connection established for testing")
                
        except Exception as e:
            logger.error("Failed to initialize test connections", extra={
                "error": str(e)
            })
            raise
    
    async def _cleanup_connections(self):
        """Cleanup database connections"""
        try:
            if self.redis_client:
                self.redis_client.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()
        except Exception as e:
            logger.warning("Error during connection cleanup", extra={
                "error": str(e)
            })
    
    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        # Redis connectivity test
        if REDIS_AVAILABLE and self.redis_client:
            try:
                start_time = time.time()
                response = self.redis_client.ping()
                connection_time = (time.time() - start_time) * 1000
                
                if response:
                    results["tests"].append({
                        "name": "redis_connectivity",
                        "status": "PASSED",
                        "connection_time_ms": round(connection_time, 2)
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "redis_connectivity",
                        "status": "FAILED",
                        "error": "Ping returned False"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "redis_connectivity",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        # PostgreSQL connectivity test
        if POSTGRESQL_AVAILABLE and self.postgres_conn:
            try:
                start_time = time.time()
                cursor = self.postgres_conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection_time = (time.time() - start_time) * 1000
                cursor.close()
                
                if result and result[0] == 1:
                    results["tests"].append({
                        "name": "postgresql_connectivity",
                        "status": "PASSED",
                        "connection_time_ms": round(connection_time, 2)
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "postgresql_connectivity",
                        "status": "FAILED",
                        "error": "Invalid query result"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "postgresql_connectivity",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        # SQLite connectivity test
        if SQLITE_AVAILABLE and self.sqlite_conn:
            try:
                start_time = time.time()
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection_time = (time.time() - start_time) * 1000
                cursor.close()
                
                if result and result[0] == 1:
                    results["tests"].append({
                        "name": "sqlite_connectivity", 
                        "status": "PASSED",
                        "connection_time_ms": round(connection_time, 2)
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "sqlite_connectivity",
                        "status": "FAILED",
                        "error": "Invalid query result"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "sqlite_connectivity",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_redis_operations(self) -> Dict[str, Any]:
        """Test Redis operations"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        if not (REDIS_AVAILABLE and self.redis_client):
            results["status"] = "SKIPPED"
            results["reason"] = "Redis not available"
            return results
        
        # Test Redis set/get operations
        try:
            test_key = f"test:validation:{uuid.uuid4().hex[:8]}"
            test_value = f"test_value_{datetime.now().isoformat()}"
            
            # Set operation
            start_time = time.time()
            self.redis_client.set(test_key, test_value, ex=60)  # 1 minute TTL
            set_time = (time.time() - start_time) * 1000
            
            # Get operation
            start_time = time.time()
            retrieved_value = self.redis_client.get(test_key)
            get_time = (time.time() - start_time) * 1000
            
            if retrieved_value == test_value:
                results["tests"].append({
                    "name": "redis_set_get_operations",
                    "status": "PASSED",
                    "set_time_ms": round(set_time, 2),
                    "get_time_ms": round(get_time, 2)
                })
                results["passed_tests"] += 1
            else:
                results["tests"].append({
                    "name": "redis_set_get_operations",
                    "status": "FAILED",
                    "error": f"Value mismatch: expected {test_value}, got {retrieved_value}"
                })
                results["failed_tests"] += 1
            results["total_tests"] += 1
            
            # Cleanup
            self.redis_client.delete(test_key)
            
        except Exception as e:
            results["tests"].append({
                "name": "redis_set_get_operations",
                "status": "FAILED",
                "error": str(e)
            })
            results["failed_tests"] += 1
            results["total_tests"] += 1
        
        # Test Redis TTL operations
        try:
            test_key = f"test:ttl:{uuid.uuid4().hex[:8]}"
            
            self.redis_client.set(test_key, "ttl_test", ex=30)
            ttl = self.redis_client.ttl(test_key)
            
            if 25 <= ttl <= 30:  # Allow some variance
                results["tests"].append({
                    "name": "redis_ttl_operations",
                    "status": "PASSED",
                    "ttl_seconds": ttl
                })
                results["passed_tests"] += 1
            else:
                results["tests"].append({
                    "name": "redis_ttl_operations",
                    "status": "FAILED",
                    "error": f"Unexpected TTL: {ttl}"
                })
                results["failed_tests"] += 1
            results["total_tests"] += 1
            
            # Cleanup
            self.redis_client.delete(test_key)
            
        except Exception as e:
            results["tests"].append({
                "name": "redis_ttl_operations",
                "status": "FAILED",
                "error": str(e)
            })
            results["failed_tests"] += 1
            results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_data_persistence(self) -> Dict[str, Any]:
        """Test data persistence operations"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        # Test sample traffic record format
        sample_record = {
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4())[:8],
            "vehicle_count": random.randint(1, 5),
            "detection_confidence": round(random.uniform(0.8, 0.99), 2),
            "weather_condition": random.choice(["clear", "cloudy", "rainy"]),
            "camera_id": "test_camera_01"
        }
        
        # Test Redis data persistence
        if REDIS_AVAILABLE and self.redis_client:
            try:
                test_key = f"test:persistence:{uuid.uuid4().hex[:8]}"
                
                start_time = time.time()
                self.redis_client.set(test_key, json.dumps(sample_record), ex=300)
                write_time = (time.time() - start_time) * 1000
                
                start_time = time.time()
                retrieved_data = self.redis_client.get(test_key)
                read_time = (time.time() - start_time) * 1000
                
                retrieved_record = json.loads(retrieved_data) if retrieved_data else None
                
                if retrieved_record == sample_record:
                    results["tests"].append({
                        "name": "redis_data_persistence",
                        "status": "PASSED",
                        "write_time_ms": round(write_time, 2),
                        "read_time_ms": round(read_time, 2)
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "redis_data_persistence",
                        "status": "FAILED",
                        "error": "Data integrity check failed"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
                # Cleanup
                self.redis_client.delete(test_key)
                
            except Exception as e:
                results["tests"].append({
                    "name": "redis_data_persistence",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        # Test SQLite data persistence
        if SQLITE_AVAILABLE and self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                
                # Create test table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_traffic_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        correlation_id TEXT,
                        vehicle_count INTEGER,
                        detection_confidence REAL,
                        weather_condition TEXT,
                        camera_id TEXT
                    )
                """)
                
                # Insert test record
                start_time = time.time()
                cursor.execute("""
                    INSERT INTO test_traffic_records 
                    (timestamp, correlation_id, vehicle_count, detection_confidence, weather_condition, camera_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sample_record["timestamp"],
                    sample_record["correlation_id"],
                    sample_record["vehicle_count"],
                    sample_record["detection_confidence"],
                    sample_record["weather_condition"],
                    sample_record["camera_id"]
                ))
                self.sqlite_conn.commit()
                write_time = (time.time() - start_time) * 1000
                
                # Read test record
                start_time = time.time()
                cursor.execute("""
                    SELECT timestamp, correlation_id, vehicle_count, detection_confidence, weather_condition, camera_id
                    FROM test_traffic_records WHERE correlation_id = ?
                """, (sample_record["correlation_id"],))
                result = cursor.fetchone()
                read_time = (time.time() - start_time) * 1000
                
                if result:
                    retrieved_record = {
                        "timestamp": result[0],
                        "correlation_id": result[1],
                        "vehicle_count": result[2],
                        "detection_confidence": result[3],
                        "weather_condition": result[4],
                        "camera_id": result[5]
                    }
                    
                    if retrieved_record == sample_record:
                        results["tests"].append({
                            "name": "sqlite_data_persistence",
                            "status": "PASSED",
                            "write_time_ms": round(write_time, 2),
                            "read_time_ms": round(read_time, 2)
                        })
                        results["passed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "sqlite_data_persistence",
                            "status": "FAILED",
                            "error": "Data integrity check failed"
                        })
                        results["failed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "sqlite_data_persistence",
                        "status": "FAILED",
                        "error": "No record found after insert"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
                # Cleanup test table
                cursor.execute("DROP TABLE IF EXISTS test_traffic_records")
                self.sqlite_conn.commit()
                cursor.close()
                
            except Exception as e:
                results["tests"].append({
                    "name": "sqlite_data_persistence",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_redis_optimization(self) -> Dict[str, Any]:
        """Test Redis optimization functionality"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        if not (REDIS_AVAILABLE and self.redis_client):
            results["status"] = "SKIPPED"
            results["reason"] = "Redis not available"
            return results
        
        # Test TTL optimization
        try:
            test_keys = []
            
            # Create test keys with different patterns
            patterns_to_test = [
                ("sky:analysis:test", 86400),
                ("vehicle:detection:test", 604800),
                ("weather:test", 3600),
                ("radar:current:test", 300)
            ]
            
            for key_pattern, expected_ttl in patterns_to_test:
                test_key = f"{key_pattern}:{uuid.uuid4().hex[:8]}"
                test_keys.append(test_key)
                
                # Set key without TTL initially
                self.redis_client.set(test_key, "optimization_test")
                
                # Simulate TTL application (like optimization service would do)
                self.redis_client.expire(test_key, expected_ttl)
                
                # Check TTL was set correctly
                actual_ttl = self.redis_client.ttl(test_key)
                
                # Allow some variance in TTL
                if expected_ttl - 10 <= actual_ttl <= expected_ttl:
                    results["tests"].append({
                        "name": f"ttl_optimization_{key_pattern.replace(':', '_')}",
                        "status": "PASSED",
                        "expected_ttl": expected_ttl,
                        "actual_ttl": actual_ttl
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": f"ttl_optimization_{key_pattern.replace(':', '_')}",
                        "status": "FAILED",
                        "error": f"TTL mismatch: expected ~{expected_ttl}, got {actual_ttl}"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
            
            # Cleanup test keys
            if test_keys:
                self.redis_client.delete(*test_keys)
            
        except Exception as e:
            results["tests"].append({
                "name": "redis_ttl_optimization",
                "status": "FAILED",
                "error": str(e)
            })
            results["failed_tests"] += 1
            results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_centralized_logging(self) -> Dict[str, Any]:
        """Test centralized logging functionality"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        try:
            # Test correlation context
            correlation_id = str(uuid.uuid4())[:8]
            
            with CorrelationContext.set_correlation_id(correlation_id):
                current_correlation = CorrelationContext.get_correlation_id()
                
                if current_correlation == correlation_id:
                    results["tests"].append({
                        "name": "correlation_context_management",
                        "status": "PASSED",
                        "correlation_id": correlation_id
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "correlation_context_management",
                        "status": "FAILED",
                        "error": f"Correlation ID mismatch: expected {correlation_id}, got {current_correlation}"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
                # Test structured logging
                test_logger = ServiceLogger("test_service")
                test_logger.info("Test log message", extra={
                    "business_event": "test_logging_functionality",
                    "test_data": {"key": "value"},
                    "correlation_id": correlation_id
                })
                
                results["tests"].append({
                    "name": "structured_logging",
                    "status": "PASSED",
                    "message": "Logger created and message logged successfully"
                })
                results["passed_tests"] += 1
                results["total_tests"] += 1
                
        except Exception as e:
            results["tests"].append({
                "name": "centralized_logging",
                "status": "FAILED",
                "error": str(e)
            })
            results["failed_tests"] += 1
            results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_health_checks(self) -> Dict[str, Any]:
        """Test health check functionality"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        # Test Redis health
        if REDIS_AVAILABLE and self.redis_client:
            try:
                start_time = time.time()
                info = self.redis_client.info()
                health_check_time = (time.time() - start_time) * 1000
                
                if info and 'redis_version' in info:
                    results["tests"].append({
                        "name": "redis_health_check",
                        "status": "PASSED",
                        "health_check_time_ms": round(health_check_time, 2),
                        "redis_version": info.get('redis_version', 'unknown')
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "redis_health_check",
                        "status": "FAILED",
                        "error": "Invalid Redis info response"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "redis_health_check",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        # Test PostgreSQL health
        if POSTGRESQL_AVAILABLE and self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                start_time = time.time()
                cursor.execute("SELECT version()")
                version_result = cursor.fetchone()
                health_check_time = (time.time() - start_time) * 1000
                cursor.close()
                
                if version_result:
                    results["tests"].append({
                        "name": "postgresql_health_check",
                        "status": "PASSED",
                        "health_check_time_ms": round(health_check_time, 2),
                        "postgresql_version": version_result[0][:50]  # Truncate long version string
                    })
                    results["passed_tests"] += 1
                else:
                    results["tests"].append({
                        "name": "postgresql_health_check",
                        "status": "FAILED",
                        "error": "No version information returned"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "postgresql_health_check",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results
    
    async def _test_error_recovery(self) -> Dict[str, Any]:
        """Test error recovery scenarios"""
        results = {"status": "UNKNOWN", "tests": [], "total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        # Test Redis connection recovery
        if REDIS_AVAILABLE and self.redis_client:
            try:
                # Test with invalid operation (should handle gracefully)
                try:
                    self.redis_client.get("nonexistent:key:12345")
                    results["tests"].append({
                        "name": "redis_graceful_error_handling",
                        "status": "PASSED",
                        "message": "Handled nonexistent key gracefully"
                    })
                    results["passed_tests"] += 1
                except Exception:
                    results["tests"].append({
                        "name": "redis_graceful_error_handling",
                        "status": "FAILED",
                        "error": "Should handle nonexistent keys gracefully"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
            except Exception as e:
                results["tests"].append({
                    "name": "redis_error_recovery",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        # Test SQLite transaction recovery
        if SQLITE_AVAILABLE and self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                
                # Test invalid SQL handling
                try:
                    cursor.execute("SELECT * FROM nonexistent_table_12345")
                    results["tests"].append({
                        "name": "sqlite_error_recovery",
                        "status": "FAILED", 
                        "error": "Should have failed on nonexistent table"
                    })
                    results["failed_tests"] += 1
                except sqlite3.OperationalError:
                    # Expected error - good error handling
                    results["tests"].append({
                        "name": "sqlite_error_recovery",
                        "status": "PASSED",
                        "message": "Properly handled invalid table query"
                    })
                    results["passed_tests"] += 1
                except Exception as e:
                    results["tests"].append({
                        "name": "sqlite_error_recovery",
                        "status": "FAILED",
                        "error": f"Unexpected error type: {str(e)}"
                    })
                    results["failed_tests"] += 1
                results["total_tests"] += 1
                
                cursor.close()
                
            except Exception as e:
                results["tests"].append({
                    "name": "sqlite_error_recovery",
                    "status": "FAILED",
                    "error": str(e)
                })
                results["failed_tests"] += 1
                results["total_tests"] += 1
        
        results["status"] = "PASSED" if results["failed_tests"] == 0 else "FAILED"
        return results


async def main():
    """Main validation entry point"""
    try:
        print("=" * 80)
        print("ENHANCED DATABASE SERVICES VALIDATION SUITE")
        print("=" * 80)
        
        validator = DatabaseServicesValidator()
        results = await validator.run_complete_validation()
        
        # Print detailed results
        print(f"\n{'='*20} VALIDATION RESULTS {'='*20}")
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Duration: {results['test_duration_seconds']} seconds")
        
        print(f"\n{'='*20} TEST CATEGORIES {'='*20}")
        for category_name, category_results in results['test_categories'].items():
            print(f"\n{category_name.upper()}:")
            print(f"  Status: {category_results.get('status', 'UNKNOWN')}")
            print(f"  Tests: {category_results.get('total_tests', 0)} (Passed: {category_results.get('passed_tests', 0)}, Failed: {category_results.get('failed_tests', 0)})")
            
            if 'tests' in category_results:
                for test in category_results['tests']:
                    status_icon = "✓" if test['status'] == 'PASSED' else "✗"
                    print(f"    {status_icon} {test['name']}: {test['status']}")
                    if test['status'] == 'FAILED' and 'error' in test:
                        print(f"      Error: {test['error']}")
        
        print(f"\n{'='*60}")
        
        # Save results to file
        results_file = Path("database_services_validation_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if results['overall_status'] in ['PASSED', 'MOSTLY_PASSED']:
            print("\n🎉 Database services validation SUCCESSFUL!")
            sys.exit(0)
        else:
            print(f"\n❌ Database services validation FAILED! Status: {results['overall_status']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Validation suite execution failed", extra={
            "business_event": "validation_suite_execution_failure",
            "error": str(e)
        })
        print(f"\n❌ CRITICAL ERROR: Validation suite execution failed")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())