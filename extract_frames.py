import sys
from pathlib import Path
import av 
import csv

video_path = Path(sys.argv[1])
output_dir = Path("outputs") / video_path.stem
output_dir.mkdir(parents=True ,exist_ok=True)

with av.open(str(video_path)) as container:
    next_sample_s = 0
    rows = []

    for frame in container.decode(video=0):
        timestamp_s = frame.time

        if timestamp_s is not None and timestamp_s >= next_sample_s:
            image_path = output_dir / f"frame_{next_sample_s:04d}.jpg"
            print(f"{timestamp_s:.3f}")
            frame.to_image().save(image_path)
            rows.append([Path(sys.argv[1]).stem, timestamp_s, image_path.as_posix()])
            next_sample_s = int(timestamp_s) + 1
    with (output_dir / "frames.csv").open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["video_id", "timestamp_s", "frame_path"])
        writer.writerows(rows)
        
