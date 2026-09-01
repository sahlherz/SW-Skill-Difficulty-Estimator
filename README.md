# Calisthenics skill difficulty estimation from video

This repository contains the code for a project estimating calisthenics skill difficulty from video, using pose estimation and Elo-derived difficulty supervision.

The dataset was built from a ranked calisthenics app's leaderboard (Elo ratings, videos, and skill metadata), collected under a data-use agreement with the platform's founder. The dataset, the app's collection endpoints, and the scraping method are not included in this repository.

## Method

```
collect → extract landmarks → build manifest → filter cohort → train
```

Videos are processed with MediaPipe pose estimation into per-video landmark tensors. Difficulty labels come from community-judged athlete Elo ratings on the source leaderboard rather than hand-assigned scores. Resistance bands and added weight change difficulty substantially but are nearly indistinguishable from unassisted reps in pose-landmark space, so the corpus was hand-labeled for both to allow exclusion or explicit modeling. Train/test splits are athlete-disjoint to prevent identity leakage.

## Installation

Requires Python 3.12 (MediaPipe Tasks API).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Project structure

```
_data/
├── landmarks/                      # sample npy, shape [T, 33, 7]         
└── megalb.csv                      # sample row of the final, unified leaderboard csv file.
_scripts/
├── processing/                     # pose extraction, manifest building, labeling
├── build_manifest.py               # used already-computed landmarks as ground truth for rebuilding a video-data file after I fixed an issue of 50 videos being rotated
└── leaderboard_csv_search.py       # Preliminary search through skill names and descriptions to estimate band usage count; ended up being only 2 off
_videos/
└── example video                   # video of me
CV/
├── bulk_landmarks_extractor.py     # parallelized extractor of files in _videos -> landmarks. runs mediapipe for all the landmarks. also creates a csv of useful video data
├── computer_vision.py              # me experimenting with mediapipe at the beginning, drew green dots on the landmarks to see whether this project would be possible/mediapipe would be suitable
├── filter_video_names.py           # estimating skill counts in the dataset
├── loader.py                       # filters the cohort, most significant filter being the presence or lack of bands/weights, which are invisible in pose space
└── single_landmarks_extractor.py   # my first extractor, running mediapipe on just one video to create its .npy file

```

## Landmark format

One `.npy` per video, shape `[T, 33, 7]` — frames × MediaPipe landmarks × `(x, y, z, visibility, presence, image_x, image_y)`. World landmarks are used, so coordinates are metric and relative to the hip midpoint. Frames with no detected pose are all-`NaN`.

## Dataset

2,193 videos collected; 1,891 in the default clean cohort after removing bands, added weight, and clips with excessive undetected frames. 

## Status

Landmark extraction and cohort loading are complete. Difficulty regression is in progress.
