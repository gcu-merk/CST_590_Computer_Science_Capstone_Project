#!/usr/bin/env python3
"""
Docker Swagger Deployment Preparation Script
Ensures Swagger implementation is ready for Docker container deployment
"""

import os
import sys
import shutil
from pathlib import Path

def ensure_swagger_files():
    """Ensure all Swagger files are in place for Docker deployment"""
    edge_api_dir = Path("edge_api")
    
    required_files = [
        "swagger_config.py",
        "api_models.py", 
        "swagger_api_gateway.py",
        "swagger_ui_config.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not (edge_api_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All Swagger files present for Docker deployment")
    return True

def validate_main_app():
    """Validate that radar_service.py is present (main_edge_app.py deprecated)"""
    radar_service_file = Path("radar_service.py")
    
    if not radar_service_file.exists():
        print("❌ radar_service.py not found")
        return False
    
    print("✅ radar_service.py found (main_edge_app.py has been deprecated)")
    print("ℹ️  Current production system uses radar_service.py directly")
    return True

def check_requirements():
    """Check that requirements.txt includes Swagger dependencies"""
    req_file = Path("edge_api/requirements.txt")
    
    if not req_file.exists():
        print("❌ edge_api/requirements.txt not found")
        return False
    
    content = req_file.read_text()
    
    required_packages = ["flask-restx", "flask-socketio", "apispec"]
    missing_packages = []
    
    for package in required_packages:
        if package not in content:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Missing packages in requirements.txt: {missing_packages}")
        return False
    
    print("✅ requirements.txt includes Swagger dependencies")
    return True

def show_deployment_info():
    """Show deployment information"""
    print("\n" + "="*60)
    print("🐳 DOCKER DEPLOYMENT INFORMATION")
    print("="*60)
    print()
    print("📦 Swagger API is configured for Docker deployment:")
    print()
    print("🔧 Build & Deploy:")
    print("   docker-compose build")
    print("   docker-compose up -d")
    print()
    print("🌐 Access Points:")
    print("   • API Endpoints: http://localhost:5000/api/")
    print("   • Swagger UI: http://localhost:5000/docs/")
    print("   • Health Check: http://localhost:5000/api/health")
    print()
    print("🔍 Verification:")
    print("   docker-compose ps")
    print("   docker-compose logs traffic-monitor")
    print("   curl http://localhost:5000/docs/")
    print()
    print("📋 Features in Docker:")
    print("   ✅ Interactive Swagger UI documentation")
    print("   ✅ API endpoint validation")
    print("   ✅ Real-time testing capabilities") 
    print("   ✅ Professional styling and branding")
    print("   ✅ Backward compatibility with existing endpoints")
    print()
    print("🚀 The Swagger API will automatically start inside the")
    print("   traffic-monitor Docker container on port 5000")

def main():
    """Main deployment preparation function"""
    print("🐳 Preparing Swagger API for Docker Deployment")
    print("="*50)
    
    success_count = 0
    total_checks = 3
    
    # Check 1: Swagger files
    print("\n📁 Checking Swagger files...")
    if ensure_swagger_files():
        success_count += 1
    
    # Check 2: Main app integration
    print("\n🔧 Checking main application integration...")
    if validate_main_app():
        success_count += 1
    
    # Check 3: Requirements
    print("\n📦 Checking requirements...")
    if check_requirements():
        success_count += 1
    
    # Show results
    print(f"\n✅ Deployment Check: {success_count}/{total_checks} passed")
    
    if success_count == total_checks:
        print("\n🎉 Swagger API is ready for Docker deployment!")
        show_deployment_info()
        return True
    else:
        print(f"\n⚠️  {total_checks - success_count} issues found. Please resolve before deployment.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Deployment preparation failed: {e}")
        sys.exit(1)