#!/usr/bin/env python3
"""
Simplified OPS243-C Radar Service for UART testing
"""

import time
import serial
import json
import threading
import logging
from datetime import datetime
from typing import Callable, Optional, Dict

LOGGER = logging.getLogger(__name__)

class SimpleRadarService:
    """Simplified radar service for OPS243-C via UART"""
    
    def __init__(self, port='/dev/ttyAMA0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.callback = None
        self.thread = None
    
    def start(self, callback: Callable[[Dict], None]) -> bool:
        """Start the radar service"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(0.5)
            
            # Configure radar
            commands = ['OJ', 'AL15', 'AH45', 'AE']
            for cmd in commands:
                self.ser.write(f'{cmd}\n'.encode())
                time.sleep(0.2)
            
            self.callback = callback
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            
            LOGGER.info(f"Radar service started on {self.port}")
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to start radar service: {e}")
            return False
    
    def _read_loop(self):
        """Read data from radar"""
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        data = self._parse_line(line)
                        if data and self.callback:
                            self.callback(data)
                time.sleep(0.1)
            except Exception as e:
                LOGGER.error(f"Error in read loop: {e}")
                time.sleep(0.5)
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """Parse radar data line"""
        if not line:
            return None
            
        # Try JSON first
        try:
            if line.startswith('{'):
                data = json.loads(line)
                data['_ts'] = time.time()
                return data
        except (json.JSONDecodeError, ValueError) as e:
            pass
        
        # Try simple format
        parts = line.split()
        if len(parts) >= 2:
            try:
                speed = float(parts[0])
                unit = parts[1]
                return {
                    'speed': speed, 
                    'unit': unit, 
                    '_raw': line, 
                    '_ts': time.time()
                }
            except (ValueError, IndexError) as e:
                pass
        
        return {'_raw': line, '_ts': time.time()}
    
    def stop(self):
        """Stop the radar service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.ser:
            self.ser.close()
        LOGGER.info("Radar service stopped")

def test_radar():
    """Test the radar service"""
    def log_msg(msg):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f'[{ts}] {msg}')
    
    def radar_callback(data):
        if 'speed' in data:
            speed = data['speed']
            log_msg(f'🚗 Vehicle: {speed} mph')
            if speed >= 45:
                log_msg(f'🚨 HIGH SPEED: {speed} mph (GPIO6/Purple)')
            elif speed >= 15:
                log_msg(f'⚠️  LOW SPEED: {speed} mph (GPIO5/Blue)')
        else:
            log_msg(f'📊 Data: {data}')
    
    log_msg('🚀 Starting simplified radar service...')
    service = SimpleRadarService()
    
    if service.start(radar_callback):
        log_msg('✅ Service started, monitoring...')
        try:
            time.sleep(30)  # Monitor for 30 seconds
        except KeyboardInterrupt:
            pass
        service.stop()
    else:
        log_msg('❌ Failed to start service')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_radar()