import json
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "SoccerNet"   # this matches your downloaded folder
OUT_CSV = ROOT / "data" / "meta" / "penalties.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

LABEL_FILENAME = "Labels-v2.json"

def parse_gameTime(gt: str):
    # common format: "1 - 12:34"
    m = re.match(r"^\s*([12])\s*-\s*(\d{1,2}):(\d{2})\s*$", gt)
    if not m:
        return None
    half = int(m.group(1))
    t_seconds = int(m.group(2)) * 60 + int(m.group(3))
    return half, float(t_seconds)

def main():
    print("RAW_DIR:", RAW_DIR)
    label_files = list(RAW_DIR.rglob(LABEL_FILENAME))
    print(f"Found {len(label_files)} label files named {LABEL_FILENAME}")

    rows = []

    for lf in label_files:
        try:
            data = json.loads(lf.read_text(encoding="utf-8"))
        except Exception as e:
            print("Skip unreadable:", lf, e)
            continue

        ann = data.get("annotations")
        if not isinstance(ann, list):
            continue

        game_id = lf.parent.name

        for ev in ann:
            if not isinstance(ev, dict):
                continue

            label = ev.get("label", "")
            if not isinstance(label, str):
                continue

            if "penalty" not in label.lower():
                continue

            half = None
            t_seconds = None

            gt = ev.get("gameTime")
            if isinstance(gt, str):
                parsed = parse_gameTime(gt)
                if parsed:
                    half, t_seconds = parsed

            if t_seconds is None:
                pos = ev.get("position")
                if pos is not None:
                    try:
                        posf = float(pos)
                        t_seconds = posf / 1000.0 if posf > 10000 else posf
                    except:
                        pass

                h = ev.get("half") or ev.get("period")
                if h is not None:
                    try:
                        half = int(h)
                    except:
                        pass

            if t_seconds is None:
                continue

            rows.append({
                "game_id": game_id,
                "half": half,
                "t_seconds": round(float(t_seconds), 3),
                "label": label,
                "gameTime": ev.get("gameTime", ""),
                "labels_file": str(lf),
            })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["game_id", "half", "t_seconds", "label", "gameTime", "labels_file"]
        )
        w.writeheader()
        w.writerows(rows)

    print(f"Extracted {len(rows)} penalty-like events.")
    print("Saved:", OUT_CSV)
    if rows:
        print("Example:", rows[0])

if __name__ == "__main__":
    main()
