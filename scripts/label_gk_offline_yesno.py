import csv
from pathlib import Path
import cv2

INDEX = Path("data/meta/kick_windows.csv")
OUT   = Path("data/meta/gk_offline_labels.csv")

def get_kick_frame(cap, kick_in_window_s):
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    kf = int(round(kick_in_window_s * fps))
    return kf, fps

rows = []
with INDEX.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    rows = list(r)

done = {}
if OUT.exists() and OUT.stat().st_size > 0:
    with OUT.open(newline="", encoding="utf-8") as f:
        rr = csv.DictReader(f)
        for x in rr:
            done[x["window_file"]] = x

with OUT.open("w", newline="", encoding="utf-8") as g:
    fieldnames = ["window_file","clip_name","kick_in_window_s","kick_frame_window","fps","violation","note"]
    w = csv.DictWriter(g, fieldnames=fieldnames)
    w.writeheader()

    # keep previous labels
    for k, x in done.items():
        w.writerow(x)

    for i, row in enumerate(rows, start=1):
        vid = row["window_file"].replace("/","\\")
        if vid in done:
            continue

        kick_in = float(row["kick_in_window_s"])

        cap = cv2.VideoCapture(vid)
        if not cap.isOpened():
            print("[SKIP cannot open]", vid)
            continue

        kf, fps = get_kick_frame(cap, kick_in)
        cap.set(cv2.CAP_PROP_POS_FRAMES, kf)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            print("[SKIP cannot read frame]", vid)
            continue

        txt = "y=violation  n=legal  s=skip  q=quit"
        cv2.putText(frame, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"{i}/{len(rows)}  kick_frame={kf}  fps={fps:.2f}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow("GK Goal-line label (kick frame)", frame)
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()

        if key == ord("q"):
            break
        if key == ord("s"):
            continue
        if key not in (ord("y"), ord("n")):
            print("Unknown key -> skipped")
            continue

        violation = 1 if key == ord("y") else 0
        outrow = {
            "window_file": row["window_file"],
            "clip_name": row["clip_name"],
            "kick_in_window_s": row["kick_in_window_s"],
            "kick_frame_window": str(kf),
            "fps": f"{fps:.3f}",
            "violation": str(violation),
            "note": "",
        }
        w.writerow(outrow)
        g.flush()
        done[vid] = outrow
        print("[LABELED]", Path(vid).name, "violation=" + str(violation))

print("Saved:", OUT)
