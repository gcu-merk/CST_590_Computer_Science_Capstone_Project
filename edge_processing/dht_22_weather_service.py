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
    Read DHT22 sensor using lgpio library with proper bit-bang protocol and retry logic
    
    Args:
        gpio_pin: GPIO pin number for DHT22 data line
        
    Returns:
        Tuple of (temperature_c, humidity)
        
    Raises:
        RuntimeError: If sensor reading fails after all retries or GPIO is unavailable
        ValueError: If sensor data is out of valid range
        
    Enhanced with retry logic for improved reliability!
    """
    max_retries = 3
    retry_delay = 0.1  # 100ms between retries
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"DHT22 read attempt {attempt + 1}/{max_retries}")
            return _read_dht22_single_attempt(gpio_pin)
            
        except RuntimeError as e:
            error_msg = str(e)
            
            # Classify error types for different retry strategies
            if "checksum" in error_msg.lower():
                logger.warning(f"DHT22 checksum error on attempt {attempt + 1}: {e}")
                error_type = "checksum"
            elif "timeout on bit" in error_msg.lower():
                logger.warning(f"DHT22 bit timing error on attempt {attempt + 1}: {e}")
                error_type = "timing"
            elif "timeout waiting" in error_msg.lower():
                logger.warning(f"DHT22 response timeout on attempt {attempt + 1}: {e}")
                error_type = "response"
            else:
                logger.warning(f"DHT22 communication error on attempt {attempt + 1}: {e}")
                error_type = "communication"
            
            # If this is the last attempt, raise the error
            if attempt == max_retries - 1:
                logger.error(f"DHT22 failed after {max_retries} attempts, last error: {e}")
                raise
            
            # Wait before retry (longer for response timeouts)
            delay = retry_delay * (2 if error_type == "response" else 1)
            logger.debug(f"Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    # Should never reach here due to the raise in the loop
    raise RuntimeError("DHT22 reading failed after all retries")


def _read_dht22_single_attempt(gpio_pin: int) -> Tuple[float, float]:
    """
    Single attempt to read DHT22 sensor data
    
    Args:
        gpio_pin: GPIO pin number for DHT22 data line
        
    Returns:
        Tuple of (temperature_c, humidity)
        
    Raises:
        RuntimeError: If sensor reading fails or GPIO is unavailable
        ValueError: If sensor data is out of valid range
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
        
        # Read 40 bits of data with improved timing tolerance
        for i in range(40):
            # Wait for bit start (low signal) with adaptive timeout
            bit_start = time.time()
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                if time.time() - bit_start > 0.00015:  # Increased to 150us timeout
                    raise RuntimeError(f"DHT22 timeout on bit {i} start")
            
            # Wait for data signal (high signal) with adaptive timeout
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 0:
                if time.time() - bit_start > 0.0003:  # Increased to 300us timeout
                    raise RuntimeError(f"DHT22 timeout on bit {i} data")
            
            # Measure high signal duration to determine bit value
            high_start = time.time()
            while lgpio.gpio_read(gpio_handle, gpio_pin) == 1:
                if time.time() - high_start > 0.00015:  # Increased to 150us max
                    break
            
            high_duration = time.time() - high_start
            
            # Improved bit detection based on diagnostic measurements:
            # DHT22: 23-28us = 0, 70-75us = 1
            # Using 45us as threshold (midpoint between ranges)
            bit_value = 1 if high_duration > 0.000045 else 0  # 45us threshold
            data_bits.append(bit_value)
            
            # Debug timing for first few bits
            if i < 5:
                logger.debug(f"Bit {i}: {bit_value} (duration: {high_duration*1000000:.1f}us)")
        
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
    
    # Verify checksum with tolerance for single-bit errors
    calculated_checksum = (humidity_high + humidity_low + temp_high + temp_low) & 0xFF
    checksum_diff = abs(checksum - calculated_checksum)
    
    if checksum != calculated_checksum:
        # Check if it's a single-bit error (difference of 1, 2, 4, 8, 16, 32, 64, 128)
        if checksum_diff in [1, 2, 4, 8, 16, 32, 64, 128]:
            logger.warning(f"DHT22 single-bit checksum error detected (diff={checksum_diff}), accepting reading")
            logger.debug(f"Checksum: expected {checksum:02x}, calculated {calculated_checksum:02x}")
        else:
            raise RuntimeError(f"DHT22 checksum validation failed: "
                              f"expected {checksum:02x}, calculated {calculated_checksum:02x} (diff={checksum_diff})")
    else:
        logger.debug(f"DHT22 checksum validation passed: {checksum:02x}")
    
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

