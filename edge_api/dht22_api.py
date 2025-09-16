from flask import Flask, jsonify
import redis
import os

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

@app.route('/api/weather/dht22', methods=['GET'])
def get_dht22_weather():
    data = r.hgetall(REDIS_KEY)
    if not data:
        return jsonify({"error": "No DHT22 data found"}), 404
    # Decode bytes to strings
    result = {k.decode(): float(v) for k, v in data.items()}
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
