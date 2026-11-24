import csv

skill = "planche"

with open("_data/megalb.csv", "r", encoding="utf-8") as data:
    reader = csv.DictReader(data)

    count = 0

    for row in reader:
        if skill in row["skill_name"].lower() or skill in row["skill_description"].lower():
            count += 1
    
print(count)