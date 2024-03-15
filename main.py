import csv
from openskill.models import PlackettLuce

def main():
    model = PlackettLuce()
    
    player_ratings = {}
    
    # Read the CSV file
    with open('values.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Extract information from the row
            players = [row[f'player_{letter}'] for letter in 'abcd' if row[f'player_{letter}']]
            ranks = [int(row[f'rank_{letter}']) for letter in 'abcd' if row[f'rank_{letter}']]
            
            # Initialize player ratings if not already present
            for player in players:
                if player not in player_ratings:
                    player_ratings[player] = model.rating(name=player)

            # Update the ratings
            
            # need a list of player_ratings from players                    
            updated_rating = model.rate(teams=[[player_ratings[player]] for player in players], ranks=ranks)
            # print(updated_rating[0][0])
            # each player in players needs their updated_rating stored in player_ratings
            for i in range(len(players)):
                player_ratings[players[i]] = updated_rating[i][0]

    # Print the ratings
    print(player_ratings)

if __name__ == "__main__":
    main()
