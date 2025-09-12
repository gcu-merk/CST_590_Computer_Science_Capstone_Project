# Edge AI Vehicle Classification: On-Camera Processing Architecture

## Executive Summary

This document outlines the architecture for real-time vehicle classification using the Sony IMX500 AI camera's built-in neural processing unit (NPU). The system performs radar-triggered image capture followed by immediate on-camera AI inference for vehicle type identification, minimizing latency and reducing computational load on the host Raspberry Pi.

## IMX500 AI Camera Capabilities

### Hardware Specifications

**Sony IMX500 AI Camera Module:**
- **Image Sensor:** 12.3MP (4056x3040) with AI accelerator
- **AI Processing Unit:** Dedicated neural network processor
- **Inference Performance:** Up to 3.1 TOPS (Tera Operations Per Second)
- **Supported Models:** TensorFlow Lite, ONNX (converted)
- **Memory:** On-chip memory for model storage and inference
- **Interface:** CSI-2 to Raspberry Pi + I2C for AI control

**Key Advantages:**
- **Ultra-low Latency:** Sub-100ms inference directly on sensor
- **Power Efficiency:** Dedicated AI chip vs general-purpose CPU
- **Real-time Processing:** No need to transfer high-res images for analysis
- **Privacy:** Processing happens locally, no cloud dependency
- **Bandwidth Efficiency:** Only metadata and classifications transmitted

### Supported AI Models

**Pre-trained Vehicle Classification Models:**
- **MobileNetV2-Vehicle:** Lightweight vehicle type classifier
- **YOLOv5n-Traffic:** Object detection optimized for traffic scenarios
- **EfficientDet-Vehicle:** Efficient vehicle detection and classification
- **Custom Traffic Models:** Purpose-built for traffic monitoring

**Classification Categories:**
```
Vehicle Types:
├── Passenger Vehicles
│   ├── Sedan
│   ├── SUV/Crossover
│   ├── Hatchback
│   ├── Coupe
│   └── Convertible
├── Commercial Vehicles
│   ├── Pickup Truck
│   ├── Van
│   ├── Box Truck
│   ├── Semi Truck/Tractor-Trailer
│   └── Bus
├── Specialized Vehicles
│   ├── Emergency (Police, Fire, Ambulance)
│   ├── Construction/Work Vehicles
│   ├── Recreational (RV, Camper)
│   └── Agricultural
├── Two-Wheelers
│   ├── Motorcycle
│   ├── Bicycle
│   └── Scooter/Moped
└── Other
    ├── Trailer (detached)
    ├── Unknown Vehicle
    └── Non-Vehicle Object
```

## System Architecture

### Edge Processing Flow

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

### Processing Pipeline

**Stage 1: Radar Detection**
1. Radar continuously monitors for vehicle approach
2. Speed, direction, and range data collected
3. Trigger signal sent to edge controller when thresholds met

**Stage 2: Camera Activation & Capture**
1. Edge controller receives radar trigger
2. IMX500 camera activated via I2C commands
3. High-resolution image captured (4056x3040)
4. Image automatically processed by on-camera AI

**Stage 3: On-Camera AI Inference**
1. Captured image fed to pre-loaded neural network
2. Vehicle detection and classification performed on-sensor
3. Confidence scores and bounding boxes generated
4. Results packaged with image metadata

**Stage 4: Data Fusion & Storage**
1. AI results combined with radar data
2. Enhanced metadata package created
3. High-resolution image stored with classifications
4. Summary data transmitted to central system

## Technical Implementation

### IMX500 AI Model Deployment

