import time
import redis
import os
import json
import subprocess
import sys
from datetime import datetime, timezone

# Import lgpio for modern GPIO access
try:
    import lgpio
    LGPIO_AVAILABLE = True
    print("lgpio library loaded successfully")
except ImportError as e:
    print(f"lgpio not available: {e}")
    LGPIO_AVAILABLE = False
    sys.exit(1)  # Fail fast if lgpio is not available

# Initialize GPIO handle
gpio_handle = None
if LGPIO_AVAILABLE:
    try:
        gpio_handle = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4
        print("GPIO chip 4 opened successfully")
    except Exception as e:
        print(f"Failed to open GPIO chip 4: {e}")
        sys.exit(1)

# Configuration
GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 4))  # Default to GPIO4
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
UPDATE_INTERVAL = int(os.getenv("DHT22_UPDATE_INTERVAL", 600))  # Default: 10 minutes
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

def read_dht22_lgpio(gpio_pin):
    """
    Read DHT22 sensor using lgpio library with proper bit-bang protocol
    Returns tuple of (temperature_c, humidity) or (None, None) if reading fails
    NO FALLBACKS - Real sensor only!
    """
    if not LGPIO_AVAILABLE or gpio_handle is None:
        raise RuntimeError("GPIO not available - cannot read DHT22 sensor")
    
    try:
        # DHT22 communication protocol:
        # 1. Send start signal: Pull low for 1-10ms, then high for 20-40us
        lgpio.gpio_claim_output(gpio_handle, gpio_pin)
        lgpio.gpio_write(gpio_handle, gpio_pin, 0)  # Pull low
        time.sleep(0.018)  # Wait 18ms (DHT22 start signal)
        lgpio.gpio_write(gpio_handle, gpio_pin, 1)  # Pull high
        time.sleep(0.00003)  # Wait 30us
        
        # Switch to input mode to read sensor response
        lgpio.gpio_free(gpio_handle, gpio_pin)
        lgpio.gpio_claim_input(gpio_handle, gpio_pin)
        
        # Read the data bits
        data_bits = []
        timeout_start = time.time()
        
        # Wait for sensor to pull low (response signal)
        while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
            if time.time() - timeout_start > 0.001:  # 1ms timeout
                raise RuntimeError("DHT22 timeout waiting for response signal")
        
        # Wait for sensor to pull high (prepare for data)
        while lgpio.gpio_read(gpio_handle, gpio_pin) == 0:
            if time.time() - timeout_start > 0.002:  # 2ms timeout
                raise RuntimeError("DHT22 timeout waiting for data preparation")
        
        # Read 40 bits of data
        for i in range(40):
            # Wait for bit start (low signal)
            bit_start = time.time()
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                if time.time() - bit_start > 0.0001:  # 100us timeout
                    raise RuntimeError(f"DHT22 timeout on bit {i} start")
            
            # Wait for data signal (high signal)
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 0:
                if time.time() - bit_start > 0.0002:  # 200us timeout
                    raise RuntimeError(f"DHT22 timeout on bit {i} data")
            
            # Measure high signal duration to determine bit value
            high_start = time.time()
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                if time.time() - high_start > 0.0001:  # 100us max
                    break
            
            high_duration = time.time() - high_start
            # DHT22: 26-28us = 0, 70us = 1
            data_bits.append(1 if high_duration > 0.00004 else 0)  # 40us threshold
        
        # Debug: Print raw data bits for first 10 bits to check data integrity
        print(f"First 10 data bits: {data_bits[:10]}")
        print(f"Last 10 data bits: {data_bits[-10:]}")
        
        # Convert bits to bytes
        humidity_high = 0
        humidity_low = 0
        temp_high = 0
        temp_low = 0
        checksum = 0
        
        for i in range(8):
            humidity_high = (humidity_high << 1) | data_bits[i]
        for i in range(8, 16):
            humidity_low = (humidity_low << 1) | data_bits[i]
        for i in range(16, 24):
            temp_high = (temp_high << 1) | data_bits[i]
        for i in range(24, 32):
            temp_low = (temp_low << 1) | data_bits[i]
        for i in range(32, 40):
            checksum = (checksum << 1) | data_bits[i]
        
        # Debug: Print raw data bytes
        print(f"Raw DHT22 bytes: H_high={humidity_high:02x}({humidity_high}) H_low={humidity_low:02x}({humidity_low}) T_high={temp_high:02x}({temp_high}) T_low={temp_low:02x}({temp_low}) Checksum={checksum:02x}({checksum})")
        
        # Verify checksum
        calculated_checksum = (humidity_high + humidity_low + temp_high + temp_low) & 0xFF
        if checksum != calculated_checksum:
            raise RuntimeError(f"DHT22 checksum error: expected {checksum}, got {calculated_checksum}")
        
        # Calculate actual values according to DHT22 datasheet
        humidity = ((humidity_high << 8) | humidity_low) / 10.0
        temperature_raw = ((temp_high & 0x7F) << 8) | temp_low
        temperature = temperature_raw / 10.0
        
        # Handle negative temperature (MSB of temp_high indicates sign)
        if temp_high & 0x80:
            temperature = -temperature
        
        # Debug: Print calculated values and conversion steps
        print(f"Humidity calculation: ({humidity_high} << 8) | {humidity_low} = {(humidity_high << 8) | humidity_low} / 10.0 = {humidity}%")
        print(f"Temperature calculation: ({temp_high & 0x7F} << 8) | {temp_low} = {temperature_raw} / 10.0 = {temperature}°C")
        print(f"Temperature sign bit: {bool(temp_high & 0x80)} (negative: {temp_high & 0x80 != 0})")
        
        # Temperature sanity check and potential correction
        original_temp = temperature
        if temperature > 50.0:  # Unrealistic indoor temperature in Celsius
            # Check if this might be Fahrenheit data being interpreted as Celsius
            if 32.0 <= temperature <= 120.0:  # Reasonable Fahrenheit range
                # Convert from Fahrenheit to Celsius
                temperature = (temperature - 32.0) * 5.0 / 9.0
                print(f"Temperature anomaly detected: {original_temp}°C seems like Fahrenheit")
                print(f"Auto-correcting: {original_temp}°F → {temperature:.1f}°C")
            else:
                print(f"WARNING: Extreme temperature reading: {temperature}°C")
        
        print(f"Final calculated values: temp={temperature}°C, humidity={humidity}%")
        
        # Validate sensor ranges
        if humidity < 0 or humidity > 100:
            raise RuntimeError(f"DHT22 humidity out of range: {humidity}%")
        if temperature < -40 or temperature > 80:
            raise RuntimeError(f"DHT22 temperature out of range: {temperature}°C")
        
        print(f"DHT22 sensor reading: {temperature}°C, {humidity}%")
        return temperature, humidity
        
    except Exception as e:
        print(f"DHT22 sensor read failed: {e}")
        raise  # Re-raise the exception instead of returning None
    finally:
        try:
            lgpio.gpio_free(gpio_handle, gpio_pin)
        except:
            pass

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0

