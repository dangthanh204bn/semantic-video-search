import csv
import cv2
import sys

last_kept = None
with open(sys.argv[1], newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        current = cv2.imread(row["frame_path"], cv2.IMREAD_GRAYSCALE)

        if current is None:
            raise ValueError(f"Không đọc được ảnh: {row['frame_path']}")
        if last_kept is not None and cv2.absdiff(last_kept, current).mean() <= 3.0:
            decision = "REUSE"
        else:
            decision = "KEEP"
            last_kept = current

        print(row["timestamp_s"], decision)