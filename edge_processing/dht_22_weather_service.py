import time
import adafruit_dht
import board
import redis
import os

# Configuration
GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 4))  # Default to GPIO4
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
UPDATE_INTERVAL = int(os.getenv("DHT22_UPDATE_INTERVAL", 300))  # Default: 5 minutes
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

dhtDevice = adafruit_dht.DHT22(getattr(board, f"D{GPIO_PIN}"))

def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0

while True:
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        if temperature_c is not None and humidity is not None:
            temperature_f = c_to_f(temperature_c)
            data = {
                "temperature_f": round(temperature_f, 1),
                "humidity": round(humidity, 1)
            }
            r.hmset(REDIS_KEY, data)
            print(f"Updated Redis: {data}")
        else:
            print("Sensor read failed: None values")
    except Exception as e:
        print(f"Error reading DHT22: {e}")
    time.sleep(UPDATE_INTERVAL)
