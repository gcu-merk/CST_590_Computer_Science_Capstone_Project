#!/bin/bash
# Make deployment scripts executable

echo "Setting executable permissions for deployment scripts..."

chmod +x deployment/deploy.sh
chmod +x deployment/verify-deployment.sh
chmod +x deployment/health-check.sh

echo "✅ Deployment script permissions updated:"
ls -la deployment/*.sh