# resonant-collectibles
Collectibles tracker for Control Resonant.

- `data/collectibles.json`: the database. 67 trophy collectibles across 7 zones and 8 types, with locations, ability requirements and fast travel doors.
- `data/collectibles.csv`: flat export of the same data.
- `web/tracker.template.html`: tracker page source.
- `web/tracker.html`: built page with the data embedded. Published as a claude.ai artifact.
- `scripts/build.py`: regenerates the CSV and the built page after editing the JSON.

```
python3 scripts/build.py
```

Sources: PowerPyx zone guides (Oct 2026), allthings.how for the Central taxi.
