import os
from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

RAW = Path("data/raw/SoccerNet")
GAME = os.environ.get("SN_GAME")
PW = os.environ.get("SOCCERNET_PW", "")

if not GAME:
    raise SystemExit("SN_GAME is not set. In PowerShell do:  $env:SN_GAME = \"<game_id>\"")

dl = SoccerNetDownloader(LocalDirectory=str(RAW))
# your SoccerNet version wants password set as attribute (not __init__(password=...))
dl.password = PW

files = ["1_720p.mkv"]  # only half 1, only 720p -> fast probe

tasks = ["england_epl"]            # your folder structure shows england_epl
splits = ["train", "valid", "test"]  # we try all because split can vary

print("GAME:", GAME)
print("Trying to download:", files)

last_err = None
for task in tasks:
    for split in splits:
        try:
            print(f"-> task={task} split={split}")
            dl.downloadGames(files=files, split=split, task=task, games=[GAME])
            print("SUCCESS ✅ 720p exists for this game.")
            raise SystemExit(0)
        except Exception as e:
            last_err = e
            print("   fail:", type(e).__name__, e)

print("\nFAILED ❌ Could not download 720p for this game.")
print("Last error:", type(last_err).__name__, last_err)
print("This usually means 720p isn't available for your access/dataset (or task/split differs).")
