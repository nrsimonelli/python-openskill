import csv
import json
from openskill.models import PlackettLuce

def main():
    # adjusting the default values to match typical DE ratings
    adjusted_mu = 1200
    model = PlackettLuce(mu=adjusted_mu, sigma=adjusted_mu/3, beta=adjusted_mu/6, tau=adjusted_mu/300)
    # model = PlackettLuce()
    
    player_ratings = {
        'all_time': {},
        'one_versus_one': {},
        'three_and_four_player': {},
        'by_event': {}
    }

    # key value pairs of all event names and keys from values.csv
    event_key = {
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

    all_events = list(event_key.values())
    one_versus_one_event_list = [5, 7, 10, 12, 16, 20]
    three_and_four_player_event_list = list(set(all_events) - set(one_versus_one_event_list))

    # Read the CSV file
    with open('values.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Extract information from the row
            players = [row[f'player_{letter}'] for letter in 'abcd' if row[f'player_{letter}']]
            ranks = [int(row[f'rank_{letter}']) for letter in 'abcd' if row[f'rank_{letter}']]
            event = int(event_key[row['event']])

            if event not in player_ratings['by_event']:
                player_ratings['by_event'][event] = {}

            if event in one_versus_one_event_list:
                # Initialize player ratings if not already present
                for player in players:
                    if player not in player_ratings['one_versus_one']:
                        player_ratings['one_versus_one'][player] = model.rating(name=player)
                            
                updated_one_versus_one_rating = model.rate(teams=[[player_ratings['one_versus_one'][player]] for player in players], ranks=ranks)

                for i in range(len(players)):
                    player_ratings['one_versus_one'][players[i]] = updated_one_versus_one_rating[i][0]

            if event in three_and_four_player_event_list:
                # Initialize player ratings if not already present
                for player in players:
                    if player not in player_ratings['three_and_four_player']:
                        player_ratings['three_and_four_player'][player] = model.rating(name=player)
                            
                updated_three_and_four_player_rating = model.rate(teams=[[player_ratings['three_and_four_player'][player]] for player in players], ranks=ranks)

                for i in range(len(players)):
                    player_ratings['three_and_four_player'][players[i]] = updated_three_and_four_player_rating[i][0]
            
            # Initialize player ratings if not already present
            for player in players:
                if player not in player_ratings['all_time']:
                    player_ratings['all_time'][player] = model.rating(name=player)
                
                if player not in player_ratings['by_event'][event]:
                  player_ratings['by_event'][event] = [model.rating(name=player)]
                else:
                  player_ratings['by_event'][event].append(model.rating(name=player))
            
            # Update the ratings                
            updated_rating = model.rate(teams=[[player_ratings['all_time'][player]] for player in players], ranks=ranks)


            # each player in players needs their updated_rating stored in player_ratings
            for i in range(len(players)):
                player_ratings['all_time'][players[i]] = updated_rating[i][0]

    # Print the ratings in a nice format
    # sort the player_ratings by mu
    player_ratings['all_time'] = {k: v for k, v in sorted(player_ratings['all_time'].items(), key=lambda item: item[1].mu, reverse=True)}
    player_ratings['one_versus_one'] = {k: v for k, v in sorted(player_ratings['one_versus_one'].items(), key=lambda item: item[1].mu, reverse=True)}
    player_ratings['three_and_four_player'] = {k: v for k, v in sorted(player_ratings['three_and_four_player'].items(), key=lambda item: item[1].mu, reverse=True)}
    print(player_ratings['by_event'])

    with open("player_rankings.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma} for player, rating in player_ratings['all_time'].items()}, indent=2))
    with open("one_versus_one.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma} for player, rating in player_ratings['one_versus_one'].items()}, indent=2))
    with open("three_and_four_player_rankings.json", "w") as outfile:
        outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma} for player, rating in player_ratings['three_and_four_player'].items()}, indent=2))


if __name__ == "__main__":
    main()
