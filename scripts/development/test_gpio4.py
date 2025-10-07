#!/usr/bin/env python3
"""
GPIO4 Test Script
Tests basic GPIO4 functionality to verify hardware connectivity
"""
import time
import sys

try:
    import lgpio
    print("✅ lgpio library loaded successfully")
except ImportError as e:
    print(f"❌ lgpio library not available: {e}")
    sys.exit(1)

def test_gpio4():
    """Test GPIO4 basic functionality"""
    gpio_handle = None
    gpio_pin = 4
    
    try:
        # Open GPIO chip
        print("📍 Opening GPIO chip 4...")
        gpio_handle = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4
        print("✅ GPIO chip 4 opened successfully")
        
        # Test output mode
        print(f"🔧 Setting GPIO{gpio_pin} as output...")
        lgpio.gpio_claim_output(gpio_handle, gpio_pin)
        print(f"✅ GPIO{gpio_pin} claimed as output")
        
        # Test writing high/low
        print(f"⬆️  Setting GPIO{gpio_pin} HIGH...")
        lgpio.gpio_write(gpio_handle, gpio_pin, 1)
        time.sleep(0.5)
        
        print(f"⬇️  Setting GPIO{gpio_pin} LOW...")
        lgpio.gpio_write(gpio_handle, gpio_pin, 0)
        time.sleep(0.5)
        
        # Release output mode
        lgpio.gpio_free(gpio_handle, gpio_pin)
        print(f"✅ GPIO{gpio_pin} released from output mode")
        
        # Test input mode
        print(f"🔧 Setting GPIO{gpio_pin} as input...")
        lgpio.gpio_claim_input(gpio_handle, gpio_pin)
        print(f"✅ GPIO{gpio_pin} claimed as input")
        
        # Read current state
        state = lgpio.gpio_read(gpio_handle, gpio_pin)
        print(f"📖 GPIO{gpio_pin} current state: {state}")
        
        # Test multiple reads
        print("📖 Testing multiple reads...")
        for i in range(5):
            state = lgpio.gpio_read(gpio_handle, gpio_pin)
            print(f"   Read {i+1}: {state}")
            time.sleep(0.1)
        
        # Release input mode
        lgpio.gpio_free(gpio_handle, gpio_pin)
        print(f"✅ GPIO{gpio_pin} released from input mode")
        
        print("🎉 GPIO4 test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ GPIO4 test failed: {e}")
        return False
        
    finally:
        if gpio_handle is not None:
            try:
                lgpio.gpiochip_close(gpio_handle)
                print("✅ GPIO chip closed")
            except Exception as e:
                pass

def test_gpio_devices():
    """Check available GPIO devices"""
    print("\n🔍 Checking GPIO devices...")
    
    import os
    
    # Check gpiochip devices
    gpio_devices = []
    for i in range(10):
        device = f"/dev/gpiochip{i}"
        if os.path.exists(device):
            gpio_devices.append(device)
    
    if gpio_devices:
        print(f"✅ Found GPIO devices: {gpio_devices}")
    else:
        print("❌ No GPIO devices found")
    
    # Check gpiomem devices
    gpiomem_devices = []
    for i in range(10):
        device = f"/dev/gpiomem{i}"
        if os.path.exists(device):
            gpiomem_devices.append(device)
    
    if gpiomem_devices:
        print(f"✅ Found GPIO memory devices: {gpiomem_devices}")
    else:
        print("❌ No GPIO memory devices found")

if __name__ == "__main__":
    print("🧪 GPIO4 Hardware Test")
    print("=" * 40)
    
    test_gpio_devices()
    print()
    
    success = test_gpio4()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ GPIO4 hardware test PASSED")
        sys.exit(0)
    else:
        print("❌ GPIO4 hardware test FAILED")
        sys.exit(1)