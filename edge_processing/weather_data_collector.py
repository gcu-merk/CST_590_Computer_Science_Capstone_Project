#!/usr/bin/env python3
"""
Weather Data Collector Service
Reads DHT22 sensor, fetches weather.gov API, and stores results in Redis
"""

import os
import json
import requests
import Adafruit_DHT
import redis
from datetime import datetime, timezone

# DHT22 config
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # GPIO4

# Redis config
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_KEY = 'weather:latest'

# Weather.gov API
WEATHER_API_URL = 'https://api.weather.gov/stations/KOKC/observations/latest'


def read_dht22():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        return {
            'temperature_c': round(temperature, 1),
            'humidity': round(humidity, 1)
        }
    return None


def fetch_weather_api():
    try:
        resp = requests.get(WEATHER_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        props = data.get('properties', {})
        return {
            'api_temperature_c': props.get('temperature', {}).get('value'),
            'api_humidity': props.get('relativeHumidity', {}).get('value'),
            'api_wind_speed': props.get('windSpeed', {}).get('value'),
            'api_text': props.get('textDescription'),
            'api_timestamp': props.get('timestamp')
        }
    except Exception as e:
        return {'error': str(e)}


def store_in_redis(payload):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.set(REDIS_KEY, json.dumps(payload))


def main():
    dht_data = read_dht22()
    api_data = fetch_weather_api()
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dht22': dht_data,
        'weather_api': api_data
    }
    store_in_redis(result)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
