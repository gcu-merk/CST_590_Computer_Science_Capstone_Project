# Motion Detection Implementation Guide

## Technical Implementation Details

This document provides technical specifications and implementation guidelines for integrating motion detection into the hybrid traffic monitoring system.

## Development Phases

### Phase 1: Core Motion Detection Service

**Objectives:**
- Implement basic motion detection using OpenCV
- Create motion monitoring service architecture
- Integrate with existing capture pipeline

**Deliverables:**
- `MotionDetectionService` class
- Motion monitoring daemon
- Basic trigger integration with capture script

**Timeline:** 2-3 weeks

### Phase 2: Advanced Detection Algorithms

**Objectives:**
- Implement multiple detection algorithms (MOG2, frame diff, optical flow)
- Add adaptive thresholding and environmental compensation
- Implement ROI masking and false positive filtering

**Deliverables:**
- Multi-algorithm detection engine
- Configuration system for parameters
- ROI configuration tools

**Timeline:** 3-4 weeks

### Phase 3: Intelligent Triggering System

**Objectives:**
- Develop smart trigger decision engine
- Implement time-based and environmental adaptations
- Add performance monitoring and optimization

**Deliverables:**
- Intelligent trigger system
- Performance monitoring dashboard
- Automated optimization features

**Timeline:** 2-3 weeks

### Phase 4: Integration and Testing

**Objectives:**
- Full integration with existing hybrid system
- Comprehensive testing and validation
- Performance optimization and tuning

**Deliverables:**
- Production-ready motion detection system
- Documentation and configuration guides
- Performance benchmarks and optimization recommendations

**Timeline:** 2-3 weeks

## Technical Architecture

### Class Structure

```python
# Core motion detection classes
class MotionDetectionService:
    """Main service class for motion detection functionality"""
    
class MotionDetector:
    """Abstract base class for motion detection algorithms"""
    
class BackgroundSubtractionDetector(MotionDetector):
    """MOG2/KNN background subtraction implementation"""
    
class FrameDifferenceDetector(MotionDetector):
    """Frame differencing implementation"""
    
class OpticalFlowDetector(MotionDetector):
    """Optical flow motion detection implementation"""
    
class TriggerDecisionEngine:
    """Intelligent trigger decision making"""
    
class MotionEventManager:
    """Manage motion events and trigger coordination"""

class PerformanceMonitor:
    """Monitor system performance and resource usage"""
```

### Service Integration Points

**1. Capture Script Integration:**
```bash
# Existing capture script enhanced with motion modes
./scripts/capture-and-process.sh --mode hybrid
./scripts/capture-and-process.sh --mode motion-only
./scripts/capture-and-process.sh --motion-sensitivity high
```

**2. Container Communication:**
```python
# Motion service runs on host, communicates with container
# via shared memory, files, or inter-process communication
motion_service = MotionDetectionService()
motion_service.register_trigger_callback(container_process_callback)
```

**3. Systemd Service Architecture:**
```ini
# New motion detection service
[Unit]
Description=Traffic Monitoring Motion Detection
After=docker.service

[Service]
Type=notify
ExecStart=/usr/local/bin/motion-detection-service
User=merk
Restart=always
```

### Configuration System