```python
# imx500_ai_controller.py - Control AI inference on IMX500

import cv2
import numpy as np
from picamera2 import Picamera2
import json
import time
from typing import Dict, List, Tuple, Any

class IMX500AIController:
    def __init__(self, config: Dict[str, Any]):
        self.camera = Picamera2()
        self.model_path = config['ai']['model_path']
        self.confidence_threshold = config['ai']['confidence_threshold']
        self.nms_threshold = config['ai']['nms_threshold']
        self.classification_labels = self._load_labels(config['ai']['labels_path'])
        
        # Configure camera for AI processing
        self.camera_config = self.camera.create_preview_configuration(
            main={"size": (4056, 3040)},
            controls={"FrameRate": 1}  # Single shot mode
        )
        
        # Load AI model onto IMX500
        self._load_ai_model()
    
    def _load_ai_model(self):
        """Load neural network model onto IMX500 AI accelerator"""
        try:
            # Configure IMX500 for AI inference
            ai_config = {
                "model_path": self.model_path,
                "input_resolution": (640, 640),  # Model input size
                "confidence_threshold": self.confidence_threshold,
                "nms_threshold": self.nms_threshold
            }
            
            # Load model to on-camera AI processor
            self.camera.configure(self.camera_config)
            self.camera.start()
            
            # Enable AI inference mode
            self.camera.set_controls({
                "AiMode": True,
                "AiModelPath": self.model_path,
                "AiConfidenceThreshold": self.confidence_threshold
            })
            
            print(f"AI model loaded successfully: {self.model_path}")
            
        except Exception as e:
            print(f"Failed to load AI model: {e}")
            raise
    
    def capture_and_classify(self, radar_context: Dict[str, Any]) -> Dict[str, Any]:
        """Capture image and perform on-camera AI classification"""
        
        capture_start = time.time()
        
        try:
            # Trigger single high-resolution capture with AI
            image_array = self.camera.capture_array("main")
            
            # Get AI inference results directly from camera
            ai_results = self.camera.capture_metadata().get("ai_results", {})
            
            capture_time = time.time() - capture_start
            
            # Process AI results
            classifications = self._process_ai_results(ai_results, image_array.shape)
            
            # Create comprehensive result package
            result_package = {
                "capture_info": {
                    "timestamp": time.time(),
                    "capture_latency_ms": capture_time * 1000,
                    "image_resolution": f"{image_array.shape[1]}x{image_array.shape[0]}",
                    "file_size_estimate_mb": (image_array.nbytes / 1024 / 1024)
                },
                "radar_context": radar_context,
                "ai_classifications": classifications,
                "processing_metadata": {
                    "inference_location": "on_camera_imx500",
                    "model_used": self.model_path,
                    "confidence_threshold": self.confidence_threshold,
                    "total_detections": len(classifications.get("detections", []))
                }
            }
            
            return result_package
            
        except Exception as e:
            print(f"Capture and classification failed: {e}")
            return self._create_error_result(radar_context, str(e))
    
    def _process_ai_results(self, ai_results: Dict, image_shape: Tuple) -> Dict[str, Any]:
        """Process raw AI results from IMX500"""
        
        detections = []
        height, width = image_shape[:2]
        
        # Parse detection results from camera AI
        if "detections" in ai_results:
            for detection in ai_results["detections"]:
                
                # Extract bounding box (normalized coordinates)
                bbox = detection.get("bbox", [0, 0, 0, 0])
                x1, y1, x2, y2 = [
                    int(bbox[0] * width),
                    int(bbox[1] * height),
                    int(bbox[2] * width),
                    int(bbox[3] * height)
                ]
                
                # Extract classification information
                class_id = detection.get("class_id", -1)
                confidence = detection.get("confidence", 0.0)
                
                if class_id >= 0 and class_id < len(self.classification_labels):
                    vehicle_type = self.classification_labels[class_id]
                    
                    detection_info = {
                        "vehicle_type": vehicle_type,
                        "confidence": confidence,
                        "bbox": {
                            "x1": x1, "y1": y1,
                            "x2": x2, "y2": y2,
                            "width": x2 - x1,
                            "height": y2 - y1
                        },
                        "area_pixels": (x2 - x1) * (y2 - y1),
                        "center_point": [(x1 + x2) // 2, (y1 + y2) // 2]
                    }
                    
                    detections.append(detection_info)
        
        # Determine primary vehicle (highest confidence, largest area)
        primary_vehicle = None
        if detections:
            primary_vehicle = max(detections, 
                                key=lambda d: d["confidence"] * d["area_pixels"])
        
        return {
            "detections": detections,
            "primary_vehicle": primary_vehicle,
            "detection_count": len(detections),
            "inference_time_ms": ai_results.get("inference_time_ms", 0),
            "model_confidence": ai_results.get("overall_confidence", 0.0)
        }
    
    def _load_labels(self, labels_path: str) -> List[str]:
        """Load classification labels from file"""
        try:
            with open(labels_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f"Failed to load labels: {e}")
            return ["unknown"]
    
    def _create_error_result(self, radar_context: Dict, error_msg: str) -> Dict[str, Any]:
        """Create error result package"""
        return {
            "capture_info": {
                "timestamp": time.time(),
                "success": False,
                "error": error_msg
            },
            "radar_context": radar_context,
            "ai_classifications": {
                "detections": [],
                "primary_vehicle": None,
                "detection_count": 0
            }
        }
```

### Radar-Triggered AI Pipeline

