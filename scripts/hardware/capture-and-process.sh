#!/bin/bash
# Traffic Monitoring Capture and Process Script
# Hybrid solution: Host capture + Container processing
# 
# This script captures images using rpicam-still on the host,
# then processes them in the Docker container via shared volumes

set -euo pipefail

# Configuration
STORAGE_DIR="/mnt/storage"
SNAPSHOT_DIR="${STORAGE_DIR}/periodic_snapshots"
CONTAINER_NAME="traffic-monitor"
MAX_RETRIES=3
CAPTURE_QUALITY=95
IMAGE_WIDTH=4056
IMAGE_HEIGHT=3040

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if rpicam-still is available
    if ! command -v rpicam-still >/dev/null 2>&1; then
        log_error "rpicam-still not found. Please install rpicam-apps:"
        echo "sudo apt update && sudo apt install -y rpicam-apps"
        exit 1
    fi
    
    # Resolve container id for traffic-monitor (prefer compose label)
    cid=""
    cid=$(docker ps -a --filter "label=com.docker.compose.service=traffic-monitor" --format "{{.ID}}" 2>/dev/null || true)
    if [ -z "$cid" ]; then
        cid=$(docker ps -a --filter "name=traffic-monitor" --format "{{.ID}}" 2>/dev/null || true)
    fi

    if [ -z "$cid" ]; then
        log_error "Traffic monitor container not running. Starting compose stack..."
        docker compose up -d || docker-compose up -d || {
            log_error "Failed to start container"
            exit 1
        }
        sleep 5
        cid=$(docker ps -a --filter "label=com.docker.compose.service=traffic-monitor" --format "{{.ID}}" 2>/dev/null || docker ps -a --filter "name=traffic-monitor" --format "{{.ID}}" 2>/dev/null)
        cid=$(echo "$cid" | head -n1)
    fi
    # Use resolved container id for docker exec
    CONTAINER_NAME=${cid}
    
    # Check storage directory
    if [[ ! -d "$STORAGE_DIR" ]]; then
        log_warning "Storage directory $STORAGE_DIR does not exist. Creating..."
        sudo mkdir -p "$STORAGE_DIR"
        sudo chown $(whoami):$(whoami) "$STORAGE_DIR"
    fi
    
    # Check snapshot directory
    if [[ ! -d "$SNAPSHOT_DIR" ]]; then
        log_info "Creating snapshot directory: $SNAPSHOT_DIR"
        mkdir -p "$SNAPSHOT_DIR"
    fi
    
    log_success "Prerequisites check passed"
}

# Capture image using rpicam-still
capture_image() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local image_path="${SNAPSHOT_DIR}/traffic_${timestamp}.jpg"
    
    log_info "Capturing image: $image_path"
    
    # Capture with rpicam-still
    if rpicam-still -o "$image_path" \
        --width "$IMAGE_WIDTH" \
        --height "$IMAGE_HEIGHT" \
        --quality "$CAPTURE_QUALITY" \
        --timeout 5000 \
        --immediate 2>/dev/null; then
        
        # Verify image was created and has reasonable size
        if [[ -f "$image_path" ]] && [[ $(stat -c%s "$image_path") -gt 100000 ]]; then
            log_success "Image captured successfully: $(stat -c%s "$image_path") bytes"
            echo "$image_path"
            return 0
        else
            log_error "Image capture failed or file too small"
            return 1
        fi
    else
        log_error "rpicam-still command failed"
        return 1
    fi
}

# Process image in container
process_image() {
    local image_path="$1"
    local container_path="/mnt/storage/$(basename "$image_path")"
    
    log_info "Processing image in container: $container_path"
    
    # Test if container can access the image
    if docker exec "$CONTAINER_NAME" test -f "$container_path"; then
        log_success "Container can access image file"
        
        # Process with Python vehicle detection service
        docker exec "$CONTAINER_NAME" python3 -c "
import sys
import os
sys.path.append('/app')

try:
    from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
    import cv2
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load and process image
    image_path = '$container_path'
    logger.info(f'Loading image: {image_path}')
    
    frame = cv2.imread(image_path)
    if frame is not None:
        logger.info(f'Image loaded successfully: {frame.shape}')
        
        # Initialize service and process
        service = VehicleDetectionService()
        
        # Convert to RGB for processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run vehicle detection
        vehicles = service.detect_vehicles(frame_rgb)
        
        print(f'✅ Processing complete: {len(vehicles)} vehicles detected')
        
        # Save detection results if vehicles found
        if vehicles:
            output_path = image_path.replace('.jpg', '_processed.jpg')
            annotated_frame = service.annotate_frame(frame_rgb, vehicles)
            annotated_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, annotated_bgr)
            print(f'✅ Annotated image saved: {output_path}')
        
    else:
        print('❌ Failed to load image')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Processing error: {e}')
    sys.exit(1)
"
        
        if [[ $? -eq 0 ]]; then
            log_success "Image processing completed successfully"
            return 0
        else
            log_error "Image processing failed"
            return 1
        fi
    else
        log_error "Container cannot access image file: $container_path"
        return 1
    fi
}

# Clean up old files
cleanup_old_files() {
    local max_age_days=7
    log_info "Cleaning up files older than $max_age_days days..."
    
    find "$SNAPSHOT_DIR" -name "traffic_*.jpg" -mtime +$max_age_days -delete 2>/dev/null || true
    
    local remaining_files=$(find "$SNAPSHOT_DIR" -name "traffic_*.jpg" | wc -l)
    log_info "Files remaining in storage: $remaining_files"
}

# Main capture and process function
main() {
    log_info "=== Traffic Monitoring Capture and Process ==="
    log_info "Hybrid Host-Container Solution"
    
    check_prerequisites
    
    local retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        log_info "Attempt $((retry_count + 1)) of $MAX_RETRIES"
        
        # Capture image on host
        if image_path=$(capture_image); then
            # Process image in container
            if process_image "$image_path"; then
                log_success "Complete workflow successful!"
                cleanup_old_files
                exit 0
            else
                log_warning "Processing failed, but image captured successfully"
                log_info "Image available at: $image_path"
                exit 0  # Still successful since we have the image
            fi
        else
            log_error "Capture failed on attempt $((retry_count + 1))"
        fi
        
        retry_count=$((retry_count + 1))
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            log_info "Retrying in 5 seconds..."
            sleep 5
        fi
    done
    
    log_error "All capture attempts failed"
    exit 1
}

# Handle script arguments
case "${1:-}" in
    "test")
        log_info "Running test mode..."
        check_prerequisites
        log_success "Test mode completed"
        ;;
    "capture-only")
        log_info "Capture-only mode..."
        check_prerequisites
        if image_path=$(capture_image); then
            log_success "Image captured: $image_path"
        else
            log_error "Capture failed"
            exit 1
        fi
        ;;
    "cleanup")
        log_info "Cleanup mode..."
        cleanup_old_files
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [test|capture-only|cleanup]"
        echo "  test        - Check prerequisites only"
        echo "  capture-only - Capture image without processing"
        echo "  cleanup     - Clean up old files only"
        echo "  (no args)   - Full capture and process workflow"
        exit 1
        ;;
esac
