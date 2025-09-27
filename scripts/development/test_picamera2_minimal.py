from picamera2 import Picamera2
import time

print("Starting minimal Picamera2 test...")
picam2 = Picamera2()
picam2.start()
time.sleep(2)  # Give the camera time to warm up
picam2.capture_file("/tmp/test_picamera2.jpg")
picam2.stop()
print("Image captured to /tmp/test_picamera2.jpg")
