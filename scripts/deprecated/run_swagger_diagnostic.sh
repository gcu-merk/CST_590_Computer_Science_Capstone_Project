#!/bin/bash
# Swagger Diagnostic Script Runner
# Copies and runs the diagnostic script on the Pi

echo "🔍 Swagger Issue Diagnostic"
echo "=========================="

# Copy the diagnostic script to the container
echo "📁 Copying diagnostic script to container..."
docker cp scripts/diagnose_swagger_issue.py edge-api:/app/diagnose_swagger_issue.py

# Run the diagnostic script inside the container
echo "🧪 Running diagnostic script..."
docker exec edge-api python /app/diagnose_swagger_issue.py

echo ""
echo "🔍 Additional container inspection..."
echo "Container logs (last 20 lines):"
docker logs edge-api --tail 20

echo ""
echo "🔍 Process inspection..."
docker exec edge-api ps aux

echo ""
echo "🔍 Python path inspection..."
docker exec edge-api python -c "import sys; print('\\n'.join(sys.path))"

echo ""
echo "📋 Diagnostic complete!"