from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

ROOT = Path(__file__).resolve().parents[1]   # repo root
OUT = ROOT / "data" / "raw" / "SoccerNet"
OUT.mkdir(parents=True, exist_ok=True)

dl = SoccerNetDownloader(LocalDirectory=str(OUT))

# Download ONLY the v2 Action Spotting labels (includes Penalty timestamps)
dl.downloadGames(files=["Labels-v2.json"], split=["train", "valid", "test"])

print("Done. Saved under:", OUT)
