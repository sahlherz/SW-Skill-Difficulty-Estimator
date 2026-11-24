import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import threading
import time

# --- SETUP DETECTOR ---
baseOpts = python.BaseOptions(model_asset_path="CV/pose_landmarker_heavy.task")
options = vision.PoseLandmarkerOptions(base_options=baseOpts, running_mode=vision.RunningMode.VIDEO)
detector = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture("./_videos/IAAQEyPks4dMzTOWRfwQziCxHXk1.mp4")
window_name = 'MediaPipe Pose'

cv2.namedWindow('MediaPipe Pose', cv2.WINDOW_NORMAL)
cv2.resizeWindow('MediaPipe Pose', 400, 711) # Set width and height here

# Global variables to share data between threads
latest_result = None
frame_to_process = None
lock = threading.Lock()

def detection_thread():
    global latest_result, frame_to_process
    frame_count = 1
    while cap.isOpened():
        if frame_to_process is not None:
            # 1. Grab a copy of the frame to work on
            with lock:
                local_frame = frame_to_process.copy()
                frame_to_process = None # Reset for next capture
            
            # 2. Run detection
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30
            timestamp = int(frame_count / fps * 1_000)
            rgb_frame = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            res = detector.detect_for_video(mp_image, timestamp)
            
            # 3. Save result
            with lock:
                latest_result = res
        else:
            time.sleep(0.001) # Avoid burning CPU while waiting
        frame_count += 1

# Start the background thread
t = threading.Thread(target=detection_thread, daemon=True)
t.start()

# --- MAIN LOOP (Video Playback) ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    # Pass the fresh frame to the detector thread
    with lock:
        frame_to_process = frame

    # Draw the MOST RECENT results found by the background thread
    with lock:
        if latest_result and latest_result.pose_landmarks:
            h, w = frame.shape[:2]
            for landmark in latest_result.pose_landmarks[0]:
                px, py = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (px, py), 5, (0, 255, 0), -1)

    # Display at normal video speed
    cv2.imshow(window_name, frame)
    
    # 33ms wait roughly matches 30fps video
    if cv2.waitKey(33) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
