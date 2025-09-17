# Motion Detection Configuration Reference

## Configuration File Locations

**Primary Configuration:**
- `/etc/traffic-monitoring/motion-config.yaml` - Main motion detection configuration
- `/etc/traffic-monitoring/roi-masks.json` - Region of Interest mask definitions
- `/etc/traffic-monitoring/environmental-profiles.yaml` - Weather and lighting adaptations

**Runtime Configuration:**
- `/var/lib/traffic-monitoring/motion-state.json` - Current motion detection state
- `/tmp/motion-detection.pid` - Process ID file
- `/var/log/motion-detection/` - Log files and debug output

## Complete Configuration Schema

### Main Configuration File

```yaml
# /etc/traffic-monitoring/motion-config.yaml
# Complete motion detection configuration

# Service Configuration
service:
  enabled: true
  debug_mode: false
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  pid_file: "/tmp/motion-detection.pid"
  log_directory: "/var/log/motion-detection"
  
# Video Stream Configuration
video_stream:
  # Video capture settings
  width: 320
  height: 240
  framerate: 10
  codec: "mjpeg"  # mjpeg, h264, raw
  device: "/dev/video0"
  
  # Buffer management
  buffer_size: 5          # Number of frames to keep in memory
  max_buffer_memory: 50   # Maximum buffer memory in MB
  
  # Stream health monitoring
  stream_timeout: 10      # Seconds before considering stream dead
  restart_on_failure: true
  max_restart_attempts: 3

# Motion Detection Algorithms
detection:
  # Primary algorithm selection
  primary_algorithm: "background_subtraction"  # background_subtraction, frame_difference, optical_flow
  fallback_algorithm: "frame_difference"       # Used if primary fails
  
  # Background Subtraction (MOG2/KNN) Parameters
  background_subtraction:
    algorithm: "MOG2"     # MOG2, KNN, GMG
    history: 500          # Number of frames for background learning
    var_threshold: 16     # Threshold for foreground detection
    detect_shadows: true  # Enable shadow detection
    shadow_threshold: 0.5 # Shadow detection threshold
    nmixtures: 5          # Number of Gaussian mixtures (MOG2)
    background_ratio: 0.9 # Background ratio threshold
    
  # Frame Differencing Parameters
  frame_difference:
    threshold: 30         # Pixel difference threshold (0-255)
    min_area: 100         # Minimum contour area in pixels
    gaussian_blur: 5      # Gaussian blur kernel size (odd numbers)
    morphology_kernel: 3  # Morphological operation kernel size
    erosion_iterations: 1 # Number of erosion iterations
    dilation_iterations: 2 # Number of dilation iterations
    
  # Optical Flow Parameters
  optical_flow:
    method: "lucas_kanade"  # lucas_kanade, farneback
    max_corners: 100        # Maximum corners to track
    quality_level: 0.01     # Corner detection quality
    min_distance: 10        # Minimum distance between corners
    block_size: 7           # Block size for corner detection
    flow_threshold: 2.0     # Motion magnitude threshold

# Trigger Decision Parameters
trigger:
  # Motion thresholds
  motion_area_threshold: 200      # Minimum motion area in pixels
  motion_intensity_threshold: 30  # Minimum motion intensity (0-255)
  motion_percentage_threshold: 2  # Minimum percentage of frame with motion
  
  # Temporal requirements
  duration_threshold: 3           # Motion must persist for N frames
  cooldown_period: 10            # Minimum seconds between triggers
  max_triggers_per_minute: 6     # Rate limiting
  
  # Confidence requirements
  confidence_threshold: 0.7      # Minimum confidence for trigger
  multi_algorithm_consensus: false # Require multiple algorithms to agree
  
  # Advanced filtering
  noise_filter_enabled: true     # Enable noise filtering
  edge_motion_filter: true       # Filter motion at frame edges
  aspect_ratio_filter: true      # Filter unrealistic aspect ratios

# Environmental Adaptation
environmental:
  # Time-based sensitivity adjustment
  time_based_adaptation:
    enabled: true
    
    schedules:
      dawn:  # 5:00 AM - 7:00 AM
        start_time: "05:00"
        end_time: "07:00"
        sensitivity_multiplier: 0.8
        area_threshold_multiplier: 1.2
        
      day:   # 7:00 AM - 6:00 PM
        start_time: "07:00"
        end_time: "18:00"
        sensitivity_multiplier: 1.0
        area_threshold_multiplier: 1.0
        
      dusk:  # 6:00 PM - 8:00 PM
        start_time: "18:00"
        end_time: "20:00"
        sensitivity_multiplier: 0.8
        area_threshold_multiplier: 1.2
        
      night: # 8:00 PM - 5:00 AM
        start_time: "20:00"
        end_time: "05:00"
        sensitivity_multiplier: 0.6
        area_threshold_multiplier: 1.5
        
      rush_hour: # 7:00-9:00 AM, 4:00-6:00 PM
        periods:
          - start_time: "07:00"
            end_time: "09:00"
          - start_time: "16:00"
            end_time: "18:00"
        sensitivity_multiplier: 1.5
        cooldown_period: 5
        
  # Weather-based adaptation
  weather_adaptation:
    enabled: true
    
    conditions:
      clear:
        sensitivity_multiplier: 1.0
        area_threshold_multiplier: 1.0
        
      cloudy:
        sensitivity_multiplier: 0.9
        area_threshold_multiplier: 1.1
        
      rain:
        sensitivity_multiplier: 1.5
        area_threshold_multiplier: 1.3
        noise_filter_enhanced: true
        
      heavy_rain:
        sensitivity_multiplier: 2.0
        area_threshold_multiplier: 1.5
        temporal_averaging: 5
        
      snow:
        sensitivity_multiplier: 2.5
        area_threshold_multiplier: 2.0
        temporal_averaging: 7
        
      fog:
        sensitivity_multiplier: 0.7
        contrast_enhancement: true
        
      wind:
        sensitivity_multiplier: 1.2
        roi_masking_strict: true

# Region of Interest (ROI) Configuration
roi:
  enabled: true
  config_file: "/etc/traffic-monitoring/roi-masks.json"
  
  # Predefined ignore zones
  ignore_zones:
    trees_and_vegetation:
      enabled: true
      coordinates: []  # Defined in roi-masks.json
      
    sky_area:
      enabled: true
      coordinates: []
      
    building_edges:
      enabled: true
      coordinates: []
      
  # Focus zones (higher sensitivity)
  focus_zones:
    road_area:
      enabled: true
      coordinates: []
      sensitivity_multiplier: 1.2
      
    intersection:
      enabled: false
      coordinates: []
      sensitivity_multiplier: 1.5

# Performance Configuration
performance:
  # CPU usage limits
  max_cpu_usage: 80            # Percentage
  cpu_monitoring_interval: 5   # Seconds
  
  # Memory management
  max_memory_usage: 200        # MB
  memory_monitoring_interval: 10 # Seconds
  garbage_collection_interval: 300 # Seconds
  
  # Processing optimization
  optimization_mode: "balanced"  # performance, efficiency, balanced
  adaptive_processing: true      # Adjust processing based on load
  skip_frames_under_load: true   # Skip processing frames when overloaded
  
  # Thread management
  max_worker_threads: 2
  opencv_thread_limit: 2
  
  # I/O optimization
  async_file_operations: true
  batch_logging: true
  log_buffer_size: 100

# Integration Configuration
integration:
  # Hybrid system coordination
  periodic_capture_coordination: true
  periodic_interval_seconds: 900    # 15 minutes when motion enabled
  
  # Container communication
  # Avoid setting container_name to allow compose to namespace containers per project
  # (container_name example removed — avoid using fixed container names in compose)
  shared_storage_path: "/mnt/storage"
  
  # Capture script integration
  capture_script_path: "/home/merk/CST_590_Computer_Science_Capstone_Project/scripts/capture-and-process.sh"
  high_res_capture_timeout: 30
  
  # API integration
  api_endpoint: "http://localhost:5000"
  health_check_interval: 60
  
# Logging and Monitoring
logging:
  # Log levels and destinations
  file_logging: true
  console_logging: false
  syslog_logging: true
  
  # Log rotation
  max_log_file_size: "10MB"
  max_log_files: 5
  
  # Debug logging
  debug_save_frames: false       # Save frames for debugging
  debug_frame_directory: "/tmp/motion-debug"
  debug_max_frames: 100
  
  # Performance logging
  log_performance_metrics: true
  performance_log_interval: 300  # Seconds
  
# Alerting and Notifications
alerting:
  enabled: false
  
  # Alert conditions
  high_false_positive_rate: 0.3   # Alert if >30% false positives
  system_overload_threshold: 90   # Alert if >90% CPU for >5 minutes
  motion_service_failure: true    # Alert if service stops
  
  # Notification methods
  email_notifications: false
  webhook_notifications: false
  log_alerts: true

# Development and Testing
development:
  # Testing modes
  test_mode: false
  simulate_motion: false
  playback_video_file: null
  
  # Calibration assistance
  show_motion_overlay: false
  save_calibration_images: false
  calibration_image_directory: "/tmp/motion-calibration"
  
  # Performance profiling
  enable_profiling: false
  profiling_output_directory: "/tmp/motion-profiling"
```

