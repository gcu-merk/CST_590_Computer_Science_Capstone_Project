# Dockerfile for Raspberry Pi 5 Edge ML Traffic Monitoring System
FROM arm64v8/python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

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
    && rm -rf /var/lib/apt/lists/*


# Raspberry Pi specific packages (picamera2, gpiozero, RPi.GPIO) should be installed on the Pi itself or in the running container, not during cloud build.
# See deployment instructions for details.

# Copy requirements first for better caching
COPY edge-processing/requirements.txt /app/edge-processing/
COPY edge-api/requirements.txt /app/edge-api/

# Install Python dependencies
RUN pip install --no-cache-dir -r edge-processing/requirements.txt
RUN pip install --no-cache-dir -r edge-api/requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data/exports /app/data/backups /app/data/models /app/config

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
