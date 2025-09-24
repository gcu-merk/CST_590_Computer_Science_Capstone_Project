#!/usr/bin/env python3
"""
Test radar service with full UART and GPIO integration
"""

import sys
import time
from datetime import datetime

# Add current directory to path
sys.path.append('/mnt/storage')

def log_msg(msg):
    ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'[{ts}] {msg}')

def radar_callback(data):
    """Handle radar detection data"""
    if 'speed' in data:
        speed = data['speed']
        log_msg(f'🚗 Vehicle detected: {speed} mph')
        
        # Check speed thresholds
        if speed >= 45:
            log_msg(f'🚨 HIGH SPEED ALERT: {speed} mph (GPIO6/Purple should trigger)')
        elif speed >= 15:
            log_msg(f'⚠️  LOW SPEED ALERT: {speed} mph (GPIO5/Blue should trigger)')
        else:
            log_msg(f'✅ Normal speed: {speed} mph')
    else:
        log_msg(f'📊 Radar data: {data}')

def test_integrated_radar():
    try:
        from ops243_radar_service import OPS243Service
        
        log_msg('🚀 Starting OPS243-C Radar Service with GPIO Integration...')
        log_msg('   UART: /dev/ttyAMA0 @ 9600 baud')
        log_msg('   GPIO: Pin 23 (Orange wire - Host Interrupt)')
        
        # Create service with UART and GPIO
        service = OPS243Service(
            port='/dev/ttyAMA0', 
            baudrate=9600, 
            gpio_pin=23  # Orange wire for host interrupt
        )
        
        success = service.start(radar_callback)
        
        if success:
            log_msg('✅ Radar service started successfully')
            log_msg('🎯 Monitoring for vehicle detections...')
            log_msg('   Speed alerts configured: 2mph (low), 26mph (high)')
            log_msg('   Press Ctrl+C to stop')
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                log_msg('🛑 Stopping radar service...')
                
        else:
            log_msg('❌ Failed to start radar service')
            
        service.stop()
        log_msg('✅ Radar service stopped')
        
    except Exception as e:
        log_msg(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_integrated_radar()