**Configuration File Structure:**
```yaml
# /etc/traffic-monitoring/motion-config.yaml
motion_detection:
  enabled: true
  algorithm: "background_subtraction"  # or "frame_difference", "optical_flow"
  
  video_stream:
    width: 320
    height: 240
    framerate: 10
    buffer_size: 5
    
  detection_parameters:
    background_subtraction:
      history: 500
      var_threshold: 16
      detect_shadows: true
      
    frame_difference:
      threshold: 30
      min_area: 100
      gaussian_blur: 5
      
    optical_flow:
      max_corners: 100
      quality_level: 0.01
      min_distance: 10
      
  trigger_parameters:
    motion_threshold: 0.05        # 5% of frame must change
    area_threshold: 200           # Minimum motion area in pixels
    duration_threshold: 3         # Motion must persist for 3 frames
    cooldown_period: 10           # Seconds between triggers
    
  environmental_adaptation:
    time_based_sensitivity: true
    weather_compensation: true
    lighting_adjustment: true
    
  roi_masking:
    enabled: true
    ignore_zones:
      - name: "tree_area"
        coordinates: [[100, 50], [200, 150]]
      - name: "flag_pole"
        coordinates: [[300, 0], [350, 100]]
        
  performance:
    max_cpu_usage: 80            # Percentage
    max_memory_usage: 200        # MB
    optimization_mode: "balanced" # "performance", "efficiency", "balanced"
```

### Database Schema Extensions

**Motion Events Table:**
```sql
CREATE TABLE motion_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    duration_ms INTEGER,
    motion_area INTEGER,
    confidence REAL,
    trigger_source TEXT,  -- 'motion', 'periodic', 'manual'
    algorithm_used TEXT,
    image_path TEXT,
    processing_result TEXT,
    vehicles_detected INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_motion_events_timestamp ON motion_events(timestamp);
CREATE INDEX idx_motion_events_trigger_source ON motion_events(trigger_source);
```

**Performance Metrics Table:**
```sql
CREATE TABLE motion_performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    cpu_usage REAL,
    memory_usage REAL,
    processing_time_ms INTEGER,
    frames_processed INTEGER,
    false_positives INTEGER,
    true_positives INTEGER,
    system_load REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### API Extensions

**REST API Endpoints:**
```python
# Motion detection control endpoints
@app.route('/api/motion/status', methods=['GET'])
def get_motion_status():
    """Get current motion detection status and statistics"""

@app.route('/api/motion/config', methods=['GET', 'POST'])
def motion_config():
    """Get or update motion detection configuration"""

@app.route('/api/motion/calibrate', methods=['POST'])
def calibrate_motion_detection():
    """Start interactive motion detection calibration"""

@app.route('/api/motion/events', methods=['GET'])
def get_motion_events():
    """Get recent motion detection events"""

@app.route('/api/motion/performance', methods=['GET'])
def get_motion_performance():
    """Get motion detection performance metrics"""

