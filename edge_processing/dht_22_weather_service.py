import time
import board
import digitalio
import adafruit_dht
import redis
import os
import json
from datetime import datetime, timezone

# Configuration
GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 4))  # Default to GPIO4
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
UPDATE_INTERVAL = int(os.getenv("DHT22_UPDATE_INTERVAL", 300))  # Default: 5 minutes
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

# DHT22 sensor configuration using CircuitPython
def get_board_pin(gpio_pin):
    """Map GPIO pin number to board pin object"""
    pin_map = {
        4: board.D4,
        18: board.D18,
        23: board.D23,
        24: board.D24,
        25: board.D25,
        # Add more mappings as needed
    }
    return pin_map.get(gpio_pin, board.D4)  # Default to D4

dht_pin = get_board_pin(GPIO_PIN)
dht = adafruit_dht.DHT22(dht_pin)

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0

def read_dht22_sensor():
    """
    Read temperature and humidity from DHT22 sensor using CircuitPython DHT library
    Returns tuple of (temperature_c, humidity) or (None, None) if reading fails
    """
    try:
        # Read sensor data using CircuitPython library
        temperature_c = dht.temperature
        humidity = dht.humidity
        
        if temperature_c is not None and humidity is not None:
            return round(temperature_c, 1), round(humidity, 1)
        return None, None
    except RuntimeError as error:
        # Reading from DHT sensors can sometimes fail with a RuntimeError
        # This is common and expected, just return None values
        print(f"DHT22 reading error: {error.args[0]}")
        return None, None
    except Exception as error:
        print(f"Unexpected DHT22 error: {error}")
        return None, None

print("Starting DHT22 Weather Service")
print(f"Update interval: {UPDATE_INTERVAL} seconds")
print(f"Redis host: {REDIS_HOST}:{REDIS_PORT}")
print(f"GPIO Pin: {GPIO_PIN}")
print("Using CircuitPython DHT library")

try:
    while True:
        try:
            temperature_c, humidity = read_dht22_sensor()
            timestamp = datetime.now(timezone.utc).isoformat()

            if temperature_c is not None and humidity is not None:
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
                print(f"Updated Redis {REDIS_KEY}: {data}")
            else:
                print("Failed to read DHT22 sensor - temperature or humidity returned None")
        except Exception as e:
            print(f"Error reading DHT22 sensor or writing to Redis: {e}")
        time.sleep(UPDATE_INTERVAL)
except KeyboardInterrupt:
    print("DHT22 service stopped by user")
finally:
    # Clean up the DHT sensor
    try:
        dht.exit()
    except:
        pass
    print("DHT22 service cleanup completed")