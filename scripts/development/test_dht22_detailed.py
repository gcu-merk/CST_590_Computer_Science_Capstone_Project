#!/usr/bin/env python3
"""
DHT22 Detailed Diagnostic Test
Tests DHT22 sensor communication with detailed timing analysis
"""
import time
import sys

try:
    import lgpio
    print("✅ lgpio library loaded successfully")
except ImportError as e:
    print(f"❌ lgpio library not available: {e}")
    sys.exit(1)

def detailed_dht22_test(gpio_pin=4):
    """Detailed DHT22 communication test with timing analysis"""
    gpio_handle = None
    
    try:
        # Open GPIO chip
        print(f"📍 Opening GPIO chip 4 for DHT22 on GPIO{gpio_pin}...")
        gpio_handle = lgpio.gpiochip_open(4)
        print("✅ GPIO chip 4 opened successfully")
        
        print(f"\n🔧 Starting DHT22 communication protocol...")
        
        # Step 1: Send start signal
        print("1️⃣  Sending start signal...")
        lgpio.gpio_claim_output(gpio_handle, gpio_pin)
        lgpio.gpio_write(gpio_handle, gpio_pin, 0)  # Pull low
        print("   - Pulled GPIO low")
        time.sleep(0.018)  # 18ms
        print("   - Waited 18ms")
        lgpio.gpio_write(gpio_handle, gpio_pin, 1)  # Pull high
        print("   - Pulled GPIO high")
        time.sleep(0.00003)  # 30us
        print("   - Waited 30us")
        
        # Step 2: Switch to input mode
        print("2️⃣  Switching to input mode...")
        lgpio.gpio_free(gpio_handle, gpio_pin)
        lgpio.gpio_claim_input(gpio_handle, gpio_pin)
        print("   - GPIO set to input mode")
        
        # Step 3: Wait for sensor response
        print("3️⃣  Waiting for sensor response...")
        timeout_start = time.time()
        
        # Wait for sensor to pull low (response signal)
        print("   - Waiting for sensor to pull low...")
        response_received = False
        while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
            if time.time() - timeout_start > 0.001:  # 1ms timeout
                print("   ❌ TIMEOUT: Sensor didn't respond (pull low)")
                break
        else:
            print("   ✅ Sensor pulled low (response received)")
            response_received = True
        
        if response_received:
            # Wait for sensor to pull high (prepare for data)
            print("   - Waiting for sensor to pull high...")
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 0:
                if time.time() - timeout_start > 0.002:  # 2ms timeout
                    print("   ❌ TIMEOUT: Sensor didn't prepare for data (pull high)")
                    response_received = False
                    break
            else:
                print("   ✅ Sensor pulled high (ready for data)")
        
        # Step 4: Try to read some data bits
        if response_received:
            print("4️⃣  Attempting to read data bits...")
            successful_bits = 0
            
            for bit_num in range(10):  # Try first 10 bits
                try:
                    # Wait for bit start (low signal)
                    bit_start = time.time()
                    while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                        if time.time() - bit_start > 0.0001:  # 100us timeout
                            raise Exception(f"Timeout on bit {bit_num} start")
                    
                    # Wait for data signal (high signal)
                    while lgpio.gpio_read(gpio_handle, gpio_pin) == 0:
                        if time.time() - bit_start > 0.0002:  # 200us timeout
                            raise Exception(f"Timeout on bit {bit_num} data")
                    
                    # Measure high signal duration
                    high_start = time.time()
                    while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                        if time.time() - high_start > 0.0001:  # 100us max
                            break
                    
                    high_duration = time.time() - high_start
                    bit_value = 1 if high_duration > 0.00004 else 0
                    
                    print(f"   ✅ Bit {bit_num}: {bit_value} (duration: {high_duration*1000000:.1f}us)")
                    successful_bits += 1
                    
                except Exception as e:
                    print(f"   ❌ Bit {bit_num}: {e}")
                    break
            
            print(f"   📊 Successfully read {successful_bits}/10 test bits")
        
        # Cleanup
        lgpio.gpio_free(gpio_handle, gpio_pin)
        print("✅ GPIO released")
        
        return response_received and successful_bits > 0
        
    except Exception as e:
        print(f"❌ DHT22 test failed: {e}")
        return False
        
    finally:
        if gpio_handle is not None:
            try:
                lgpio.gpiochip_close(gpio_handle)
                print("✅ GPIO chip closed")
            except Exception as e:
                pass

def check_gpio_state(gpio_pin=4):
    """Check initial GPIO state"""
    gpio_handle = None
    try:
        gpio_handle = lgpio.gpiochip_open(4)
        lgpio.gpio_claim_input(gpio_handle, gpio_pin)
        
        print(f"\n📖 Initial GPIO{gpio_pin} state analysis:")
        
        # Take multiple readings
        readings = []
        for i in range(10):
            state = lgpio.gpio_read(gpio_handle, gpio_pin)
            readings.append(state)
            time.sleep(0.01)
        
        print(f"   Readings: {readings}")
        
        if all(r == 1 for r in readings):
            print("   ✅ GPIO consistently HIGH (expected for idle DHT22)")
        elif all(r == 0 for r in readings):
            print("   ⚠️  GPIO consistently LOW (might indicate wiring issue)")
        else:
            print("   ⚠️  GPIO fluctuating (might indicate noise or loose connection)")
        
        lgpio.gpio_free(gpio_handle, gpio_pin)
        
    except Exception as e:
        print(f"   ❌ Error checking GPIO state: {e}")
    finally:
        if gpio_handle:
            lgpio.gpiochip_close(gpio_handle)

if __name__ == "__main__":
    print("🔬 DHT22 Detailed Diagnostic Test")
    print("=" * 50)
    
    check_gpio_state()
    
    print(f"\n🧪 Testing DHT22 communication...")
    success = detailed_dht22_test()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ DHT22 communication test PASSED")
        print("   The sensor is responding and communicating")
    else:
        print("❌ DHT22 communication test FAILED")
        print("   Possible issues:")
        print("   - DHT22 sensor not connected to GPIO4")
        print("   - DHT22 sensor power supply issue")
        print("   - DHT22 sensor hardware failure")
        print("   - Wiring/connection problem")