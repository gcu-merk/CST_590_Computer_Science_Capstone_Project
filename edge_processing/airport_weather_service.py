#!/usr/bin/env python3
"""
Airport Weather Service
Periodically fetches weather.gov API and updates Redis with latest observation
"""
import os
import time
import json
import requests
import redis
from datetime import datetime, timezone

# Configurable interval (minutes)
FETCH_INTERVAL_MINUTES = int(os.getenv('FETCH_INTERVAL_MINUTES', 5))

# Redis config
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_KEY = 'weather:latest'

# Weather.gov API
WEATHER_API_URL = 'https://api.weather.gov/stations/KOKC/observations/latest'


def fetch_weather_api():
    try:
        resp = requests.get(WEATHER_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        props = data.get('properties', {})
        parsed = {
            'timestamp': props.get('timestamp'),
            'textDescription': props.get('textDescription'),
            'temperature': props.get('temperature', {}).get('value'),
            'windDirection': props.get('windDirection', {}).get('value'),
            'windSpeed': props.get('windSpeed', {}).get('value'),
            'visibility': props.get('visibility', {}).get('value'),
            'precipitationLast3Hours': props.get('precipitationLast3Hours', {}).get('value'),
            'relativeHumidity': props.get('relativeHumidity', {}).get('value'),
            'cloudLayers': props.get('cloudLayers', []),
            'stationId': props.get('stationId'),
            'stationName': props.get('stationName'),
        }
        return parsed
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()}


def store_in_redis(payload):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.set(REDIS_KEY, json.dumps(payload))


def main():
    print(f"Starting Airport Weather Service. Fetch interval: {FETCH_INTERVAL_MINUTES} min")
    while True:
        weather_json = fetch_weather_api()
        store_in_redis(weather_json)
        print(f"[{datetime.now(timezone.utc).isoformat()}] Updated Redis with latest weather.gov observation.")
        time.sleep(FETCH_INTERVAL_MINUTES * 60)

if __name__ == '__main__':
    main()
