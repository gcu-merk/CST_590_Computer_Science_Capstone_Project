#!/bin/bash
# Generate self-signed SSL certificate for development HTTPS

echo "🔐 Generating self-signed SSL certificate for Pi API HTTPS access..."

# Create SSL directory
mkdir -p nginx/ssl

# Generate private key
openssl genrsa -out nginx/ssl/key.pem 2048

# Generate certificate
openssl req -new -x509 -key nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 \
    -subj "/C=US/ST=Oklahoma/L=OKC/O=TrafficMonitoring/CN=100.121.231.16"

echo "✅ SSL certificate generated successfully!"
echo "📁 Files created:"
echo "   - nginx/ssl/key.pem (private key)"
echo "   - nginx/ssl/cert.pem (certificate)"
echo ""
echo "⚠️  Note: This is a self-signed certificate for development use only."
echo "   Browsers will show a security warning that you'll need to accept."