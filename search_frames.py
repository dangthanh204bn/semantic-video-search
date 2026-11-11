import sys
import csv
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer


with np.load(sys.argv[1], allow_pickle=False) as archive:
    image_paths = archive["image_paths"]
    embeddings = archive["embeddings"]

model = SentenceTransformer(
    "sentence-transformers/clip-ViT-B-32-multilingual-v1",
    device="cpu"
)
query_embedding = model.encode(sys.argv[2], normalize_embeddings=True)

scores = embeddings @ query_embedding
best_index = int(scores.argmax())
print(f"{image_paths[best_index]} {scores[best_index]:.4f}")

best_path = image_paths[best_index]
manifest_path = Path(sys.argv[1]).with_name("frames_dedup.csv")

with manifest_path.open(newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        if row["representative_frame_path"] == best_path:
            print(row["video_id"], row["timestamp_s"], row["decision"])