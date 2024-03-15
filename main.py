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

            print(f"Players: {players}, Ranks: {ranks}")
            
    #         # Initialize player ratings if not already present
    #         for player in players:
    #             if player not in player_ratings:
    #                 player_ratings[player] = model.rating(name=player)

if __name__ == "__main__":
    main()