print("Starting DHT22 Weather Service")
print(f"Update interval: {UPDATE_INTERVAL} seconds (10 minutes)")
print(f"Redis host: {REDIS_HOST}:{REDIS_PORT}")
print(f"GPIO Pin: {GPIO_PIN}")
print("Using lgpio library - NO FALLBACKS, real sensor only!")

try:
    while True:
        try:
            # This will raise an exception if sensor reading fails
            temperature_c, humidity = read_dht22_lgpio(GPIO_PIN)
            timestamp = datetime.now(timezone.utc).isoformat()
            
            temperature_f = c_to_f(temperature_c)
            data = {
                "temperature_c": temperature_c,
                "temperature_f": round(temperature_f, 1),
                "humidity": humidity,
                "timestamp": timestamp,
            }
            # Use hset mapping for redis-py 4.x compatibility
            r.hset(REDIS_KEY, mapping=data)
            # Also keep legacy plain key for compatibility with API
            r.set(f"{REDIS_KEY}:latest", json.dumps(data))
            print(f"✅ DHT22 reading successful - Updated Redis {REDIS_KEY}: {data}")
            
        except Exception as e:
            print(f"❌ DHT22 sensor failure: {e}")
            print("Will retry in 10 minutes...")
            # Do NOT write any data to Redis on failure
            
        time.sleep(UPDATE_INTERVAL)
except KeyboardInterrupt:
    print("DHT22 service stopped by user")
finally:
    # Clean up GPIO
    if gpio_handle is not None:
        try:
            lgpio.gpiochip_close(gpio_handle)
            print("GPIO cleanup completed")
        except:
            pass
    print("DHT22 service cleanup completed")