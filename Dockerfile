# Multi-stage Dockerfile following Docker best practices
# Raspberry Pi 5 Edge ML Traffic Monitoring System

# Build stage - for compiling dependencies
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies including SSL/TLS support
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libhdf5-dev \
    libatlas-base-dev \
    gfortran \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    git \
    wget \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    openssl \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Use system Python (has guaranteed SSL support)
ENV PATH="/usr/local/bin:$PATH"

# Copy and install Python dependencies
COPY edge_api/requirements.txt /tmp/requirements-api.txt
COPY edge_processing/requirements-pi.txt /tmp/requirements-pi.txt

# Install Python packages using system Python with SSL support
RUN pip3 install --no-cache-dir --upgrade pip

# Install API requirements with trusted hosts to handle SSL/certificate issues
RUN pip3 install --no-cache-dir --timeout=60 \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host www.piwheels.org \
    --trusted-host archive1.piwheels.org \
    -r /tmp/requirements-api.txt

# Install Pi packages that can work in Docker build environment
RUN pip3 install --no-cache-dir --timeout=60 \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host www.piwheels.org \
    --trusted-host archive1.piwheels.org \
    redis>=4.6.0 \
    numpy>=1.21.0 \
    pyserial>=3.5 \
    || echo "Some packages failed - will retry on Pi"

# Skip hardware-specific packages during build (install at runtime on Pi)
# These will be installed when container runs on actual Pi hardware:
# - picamera2, RPi.GPIO, gpiozero, lgpio (require Pi hardware)
# - opencv-python (large package, install at runtime)

# Runtime stage - minimal runtime image
FROM python:3.11-slim-bookworm AS runtime

# Install essential SSL/TLS support and add Raspberry Pi OS repositories
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    openssl \
    && mkdir -p /usr/share/keyrings && \
    wget -qO - https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor > /usr/share/keyrings/raspberrypi-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.org/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    # Essential runtime libraries
    python3-opencv \
    libcamera-tools \
    v4l-utils \
    sqlite3 \
    libsqlite3-dev \
    curl \
    # Hardware interface libraries  
    libgpiod2 \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Raspberry Pi specific packages with proper error handling
RUN apt-get update && \
    # Try to install Pi-specific packages and create availability flags
    mkdir -p /tmp/package-flags && \
    (apt-get install -y python3-picamera2 && touch /tmp/package-flags/picamera2-available || \
     echo "python3-picamera2 not available - will install at runtime") && \
    (apt-get install -y libcamera-apps && touch /tmp/package-flags/libcamera-available || \
     echo "libcamera-apps not available - will install at runtime") && \
    (apt-get install -y rpicam-apps && touch /tmp/package-flags/rpicam-available || \
     echo "rpicam-apps not available - will install at runtime") && \
    (apt-get install -y imx500-all && touch /tmp/package-flags/imx500-available || \
     echo "imx500-all not available - will install at runtime") && \
    (apt-get install -y python3-imx500 && touch /tmp/package-flags/python3-imx500-available || \
     echo "python3-imx500 not available - will install at runtime") && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create application user (security best practice)
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /bin/bash appuser && \
    # Create hardware access groups with proper error handling
    for group in gpio i2c spi; do \
        getent group $group || groupadd $group; \
    done && \
    usermod -a -G gpio,i2c,spi appuser

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appuser . /app/

# Create data directories with proper permissions
RUN mkdir -p /mnt/storage/{logs,data,config,scripts} && \
    chown -R appuser:appuser /mnt/storage

# Make entrypoint executable
RUN chmod +x /app/docker_entrypoint.py

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 5000

# Health check using Python with proper error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys,urllib.request; urllib.request.urlopen('http://localhost:5000/api/health'); sys.exit(0)" || exit 1

# Switch to non-root user
USER appuser

# Use Python entry point instead of shell script
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
