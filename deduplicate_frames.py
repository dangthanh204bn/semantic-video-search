import csv
import cv2
import sys
from pathlib import Path

last_kept = None
last_kept_path = None
outputs_rows = []
with open(sys.argv[1], newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        current = cv2.imread(row["frame_path"], cv2.IMREAD_GRAYSCALE)

        if current is None:
            raise ValueError(f"Không đọc được ảnh: {row['frame_path']}")
        if last_kept is not None and cv2.absdiff(last_kept, current).mean() <= 3.0:
            decision = "REUSE"
        else:
            decision = "KEEP"
            last_kept_path = row["frame_path"]
            last_kept = current

        row["decision"] = decision
        row["representative_frame_path"] = last_kept_path
        outputs_rows.append(row)

    output_path = Path(sys.argv[1]).with_name("frames_dedup.csv")
    columns = [
        "video_id", "timestamp_s", "frame_path",
        "decision", "representative_frame_path",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(outputs_rows)