import csv
import json
from openskill.models import PlackettLuce
import graph

EVENT_KEY = {
    'First DE Tournament': 1,
    'Second DE Tournament': 2,
    'Draft Kings, January 2021': 3,
    'Draft Swiss, March': 4,
    '1v1, March 2021': 5,
    'Classic, May 2021': 6,
    '1v1, July 2021': 7,
    'Winter Cup 2021': 8,
    'February 2022 Draft': 9,
    'Season 1, 1v1 League': 10,
    'May 2022 Mashup': 11,
    'Season 2, 1v1 League': 12,
    'September Scenarios 2022': 13,
    'Factory Rush 2022': 14,
    '2023 New Years Tournament': 15,
    'Season 3, 1v1 League': 16,
    'Factory Rush 2023': 17,
    '2024 Scythe Ice Bowl (Main)': 18,
    '2024 Scythe Ice Bowl (Novice)': 19,
    'Season 4, 1v1 League': 20,
}

model = PlackettLuce()

def initialize_rating(player_ratings, player):
    if player not in player_ratings:
        player_ratings[player] = model.rating(name=player)

def initialize_event_rating(rating_by_event, player, event):
    if event not in rating_by_event:
        rating_by_event[event] = {}
    if player not in rating_by_event[event]:
      rating_by_event[event][player] = []

def update_rating(player_ratings, players, ranks):
    updated_rating = model.rate(teams=[[player_ratings[player]] for player in players], ranks=ranks)
    for i in range(len(players)):
        player_ratings[players[i]] = updated_rating[i][0]
    return updated_rating

def update_event_rating(event_rating, players, updated_rating):
  # each player in players needs their updated_rating stored in player_ratings
  for i in range(len(players)):
    event_rating[players[i]].append({"mu": updated_rating[i][0].mu, "sigma": updated_rating[i][0].sigma, "ordinal": updated_rating[i][0].ordinal(z=3) * 24 + 1200})
        

def main():   
    player_ratings = {
        'all_time': {},
        'one_versus_one': {},
        'three_and_four_player': {},
    }  

    rating_by_event = dict()

    all_events = list(EVENT_KEY.values())
    one_versus_one_event_list = [5, 7, 10, 12, 16, 20]
    three_and_four_player_event_list = list(set(all_events) - set(one_versus_one_event_list))  

    # Read the CSV file
    with open('values.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)     

        for row in reader:
            # Extract information from the row
            players = [row[f'player_{letter}'] for letter in 'abcd' if row[f'player_{letter}']]
            ranks = [int(row[f'rank_{letter}']) for letter in 'abcd' if row[f'rank_{letter}']]
            event = int(EVENT_KEY[row['event']])

            # Initialize ratings for players if they don't exist in the given event category
            for player in players:
                if event in one_versus_one_event_list:
                    initialize_rating(player_ratings['one_versus_one'], player)
                if event in three_and_four_player_event_list:
                    initialize_rating(player_ratings['three_and_four_player'], player)

                initialize_rating(player_ratings['all_time'], player)
                initialize_event_rating(rating_by_event, player, event)
            
            # Update the ratings    
            if event in one_versus_one_event_list:
                update_rating(player_ratings['one_versus_one'], players, ranks)

            if event in three_and_four_player_event_list:
                update_rating(player_ratings['three_and_four_player'], players, ranks)

            updated_rating = update_rating(player_ratings['all_time'], players, ranks)
            update_event_rating(rating_by_event[event], players, updated_rating)

    
    for category in player_ratings:
        for player in player_ratings[category]:
            player_ratings[category][player].ordinal = player_ratings[category][player].ordinal(z=3) * 24 + 1200

        player_ratings[category] = {k: v for k, v in sorted(player_ratings[category].items(), key=lambda item: item[1].ordinal, reverse=True)}

        with open(f"{category}_ratings.json", "w") as outfile:
                outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma, "ordinal": rating.ordinal } for player, rating in player_ratings[category].items()}, indent=2))

    with open(f"rating_by_event.json", "w") as outfile:
        outfile.write(json.dumps(rating_by_event, indent=2))

    # graphing demonstrations
    tournament_num = 18
    graph.graph_tournament(rating_by_event[tournament_num], list(EVENT_KEY.keys())[tournament_num - 1])
    graph.clear()
    player = "JoyDivision"
    graph.graph_player(rating_by_event, player, "event") # or by game
    graph.clear()

    player_group = ["FOMOF", "JoyDivision", "Mr. Der", "Nevic", "nobadinohz"]
    graph.graph_players(rating_by_event, player_group, "event")
    graph.clear()

if __name__ == "__main__":
    main()
