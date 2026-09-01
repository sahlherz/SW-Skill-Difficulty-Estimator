import csv, json

with open("clean_leaderboard.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("leaderboard.csv", "w", newline='', encoding="utf-8") as f:
    fields = ["username", "uid", "elo", "rank", "gender"]

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(data)

