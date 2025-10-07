# Radar Service Changelog

## Version 2.1.1 (September 26, 2025)

### Fixed
- **Logging Issue Resolution**: Fixed spurious "Error in radar monitoring loop" messages
  - Added proper exception handling around Redis publishing in vehicle detection
  - Prevents Redis connection errors from bubbling up to monitoring loop
  - Vehicle detections continue to be logged successfully even if Redis publishing fails
  - Improved error isolation and system resilience

### Technical Details
- Modified `_process_radar_data_enhanced()` method in `radar_service.py`
- Added try-catch block around `_publish_to_redis_enhanced()` call
- Enhanced error logging with specific `redis_publish_error` type
- Maintains detection functionality while gracefully handling Redis issues

### Impact
- ✅ Vehicle detections work properly (unchanged)
- ✅ Clean, informative logging without false error messages
- ✅ Better system resilience to Redis connectivity issues
- ✅ Improved debugging capabilities with specific error types

## Version 2.1.0 (Previous)
- Enhanced production radar service with correlation tracking and performance monitoring