```python
# radar_ai_pipeline.py - Complete radar-to-AI processing pipeline

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import gpio

class RadarAIPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.radar_monitor = RadarMonitor(config)
        self.ai_controller = IMX500AIController(config)
        self.data_manager = EdgeDataManager(config)
        self.config = config
        
    async def start_pipeline(self):
        """Start the complete radar-to-AI processing pipeline"""
        print("Starting Radar-AI Pipeline...")
        
        # Initialize all components
        await self.radar_monitor.initialize()
        await self.ai_controller.initialize()
        await self.data_manager.initialize()
        
        # Start radar monitoring loop
        while True:
            try:
                # Wait for radar detection
                radar_data = await self.radar_monitor.wait_for_detection()
                
                if self._should_trigger_capture(radar_data):
                    await self._process_detection_event(radar_data)
                
            except Exception as e:
                print(f"Pipeline error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    def _should_trigger_capture(self, radar_data: Dict) -> bool:
        """Determine if detection should trigger AI processing"""
        
        # Speed filtering
        speed_kmh = radar_data.get('speed_kmh', 0)
        if speed_kmh < self.config['radar']['min_trigger_speed']:
            return False
        
        # Direction filtering
        direction = radar_data.get('direction', 'unknown')
        allowed_directions = self.config['radar']['allowed_directions']
        if direction not in allowed_directions:
            return False
        
        # Range filtering
        range_meters = radar_data.get('range_meters', float('inf'))
        if range_meters > self.config['radar']['max_trigger_range']:
            return False
        
        # Rate limiting
        if not self._check_rate_limit():
            return False
        
        return True
    
    async def _process_detection_event(self, radar_data: Dict):
        """Process a complete detection event"""
        
        event_id = f"event_{int(datetime.now().timestamp())}"
        print(f"Processing detection event: {event_id}")
        
        try:
            # Step 1: Capture image and perform on-camera AI
            ai_results = self.ai_controller.capture_and_classify(radar_data)
            
            # Step 2: Enhance with radar correlation
            enhanced_results = self._correlate_radar_ai_data(radar_data, ai_results)
            
            # Step 3: Store results and manage data
            await self.data_manager.store_detection_event(event_id, enhanced_results)
            
            # Step 4: Trigger any downstream processing
            await self._trigger_downstream_processing(event_id, enhanced_results)
            
            print(f"Event {event_id} processed successfully")
            
        except Exception as e:
            print(f"Failed to process event {event_id}: {e}")
    
    def _correlate_radar_ai_data(self, radar_data: Dict, ai_results: Dict) -> Dict:
        """Correlate radar measurements with AI classifications"""
        
        # Extract AI primary vehicle
        primary_vehicle = ai_results.get("ai_classifications", {}).get("primary_vehicle")
        
        # Create enhanced analysis
        correlation_analysis = {
            "speed_radar_kmh": radar_data.get('speed_kmh', 0),
            "direction_radar": radar_data.get('direction', 'unknown'),
            "range_radar_meters": radar_data.get('range_meters', 0),
            "vehicle_type_ai": primary_vehicle.get('vehicle_type') if primary_vehicle else 'none_detected',
            "confidence_ai": primary_vehicle.get('confidence') if primary_vehicle else 0.0,
            "correlation_timestamp": datetime.now().isoformat()
        }
        
        # Estimate vehicle size from AI bounding box and radar range
        if primary_vehicle and radar_data.get('range_meters'):
            bbox = primary_vehicle.get('bbox', {})
            estimated_size = self._estimate_vehicle_size(bbox, radar_data.get('range_meters'))
            correlation_analysis["estimated_size_meters"] = estimated_size
        
        # Combine all data
        enhanced_results = {
            **ai_results,
            "radar_data": radar_data,
            "correlation_analysis": correlation_analysis,
            "event_summary": {
                "detection_success": len(ai_results.get("ai_classifications", {}).get("detections", [])) > 0,
                "primary_classification": correlation_analysis["vehicle_type_ai"],
                "radar_speed": correlation_analysis["speed_radar_kmh"],
                "confidence_score": correlation_analysis["confidence_ai"]
            }
        }
        
        return enhanced_results
    
    def _estimate_vehicle_size(self, bbox: Dict, range_meters: float) -> Dict:
        """Estimate real-world vehicle size from bounding box and range"""
        
        # Camera field of view and pixel calculations
        # IMX500: approximately 62° horizontal FOV
        horizontal_fov_radians = 1.08  # ~62 degrees
        image_width_pixels = 4056
        
        # Calculate meters per pixel at the given range
        meters_per_pixel = (2 * range_meters * np.tan(horizontal_fov_radians / 2)) / image_width_pixels
        
        # Estimate vehicle dimensions
        vehicle_width_pixels = bbox.get('width', 0)
        vehicle_height_pixels = bbox.get('height', 0)
        
        estimated_width_meters = vehicle_width_pixels * meters_per_pixel
        estimated_height_meters = vehicle_height_pixels * meters_per_pixel
        
        return {
            "width_meters": round(estimated_width_meters, 2),
            "height_meters": round(estimated_height_meters, 2),
            "area_square_meters": round(estimated_width_meters * estimated_height_meters, 2)
        }
```

### Configuration for Edge AI

