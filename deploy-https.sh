#!/bin/bash
# Deploy HTTPS configuration for Tailscale

echo "🚀 Deploying HTTPS configuration for Raspberry Pi..."

# Step 1: Copy files to the Pi
echo "📁 Copying configuration files to Pi..."
scp -r nginx/ pi@100.121.231.16:~/
scp setup-https.sh pi@100.121.231.16:~/
scp docker-compose.yml pi@100.121.231.16:~/

echo "🔐 Setting up SSL certificates on Pi..."
ssh pi@100.121.231.16 'chmod +x setup-https.sh && ./setup-https.sh'

echo "🐳 Deploying nginx proxy container..."
ssh pi@100.121.231.16 'docker compose up -d nginx-proxy'

echo "🧪 Testing HTTPS connectivity..."
echo "Waiting 10 seconds for nginx to start..."
sleep 10

# Test the HTTPS endpoint
HOSTNAME="edge-traffic-monitoring.taild46447.ts.net"
echo "Testing: https://$HOSTNAME/api/health"

if curl -f -s "https://$HOSTNAME/api/health" > /dev/null; then
    echo "✅ HTTPS API is working!"
else
    echo "❌ HTTPS test failed. Check logs:"
    ssh pi@100.121.231.16 'docker logs nginx-proxy'
fi

echo ""
echo "🎉 Deployment complete!"
echo "📡 Your API is now available at:"
echo "   https://$HOSTNAME"
echo ""
echo "🌐 Update your website to use this HTTPS URL"