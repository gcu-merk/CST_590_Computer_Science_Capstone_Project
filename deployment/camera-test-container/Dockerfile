FROM debian:bullseye-slim

# Small container that captures a still image from /dev/video0 using fswebcam
# or generates a placeholder image if no camera device present.

RUN apt-get update && \
    apt-get install -y --no-install-recommends fswebcam imagemagick ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user to run captures
RUN useradd -m -s /bin/bash camerabot

WORKDIR /app
COPY capture.sh /app/capture.sh
RUN chmod +x /app/capture.sh

USER camerabot

ENTRYPOINT ["/app/capture.sh"]
