import time
import redis
import os
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Tuple, Optional

# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import lgpio for modern GPIO access - fail fast if not available
try:
    import lgpio
    logger.info("lgpio library loaded successfully")
except ImportError as e:
    logger.critical(f"lgpio library not available: {e}")
    logger.critical("DHT22 service requires lgpio for GPIO access - exiting")
    sys.exit(1)

# Initialize GPIO handle with proper error handling
gpio_handle = None
try:
    gpio_handle = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4
    logger.info("GPIO chip 4 opened successfully")
except Exception as e:
    logger.critical(f"Failed to open GPIO chip 4: {e}")
    logger.critical("DHT22 service requires GPIO access - exiting")
    sys.exit(1)

# Configuration
GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 4))  # Default to GPIO4
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
UPDATE_INTERVAL = int(os.getenv("DHT22_UPDATE_INTERVAL", 600))  # Default: 10 minutes
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

def read_dht22_lgpio(gpio_pin: int) -> Tuple[float, float]:
    """
    Read DHT22 sensor using lgpio library with proper bit-bang protocol
    
    Args:
        gpio_pin: GPIO pin number for DHT22 data line
        
    Returns:
        Tuple of (temperature_c, humidity)
        
    Raises:
        RuntimeError: If sensor reading fails or GPIO is unavailable
        ValueError: If sensor data is out of valid range
        
    NO FALLBACKS - Real sensor only!
    """
    if gpio_handle is None:
        raise RuntimeError("GPIO handle not available - cannot read DHT22 sensor")
    
    try:
        logger.debug(f"Starting DHT22 read on GPIO pin {gpio_pin}")
        
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
        
        # Read the data bits with proper timeout handling
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
        
        logger.debug(f"Successfully read {len(data_bits)} data bits from DHT22")
        
        # Parse and validate the sensor data
        return _parse_dht22_data(data_bits)
        
    except Exception as e:
        logger.error(f"DHT22 sensor communication failed: {e}")
        raise
    finally:
        # Always cleanup GPIO resources
        try:
            lgpio.gpio_free(gpio_handle, gpio_pin)
        except Exception as cleanup_error:
            logger.warning(f"GPIO cleanup warning: {cleanup_error}")


def _parse_dht22_data(data_bits: list) -> Tuple[float, float]:
    """
    Parse DHT22 raw data bits into temperature and humidity values
    
    Args:
        data_bits: List of 40 bits from DHT22 sensor
        
    Returns:
        Tuple of (temperature_c, humidity)
        
    Raises:
        ValueError: If data is invalid or out of range
        RuntimeError: If checksum validation fails
    """
    if len(data_bits) != 40:
        raise ValueError(f"Expected 40 data bits, got {len(data_bits)}")
    
    # Debug: Print raw data bits for diagnostics
    logger.debug(f"First 10 data bits: {data_bits[:10]}")
    logger.debug(f"Last 10 data bits: {data_bits[-10:]}")
    
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
    logger.debug(f"Raw DHT22 bytes: H_high={humidity_high:02x}({humidity_high}) "
                f"H_low={humidity_low:02x}({humidity_low}) T_high={temp_high:02x}({temp_high}) "
                f"T_low={temp_low:02x}({temp_low}) Checksum={checksum:02x}({checksum})")
    
    # Verify checksum
    calculated_checksum = (humidity_high + humidity_low + temp_high + temp_low) & 0xFF
    if checksum != calculated_checksum:
        raise RuntimeError(f"DHT22 checksum validation failed: "
                          f"expected {checksum:02x}, calculated {calculated_checksum:02x}")
    
    # Calculate actual values according to DHT22 datasheet
    humidity = ((humidity_high << 8) | humidity_low) / 10.0
    temperature_raw = ((temp_high & 0x7F) << 8) | temp_low
    temperature = temperature_raw / 10.0
    
    # Handle negative temperature (MSB of temp_high indicates sign)
    if temp_high & 0x80:
        temperature = -temperature
    
    logger.debug(f"Parsed values: temp={temperature}°C, humidity={humidity}%")
    
    # Apply temperature correction for suspected Fahrenheit readings
    temperature = _validate_and_correct_temperature(temperature)
    
    # Validate sensor ranges
    _validate_sensor_ranges(temperature, humidity)
    
    logger.info(f"DHT22 reading successful: {temperature:.1f}°C, {humidity:.1f}%")
    return temperature, humidity


def _validate_and_correct_temperature(temperature: float) -> float:
    """
    Validate temperature reading and apply corrections if needed
    
    Args:
        temperature: Raw temperature reading in Celsius
        
    Returns:
        Corrected temperature in Celsius
    """
    original_temp = temperature
    
    # Temperature sanity check and potential correction
    if temperature > 50.0:  # Unrealistic indoor temperature in Celsius
        if 32.0 <= temperature <= 120.0:  # Reasonable Fahrenheit range
            # Convert from Fahrenheit to Celsius
            temperature = (temperature - 32.0) * 5.0 / 9.0
            logger.warning(f"Temperature anomaly detected: {original_temp}°C appears to be Fahrenheit")
            logger.info(f"Auto-correcting: {original_temp}°F → {temperature:.1f}°C")
        else:
            logger.warning(f"Extreme temperature reading detected: {temperature}°C")
    
    return temperature


