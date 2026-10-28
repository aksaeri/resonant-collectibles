"""Build data/archives.json from saved camzillasmom.com guide pages plus data/manual/*.json,
cross-checked against data/sources/archive-sheet.json (community spreadsheet).

Usage: python3 scripts/import_archives.py <dir with saved .html guide pages>
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# In-game Archives > Collectibles menu order, with the guide page slug for each.
CATEGORIES = [
    ("Jesse Faden", "jesse-faden"), ("Dylan Faden", "dylan-faden"), ("Ordinary AWE", "ordinary-awe"),
    ("Dr. Darling", "dr-darling"), ("Prime Candidate Program", "prime-candidate-program"),
    ("Zoe's Mixtape", "zoes-mixtape"), ("Civilian Records", "civilian-records"),
    ("Oldest House Lockdown", "oldest-house-lockdown"), ("Crisis Containment", "crisis-containment"),
    ("Evacuation Efforts", "evacuation-efforts"), ("FBC Research & Records", "fbc-research-records"),
    ("FBC Logistics", "fbc-logistics"), ("Subway Maintenance", "subway-maintenance"),
    ("The Patterning", "the-patterning"), ("Resonant Entities", "resonant-entities"),
    ("Simon Arish", "simon-arish"), ("Central Factory Investigation", "central-factory-investigation"),
    ("West Incursion Records", "west-incursion-records"), ("Astral Plane Breach", "astral-plane-breach"),
    ("Park Survey", "park-survey"), ("Dr. Raya Underhill", "dr-raya-underhill"),
    ("Underpass Accounts", "underpass-accounts"), ("Underpass Exploration", "underpass-exploration"),
    ("Altered Item Reports", "altered-item-reports"), ("Altered Speakers", "manual:altered-speakers"),
    ("Dig Site Threshold", "dig-site-threshold-collectibles-all-7-archives-locations"),
    ("Impermanence Threshold", "impermanence-threshold"), ("Secret Organization", "secret-organization"),
    ("Dylan's Sketchbook", "dylans-sketchbook"), ("Season's Greetings", "hub:Seasons Greetings"),
    ("The Nightwatchman", "hub:The Nightwatchman"),
]

ZONE_ORDER = ["Downtown", "Oldest House", "Prime Candidate Training", "Central", "West Incursion Zone",
              "Evacuation Zone", "The Park", "Underpass", "The Unknown", "Other"]


# Guide headings that carry a location suffix; the in-game titles are shorter.
TITLE_FIXES = {
    "Medic’s Assessment Recording in the Field Hospital": "Medic’s Assessment Recording",
    "Dig Site Threshold Quarantine List (Cabinet Code)": "Dig Site Threshold Quarantine List",
    "Team Lead’s Expedition Log at the Threshold Dig Site": "Team Lead’s Expedition Log",
    "Threshold Site Recording in the Mobile Research Station": "Threshold Site Recording",
    "Wilson’s ID Badge on the White Lab Coat": "Wilson’s ID Badge",
    "Parabiologist’s Notes at the Threshold Dig Site": "Parabiologist’s Notes",
    "Dig Site Threshold Note in the Mobile Research Station": "Dig Site Threshold Note",
}

# Sheet spellings that differ from the guide for the same entry.
SHEET_ALIASES = {"missingnotes1": "missionnotes1", "themoldgrowthstimulator": "themoldgrowthsimulator",
                 "fuckyoularrynote": "fckyoularrynote"}
SHEET_REGIONS = {"Unknown": "The Unknown"}


def norm(s):
    s = str(s).lower().replace("’", "'").replace("&", "and").replace("ü", "u")
    return re.sub(r"[^a-z0-9]", "", s)


def zone_of(loc, how):
    s = loc.lower()
    for key, zone in [("prime candidate", "Prime Candidate Training"), ("oldest house rooftop", "Downtown"),
                      ("underpass", "Underpass"), ("oldest house", "Oldest House"), ("central executive", "Oldest House")]:
        if key in s:
            return zone
    # "Place, Zone": the part after the last comma names the zone.
    if "," in s:
        z = zone_of(s.rsplit(",", 1)[1], how)
        if z != "Other":
            return z
    rules = [
        ("prime candidate", "Prime Candidate Training"), ("underpass", "Underpass"), ("astral", "Underpass"),
        ("unknown", "The Unknown"), ("dylan’s apartment", "The Unknown"), ("dylan's apartment", "The Unknown"),
        ("oldest house rooftop", "Downtown"), ("oldest house", "Oldest House"), ("central executive", "Oldest House"),
        ("west incursion", "West Incursion Zone"), ("evacuation", "Evacuation Zone"), ("park", "The Park"),
        ("central", "Central"), ("downtown", "Downtown"), ("vanished station", "Central"),
        ("east park station", "Central"),
    ]
    for key, zone in rules:
        if key in s:
            return zone
    return "Other"


def to_lines(path):
    h = path.read_text(errors="ignore")
    m = re.search(r"<article.*?</article>", h, re.S)
    t = m.group(0) if m else h
    t = re.sub(r"<(script|style).*?</\1>", "", t, flags=re.S)
    t = re.sub(r"<(h[1-6]|p|li|br|div|tr)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = re.sub(r"[ \t]+", " ", t)
    return [l.strip() for l in t.split("\n") if l.strip()]


HDR = re.compile(r"^(\d+) [–-] (.+)$")
FIELD = re.compile(r"^(Location|Quest|Unlocks|Requires|Requirement|Quest Required|Needed for):")
STOP = {"Camzillasmom", "About Control Resonant", "The Master of Many Worlds"}


def parse(lines):
    items = []
    for i, line in enumerate(lines):
        if not line.startswith("Collectible Category:"):
            continue
        j = i - 1
        while j > 0 and FIELD.match(lines[j]):
            j -= 1
        mh = HDR.match(lines[j])
        title = mh.group(2) if mh else lines[j]
        fields = {}
        for l in lines[j + 1:i + 1]:
            k, _, v = l.partition(":")
            fields[k.strip()] = v.strip()
        k = i + 1
        if k < len(lines) and lines[k].startswith("Description:"):
            k += 1
        body = []
        while k < len(lines) and not HDR.match(lines[k]) and lines[k] not in STOP \
                and not lines[k].startswith("Collectible Category:"):
            body.append(lines[k])
            k += 1
        unlock = next((fields[f] for f in ("Unlocks", "Requires", "Requirement", "Quest Required") if fields.get(f)), "")
        items.append({"title": title, "category_label": fields.get("Collectible Category", ""),
                      "location": fields.get("Location", ""), "quest": fields.get("Quest", ""),
                      "unlocks": unlock, "how": " ".join(body)})
    return items


def main(src):
    src = Path(src)
    sheet = json.loads((ROOT / "data/sources/archive-sheet.json").read_text())
    hub = parse(to_lines(src / "hub.html"))
    cats, items = [], []
    for order, (name, slug) in enumerate(CATEGORIES, 1):
        cid = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")
        if slug.startswith("manual:"):
            raw = json.loads((ROOT / "data/manual" / (slug[7:] + ".json")).read_text())
        elif slug.startswith("hub:"):
            raw = [x for x in hub if x["category_label"] == slug[4:]]
        else:
            raw = parse(to_lines(src / (slug + ".html")))
        cats.append({"id": cid, "name": name, "order": order, "count": len(raw)})
        rows = [r for r in sheet if norm(r["category"]) == norm(name)]
        for n, x in enumerate(raw, 1):
            title = TITLE_FIXES.get(x["title"], x["title"])
            k = norm(title)
            row = next((r for r in rows if SHEET_ALIASES.get(norm(r["title"]), norm(r["title"])) == k), None)
            text = " ".join([x.get("quest", ""), x.get("unlocks", ""), x["how"]])
            flags = []
            if re.search(r"Game\+", text):
                flags.append("game-plus")
            elif re.search(r"main story|finish the game|finish the main|complete the main|after the story", text, re.I):
                flags.append("post-story")
            if x.get("unverified"):
                flags.append("unverified")
            zone = zone_of(x["location"], x["how"])
            alt = None
            if row:
                region = SHEET_REGIONS.get(row["region"], row["region"])
                if zone == "Other" and region in ZONE_ORDER:
                    zone = region
                alt = {"type": row["type"], "region": region if region in ZONE_ORDER else "",
                       "location": row["location"] or "", "notes": row["notes"] or ""}
            else:
                flags.append("not-in-sheet")
            items.append({
                # Ids are the tick keys in the tracker's store: pinned ids survive reordering.
                "id": x.get("id", f"{cid}-{n:02d}"), "category": cid, "n": n, "title": title,
                "zone": zone, "place": x["location"],
                "quest": x.get("quest", ""), "unlocks": x.get("unlocks", ""), "how": x["how"], "flags": flags,
                "sheet": alt,
            })
    out = {
        "game": "Control Resonant",
        "set": "Archives > Collectibles",
        "total": len(items),
        "sources": ["https://camzillasmom.com/control-resonant-game-guides-collectibles-hub/",
                    "https://mapmaster.io/games/control-resonant/guides/Altered%20Speakers%20Collectible",
                    "https://docs.google.com/spreadsheets/d/1Frm8FKQm6QdoGvSIMyh3rT-DXXHFGS1g"],
        "zones": ZONE_ORDER,
        "categories": cats,
        "items": items,
    }
    (ROOT / "data/archives.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(items)} items in {len(cats)} categories")


if __name__ == "__main__":
    main(sys.argv[1])
