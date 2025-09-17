Camera test container

This is a minimal container that captures a single JPEG image from `/dev/video0` and writes it to `/mnt/storage/camera_capture/live`.

Build:

    docker build -t camera-test:latest .

Run (one-shot):

    docker run --rm \
      --device /dev/video0:/dev/video0 \
      -v /mnt/storage/camera_capture/live:/mnt/storage/camera_capture/live \
      camera-test:latest

Run as a periodic container (every minute) using a simple loop (host):

    while true; do docker run --rm --device /dev/video0:/dev/video0 -v /mnt/storage/camera_capture/live:/mnt/storage/camera_capture/live camera-test:latest; sleep 60; done

Notes:
- The container uses `fswebcam` to capture a still image if `/dev/video0` is present, otherwise it generates a placeholder image using ImageMagick.
- The `OUT_DIR` environment variable can be overridden at runtime.
- This container is intentionally standalone and does not modify any existing project files.
