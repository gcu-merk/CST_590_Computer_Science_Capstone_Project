#!/bin/bash
# Complete Camera Pipeline Test Script
# Tests IMX500 camera capture, shared volume setup, and Docker container processing
# Run this script on your Raspberry Pi: bash test_complete_camera_pipeline.sh

echo "🚗 Complete Camera Pipeline Test - $(date)"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to run command and check result
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -e "\n${BLUE}Testing: $test_name${NC}"
    
    if [ -n "$expected_pattern" ]; then
        result=$(eval "$test_command" 2>&1)
        if echo "$result" | grep -q "$expected_pattern"; then
            print_result 0 "$test_name"
            echo "    Output: $result"
        else
            print_result 1 "$test_name"
            echo "    Expected: $expected_pattern"
            echo "    Got: $result"
        fi
    else
        if eval "$test_command" >/dev/null 2>&1; then
            print_result 0 "$test_name"
        else
            print_result 1 "$test_name"
        fi
    fi
}

echo -e "\n${YELLOW}📋 1. BASIC SYSTEM CHECKS${NC}"
echo "----------------------------------------"

# Test 1: Check if we're on Raspberry Pi
run_test "Raspberry Pi Detection" "cat /proc/device-tree/model" "Raspberry Pi"

# Test 2: Check camera detection
run_test "Camera Hardware Detection" "rpicam-hello --list-cameras" "Available cameras"

# Test 3: Check if IMX500 firmware is installed
run_test "IMX500 Firmware Check" "ls /usr/share/rpi-camera-assets/imx500*" "imx500"

echo -e "\n${YELLOW}📷 2. CAMERA CAPTURE TESTS${NC}"
echo "----------------------------------------"

# Test 4: Basic camera test
echo -e "\n${BLUE}Testing: Basic Camera Function${NC}"
timeout 10s rpicam-hello -t 5s --nopreview >/dev/null 2>&1
print_result $? "Basic Camera Function"

# Test 5: Image capture test
echo -e "\n${BLUE}Testing: Image Capture${NC}"
rm -f /tmp/test_capture.jpg
rpicam-still -o /tmp/test_capture.jpg --immediate --width 4056 --height 3040 --quality 95 --timeout 3000 --nopreview --encoding jpg >/dev/null 2>&1
if [ -f /tmp/test_capture.jpg ]; then
    file_size=$(stat -c%s /tmp/test_capture.jpg)
    if [ $file_size -gt 100000 ]; then  # > 100KB
        print_result 0 "Image Capture (Size: ${file_size} bytes)"
    else
        print_result 1 "Image Capture (File too small: ${file_size} bytes)"
    fi
else
    print_result 1 "Image Capture (No file created)"
fi

# Test 6: AI Camera test
echo -e "\n${BLUE}Testing: AI Camera Function${NC}"
if [ -f /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json ]; then
    timeout 15s rpicam-hello -t 5s --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --nopreview >/dev/null 2>&1
    print_result $? "AI Camera Function"
else
    print_result 1 "AI Camera Function (No AI model file found)"
fi

echo -e "\n${YELLOW}📁 3. SHARED VOLUME SETUP${NC}"
echo "----------------------------------------"

# Test 7: Check shared volume directory structure (read-only test)
echo -e "\n${BLUE}Testing: Shared Volume Directory Structure${NC}"

