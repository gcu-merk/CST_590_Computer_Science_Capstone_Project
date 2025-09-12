# Multi-Sensor Architecture: Camera + Radar Integration

## Executive Summary

This document outlines the integration architecture for combining camera-based motion detection with radar sensors for enhanced traffic monitoring capabilities. The system supports multiple triggering strategies and provides comprehensive sensor fusion capabilities.

## Sensor Triggering Strategies

### Strategy 1: Radar-Triggered Camera (Recommended)

**Concept:** Radar detects motion/presence → Triggers high-resolution camera capture

**Advantages:**
- **Power Efficiency:** Radar sensors typically consume less power than continuous video processing
- **Weather Independence:** Radar works in fog, rain, snow, and darkness
- **Range Detection:** Radar provides accurate distance and speed measurements
- **Reliable Detection:** Less prone to false positives from lighting changes, shadows
- **Faster Response:** Radar detection is typically faster than video processing
- **Privacy Friendly:** No continuous video recording, only triggered captures

**Use Cases:**
- Speed enforcement systems
- Traffic counting and classification
- Security applications where privacy is important
- Remote locations with power constraints
- Weather-challenging environments

**Implementation:**
```
Radar Sensor → Motion Detection → Camera Trigger → High-Res Capture → Processing
```

### Strategy 2: Camera-Triggered Radar

**Concept:** Camera motion detection → Activates radar for detailed measurements

**Advantages:**
- **Visual Confirmation:** Camera provides visual context before radar activation
- **Object Classification:** Can distinguish between vehicles, pedestrians, animals
- **Direction Analysis:** Computer vision can determine movement direction
- **Cost Efficiency:** Radar only activated when needed
- **Rich Data:** Camera provides visual data for analysis and verification

**Use Cases:**
- Research and analytics applications
- Systems requiring visual verification
- Urban environments with good lighting
- Applications needing object classification

**Implementation:**
```
Camera Stream → Motion Detection → Radar Activation → Combined Analysis
```

### Strategy 3: Dual Independent Sensors with Fusion

**Concept:** Both sensors operate independently, data is fused for enhanced accuracy

**Advantages:**
- **Maximum Reliability:** Redundant detection reduces false negatives
- **Rich Dataset:** Combined visual and radar data
- **Fault Tolerance:** System continues operating if one sensor fails
- **Enhanced Accuracy:** Cross-validation between sensors
- **Comprehensive Analysis:** Speed, size, direction, classification

**Use Cases:**
- Critical traffic monitoring applications
- Research and development
- High-accuracy measurement requirements
- Safety-critical applications

## Recommended Architecture: Radar-Triggered Edge AI Camera

Based on typical traffic monitoring requirements, the radar-triggered camera approach with on-camera AI processing is recommended for most deployments.

### Enhanced System Architecture with Edge AI

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Radar Sensor  │────│   Raspberry Pi 5     │────│   IMX500 AI Camera │
│   (Detection)   │    │   (Coordination)     │    │   (AI Processing)   │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
        │                        │                           │
        │ Motion Alert           │ Trigger Signal            │ Image + AI Results
        │                        │                           │
        └────────────────────────┼───────────────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Edge Controller │
                        │  (Data Fusion &  │
                        │   Storage)       │
                        └──────────────────┘
```

### Edge AI Processing Flow

**Enhanced Processing Pipeline:**
1. **Radar Detection** → Motion/speed/direction data collected
2. **Camera Trigger** → IMX500 camera activated via I2C commands  
3. **On-Camera AI** → Vehicle classification performed directly on sensor
4. **Data Fusion** → AI results combined with radar measurements
5. **Local Storage** → Enhanced metadata with classifications stored

### Hardware Integration

**Radar Sensor Options:**
- **OPS243-C Doppler Radar:** Continuous wave, speed detection
- **mmWave Radar (77GHz):** High precision, multiple object tracking
- **Ultrasonic Sensors:** Short range, cost-effective for basic detection
- **LIDAR:** High precision, 3D mapping capabilities

**Interface Connections:**
```
Raspberry Pi 5 GPIO Connections:
├── Radar Sensor
│   ├── VCC (3.3V/5V) → Pin 2 or Pin 4
│   ├── GND → Pin 6
│   ├── TX (Data) → Pin 10 (GPIO 15, UART RX)
│   ├── RX (Commands) → Pin 8 (GPIO 14, UART TX)
│   └── Direction Pin → Pin 16 (GPIO 23)
├── Camera (IMX500)
│   ├── CSI-2 Connection (dedicated ribbon)
│   └── I2C Control (built-in)
└── Status LEDs
    ├── Radar Active → Pin 18 (GPIO 24)
    ├── Camera Active → Pin 22 (GPIO 25)
    └── System Status → Pin 24 (GPIO 8)
