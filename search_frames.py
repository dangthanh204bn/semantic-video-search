import sys
import csv
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

def find_frames(index_path, query):
    with np.load(index_path, allow_pickle=False) as archive:
        image_paths = archive["image_paths"]
        embeddings = archive["embeddings"]

    model = SentenceTransformer(
        "sentence-transformers/clip-ViT-B-32-multilingual-v1",
        device="cpu"
    )
    query_embedding = model.encode(query, normalize_embeddings=True)

    scores = embeddings @ query_embedding
    best_index = int(scores.argmax())
    best_path = str(image_paths[best_index])
    best_score = float(scores[best_index])

    manifest_path = Path(index_path).with_name("frames_dedup.csv")
    with manifest_path.open(newline="", encoding="utf-8") as file:
        matches = [
            row for row in csv.DictReader(file)
            if row["representative_frame_path"] == best_path
        ]

    if not matches:
        return best_path, best_score, []

    video_id = matches[0]["video_id"]
    timestamps = sorted(float(row["timestamp_s"]) for row in matches)
    hits = []
    start = end = timestamps[0]

    for timestamp in timestamps[1:]:
        if timestamp -end > 1.5:
            hits.append({"video_id": video_id, "start_s": start, "end_s": end})
            start = timestamp
        end = timestamp

    hits.append({"video_id": video_id, "start_s": start, "end_s": end})
    return best_path, best_score, hits

if __name__ == "__main__":
    best_path, best_score, hits = find_frames(sys.argv[1], sys.argv[2])
    print(f"{best_path} {best_score:.4f}")
    for hit in hits:
        print(f"{hit['start_s']:.3f}-{hit['end_s']:.3f} giây")