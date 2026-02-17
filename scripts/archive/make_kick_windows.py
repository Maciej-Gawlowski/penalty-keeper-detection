import os, csv, shutil, subprocess
from pathlib import Path

# ---- Config (defaults) ----
KICK_CSV = Path(os.getenv("KICK_CSV", "data/meta/kick_times.csv"))

# IMPORTANT: you no longer have data/clips/penalties, only penalties_720p
IN_DIR   = Path(os.getenv("IN_DIR", "data/clips/penalties_720p"))

# IMPORTANT: output windows should go to kick_windows_720p
OUT_DIR  = Path(os.getenv("OUT_DIR", "data/clips/kick_windows_720p"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRE  = float(os.getenv("KICK_PRE", "1.5"))   # seconds before kick
POST = float(os.getenv("KICK_POST","2.5"))   # seconds after kick

ffmpeg = os.getenv("FFMPEG_EXE") or shutil.which("ffmpeg")
if not ffmpeg:
    raise SystemExit("ffmpeg not found. Set $env:FFMPEG_EXE to full path of ffmpeg.exe")

OUT_CSV = Path(os.getenv("OUT_CSV", "data/meta/kick_windows_720p.csv"))
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def run(cmd):
    subprocess.run(cmd, check=True)


def resolve_src(row: dict) -> Path | None:
    """
    Supports either:
      A) clip_name column (filename only)  -> uses IN_DIR / clip_name
      B) clip_path column (full path)      -> uses clip_path directly
    """
    if "clip_path" in row and row["clip_path"].strip():
        return Path(row["clip_path"].strip())

    if "clip_name" in row and row["clip_name"].strip():
        return IN_DIR / row["clip_name"].strip()

    return None


def get_kick_time(row: dict) -> float | None:
    for key in ("kick_time_s", "kick_s", "kick_time", "t"):
        if key in row and str(row[key]).strip():
            return float(row[key])
    return None


def get_kick_frame(row: dict) -> str:
    # optional; keep if present, else blank
    for key in ("kick_frame", "frame"):
        if key in row and str(row[key]).strip():
            return str(int(float(row[key])))
    return ""


with KICK_CSV.open(newline="", encoding="utf-8") as f, OUT_CSV.open("w", newline="", encoding="utf-8") as g:
    r = csv.DictReader(f)
    w = csv.DictWriter(
        g,
        fieldnames=["src_file", "window_file", "start_s", "dur_s", "kick_in_window_s", "kick_frame"],
    )
    w.writeheader()

    for row in r:
        src = resolve_src(row)
        kick_t = get_kick_time(row)
        kick_fr = get_kick_frame(row)

        if src is None or kick_t is None:
            print("[SKIP bad row]", row)
            continue

        if src.is_dir():
            print("[SKIP src is a folder, not a file]", src)
            continue

        if not src.exists():
            print("[SKIP missing]", src)
            continue

        start = max(0.0, kick_t - PRE)
        dur   = PRE + POST
        kick_in_window = kick_t - start

        out_name = src.stem + "_KICK.mp4"
        dst = OUT_DIR / out_name

        # More accurate seeking: put -ss AFTER -i (slower but better alignment)
        cmd = [
            ffmpeg, "-y",
            "-i", str(src),
            "-ss", f"{start:.3f}",
            "-t", f"{dur:.3f}",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            str(dst)
        ]
        run(cmd)

        w.writerow({
            "src_file": str(src).replace("\\","/"),
            "window_file": str(dst).replace("\\","/"),
            "start_s": f"{start:.3f}",
            "dur_s": f"{dur:.3f}",
            "kick_in_window_s": f"{kick_in_window:.3f}",
            "kick_frame": kick_fr,
        })
        print("[OK]", dst.name)

print("Saved:", OUT_CSV)
