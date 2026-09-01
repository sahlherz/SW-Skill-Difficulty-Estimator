import json, csv



#OK the extra person stuff turned out to be useless, there was no extra person, the extra line in uuid_leaderboard.csv was the header line hahaha

#Find the extra person more efficiently
uidSet = set()
with open("push_users.jsonl", "r", encoding="utf-8") as file1:
    for line in file1:
        data = json.loads(line)
        uidSet.add(data["fields"]["uid"]["stringValue"])

with open("uuid_leaderboard.csv", "r", encoding="utf-8") as file2:
    reader = csv.DictReader(file2)
    for row in reader:
        myUid = row["uid"]
        if not myUid in uidSet:
            print(myUid)



#Find the extra person in uuid_leaderboard.csv
# with open("uuid_leaderboard.csv", "r", encoding="utf-8") as file2:
#     reader = csv.DictReader(file2)
#     for row in reader:
#         uid2 = row["uid"]
#         flag = False
#         with open("push_users.jsonl", "r", encoding="utf-8") as file1:
#             for line in file1:
#                 data = json.loads(line)
#                 uid = data["fields"]["uid"]["stringValue"]

#                 if uid2 == uid:
#                     flag = True
#                     break
        
#         if not flag:
#             print(uid)




#Check duplicate counts
#ok now I don't need this either, I need to find what uid is in uuid_leaderboard.csv and not in push_users.jsonl
# uid_counts = {}

# with open("push_users.jsonl", "r", encoding="utf-8") as file:
#     for line in file:
#         data = json.loads(line)
#         uid = data["fields"]["uid"]["stringValue"]
#         uid_counts[uid] = uid_counts.get(uid, 0) + 1

# duplicates = {uid for uid in uid_counts if uid_counts[uid] > 1}


#Delete duplicates
# This was the deletion version, now I restored the dupe checking version to see if it worked. Ok it did yay
# with open("push_users.jsonl", "r", encoding="utf-8") as file, open("correct_push_users.jsonl", "w", newline="", encoding="utf-8") as out:
#     for line in file:
#         data = json.loads(line)
#         uid = data["fields"]["uid"]["stringValue"]
#         uid_counts[uid] = uid_counts.get(uid, 0) + 1
#         if uid_counts[uid] <= 1:
#             out.write(line)



# print(duplicates)
# print(len(duplicates))