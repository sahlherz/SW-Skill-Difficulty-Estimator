import mediapipe as mp
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import csv
import numpy

#baseOpts = python.BaseOptions(model_asset_path="pose_landmarker_heavy.task", delegate=python.BaseOptions.Delegate.GPU)
baseOpts = python.BaseOptions(model_asset_path="CV/pose_landmarker_heavy.task")
options = vision.PoseLandmarkerOptions(base_options=baseOpts, running_mode=vision.RunningMode.VIDEO)

detector = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture("./videos/sBMfOfntE3diD1zOssoqxdxR1PU2.mp4") #my video

window_name = 'MediaPipe Pose'
cv2.namedWindow('MediaPipe Pose', cv2.WINDOW_NORMAL)
cv2.resizeWindow('MediaPipe Pose', 400, 711) # Set width and height here

frame_count = 1
with open("landmarks.csv", "w", newline="", encoding="utf-8") as file:
    fields = ["frame", "landmark_id", "x", "y", "z", "visibility", "presence", "image_x", "image_y", "existence"]
    writer = csv.DictWriter(file, fields)
    writer.writeheader()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        #frame = cv2.resize(frame, (480, 854)) 

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        timestamp = int(frame_count / fps * 1_000)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = detector.detect_for_video(mp_image, timestamp)
        
        if result.pose_landmarks and result.pose_world_landmarks:
            id = 0
            for image_lm, world_lm in zip(result.pose_landmarks[0], result.pose_world_landmarks[0]):
                image_x = image_lm.x
                image_y = image_lm.y
                image_z = image_lm.z

                visibility = world_lm.visibility
                world_x = world_lm.x
                world_y = world_lm.y
                world_z = world_lm.z
                presence = world_lm.presence


                pixel_x = int(image_x * frame.shape[1])
                pixel_y = int(image_y* frame.shape[0])

                cv2.circle(frame, (pixel_x, pixel_y), 5, (255 - 255*visibility, 255*visibility, 0), -1)

                row = {
                    "frame": frame_count,
                    "landmark_id": id,
                    "x": world_x,
                    "y": world_y,
                    "z": world_z,
                    "visibility": visibility,
                    "presence": presence,
                    "image_x": image_x,
                    "image_y": image_y,
                    "existence": 1
                }

                #writer.writerow(row)
                id += 1
        else:
            row = {"frame": frame_count, "landmark_id": "NaN", "x": "NaN", "y": "NaN", "z": "NaN", "visibility": "NaN", "presence": "NaN", "image_x": "NaN", "image_y": "NaN", "existence": 0}
            writer.writerow(row)

        frame_count += 1


                
        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
