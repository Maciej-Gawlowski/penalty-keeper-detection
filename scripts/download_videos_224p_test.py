from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "SoccerNet"
OUT.mkdir(parents=True, exist_ok=True)

dl = SoccerNetDownloader(LocalDirectory=str(OUT))

pw = input("Paste SoccerNet VIDEO password from NDA email: ").strip()
dl.password = pw

# start small: 224p only + video.ini
dl.downloadGames(files=["1_224p.mkv", "2_224p.mkv", "video.ini"], split=["test"])

print("Done.")
