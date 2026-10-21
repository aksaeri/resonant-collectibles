"""Build web/tracker.html and data/collectibles.csv from data/collectibles.json."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/collectibles.json").read_text())

template = (ROOT / "web/tracker.template.html").read_text()
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
(ROOT / "web/tracker.html").write_text(template.replace("__DATA__", payload))

zones = {z["id"]: z["name"] for z in data["zones"]}
cats = {c["id"]: c["name"] for c in data["categories"]}
with open(ROOT / "data/collectibles.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "zone", "category", "name", "requires", "location"])
    for i in data["items"]:
        w.writerow([i["id"], zones[i["zone"]], cats[i["category"]], i["name"], "; ".join(i["requires"]), i["location"]])

print(f"{len(data['items'])} items written")
