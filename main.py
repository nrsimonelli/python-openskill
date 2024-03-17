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

ADJUSTED_MU = 1200
model = PlackettLuce(mu=ADJUSTED_MU, sigma=ADJUSTED_MU/3, beta=ADJUSTED_MU/6, tau=ADJUSTED_MU/300)
# model = PlackettLuce()

def calculate_ordinal(player_ratings):
    for player in player_ratings:
        player['ordinal'] = player.ordinal()

def initialize_rating(player_ratings, player):
    if player not in player_ratings:
        player_ratings[player] = model.rating(name=player)

def initialize_event_rating(player_ratings, player, event):
    if event not in player_ratings['by_event']:
        player_ratings['by_event'][event] = {}
    if player not in player_ratings['by_event'][event]:
      player_ratings['by_event'][event][player] = []

def update_rating(player_ratings, players, ranks):
    updated_rating = model.rate(teams=[[player_ratings[player]] for player in players], ranks=ranks)
    for i in range(len(players)):
        player_ratings[players[i]] = updated_rating[i][0]
    return updated_rating

def update_event_rating(player_ratings, players, updated_rating):
  # each player in players needs their updated_rating stored in player_ratings
  for i in range(len(players)):
    player_ratings[players[i]].append({"mu": updated_rating[i][0].mu, "sigma": updated_rating[i][0].sigma, "ordinal": updated_rating[i][0].ordinal()})
        

def main(): 
    # demo()   
    player_ratings = {
        'all_time': {},
        'one_versus_one': {},
        'three_and_four_player': {},
        'by_event': {}
    }   
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

            for player in players:
                if event in one_versus_one_event_list:
                    initialize_rating(player_ratings['one_versus_one'], player)
                if event in three_and_four_player_event_list:
                    initialize_rating(player_ratings['three_and_four_player'], player)
                
                initialize_rating(player_ratings['all_time'], player)
                initialize_event_rating(player_ratings, player, event)

            # Initialize player ratings if not already present
            
            # Update the ratings    
            if event in one_versus_one_event_list:
                update_rating(player_ratings['one_versus_one'], players, ranks)
            if event in three_and_four_player_event_list:
                update_rating(player_ratings['three_and_four_player'], players, ranks)

            updated_rating = update_rating(player_ratings['all_time'], players, ranks)
            update_event_rating(player_ratings['by_event'][event], players, updated_rating)

    for player in player_ratings['one_versus_one']:
        player_ratings['one_versus_one'][player].ordinal = player_ratings['one_versus_one'][player].ordinal()
    for player in player_ratings['three_and_four_player']:
        player_ratings['three_and_four_player'][player].ordinal = player_ratings['three_and_four_player'][player].ordinal()
    for player in player_ratings['all_time']:
        player_ratings['all_time'][player].ordinal = player_ratings['all_time'][player].ordinal()


    player_ratings['all_time'] = {k: v for k, v in sorted(player_ratings['all_time'].items(), key=lambda item: item[1].ordinal, reverse=True)}
    player_ratings['one_versus_one'] = {k: v for k, v in sorted(player_ratings['one_versus_one'].items(), key=lambda item: item[1].ordinal, reverse=True)}
    player_ratings['three_and_four_player'] = {k: v for k, v in sorted(player_ratings['three_and_four_player'].items(), key=lambda item: item[1].ordinal, reverse=True)}

    with open("player_rankings.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma, "ordinal": rating.ordinal } for player, rating in player_ratings['all_time'].items()}, indent=2))
    with open("one_versus_one.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma, "ordinal": rating.ordinal } for player, rating in player_ratings['one_versus_one'].items()}, indent=2))
    with open("three_and_four_player_rankings.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma, "ordinal": rating.ordinal } for player, rating in player_ratings['three_and_four_player'].items()}, indent=2))
    with open("by_event.json", "w") as outfile:
        outfile.write(json.dumps(player_ratings["by_event"], indent=2))

    # graphing demonstration
    tournament_num = 18
    graph.graph_tournament(player_ratings["by_event"][tournament_num], list(EVENT_KEY.keys())[tournament_num - 1])
    player = "morewhales"
    graph.graph_player(player_ratings["by_event"], player, "event") # or by game

if __name__ == "__main__":
    main()
