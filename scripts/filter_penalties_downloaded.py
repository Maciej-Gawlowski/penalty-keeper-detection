import csv
from pathlib import Path

raw = Path("data/raw/SoccerNet")
games = {p.parent.name for p in raw.rglob("*_224p.mkv")}

inp = Path("data/meta/penalties.csv")
out = Path("data/meta/penalties_downloaded.csv")

if not inp.exists() or inp.stat().st_size == 0:
    raise SystemExit("penalties.csv is missing/empty. Re-run: & .\\.venv\\Scripts\\python.exe scripts\\extract_penalties.py")

n_in = n_out = 0
with inp.open(newline="", encoding="utf-8") as f, out.open("w", newline="", encoding="utf-8") as g:
    r = csv.DictReader(f)
    if not r.fieldnames:
        raise SystemExit("penalties.csv has no header (empty). Re-run extract_penalties.py.")
    w = csv.DictWriter(g, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        n_in += 1
        if row.get("game_id") in games:
            w.writerow(row)
            n_out += 1

print("games_with_video:", len(games))
print("input_events:", n_in)
print("kept_events:", n_out)
print("saved:", out)
