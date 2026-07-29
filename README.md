# Python OpenSkill Rating System

OpenSkill (Plackett-Luce) ratings for Scythe tournaments: CSV game history → ratings → Supabase.

## Adding a new event

**Start here:** [docs/ADD_AN_EVENT.md](docs/ADD_AN_EVENT.md)

That guide covers raw sheets → name sanitization → `values.csv` → event/players → `main.py` → optional faction/mat/bid backfill.

## Day-to-day rating sync

```bash
uv run python main.py
```

From the **repository root**. With `.env` set:

1. Loads existing Supabase rows (when present)
2. Replays every game in `values.csv`
3. Upserts games, participations, and player ratings
4. Writes root CSV/JSON exports when `GENERATE_CSV=true`

### Safe flags

```bash
uv run python main.py --preflight-only   # compare values.csv keys to DB
uv run python main.py --dry-run          # full replay, no writes
uv run python main.py --allow-new-games  # live run when adding new matches
```

## Inputs (tracked)

| File               | Role                                                |
| ------------------ | --------------------------------------------------- |
| `values.csv`       | All game results (`event`, `match`, players, ranks) |
| `players_rows.csv` | Username → `id` (must match Supabase `players`)     |
| `events_rows.csv`  | Event name → `id`, `rating_event`, format flags     |

## Local-only (gitignored)

Keep on disk when working events; not required to clone or run ratings:

| Path                                            | Role                                             |
| ----------------------------------------------- | ------------------------------------------------ |
| `data/source/`                                  | Raw sheet exports (conversion + detail backfill) |
| `scripts/archive/`                              | Convert / sanitize / backfill helpers            |
| `docs/ops/`, `docs/research/`                   | Rare maintenance notes / SoS experiments         |
| Generated `*_ratings.json`, `games_rows.csv`, … | Exports from `main.py`                           |

## Outputs (`main.py`)

Local exports (gitignored; regenerated when `GENERATE_CSV=true`):

| File                                            | Role                                                  |
| ----------------------------------------------- | ----------------------------------------------------- |
| `games_rows.csv`                                | Games export                                          |
| `game_participation_rows.csv`                   | Participation export                                  |
| `event_participation.csv`                       | Event participation export                            |
| `*_ratings.json`                                | `all_time`, `one_versus_one`, `three_and_four_player` |
| `rating_by_event.json` / `supabase_rating.json` | Per-event history / payloads                          |

`players_rows.csv` is also rewritten with `current_rating` (still tracked as an input of record).

## Layout

```
python-openskill/
├── main.py                 # CSV → ratings → Supabase + exports
├── pyproject.toml / uv.lock
├── values.csv / players_rows.csv / events_rows.csv
├── docs/ADD_AN_EVENT.md    # Canonical “add an event” runbook
├── data/source/            # Local: raw sheets (gitignored)
├── scripts/archive/        # Local: convert / backfill tools (gitignored)
└── [generated CSV/JSON]    # Local exports (gitignored)
```

## Setup

1. Install [uv](https://docs.astral.sh/uv/) (`uv --version`).
2. From repo root: `uv sync`
3. `.env`:

   ```
   SUPABASE_URL=…
   SUPABASE_KEY=…          # service role for writes
   GENERATE_CSV=true
   ```

4. Ensure the three root input CSVs exist.

Python **3.11+**. Use `uv add` / `uv remove` for deps (`uv.lock` is the lockfile).

## Rating categories

Driven by `events_rows.csv` → `rating_event`:

- **`false`** → one-versus-one ladder (1v1 leagues)
- **`true`** → three-and-four-player / main site ratings
- **All time** — all events; **by event** — `rating_by_event.json` / Supabase event participation
