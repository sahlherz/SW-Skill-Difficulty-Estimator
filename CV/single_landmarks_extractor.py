import mediapipe as mp
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time

start_time = time.perf_counter()

baseOpts = python.BaseOptions(model_asset_path="CV/pose_landmarker_heavy.task")
options = vision.PoseLandmarkerOptions(base_options=baseOpts, running_mode=vision.RunningMode.VIDEO)

detector = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture("./_videos/sBMfOfntE3diD1zOssoqxdxR1PU2.mp4") #my video

frame_count = 0
frame_list = []

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    timestamp = int(frame_count / fps * 1_000)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    result = detector.detect_for_video(mp_image, timestamp)
    
    matrix = np.full((33, 7), np.nan, dtype=np.float32)
    if result.pose_landmarks and result.pose_world_landmarks:
        for id_lm, (image_lm, world_lm) in enumerate(zip(result.pose_landmarks[0], result.pose_world_landmarks[0])):
            
            matrix[id_lm, :] = [world_lm.x, world_lm.y, world_lm.z, world_lm.visibility, world_lm.presence, image_lm.x, image_lm.y]
        
    frame_list.append(matrix)

        
    frame_count += 1

cap.release()

matrix = np.stack(frame_list)
np.save("landmarks.npy", matrix)

end_time = time.perf_counter()
execution_time = end_time - start_time
print(f"Execution time: {execution_time:.6f} seconds")
