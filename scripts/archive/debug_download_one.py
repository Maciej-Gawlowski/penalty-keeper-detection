import os
from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

OUT = Path("data/raw/SoccerNet_TEST")
OUT.mkdir(parents=True, exist_ok=True)

dl = SoccerNetDownloader(LocalDirectory=str(OUT))
if hasattr(dl, "password"):
    dl.password = os.environ.get("SOCCERNET_PW","")

game = os.environ["SN_GAME"]
print("GAME=", game)
print("pw_len=", len(getattr(dl,"password","")))

splits = ["train","valid","test","challenge"]
files = ["1_224p.mkv","1.mkv","2.mkv","1_720p.mkv","2_720p.mkv"]

for f in files:
    for s in splits:
        print(f"\nTRY file={f} split={s}")
        try:
            dl.downloadGame(game, files=[f], spl=s, verbose=True)
        except Exception as e:
            print("  exception:", type(e).__name__, e)

        hits = list(OUT.rglob(f))
        if hits:
            p = hits[0]
            print("✅ DOWNLOADED:", p)
            print("   size:", p.stat().st_size)
            raise SystemExit

print("\n❌ Nothing downloaded (all 404). If SN_GAME is correct, then your access/password likely doesn’t allow these files.")
