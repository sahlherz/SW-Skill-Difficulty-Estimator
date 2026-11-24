"""
Angle visualizer for SW Skill Difficulty Estimator.

Draws, over the source video:
  - landmarks, colored red->green by visibility, with the visibility number
  - joint-angle arcs at each configured joint, with the angle in degrees
  - the arc/number colored by a CONFIDENCE score derived from the visibility of
    the three landmarks the angle is built from

Confidence modes (switch live with 'c'):
    min      - angle is only as good as its worst landmark
    mean     - average of the three
    product  - punishes several mediocre landmarks harder than min

Controls:
    space   play / pause
    . / ,   step one frame forward / back (works while paused)
    j / l   jump back / forward 10 frames
    c       cycle confidence mode
    a       cycle which angle SET is drawn (see ANGLE_SETS)
    v       toggle per-landmark visibility numbers
    h       toggle the help overlay
    q       quit

Usage:
    python angle_visualizer.py <uid>
    python angle_visualizer.py <uid> --video-dir _videos --npy-dir _data/landmarks
    python angle_visualizer.py <uid> --start 300
"""

import argparse
import os
import numpy as np
import cv2

# ---------------------------------------------------------------- landmarks
# MediaPipe Pose landmark indices.
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW,    R_ELBOW    = 13, 14
L_WRIST,    R_WRIST    = 15, 16
L_HIP,      R_HIP      = 23, 24
L_KNEE,     R_KNEE     = 25, 26
L_ANKLE,    R_ANKLE    = 27, 28

# Each angle: (label, end1, vertex, end2)
ANGLE_DEFS = {
    "elbow_L":    ("L elbow",    L_WRIST,    L_ELBOW,    L_SHOULDER),
    "elbow_R":    ("R elbow",    R_WRIST,    R_ELBOW,    R_SHOULDER),
    "shoulder_L": ("L shoulder", L_ELBOW,    L_SHOULDER, L_HIP),
    "shoulder_R": ("R shoulder", R_ELBOW,    R_SHOULDER, R_HIP),
    "hip_L":      ("L hip",      L_SHOULDER, L_HIP,      L_KNEE),
    "hip_R":      ("R hip",      R_SHOULDER, R_HIP,      R_KNEE),
    "knee_L":     ("L knee",     L_HIP,      L_KNEE,     L_ANKLE),
    "knee_R":     ("R knee",     R_HIP,      R_KNEE,     R_ANKLE),
}

# Cycle through these with 'a'.
ANGLE_SETS = [
    ("elbows",    ["elbow_L", "elbow_R"]),
    ("shoulders", ["shoulder_L", "shoulder_R"]),
    ("hips",      ["hip_L", "hip_R"]),
    ("knees",     ["knee_L", "knee_R"]),
    ("arms",      ["elbow_L", "elbow_R", "shoulder_L", "shoulder_R"]),
    ("all",       list(ANGLE_DEFS.keys())),
    ("none",      []),
]

CONF_MODES = ["min", "mean", "product"]

# Skeleton connections, for context.
SKELETON = [
    (L_SHOULDER, R_SHOULDER), (L_SHOULDER, L_ELBOW), (L_ELBOW, L_WRIST),
    (R_SHOULDER, R_ELBOW), (R_ELBOW, R_WRIST),
    (L_SHOULDER, L_HIP), (R_SHOULDER, R_HIP), (L_HIP, R_HIP),
    (L_HIP, L_KNEE), (L_KNEE, L_ANKLE), (R_HIP, R_KNEE), (R_KNEE, R_ANKLE),
]

VIS_CH = 3  # channel index of visibility


