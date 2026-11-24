import csv
import pandas as pd
import numpy as np



#First, I know that I need some sort of filtering ability. So I'll turn it into a parametrized function.
def select_cohort(modifiers_kept=None, max_undetected_frac=0.5, min_duration_sec=0.0):
    if modifiers_kept is None:
        modifiers_kept = {"clean"}
    df = pd.read_csv("_data/megalb.csv")

    df["undetected_frac"] = df["n_undetected"] / df["n_frames"] # The dataframe now also has a new column that will be preserved when I pass it on!

    filtered_df = df[
        (df["modifier"].isin(modifiers_kept)) & 
        (df["undetected_frac"] <= max_undetected_frac) & 
        (df["duration_sec"] >= min_duration_sec)
    ]

    print(f"Total filtered rows: {len(filtered_df)}")
    return filtered_df


# Man... that's it? That was quick
#it ended up being a little less quick (45 min more) but vastly more satisfying!

        

# Now for part 2. 

def load_sequence(row, min_gap_duration=0.1):
    seq = np.load(f"_data/landmarks/{row.uid}.npy")
    missing = np.isnan(seq).all(axis=(1,2))

    valid_indices = np.where(~missing)[0]
    if len(valid_indices) == 0:
        return "No detected frames!"
    first_detected_frame = valid_indices[0]
    last_detected_frame = valid_indices[-1]

    seq_kept = seq[first_detected_frame : last_detected_frame+1].copy()
    missing_kept = missing[first_detected_frame : last_detected_frame+1].copy()
    ratio = 0.2
    if missing_kept.mean() > ratio:
        return "Undetected ratio too high!"
    minlength = 1
    if len(seq_kept) / row.fps < minlength:
        return "Video duration too low!"

    # hooray now I can start the interpolation

    diffs = np.diff(missing_kept) # calculates the difference between consecutive values. so True->True or False->False => diffs[i] = 0, True->False => diffs[i] = -1, False->True => diffs[i] = 1
    boundary_indices = np.where(diffs)[0] #Since we start and end with detected frames, this is always even length, where the first index in a pair is the last detected frame, and the second index in a pair is last undetected frame. All nonzeros evaluate to True. 

    undetected_runs = []
    for start_idx, end_idx in zip(boundary_indices[::2], boundary_indices[1::2]):
        undetected_runs.append([start_idx+1, end_idx])

    short_udt_runs = []
    for run in undetected_runs:
        seconds = (run[1] - run[0] + 1) / row.fps
        if seconds < min_gap_duration:
            short_udt_runs.append(run)

    gap_indices = []
    for run in short_udt_runs:
        gap_indices.extend(np.arange(run[0], run[1]+1))
    gap_indices = np.array(gap_indices, dtype=int)


    num_landmarks, num_channels = seq_kept.shape[1], seq_kept.shape[2]
    known = ~missing_kept
    known_pos = np.where(known)[0]

    if len(gap_indices) > 0:
        for landmark_idx in range(num_landmarks):
            for value_idx in range(num_channels):
                series = seq_kept[:, landmark_idx, value_idx]

                filled = np.interp(gap_indices, known_pos, series[known])
                seq_kept[gap_indices, landmark_idx, value_idx] = filled

    missing_final = np.isnan(seq_kept).all(axis=(1,2))

    record = {
        "username": row.username,
        "uid": row.uid,
        "elo": row.elo,
        "rank": row.rank,
        "gender": row.gender,
        "n_frames": len(seq_kept),
        "n_undetected": np.sum(missing_final),
        "fps": row.fps,
        "width": row.width,
        "height": row.height,
        "modifier": row.modifier,
        "duration_sec": len(seq_kept) / row.fps,
        "seq": seq_kept
    }

    return record

def load_cohort(filtered_df):
    num_high_undetected_ratio = 0
    num_low_video_duration = 0

    num_undetected_before = 0
    num_undetected_after = 0

    num_frames_before = 0
    num_frames_after = 0

    cohort = []

    for row in filtered_df.itertuples():
        num_undetected_before += row.n_undetected
        num_frames_before += row.n_frames

        record = load_sequence(row)

        if record == "Undetected ratio too high!":
            num_high_undetected_ratio += 1
            continue
        if record == "Video duration too low!":
            num_low_video_duration += 1
            continue

        cohort.append(record)
        num_undetected_after += record["n_undetected"]
        num_frames_after += record["n_frames"]

    undetected_delta = num_undetected_before - num_undetected_after
    frames_delta = num_frames_before - num_frames_after
    print(f"Stats:")
    print(f"Undetected ratio too high: {num_high_undetected_ratio}")
    print(f"Video duration too low: {num_low_video_duration}")
    print(f"Good: {len(cohort)}")
    print(f"Change in undetected frame count: {undetected_delta}")
    print(f"Change in frame count: {frames_delta}")

    return cohort

if __name__ == "__main__":
    filtered_df = select_cohort()
    load_cohort(filtered_df)
