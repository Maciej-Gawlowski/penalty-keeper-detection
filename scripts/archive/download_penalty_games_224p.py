import os
import csv
import random
from pathlib import Path
from SoccerNet.Downloader import SoccerNetDownloader

RAW = Path("data/raw/SoccerNet").resolve()

def game_rel_from_labels_file(labels_file: str) -> str:
    p = Path(labels_file).resolve()
    # labels_file is usually .../data/raw/SoccerNet/<league>/<season>/<game>/Labels-v2.json
    try:
        rel = p.parent.relative_to(RAW)
        return rel.as_posix()
    except Exception:
        # fallback: find "SoccerNet" in the path and take everything after it
        parts = list(p.parts)
        if "SoccerNet" in parts:
            i = parts.index("SoccerNet")
            rel = Path(*parts[i+1:-1])  # drop Labels-v2.json
            return rel.as_posix()
        raise RuntimeError(f"Cannot derive game path from labels_file: {labels_file}")

def main():
    # Use your full penalties file here:
    csv_path = Path("data/meta/penalties_all.csv")
    if not csv_path.exists():
        # fallback if you don't have penalties_all.csv
        csv_path = Path("data/meta/penalties.csv")

    if not csv_path.exists():
        raise SystemExit("Could not find data/meta/penalties_all.csv or data/meta/penalties.csv")

    max_games = int(os.environ.get("MAX_PEN_GAMES", "30"))  # default 30 games
    shuffle = os.environ.get("SHUFFLE", "1") != "0"

    pw = os.environ.get("SOCCERNET_PW")
    if not pw:
        pw = input("SoccerNet video password: ").strip()

    # collect unique game paths that contain at least one penalty
    games = []
    seen = set()

    with csv_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            lf = row.get("labels_file", "")
            if not lf:
                continue
            g = game_rel_from_labels_file(lf)
            if g not in seen:
                seen.add(g)
                games.append(g)

    if shuffle:
        random.seed(0)
        random.shuffle(games)

    games = games[:max_games]
    print(f"Penalty games available in CSV: {len(seen)}")
    print(f"Will download: {len(games)} games -> ~{2*len(games)} half videos")

    dl = SoccerNetDownloader(LocalDirectory=str(RAW))
    dl.password = pw  # set password for video downloads

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game}")
        # IMPORTANT: do NOT request video.ini (it often triggers 401); only the mkv files
        dl.downloadGame(files=["1_224p.mkv", "2_224p.mkv"], game=game)

    print("Done.")

if __name__ == "__main__":
    main()
