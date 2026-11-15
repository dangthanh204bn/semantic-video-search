import sys
import csv
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_frame_query_model():
    return SentenceTransformer(
        "sentence-transformers/clip-ViT-B-32-multilingual-v1",
        device="cpu",
    )

def encode_frame_query(query):
    model = get_frame_query_model()
    return model.encode(query, normalize_embeddings=True)

def find_frame_candidates(index_path, query, top_k=3):
    query_embedding = encode_frame_query(query)
    return find_frame_candidates_by_embedding(
        index_path, query_embedding, top_k=top_k
    )
def find_frame_candidates_by_embedding(index_path, query_embedding, top_k=3):
    with np.load(index_path, allow_pickle=False) as archive:
        image_paths = archive["image_paths"]
        embeddings = archive["embeddings"]

    scores = embeddings @ query_embedding

    ranked_indices = np.argsort(-scores, kind="stable")[:top_k]

    manifest_path = Path(index_path).with_name("frames_dedup.csv")
    with manifest_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    candidates = []
    for index in ranked_indices:
        image_path = str(image_paths[index])
        candidates.append({
            "image_path": image_path,
            "score": float(scores[index]),
            "hits": group_frame_hits(rows, image_path),
        })
    return candidates

def find_frames(index_path, query):
    best = find_frame_candidates(index_path, query, top_k=1)[0]
    return best["image_path"], best["score"], best["hits"]

def group_frame_hits(rows, image_path):
    matches = [
        row for row in rows
        if row["representative_frame_path"] == image_path
    ]
    if not matches:
        return []
    video_id = matches[0]["video_id"]
    timestamps = sorted(float(row["timestamp_s"]) for row in matches)
    hits = []
    start = end = timestamps[0]

    for timestamp in timestamps[1:]:
        if timestamp - end > 1.5:
            hits.append({"video_id": video_id, "start_s": start, "end_s": end})
            start = timestamp
        end = timestamp
    hits.append({"video_id": video_id, "start_s": start, "end_s":end})
    return hits

if __name__ == "__main__":
    best_path, best_score, hits = find_frames(sys.argv[1], sys.argv[2])
    print(f"{best_path} {best_score:.4f}")
    for hit in hits:
        print(f"{hit['start_s']:.3f}-{hit['end_s']:.3f} giây")