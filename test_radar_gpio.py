#!/usr/bin/env python3
"""
Test script to monitor radar GPIO pins for activity
Tests the new Blue (GPIO5) and Purple (GPIO6) wire connections
"""

import RPi.GPIO as GPIO
import time
import signal
import sys
from datetime import datetime

# GPIO Pin Assignments (matching the enhanced IMX500 service)
RADAR_HOST_INTERRUPT = 23  # Orange wire
RADAR_RESET = 24          # Yellow wire
RADAR_LOW_ALERT = 5       # Blue wire (NEW)
RADAR_HIGH_ALERT = 6      # Purple wire (NEW)

# Pin configuration
GPIO_PINS = {
    'Host Interrupt (Orange)': RADAR_HOST_INTERRUPT,
    'Reset (Yellow)': RADAR_RESET,
    'Low Alert (Blue)': RADAR_LOW_ALERT,
    'High Alert (Purple)': RADAR_HIGH_ALERT
}

def log_with_timestamp(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def gpio_callback(pin):
    """Callback function for GPIO interrupts"""
    pin_name = next((name for name, num in GPIO_PINS.items() if num == pin), f"GPIO{pin}")
    state = GPIO.input(pin)
    log_with_timestamp(f"🚨 RADAR INTERRUPT: {pin_name} -> {'HIGH' if state else 'LOW'}")

def signal_handler(signum, frame):
    """Clean shutdown on Ctrl+C"""
    log_with_timestamp("🛑 Shutting down GPIO monitoring...")
    GPIO.cleanup()
    sys.exit(0)

def main():
    """Main monitoring loop"""
    log_with_timestamp("🔧 Initializing Radar GPIO Monitor...")
    
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Set up signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Configure each pin and set up interrupt detection
    for pin_name, pin_num in GPIO_PINS.items():
        try:
            # Set up as input with pull-up resistor
            GPIO.setup(pin_num, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add interrupt detection on both rising and falling edges
            GPIO.add_event_detect(pin_num, GPIO.BOTH, callback=gpio_callback, bouncetime=50)
            
            # Read initial state
            initial_state = GPIO.input(pin_num)
            log_with_timestamp(f"✅ {pin_name} (GPIO{pin_num}): Initial state = {'HIGH' if initial_state else 'LOW'}")
            
        except Exception as e:
            log_with_timestamp(f"❌ Error setting up {pin_name} (GPIO{pin_num}): {e}")
    
    log_with_timestamp("🎯 Monitoring radar GPIO pins for activity...")
    log_with_timestamp("   Press Ctrl+C to stop monitoring")
    
    try:
        # Main monitoring loop
        while True:
            time.sleep(1)
            
            # Periodically check pin states (every 10 seconds)
            if int(time.time()) % 10 == 0:
                states = []
                for pin_name, pin_num in GPIO_PINS.items():
                    try:
                        state = GPIO.input(pin_num)
                        states.append(f"{pin_name}={'H' if state else 'L'}")
                    except:
                        states.append(f"{pin_name}=ERR")
                
                log_with_timestamp(f"📊 Status: {' | '.join(states)}")
                time.sleep(1)  # Avoid duplicate logs
                
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()