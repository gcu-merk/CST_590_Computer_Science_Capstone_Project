import time
import adafruit_dht
import board
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

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Sensor setup - allow graceful fallback
SENSOR_AVAILABLE = True
try:
    dhtDevice = adafruit_dht.DHT22(getattr(board, f"D{GPIO_PIN}"))
except Exception as e:
    SENSOR_AVAILABLE = False
    print(f"Warning: Adafruit DHT sensor init failed: {e}")

def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0

def generate_mock_dht22_data():
    # simple deterministic-ish mock for environments without sensor
    import random
    base_temp_c = 22.0
    base_humidity = 45.0
    temperature_c = base_temp_c + random.uniform(-3, 3)
    humidity = base_humidity + random.uniform(-8, 8)
    return temperature_c, humidity

USE_MOCK = os.getenv("DHT22_USE_MOCK", "false").lower() in ("1", "true", "yes")

print("Starting DHT22 Weather Service")
print(f"Update interval: {UPDATE_INTERVAL} seconds")
print(f"Redis host: {REDIS_HOST}:{REDIS_PORT}")
print(f"Sensor available: {SENSOR_AVAILABLE}; USE_MOCK={USE_MOCK}")

while True:
    try:
        if (not SENSOR_AVAILABLE) or USE_MOCK:
            temperature_c, humidity = generate_mock_dht22_data()
        else:
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity

        timestamp = datetime.now(timezone.utc).isoformat()

        if temperature_c is not None and humidity is not None:
            temperature_f = c_to_f(temperature_c)
            data = {
                "temperature_c": round(temperature_c, 1),
                "temperature_f": round(temperature_f, 1),
                "humidity": round(humidity, 1),
                "timestamp": timestamp,
            }
            # Use hset mapping for redis-py 4.x compatibility
            r.hset(REDIS_KEY, mapping=data)
            # Also keep legacy plain key for compatibility with API
            r.set(f"{REDIS_KEY}:latest", json.dumps(data))
            print(f"Updated Redis {REDIS_KEY}: {data}")
        else:
            print("Sensor read returned None for temp or humidity")
    except Exception as e:
        print(f"Error reading/writing DHT22: {e}")
    time.sleep(UPDATE_INTERVAL)