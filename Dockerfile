# Multi-stage Dockerfile following Docker best practices
# Raspberry Pi 5 Edge ML Traffic Monitoring System

# Build stage - for compiling dependencies
FROM arm64v8/python:3.11-slim-bookworm AS builder

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
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Update SSL certificates
RUN update-ca-certificates

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY edge_api/requirements.txt /tmp/requirements-api.txt
COPY edge_processing/requirements-pi.txt /tmp/requirements-pi.txt

# Install Python packages in virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements-api.txt && \
    (pip install --no-cache-dir -r /tmp/requirements-pi.txt || echo "Some Pi packages not available")

# Runtime stage - minimal runtime image
FROM arm64v8/python:3.11-slim-bookworm AS runtime

# Install essential SSL/TLS support and add Raspberry Pi OS repositories
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    openssl \
    && mkdir -p /usr/share/keyrings && \
    wget -qO - http://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor > /usr/share/keyrings/raspberrypi-archive-keyring.gpg && \
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
    # Raspberry Pi specific packages (optional)
    && (apt-get install -y \
        python3-picamera2 \
        libcamera-apps \
        rpicam-apps \
        imx500-all \
        python3-imx500 \
    || echo "Pi packages not available") \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application user (security best practice)
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /bin/bash appuser && \
    # Add to GPIO groups for Pi hardware access
    groupadd -f gpio && \
    groupadd -f i2c && \
    groupadd -f spi && \
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

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Switch to non-root user
USER appuser

# Use Python entry point instead of shell script
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
