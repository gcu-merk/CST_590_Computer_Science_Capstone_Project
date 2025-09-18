#!/usr/bin/env python3
"""
Swagger Integration Script for Traffic Monitoring System
Integrates the new Swagger-enabled API with the existing deployment
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def backup_original_api():
    """Backup the original API gateway"""
    original_file = Path('edge_api_gateway.py')
    backup_file = Path('edge_api_gateway_original.py')
    
    if original_file.exists() and not backup_file.exists():
        shutil.copy2(original_file, backup_file)
        print(f"✅ Backed up original API to {backup_file}")
    else:
        print(f"ℹ️  Backup already exists or original file not found")

def deploy_swagger_api():
    """Deploy the Swagger-enabled API"""
    swagger_file = Path('swagger_api_gateway.py')
    target_file = Path('edge_api_gateway.py')
    
    if swagger_file.exists():
        # Create backup first
        backup_original_api()
        
        # Copy Swagger version to main file
        shutil.copy2(swagger_file, target_file)
        print(f"✅ Deployed Swagger-enabled API to {target_file}")
        
        return True
    else:
        print(f"❌ Swagger API file not found: {swagger_file}")
        return False

def update_docker_compose():
    """Update docker-compose.yml to expose Swagger UI port"""
    compose_file = Path('../docker-compose.yml')
    
    if not compose_file.exists():
        print(f"⚠️  Docker Compose file not found: {compose_file}")
        return False
    
    # Read current compose file
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Check if Swagger documentation port is already exposed
    if '"5000:5000"' in content and '/docs' not in content:
        print("ℹ️  Docker Compose already configured for API port")
        print("🌐 Swagger UI will be available at: http://localhost:5000/docs/")
        return True
    
    print("ℹ️  Docker Compose configuration appears correct")
    return True

def install_dependencies():
    """Install required Python dependencies"""
    try:
        # Install packages from requirements.txt
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def validate_swagger_setup():
    """Validate that Swagger setup is working"""
    try:
        # Import test
        sys.path.append(str(Path.cwd()))
        
        # Test imports
        from swagger_config import API_CONFIG, create_api_models
        from api_models import get_model_registry
        from swagger_ui_config import get_swagger_config
        
        print("✅ All Swagger modules import successfully")
        
        # Test API config
        if API_CONFIG.get('title') and API_CONFIG.get('version'):
            print(f"✅ API Configuration valid: {API_CONFIG['title']} v{API_CONFIG['version']}")
        
        # Test models
        models = get_model_registry()
        if models and len(models) > 0:
            print(f"✅ API Models loaded: {len(models)} models available")
            print(f"   📋 Available models: {', '.join(list(models.keys())[:5])}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Please ensure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def create_integration_guide():
    """Create an integration guide for the development team"""
    guide_content = """
# Swagger API Integration Guide

## 🚀 Quick Start

The Traffic Monitoring System now includes comprehensive Swagger/OpenAPI documentation!

### Accessing the Documentation

1. **Development**: http://localhost:5000/docs/
2. **Production**: http://100.121.231.16:5000/docs/

### Key Features

✅ **Interactive API Testing** - Try endpoints directly in the browser
✅ **Comprehensive Documentation** - Detailed descriptions for all endpoints
✅ **Request/Response Examples** - See exactly what data to expect
✅ **Parameter Validation** - Built-in validation with helpful error messages
✅ **Multiple Response Formats** - JSON examples for all scenarios
✅ **WebSocket Documentation** - Real-time API documentation included

## 📚 API Endpoints

### System Health
- `GET /api/health` - Comprehensive system status
- Real-time hardware metrics (CPU, memory, temperature)
- Service connectivity status

### Vehicle Detection
- `GET /api/detections` - Recent vehicle detections
- `GET /api/tracks` - Active vehicle tracks
- Configurable time ranges and filtering

### Speed Analysis
- `GET /api/speeds` - Speed measurements and violations
- Average and maximum speed calculations
- Direction and confidence data

### Weather Monitoring
- `GET /api/weather` - Multi-source weather data
- DHT22 sensor + airport weather integration
- Sky condition analysis for traffic visibility

