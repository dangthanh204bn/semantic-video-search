import numpy as np
import sys

from sentence_transformers import SentenceTransformer

def find_transcripts(index_path, query, top_k=3):
    model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    query_embedding = model.encode("query: " + query, normalize_embeddings=True)

    with np.load(index_path, allow_pickle=False) as archive:
        scores = archive["embeddings"] @ query_embedding
        ranked_indices = np.argsort(-scores, kind="stable")[:top_k]

        hits = []
        for index in ranked_indices:
            hits.append({
                "video_id": str(archive["video_ids"][index]),
                "start_s": float(archive["start_s"][index]),
                "end_s": float(archive["end_s"][index]),
                "text": str(archive["texts"][index])
            })
        return hits

def find_transcript(index_path, query):
    return find_transcripts(index_path, query, top_k=1)[0]

if __name__ == "__main__":
    hit = find_transcript(sys.argv[1], sys.argv[2])
    print(hit["video_id"], hit["start_s"], hit["end_s"])
    print(hit["text"])