import csv, os
from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

RAW = Path("data/raw/SoccerNet")
INP = Path("data/meta/penalties.csv")
PW  = os.getenv("SOCCERNET_PW", "")

if not INP.exists():
    raise SystemExit(f"Missing {INP}")

targets = []
seen = set()

with INP.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        game_id   = row["game_id"].strip()
        half      = str(row["half"]).strip()
        half_file = f"{half}_720p.mkv"
        labels_path = Path(row["labels_file"].strip())
        try:
            parts   = labels_path.parts
            sn_idx  = next(i for i, p in enumerate(parts) if p == "SoccerNet")
            league  = parts[sn_idx + 1]
            season  = parts[sn_idx + 2]
        except (StopIteration, IndexError):
            print(f"[WARN] nie moge wyciagnac league/season z: {labels_path}")
            continue
        key = (league, season, game_id, half_file)
        if key not in seen:
            seen.add(key)
            targets.append(key)

print(f"Targets: {len(targets)}")

dl = SoccerNetDownloader(LocalDirectory=str(RAW))
if PW:
    dl.password = PW
else:
    print("WARNING: SOCCERNET_PW nie ustawione!")

ok = fail = 0
for league, season, game, half_file in targets:
    expected = RAW / league / season / game / half_file
    if expected.exists() and expected.stat().st_size > 0:
        print(f"[SKIP] juz jest: {expected}")
        ok += 1
        continue
    expected.parent.mkdir(parents=True, exist_ok=True)
    print(f"[DL] {league}/{season}/{game} | {half_file}")
    pobrano = False
    for split in ["train", "valid", "test", "challenge"]:
        try:
            dl.downloadGame(game=game, files=[half_file], split=split, task=league)
            if expected.exists() and expected.stat().st_size > 0:
                pobrano = True
                break
        except Exception:
            continue
    if pobrano:
        print(f"[OK] {expected}")
        ok += 1
    else:
        print(f"[FAIL] brak: {expected}")
        fail += 1

print(f"\nDone. OK: {ok}  FAIL: {fail}")