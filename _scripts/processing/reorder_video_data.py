#Here we'll reorder _data/video_data.csv to have rank-order
import csv

finalLeaderboardPath = "_data/Finals Pre-CV/final_leaderboard.csv"
videoDataUnrotatedPath = "_data/Intermediates CV/video_data_with_unrotated.csv"
sortedVideoDataUnrotatedPath = "_data/Intermediates CV/sorted_video_data_with_unrotated.csv"

def get_uid(line):
    if line.startswith("uid,"):
        return line.strip().split("None for uid: ")[0]
    else:
        return line[0 : line.find(",")]

with open(finalLeaderboardPath, "r", encoding="utf-8") as truth:
    reader = csv.DictReader(truth)
    uid_list = [row["uid"] for row in reader]

with open(videoDataUnrotatedPath, "r", encoding="utf-8") as data:
    next(data)
    lines = data.readlines()

lines.sort(key = lambda line: uid_list.index(get_uid(line)))

with open(sortedVideoDataUnrotatedPath, "w", newline="", encoding="utf-8") as file:
    file.writelines("uid,status,failure_reason,n_frames,n_undetected,fps,width,height" + "\n")
    file.writelines(lines)

