import numpy as np
from pathlib import Path
import csv
import cv2

videoDataPath = "_data/Intermediates CV/video_data_with_unrotated.csv"
landmarksFolderPath = Path("_data/landmarks")
videoPath = Path("_videos")

#Ok so my goal is to build the video data csv again. That csv has the fields:
# uid,status,failure_reason,n_frames,n_undetected,fps,width,height
# uid: from the filename
# status: all are "done" anyways
# failure_reason: none have this
# n_frames: from the .npy file
# n_undetected: count the number of all-NaN frames in the .npy file
# fps, width, height: from cv2 or something

# Let's do this


with open(videoDataPath,"w", newline="", encoding="utf-8") as vidData:
    fields = ["uid", "status", "failure_reason", "n_frames", "n_undetected", "fps", "width", "height"]

    writer = csv.DictWriter(vidData, fieldnames=fields)
    writer.writeheader()
    
    n=1
    for landmarkFile, video in zip(landmarksFolderPath.glob("*.npy"), videoPath.glob("*.mp4")):
        #From landmarks we get n_frames and n_undetected
        arr = np.load(landmarkFile)
        n_frames = arr.shape[0]
        n_undetected = np.isnan(arr).all(axis=(1,2)).sum() # np.isnan(arr) makes a binary matrix, .all(axis=(1,2)) makes a list n_frames long where 1 is an all-NaN frame, sum sums those to find the count 

        #From videos we get fps, width, height
        cap = cv2.VideoCapture(video)
        if cap.isOpened():
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)

        attributes = {
            "uid": landmarkFile.stem,
            "status": "done",
            "failure_reason": "",
            "n_frames": n_frames,
            "n_undetected": n_undetected,
            "fps": fps,
            "width": width,
            "height": height
        }
        # [landmarkFile.stem, "done", "", n_frames, n_undetected, fps, width, height]

        writer.writerow(attributes)


            

            
        