### ROI Masks Configuration

```json
{
  "roi_masks": {
    "version": "1.0",
    "camera_resolution": {
      "width": 320,
      "height": 240
    },
    "ignore_zones": {
      "trees_and_vegetation": [
        {
          "name": "tree_left_side",
          "coordinates": [
            [10, 50],
            [80, 50],
            [80, 180],
            [10, 180]
          ],
          "description": "Large tree on left side of frame"
        },
        {
          "name": "bushes_right",
          "coordinates": [
            [250, 100],
            [310, 100],
            [310, 200],
            [250, 200]
          ],
          "description": "Bushes and vegetation on right"
        }
      ],
      "sky_area": [
        {
          "name": "sky_upper_portion",
          "coordinates": [
            [0, 0],
            [320, 0],
            [320, 60],
            [0, 60]
          ],
          "description": "Upper portion of frame (sky, clouds, birds)"
        }
      ],
      "building_edges": [
        {
          "name": "building_corner",
          "coordinates": [
            [0, 80],
            [30, 80],
            [30, 240],
            [0, 240]
          ],
          "description": "Building corner that creates shadows"
        }
      ]
    },
    "focus_zones": {
      "road_area": [
        {
          "name": "main_road",
          "coordinates": [
            [80, 120],
            [240, 120],
            [240, 220],
            [80, 220]
          ],
          "sensitivity_multiplier": 1.2,
          "description": "Main road area where vehicles travel"
        }
      ],
      "intersection": [
        {
          "name": "intersection_center",
          "coordinates": [
            [120, 100],
            [200, 100],
            [200, 180],
            [120, 180]
          ],
          "sensitivity_multiplier": 1.5,
          "description": "Intersection center - high activity area"
        }
      ]
    }
  }
}
```

