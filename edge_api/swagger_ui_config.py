#!/usr/bin/env python3
"""
Custom Swagger UI Configuration and Templates
Provides enhanced styling and configuration for the Swagger documentation interface
"""

# Custom Swagger UI HTML template with enhanced styling
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{title}} - API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="{{url_for('static', filename='favicon.png')}}" sizes="32x32" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        
        /* Custom header styling */
        .swagger-ui .topbar {
            background-color: #1f2937;
            border-bottom: 3px solid #3b82f6;
        }
        
        .swagger-ui .topbar .download-url-wrapper {
            display: none;
        }
        
        /* Custom branding */
        .swagger-ui .topbar .topbar-wrapper .link {
            content: "Traffic Monitoring API";
            font-size: 1.5em;
            font-weight: bold;
            color: #ffffff;
        }
        
        /* Enhanced info section */
        .swagger-ui .info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        .swagger-ui .info .title {
            color: white;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .swagger-ui .info .description {
            font-size: 1.1rem;
            line-height: 1.6;
        }
        
        /* Tag sections styling */
        .swagger-ui .opblock-tag {
            background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%);
            border-left: 4px solid #3b82f6;
            border-radius: 6px;
            margin-bottom: 1rem;
        }
        
        /* Method colors */
        .swagger-ui .opblock.opblock-get {
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.1);
        }
        
        .swagger-ui .opblock.opblock-post {
            border-color: #f59e0b;
            background: rgba(245, 158, 11, 0.1);
        }
        
        .swagger-ui .opblock.opblock-put {
            border-color: #8b5cf6;
            background: rgba(139, 92, 246, 0.1);
        }
        
        .swagger-ui .opblock.opblock-delete {
            border-color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
        }
        
        /* Response styling */
        .swagger-ui .responses-inner {
            background: #f8fafc;
            border-radius: 6px;
            padding: 1rem;
        }
        
        /* Custom footer */
        .api-footer {
            background: #1f2937;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
        }
        
        .api-footer h3 {
            margin-bottom: 1rem;
            color: #3b82f6;
        }
        
        .api-footer .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1rem;
        }
        
        .api-footer .footer-links a {
            color: #9ca3af;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .api-footer .footer-links a:hover {
            color: #3b82f6;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-error { background-color: #ef4444; }
        
        /* Custom badges */
        .api-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 0.375rem;
            margin-left: 0.5rem;
        }
        
        .api-badge.realtime {
            background-color: #dbeafe;
            color: #1e40af;
        }
        
        .api-badge.hardware {
            background-color: #f3e8ff;
            color: #7c3aed;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .swagger-ui .info .title {
                font-size: 2rem;
            }
            
            .api-footer .footer-links {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    
    <!-- Custom footer -->
    <div class="api-footer">
        <h3>🚗 Traffic Monitoring System</h3>
        <p>Real-time traffic analysis with vehicle detection, speed monitoring, and weather integration</p>
        <div class="footer-links">
            <a href="/api/health">System Health</a>
            <a href="/api/endpoints">API Directory</a>
            <a href="https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project">GitHub Repository</a>
        </div>
        <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
            Powered by Raspberry Pi 5 • Flask-RESTX • OpenAPI 3.0
        </p>
    </div>
    
    <script src="{{swagger_js_url}}"></script>
    <script src="{{swagger_css_url}}"></script>
    <script>
        window.onload = function() {
            // Custom Swagger UI configuration
            const ui = SwaggerUIBundle({
                url: "{{swagger_json_url}}",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                onComplete: function() {
                    // Add custom enhancements after UI loads
                    addCustomEnhancements();
                }
            });
            
            // Custom enhancement functions
            function addCustomEnhancements() {
                // Add status indicators to operation summaries
                setTimeout(() => {
                    const operations = document.querySelectorAll('.opblock-summary-description');
                    operations.forEach(op => {
                        if (op.textContent.includes('health')) {
                            op.insertAdjacentHTML('beforebegin', '<span class="status-indicator status-healthy"></span>');
                        } else if (op.textContent.includes('real-time') || op.textContent.includes('WebSocket')) {
                            op.insertAdjacentHTML('afterend', '<span class="api-badge realtime">Real-time</span>');
                        } else if (op.textContent.includes('GPIO') || op.textContent.includes('sensor') || op.textContent.includes('camera')) {
                            op.insertAdjacentHTML('afterend', '<span class="api-badge hardware">Hardware</span>');
                        }
                    });
                }, 1000);
            }
            
            window.ui = ui;
        };
    </script>
</body>
</html>
"""

# Custom Swagger configuration for Flask-RESTX
SWAGGER_CONFIG = {
    'title': 'Traffic Monitoring Edge API',
    'uiversion': 3,
    'doc_dir': './docs/',
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/api/swagger.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/docs/static',
    'swagger_ui': True,
    'specs_route': '/docs/',
    'openapi': '3.0.2'
}

# Custom Swagger UI settings
SWAGGER_UI_CONFIG = {
    'deepLinking': True,
    'displayRequestDuration': True,
    'defaultModelsExpandDepth': 2,
    'defaultModelExpandDepth': 2,
    'displayOperationId': False,
    'docExpansion': 'list',
    'filter': True,
    'showExtensions': True,
    'showCommonExtensions': True,
    'tryItOutEnabled': True,
    'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
    'validatorUrl': None
}

# OpenAPI specification enhancements
OPENAPI_ENHANCEMENTS = {
    'info': {
        'termsOfService': 'https://example.com/terms',
        'contact': {
            'name': 'Traffic Monitoring Support',
            'url': 'https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project',
            'email': 'support@trafficmonitor.local'
        },
        'license': {
            'name': 'MIT License',
            'url': 'https://opensource.org/licenses/MIT'
        }
    },
    'externalDocs': {
        'description': 'Find more info about the Traffic Monitoring System',
        'url': 'https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/blob/main/README.md'
    },
    'servers': [
        {
            'url': 'http://localhost:5000',
            'description': 'Development server'
        },
        {
            'url': 'http://100.121.231.16:5000',
            'description': 'Raspberry Pi production server'
        }
    ]
}

# Response examples for better documentation
ENHANCED_RESPONSE_EXAMPLES = {
    'system_health_example': {
        'summary': 'Healthy system status',
        'description': 'Example of a healthy system with all services running',
        'value': {
            'status': 'healthy',
            'timestamp': '2025-09-18T10:30:00Z',
            'uptime_seconds': 86400.5,
            'cpu_usage': 35.2,
            'memory_usage': 58.7,
            'disk_usage': 42.1,
            'temperature': 38.5,
            'services': {
                'redis': 'connected',
                'database': 'connected',
                'vehicle_detection': 'active',
                'speed_analysis': 'active',
                'data_fusion': 'active',
                'camera': 'active',
                'dht22_sensor': 'active'
            }
        }
    },
    'vehicle_detection_example': {
        'summary': 'Vehicle detection results',
        'description': 'Example response showing detected vehicles',
        'value': {
            'detections': [
                {
                    'id': 'det_20250918_103000_001',
                    'timestamp': '2025-09-18T10:30:00Z',
                    'confidence': 0.95,
                    'bbox': [120, 80, 200, 150],
                    'vehicle_type': 'car',
                    'direction': 'north',
                    'lane': 1
                },
                {
                    'id': 'det_20250918_103001_002',
                    'timestamp': '2025-09-18T10:30:01Z',
                    'confidence': 0.87,
                    'bbox': [350, 90, 180, 140],
                    'vehicle_type': 'truck',
                    'direction': 'south',
                    'lane': 2
                }
            ],
            'count': 2,
            'timespan_seconds': 60
        }
    },
    'speed_analysis_example': {
        'summary': 'Speed measurement results',
        'description': 'Example response showing speed detections',
        'value': {
            'speeds': [
                {
                    'id': 'speed_20250918_103000_001',
                    'start_time': '2025-09-18T10:30:00Z',
                    'end_time': '2025-09-18T10:30:05Z',
                    'avg_speed_mps': 13.89,
                    'avg_speed_mph': 31.1,
                    'max_speed_mps': 15.2,
                    'direction': 'north',
                    'confidence': 0.92
                }
            ],
            'count': 1,
            'timespan_seconds': 60
        }
    },
    'weather_data_example': {
        'summary': 'Current weather conditions',
        'description': 'Example weather data from multiple sources',
        'value': {
            'timestamp': '2025-09-18T10:30:00Z',
            'current_conditions': {
                'temperature_c': 22.5,
                'temperature_f': 72.5,
                'humidity': 65.3,
                'pressure': 1013.25,
                'sky_condition': 'clear'
            },
            'dht22_sensor': {
                'temperature_c': 22.1,
                'humidity': 64.8,
                'timestamp': '2025-09-18T10:29:55Z'
            },
            'airport_data': {
                'temperature_c': 22.8,
                'humidity': 66.0,
                'wind_speed': 3.2,
                'visibility': 10.0,
                'timestamp': '2025-09-18T10:25:00Z'
            },
            'analysis': {
                'visibility_impact': 'none',
                'detection_adjustment': 1.0,
                'weather_score': 0.95
            }
        }
    }
}

def get_custom_swagger_template():
    """Get the custom Swagger UI HTML template"""
    return SWAGGER_UI_TEMPLATE

def get_swagger_config():
    """Get the Swagger configuration"""
    return SWAGGER_CONFIG

def get_swagger_ui_config():
    """Get the Swagger UI configuration"""
    return SWAGGER_UI_CONFIG

def get_openapi_enhancements():
    """Get OpenAPI specification enhancements"""
    return OPENAPI_ENHANCEMENTS

def get_response_examples():
    """Get enhanced response examples"""
    return ENHANCED_RESPONSE_EXAMPLES