#!/usr/bin/env python3
"""
Direct OPS243-C Radar Hardware Test
Tests UART communication and basic radar functionality
"""

import serial
import time
import sys

def test_radar_hardware():
    """Test radar hardware directly"""
    try:
        print('[TEST] Testing OPS243-C radar connection...')
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
        time.sleep(1)
        
        print('[TEST] Sending configuration commands...')
        commands = ['OJ\n', 'AL15\n', 'AH45\n', 'AE\n', '??\n']
        for cmd in commands:
            print(f'[CMD] Sending: {cmd.strip()}')
            ser.write(cmd.encode())
            time.sleep(0.5)
            response = ser.read(100)
            if response:
                print(f'[RESP] {response}')
            else:
                print('[RESP] No response')
        
        print('[TEST] Listening for radar data for 20 seconds...')
        print('[TEST] Move in front of the radar to test detection...')
        start_time = time.time()
        detection_count = 0
        
        while time.time() - start_time < 20:
            data = ser.read(100)
            if data:
                detection_count += 1
                try:
                    decoded = data.decode('utf-8', errors='ignore')
                    print(f'[DETECT #{detection_count}] {decoded.strip()}')
                except (UnicodeDecodeError, AttributeError) as e:
                    print(f'[DETECT #{detection_count}] Raw: {data}')
            time.sleep(0.1)
        
        ser.close()
        print(f'[RESULT] Test completed. {detection_count} radar readings received.')
        
        if detection_count == 0:
            print('[WARNING] No radar data received - check wiring and power')
            return False
        else:
            print('[SUCCESS] Radar is receiving data!')
            return True
            
    except serial.SerialException as e:
        print(f'[ERROR] Serial connection failed: {e}')
        return False
    except Exception as e:
        print(f'[ERROR] Unexpected error: {e}')
        return False

if __name__ == "__main__":
    success = test_radar_hardware()
    sys.exit(0 if success else 1)