```

## Implementation Architecture

### Phase 1: Basic Radar-Triggered Capture

**Components:**
- Radar monitoring service
- Camera trigger interface
- Basic data logging

**Flow:**
1. Radar continuously monitors for motion
2. Motion detected → GPIO interrupt to camera system
3. Camera captures high-resolution image using rpicam-still
4. Basic metadata logged (timestamp, radar speed/direction)

### Phase 2: Enhanced Processing

**Components:**
- Vehicle classification using camera data
- Speed correlation between radar and visual analysis
- Environmental condition adaptation

**Flow:**
1. Radar detects motion
2. Camera captures image sequence (before/during/after)
3. AI processing identifies vehicle type, size, direction
4. Radar speed data correlated with visual analysis
5. Enhanced dataset stored for analysis

### Phase 3: Intelligent Sensor Fusion

**Components:**
- Multi-sensor data fusion algorithms
- Predictive triggering based on patterns
- Advanced analytics and reporting

**Flow:**
1. Radar provides continuous monitoring
2. Predictive algorithms determine optimal camera timing
3. Camera provides classification and verification
4. Machine learning improves trigger decisions over time
5. Comprehensive traffic analysis and reporting

## Technical Implementation

### Radar Integration Service

```python
# radar_monitor.py - Continuous radar monitoring service

import serial
import gpio
import time
import asyncio
from typing import Optional, Dict, Any

class RadarMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.serial_port = config['radar']['serial_port']
        self.baud_rate = config['radar']['baud_rate']
        self.trigger_pin = config['camera']['trigger_pin']
        self.radar_connection = None
        
    async def start_monitoring(self):
        """Start continuous radar monitoring"""
        self.radar_connection = serial.Serial(
            self.serial_port, 
            self.baud_rate, 
            timeout=1
        )
        
        while True:
            motion_data = await self.read_radar_data()
            if self.should_trigger_camera(motion_data):
                await self.trigger_camera_capture(motion_data)
            
            await asyncio.sleep(0.1)  # 100ms monitoring interval
    
    def should_trigger_camera(self, motion_data: Dict) -> bool:
        """Determine if camera should be triggered"""
        # Speed threshold
        if motion_data.get('speed', 0) < self.config['min_speed_kmh']:
            return False
            
        # Direction filter
        if self.config.get('direction_filter'):
            if motion_data.get('direction') not in self.config['allowed_directions']:
                return False
                
        # Range filter
        if motion_data.get('range', 0) > self.config['max_range_meters']:
            return False
            
        return True
    
    async def trigger_camera_capture(self, motion_data: Dict):
        """Trigger camera capture with radar context"""
        trigger_data = {
            'timestamp': time.time(),
            'radar_speed': motion_data.get('speed'),
            'radar_direction': motion_data.get('direction'),
            'radar_range': motion_data.get('range'),
            'trigger_source': 'radar'
        }
        
        # Trigger GPIO pin for camera
        gpio.output(self.trigger_pin, gpio.HIGH)
        await asyncio.sleep(0.1)
        gpio.output(self.trigger_pin, gpio.LOW)
        
        # Log trigger event
        await self.log_trigger_event(trigger_data)
```

### Camera Trigger Interface

```python
# camera_trigger.py - Interface between radar and camera system

import asyncio
import subprocess
import json
from datetime import datetime
from typing import Dict, Any

