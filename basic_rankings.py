import csv
import json

rankings = json.load(open("three_and_four_player_ratings.json"))

with open("basic_rankings/3_and_4_player_basic_rankings.csv", "w", newline="") as outfile:
  writer = csv.writer(outfile)
  writer.writerow(["Ranking", "Player", "Elo"])

  for i, key in enumerate(rankings):
    writer.writerow([f"{i + 1}", key, f"{round(rankings[key]["ordinal"], 2)}"])
