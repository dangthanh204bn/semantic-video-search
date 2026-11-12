import numpy as np
import sys

from sentence_transformers import SentenceTransformer

def find_transcript(index_path, query):
    model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    query_embedding = model.encode("query: " + query, normalize_embeddings=True)

    with np.load(index_path, allow_pickle=False) as archive:
        scores = archive["embeddings"] @ query_embedding
        best_index = int(scores.argmax())

        return {
            "video_id": str(archive["video_ids"][best_index]),
            "start_s": float(archive["start_s"][best_index]),
            "end_s": float(archive["end_s"][best_index]),
            "text": str(archive["texts"][best_index])
        }
if __name__ == "__main__":
    hit = find_transcript(sys.argv[1], sys.argv[2])
    print(hit["video_id"], hit["start_s"], hit["end_s"])
    print(hit["text"])