### Environmental Profiles

```yaml
# /etc/traffic-monitoring/environmental-profiles.yaml
# Predefined environmental adaptation profiles

profiles:
  suburban_residential:
    description: "Residential area with trees, occasional pedestrians"
    base_sensitivity: 0.8
    focus_on_vehicles: true
    ignore_pedestrians: false
    tree_motion_tolerance: high
    
    time_adjustments:
      school_hours:
        start_time: "07:30"
        end_time: "08:30"
        end_time_afternoon: "15:00"
        end_time_afternoon_end: "16:00"
        sensitivity_multiplier: 1.3
        
  urban_busy_street:
    description: "Busy urban street with constant traffic"
    base_sensitivity: 1.2
    cooldown_period: 5
    high_activity_mode: true
    
    rush_hour_adjustments:
      morning:
        start_time: "07:00"
        end_time: "09:30"
        sensitivity_multiplier: 1.5
        max_triggers_per_minute: 10
      evening:
        start_time: "16:30"
        end_time: "19:00"
        sensitivity_multiplier: 1.5
        max_triggers_per_minute: 10
        
  rural_highway:
    description: "Rural highway with occasional traffic"
    base_sensitivity: 0.9
    large_vehicle_focus: true
    speed_compensation: true
    
    weather_sensitivity:
      wind: 1.5  # More sensitive to wind affecting roadside vegetation
      
  parking_lot:
    description: "Parking lot with slow-moving vehicles and pedestrians"
    base_sensitivity: 1.1
    slow_motion_detection: true
    pedestrian_filtering: enhanced
    
  industrial_area:
    description: "Industrial area with trucks and heavy vehicles"
    base_sensitivity: 1.0
    large_vehicle_priority: true
    noise_tolerance: high
    vibration_filtering: enhanced

# Weather-specific presets
weather_presets:
  clear_day:
    contrast_enhancement: false
    shadow_filtering: standard
    sensitivity_adjustment: 1.0
    
  overcast:
    contrast_enhancement: slight
    shadow_filtering: reduced
    sensitivity_adjustment: 0.9
    
  light_rain:
    noise_filtering: enhanced
    temporal_averaging: 3
    sensitivity_adjustment: 1.3
    
  heavy_rain:
    noise_filtering: maximum
    temporal_averaging: 5
    sensitivity_adjustment: 1.8
    roi_masking_strict: true
    
  snow:
    particle_filtering: enabled
    temporal_averaging: 7
    sensitivity_adjustment: 2.2
    contrast_enhancement: enhanced
    
  fog_mist:
    contrast_enhancement: maximum
    edge_detection_enhanced: true
    sensitivity_adjustment: 0.7
    
  windy_conditions:
    vegetation_filtering: enhanced
    roi_ignore_zones_expanded: true
    temporal_stability_required: 4
    sensitivity_adjustment: 1.4

# Lighting condition presets
lighting_presets:
  bright_sunlight:
    exposure_compensation: true
    shadow_detection: enhanced
    glare_filtering: enabled
    
  golden_hour:
    dynamic_range_optimization: true
    shadow_transition_handling: true
    
  artificial_lighting:
    flicker_compensation: enabled
    color_balance_adjustment: true
    
  low_light:
    noise_reduction: enhanced
    gain_compensation: automatic
    motion_blur_tolerance: increased
    
  mixed_lighting:
    adaptive_exposure: enabled
    local_contrast_enhancement: true
```

