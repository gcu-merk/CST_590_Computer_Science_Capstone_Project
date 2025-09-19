#!/bin/bash
# Setup Docker cleanup cron job for host-level maintenance

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STORAGE_ROOT="${STORAGE_ROOT:-/mnt/storage}"

echo -e "${YELLOW}Setting up Docker cleanup cron job...${NC}"

# Create logs directory if it doesn't exist
sudo mkdir -p "$STORAGE_ROOT/logs"
sudo chown $(whoami):$(whoami) "$STORAGE_ROOT/logs"

# Add Docker cleanup cron job (daily at 3:00 AM)
CRON_JOB="0 3 * * * /usr/bin/docker system prune -f --filter until=24h >> $STORAGE_ROOT/logs/docker-cleanup.log 2>&1"

# Check if the cron job already exists
if crontab -l 2>/dev/null | grep -q "docker system prune"; then
    echo -e "${YELLOW}Docker cleanup cron job already exists${NC}"
    echo "Existing cron jobs:"
    crontab -l 2>/dev/null | grep "docker system prune"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Docker cleanup cron job added${NC}"
fi

# Test Docker cleanup immediately (dry run)
echo -e "${YELLOW}Testing Docker cleanup (showing what would be cleaned)...${NC}"
docker system df
echo
echo -e "${YELLOW}Running test cleanup...${NC}"
CLEANUP_RESULT=$(docker system prune -f --filter until=24h 2>&1)
echo "$CLEANUP_RESULT"

# Log the test run
echo "$(date): Test cleanup - $CLEANUP_RESULT" >> "$STORAGE_ROOT/logs/docker-cleanup.log"

echo
echo -e "${GREEN}✓ Docker cleanup cron job setup complete!${NC}"
echo -e "${YELLOW}Cron job details:${NC}"
echo "• Schedule: Daily at 3:00 AM"
echo "• Command: docker system prune -f --filter until=24h"
echo "• Log file: $STORAGE_ROOT/logs/docker-cleanup.log"
echo
echo -e "${YELLOW}To view the cron job:${NC}"
echo "crontab -l | grep docker"
echo
echo -e "${YELLOW}To view cleanup logs:${NC}"
echo "tail -f $STORAGE_ROOT/logs/docker-cleanup.log"