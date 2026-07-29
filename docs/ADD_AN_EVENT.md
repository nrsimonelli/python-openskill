# Adding an Event: Raw Sheets → Supabase

Canonical runbook for taking tournament/league spreadsheet exports all the way into the database. Lessons from Scenario SnowDown (event 30) and Season 8, 1v1 League (event 31) are baked in.

For day-to-day rating sync only, see the root [README](../README.md).

---

## Pipeline overview

```
Google Sheet / CSV export
        ↓
 data/source/<event>_….csv          (raw; keep for detail backfill)
        ↓
 Sanitize player names in place     (backup → remap → verify)
        ↓
 Convert → values.csv rows          (event, match, players, ranks)
        ↓
 Register event + new players       (events_rows.csv, players_rows.csv + Supabase)
        ↓
 uv run python main.py              (preflight → dry-run → --allow-new-games)
        ↓
 Optional detail backfill           (faction, mat, bid, score, rounds)
```

`main.py` only reads **root** `values.csv`, `players_rows.csv`, and `events_rows.csv`. It does **not** read `data/source/`. It writes rankings + ratings; it does **not** write faction/mat/bid/score (those are a second step).

---

## 0. Drop raw files in the right place

Put exports under:

```text
data/source/
```

Suggested names:

| Format              | Example                                |
| ------------------- | -------------------------------------- |
| 1v1 tiered league   | `season8_t1.csv` … `season8_t4.csv`    |
| 3p scenario / swiss | `Scenario_SnowDown_qualifiers_raw.csv` |
| 3p bracket          | `Scenario_SnowDown_bracket_raw.csv`    |
| Factory Rush–style  | `Factory Rush 2025.csv`                |

`main.py` never reads this folder. Raws are **local-only** (gitignored) — keep them for detail backfill scripts under `scripts/archive/`.

---

## 1. Sanitize player names

Mismatched usernames cause FK failures and duplicate “new” players.

### Steps

1. Collect every name from winner/loser (and combo/home/away columns if present).
2. Compare to `players_rows.csv` (exact → case-insensitive → alphanumeric-normalized → fuzzy).
3. Build a remap table; apply **in place** on the source CSVs (all name columns).
4. Keep a timestamped backup (`*.bak_YYYYMMDD_HHMMSS`) until verified.
5. Anything still unmatched is either a **new player** (add later) or needs a human alias decision.

### Recurring remaps (examples)

| Sheet                                    | Canonical                      |
| ---------------------------------------- | ------------------------------ |
| `dAyKiLLeR`                              | `dAy`                          |
| `dzordz`                                 | `Dzordz`                       |
| `lovabletifosi` / `Loveabletifosi`       | `loveable tofosi`              |
| `wavesamu` / `Wavesamu`                  | `WaveSamu`                     |
| `grishous`                               | `Grishous`                     |
| `fllyingmustang`                         | `Fllyingmustang`               |
| `Nullpoint`                              | `nullPoint`                    |
| `BigRedFred`                             | `Big Red Fred`                 |
| `DonKiKong` / `DonKikong/Grunz (He/Him)` | `DonKikong`                    |
| `GarretK#4892`                           | `GarretK`                      |
| `egamma`                                 | `egamma.net`                   |
| `Fuuuub`                                 | `FibausmHochhaus`              |
| `zJoueyTyke`                             | `JoeyTyke`                     |
| `Donov108`                               | `donov`                        |
| `Berzo`                                  | `Berzo` (new; not `berzo0718`) |

Strip Discord tags (`Name#1234` → decide canonical). Prefer existing DB usernames over inventing new ones.

### New players

Add to `players_rows.csv` **and** Supabase `players` **before** `main.py`:

- Next sequential `id`
- `username` exactly as it will appear in `values.csv`
- Default rating: `{"mu": 25, "sigma": 8.333333333333334, "ordinal": 1200}`

`main.py` does not create players.

---

## 2. Match naming conventions

Match names become `games.name` and must stay stable forever.

### 1v1 leagues (tiered)

| Sheet              | `values.csv` match |
| ------------------ | ------------------ |
| Tier 1, Match # 5  | `T1 G5`            |
| Tier 4, Match # 19 | `T4 G19`           |

Column is usually `Match #` or `Game #`. Winner → rank 1, loser → rank 2.

### 3p — one game per group per round (SnowDown-style)

Scenario/round → `R#`, group → letter (`1`→`A`):

| Example | Meaning                     |
| ------- | --------------------------- |
| `R1 A`  | Round/scenario 1, group 1   |
| `R8 M`  | Round 8, group 13           |
| `R9 A`  | Bracket continues numbering |

**Do not** use `R1 A1` unless the group actually plays multiple games (Autobidder / Winter Cup style).

### 3p — multi-game groups

| Example          | Meaning                         |
| ---------------- | ------------------------------- |
| `R1 A1`, `R1 A2` | Round 1, group A, games 1 and 2 |

### Factory Rush

| Example        | Meaning          |
| -------------- | ---------------- |
| `R1 T1`        | Round 1, table 1 |
| `FF 1`, `FF 2` | Finals games     |

### Finals

Almost never stay on `R# Letter`:

| Situation          | Name              |
| ------------------ | ----------------- |
| Single final       | `FF`              |
| Multi-game final   | `FF 1`, `FF 2`, … |
| Grouped multi-game | `FF A 1`, …       |

### Ranking rules for OpenSkill

