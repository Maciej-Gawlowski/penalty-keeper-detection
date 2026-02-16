import csv, os, inspect
from pathlib import Path

RAW = Path("data/raw/SoccerNet")
INP = Path("data/meta/penalties.csv")
PW  = os.getenv("SOCCERNET_PW", "")

if not INP.exists():
    raise SystemExit(f"Missing {INP}")

from SoccerNet.Downloader import SoccerNetDownloader

def find_game_dir(game_name: str) -> Path | None:
    # Look for .../<task>/<season>/<game>
    hits = [p for p in RAW.rglob(game_name) if p.is_dir() and p.name == game_name]
    if not hits:
        return None
    # Choose the shortest path (usually the correct one if duplicates exist)
    hits.sort(key=lambda p: len(str(p)))
    return hits[0]

def set_password(dl, pw: str):
    if not pw:
        print("WARNING: SOCCERNET_PW not set.")
        return
    if hasattr(dl, "password"):
        dl.password = pw

def download_until_exists(dl, task: str, split_list: list[str], game: str, half_file: str, expected_path: Path) -> bool:
    # Different SoccerNet versions have different signatures; try a few.
    call_variants = [
        lambda split: dl.downloadGame(game, [half_file], split, task),
        lambda split: dl.downloadGame(game, split, task, [half_file]),
        lambda split: dl.downloadGame(task, split, game, [half_file]),
        lambda split: dl.downloadGame(game=game, files=[half_file], split=split, task=task),
    ]

    for split in split_list:
        for i, call in enumerate(call_variants, start=1):
            try:
                call(split)
            except TypeError:
                continue
            except Exception as e:
                # keep trying other variants/splits
                continue

            # IMPORTANT: only "success" if the file exists now
            if expected_path.exists() and expected_path.stat().st_size > 0:
                return True

            # Sometimes downloader saves in a different spot; try locate it
            matches = [p for p in RAW.rglob(half_file) if p.parent.name == game and p.stat().st_size > 0]
            if matches:
                found = matches[0]
                # normalize location (optional but helpful)
                expected_path.parent.mkdir(parents=True, exist_ok=True)
                if found.resolve() != expected_path.resolve():
                    try:
                        found.replace(expected_path)
                    except Exception:
                        pass
                if expected_path.exists() and expected_path.stat().st_size > 0:
                    return True

    return False

# Build unique targets from penalties.csv
targets = {}
with INP.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        game = row["game_id"].strip()
        half = str(row["half"]).strip()
        half_file = f"{half}_720p.mkv"
        game_dir = find_game_dir(game)
        if not game_dir:
            continue
        season = game_dir.parent.name
        task = game_dir.parent.parent.name
        expected = game_dir / half_file
        targets[(task, season, game, half_file)] = expected

print("Targets:", len(targets))

dl = SoccerNetDownloader(LocalDirectory=str(RAW))
set_password(dl, PW)

# Print signature info for debugging
try:
    print("downloadGame signature:", inspect.signature(dl.downloadGame))
except Exception:
    print("downloadGame signature: <could not inspect>")

ok = fail = 0
splits = ["train", "valid", "test"]

for (task, season, game, half_file), expected_path in targets.items():
    if expected_path.exists() and expected_path.stat().st_size > 0:
        print("[SKIP] already:", expected_path)
        ok += 1
        continue

    print(f"[DL] {task} | {game} | {half_file}")
    worked = download_until_exists(dl, task, splits, game, half_file, expected_path)

    if worked:
        print("[OK] saved:", expected_path)
        ok += 1
    else:
        print("[FAIL] still missing:", expected_path)
        fail += 1

print("\nDone. OK:", ok, "FAIL:", fail)
