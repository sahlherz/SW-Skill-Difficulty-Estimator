import csv

search_terms = ["assist", "band", "resist", "loop"]
path = "_data/megalb.csv"

with open(path, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    count = 0
    for row in reader:
        combined = (row["skill_name"] + " " + row["skill_description"]).lower()

        if any(term in combined for term in search_terms):
            count += 1

print(count)


    
