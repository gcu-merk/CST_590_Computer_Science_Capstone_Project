# Motion Detection Architecture for Traffic Monitoring System

## Overview

This document outlines the software-based motion detection enhancement for the hybrid traffic monitoring solution. Motion detection adds intelligent, event-driven capture capabilities to complement the existing periodic capture system.

## Architecture Design

### High-Level Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Background      │    │ Motion Detection│    │ Trigger Capture │
│ Monitoring      │───▶│ Algorithm       │───▶│ & Processing    │
│ (rpicam-vid)    │    │ (OpenCV diff)   │    │ (rpicam-still)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Integration

**Enhanced Multi-Sensor Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                Edge AI Detection Layer                  │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │   Radar     │ │   Motion    │ │   IMX500 AI Camera  │ │
│ │  Sensor     │ │ Detection   │ │   Classification    │ │
│ │(Continuous) │ │(Validation) │ │  (Edge Processing)  │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Data Fusion Layer                       │
├─────────────────────────────────────────────────────────┤
│ • Speed correlation (radar + visual estimation)         │
│ • Vehicle classification (AI + size validation)         │
│ • Confidence weighting (multi-sensor agreement)         │
│ • Environmental adaptation (weather, lighting)          │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│              Enhanced Capture & Storage                 │
├─────────────────────────────────────────────────────────┤
│ • High-resolution image capture (rpicam-still)          │
│ • AI classification metadata storage                    │
│ • Radar correlation data                                │
│ • Multi-sensor event logging                            │
└─────────────────────────────────────────────────────────┘
```
│ │   Motion    │ │  Trigger    │ │    Intelligence     │ │
│ │ Monitoring  │ │ Decision    │ │   & Filtering       │ │
│ │             │ │   Engine    │ │                     │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│              Existing Hybrid Solution                   │
├─────────────────────────────────────────────────────────┤
│ Host Capture (rpicam-still) + Container Processing      │
└─────────────────────────────────────────────────────────┘
```

## Motion Detection Methods

### 1. Background Subtraction

**Purpose**: Detect moving objects against a stable background

**Algorithm Options**:
- **MOG2 (Mixture of Gaussians)**: Adaptive background modeling
- **KNN (K-Nearest Neighbors)**: Better shadow detection
- **GMG (Gaussian Mixture)**: Good for noisy environments

**Implementation**:
```python
# Conceptual implementation
background_subtractor = cv2.createBackgroundSubtractorMOG2(
    detectShadows=True,
    varThreshold=16,
    history=500
)

# For each frame:
foreground_mask = background_subtractor.apply(frame)
motion_detected = analyze_foreground_mask(foreground_mask)
```

**Advantages**:
- Excellent for stationary camera setups
- Adapts to lighting changes automatically
- Good performance in various weather conditions

**Considerations**:
- Requires initialization period (learning background)
- May struggle with sudden lighting changes
- Can generate false positives from shadows

### 2. Frame Differencing

**Purpose**: Detect changes between consecutive frames

**Algorithm**:
```python
# Conceptual implementation
def detect_motion_frame_diff(frame1, frame2, threshold=30, min_area=100):
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Apply threshold and morphological operations
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    # Find contours and filter by area
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]
    
    return len(significant_contours) > 0, significant_contours
```

**Advantages**:
- Simple and fast computation
- No initialization period required
- Works well for detecting immediate movement

**Considerations**:
- Sensitive to camera vibration
- May miss slow-moving objects
- Requires parameter tuning for environment

### 3. Optical Flow

**Purpose**: Track motion vectors of feature points

**Algorithm Options**:
- **Lucas-Kanade**: Sparse optical flow (track specific points)
- **Farneback**: Dense optical flow (track all pixels)

**Implementation**:
```python
# Conceptual sparse optical flow
def detect_motion_optical_flow(frame1, frame2):
    # Detect features in first frame
    features = cv2.goodFeaturesToTrack(
        cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY),
        maxCorners=100,
        qualityLevel=0.01,
        minDistance=10
    )
    
    # Calculate optical flow
    flow_vectors, status, error = cv2.calcOpticalFlowPyrLK(
        cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY),
        features,
        None
    )
    
    # Analyze motion magnitude
    motion_magnitude = calculate_motion_magnitude(features, flow_vectors, status)
    return motion_magnitude > threshold
```

**Advantages**:
- Very accurate motion detection
- Provides directional information
- Good for tracking specific objects

**Considerations**:
- More CPU intensive
- Requires good feature points
- Complex implementation

