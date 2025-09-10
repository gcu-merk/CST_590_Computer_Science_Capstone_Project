import cv2

def main():
    cap = cv2.VideoCapture(0)  # 0 is usually the default camera
    if not cap.isOpened():
        print("Camera not accessible")
        return
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("test_image.jpg", frame)
        print("Image captured and saved as test_image.jpg")
    else:
        print("Failed to capture image")
    cap.release()

if __name__ == "__main__":
    main()