check_directory_structure() {
    local base_dir="/mnt/storage/camera_capture"
    local required_subdirs=("live" "metadata" "periodic_snapshots" "processed")
    local missing_dirs=()
    local permission_issues=()
    
    # Check if base mount point exists
    if [ ! -d "/mnt/storage" ]; then
        echo "  ✗ Base mount point /mnt/storage does not exist"
        return 1
    fi
    
    # Check if base directory exists
    if [ ! -d "$base_dir" ]; then
        echo "  ✗ Camera capture directory $base_dir does not exist"
        return 1
    fi
    
    # Check all required subdirectories
    for subdir in "${required_subdirs[@]}"; do
        local full_path="$base_dir/$subdir"
        if [ ! -d "$full_path" ]; then
            missing_dirs+=("$subdir")
        elif [ ! -w "$full_path" ]; then
            permission_issues+=("$subdir")
        fi
    done
    
    # Report findings
    if [ ${#missing_dirs[@]} -eq 0 ] && [ ${#permission_issues[@]} -eq 0 ]; then
        echo "  ✓ All required directories exist and are writable"
        return 0
    else
        if [ ${#missing_dirs[@]} -gt 0 ]; then
            echo "  ✗ Missing directories: ${missing_dirs[*]}"
        fi
        if [ ${#permission_issues[@]} -gt 0 ]; then
            echo "  ✗ Permission issues: ${permission_issues[*]}"
        fi
        return 1
    fi
}

if check_directory_structure; then
    print_result 0 "Shared Volume Directory Structure"
else
    print_result 1 "Shared Volume Directory Structure"
    echo "    RECOMMENDATION: Run camera pipeline initialization to create directories"
fi

# Test 8: Test image capture to shared volume (read-only validation)
echo -e "\n${BLUE}Testing: Image Capture to Shared Volume${NC}"

test_image_capture() {
    local base_dir="/mnt/storage/camera_capture"
    local timestamp=$(date +%Y%m%d_%H%M%S_%3N)
    local filename="test_capture_${timestamp}.jpg"
    local shared_image_path="$base_dir/live/${filename}"
    
    # Pre-flight checks
    if [ ! -d "$base_dir/live" ]; then
        echo "  ✗ live directory does not exist: $base_dir/live"
        return 1
    fi
    
    if [ ! -w "$base_dir/live" ]; then
        echo "  ✗ live directory is not writable"
        return 1
    fi
    
    # Attempt image capture
    echo "  Attempting image capture..."
    if rpicam-still -o "$shared_image_path" --immediate --width 4056 --height 3040 --quality 95 --timeout 3000 --nopreview --encoding jpg >/dev/null 2>&1; then
        if [ -f "$shared_image_path" ]; then
            local file_size=$(stat -c%s "$shared_image_path" 2>/dev/null || echo "0")
            if [ "$file_size" -gt 100000 ]; then  # > 100KB indicates successful capture
                echo "  ✓ Image captured: $filename ($file_size bytes)"
                
                # Clean up test file
                rm -f "$shared_image_path" 2>/dev/null
                return 0
            else
                echo "  ✗ Image file too small: $file_size bytes"
                rm -f "$shared_image_path" 2>/dev/null
                return 1
            fi
        else
            echo "  ✗ Image file not created"
            return 1
        fi
    else
        echo "  ✗ Camera capture command failed"
        return 1
    fi
}

if test_image_capture; then
    print_result 0 "Image Capture to Shared Volume"
else
    print_result 1 "Image Capture to Shared Volume"
    echo "    RECOMMENDATION: Check directory permissions and camera functionality"
fi

# Test 9: Directory permissions check (diagnostic only)
echo -e "\n${BLUE}Testing: Directory Permissions${NC}"

check_directory_permissions() {
    local base_dir="/mnt/storage/camera_capture"
    local required_subdirs=("live" "metadata" "periodic_snapshots" "processed")
    local permission_report=()
    local all_good=true
    
    echo "  Checking permissions for camera directories..."
    
    for subdir in "${required_subdirs[@]}"; do
        local full_path="$base_dir/$subdir"
        
        if [ ! -d "$full_path" ]; then
            permission_report+=("✗ $subdir: Directory does not exist")
            all_good=false
            continue
        fi
        
        # Get detailed permissions info
        local perms=$(ls -ld "$full_path" | awk '{print $1}')
        local owner=$(ls -ld "$full_path" | awk '{print $3":"$4}')
        
        if [ -w "$full_path" ]; then
            permission_report+=("✓ $subdir: writable ($perms, $owner)")
        else
            permission_report+=("✗ $subdir: not writable ($perms, $owner)")
            all_good=false
        fi
    done
    
    # Display report
    for report_line in "${permission_report[@]}"; do
        echo "    $report_line"
    done
    
    # Test actual file creation capability
    local test_file="$base_dir/live/permission_test_$(date +%s).tmp"
    if touch "$test_file" 2>/dev/null; then
        echo "    ✓ File creation test: successful"
        rm -f "$test_file" 2>/dev/null
    else
        echo "    ✗ File creation test: failed"
        all_good=false
    fi
    
    $all_good
}

if check_directory_permissions; then
    print_result 0 "Directory Permissions"
else
    print_result 1 "Directory Permissions"
    echo "    RECOMMENDATION: Run camera initialization script to fix permissions"
fi

echo -e "\n${YELLOW}🐳 4. DOCKER CONTAINER TESTS${NC}"
echo "----------------------------------------"

# Test 10: Check if Docker is running (diagnostic only)
echo -e "\n${BLUE}Testing: Docker Service${NC}"

check_docker_status() {
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "  ✗ Docker is not installed"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker version >/dev/null 2>&1; then
        echo "  ✗ Docker daemon is not running"
        echo "    RECOMMENDATION: sudo systemctl start docker"
        return 1
    fi
    
    # Get Docker version info
    local version=$(docker --version 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "  ✓ Docker is running: $version"
        return 0
    else
        echo "  ✗ Docker command failed"
        return 1
    fi
}

if check_docker_status; then
    print_result 0 "Docker Service"
else
    print_result 1 "Docker Service"
    echo "    RECOMMENDATION: Start Docker service or check installation"
fi

# Test 11: Check container status (diagnostic only, no auto-start)
echo -e "\n${BLUE}Testing: Container Status${NC}"

find_application_container() {
    local container_patterns=("traffic" "edge" "monitor" "camera" "capstone")
    local container_name=""
    
    # Look for running containers first
    for pattern in "${container_patterns[@]}"; do
        container_name=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -i "$pattern" | head -1 | tr -d '\n\r')
        if [ -n "$container_name" ]; then
            echo "$container_name"
            return 0
        fi
    done
    
    # Look for stopped containers
    for pattern in "${container_patterns[@]}"; do
        container_name=$(docker ps -a --format "{{.Names}}" 2>/dev/null | grep -i "$pattern" | head -1 | tr -d '\n\r')
        if [ -n "$container_name" ]; then
            echo "$container_name"
            return 1  # Found but not running
        fi
    done
    
    # Check for docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        return 2  # Compose available but not running
    fi
    
    return 3  # No containers found
}

# Get container info with proper error handling
echo "  Searching for application containers..."
container_name=$(find_application_container 2>/dev/null)
container_result=$?

# Clean the container name of any extra characters
container_name=$(echo "$container_name" | tr -d '\n\r' | xargs)

if [ $container_result -eq 0 ] && [ -n "$container_name" ]; then
    echo "  ✓ Found running container: $container_name"
    print_result 0 "Container Status (Running: $container_name)"
elif [ $container_result -eq 1 ]; then
    echo "  Found stopped container: $container_name"
    print_result 1 "Container Status (Found but stopped: $container_name)"
elif [ $container_result -eq 2 ]; then
    echo "  Found docker-compose.yml but no containers running"
    echo "    RECOMMENDATION: docker-compose up -d"
    print_result 1 "Container Status (Docker Compose available but not running)"
else
    echo "  No application containers found"
    echo "    RECOMMENDATION: Check docker-compose.yml or container setup"
    print_result 1 "Container Status (No containers found)"
    echo "    Available containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" | head -5
fi
# Conditional container tests (only if container is running)
if [ $container_result -eq 0 ] && [ -n "$container_name" ]; then
    
    # Test 12: Check volume mount in container (diagnostic only)
    echo -e "\n${BLUE}Testing: Volume Mount in Container${NC}"
    
    check_container_volume() {
        local expected_paths=("/app/data/camera_capture" "/app/data/camera_capture/live" "/app/data/camera_capture/metadata")
        local missing_paths=()
        
        for path in "${expected_paths[@]}"; do
            if docker exec "$container_name" test -d "$path" 2>/dev/null; then
                echo "    ✓ Path exists in container: $path"
            else
                echo "    ✗ Path missing in container: $path"
                missing_paths+=("$path")
            fi
        done
        
        # Check if volume is writable from container
        local test_file="/app/data/camera_capture/live/container_write_test_$(date +%s).tmp"
        if docker exec "$container_name" touch "$test_file" 2>/dev/null; then
            echo "    ✓ Container can write to volume"
            docker exec "$container_name" rm -f "$test_file" 2>/dev/null
        else
            echo "    ✗ Container cannot write to volume"
            missing_paths+=("write_permission")
        fi
        
        [ ${#missing_paths[@]} -eq 0 ]
    }
    
    if check_container_volume; then
        print_result 0 "Volume Mount in Container"
    else
        print_result 1 "Volume Mount in Container"
        echo "    RECOMMENDATION: Check docker-compose.yml volume configuration"
    fi
    
    # Test 13: Check container image access (diagnostic only)
    echo -e "\n${BLUE}Testing: Container Image Access${NC}"
    
    check_container_image_access() {
        # Check if container can access the live directory
        if ! docker exec "$container_name" test -d /app/data/camera_capture/live 2>/dev/null; then
            echo "    ✗ Container cannot access live directory"
            return 1
        fi
        
        local image_count=$(docker exec "$container_name" find /app/data/camera_capture/live -name "*.jpg" 2>/dev/null | wc -l || echo "0")
        local recent_images=$(docker exec "$container_name" find /app/data/camera_capture/live -name "*.jpg" -newermt "5 minutes ago" 2>/dev/null | wc -l || echo "0")
        
        echo "    Total images found: $image_count"
        echo "    Recent images (last 5 min): $recent_images"
        
        if [ "$image_count" -gt 0 ]; then
            # Show sample of available images
            echo "    Sample images:"
            docker exec "$container_name" ls -la /app/data/camera_capture/live/ 2>/dev/null | tail -3 | while read line; do
                if [[ "$line" =~ \.jpg$ ]]; then
                    echo "      $line"
                fi
            done
            return 0
        else
            echo "    Directory contents:"
            docker exec "$container_name" ls -la /app/data/camera_capture/live/ 2>/dev/null | head -5 || echo "      Cannot list directory"
            return 1
        fi
    }
            docker exec "$container_name" ls -la /app/data/camera_capture/ 2>/dev/null || echo "      Cannot list directory"
            return 1
        fi
    }
    
    if check_container_image_access; then
        print_result 0 "Container Image Access"
    else
        print_result 1 "Container Image Access"
        echo "    RECOMMENDATION: Check host-side image capture service"
    fi
    
    # Test 14: Test shared volume image provider
    echo -e "\n${BLUE}Testing: Shared Volume Image Provider${NC}"
    provider_test=$(docker exec "$container_name" python3 -c "
try:
    import sys
    sys.path.append('/app')
    from edge_processing.shared_volume_image_provider import SharedVolumeImageProvider
    provider = SharedVolumeImageProvider()
    provider.start_monitoring()
    import time; time.sleep(2)
    success, image, metadata = provider.get_latest_image(max_age_seconds=300.0)
    provider.stop_monitoring()
    print(f'SUCCESS:{success}')
    if success and image is not None:
        print(f'SHAPE:{image.shape}')
        print(f'FILENAME:{metadata.get(\"filename\", \"unknown\")}')
    else:
        print('ERROR:No recent image found (check if images are being captured)')
except ImportError as e:
    print(f'ERROR:Module not found - {e}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)
    
    if echo "$provider_test" | grep -q "SUCCESS:True"; then
        print_result 0 "Shared Volume Image Provider"
        echo "    $(echo "$provider_test" | grep -E "(SUCCESS|SHAPE|FILENAME)")"
    else
        print_result 1 "Shared Volume Image Provider"
        echo "    Error: $(echo "$provider_test" | grep ERROR)"
    fi
    
    # Test 15: Test weather analysis service
    echo -e "\n${BLUE}Testing: Weather Analysis Service${NC}"
    weather_test=$(docker exec "$container_name" python3 -c "
try:
    import sys, requests, json
    response = requests.get('http://localhost:5000/api/weather', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if 'sky_condition' in data and data['sky_condition']['condition'] != 'unknown':
            print('SUCCESS:Weather analysis working')
            print(f'CONDITION:{data[\"sky_condition\"][\"condition\"]}')
        elif 'error' in data.get('sky_condition', {}):
            print(f'WARNING:Weather service running but has errors - {data[\"sky_condition\"][\"error\"]}')
        else:
            print('WARNING:Weather service running but no sky condition data')
    else:
        print(f'ERROR:API returned status {response.status_code}')
except requests.exceptions.ConnectionError:
    print('ERROR:Cannot connect to API (service may not be running)')
except requests.exceptions.Timeout:
    print('ERROR:API request timed out')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)
    
    if echo "$weather_test" | grep -q "SUCCESS:"; then
        print_result 0 "Weather Analysis Service"
        echo "    $(echo "$weather_test" | grep -E "(SUCCESS|CONDITION)")"
    elif echo "$weather_test" | grep -q "WARNING:"; then
        print_result 1 "Weather Analysis Service" 
        echo "    $(echo "$weather_test" | grep WARNING)"
    else
        print_result 1 "Weather Analysis Service"
        echo "    Error: $(echo "$weather_test" | grep ERROR)"
    fi
        print(f'ERROR:{data[\"sky_condition\"][\"error\"]}')
    else:
        print('ERROR:Unknown weather analysis issue')
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)
    
    if echo "$weather_test" | grep -q "SUCCESS"; then
        print_result 0 "Weather Analysis Service"
        echo "    $weather_test"
    else
        print_result 1 "Weather Analysis Service"
        echo "    $weather_test"
    fi
    
else
    print_result 1 "Container Not Found"
    echo "    Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | head -5
fi

echo -e "\n${YELLOW}🔧 5. CONTINUOUS CAPTURE TEST${NC}"
echo "----------------------------------------"

# Test 16: 30-second continuous capture test
echo -e "\n${BLUE}Testing: Continuous Capture (30 seconds)${NC}"
echo "  Starting continuous capture test..."

# Start continuous capture in background
(
    for i in {1..6}; do  # 6 images over 30 seconds
        timestamp=$(date +%Y%m%d_%H%M%S_%3N)
        filename="test_continuous_${timestamp}.jpg"
        rpicam-still -o "/mnt/storage/camera_capture/live/${filename}" --immediate --width 4056 --height 3040 --quality 95 --timeout 3000 --nopreview --encoding jpg >/dev/null 2>&1
        echo "    Captured: $filename"
        sleep 5
    done
) &
capture_pid=$!

# Wait for completion
sleep 30
wait $capture_pid

# Count captured images
continuous_count=$(find /mnt/storage/camera_capture/live -name "test_continuous_*.jpg" | wc -l)
if [ $continuous_count -ge 3 ]; then
    print_result 0 "Continuous Capture ($continuous_count images)"
else
    print_result 1 "Continuous Capture ($continuous_count images, expected >= 3)"
fi

echo -e "\n${YELLOW}📊 6. SYSTEM PERFORMANCE${NC}"
echo "----------------------------------------"

# Test 17: System resources
echo -e "\n${BLUE}System Resources:${NC}"
echo "  CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "  Memory: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "  Disk (storage): $(df -h /mnt/storage | awk 'NR==2{print $5}')"
echo "  Temperature: $(vcgencmd measure_temp | cut -d'=' -f2)"

# Test 18: Capture performance
echo -e "\n${BLUE}Testing: Capture Performance${NC}"
start_time=$(date +%s.%3N)
rpicam-still -o /tmp/perf_test.jpg --immediate --width 4056 --height 3040 --quality 95 --timeout 3000 --nopreview --encoding jpg >/dev/null 2>&1
end_time=$(date +%s.%3N)
capture_time=$(echo "$end_time - $start_time" | bc)

if [ -f /tmp/perf_test.jpg ]; then
    print_result 0 "Capture Performance (${capture_time}s)"
else
    print_result 1 "Capture Performance"
fi

echo -e "\n${YELLOW}📋 7. FINAL STATUS SUMMARY${NC}"
echo "----------------------------------------"

# Count files in shared volume
total_images=$(find /mnt/storage/camera_capture/live -name "*.jpg" 2>/dev/null | wc -l)
total_metadata=$(find /mnt/storage/camera_capture/metadata -name "*.json" 2>/dev/null | wc -l)
disk_usage=$(du -sh /mnt/storage/camera_capture 2>/dev/null | cut -f1)

echo "  📷 Total images captured: $total_images"
echo "  📄 Metadata files: $total_metadata"
echo "  💾 Disk usage: $disk_usage"
echo "  🐳 Container status: $([ -n "$container_name" ] && echo "Running ($container_name)" || echo "Not found")"

# Final test results
echo -e "\n${YELLOW}🏁 TEST RESULTS SUMMARY${NC}"
echo "=============================================="
echo -e "  ${GREEN}✓ Tests Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}✗ Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Camera pipeline is working correctly.${NC}"
    echo -e "${GREEN}Your system should now be capturing images and processing them in Docker containers.${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
    echo -e "${YELLOW}Common issues and solutions:${NC}"
    echo "  • Camera not detected: Check hardware connections and camera enable in raspi-config"
    echo "  • Directory issues: Run 'sudo bash scripts/camera-init.sh' to initialize infrastructure"
    echo "  • Container not found: Run 'docker-compose up -d' to start services"
    echo "  • Permission errors: Covered by camera-init.sh script"
    echo "  • Weather service errors: Check container logs with 'docker logs <container_name>'"
    echo ""
    echo -e "${BLUE}🔧 RECOMMENDED FIXES:${NC}"
    echo "  1. Initialize camera infrastructure:"
    echo "     sudo bash scripts/camera-init.sh"
    echo ""
    echo "  2. Start Docker services:"
    echo "     docker-compose up -d"
    echo ""
    echo "  3. Start camera capture service:"
    echo "     sudo systemctl start host-camera-capture"
    echo ""
    echo "  4. Re-run this test:"
    echo "     bash test_complete_camera_pipeline.sh"
fi

echo -e "\n${BLUE}🔍 Next steps:${NC}"
echo "  • Monitor live images: watch -n 2 'ls -la /mnt/storage/camera_capture/live/ | tail -5'"
echo "  • Check weather API: curl http://100.121.231.16:5000/api/weather"
echo "  • View container logs: docker logs <container_name>"
echo "  • System dashboard: http://100.121.231.16:5000"

# Cleanup test files
echo -e "\n${BLUE}Cleaning up test files...${NC}"
rm -f /tmp/test_capture.jpg /tmp/perf_test.jpg
find /mnt/storage/camera_capture/live -name "test_continuous_*.jpg" -delete 2>/dev/null

echo -e "\n${GREEN}Test complete! $(date)${NC}"