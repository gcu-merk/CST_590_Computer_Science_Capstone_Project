# Dockerfile for Raspberry Pi 5 Edge ML Traffic Monitoring System
FROM arm64v8/python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Add Raspberry Pi OS repositories for camera packages
RUN apt-get update && apt-get install -y wget gnupg && \
    mkdir -p /usr/share/keyrings && \
    wget -qO - http://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor > /usr/share/keyrings/raspberrypi-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.org/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libatlas-base-dev \
    gfortran \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    sqlite3 \
    libsqlite3-dev \
    git \
    wget \
    curl \
    # Camera and video processing libraries
    python3-opencv \
    libcamera-dev \
    libcamera-tools \
    v4l-utils \
    fswebcam \
    libgpiod2 \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*


# Try to install Raspberry Pi specific packages (may not be available in all environments)
RUN apt-get update && ( \
    apt-get install -y \
        python3-picamera2 \
        libcamera-apps \
        rpicam-apps \
        imx500-all \
        python3-imx500 \
    || echo "Raspberry Pi specific packages not available, continuing without them" \
    ) ; rm -rf /var/lib/apt/lists/*

# Install IMX500 libraries from Raspberry Pi repository if available
RUN apt-get update && ( \
    apt-get install -y \
        imx500-tools \
        imx500-models \
    || echo "IMX500 tools not available" \
    ) ; rm -rf /var/lib/apt/lists/*

# Install Python camera packages via pip as fallback
RUN pip install --no-cache-dir \
    picamera2 \
    opencv-python \
    numpy \
    pillow \
    imx500 \
    || echo "Some Python packages may not be available"

# Try to install IMX500 Python package specifically
RUN pip install --no-cache-dir \
    imx500 \
    || echo "IMX500 Python package not available"

# Copy requirements first for better caching
COPY edge_processing/requirements-cloud.txt /app/edge_processing/
COPY edge_processing/requirements-pi.txt /app/edge_processing/
COPY edge_api/requirements.txt /app/edge_api/

# Install Python dependencies (cloud-compatible only)
RUN pip install --no-cache-dir -r edge_processing/requirements-cloud.txt
RUN pip install --no-cache-dir -r edge_api/requirements.txt

# Try to install Pi-specific dependencies (may fail in non-Pi environments)
RUN pip install --no-cache-dir -r edge_processing/requirements-pi.txt || echo "Pi-specific packages not available"

# Copy application code
COPY . /app/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh /app/scripts/*.py 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /mnt/storage/logs/docker /mnt/storage/data/exports /mnt/storage/data/backups /mnt/storage/data/models /mnt/storage/config

# Add GPIO group and user permissions for Raspberry Pi 5
RUN groupadd -f gpio && \
    groupadd -f i2c && \
    groupadd -f spi && \
    usermod -a -G gpio,i2c,spi root

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the main application
CMD ["python", "main_edge_app.py"]
