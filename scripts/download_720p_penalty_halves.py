import os, csv, re, inspect
from pathlib import Path

RAW = Path("data/raw/SoccerNet")
CSV_IN = Path("data/meta/penalties.csv")  # currently your "downloaded/filtered" penalties file

def call_flexible(fn, **kwargs):
    """Call fn with only the kwargs that exist in its signature."""
    sig = inspect.signature(fn)
    filt = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return fn(**filt)

def try_download(dl, task, split, game, file_name):
    # Try several common calling conventions across SoccerNet package versions
    attempts = []

    # Most common: downloadGames(files=[...], split=[...], task=...)
    attempts.append(("downloadGames split=list", lambda: call_flexible(
        dl.downloadGames, files=[file_name], split=[split], task=task
    )))

    # Some versions: split as string
    attempts.append(("downloadGames split=str", lambda: call_flexible(
        dl.downloadGames, files=[file_name], split=split, task=task
    )))

    # Some versions may have downloadGame (singular)
    if hasattr(dl, "downloadGame"):
        attempts.append(("downloadGame split=list", lambda: call_flexible(
            dl.downloadGame, files=[file_name], split=[split], task=task, game=game
        )))
        attempts.append(("downloadGame split=str", lambda: call_flexible(
            dl.downloadGame, files=[file_name], split=split, task=task, game=game
        )))

    last_err = None
    for name, fn in attempts:
        try:
            fn()
            return True, name, None
        except Exception as e:
            last_err = e

    return False, None, last_err

def main():
    pw = os.environ.get("SOCCERNET_PW", "")
    if not pw:
        raise SystemExit("Set SOCCERNET_PW first (PowerShell: $env:SOCCERNET_PW='...')")

    if not CSV_IN.exists():
        raise SystemExit(f"Missing {CSV_IN}. You should have it from your earlier steps.")

    # Use the environment where SoccerNet is installed (your .venv worked earlier)
    from SoccerNet.Downloader import SoccerNetDownloader

    dl = SoccerNetDownloader(LocalDirectory=str(RAW))
    # Most versions use attribute password (NOT __init__ kwarg)
    if hasattr(dl, "password"):
        dl.password = pw

    # Build targets: unique (task, game_id, half) from penalties.csv
    targets = set()
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            game = row.get("game_id", "").strip()
            half = row.get("half", "").strip()
            labels_file = row.get("labels_file", "")

            if not game or not half:
                continue

            # half may be "1" or "1.0"
            half_i = int(float(half))
            file_name = f"{half_i}_720p.mkv"

            # labels_file contains .../SoccerNet/<task>/<season>/<game_id>/Labels-v2.json
            m = re.search(r"SoccerNet[\\/](?P<task>[^\\/]+)[\\/](?P<season>[^\\/]+)[\\/]", labels_file)
            if not m:
                continue

            task = m.group("task")
            targets.add((task, game, file_name))

    print(f"Targets (task, game, half-file): {len(targets)}")

    # Download each target, trying train/valid/test
    ok = 0
    fail = 0
    for task, game, file_name in sorted(targets):
        # Skip if already present anywhere under RAW
        already = list(RAW.rglob(f"{game}/{file_name}"))
        if already:
            print(f"[SKIP] {game} {file_name}")
            ok += 1
            continue

        success = False
        last = None
        for split in ["train", "valid", "test"]:
            success, how, err = try_download(dl, task, split, game, file_name)
            if success:
                print(f"[OK] {game} {file_name}  task={task} split={split} via {how}")
                ok += 1
                break
            last = err

        if not success:
            print(f"[FAIL] {game} {file_name}  last_error={type(last).__name__}: {last}")
            fail += 1

    print("\nDone.")
    print("OK:", ok)
    print("FAIL:", fail)

if __name__ == "__main__":
    main()