class CameraTriggerInterface:
    def __init__(self, config: Dict[str, Any]):
        self.capture_script = config['camera']['capture_script_path']
        self.output_directory = config['camera']['output_directory']
        self.max_capture_time = config['camera']['max_capture_time']
        
    async def handle_radar_trigger(self, radar_data: Dict[str, Any]):
        """Handle radar-triggered camera capture"""
        
        # Prepare capture metadata
        capture_metadata = {
            'trigger_source': 'radar',
            'trigger_timestamp': datetime.now().isoformat(),
            'radar_speed_kmh': radar_data.get('speed'),
            'radar_direction': radar_data.get('direction'),
            'radar_range_meters': radar_data.get('range'),
            'capture_settings': {
                'resolution': '4056x3040',
                'format': 'jpg',
                'quality': 95
            }
        }
        
        # Generate unique capture ID
        capture_id = f"radar_trigger_{int(datetime.now().timestamp())}"
        
        # Execute capture with enhanced parameters
        capture_command = [
            self.capture_script,
            '--trigger-source', 'radar',
            '--capture-id', capture_id,
            '--metadata', json.dumps(capture_metadata),
            '--output-dir', self.output_directory
        ]
        
        try:
            result = await asyncio.wait_for(
                subprocess.run(
                    capture_command,
                    capture_output=True,
                    text=True,
                    check=True
                ),
                timeout=self.max_capture_time
            )
            
            await self.process_capture_result(capture_id, result, radar_data)
            
        except asyncio.TimeoutError:
            print(f"Camera capture timeout for trigger {capture_id}")
        except subprocess.CalledProcessError as e:
            print(f"Camera capture failed: {e}")
    
    async def process_capture_result(self, capture_id: str, result, radar_data: Dict):
        """Process successful camera capture"""
        
        # Parse capture results
        capture_info = {
            'capture_id': capture_id,
            'success': True,
            'image_path': result.stdout.strip(),
            'radar_context': radar_data,
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Trigger any additional processing
        await self.trigger_image_analysis(capture_info)
        
        # Update system metrics
        await self.update_capture_metrics(capture_info)
```

### Configuration Integration

```yaml
# Enhanced configuration for multi-sensor system

# Radar Sensor Configuration
radar:
  enabled: true
  sensor_type: "OPS243-C"  # OPS243-C, mmWave, ultrasonic, lidar
  
  # Serial communication
  serial_port: "/dev/ttyUSB0"
  baud_rate: 9600
  data_bits: 8
  stop_bits: 1
  parity: "none"
  
  # Detection parameters
  min_speed_kmh: 5          # Minimum speed to trigger camera
  max_range_meters: 100     # Maximum detection range
  detection_angle: 12       # Detection beam angle in degrees
  
  # Direction filtering
  direction_filter: true
  allowed_directions: ["approaching", "receding", "both"]
  
  # Performance settings
  sampling_rate_hz: 10      # Radar data sampling frequency
  averaging_window: 3       # Number of samples to average
  noise_threshold: 0.1      # Minimum signal strength

# Camera Trigger Configuration
camera_trigger:
  # Trigger settings
  trigger_delay_ms: 50      # Delay between radar detection and camera trigger
  pre_trigger_frames: 1     # Frames to capture before trigger point
  post_trigger_frames: 2    # Frames to capture after trigger point
  
  # Capture parameters
  high_res_enabled: true    # Use high resolution for triggered captures
  burst_mode: false         # Capture multiple images per trigger
  burst_count: 3            # Number of images in burst mode
  
  # Integration with existing hybrid system
  hybrid_coordination: true
  disable_periodic_capture: false  # Keep periodic captures running
  periodic_interval_extension: 1800  # Extend interval when radar active (30 min)

# Multi-Sensor Fusion
sensor_fusion:
  enabled: false            # Enable for Phase 3 implementation
  
  # Cross-validation
  speed_correlation_threshold: 0.8  # Correlation between radar and visual speed
  direction_agreement_required: true
  
  # Data enrichment
  combine_datasets: true
  metadata_fusion: true
  
  # Machine learning
  adaptive_triggers: false  # Learn optimal trigger patterns
  false_positive_learning: true

# Data Storage and Analysis
data_storage:
  # Enhanced metadata for radar-triggered captures
  include_radar_data: true
  radar_data_fields:
    - speed_kmh
    - direction
    - range_meters
    - signal_strength
    - detection_confidence
  
  # Performance metrics
  track_trigger_accuracy: true
  measure_response_latency: true
  
# System Integration
integration:
  # API enhancements for radar data
  api_radar_endpoint: "/api/radar-status"
  api_trigger_history: "/api/trigger-history"
  
  # Monitoring and alerting
  radar_health_monitoring: true
  trigger_performance_alerts: true
  
  # External system integration
  webhook_on_trigger: false
  external_analytics_push: false
```

### Performance Considerations

### Latency Optimization

**Radar-to-Camera-AI Trigger Latency:**
- Target: <350ms from radar detection to vehicle classification
- GPIO interrupt handling: <10ms
- Camera initialization: <50ms
- Image capture execution: <150ms
- **On-camera AI inference: <100ms**
- **Data correlation: <40ms**

**Optimization Strategies:**
- Keep camera system in warm standby mode
- **Pre-load AI models onto IMX500 sensor**
- Use hardware interrupts for radar signals
- **Optimize AI model size for inference speed**
- **Parallel processing of radar and AI data**

### Power Management

**Enhanced Edge AI Power Profile:**
- Radar continuous operation: 0.5-2W
- **Camera triggered operation with AI: <3W average**
- **IMX500 AI processing: 2-3W during inference**
- Total system power: **4-6W average** vs 12-15W continuous processing

**Battery Life Estimation:**
- 12V 7Ah battery: **20-35 hours operation** with edge AI
- Solar panel integration: Sustained operation
- Power management modes for extended deployment

### Data Storage

**Enhanced Metadata Structure for Edge AI:**
```json
{
  "capture_info": {
    "capture_id": "radar_trigger_1725984000",
    "timestamp": "2024-09-10T14:00:00Z",
    "trigger_source": "radar",
    "image_path": "/mnt/storage/captures/radar_trigger_1725984000.jpg"
  },
  "radar_data": {
    "speed_kmh": 45.2,
    "direction": "approaching",
    "range_meters": 75.3,
    "signal_strength": 0.85,
    "detection_confidence": 0.92
  },
  "ai_classification": {
    "primary_vehicle_type": "SUV",
    "confidence": 0.87,
    "bounding_box": {
      "x1": 120, "y1": 150,
      "x2": 280, "y2": 350
    },
    "estimated_size": {
      "width_meters": 2.1,
      "height_meters": 1.8
    },
    "inference_time_ms": 95,
    "model_version": "vehicle_classifier_v3"
  },
  "camera_data": {
    "resolution": "4056x3040",
    "file_size_mb": 1.4,
    "capture_latency_ms": 145
  },
  "correlation_analysis": {
    "speed_radar_ai_match": true,
    "size_category_validation": "confirmed",
    "confidence_boost": 0.1
  },
  "environmental": {
    "weather": "clear",
    "lighting": "daylight",
    "temperature_c": 22
  }
}
```

## Implementation Roadmap

### Phase 1: Basic Radar Integration with Edge AI (Week 1-2)

**Components:**
- Radar monitoring service
- IMX500 AI camera integration
- Basic edge AI vehicle classification
- Enhanced data logging with AI results

**Flow:**
1. Radar continuously monitors for motion
2. Motion detected → GPIO interrupt to camera system
3. Camera captures high-resolution image using rpicam-still
4. **On-camera AI performs vehicle classification**
5. **Enhanced metadata logged (timestamp, radar speed/direction, vehicle type, confidence)**

### Phase 2: Enhanced Edge Processing (Week 3-4)

**Components:**
- **Advanced vehicle classification with multiple models**
- **Speed correlation between radar and AI size estimation**
- **Environmental condition adaptation for AI models**
- **Real-time data fusion algorithms**

**Flow:**
1. Radar detects motion
2. **Camera captures image with optimized AI inference**
3. **On-camera AI identifies vehicle type, size, confidence**
4. **Radar speed data correlated with AI visual analysis**
5. **Enhanced dataset stored with vehicle classifications**

### Phase 3: Intelligent Edge AI Fusion (Week 5-6)

**Components:**
- **Multi-sensor data fusion with AI confidence weighting**
- **Predictive triggering based on vehicle approach patterns**
- **Advanced analytics with real-time vehicle classification**
- **Machine learning for trigger optimization**

**Flow:**
1. Radar provides continuous monitoring
2. **AI-enhanced predictive algorithms determine optimal camera timing**
3. **Camera provides classification and size estimation**
4. **Machine learning improves both trigger decisions and AI accuracy over time**
5. **Comprehensive traffic analysis with real-time vehicle identification**

### Phase 4: Production Deployment (Week 7-8)
- System hardening and error handling
- Comprehensive testing and validation
- Documentation and operational procedures
- Performance monitoring and maintenance

## Next Steps

1. **Radar Sensor Selection:** Choose appropriate radar sensor based on requirements
2. **Hardware Integration:** Plan GPIO connections and power requirements
3. **Software Architecture:** Design radar monitoring service architecture
4. **Testing Strategy:** Develop validation and performance testing procedures
5. **Configuration Design:** Create comprehensive configuration management

The radar-triggered camera approach provides an optimal balance of power efficiency, reliability, and comprehensive data collection for most traffic monitoring applications.
