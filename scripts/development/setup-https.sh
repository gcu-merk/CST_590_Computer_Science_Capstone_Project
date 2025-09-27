#!/bin/bash
# Setup HTTPS for Tailscale on Raspberry Pi

echo "🔐 Setting up Tailscale HTTPS for edge-traffic-monitoring..."

# Check current Tailscale status
echo "📋 Current Tailscale status:"
tailscale status

# Get the hostname
HOSTNAME=$(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')
echo "🏠 Hostname: $HOSTNAME"

# Request certificate for this machine
echo "📜 Requesting SSL certificate..."
tailscale cert $HOSTNAME

# Check if certificate was created
if [ -f "${HOSTNAME}.crt" ] && [ -f "${HOSTNAME}.key" ]; then
    echo "✅ SSL certificate created successfully!"
    echo "📂 Certificate files:"
    ls -la ${HOSTNAME}.*
    
    # Move certificates to nginx directory
    sudo mkdir -p /etc/nginx/ssl
    sudo mv ${HOSTNAME}.crt /etc/nginx/ssl/
    sudo mv ${HOSTNAME}.key /etc/nginx/ssl/
    
    echo "📁 Certificates moved to /etc/nginx/ssl/"
    echo "🔧 Ready to configure nginx with HTTPS"
else
    echo "❌ Certificate generation failed"
    echo "ℹ️  You may need to enable HTTPS capability in Tailscale admin console"
fi

# Alternative: Enable Tailscale Funnel (direct HTTPS serving)
echo ""
echo "🚀 Alternative: Setting up Tailscale Funnel for direct HTTPS..."
echo "📝 This will serve your API directly over HTTPS without nginx"

# Serve the traffic-monitor container via Funnel
echo "🔗 Enabling Funnel for port 5000..."
tailscale funnel --bg --https=443 http://localhost:5000

echo ""
echo "🎉 Setup complete!"
echo "📡 Your API should now be available at:"
echo "   https://$HOSTNAME"
echo ""
echo "🧪 Test with:"
echo "   curl https://$HOSTNAME/api/health"