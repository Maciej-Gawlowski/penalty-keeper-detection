import csv
import os
import re
import subprocess
from pathlib import Path

# --------- settings you can tweak ----------
CSV_PATH = Path("data/meta/penalties.csv")
OUT_DIR = Path("data/clips/penalties_720p")
PRE_SECONDS = 10      # seconds before penalty
POST_SECONDS = 10     # seconds after penalty
REENCODE_TO_MP4 = True  # True = smaller + more compatible, False = faster but mkv copy
# -------------------------------------------

def slug(s: str, max_len: int = 120) -> str:
    s = s.strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    return s[:max_len] if len(s) > max_len else s

def run(cmd: list[str]) -> None:
    # show minimal output; raise if ffmpeg fails
    subprocess.run(cmd, check=True)

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing {CSV_PATH}. Run scripts/extract_penalties.py first.")
    if CSV_PATH.stat().st_size == 0:
        raise RuntimeError(f"{CSV_PATH} is empty (0 bytes). Re-run scripts/extract_penalties.py and ensure it writes rows.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index_path = OUT_DIR / "clips_index.csv"

    created = 0
    skipped_missing_video = 0
    skipped_bad_row = 0

    with CSV_PATH.open("r", newline="", encoding="utf-8") as f_in, index_path.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["clip_path", "game_id", "half", "t_seconds", "label", "gameTime", "video_path"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                game_id = row["game_id"]
                half = int(row["half"])
                t = float(row["t_seconds"])
                label = row.get("label", "")
                gameTime = row.get("gameTime", "")
                labels_file = row["labels_file"]
            except Exception:
                skipped_bad_row += 1
                continue

            game_dir = Path(labels_file).parent
            video_name = "1_720p.mkv" if half == 1 else "2_720p.mkv"
            video_path = game_dir / video_name

            if not video_path.exists():
                skipped_missing_video += 1
                continue

            start = max(t - PRE_SECONDS, 0.0)
            duration = PRE_SECONDS + POST_SECONDS

            safe_game = slug(game_id)
            out_name = f"{safe_game}_H{half}_{int(t):06d}s.mp4" if REENCODE_TO_MP4 else f"{safe_game}_H{half}_{int(t):06d}s.mkv"
            out_path = OUT_DIR / out_name

            # ffmpeg command
            if REENCODE_TO_MP4:
                cmd = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{start:.3f}", "-i", str(video_path),
                    "-t", f"{duration:.3f}",
                    "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "96k",
                    str(out_path)
                ]
            else:
                # fast, but cuts only on keyframes sometimes (less precise)
                cmd = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{start:.3f}", "-i", str(video_path),
                    "-t", f"{duration:.3f}",
                    "-c", "copy",
                    str(out_path)
                ]

            try:
                run(cmd)
                created += 1
                writer.writerow({
                    "clip_path": str(out_path),
                    "game_id": game_id,
                    "half": half,
                    "t_seconds": t,
                    "label": label,
                    "gameTime": gameTime,
                    "video_path": str(video_path),
                })
                print(f"[OK] {out_path.name}")
            except subprocess.CalledProcessError:
                print(f"[FAIL] ffmpeg failed for {game_id} H{half} t={t}")
                continue

    print("\nDone.")
    print(f"Created clips: {created}")
    print(f"Skipped (missing video file): {skipped_missing_video}")
    print(f"Skipped (bad csv rows): {skipped_bad_row}")
    print(f"Index saved to: {index_path}")

if __name__ == "__main__":
    main()

