import csv
import json

storage = {}
starts = [3, 10, 17]


for i in range(len(starts)):
    start = starts[i]
    with open("casual_data.csv", "r", encoding="Latin1") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for count, row in enumerate(reader):
            if count > 2: # skip headers
                if f"R{row[0]}" not in storage.keys():
                    storage[f"R{row[0]}"] = {}
                if f"{row[1]}{i + 1}" not in storage[f"R{row[0]}"].keys():
                    storage[f"R{row[0]}"][f"{row[1]}{i + 1}"] = [] # in the other version it's {}
                if len((row[start])) > 0:
                    # this for noting down the other stuff we care about in game_participation
                    # storage[f"R{row[0]}"][f"{row[1]}{i + 1}"][row[2]] = [row[start], row[start + 1], float(row[start+2]), int(row[start+4])]
                    storage[f"R{row[0]}"][f"{row[1]}{i + 1}"].append([row[2], 1 if row[start + 6] == "yes" else 2])

# putting them back in game order
for key in storage:
    storage[key] = dict(sorted(storage[key].items()))

with open("intermediate.json", "w") as f:
    json.dump(storage, f)

csv_storage = []
tournament_name = "2024 Spring Autobidder Draft Tournament (Casual Bracket)"

for round, games in storage.items():
    for game, player_data in games.items():
        if len(player_data) > 0:
            current_game = [tournament_name, f"{round} {game}"]
            for player in player_data:
                current_game.extend(player)
            for _ in range(10 - len(current_game)):
                current_game.append('')
            csv_storage.append(current_game)

with open("intermediate.csv", "w", encoding="Latin1", newline="") as csvfile:
    writer = csv.writer(csvfile)
    for game in csv_storage:
        writer.writerow(game)
