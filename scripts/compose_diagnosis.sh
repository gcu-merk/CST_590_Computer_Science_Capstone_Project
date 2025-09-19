#!/bin/bash

echo "=== Diagnosing Docker Compose Configuration ==="
echo "Date: $(date)"
echo

echo "1. Current directory and compose files..."
cd /mnt/storage/deployment-staging
pwd
ls -la docker-compose*.yml
echo

echo "2. Checking docker-compose.pi.yml content..."
echo "--- docker-compose.pi.yml ---"
cat docker-compose.pi.yml
echo

echo "3. Checking if there's a main docker-compose.yml..."
echo "--- docker-compose.yml (if exists) ---"
cat docker-compose.yml | head -20
echo

echo "4. Looking for the correct compose file with image specification..."
grep -r "gcumerk/cst590-capstone-public" . || echo "Image not found in compose files"
echo

echo "5. Checking what files are available..."
ls -la | grep compose
echo

echo "=== Diagnosis Complete ==="
echo "Need to identify the correct compose file or fix the image specification"