## Configuration Management Commands

### Validation and Testing

```bash
# Validate configuration files
motion-config --validate

# Test configuration with sample video
motion-config --test-config /path/to/test/video.mp4

# Interactive configuration wizard
motion-config --wizard

# Generate configuration from template
motion-config --generate-template suburban_residential

# Backup and restore configuration
motion-config --backup /path/to/backup/
motion-config --restore /path/to/backup/motion-config-backup.tar.gz
```

### Runtime Configuration Updates

```bash
# Reload configuration without restarting service
motion-config --reload

# Update specific parameter
motion-config --set trigger.cooldown_period=15

# Enable debug mode temporarily
motion-config --debug-mode on --duration 300  # 5 minutes

# Switch environmental profile
motion-config --profile urban_busy_street

# Adjust sensitivity for current conditions
motion-config --sensitivity 1.2 --duration 3600  # 1 hour
```

### Monitoring and Diagnostics

```bash
# Show current configuration status
motion-config --status

# Display performance metrics
motion-config --performance

# Show recent motion events
motion-config --events --last 24h

# Generate configuration report
motion-config --report --output /tmp/motion-config-report.html

# Export configuration for sharing
motion-config --export --anonymize --output motion-setup.yaml
```

This configuration reference provides comprehensive control over all aspects of the motion detection system, allowing for fine-tuning and adaptation to various deployment environments and conditions.
