import json, csv

with open("skill_docs_sorted.jsonl", "r", encoding="utf-8") as skill_names, open("temp_leaderboard.csv", "r", encoding="utf-8") as temp, open("final_leaderboard.csv", "w", newline="", encoding="utf-8") as outfile:
    reader = csv.DictReader(temp)
    fields = reader.fieldnames + ["skill_name", "skill_description"]
    writer = csv.DictWriter(outfile, fields)

    writer.writeheader()

    for row in reader:

        textLine = next(skill_names)
        if textLine.startswith("None"): #Handling the deleted videos
            row["skill_name"] = "No name"
            row["skill_description"] = "No description"

            writer.writerow(row)
            continue
        jsonLine = json.loads(textLine)
        skill_name = jsonLine["fields"]["name"]["stringValue"].replace("\n", " ")
        skill_description = jsonLine["fields"]["description"]["stringValue"].replace("\n", " ")

        if skill_description == "": #Handling user noninput of description
            skill_description = "Unlabeled"
        row["skill_name"] = skill_name
        row["skill_description"] = skill_description

        writer.writerow(row)
