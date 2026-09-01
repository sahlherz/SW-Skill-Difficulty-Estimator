import json, csv

def get_uid(line):
    if line.startswith("None"):
        return line.strip().split("None for uid: ")[1]
    else:
        return json.loads(line)["fields"]["userId"]["stringValue"]

with open("temp_leaderboard.csv", "r", encoding="utf-8") as truth:
    reader = csv.DictReader(truth)
    uid_list = [row["uid"] for row in reader]

with open("skill_docs.jsonl", "r", encoding="utf-8") as skills:
    lines = skills.readlines()

lines.sort(key = lambda line: uid_list.index(get_uid(line)))

with open("skill_docs_sorted.jsonl", "w", newline="", encoding="utf-8") as file:
    file.writelines(lines)