## Implementation Strategy

### Low-Power Monitoring Mode

**Video Stream Configuration**:
```bash
# Continuous low-resolution monitoring for motion detection
rpicam-vid --width 320 --height 240 --framerate 10 \
  --output - --timeout 0 --codec mjpeg | motion-detection-processor

# Advantages of low-resolution monitoring:
# - Reduced CPU usage (320x240 vs 4056x3040)
# - Lower bandwidth requirements
# - Faster processing for real-time detection
# - Preserves high-resolution capture for actual events
```

**Motion Detection Pipeline**:
```
Video Stream → Frame Buffer → Motion Analysis → Trigger Decision → High-Res Capture
    ↓              ↓              ↓              ↓              ↓
  320x240      Ring Buffer    OpenCV Diff    Smart Logic   4056x3040
  10 FPS       Last 3-5        Algorithm      Filtering     rpicam-still
  MJPEG        frames         Background      Cooldown      Full Quality
               Memory         Subtraction     Thresholds    Processing
```

### Hybrid Trigger System

**Multiple Trigger Sources**:
```
┌─────────────────────────────────────────────────────────┐
│                   Capture Triggers                     │
├─────────────────────────────────────────────────────────┤
│ 1. ⏰ Periodic (every 5 min) - baseline monitoring     │
│   • Ensures regular data collection                    │
│   • Captures quiet periods for trend analysis          │
│   • Provides backup if motion detection fails          │
├─────────────────────────────────────────────────────────┤
│ 2. 🏃 Motion detected - event-driven captures          │
│   • Real-time response to activity                     │
│   • Optimized storage usage                            │
│   • Higher temporal resolution for events              │
├─────────────────────────────────────────────────────────┤
│ 3. 🚗 Vehicle detected - AI-triggered sequences        │
│   • Chain captures for vehicle tracking                │
│   • Multiple angles/timestamps per vehicle             │
│   • Enhanced data for ML training                      │
├─────────────────────────────────────────────────────────┤
│ 4. 📱 Manual trigger - API/web interface               │
│   • On-demand captures for testing                     │
│   • User-initiated data collection                     │
│   • Remote monitoring capabilities                     │
└─────────────────────────────────────────────────────────┘
```

### Smart Triggering Logic

**Multi-Factor Decision Engine**:
```python
# Conceptual trigger decision logic
def should_trigger_capture(motion_data, system_state, environment):
    # Primary motion criteria
    motion_valid = (
        motion_data.area > MIN_MOTION_AREA and
        motion_data.intensity > MOTION_THRESHOLD and
        motion_data.duration > MIN_DURATION
    )
    
    # System state checks
    system_ready = (
        time_since_last_capture > COOLDOWN_PERIOD and
        system_state.cpu_usage < MAX_CPU_THRESHOLD and
        system_state.storage_available > MIN_STORAGE
    )
    
    # Environmental filtering
    environment_suitable = (
        not is_false_positive(motion_data, environment) and
        environment.lighting_adequate and
        not environment.severe_weather
    )
    
    return motion_valid and system_ready and environment_suitable
```

## Motion Detection Parameters

### Sensitivity Configuration

**Threshold Parameters**:
```yaml
motion_detection:
  # Primary sensitivity controls
  pixel_change_threshold: 2-5%     # Percentage of pixels that must change
  area_threshold: 100-500 pixels   # Minimum contiguous motion area
  duration_threshold: 2-3 frames   # Motion must persist across frames
  intensity_threshold: 30-80       # Brightness change magnitude (0-255)
  
  # Advanced filtering
  cooldown_period: 10 seconds      # Minimum time between triggers
  noise_filter_size: 3x3          # Morphological filter kernel
  gaussian_blur: 5x5               # Noise reduction before detection
  
  # ROI (Region of Interest) masking
  ignore_zones:
    - trees: [[x1,y1], [x2,y2]]    # Ignore swaying vegetation
    - flags: [[x3,y3], [x4,y4]]    # Ignore flags, banners
    - sky: [[x5,y5], [x6,y6]]      # Ignore clouds, birds
```

**Adaptive Sensitivity**:
```yaml
# Time-based sensitivity adjustment
sensitivity_schedule:
  day_time:        # 6 AM - 8 PM
    threshold: 5%
    area_min: 200
    description: "Higher threshold for busy periods"
    
  night_time:      # 8 PM - 6 AM
    threshold: 3%
    area_min: 100
    description: "Lower threshold for quiet periods"
    
  rush_hour:       # 7-9 AM, 4-6 PM
    threshold: 8%
    area_min: 300
    cooldown: 5     # Shorter cooldown for high activity
    description: "Higher threshold to avoid spam"
```

