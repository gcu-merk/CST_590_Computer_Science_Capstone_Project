#!/bin/bash
# SSD Health Alert Script
# This script checks SSD health and sends alerts if usage is concerning

LOG_FILE="/mnt/storage/logs/ssd_alerts.log"
ALERT_THRESHOLD=50  # Alert when SSD usage exceeds 50%

# Run the Python monitoring script and capture output
HEALTH_OUTPUT=$(python3 /mnt/storage/scripts/ssd_write_monitor.py)

# Extract the endurance percentage used
ENDURANCE_USED=$(echo "$HEALTH_OUTPUT" | grep "Endurance used:" | awk '{print $3}' | sed 's/%//')

# Check if we need to send an alert
if (( $(echo "$ENDURANCE_USED > $ALERT_THRESHOLD" | bc -l) )); then
    TIMESTAMP=$(date)
    echo "[$TIMESTAMP] ALERT: SSD endurance usage is ${ENDURANCE_USED}%" >> "$LOG_FILE"
    
    # You can add email notifications here if needed
    # echo "SSD Alert: ${ENDURANCE_USED}% usage detected" | mail -s "Pi SSD Alert" your-email@example.com
fi

# Log current status
TIMESTAMP=$(date)
echo "[$TIMESTAMP] SSD Health Check: ${ENDURANCE_USED}% used" >> "$LOG_FILE"