| Format                              | Ranks                                                                                                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1v1                                 | Winner `1`, loser `2`                                                                                                                                                     |
| 3p/4p (this project's rated events) | Winner `1`; **all others `2`** (shared). Do not use rank 3 for “2nd vs 3rd” — recent events (Factory Rush, Autobidder, Winter Ban-Draft-Bid, SnowDown) all use `(1,2,2)`. |

---

## 3. Convert sheets → `values.csv`

Each row:

```csv
event,match,player_a,rank_a,player_b,rank_b,player_c,rank_c,player_d,rank_d
```

- `event` must **exactly** match `events_rows.csv` / Supabase `events.name`
- Append in **chronological** order relative to other events (ratings depend on full history)
- Prefer writing a preview under `temp/` (gitignored), spot-check, then append to `values.csv`

Helpers (optional; **local-only**, gitignored under `scripts/archive/`):

- `convert_sheet_to_values.py` / `convert_multiple_tiers.py` — 1v1 tiers
- `convert_autobidder_draft.py` — multi-game 3p groups
- `convert_factory_rush_to_values.py` — Factory Rush wide sheets

You can also convert by hand or with a one-off script — match naming conventions in this doc are the source of truth.

---

## 4. Register the event

`main.py` does **not** insert into `events`. Add the row to:

1. Root `events_rows.csv`
2. Supabase `events` (same `id` and `name`)

| Field                  | Notes                                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `id`                   | Next integer after max in CSV/DB                                                                          |
| `name`                 | Exact string used in `values.csv`                                                                         |
| `start_date`           | Event start                                                                                               |
| `bid` / `draft`        | Booleans                                                                                                  |
| `num_players_per_game` | `2`, `3`, or `4`                                                                                          |
| `rating_event`         | **`false`** → feeds **one_versus_one** ladder; **`true`** → **three_and_four_player** / main site ratings |

Examples:

- `Season 8, 1v1 League` → `rating_event=false`, `num_players_per_game=2`
- `Scenario SnowDown` → `rating_event=true`, `num_players_per_game=3`

---

## 5. Run `main.py` (ratings + games)

From repo root, with `.env` set (`SUPABASE_URL`, `SUPABASE_KEY`):

```bash
# Fast: compare values.csv keys to DB (no rating math)
uv run python main.py --preflight-only

# Full replay, no writes
uv run python main.py --dry-run

# Live — required when values.csv has new (event_id, match) keys
uv run python main.py --allow-new-games
```

### What a healthy new-event preflight looks like

- `N` unique games in `values.csv`
- `K` missing in Supabase (exactly the new event’s games)
- Sample keys show the new `event_id` and match names

### Important implementation notes

- **`games.id` has no DB default.** `main.py` assigns `id = max(existing)+1` on insert. Do not remove that.
- Windows runs can look “stuck” after loading data while thousands of per-row API updates run (10–15+ minutes is normal on a full replay). Wait for `Processing complete!`.
- If inserts fail with `null value in column "id"`, you are on an old `main.py` without the explicit-id fix.

### After a successful live run

- New rows in `games`, `game_participation` (ranking + `updated_rating` only)
- `event_participation` + `players.current_rating` updated
- Root exports refreshed when `GENERATE_CSV=true`

Faction / mat / bid / score are still **null** until step 6.

---

## 6. Detail backfill (faction, mat, bid, score, rounds)

Optional second step. Local scripts under `scripts/archive/` (gitignored) PATCH existing `game_participation` rows. Default is dry-run; `--execute` writes.

```bash
# Example: Season 8
uv run python scripts/archive/update_season8_game_participation.py
uv run python scripts/archive/update_season8_game_participation.py --execute

# Example: Scenario SnowDown
uv run python scripts/archive/update_scenario_snowdown_game_participation.py
uv run python scripts/archive/update_scenario_snowdown_game_participation.py --execute
```

Conventions:

- Enums **lowercased** (`Crimea` → `crimea`)
- Strip junk like `Togawa (w/ bonus)` → `togawa`
- Bid events: store `bid`; store **net** score in `final_score` (Season 7 / 8 / SnowDown)
- Match on `(game_id, player_id)` — games must already exist

Copy a recent `update_*_game_participation.py` (Season 8 / SnowDown) when adding a new event’s backfill.

---

## Checklist (copy per event)

- [ ] Raws in `data/source/`
- [ ] Names sanitized; backups verified
- [ ] New players inserted (CSV + Supabase)
- [ ] Event row inserted (CSV + Supabase) with correct `rating_event`
- [ ] Converted rows previewed; match names follow conventions
- [ ] Appended to `values.csv` in chronological order
- [ ] `--preflight-only` shows only expected missing keys
- [ ] `--dry-run` clean
- [ ] `main.py --allow-new-games` completes
- [ ] Detail backfill dry-run then `--execute`
- [ ] Spot-check Supabase (one game’s faction/mat/score + a known final)

---

## Worked references

| Event                | Id  | Notes                                                                                                        |
| -------------------- | --- | ------------------------------------------------------------------------------------------------------------ |
| Scenario SnowDown    | 30  | Qualifiers `R1 A`…`R8 M` + bracket `R9`…`R12` + `FF`; ranks `(1,2,2)`; see former SnowDown notes merged here |
| Season 8, 1v1 League | 31  | Four tiers `T1`–`T4`; `rating_event=false`; backfill script strips `(w/ bonus)`                              |

Supporting tooling (`data/source/`, `scripts/archive/`, ops/research notes) is **local-only** and gitignored — see the root README.
