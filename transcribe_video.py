import sys
import csv
from pathlib import Path
from faster_whisper import WhisperModel

video_path = Path(sys.argv[1])
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(sys.argv[1], language="vi", vad_filter=True)

output_dir = Path("outputs") / video_path.stem
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "transcript.csv"

with output_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["video_id","start_s","end_s","text"])

    for segment in segments:
        writer.writerow([
            video_path.stem,
            segment.start,
            segment.end,
            segment.text.strip(),
        ])
