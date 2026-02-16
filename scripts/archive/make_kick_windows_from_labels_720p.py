import argparse, csv, subprocess
from pathlib import Path

def ffmpeg_cut(in_path: Path, out_path: Path, start_s: float, dur_s: float):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-ss", f"{start_s:.6f}",
        "-t", f"{dur_s:.6f}",
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="data/meta/kick_moments_720p.csv")
    ap.add_argument("--out_dir", default="data/clips/kick_windows_720p")
    ap.add_argument("--pre", type=float, default=1.5)
    ap.add_argument("--post", type=float, default=2.5)
    args = ap.parse_args()

    labels = Path(args.labels)
    out_dir = Path(args.out_dir)
    out_index = out_dir / "kick_windows_index.csv"

    rows = []
    with labels.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if not row.get("kick_time_s"):
                continue
            rows.append(row)

    if not rows:
        raise SystemExit("No labeled kick_time_s found in labels CSV.")

    out_dir.mkdir(parents=True, exist_ok=True)
    with out_index.open("w", newline="", encoding="utf-8") as f_out:
        w = csv.DictWriter(f_out, fieldnames=["clip_name", "src_clip", "kick_time_s", "out_clip"])
        w.writeheader()

        ok = 0
        for row in rows:
            src = Path(row["clip_path"])
            kick_t = float(row["kick_time_s"])
            start = max(0.0, kick_t - args.pre)
            dur = args.pre + args.post

            out_name = src.stem + "_KICK.mp4"
            out_path = out_dir / out_name

            ffmpeg_cut(src, out_path, start, dur)
            w.writerow({
                "clip_name": row["clip_name"],
                "src_clip": str(src),
                "kick_time_s": f"{kick_t:.6f}",
                "out_clip": str(out_path),
            })
            ok += 1
            print(f"[OK] {out_name}")

    print(f"Done. Created {ok} kick windows at {out_dir}")

if __name__ == "__main__":
    main()
