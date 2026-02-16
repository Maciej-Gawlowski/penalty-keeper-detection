import argparse
import csv
from pathlib import Path

import cv2


def draw_text(img, lines, x=10, y=25, dy=22):
    for i, s in enumerate(lines):
        cv2.putText(img, s, (x, y + i * dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, s, (x, y + i * dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Folder with .mp4 clips (e.g. data/clips/kick_windows_720p)")
    ap.add_argument("--out", required=True, help="Output CSV (e.g. data/meta/kick_moments_720p.csv)")
    ap.add_argument("--resume", action="store_true", help="Resume if CSV already exists")
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    clips = sorted(src.glob("*.mp4"))
    if not clips:
        raise SystemExit(f"No .mp4 found in {src}")

    done = set()
    if args.resume and out.exists():
        with out.open("r", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add(Path(r["clip_path"]).name)

    write_header = not out.exists() or out.stat().st_size == 0
    f_out = out.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f_out, fieldnames=["clip_path", "kick_time_s"])
    if write_header:
        writer.writeheader()

    for clip in clips:
        if clip.name in done:
            continue

        cap = cv2.VideoCapture(str(clip))
        if not cap.isOpened():
            print(f"[SKIP] cannot open {clip}")
            continue

        paused = False
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        delay_play = max(1, int(1000 / fps))

        print(f"\n[SHOW] {clip.name}")
        print("Controls: SPACE pause/play | K mark kick | J/L seek -1s/+1s | A/D seek -0.2s/+0.2s | Q quit")

        while True:
            if not paused:
                ok, frame = cap.read()
                if not ok:
                    # end of clip without label
                    print(f"[NO LABEL] {clip.name} (reached end)")
                    break

            t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            frame_show = frame.copy()

            draw_text(frame_show, [
                f"{clip.name}",
                f"time = {t:0.3f}s",
                "SPACE pause/play | K mark | J/L -1/+1s | A/D -0.2/+0.2s | Q quit",
            ])

            cv2.imshow("Label kick moment", frame_show)
            key = cv2.waitKey(0 if paused else delay_play) & 0xFF

            if key in (ord("q"), 27):  # q or ESC
                cap.release()
                f_out.close()
                cv2.destroyAllWindows()
                return

            if key == ord(" "):
                paused = not paused
                continue

            if key == ord("k"):
                writer.writerow({"clip_path": str(clip), "kick_time_s": f"{t:.3f}"})
                f_out.flush()
                print(f"[OK] {clip.name} kick_time_s={t:.3f}")
                break

            # --- SEEK HELPERS (frame-accurate for A/D) ---
            def read_current_frame_index():
                """
                After cap.read(), POS_FRAMES points to the *next* frame to be read.
                So the frame we are showing is (POS_FRAMES - 1).
                """
                return int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

            def seek_to_frame(frame_idx):
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frame_idx)))
                ok, fr = cap.read()
                return ok, fr

            def seek_to_time_sec(new_t):
                cap.set(cv2.CAP_PROP_POS_MSEC, max(0, float(new_t) * 1000.0))
                ok, fr = cap.read()
                return ok, fr

            # current displayed frame index (compute from capture)
            cur_idx = read_current_frame_index()

            if key == ord("j"):  # -1s
                ok, frame = seek_to_time_sec(t - 1.0)
                paused = True
                if not ok:
                    break
                continue

            if key == ord("l"):  # +1s
                ok, frame = seek_to_time_sec(t + 1.0)
                paused = True
                if not ok:
                    break
                continue

            if key == ord("a"):  # -1 frame EXACT
                ok, frame = seek_to_frame(cur_idx - 1)
                paused = True
                if not ok:
                    break
                continue

            if key == ord("d"):  # +1 frame EXACT
                ok, frame = seek_to_frame(cur_idx + 1)
                paused = True
                if not ok:
                    break
                continue

        cap.release()

    f_out.close()
    cv2.destroyAllWindows()
    print(f"\nSaved labels to: {out}")


if __name__ == "__main__":
    main()
