import csv

finalLeaderboardPath = "_data/Finals Pre-CV/final_leaderboard-ranksFixed.csv"
videoDataPath = "_data/Intermediates CV/video_data.csv"
modifierLabelPath = "_data/Intermediates CV/modifier_labels.csv" 
megalbPath = "_data/megalb.csv"


with open(finalLeaderboardPath, "r", encoding="utf-8") as lb, open(videoDataPath, "r", encoding="utf-8") as vd, open(modifierLabelPath, "r", encoding="utf-8") as ml, open(megalbPath, "w", newline="", encoding="utf-8") as mega:
    fields = ["username", "uid", "elo", "rank", "gender", "skill_name", "skill_description", "n_frames", "n_undetected", "fps", "width", "height", "modifier", "duration_sec"]

    writer = csv.DictWriter(mega, fieldnames=fields)
    writer.writeheader()
    lbread = csv.DictReader(lb)
    vdread = csv.DictReader(vd)
    mlread = csv.DictReader(ml)
    readers = [lbread, vdread, mlread]

    for rows in zip(*readers):
        lbrow = rows[0]
        vdrow = rows[1]
        mlrow = rows[2]

        dicto = {
            "username": lbrow["username"],
            "uid": lbrow["uid"],
            "elo": lbrow["elo"],
            "rank": lbrow["rank"],
            "gender": lbrow["gender"],
            "skill_name": lbrow["skill_name"],
            "skill_description": lbrow["skill_description"],
            "n_frames": vdrow["n_frames"],
            "n_undetected": vdrow["n_undetected"],
            "fps": vdrow["fps"],
            "width": vdrow["width"],
            "height": vdrow["height"],
            "modifier": mlrow["modifier"],
            "duration_sec": float(vdrow["n_frames"]) / float(vdrow["fps"]) # if anything has fps = 0 this breaks, default is 30 in that case tho
        }


        writer.writerow(dicto)