@app.route('/api/motion/trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger a capture (for testing)"""
```

### Testing Strategy

**Unit Testing:**
```python
# Test motion detection algorithms
class TestMotionDetectors(unittest.TestCase):
    def test_background_subtraction_detection(self):
        """Test MOG2 background subtraction accuracy"""
        
    def test_frame_difference_detection(self):
        """Test frame differencing sensitivity"""
        
    def test_optical_flow_detection(self):
        """Test optical flow motion tracking"""

# Test trigger decision engine
class TestTriggerEngine(unittest.TestCase):
    def test_trigger_decision_logic(self):
        """Test multi-factor trigger decisions"""
        
    def test_false_positive_filtering(self):
        """Test environmental false positive filtering"""
        
    def test_cooldown_enforcement(self):
        """Test trigger cooldown period enforcement"""
```

**Integration Testing:**
```python
# Test full motion detection pipeline
class TestMotionDetectionIntegration(unittest.TestCase):
    def test_end_to_end_motion_capture(self):
        """Test complete motion → capture → process pipeline"""
        
    def test_hybrid_mode_coordination(self):
        """Test coordination between periodic and motion triggers"""
        
    def test_performance_under_load(self):
        """Test system performance during high activity periods"""
```

**Field Testing:**
```yaml
# Field testing scenarios
field_tests:
  low_traffic_period:
    duration: "24 hours"
    expected_triggers: 50-100
    success_criteria: "<5% false positives"
    
  high_traffic_period:
    duration: "8 hours"
    expected_triggers: 200-500
    success_criteria: ">90% vehicle detection accuracy"
    
  weather_conditions:
    scenarios: ["rain", "wind", "fog", "bright_sun"]
    success_criteria: "Adaptive performance maintained"
    
  night_operation:
    duration: "12 hours"
    lighting: "streetlights only"
    success_criteria: "Motion detection functional"
```

## Performance Optimization Guidelines

### CPU Optimization

**Algorithm Selection:**
- **Low CPU environments**: Use frame differencing
- **Moderate CPU**: Use MOG2 background subtraction
- **High CPU available**: Use optical flow for maximum accuracy

**Processing Optimizations:**
```python
# Optimization techniques
def optimize_for_performance():
    # 1. Reduce processing resolution
    frame = cv2.resize(frame, (160, 120))  # Even lower for CPU-constrained systems
    
    # 2. Skip frames during high load
    if cpu_usage > 80:
        process_every_nth_frame = 3
    else:
        process_every_nth_frame = 1
    
    # 3. Use efficient OpenCV operations
    cv2.setUseOptimized(True)
    cv2.setNumThreads(2)  # Limit OpenCV thread usage
    
    # 4. Implement adaptive processing
    if motion_detected_recently:
        increase_processing_frequency()
    else:
        decrease_processing_frequency()
```

### Memory Optimization

**Buffer Management:**
```python
# Efficient frame buffer management
class FrameBuffer:
    def __init__(self, max_size=5):
        self.frames = collections.deque(maxlen=max_size)
        self.max_memory_mb = 50
        
    def add_frame(self, frame):
        # Compress frame if memory usage too high
        if self.get_memory_usage() > self.max_memory_mb:
            frame = self.compress_frame(frame)
        self.frames.append(frame)
        
    def get_memory_usage(self):
        return sum(frame.nbytes for frame in self.frames) / 1024 / 1024
```

### Storage Optimization

**Intelligent Storage Management:**
```python
def optimize_storage():
    # 1. Compress old images
    compress_images_older_than(days=7)
    
    # 2. Delete low-confidence captures
    delete_images_with_confidence_below(threshold=0.3)
    
    # 3. Keep only best captures per time period
    keep_best_n_captures_per_hour(n=5)
    
    # 4. Archive to external storage
    archive_images_older_than(days=30)
```

## Monitoring and Maintenance

### Health Monitoring

**System Health Checks:**
```python
def check_motion_detection_health():
    health_status = {
        'motion_service_running': is_process_running('motion-detection'),
        'video_stream_active': check_video_stream_health(),
        'cpu_usage_acceptable': get_cpu_usage() < 80,
        'memory_usage_acceptable': get_memory_usage() < 200,
        'recent_triggers': count_triggers_last_hour() > 0,
        'false_positive_rate': calculate_false_positive_rate(),
        'processing_latency': get_average_processing_time()
    }
    return health_status
```

**Automated Maintenance:**
```bash
#!/bin/bash
# Daily maintenance script
# /etc/cron.daily/motion-detection-maintenance

# Clean up old log files
find /var/log/motion-detection -name "*.log" -mtime +7 -delete

# Optimize motion detection parameters based on performance
python3 /usr/local/bin/motion-detection-optimizer.py

# Generate daily performance report
python3 /usr/local/bin/motion-performance-report.py

# Check and repair any corrupted configuration
python3 /usr/local/bin/motion-config-validator.py --repair
```

### Performance Monitoring Dashboard

**Key Metrics to Track:**
```yaml
dashboard_metrics:
  real_time:
    - cpu_usage
    - memory_usage
    - processing_latency
    - trigger_rate
    - false_positive_rate
    
  daily_summaries:
    - total_triggers
    - vehicles_detected
    - storage_usage
    - system_uptime
    - error_count
    
  weekly_trends:
    - trigger_patterns
    - performance_trends
    - accuracy_improvements
    - resource_optimization
```

This implementation guide provides the technical foundation for developing a robust, efficient motion detection system that integrates seamlessly with the existing hybrid traffic monitoring solution.