# ---------------------------------------------------------------- geometry
def angle_at(frame_lms, end1, vertex, end2):
    """Angle in degrees at `vertex`, from the world xyz of one frame.
    frame_lms is [33, 7]. Returns None if any point is NaN."""
    a = frame_lms[end1, :3]
    b = frame_lms[vertex, :3]
    c = frame_lms[end2, :3]
    if np.isnan(a).any() or np.isnan(b).any() or np.isnan(c).any():
        return None

    v1, v2 = a - b, c - b
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return None
    cos = np.clip(np.dot(v1, v2) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def confidence(frame_lms, idxs, mode):
    """Combine the visibility of the landmarks an angle depends on."""
    vis = np.array([frame_lms[i, VIS_CH] for i in idxs], dtype=float)
    if np.isnan(vis).any():
        return 0.0
    if mode == "min":
        return float(vis.min())
    if mode == "mean":
        return float(vis.mean())
    if mode == "product":
        return float(np.prod(vis))
    return float(vis.min())


# ---------------------------------------------------------------- drawing
def heat_color(t):
    """t in [0,1] -> BGR, red (low) through yellow to green (high)."""
    t = 0.0 if t is None or np.isnan(t) else float(np.clip(t, 0.0, 1.0))
    if t < 0.5:                      # red -> yellow
        g = int(255 * (t / 0.5))
        return (0, g, 255)
    g = 255                          # yellow -> green
    r = int(255 * (1 - (t - 0.5) / 0.5))
    return (0, g, r)


def to_px(frame_lms, idx, w, h):
    """Image-space pixel position of a landmark (channels 5,6 = image x,y)."""
    x, y = frame_lms[idx, 5], frame_lms[idx, 6]
    if np.isnan(x) or np.isnan(y):
        return None
    return (int(x * w), int(y * h))


def draw_arc(img, vertex_px, p1_px, p2_px, deg, color, radius=34):
    """Draw the angle arc at the vertex, spanning between the two limbs."""
    a1 = np.degrees(np.arctan2(p1_px[1] - vertex_px[1], p1_px[0] - vertex_px[0]))
    a2 = np.degrees(np.arctan2(p2_px[1] - vertex_px[1], p2_px[0] - vertex_px[0]))

    # Sweep the short way around, so the arc matches the angle being reported.
    sweep = (a2 - a1 + 180) % 360 - 180
    cv2.ellipse(img, vertex_px, (radius, radius), 0, a1, a1 + sweep, color, 2)

    # Label just outside the arc, on the bisector.
    mid = np.radians(a1 + sweep / 2)
    lx = int(vertex_px[0] + (radius + 20) * np.cos(mid))
    ly = int(vertex_px[1] + (radius + 20) * np.sin(mid))
    txt = f"{deg:.0f}"
    cv2.putText(img, txt, (lx - 12, ly + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, txt, (lx - 12, ly + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2, cv2.LINE_AA)


def draw_frame(img, frame_lms, angle_keys, conf_mode, show_vis_nums):
    h, w = img.shape[:2]

    # skeleton
    for i, j in SKELETON:
        p, q = to_px(frame_lms, i, w, h), to_px(frame_lms, j, w, h)
        if p and q:
            cv2.line(img, p, q, (90, 90, 90), 2, cv2.LINE_AA)

    # landmarks, colored + numbered by visibility
    for i in range(frame_lms.shape[0]):
        p = to_px(frame_lms, i, w, h)
        if p is None:
            continue
        vis = frame_lms[i, VIS_CH]
        cv2.circle(img, p, 4, heat_color(vis), -1, cv2.LINE_AA)
        if show_vis_nums and not np.isnan(vis):
            cv2.putText(img, f"{vis:.2f}", (p[0] + 6, p[1] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, f"{vis:.2f}", (p[0] + 6, p[1] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.34, (235, 235, 235), 1, cv2.LINE_AA)

    # angles
    readout = []
    for key in angle_keys:
        label, e1, vx, e2 = ANGLE_DEFS[key]
        deg = angle_at(frame_lms, e1, vx, e2)
        if deg is None:
            readout.append((label, None, 0.0))
            continue
        conf = confidence(frame_lms, (e1, vx, e2), conf_mode)
        color = heat_color(conf)
        pv, p1, p2 = (to_px(frame_lms, vx, w, h),
                      to_px(frame_lms, e1, w, h),
                      to_px(frame_lms, e2, w, h))
        if pv and p1 and p2:
            draw_arc(img, pv, p1, p2, deg, color)
        readout.append((label, deg, conf))
    return readout


def draw_hud(img, frame_idx, n_frames, conf_mode, set_name, readout, paused, show_help):
    lines = [f"frame {frame_idx}/{n_frames - 1}"
             f"{'  [PAUSED]' if paused else ''}",
             f"angles: {set_name}   conf: {conf_mode}"]
    for label, deg, conf in readout:
        lines.append(f"  {label:<11} "
                     + (f"{deg:6.1f}d  conf {conf:.2f}" if deg is not None else "   --"))
    if show_help:
        lines += ["", "space play/pause   . , step   j l jump10",
                  "c conf mode   a angle set   v vis nums   h help   q quit"]

    pad, lh = 8, 19
    box_h = pad * 2 + lh * len(lines)
    box_w = 330
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (box_w, box_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)

    for k, line in enumerate(lines):
        cv2.putText(img, line, (pad, pad + lh * (k + 1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (240, 240, 240), 1, cv2.LINE_AA)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("uid")
    ap.add_argument("--video-dir", default="_videos")
    ap.add_argument("--npy-dir", default="_data/landmarks")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--width", type=int, default=520, help="display width")
    args = ap.parse_args()

    video_path = os.path.join(args.video_dir, f"{args.uid}.mp4")
    npy_path = os.path.join(args.npy_dir, f"{args.uid}.npy")
    for p in (video_path, npy_path):
        if not os.path.exists(p):
            print(f"ERROR: not found: {p}")
            return

    lms = np.load(npy_path)          # [T, 33, 7] -- RAW, untrimmed
    cap = cv2.VideoCapture(video_path)
    n_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    n_frames = min(len(lms), n_video) if n_video > 0 else len(lms)
    print(f"{args.uid}: landmarks T={len(lms)}, video frames={n_video}")

    win = "angle visualizer"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    idx = max(0, min(args.start, n_frames - 1))
    paused = True
    conf_i, set_i = 0, 0
    show_vis_nums = True
    show_help = True
    last_idx = -1
    frame = None

    while True:
        if idx != last_idx:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                idx = max(0, idx - 1)
                paused = True
                continue
            last_idx = idx

        img = frame.copy()
        set_name, keys = ANGLE_SETS[set_i]
        readout = draw_frame(img, lms[idx], keys, CONF_MODES[conf_i], show_vis_nums)
        draw_hud(img, idx, n_frames, CONF_MODES[conf_i], set_name,
                 readout, paused, show_help)

        h, w = img.shape[:2]
        scale = args.width / w
        cv2.imshow(win, cv2.resize(img, (args.width, int(h * scale))))

        key = cv2.waitKey(0 if paused else 25) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('.'):
            idx = min(idx + 1, n_frames - 1); paused = True
        elif key == ord(','):
            idx = max(idx - 1, 0); paused = True
        elif key == ord('l'):
            idx = min(idx + 10, n_frames - 1); paused = True
        elif key == ord('j'):
            idx = max(idx - 10, 0); paused = True
        elif key == ord('c'):
            conf_i = (conf_i + 1) % len(CONF_MODES)
        elif key == ord('a'):
            set_i = (set_i + 1) % len(ANGLE_SETS)
        elif key == ord('v'):
            show_vis_nums = not show_vis_nums
        elif key == ord('h'):
            show_help = not show_help

        if not paused:
            idx += 1
            if idx >= n_frames:
                idx = 0

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