### Environmental Adaptation

**Weather Compensation**:
```yaml
weather_adjustments:
  rain:
    threshold_multiplier: 1.5      # Increase threshold (more noise)
    area_multiplier: 1.3           # Require larger motion areas
    description: "Compensate for rain droplets, puddle reflections"
    
  wind:
    threshold_multiplier: 1.2      # Slight increase for vegetation movement
    roi_expansion: true            # Expand ignore zones for trees
    description: "Account for increased vegetation movement"
    
  fog:
    contrast_enhancement: true     # Pre-process frames for low contrast
    threshold_multiplier: 0.8      # Lower threshold (reduced visibility)
    description: "Enhance detection in low-visibility conditions"
    
  snow:
    threshold_multiplier: 2.0      # Significantly higher threshold
    temporal_averaging: 5          # Average over more frames
    description: "Filter out snowflake noise"
```

**Lighting Adaptation**:
```yaml
lighting_adjustments:
  dawn_dusk:
    adaptive_background: true      # Faster background model updates
    shadow_detection: enhanced     # Better shadow filtering
    threshold_adjustment: dynamic  # Gradual threshold changes
    
  night_mode:
    ir_optimization: true          # Optimize for infrared if available
    noise_reduction: enhanced      # More aggressive noise filtering
    gain_compensation: automatic   # Adjust for low-light gain
    
  bright_sunny:
    shadow_masking: aggressive     # Strong shadow filtering
    reflection_filter: true        # Filter reflections from vehicles
    contrast_normalization: true   # Normalize high-contrast scenes
```

## Processing Pipeline Architecture

### 1. Motion Monitoring Service

**Service Architecture**:
```
Motion Monitoring Service
├── Video Stream Manager
│   ├── rpicam-vid process management
│   ├── Frame buffer management (ring buffer)
│   └── Stream health monitoring
├── Motion Detection Engine
│   ├── Background subtraction processor
│   ├── Frame differencing analyzer
│   └── Optical flow calculator (optional)
├── Trigger Decision Engine
│   ├── Multi-factor analysis
│   ├── Environmental adaptation
│   └── False positive filtering
└── Integration Interface
    ├── High-resolution capture trigger
    ├── Container processing coordination
    └── Logging and metrics collection
```

**Service Configuration**:
```yaml
motion_service:
  video_stream:
    resolution: "320x240"
    framerate: 10
    codec: "mjpeg"
    buffer_size: 5              # Keep last 5 frames
    
  detection_engine:
    primary_method: "background_subtraction"
    fallback_method: "frame_differencing"
    update_interval: 100        # Update background every 100 frames
    
  trigger_engine:
    decision_interval: 0.1      # Check for triggers every 100ms
    confidence_threshold: 0.7   # Minimum confidence for trigger
    debounce_time: 2.0         # Minimum time between decisions
```

### 2. Integration with Existing System

**Enhanced Multi-Sensor Architecture**:
```yaml
operation_modes:
  radar_primary_ai:
    description: "Radar-triggered edge AI processing - recommended"
    radar_detection: true
    edge_ai_classification: true
    motion_detection: false      # Motion as backup validation only
    periodic_captures: true
    periodic_interval: 900       # 15 minutes when radar active
    
  motion_backup:
    description: "Motion detection when radar unavailable"
    motion_detection: true
    radar_detection: false
    edge_ai_classification: true
    periodic_captures: true
    
  hybrid_multi_sensor:
    description: "Full multi-sensor fusion"
    radar_detection: true
    motion_detection: true
    edge_ai_classification: true
    sensor_fusion: true
    confidence_weighting: true
    motion_detection: true
    capture_interval: 900       # Reduce to 15 minutes
    motion_priority: true       # Motion triggers take precedence
    
  hybrid_aggressive:
    description: "Maximum coverage - frequent periodic + motion"
    motion_detection: true
    capture_interval: 300       # Keep 5-minute periodic
    motion_sensitivity: high
    max_captures_per_hour: 60   # Rate limiting
```

### 3. Enhanced Capture Script Integration

