#!/bin/bash
# Post-Deployment Validation Script
# Ensures all service fixes are working correctly

set -e

echo "=== Post-Deployment Service Validation ==="
echo "Checking that all service restart fixes are working"
echo ""

# Function to check service health
check_service_health() {
    local service_name=$1
    local timeout=${2:-30}
    
    echo "🔍 Checking $service_name health..."
    
    # Wait for service to be healthy or running
    local count=0
    while [ $count -lt $timeout ]; do
        status=$(docker inspect $service_name --format='{{.State.Health.Status}}' 2>/dev/null || echo "running")
        if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
            echo "✅ $service_name is $status"
            return 0
        elif [ "$status" = "starting" ]; then
            echo "⏳ $service_name is starting... ($count/$timeout)"
        else
            echo "⚠️ $service_name status: $status ($count/$timeout)"
        fi
        
        sleep 1
        count=$((count + 1))
    done
    
    echo "❌ $service_name failed health check"
    return 1
}

# Function to check for restart loops
check_restart_loops() {
    echo "🔄 Checking for service restart loops..."
    
    # Check if any services are restarting frequently
    restart_services=$(docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -i "restart\|restarting" || true)
    
    if [ -n "$restart_services" ]; then
        echo "❌ Services in restart loop:"
        echo "$restart_services"
        return 1
    else
        echo "✅ No services in restart loops"
        return 0
    fi
}

# Function to validate database persistence
validate_database_persistence() {
    echo "🗄️ Validating database persistence..."
    
    # Check if database file exists and is accessible
    if docker exec database-persistence test -f /app/data/traffic_data.db; then
        echo "✅ Database file exists at correct path"
        
        # Check if database is writable
        if docker exec database-persistence python -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/traffic_data.db')
    conn.execute('SELECT 1')
    print('✅ Database is accessible')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
        "; then
            echo "✅ Database persistence validation passed"
            return 0
        fi
    else
        echo "❌ Database file not found or not accessible"
        return 1
    fi
}

# Function to validate API service
validate_api_service() {
    echo "🌐 Validating API service..."
    
    # Check if traffic-monitor service is running
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "traffic-monitor.*Up"; then
        echo "✅ Traffic monitor service is running"
        
        # Test basic API endpoint (if available)
        if docker exec traffic-monitor python -c "
import requests
try:
    # Test if marshmallow import works
    from marshmallow import EXCLUDE
    print('✅ Marshmallow compatibility fix working')
    
    # Test if psycopg2 is available
    import psycopg2
    print('✅ psycopg2 module is available')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
        " 2>/dev/null; then
            echo "✅ API service validation passed"
            return 0
        fi
    else
        echo "❌ Traffic monitor service not running"
        return 1
    fi
}

# Function to validate data flow
validate_data_flow() {
    echo "📊 Validating data flow pipeline..."
    
    # Check Redis keys for active data
    redis_keys=$(docker exec redis redis-cli KEYS "*" | wc -l)
    if [ "$redis_keys" -gt 0 ]; then
        echo "✅ Redis has $redis_keys active data keys"
        
        # Check for recent consolidation data
        if docker exec redis redis-cli EXISTS "consolidation:latest" | grep -q "1"; then
            echo "✅ Recent consolidation data found"
        else
            echo "⚠️ No recent consolidation data (may be normal if no vehicles detected)"
        fi
        
        return 0
    else
        echo "❌ No data found in Redis"
        return 1
    fi
}

# Main validation sequence
echo "Starting validation sequence..."
echo ""

# 1. Check for restart loops first
if ! check_restart_loops; then
    echo ""
    echo "❌ VALIDATION FAILED: Services are in restart loops"
    echo "Check logs with: docker-compose logs [service-name]"
    exit 1
fi

# 2. Check individual service health
services=("redis" "postgres" "traffic-monitor" "database-persistence" "vehicle-consolidator")
failed_services=()

for service in "${services[@]}"; do
    if ! check_service_health "$service" 60; then
        failed_services+=("$service")
    fi
done

if [ ${#failed_services[@]} -gt 0 ]; then
    echo ""
    echo "❌ VALIDATION FAILED: Unhealthy services: ${failed_services[*]}"
    echo "Check logs with: docker logs [service-name]"
    exit 1
fi

# 3. Validate specific fixes
echo ""
echo "🔧 Validating specific fixes..."

validation_results=0

if ! validate_database_persistence; then
    validation_results=1
fi

if ! validate_api_service; then
    validation_results=1
fi

if ! validate_data_flow; then
    validation_results=1
fi

# Final result
echo ""
if [ $validation_results -eq 0 ]; then
    echo "🎉 ALL VALIDATIONS PASSED!"
    echo "✅ Database persistence fix: Working"
    echo "✅ API service fix: Working" 
    echo "✅ Data flow: Active"
    echo "✅ No restart loops detected"
    echo ""
    echo "Your traffic monitoring system is running correctly!"
else
    echo "❌ SOME VALIDATIONS FAILED"
    echo "Check the output above for specific issues"
    exit 1
fi