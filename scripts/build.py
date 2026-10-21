"""Build web/tracker.html and data/archives.csv from data/archives.json."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/archives.json").read_text())

template = (ROOT / "web/tracker.template.html").read_text()
script = (ROOT / "web/tracker.js").read_text()
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
page = template.replace("__DATA__", payload).replace("__SCRIPT__", script.strip())
(ROOT / "web/tracker.html").write_text(page)

cats = {c["id"]: c["name"] for c in data["categories"]}
with open(ROOT / "data/archives.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "category", "n", "title", "zone", "place", "quest", "unlocks", "flags", "how"])
    for i in data["items"]:
        w.writerow([i["id"], cats[i["category"]], i["n"], i["title"], i["zone"], i["place"], i["quest"],
                    i["unlocks"], "; ".join(i["flags"]), i["how"]])

print(f"{len(data['items'])} items written")