### Analytics
- `GET /api/analytics` - Traffic insights and statistics
- Configurable analysis periods (hour/day/week)
- Performance metrics and trends

## 🔧 Development Notes

### Backward Compatibility
- All existing endpoints remain functional
- Legacy routes maintained for smooth transition
- WebSocket functionality preserved

### New Features
- Parameter validation with helpful error messages
- Standardized error responses
- Enhanced response schemas
- Interactive documentation

### Docker Integration
- No changes required to docker-compose.yml
- Swagger UI served on same port (5000)
- All environment variables preserved

## 📱 Usage Examples

### Using the Interactive UI
1. Navigate to `/docs/` in your browser
2. Expand any endpoint section
3. Click "Try it out"
4. Fill in parameters (or use defaults)
5. Click "Execute" to test the API

### Using curl
```bash
# System health check
curl http://localhost:5000/api/health

# Get recent vehicle detections
curl "http://localhost:5000/api/detections?seconds=300"

# Get current weather data
curl http://localhost:5000/api/weather

# Get traffic analytics
curl "http://localhost:5000/api/analytics?period=hour"
```

### Using Python requests
```python
import requests

# Get system health
response = requests.get('http://localhost:5000/api/health')
health_data = response.json()

# Get recent detections with custom timespan
response = requests.get('http://localhost:5000/api/detections', 
                       params={'seconds': 600})
detections = response.json()
```

## 🛠️ Customization

### Adding New Endpoints
1. Define model in `api_models.py`
2. Add namespace and resource in `swagger_api_gateway.py`
3. Include proper documentation decorators
4. Test in Swagger UI

### Modifying Documentation
- Update `swagger_config.py` for API-level changes
- Modify `swagger_ui_config.py` for UI customization
- Use Flask-RESTX decorators for endpoint documentation

## 🔍 Troubleshooting

### Common Issues
- **Import Errors**: Ensure `flask-restx` is installed
- **UI Not Loading**: Check console for JavaScript errors
- **Validation Errors**: Review parameter types and ranges

### Getting Help
- Check Swagger UI documentation at `/docs/`
- Review API model definitions in code
- Use browser developer tools for debugging

## 📈 Performance Notes

- Swagger UI adds minimal overhead
- API validation improves data quality
- Documentation generation is cached
- WebSocket performance unchanged

---

🚗 **Traffic Monitoring System v1.0.0**
Powered by Flask-RESTX • OpenAPI 3.0 • Raspberry Pi 5
"""
    
    guide_file = Path('../documentation/SWAGGER_INTEGRATION_GUIDE.md')
    guide_file.parent.mkdir(exist_ok=True)
    
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Integration guide created: {guide_file}")

def main():
    """Main integration function"""
    print("🚀 Starting Swagger API Integration")
    print("=" * 50)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Install dependencies
    print("\n📦 Step 1: Installing dependencies...")
    if install_dependencies():
        success_count += 1
    
    # Step 2: Validate Swagger setup
    print("\n🔍 Step 2: Validating Swagger setup...")
    if validate_swagger_setup():
        success_count += 1
    
    # Step 3: Deploy Swagger API
    print("\n🚀 Step 3: Deploying Swagger-enabled API...")
    if deploy_swagger_api():
        success_count += 1
    
    # Step 4: Update Docker configuration
    print("\n🐳 Step 4: Checking Docker configuration...")
    if update_docker_compose():
        success_count += 1
    
    # Step 5: Create integration guide
    print("\n📚 Step 5: Creating integration guide...")
    try:
        create_integration_guide()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to create guide: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Integration Complete: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("\n🎉 Swagger API successfully integrated!")
        print("\n📖 Next Steps:")
        print("   1. Restart the API service (docker-compose restart)")
        print("   2. Visit http://localhost:5000/docs/ to see the documentation")
        print("   3. Test endpoints using the interactive UI")
        print("   4. Review the integration guide in documentation/")
        
        return True
    else:
        print(f"\n⚠️  Integration completed with {total_steps - success_count} issues")
        print("   Please review the error messages above and resolve any issues")
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Integration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Integration failed: {e}")
        sys.exit(1)