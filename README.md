# Python OpenSkill Rating System

A rating system implementation using the OpenSkill library to calculate player ratings for Scythe tournaments. The system processes game results, calculates ratings using the Plackett-Luce model, and syncs data with Supabase.

## Project Structure

```
python-openskill/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── values.csv                 # Main game data source (input)
├── players_rows.csv           # Player data (input/output)
├── events_rows.csv            # Event data (input)
│
├── data/                      # Data files
│   └── source/               # Original source CSV files (archived)
│
├── scripts/                   # Utility scripts
│   ├── graph.py              # Visualization utilities (optional)
│   └── archive/              # One-time conversion/cleanup scripts (archived)
│
├── docs/                      # Documentation
│   ├── SETUP.md              # Setup instructions
│   ├── WORKFLOW.md           # Workflow documentation
│   └── ...                   # Other documentation files
│
├── images/                    # Generated graph images
│
└── [Generated Output Files]   # Created by main.py:
    ├── games_rows.csv
    ├── game_participation_rows.csv
    ├── event_participation.csv
    ├── all_time_ratings.json
    ├── one_versus_one_ratings.json
    ├── three_and_four_player_ratings.json
    ├── rating_by_event.json
    └── supabase_rating.json
```

## Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables (create `.env` file):

   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   GENERATE_CSV=true
   ```

3. Ensure required CSV files are present:
   - `values.csv` - Main game data
   - `players_rows.csv` - Player information
   - `events_rows.csv` - Event information

## Usage

Run the main application:

```bash
python main.py
```

The script will:

1. Load existing data from Supabase (if configured)
2. Process all games from `values.csv`
3. Calculate ratings using OpenSkill's Plackett-Luce model
4. Update Supabase database (if configured)
5. Generate output CSV and JSON files

## Output Files

- **CSV Files**: `games_rows.csv`, `game_participation_rows.csv`, `event_participation.csv`, `players_rows.csv` (updated)
- **JSON Files**: Rating data in various formats for different rating categories

## Rating Categories

- **All Time**: Combined ratings across all events
- **One vs One**: Ratings for 1v1 events only
- **Three and Four Player**: Ratings for 3-4 player events only
- **By Event**: Ratings tracked per event

## Notes

- The `scripts/archive/` directory contains one-time conversion and cleanup scripts that were used during data migration
- Source CSV files are archived in `data/source/` for reference
- Documentation in `docs/` provides additional context about setup and workflows