**Command Line Interface**:
```bash
# Enhanced capture script with motion detection modes
capture-traffic --mode motion              # Start motion monitoring only
capture-traffic --mode periodic            # Current 5-minute timer only
capture-traffic --mode hybrid              # Both motion + periodic (recommended)
capture-traffic --mode motion --sensitivity high    # High sensitivity motion
capture-traffic --mode hybrid --config custom.yaml  # Custom configuration

# Configuration and testing
capture-traffic --test-motion              # Test motion detection setup
capture-traffic --calibrate                # Interactive sensitivity calibration
capture-traffic --show-motion              # Live motion detection preview
capture-traffic --roi-setup                # Configure region of interest masks
```

**Service Management**:
```bash
# Systemd service extensions
sudo systemctl start traffic-monitoring-motion.service    # Motion detection service
sudo systemctl enable traffic-monitoring-hybrid.timer     # Combined timer
sudo systemctl status traffic-monitoring-motion.service   # Check motion service status

# Monitoring and diagnostics
capture-traffic --motion-stats             # Show motion detection statistics
capture-traffic --motion-log              # View motion detection events
capture-traffic --performance             # System performance metrics
```

## Benefits and Performance Impact

### Benefits of Motion-Triggered Capture

**✅ Operational Efficiency**:
- **Reduced Storage Usage**: Only capture when activity occurs
- **Lower Processing Load**: Process fewer irrelevant images
- **Extended System Lifetime**: Reduced wear on storage and CPU
- **Optimized Power Consumption**: Sleep during quiet periods

**✅ Enhanced Coverage**:
- **Real-time Event Response**: Catch vehicles between periodic captures
- **Higher Temporal Resolution**: Multiple captures per traffic event
- **Better Data Quality**: Focus on periods with actual activity
- **Improved Analytics**: Time-correlated data for better insights

**✅ Intelligent Operation**:
- **Adaptive Behavior**: Adjust to traffic patterns automatically
- **False Positive Filtering**: Reduce captures from weather, animals
- **Context-Aware Triggers**: Consider time, weather, system state
- **Scalable Performance**: Efficient from single vehicle to rush hour

### Performance Considerations

**CPU Usage Profile**:
```
┌─────────────────────────────────────────────────────────┐
│                    CPU Usage Breakdown                  │
├─────────────────────────────────────────────────────────┤
│ Motion Monitoring (continuous):         5-15% CPU       │
│   • Video decoding (320x240 MJPEG)     3-8% CPU        │
│   • Motion detection algorithm         2-7% CPU        │
│                                                         │
│ High-Resolution Capture (triggered):    20-40% CPU      │
│   • rpicam-still execution             10-20% CPU       │
│   • Container processing               10-20% CPU       │
│                                                         │
│ Baseline System (without motion):       2-5% CPU        │
│   • Periodic captures only             2-5% CPU        │
└─────────────────────────────────────────────────────────┘
```

**Memory Usage**:
```yaml
memory_requirements:
  motion_service_base: 50-100 MB         # Service overhead
  video_buffer: 10-20 MB                 # Frame buffer (5 frames @ 320x240)
  opencv_processing: 20-50 MB            # OpenCV algorithm memory
  background_model: 5-15 MB              # Background subtraction model
  
  total_additional: 85-185 MB            # Additional memory for motion detection
  recommended_ram: 2 GB minimum          # For reliable operation
```

**Storage Impact**:
```yaml
storage_optimization:
  without_motion:
    captures_per_day: 288                # Every 5 minutes
    storage_per_day: ~400 MB             # 288 × 1.4MB average
    
  with_motion_low_traffic:
    periodic_captures: 96                # Every 15 minutes (reduced)
    motion_captures: 50-100              # Varies by activity
    storage_per_day: ~200-300 MB         # 30-40% reduction
    
  with_motion_high_traffic:
    periodic_captures: 96
    motion_captures: 200-400             # Busy area
    storage_per_day: ~400-700 MB         # Similar to current, but better quality
```

**Network and I/O Impact**:
```yaml
io_performance:
  video_stream_bandwidth: 1-3 Mbps      # Low-resolution monitoring
  capture_burst_io: 10-50 MB/s          # During high-res capture
  storage_write_pattern: "bursty"       # Concentrated during events
  
  optimization_strategies:
    - Use SSD for better burst I/O performance
    - Buffer motion events to smooth I/O patterns
    - Compress old images to reduce storage growth
    - Stream video to RAM disk for processing
```

This motion detection architecture provides a comprehensive framework for adding intelligent, event-driven capabilities to the existing hybrid traffic monitoring solution while maintaining its proven reliability and performance characteristics.
