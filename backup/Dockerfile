FROM python:3.11-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    pigz \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir schedule

# Create backup directory
RUN mkdir -p /mnt/backups

# Copy backup script
COPY sd_card_backup.py /app/sd_card_backup.py
RUN chmod +x /app/sd_card_backup.py

WORKDIR /app

# Run as root (required for block device access)
USER root

CMD ["python", "-u", "sd_card_backup.py"]
