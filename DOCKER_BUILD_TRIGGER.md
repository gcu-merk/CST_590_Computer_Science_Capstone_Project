Trigger Docker image rebuild - contains fixed redis_models.py

The current Docker image (gcumerk/cst590-capstone-public:latest) contains 
an old version with corrupted redis_models.py file.

This file triggers the docker-build-push.yml workflow to create a new 
image with the latest source code that includes:
- Fixed UTF-8 encoding in redis_models.py 
- Proper RedisDataManager class definition
- All recent bug fixes and improvements

Build timestamp: 2025-09-23 17:05:00 UTC
Source commit: 66d9373 (network cleanup fixes)

Rebuild trigger note:
- 2025-09-30: Include fix for Edge API enhanced gateway import in /api/analytics/speeds
	- Change: import get_speed_service via package path (edge_api.services) to avoid
		"attempted relative import with no known parent package" at runtime.
	- Commit: f9c92bb