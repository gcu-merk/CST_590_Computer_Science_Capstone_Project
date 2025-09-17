#!/bin/bash
# capture.sh - capture a single JPEG image to the mounted camera_capture live folder
# Usage: container runs this script periodically (via docker run or systemd timer) or once.

set -euo pipefail

OUT_DIR=${OUT_DIR:-/mnt/storage/camera_capture/live}
FILENAME="capture_$(date '+%Y%m%d_%H%M%S').jpg"

# Ensure output dir exists (should be mounted from host)
mkdir -p "$OUT_DIR"

# If a video device is present, use fswebcam; otherwise create a placeholder image
if [ -c /dev/video0 ]; then
    # Capture with fswebcam, scale to 1280x720 and write to OUT_DIR
    fswebcam -r 1280x720 --no-banner "$OUT_DIR/$FILENAME" || {
        echo "fswebcam capture failed, generating placeholder"
        convert -size 1280x720 xc:gray -gravity Center -pointsize 48 -fill black -annotate 0 "No camera: $(hostname)" "$OUT_DIR/$FILENAME"
    }
else
    # No camera device available: generate a placeholder image with hostname + timestamp
    convert -size 1280x720 xc:gray -gravity Center -pointsize 48 -fill black -annotate 0 "No camera: $(hostname)" "$OUT_DIR/$FILENAME"
fi

echo "Saved $OUT_DIR/$FILENAME"
