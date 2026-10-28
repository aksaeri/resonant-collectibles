# resonant-collectibles
Tracker for the Control Resonant Archives > Collectibles set.

- `data/archives.json`: the database. 331 documents, recordings and videos in 31 categories, in in-game menu order, with location, quest, unlock conditions and directions.
- `data/archives.csv`: flat export of the same data.
- `data/manual/altered-speakers.json`: hand-entered Altered Speakers set (not covered by the main guide), in spreadsheet order with pinned ids.
- `data/sources/archive-sheet.json`: extract of the community archive spreadsheet, merged in as each item's `sheet` field (file type, location, notes).
- `data/side-collectibles.json`: earlier list of the 67 trophy secrets (taxis, dogs, cameras, hideouts and so on). Not used by the tracker.
- `web/tracker.template.html`, `web/tracker.js`: tracker page source.
- `web/tracker.html`: built page with the data embedded. Published as a claude.ai artifact.
- `scripts/import_archives.py`: rebuilds `data/archives.json` from saved camzillasmom.com guide pages.
- `scripts/build.py`: rebuilds the CSV and the page.

```
python3 scripts/import_archives.py <dir of saved guide .html pages>
python3 scripts/build.py
```

Sources: camzillasmom.com Archives guides (Oct 2026), MapMaster for Altered Speakers, cross-checked against a community spreadsheet (docs.google.com/spreadsheets/d/1Frm8FKQm6QdoGvSIMyh3rT-DXXHFGS1g).

Item ids are the tick keys in the tracker's store. Never renumber them; pin an `id` in the manual JSON when reordering.
