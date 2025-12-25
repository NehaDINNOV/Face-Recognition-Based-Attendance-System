import cv2

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("❌ Camera is not opening. Check your webcam permissions.")
else:
    print("✅ Camera is working fine.")
camera.release()
