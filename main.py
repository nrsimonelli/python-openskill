import csv
import json
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from openskill.models import PlackettLuce
from supabase import create_client, Client
# import graph

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client (will be None if credentials not provided)
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")
        print("Continuing without Supabase integration. CSV files will still be generated.")

# Grab the event name and id from the events_rows.csv file
EVENT_KEY = {}
RATED_EVENT = {}

# list of player ids from players_rows.csv
PLAYER_KEY = {}
with open('players_rows.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        PLAYER_KEY[row['username']] = int(row['id'])

with open('events_rows.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        EVENT_KEY[row['name']] = int(row['id'])
        RATED_EVENT[int(row['id'])] = row['rating_event']

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

def initialize_supabase_rating(rating_for_supabase, current_rating, player, event):
    if event not in rating_for_supabase:
        rating_for_supabase[event] = {}
    if player not in rating_for_supabase[event]:
        if player not in current_rating:
            rating_for_supabase[event][player] = [{"games_won": 0}, {"mu": 25, "sigma": 8.333333333333334, "ordinal": 1200}]
        else:
            rating_for_supabase[event][player] = [{"games_won": 0}, {"mu": current_rating[player].mu, "sigma": current_rating[player].sigma, "ordinal": current_rating[player].ordinal(z=3) * 24 + 1200}]
    

def update_supabase_rating(rating_for_supabase, players, ranks, should_update, previous_ratings):
    for i in range(len(players)):
        player = players[i]
        if ranks[i] == 1:
            rating_for_supabase[player][0]['games_won'] += 1
        if should_update:
            if player in previous_ratings:
                rating_for_supabase[player][1] = {"mu": previous_ratings[player].mu, "sigma": previous_ratings[player].sigma, "ordinal": previous_ratings[player].ordinal(z=3) * 24 + 1200}
            else:
                rating_for_supabase[player].append({"mu": 25, "sigma": 8.333333333333334, "ordinal": 1200})

# Supabase data loading functions
def load_existing_games():
    """Load existing games from Supabase, returning a set of (event_id, name) tuples"""
    if not supabase:
        return set()
    
    try:
        response = supabase.table('games').select('event, name').execute()
        return {(row['event'], row['name']) for row in response.data}
    except Exception as e:
        print(f"Warning: Could not load existing games from Supabase: {e}")
        return set()

def load_existing_game_participation():
    """Load existing game_participation records, returning a set of (game_id, player_id) tuples
    
    If duplicates exist, all are included in the set (duplicates will be handled by upsert logic).
    """
    if not supabase:
        return set()
    
    try:
        response = supabase.table('game_participation').select('game, player').execute()
        # Use a set to automatically deduplicate
        return {(row['game'], row['player']) for row in response.data}
    except Exception as e:
        print(f"Warning: Could not load existing game_participation from Supabase: {e}")
        return set()

def load_existing_event_participation():
    """Load existing event_participation records, returning a dict of {(event_id, player_id): data}"""
    if not supabase:
        return {}
    
    try:
        response = supabase.table('event_participation').select('event, player, games_won, updated_rating').execute()
        return {(row['event'], row['player']): row for row in response.data}
    except Exception as e:
        print(f"Warning: Could not load existing event_participation from Supabase: {e}")
        return {}

def get_game_id_from_supabase(event_id, game_name):
    """Get the database ID for a game given event_id and name"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('games').select('id').eq('event', event_id).eq('name', game_name).limit(1).execute()
        if response.data:
            return response.data[0]['id']
    except Exception as e:
        print(f"Warning: Could not get game ID from Supabase: {e}")
    return None

def load_existing_game_ids():
    """Load existing games with their IDs from Supabase, returning a dict of {(event_id, name): id}
    
    If duplicates exist, keeps the one with the lowest ID (oldest record).
    """
    if not supabase:
        return {}
    
    try:
        response = supabase.table('games').select('id, event, name').order('id', desc=False).execute()
        game_ids = {}
        for row in response.data:
            key = (row['event'], row['name'])
            # Only keep the first occurrence (lowest ID) if duplicates exist
            if key not in game_ids:
                game_ids[key] = row['id']
        return game_ids
    except Exception as e:
        print(f"Warning: Could not load existing game IDs from Supabase: {e}")
        return {}

# Supabase upsert functions
def upsert_game(event_id, game_name, existing_game_ids):
    """Upsert a game and return its database ID"""
    if not supabase:
        return None
    
    game_key = (event_id, game_name)
    
    # Check if game already exists
    if game_key in existing_game_ids:
        # Game exists, return its ID
        return existing_game_ids[game_key]
    else:
        # Insert new game
        try:
            response = supabase.table('games').insert({
                'event': event_id,
                'name': game_name
            }).execute()
            if response.data:
                game_id = response.data[0]['id']
                # Cache the new game ID
                existing_game_ids[game_key] = game_id
                return game_id
        except Exception as e:
            print(f"Error inserting game {game_name} for event {event_id}: {e}")
    return None

def upsert_game_participation(game_id, player_id, ranking, updated_rating, existing_participation):
    """Upsert a game_participation record
    
    If duplicates exist, updates all matching records to ensure consistency.
    """
    if not supabase or not game_id:
        return
    
    participation_key = (game_id, player_id)
    
    participation_data = {
        'game': game_id,
        'player': player_id,
        'ranking': ranking,
        'updated_rating': updated_rating  # Pass dict directly for JSONB column
    }
    
    try:
        if participation_key in existing_participation:
            # Update all existing records (handles duplicates by updating all)
            supabase.table('game_participation').update(participation_data).eq('game', game_id).eq('player', player_id).execute()
        else:
            # Insert new record
            supabase.table('game_participation').insert(participation_data).execute()
    except Exception as e:
        print(f"Error upserting game_participation for game {game_id}, player {player_id}: {e}")

def upsert_event_participation(event_id, player_id, games_won, updated_rating, existing_participation):
    """Upsert an event_participation record"""
    if not supabase:
        return
    
    participation_key = (event_id, player_id)
    
    participation_data = {
        'event': event_id,
        'player': player_id,
        'games_won': games_won,
        'updated_rating': updated_rating  # Pass dict directly for JSONB column
    }
    
    try:
        if participation_key in existing_participation:
            # Update existing record
            supabase.table('event_participation').update(participation_data).eq('event', event_id).eq('player', player_id).execute()
        else:
            # Insert new record
            supabase.table('event_participation').insert(participation_data).execute()
    except Exception as e:
        print(f"Error upserting event_participation for event {event_id}, player {player_id}: {e}")

def update_player_rating(player_id, current_rating):
    """Update a player's current_rating"""
    if not supabase:
        return
    
    # Pass dict directly for JSONB column - Supabase client handles serialization
    try:
        supabase.table('players').update({'current_rating': current_rating}).eq('id', player_id).execute()
    except Exception as e:
        print(f"Error updating player {player_id} rating: {e}")

def main():   
    player_ratings = {
        'all_time': {},
        'one_versus_one': {},
        'three_and_four_player': {},
    }  

    rating_by_event = dict()

    rating_for_supabase = dict()

    all_events = list(EVENT_KEY.values())
    one_versus_one_event_list = [key for key, value in RATED_EVENT.items() if value == 'false']
    three_and_four_player_event_list = list(set(all_events) - set(one_versus_one_event_list))  

    # Load existing data from Supabase for incremental updates
    print("Loading existing data from Supabase...")
    print("  Loading games...", end='', flush=True)
    existing_games = load_existing_games()
    print(f" OK ({len(existing_games)} games)")
    
    print("  Loading game IDs...", end='', flush=True)
    existing_game_ids = load_existing_game_ids()  # Maps (event_id, name) -> id
    print(f" OK ({len(existing_game_ids)} game IDs)")
    
    print("  Loading game participation...", end='', flush=True)
    existing_game_participation = load_existing_game_participation()
    print(f" OK ({len(existing_game_participation)} participations)")
    
    print("  Loading event participation...", end='', flush=True)
    existing_event_participation = load_existing_event_participation()
    print(f" OK ({len(existing_event_participation)} participations)")
    
    print("Only new/changed records will be inserted or updated.")

    # Optional: Generate CSV files for backup/reference (regenerated from values.csv each run)
    generate_csv = os.getenv('GENERATE_CSV', 'true').lower() == 'true'
    
    # Prepare CSV file handles for batch writing
    games_csv_rows = []
    game_participation_csv_rows = []

    # Read the CSV file and process all games (for accurate rating calculations)
    # Note: We process ALL games to ensure ratings are calculated correctly,
    # but only new/changed records will be upserted to Supabase
    print("Processing games from values.csv...")
    
    # Count total rows first for progress tracking
    with open('values.csv', newline='') as csvfile:
        total_rows = sum(1 for _ in csv.DictReader(csvfile)) - 1  # Subtract header
    
    print(f"Total games to process: {total_rows}")
    print("Progress will be shown every 100 games...")
    
    game_counter = 0  # Track sequential game number for CSV (independent of database IDs)
    new_games_count = 0
    updated_games_count = 0
    games_processed_this_run = set()  # Track games we've seen in this CSV run
    
    with open('values.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)     

        for row in reader:
            game_counter += 1
            # Extract information from the row
            players = [row[f'player_{letter}'] for letter in 'abcd' if row[f'player_{letter}']]
            ranks = [int(row[f'rank_{letter}']) for letter in 'abcd' if row[f'rank_{letter}']]
            event = int(EVENT_KEY[row['event']])
            game_name = row['match']
            game_key = (event, game_name)

            # Check if this game existed in Supabase BEFORE this run started
            game_existed_before = game_key in existing_game_ids
            
            # Upsert game to Supabase and get/store its ID
            game_id = upsert_game(event, game_name, existing_game_ids)
            if game_id:
                # Update existing_games set to track processed games
                existing_games.add(game_key)
                
                # Count correctly: only count as "existing" if it was in Supabase before this run
                # If we've seen it in this CSV already, it's a duplicate name issue (shouldn't happen with unique names)
                if game_existed_before:
                    updated_games_count += 1
                elif game_key not in games_processed_this_run:
                    new_games_count += 1
                # If game_key is in games_processed_this_run, it's a duplicate name - don't count it
                
                games_processed_this_run.add(game_key)

            # Collect CSV rows for batch writing
            if generate_csv:
                games_csv_rows.append([event, game_name])

            # Initialize ratings for players if they don't exist in the given event category
            for player in players:
                if event in one_versus_one_event_list:
                    initialize_rating(player_ratings['one_versus_one'], player)
                if event in three_and_four_player_event_list:
                    initialize_rating(player_ratings['three_and_four_player'], player)

                initialize_rating(player_ratings['all_time'], player)
                initialize_event_rating(rating_by_event, player, event)
                
                initialize_supabase_rating(rating_for_supabase, player_ratings['three_and_four_player'], player, event)
            
            # Update the ratings    
            if event in one_versus_one_event_list:
                update_rating(player_ratings['one_versus_one'], players, ranks)

            if event in three_and_four_player_event_list:
                update_rating(player_ratings['three_and_four_player'], players, ranks)

            # Upsert game participation to Supabase and write to CSV
            for i, player in enumerate(players):
                player_id = PLAYER_KEY[player]
                ranking = ranks[i]
                
                if player in player_ratings['three_and_four_player']:
                    updated_rating = {
                        "mu": player_ratings['three_and_four_player'][player].mu,
                        "sigma": player_ratings['three_and_four_player'][player].sigma,
                        "ordinal": player_ratings['three_and_four_player'][player].ordinal(z=3) * 24 + 1200
                    }
                else:
                    updated_rating = {"mu": 25, "sigma": 8.333333333333334, "ordinal": 1200}
                
                # Upsert to Supabase if game_id is available
                if game_id:
                    upsert_game_participation(game_id, player_id, ranking, updated_rating, existing_game_participation)
                    # Update existing_game_participation set
                    existing_game_participation.add((game_id, player_id))
                
                # Collect CSV rows for batch writing
                if generate_csv:
                    csv_game_id = game_id if game_id else game_counter
                    game_participation_csv_rows.append([csv_game_id, player_id, ranking, json.dumps(updated_rating)])

            updated_rating = update_rating(player_ratings['all_time'], players, ranks)
            update_event_rating(rating_by_event[event], players, updated_rating)

            # boolean variable for whether the event is a one versus one event
            should_update = event in three_and_four_player_event_list
            update_supabase_rating(rating_for_supabase[event], players, ranks, should_update, player_ratings['three_and_four_player'])
            
            # Progress indicator every 100 games
            if game_counter % 100 == 0:
                print(f"  Processed {game_counter}/{total_rows} games... ({(game_counter/total_rows*100):.1f}%)")
    
    # Write CSV files in batch (write mode to regenerate from values.csv, not append)
    if generate_csv and games_csv_rows:
        print(f"\nWriting {len(games_csv_rows)} game records to CSV...")
        with open('games_rows.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['event', 'name'])  # Write header
            writer.writerows(games_csv_rows)
    
    if generate_csv and game_participation_csv_rows:
        print(f"Writing {len(game_participation_csv_rows)} game participation records to CSV...")
        with open('game_participation_rows.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['game', 'player', 'ranking', 'updated_rating'])  # Write header
            writer.writerows(game_participation_csv_rows)
    
    # Calculate final ordinal ratings
    for category in player_ratings:
        for player in player_ratings[category]:
            player_ratings[category][player].ordinal = player_ratings[category][player].ordinal(z=3) * 24 + 1200

        player_ratings[category] = {k: v for k, v in sorted(player_ratings[category].items(), key=lambda item: item[1].ordinal, reverse=True)}

        # Write JSON files for reference
        with open(f"{category}_ratings.json", "w") as outfile:
                outfile.write(json.dumps({player: {"mu": rating.mu, "sigma": rating.sigma, "ordinal": rating.ordinal } for player, rating in player_ratings[category].items()}, indent=2))

    with open(f"rating_by_event.json", "w") as outfile:
        outfile.write(json.dumps(rating_by_event, indent=2))

    with open(f"supabase_rating.json", "w") as outfile:
        outfile.write(json.dumps(rating_for_supabase, indent=2))

    # Upsert event_participation to Supabase
    if supabase:
        print(f"\nUpserting event participation to Supabase...")
        print(f"Summary: {new_games_count} new games inserted, {updated_games_count} existing games recognized")
        total_event_participations = sum(len(players) for players in rating_for_supabase.values())
        print(f"Updating {total_event_participations} event participation records...")
        event_counter = 0
    else:
        print("\nSkipping Supabase updates (no credentials configured)")
    for event in rating_for_supabase:
        for player in rating_for_supabase[event]:
            player_id = PLAYER_KEY[player]
            games_won = rating_for_supabase[event][player][0]['games_won']
            updated_rating = rating_for_supabase[event][player][1]
            upsert_event_participation(event, player_id, games_won, updated_rating, existing_event_participation)
            # Update existing_event_participation to track what we've processed
            existing_event_participation[(event, player_id)] = {
                'event': event,
                'player': player_id,
                'games_won': games_won,
                'updated_rating': updated_rating
            }
            if supabase:
                event_counter += 1
                if event_counter % 50 == 0:
                    print(f"  Updated {event_counter}/{total_event_participations} event participations...")

    # Write event_participation CSV if enabled
    if generate_csv:
        with open('event_participation.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['event', 'player', 'games_won', 'updated_rating'])
            for event in rating_for_supabase:
                for player in rating_for_supabase[event]:
                    writer.writerow([event, PLAYER_KEY[player], rating_for_supabase[event][player][0]['games_won'], json.dumps(rating_for_supabase[event][player][1])])

    # Update player ratings in Supabase and CSV
    print("\nUpdating player ratings...")
    with open('players_rows.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        if len(rows) == 0:
            return
        
        # Keep only the first 3 columns (id, created_at, username) and remove all others
        # This handles cases where there are duplicate current_rating columns
        for i in range(len(rows)):
            rows[i] = rows[i][:3]  # Keep only first 3 columns
        
        # Add current_rating header
        rows[0].append('current_rating')
        
        # Add current_rating for each player and update Supabase
        total_players = len(rows) - 1  # Exclude header
        print(f"Updating {total_players} player ratings...")
        for i in range(1, len(rows)):
            player_id = int(rows[i][0])
            player_name = rows[i][2]
            if player_name in player_ratings['three_and_four_player']:
                r = player_ratings['three_and_four_player'][player_name]
                rating_value = { "mu": r.mu, "sigma": r.sigma, "ordinal": r.ordinal}
            else:
                # Player only participated in 1v1 events, use default rating
                rating_value = {"mu": 25, "sigma": 8.333333333333334, "ordinal": 1200}
            
            rows[i].append(json.dumps(rating_value))
            
            # Update Supabase
            update_player_rating(player_id, rating_value)
            
            if (i - 1) % 50 == 0:
                print(f"  Updated {i - 1}/{total_players} player ratings...")
        
        # Write updated CSV
        with open('players_rows.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
    
    print(f"\nProcessing complete!")
    print(f"  - Processed {game_counter} games")
    print(f"  - Inserted {new_games_count} new games")
    print(f"  - Recognized {updated_games_count} existing games")

    # graphing demonstrations
    # tournament_num = 18
    # graph.graph_tournament(rating_by_event[tournament_num], list(EVENT_KEY.keys())[tournament_num - 1])
    # graph.clear()
    # player = "JoyDivision"
    # graph.graph_player(rating_by_event, player, "event") # or by game
    # graph.clear()

    # player_group = ["FOMOF", "JoyDivision", "Mr. Der", "Nevic", "nobadinohz"]
    # graph.graph_players(rating_by_event, player_group, "event")
    # graph.clear()

if __name__ == "__main__":
    main()
