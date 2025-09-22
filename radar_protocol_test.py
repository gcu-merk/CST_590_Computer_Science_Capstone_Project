#!/usr/bin/env python3
"""
OPS243-C Radar Protocol Investigation
Test different communication settings and commands
"""

import serial
import time
import sys

def test_baud_rates():
    """Test different baud rates to find the correct one"""
    baud_rates = [9600, 19200, 38400, 57600, 115200]
    
    for baud in baud_rates:
        print(f"\n=== Testing baud rate: {baud} ===")
        try:
            ser = serial.Serial('/dev/ttyAMA0', baud, timeout=2)
            time.sleep(1)
            
            # Try basic query command
            ser.write(b'??\\r\\n')
            time.sleep(0.5)
            
            response = ser.read(100)
            if response:
                print(f"Response at {baud}: {response}")
                # Try to decode
                try:
                    decoded = response.decode('utf-8', errors='ignore')
                    print(f"Decoded: '{decoded}'")
                except:
                    print("Could not decode as UTF-8")
            else:
                print(f"No response at {baud}")
            
            ser.close()
            
        except Exception as e:
            print(f"Error at {baud}: {e}")

def test_command_formats():
    """Test different command formats"""
    print("\n=== Testing Command Formats ===")
    
    try:
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=2)
        time.sleep(1)
        
        # Clear buffer
        ser.read(ser.in_waiting)
        
        commands = [
            (b'??\\r\\n', 'Query with CRLF'),
            (b'??\\n', 'Query with LF only'),
            (b'??\\r', 'Query with CR only'), 
            (b'??', 'Query plain'),
            (b'OF\\r\\n', 'Set feet/sec with CRLF'),
            (b'OM\\r\\n', 'Set mph with CRLF'),
            (b'OJ\\r\\n', 'Set JSON with CRLF'),
            (b'UC\\r\\n', 'Get units'),
            (b'PA\\r\\n', 'Query protocol'),
        ]
        
        for cmd, desc in commands:
            print(f"\nTesting: {desc}")
            print(f"Command: {cmd}")
            
            ser.write(cmd)
            time.sleep(1)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"Raw response: {response}")
                try:
                    decoded = response.decode('utf-8', errors='ignore').strip()
                    if decoded and decoded not in ['(*', '(*(*', '(*(*(*']:
                        print(f"Decoded: '{decoded}'")
                    else:
                        print("Got noise pattern")
                except:
                    print("Decode failed")
            else:
                print("No response")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

def test_continuous_read():
    """Read continuous data to understand the format"""
    print("\n=== Continuous Data Read Test ===")
    
    try:
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
        time.sleep(1)
        
        # Clear buffer
        ser.read(ser.in_waiting)
        
        print("Reading data for 15 seconds...")
        print("Move in front of radar to generate detections...")
        
        start_time = time.time()
        data_count = 0
        
        while time.time() - start_time < 15:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                if data:
                    data_count += 1
                    print(f"\\n[{data_count}] Raw: {data}")
                    
                    # Try different decodings
                    try:
                        utf8 = data.decode('utf-8', errors='ignore')
                        if utf8.strip():
                            print(f"[{data_count}] UTF-8: '{utf8.strip()}'")
                    except:
                        pass
                    
                    try:
                        ascii_clean = ''.join(chr(b) if 32 <= b <= 126 else '?' for b in data)
                        if ascii_clean.strip('?'):
                            print(f"[{data_count}] ASCII: '{ascii_clean}'")
                    except:
                        pass
            
            time.sleep(0.1)
        
        print(f"\\nReceived {data_count} data packets")
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("OPS243-C Radar Protocol Investigation")
    print("=====================================")
    
    test_baud_rates()
    test_command_formats() 
    test_continuous_read()
    
    print("\\nInvestigation complete!")