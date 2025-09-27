#!/bin/bash
# SECURITY FIX: Remove dangerous external port exposures
# This script updates docker-compose.yml to remove external access to insecure services

echo "🔒 APPLYING SECURITY FIXES - REMOVING DANGEROUS EXTERNAL EXPOSURES"
echo "=================================================================="

echo "Current dangerous exposures:"
echo "❌ Redis port 6379 - CRITICAL: Database externally accessible"
echo "❌ API port 5000 - HIGH: Unencrypted API externally accessible"
echo ""
echo "Recommended fixes:"
echo "✅ Remove Redis external port (keep internal network access)"
echo "✅ Remove API HTTP external port (force HTTPS via nginx only)"
echo "✅ Keep nginx HTTP port 80 (redirects to HTTPS)"
echo "✅ Keep nginx HTTPS port 8443 (encrypted, secure)"
echo ""

# Backup current configuration
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
echo "📁 Backup created: docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"

echo ""
echo "Manual steps required:"
echo "1. Edit docker-compose.yml"
echo "2. Remove '- \"6379:6379\"' from redis service"
echo "3. Remove '- \"5000:5000\"' from traffic-monitor service" 
echo "4. Keep internal network access for service-to-service communication"
echo "5. Redeploy with: docker-compose down && docker-compose up -d"
echo ""
echo "Result: All external access will go through nginx proxy with HTTPS encryption"