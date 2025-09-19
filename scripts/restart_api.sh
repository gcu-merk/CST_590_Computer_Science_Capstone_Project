#!/bin/bash

echo "=== Restarting Traffic Monitor Container ==="

echo "Stopping traffic-monitor container..."
docker stop traffic-monitor

echo "Removing traffic-monitor container..."
docker rm traffic-monitor

echo "Starting traffic-monitor container with docker-compose..."
docker-compose -f docker-compose.yml -f docker-compose.pi.yml up -d traffic-monitor

echo "Waiting 10 seconds for container to start..."
sleep 10

echo "Checking container status:"
docker ps --filter name=traffic-monitor --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "Checking logs:"
docker logs --tail=10 traffic-monitor

echo "Testing API health endpoint:"
sleep 5
curl -s http://localhost:5000/api/health || echo "API health check failed"