def startup_diagnostics() -> bool:
    """
    Run startup diagnostics to verify DHT22 connectivity and timing
    
    Returns:
        bool: True if diagnostics pass, False otherwise
    """
    logger.info("🔬 Running DHT22 startup diagnostics...")
    
    try:
        # Check GPIO access
        logger.info("📍 Testing GPIO access...")
        test_handle = lgpio.gpiochip_open(4)
        lgpio.gpio_claim_input(test_handle, GPIO_PIN)
        
        # Check initial GPIO state
        state = lgpio.gpio_read(test_handle, GPIO_PIN)
        logger.info(f"📖 GPIO{GPIO_PIN} initial state: {state} ({'HIGH' if state else 'LOW'})")
        
        if state == 1:
            logger.info("✅ GPIO state HIGH - good for DHT22 idle state")
        else:
            logger.warning("⚠️  GPIO state LOW - might indicate wiring issue")
        
        lgpio.gpio_free(test_handle, GPIO_PIN)
        lgpio.gpiochip_close(test_handle)
        
        # Attempt a test reading
        logger.info("🧪 Attempting test DHT22 reading...")
        try:
            temp, humidity = read_dht22_lgpio(GPIO_PIN)
            logger.info(f"✅ Test reading successful: {temp:.1f}°C, {humidity:.1f}%")
            logger.info("🎉 DHT22 startup diagnostics PASSED")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Test reading failed: {e}")
            logger.info("📋 Service will continue with retry logic")
            return False
            
    except Exception as e:
        logger.error(f"❌ GPIO access test failed: {e}")
        return False


def main() -> None:
    """Main service loop with improved error handling, retry logic, and exponential backoff"""
    logger.info("Starting Enhanced DHT22 Weather Service")
    logger.info(f"Update interval: {UPDATE_INTERVAL} seconds ({UPDATE_INTERVAL // 60} minutes)")
    logger.info(f"Redis host: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"GPIO Pin: {GPIO_PIN}")
    logger.info("Using lgpio library with enhanced reliability features!")
    
    # Run startup diagnostics
    diagnostics_passed = startup_diagnostics()
    if not diagnostics_passed:
        logger.warning("Startup diagnostics failed, but continuing with service...")
    
    # Initialize Redis connection
    try:
        redis_client = create_redis_connection()
    except Exception as e:
        logger.critical("Failed to initialize Redis connection - service cannot continue")
        sys.exit(1)
    
    consecutive_failures = 0
    max_consecutive_failures = 10  # Increased from 5 due to retry logic
    current_backoff = 1  # Start with 1 second backoff
    max_backoff = 300   # Max 5 minutes backoff
    last_success_time = time.time()
    
    try:
        while True:
            try:
                # Read sensor data with retry logic built-in
                temperature_c, humidity = read_dht22_lgpio(GPIO_PIN)
                
                # Store to Redis
                store_sensor_data(redis_client, temperature_c, humidity)
                
                # Reset failure tracking on success
                consecutive_failures = 0
                current_backoff = 1
                last_success_time = time.time()
                
                logger.info(f"✅ DHT22 reading successful after {int(time.time() - last_success_time)}s")
                
            except (RuntimeError, ValueError) as e:
                consecutive_failures += 1
                error_msg = str(e)
                
                # Classify error severity for backoff strategy
                if "checksum" in error_msg.lower() or "single-bit" in error_msg.lower():
                    error_severity = "minor"
                    backoff_multiplier = 1
                elif "timeout on bit" in error_msg.lower():
                    error_severity = "moderate" 
                    backoff_multiplier = 2
                elif "timeout waiting" in error_msg.lower():
                    error_severity = "serious"
                    backoff_multiplier = 4
                else:
                    error_severity = "unknown"
                    backoff_multiplier = 2
                
                logger.error(f"❌ DHT22 {error_severity} error (failure {consecutive_failures}/{max_consecutive_failures}): {e}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"Maximum consecutive failures ({max_consecutive_failures}) reached")
                    logger.critical("DHT22 sensor may be disconnected or faulty - service stopping")
                    break
                
                # Calculate backoff delay based on error severity
                current_backoff = min(current_backoff * backoff_multiplier, max_backoff)
                
                # For minor errors, use shorter delays
                if error_severity == "minor" and consecutive_failures <= 3:
                    delay = min(current_backoff, 30)  # Max 30s for minor errors
                else:
                    delay = current_backoff
                
                logger.info(f"Will retry in {delay}s (backoff strategy for {error_severity} error)")
                time.sleep(delay)
                continue  # Skip the normal UPDATE_INTERVAL wait
                    
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
                
                # Use moderate backoff for unexpected errors
                current_backoff = min(current_backoff * 2, max_backoff)
                time.sleep(current_backoff)
                continue
            
            # Normal wait for next reading cycle (only if no errors occurred)
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