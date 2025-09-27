#!/bin/bash
# Deploy ROI Configuration to Raspberry Pi
# This script uploads and applies the optimized ROI configuration

PI_HOST="100.121.231.16"
PI_USER="merk"
PI_STORAGE="/mnt/storage"

echo "Deploying Optimized Camera ROI Configuration"
echo "=============================================="

# Upload configuration files
echo "1. Uploading configuration files to Pi..."
scp optimized_roi_config.json ${PI_USER}@${PI_HOST}:${PI_STORAGE}/
scp apply_camera_roi.py ${PI_USER}@${PI_HOST}:${PI_STORAGE}/
scp configure_camera_roi.py ${PI_USER}@${PI_HOST}:${PI_STORAGE}/

echo "2. Applying ROI configuration..."
ssh ${PI_USER}@${PI_HOST} "cd ${PI_STORAGE} && python3 apply_camera_roi.py optimized_roi_config.json"

echo "3. Configuration deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test the new ROI configuration:"
echo "   ssh ${PI_USER}@${PI_HOST} 'cd ${PI_STORAGE} && python3 test_camera_roi.py'"
echo ""
echo "2. Monitor the camera service:"
echo "   ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u imx500-ai-capture -f'"
echo ""
echo "3. If you need to revert changes:"
echo "   ssh ${PI_USER}@${PI_HOST} 'cd ${PI_STORAGE} && cp scripts/imx500_ai_host_capture.py.backup scripts/imx500_ai_host_capture.py'"