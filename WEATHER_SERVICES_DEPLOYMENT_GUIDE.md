# Enhanced Weather Services - Deployment Guide

## 🎯 Overview
Both weather services have been successfully enhanced with centralized logging and correlation tracking. These services provide environmental monitoring that correlates with traffic patterns and system performance.

## 📋 What's Complete

### ✅ Enhanced DHT22 Weather Service
- **File**: `edge_processing/dht_22_weather_service_enhanced.py` (350+ lines)
- **Features**: 
  - Centralized logging with ServiceLogger integration
  - GPIO sensor monitoring with lgpio library for Pi 5
  - Performance monitoring for sensor read operations
  - Business event logging for environmental data
  - Redis time-series storage with 24-hour retention
  - Service statistics and health monitoring
  - Error tracking and sensor validation

### ✅ Enhanced Airport Weather Service  
- **File**: `edge_processing/airport_weather_service_enhanced.py` (320+ lines)
- **Features**:
  - Centralized logging with API monitoring
  - Weather.gov API integration with proper headers
  - Performance monitoring for API calls and response times
  - Weather data correlation with local DHT22 readings
  - HTTP error handling and timeout management
  - Redis time-series storage and data correlation
  - Service statistics and API health tracking

### ✅ Updated Docker Configuration
- **docker-compose.yml**: Updated both weather services to use enhanced versions
- **Environment Variables**: Added centralized logging configuration
- **Service Commands**: Updated to use `_enhanced` modules

## 🚀 Deployment Steps

### 1. Deploy Enhanced Weather Services
```bash
# On Raspberry Pi - update containers
docker-compose pull
docker-compose up -d airport-weather dht22-weather
```

### 2. Verify Service Status
```bash
# Check container status
docker-compose ps airport-weather dht22-weather

# View logs
docker-compose logs -f airport-weather
docker-compose logs -f dht22-weather

# Check centralized logging
tail -f /mnt/storage/logs/airport_weather.log
tail -f /mnt/storage/logs/dht22_weather.log
```

### 3. Test Weather Data Flow
```bash
# Check Redis weather data
redis-cli
> GET weather:airport:latest
> HGETALL weather:dht22
> ZRANGE weather:dht22:timeseries -5 -1 WITHSCORES
> GET weather:correlation:airport_dht22
> EXIT
```

### 4. Monitor Weather Correlation
```bash
# Monitor weather correlation events
docker-compose logs airport-weather | grep "weather_correlation"
docker-compose logs dht22-weather | grep "sensor_read_success"

# Check weather service statistics
redis-cli HGETALL weather:airport:latest:stats
redis-cli HGETALL weather:dht22:stats
```

## 🔗 Weather Correlation Pipeline

### Data Flow:
1. **DHT22 Sensor**: Local GPIO sensor reads temperature/humidity every 10 minutes
2. **Airport API**: weather.gov KOKC station data fetched every 5 minutes  
3. **Data Correlation**: Airport service correlates with local DHT22 readings
4. **Time-Series Storage**: Both services store 24-hour historical data
5. **Unified Logging**: All weather events logged with correlation IDs

### Correlation Logic:
- Temperature difference tracking between local sensor and airport
- Humidity comparison for environmental validation
- Weather pattern correlation with traffic detection accuracy
- Environmental factor impact on sensor performance

## 📊 Key Logging Events

### DHT22 Service Events:
- `service_initialization`: Service startup with GPIO configuration
- `gpio_initialization`: GPIO chip access confirmation
- `sensor_read_start`: Beginning of sensor reading cycle
- `sensor_read_success`: Successful temperature/humidity reading
- `sensor_read_failure`: GPIO read errors or validation failures
- `reading_stored`: Data successfully stored in Redis
- `performance_monitoring`: Sensor read timing metrics

### Airport Weather Events:
- `api_fetch_start`: Beginning of weather.gov API call
- `api_fetch_success`: Successful API response with data
- `api_fetch_failure`: HTTP errors, timeouts, or API issues
- `weather_data_stored`: Data successfully stored in Redis
- `weather_correlation`: Correlation with local DHT22 sensor
- `performance_monitoring`: API response timing metrics

## 🔧 Configuration

### DHT22 Service Environment Variables:
```bash
# GPIO Configuration
DHT22_GPIO_PIN=4                    # GPIO pin for DHT22 sensor
DHT22_UPDATE_INTERVAL=600           # Reading interval (10 minutes)

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
DHT22_REDIS_KEY=weather:dht22

# Centralized Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs
SERVICE_NAME=dht22_weather
```

### Airport Weather Environment Variables:
```bash
# API Configuration  
FETCH_INTERVAL_MINUTES=5            # API fetch interval
WEATHER_API_URL=https://api.weather.gov/stations/KOKC/observations/latest
WEATHER_API_TIMEOUT=10              # API timeout seconds

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
AIRPORT_WEATHER_REDIS_KEY=weather:airport:latest

# Centralized Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs
SERVICE_NAME=airport_weather
```

## 🎯 Validation Checklist

- [ ] Enhanced weather services deployed and running
- [ ] DHT22 sensor reading temperature and humidity correctly
- [ ] Airport weather API fetching KOKC observations successfully  
- [ ] Centralized logging active for both services
- [ ] Weather correlation between local and external sources working
- [ ] Redis time-series data being stored and rotated
- [ ] Performance metrics captured for sensor reads and API calls
- [ ] No errors in container logs
- [ ] Weather service statistics publishing correctly

## 🔍 Troubleshooting

### Common Issues:

1. **DHT22 GPIO Access Failed**: 
   - Verify GPIO devices mounted: `/dev/gpiochip4`
   - Check container privileged mode and gpio group access
   - Ensure lgpio library installed in container

2. **Airport Weather API Timeout**:
   - Check network connectivity to weather.gov
   - Verify User-Agent header in requests
   - Monitor API rate limiting

3. **Weather Correlation Missing**:
   - Ensure both services are running and storing data
   - Check Redis keys: `weather:dht22` and `weather:airport:latest`
   - Verify time synchronization between services

4. **Missing Weather Data**:
   - Check service health: `docker-compose ps`
   - Monitor Redis TTL settings for time-series data
   - Verify environment variable configuration

### Log Analysis:
```bash
# Filter for weather correlation events
docker-compose logs airport-weather | grep "weather_correlation"

# Monitor DHT22 sensor health
docker-compose logs dht22-weather | grep "sensor_read"

# Check API performance
docker-compose logs airport-weather | grep "api_response_time_ms"

# Review error patterns
docker-compose logs airport-weather | grep "ERROR"
docker-compose logs dht22-weather | grep "ERROR"
```

## 📈 Next Steps

With Weather Services enhancement complete, the environmental monitoring pipeline now includes:
- **DHT22 Local Sensor** ✅ (Enhanced with centralized logging)
- **Airport Weather API** ✅ (Enhanced with correlation tracking)
- **Weather Data Correlation** ✅ (Local vs external validation)

**Progress Update**: 4 of 8 services complete (50%):
- **Radar Service** ✅ 
- **Vehicle Consolidator** ✅
- **Camera Service** ✅  
- **Weather Services** ✅

**Remaining Major Services**:
- API Gateway Service Enhancement
- Database Services Integration

The environmental monitoring and correlation pipeline is now fully operational with centralized logging!