```yaml
# edge_ai_config.yaml - Configuration for on-camera AI processing

# IMX500 AI Camera Configuration
imx500_ai:
  # Model configuration
  model_path: "/opt/models/vehicle_classifier_v2.tflite"
  labels_path: "/opt/models/vehicle_labels.txt"
  
  # Inference parameters
  confidence_threshold: 0.7
  nms_threshold: 0.4
  max_detections: 10
  
  # Image capture settings
  capture_resolution: [4056, 3040]  # Full resolution
  capture_format: "RGB888"
  jpeg_quality: 95
  
  # AI processing optimization
  inference_threads: 1  # Use dedicated AI chip
  use_gpu_acceleration: false  # Use NPU instead
  model_warmup_frames: 3
  
# Enhanced Radar Integration
radar_ai_integration:
  # Trigger parameters optimized for AI
  trigger_speed_threshold: 10  # km/h minimum
  trigger_range_max: 80        # meters maximum
  trigger_cooldown: 2          # seconds between triggers
  
  # AI-specific triggers
  ai_warmup_time: 0.5         # seconds to warm up AI before capture
  pre_trigger_frames: 0       # No pre-trigger needed for single shot
  post_analysis_delay: 0.1    # Brief delay for AI completion
  
  # Performance optimization
  parallel_processing: false   # Process sequentially for reliability
  max_concurrent_inferences: 1
  
# Data Correlation
correlation_settings:
  # Radar-AI data fusion
  speed_estimation_ai: true    # Estimate speed from consecutive frames
  size_estimation_enabled: true
  direction_correlation: true
  
  # Vehicle classification enhancement
  speed_based_classification: true  # Use speed to refine vehicle type
  size_based_validation: true      # Validate classification with size
  
  # Confidence adjustment
  multi_sensor_confidence_boost: 0.1  # Boost confidence when radar+AI agree
  
# Vehicle Classification Models
vehicle_models:
  primary_model: "efficientdet_vehicle_v3"
  
  # Model variants for different conditions
  models:
    day_model:
      path: "/opt/models/vehicle_day_v3.tflite"
      conditions: ["daylight", "overcast"]
      
    night_model:
      path: "/opt/models/vehicle_night_v2.tflite"
      conditions: ["dusk", "night", "dawn"]
      
    weather_model:
      path: "/opt/models/vehicle_weather_v2.tflite"
      conditions: ["rain", "snow", "fog"]
  
  # Model performance settings
  model_switching:
    enabled: true
    time_based: true
    weather_based: false  # Disable for now
    
# Performance Monitoring
performance:
  # Latency targets
  target_capture_latency_ms: 200
  target_inference_latency_ms: 100
  target_total_latency_ms: 500
  
  # Monitoring
  log_performance_metrics: true
  performance_alert_threshold: 1000  # ms
  
  # Optimization
  adaptive_quality: true     # Reduce quality if latency too high
  skip_frames_on_overload: false  # Don't skip for single-shot mode
  
# Data Storage for Edge AI
edge_storage:
  # Enhanced metadata for AI results
  store_ai_confidence_scores: true
  store_bounding_boxes: true
  store_inference_timing: true
  
  # Image storage optimization
  compress_images: true
  compression_quality: 85
  store_full_resolution: true
  
  # AI model versioning
  track_model_versions: true
  model_performance_logging: true
```

## Performance Characteristics

### Latency Breakdown

**Target Performance:**
- Radar Detection → Camera Trigger: <50ms
- Camera Capture: <150ms
- On-Camera AI Inference: <100ms
- Data Correlation & Storage: <50ms
- **Total Event Processing: <350ms**

### Power Consumption

**Edge AI Power Profile:**
- Radar (continuous): 1-2W
- Raspberry Pi 5 (standby): 2-3W
- IMX500 Camera (idle): 0.5W
- IMX500 Camera (AI active): 2-3W
- **Total Average: 4-6W** (vs 12-15W for continuous processing)

### Accuracy Expectations

**Vehicle Classification Accuracy:**
- **Primary Vehicle Types**: 85-95% accuracy
- **Specific Sub-types**: 70-85% accuracy
- **Size Category**: 90-95% accuracy
- **False Positive Rate**: <5%

## Implementation Benefits

### Real-time Processing
- **Sub-second response** from detection to classification
- **No network latency** - all processing on-device
- **Immediate results** available for decision making

### Privacy & Security
- **No cloud dependency** - all data processed locally
- **Minimal data transmission** - only metadata sent
- **Enhanced privacy** - raw images stay on device

### Scalability
- **Independent operation** - each sensor unit self-contained
- **Minimal bandwidth** requirements
- **Easy deployment** - no cloud infrastructure needed

### Cost Efficiency
- **Reduced computational load** on host system
- **Lower bandwidth** requirements
- **Simplified architecture** - fewer moving parts

This edge AI architecture provides optimal performance for real-time vehicle classification while maintaining privacy and minimizing system complexity.
