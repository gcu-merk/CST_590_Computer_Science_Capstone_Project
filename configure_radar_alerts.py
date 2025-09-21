#!/usr/bin/env python3
"""
Radar Configuration and Testing Script
Configures OPS243-C radar with speed alert thresholds and tests GPIO integration
"""

import time
import serial
import logging
import sys
from datetime import datetime

# Radar configuration constants
RADAR_PORT = '/dev/ttyACM0'  # Default radar serial port
RADAR_BAUDRATE = 9600
LOW_SPEED_ALERT = 15   # mph - triggers GPIO5 (Blue wire)
HIGH_SPEED_ALERT = 45  # mph - triggers GPIO6 (Purple wire)

def log_with_timestamp(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def find_radar_port():
    """Find the radar serial port"""
    import glob
    
    # Common serial port patterns
    patterns = ['/dev/ttyACM*', '/dev/ttyUSB*', '/dev/serial/by-id/*OPS243*']
    
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            log_with_timestamp(f"Found potential radar ports: {ports}")
            return ports[0]
    
    log_with_timestamp("No radar serial ports found")
    return None

def configure_radar_speed_alerts():
    """Configure radar speed alert thresholds"""
    log_with_timestamp("🔧 Configuring OPS243-C Radar Speed Alerts...")
    
    # Try to find the radar port
    radar_port = find_radar_port()
    if not radar_port:
        radar_port = RADAR_PORT
        log_with_timestamp(f"Using default port: {radar_port}")
    
    try:
        # Open serial connection
        ser = serial.Serial(radar_port, RADAR_BAUDRATE, timeout=2)
        time.sleep(0.5)  # Allow device to initialize
        
        log_with_timestamp(f"✅ Connected to radar on {radar_port}")
        
        # Send configuration commands
        commands = [
            ("OJ", "Set JSON output mode"),
            (f"AL{LOW_SPEED_ALERT:02d}", f"Set low speed alert to {LOW_SPEED_ALERT} mph (GPIO5/Blue)"),
            (f"AH{HIGH_SPEED_ALERT:02d}", f"Set high speed alert to {HIGH_SPEED_ALERT} mph (GPIO6/Purple)"),
            ("AE", "Enable speed alerts"),
            ("OJ", "Confirm JSON output mode"),
            ("??", "Query current settings")
        ]
        
        for cmd, description in commands:
            log_with_timestamp(f"📤 Sending: {cmd} - {description}")
            ser.write(f"{cmd}\n".encode())
            time.sleep(0.2)
            
            # Read response
            try:
                response = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore').strip()
                if response:
                    log_with_timestamp(f"📥 Response: {response}")
            except Exception as e:
                log_with_timestamp(f"⚠️  Error reading response: {e}")
        
        # Test radar reading
        log_with_timestamp("🎯 Testing radar readings...")
        for i in range(5):
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        log_with_timestamp(f"📊 Radar data: {line}")
            except Exception as e:
                log_with_timestamp(f"⚠️  Error reading data: {e}")
            time.sleep(1)
        
        ser.close()
        log_with_timestamp("✅ Radar configuration completed")
        return True
        
    except Exception as e:
        log_with_timestamp(f"❌ Radar configuration failed: {e}")
        return False

def test_radar_with_gpio():
    """Test radar service with GPIO integration"""
    log_with_timestamp("🧪 Testing radar service with GPIO integration...")
    
    try:
        # Import the radar service
        import sys
        sys.path.append('/mnt/storage')
        from ops243_radar_service import OPS243Service
        
        def radar_callback(data):
            """Handle radar data"""
            if 'speed' in data:
                speed = data['speed']
                log_with_timestamp(f"🚗 Vehicle detected: {speed} mph")
                
                # Check if speed triggers alerts
                if speed >= HIGH_SPEED_ALERT:
                    log_with_timestamp(f"🚨 HIGH SPEED ALERT: {speed} mph (should trigger GPIO6/Purple)")
                elif speed >= LOW_SPEED_ALERT:
                    log_with_timestamp(f"⚠️  LOW SPEED ALERT: {speed} mph (should trigger GPIO5/Blue)")
                else:
                    log_with_timestamp(f"✅ Normal speed: {speed} mph")
            else:
                log_with_timestamp(f"📊 Radar data: {data}")
        
        # Start radar service with GPIO pin 23 (Orange wire - Host Interrupt)
        radar_port = find_radar_port() or RADAR_PORT
        service = OPS243Service(port=radar_port, baudrate=RADAR_BAUDRATE, gpio_pin=23)
        
        log_with_timestamp(f"Starting radar service on {radar_port} with GPIO23 interrupt...")
        success = service.start(radar_callback)
        
        if success:
            log_with_timestamp("✅ Radar service started successfully")
            log_with_timestamp("🎯 Monitoring for vehicle detections...")
            log_with_timestamp("   Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                log_with_timestamp("🛑 Stopping radar service...")
                service.stop()
                log_with_timestamp("✅ Radar service stopped")
        else:
            log_with_timestamp("❌ Failed to start radar service")
            
    except Exception as e:
        log_with_timestamp(f"❌ Radar testing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    log_with_timestamp("🚀 Starting Radar Configuration and Testing...")
    
    # Step 1: Configure speed alerts
    if configure_radar_speed_alerts():
        log_with_timestamp("✅ Speed alerts configured")
    else:
        log_with_timestamp("⚠️  Speed alert configuration failed, continuing with testing...")
    
    # Step 2: Test radar with GPIO
    test_radar_with_gpio()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()