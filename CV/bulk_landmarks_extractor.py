import os, csv, glob, time, cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from concurrent.futures import ProcessPoolExecutor, as_completed

model_path    = os.path.abspath("CV/pose_landmarker_heavy.task")
video_directory     = "./_videos" #input directory
output_directory    = os.path.abspath("./_data/landmarks")
manifest_path = "./_data/Intermediates CV/video_data_rotated_only.csv" #manifest is now called video_data

# One video uses ~18% of CPU
num_workers = max(1, (os.cpu_count() or 8) // 2)

manifest_fields = ["uid", "status", "failure_reason", "n_frames", "n_undetected", "fps", "width", "height"]


def _failed(uid, reason, fps=0, width=0, height=0):
    return {"uid": uid, "status": "failed", "failure_reason": reason, "n_frames": 0, "n_undetected": 0, "fps": fps, "width": width, "height": height}


def process_video(video_path):
    #Runs in a worker process. Creates its OWN detector (VIDEO mode is stateful, so it must be fresh per video), extracts landmarks, saves the .npy, and returns a small manifest row.
    uid = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(output_directory, uid + ".npy")
    cap = None
    detector = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return _failed(uid, "could not open video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0: #just in case
            fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        base_opts = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_opts,
            running_mode=vision.RunningMode.VIDEO,
        )
        detector = vision.PoseLandmarker.create_from_options(options)

        frames = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = int(frame_count / fps * 1_000)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect_for_video(mp_image, timestamp)

            m = np.full((33, 7), np.nan, dtype=np.float32)
            if result.pose_landmarks and result.pose_world_landmarks:
                for i, (img_lm, w_lm) in enumerate(zip(result.pose_landmarks[0], result.pose_world_landmarks[0])):
                    m[i, :] = [w_lm.x, w_lm.y, w_lm.z, w_lm.visibility, w_lm.presence, img_lm.x, img_lm.y]
            frames.append(m)
            frame_count += 1

        if frame_count == 0:
            return _failed(uid, "no frames read", fps, width, height)

        matrix = np.stack(frames)
        np.save(out_path, matrix)

        n_undetected = int(np.isnan(matrix).all(axis=(1, 2)).sum())
        return {"uid": uid, "status": "done", "failure_reason": "", "n_frames": frame_count, "n_undetected": n_undetected, "fps": round(float(fps), 3), "width": width, "height": height}

    except Exception as e:
        return _failed(uid, repr(e))
    finally:
        if cap is not None:
            cap.release()
        if detector is not None:
            detector.close()


def main():
    os.makedirs(output_directory, exist_ok=True)

    video_paths = sorted(
        os.path.abspath(p) for p in (
            set(glob.glob(os.path.join(video_directory, "*.mp4"))) #lowercase
            | set(glob.glob(os.path.join(video_directory, "*.MP4"))) #uppercase
        )
    )

    # Resumability: Look which .npy's already exist, so that a re-run only processes what's missing.
    pending = [
        p for p in video_paths
        if not os.path.exists(
            os.path.join(output_directory, os.path.splitext(os.path.basename(p))[0] + ".npy")
        )
    ]
    total, todo = len(video_paths), len(pending)
    print(f"{total} videos found | {total - todo} already done | {todo} to process")
    if todo == 0:
        return

    manifest_is_new = not os.path.exists(manifest_path)
    completed = failed = 0
    t0 = time.perf_counter()

    # Main process writes the manifest, workers save their own .npy files (distinct paths, no contention) and return just the small metadata row. 
    with open(manifest_path, "a", newline="", encoding="utf-8") as mf:
        writer = csv.DictWriter(mf, fieldnames=manifest_fields)
        if manifest_is_new:
            writer.writeheader()
            mf.flush()

        with ProcessPoolExecutor(max_workers=num_workers) as ex:
            futures = {ex.submit(process_video, p): p for p in pending}
            for fut in as_completed(futures):
                path = futures[fut]
                uid = os.path.splitext(os.path.basename(path))[0]
                try:
                    row = fut.result()
                except Exception as e:
                    # Worker died hard
                    row = _failed(uid, f"worker crashed: {e!r}")

                writer.writerow(row)
                mf.flush()
                completed += 1
                if row["status"] == "failed":
                    failed += 1
                if completed % 25 == 0 or completed == todo:
                    elapsed = (time.perf_counter() - t0) / 60
                    print(f"{completed}/{todo} done | {failed} failed | "
                          f"{elapsed:.1f} min elapsed")

    print(f"Finished {completed} videos ({failed} failed) in {(time.perf_counter() - t0) / 60:.1f} min.")
    print(f"Landmarks -> {output_directory} / Manifest -> {manifest_path}")


if __name__ == "__main__":
    main()