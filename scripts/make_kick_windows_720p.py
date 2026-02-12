import os, csv, shutil, subprocess
from pathlib import Path

KICK_CSV = Path("data/meta/kick_times.csv")      # your file
IN_DIR   = Path("data/clips/penalties_720p")          # your 17 mp4s
OUT_DIR  = Path("data/clips/kick_windows_720p")       # new folder
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRE  = float(os.getenv("KICK_PRE", "1.2"))       # seconds before kick
POST = float(os.getenv("KICK_POST","0.8"))       # seconds after kick

ffmpeg = os.getenv("FFMPEG_EXE") or shutil.which("ffmpeg")
if not ffmpeg:
    raise SystemExit("ffmpeg not found. Set $env:FFMPEG_EXE to full path of ffmpeg.exe")

out_index = Path("data/meta/kick_windows_720p.csv")

def run(cmd):
    subprocess.run(cmd, check=True)

with KICK_CSV.open(newline="", encoding="utf-8") as f, out_index.open("w", newline="", encoding="utf-8") as g:
    r = csv.DictReader(f)
    w = csv.DictWriter(g, fieldnames=["clip_name","window_file","start_s","dur_s","kick_in_window_s","kick_frame"])
    w.writeheader()

    for row in r:
        clip = row["clip_name"]
        kick_t = float(row["kick_time_s"])
        kick_fr = int(float(row["kick_frame"]))

        src = IN_DIR / clip
        if not src.exists():
            print("[SKIP missing]", src)
            continue

        start = max(0.0, kick_t - PRE)
        dur   = PRE + POST
        kick_in_window = kick_t - start

        out_name = src.stem + "_KICK.mp4"
        dst = OUT_DIR / out_name

        cmd = [
            ffmpeg, "-y",
            "-ss", f"{start:.3f}",
            "-i", str(src),
            "-t", f"{dur:.3f}",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            str(dst)
        ]
        run(cmd)

        w.writerow({
            "clip_name": clip,
            "window_file": str(dst).replace("\\","/"),
            "start_s": f"{start:.3f}",
            "dur_s": f"{dur:.3f}",
            "kick_in_window_s": f"{kick_in_window:.3f}",
            "kick_frame": str(kick_fr),
        })
        print("[OK]", dst.name)

print("Saved:", out_index)
