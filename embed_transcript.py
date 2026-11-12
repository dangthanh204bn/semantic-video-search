import csv
import sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer


with open(sys.argv[1], newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
passages = ["passage: "+ row["text"] for row in rows]
embeddings = model.encode(passages, normalize_embeddings = True)

output_path = Path(sys.argv[1]).with_name("transcript_embedding.npz")

np.savez(
    output_path,
    embeddings=embeddings,
    video_ids = np.asarray([row["video_id"] for row in rows], dtype=str),
    start_s = np.asarray([float(row["start_s"]) for row in rows]),
    end_s = np.asarray([float(row["end_s"]) for row in rows]),
    texts=np.asarray([row["text"] for row in rows], dtype=str)
)
print(output_path, embeddings.shape)