def _validate_sensor_ranges(temperature: float, humidity: float) -> None:
    """
    Validate that sensor readings are within acceptable ranges
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity percentage
        
    Raises:
        ValueError: If readings are outside valid sensor ranges
    """
    if humidity < 0 or humidity > 100:
        raise ValueError(f"DHT22 humidity out of valid range (0-100%): {humidity}%")
    
    if temperature < -40 or temperature > 80:
        raise ValueError(f"DHT22 temperature out of valid range (-40 to 80°C): {temperature}°C")

# Connect to Redis with proper error handling
def create_redis_connection() -> redis.Redis:
    """Create Redis connection with validation"""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, 
                       socket_timeout=5, socket_connect_timeout=5)
        # Test the connection
        r.ping()
        logger.info(f"Redis connection established: {REDIS_HOST}:{REDIS_PORT}")
        return r
    except redis.ConnectionError as e:
        logger.critical(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected Redis connection error: {e}")
        raise


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit"""
    return celsius * 9.0 / 5.0 + 32.0


def store_sensor_data(redis_client: redis.Redis, temperature_c: float, humidity: float) -> None:
    """
    Store sensor data to Redis with proper error handling
    
    Args:
        redis_client: Redis client instance
        temperature_c: Temperature in Celsius
        humidity: Relative humidity percentage
        
    Raises:
        redis.RedisError: If Redis operation fails
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        temperature_f = celsius_to_fahrenheit(temperature_c)
        
        data = {
            "temperature_c": round(temperature_c, 2),
            "temperature_f": round(temperature_f, 1),
            "humidity": round(humidity, 1),
            "timestamp": timestamp,
        }
        
        # Store as hash for structured access
        redis_client.hset(REDIS_KEY, mapping=data)
        # Store as JSON for backward compatibility
        redis_client.set(f"{REDIS_KEY}:latest", json.dumps(data))
        
        logger.info(f"✅ DHT22 data stored to Redis {REDIS_KEY}: "
                   f"temp={data['temperature_c']}°C ({data['temperature_f']}°F), "
                   f"humidity={data['humidity']}%")
        
    except redis.RedisError as e:
        logger.error(f"Failed to store data to Redis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error storing sensor data: {e}")
        raise

def main() -> None:
    """Main service loop with proper error handling and graceful shutdown"""
    logger.info("Starting DHT22 Weather Service")
    logger.info(f"Update interval: {UPDATE_INTERVAL} seconds ({UPDATE_INTERVAL // 60} minutes)")
    logger.info(f"Redis host: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"GPIO Pin: {GPIO_PIN}")
    logger.info("Using lgpio library - NO FALLBACKS, real sensor only!")
    
    # Initialize Redis connection
    try:
        redis_client = create_redis_connection()
    except Exception as e:
        logger.critical("Failed to initialize Redis connection - service cannot continue")
        sys.exit(1)
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    try:
        while True:
            try:
                # Read sensor data - this will raise exceptions on failure
                temperature_c, humidity = read_dht22_lgpio(GPIO_PIN)
                
                # Store to Redis - this will raise exceptions on failure
                store_sensor_data(redis_client, temperature_c, humidity)
                
                # Reset failure counter on success
                consecutive_failures = 0
                
            except (RuntimeError, ValueError) as e:
                consecutive_failures += 1
                logger.error(f"❌ DHT22 sensor error (failure {consecutive_failures}/{max_consecutive_failures}): {e}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"Maximum consecutive failures ({max_consecutive_failures}) reached")
                    logger.critical("DHT22 sensor may be disconnected or faulty - service stopping")
                    break
                    
            except redis.RedisError as e:
                logger.error(f"❌ Redis storage error: {e}")
                logger.warning("Sensor data lost - will retry next cycle")
                
            except KeyboardInterrupt:
                logger.info("Service shutdown requested by user")
                break
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"❌ Unexpected error (failure {consecutive_failures}/{max_consecutive_failures}): {e}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical("Too many unexpected errors - service stopping")
                    break
            
            # Wait for next reading cycle
            logger.debug(f"Waiting {UPDATE_INTERVAL} seconds until next reading...")
            time.sleep(UPDATE_INTERVAL)
            
    except Exception as e:
        logger.critical(f"Fatal error in main service loop: {e}")
        sys.exit(1)
    finally:
        cleanup_resources()


def cleanup_resources() -> None:
    """Clean up GPIO and other resources"""
    logger.info("Cleaning up resources...")
    
    if gpio_handle is not None:
        try:
            lgpio.gpiochip_close(gpio_handle)
            logger.info("GPIO resources cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error during GPIO cleanup: {e}")
    
    logger.info("DHT22 service shutdown complete")


if __name__ == "__main__":
    main()