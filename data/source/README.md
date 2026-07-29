# Raw source sheets (local only)

Tournament/league CSV exports live here. **Gitignored** — keep on disk for conversion and detail backfill; not required to clone or run `main.py`.

`main.py` does not read this folder.

| Kind             | Typical names                          |
| ---------------- | -------------------------------------- |
| 1v1 leagues      | `season8_t1.csv` … `season8_t4.csv`    |
| Scenario / swiss | `Scenario_SnowDown_qualifiers_raw.csv` |
| Bracket          | `Scenario_SnowDown_bracket_raw.csv`    |
| Factory Rush     | `Factory Rush 2025.csv`                |

`sss_raw.csv` / `sss_updated.csv` are Strength-of-Schedule worksheets, not the player DB.

Pipeline: [docs/ADD_AN_EVENT.md](../../docs/ADD_AN_EVENT.md).
