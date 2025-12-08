import csv

storage = {}
starts = [1, 9, 17, 25]


for i in range(len(starts)):
    storage[f"R{i + 1}"] = {}
    start = starts[i]
    with open("data.csv", "r", encoding="Latin1") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for count, row in enumerate(reader):
            if count > 1: # skip headers
                if row[0] not in storage[f"R{i + 1}"].keys():
            # use this bit if we want faction, mat, raw score, bid
                    # storage[f"R{i + 1}"][row[0]] = {}
                # if row[start + 1]: # this player actually played the game (had a faction)
                #     storage[f"R{i + 1}"][row[0]][row[start]] = [row[start+1], row[start+2], float(row[start+3]) if row[start+3] else None, int(row[start+5][1:]) if row[start+5] else None]
                    storage[f"R{i + 1}"][row[0]] = []
                if row[start+1]:
                    storage[f"R{i + 1}"][row[0]].append([row[start][0:row[start].rfind("#")], int(row[start+7])]) #grab number of points so we can calculate ranking (3 for first place, 1 for second and third, 0 for fourth)

# sanity checking
# with open("intermediate.json", "w") as f:
#     json.dump(storage, f)

csv_storage = []
tournament_name = "Casual Scythe Tournament March 2023"
points_map = {3: 1, 1: 2, 0: 3}

for round, games in storage.items():
    for game, player_data in games.items():
        if len(player_data) > 0:
            current_game = [tournament_name, f"{round}{game}"]
            for player in player_data:
                current_game.append(player[0]) # name
                current_game.append(points_map[player[1]])
            for _ in range(10 - len(current_game)):
                current_game.append('')
            csv_storage.append(current_game)

with open("intermediate.csv", "w", encoding="Latin1", newline="") as csvfile:
    writer = csv.writer(csvfile)
    for game in csv_storage:
        writer.writerow(game)
