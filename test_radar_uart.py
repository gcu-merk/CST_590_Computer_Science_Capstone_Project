#!/usr/bin/env python3
"""
Simple test for OPS243-C radar via UART
"""

import time
import serial
from datetime import datetime

def log_msg(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}')

def test_radar_uart():
    log_msg('🔧 Testing OPS243-C Radar UART Connection...')
    
    try:
        # Connect to UART
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=2)
        time.sleep(0.5)
        log_msg('✅ Connected to radar on /dev/ttyAMA0')
        
        # Send configuration commands
        commands = ['OJ', 'AL15', 'AH45', 'AE', '??']
        
        for cmd in commands:
            log_msg(f'📤 Sending: {cmd}')
            ser.write(f'{cmd}\n'.encode())
            time.sleep(0.3)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                if response:
                    log_msg(f'📥 Response: {response}')
        
        # Listen for data
        log_msg('🎯 Listening for radar data...')
        for i in range(20):
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    log_msg(f'📊 Radar: {line}')
            time.sleep(0.5)
        
        ser.close()
        log_msg('✅ Test completed')
        
    except Exception as e:
        log_msg(f'❌ Error: {e}')

if __name__ == '__main__':
    test_radar_uart()