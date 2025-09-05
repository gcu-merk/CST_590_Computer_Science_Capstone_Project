#!/usr/bin/env python3
"""
Test IMX500 camera access and save an image to external SSD.
"""
from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500
import cv2
import os

# Set your external SSD path (update as needed)
output_path = "/mnt/external_ssd/test_imx500_image.jpg"
model_path = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

try:
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Initialize Picamera2 and IMX500
    picam2 = Picamera2()
    camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)})
    picam2.configure(camera_config)
    picam2.start()
    imx500 = IMX500(model_path)

    # Capture image
    frame = picam2.capture_array()
    cv2.imwrite(output_path, frame)
    print(f"Image saved to {output_path}")

    # Optionally, get detection results
    request = picam2.capture_request()
    outputs = imx500.get_outputs(request.get_metadata())
    print("Detection outputs:", outputs)
    request.release()

except Exception as e:
    print(f"Error accessing IMX500 camera: {e}")
