import sys
from search_frames import find_frame_candidates
from search_transcript import find_transcripts
import numpy as np


def overlaps(visual_hit, speech_hit):
    return (
        visual_hit["video_id"] == speech_hit["video_id"]
        and visual_hit["start_s"] <= speech_hit["end_s"]
        and speech_hit["start_s"] <= visual_hit["end_s"]
    )

def find_overlapping_hits(visual_candidates, speech_hits):
    groups = []

    for rank, speech_hit in enumerate(speech_hits, start=1):
        matches = []

        for candidate in visual_candidates:
            for visual_hit in candidate["hits"]:
                if overlaps(visual_hit, speech_hit):
                    matches.append({
                        "start_s":max(visual_hit["start_s"], speech_hit["start_s"]),
                        "end_s": min(visual_hit["end_s"], speech_hit["end_s"]),
                        "image_path": candidate["image_path"],
                    })
        if matches:
            groups.append({
                "rank": rank,
                "speech_hit": speech_hit,
                "matches": matches,
            })
    return groups

if __name__ == "__main__":
    visual_candidates = find_frame_candidates(sys.argv[1], sys.argv[3], top_k=3)
    speech_hits = find_transcripts(sys.argv[2], sys.argv[4], top_k=3)


    groups = find_overlapping_hits(visual_candidates, speech_hits)

    if not groups:
        print("Không tìm thấy đoạn nào khớp cả hình ảnh và lời thoại.")

    for group in groups:
        speech_hit = group["speech_hit"]
        print(f"Hạng lời thoại: {group['rank']}")
        print(f"{speech_hit['video_id']} {speech_hit['start_s']:.2f}-{speech_hit['end_s']:.2f} giây")

        for match in group["matches"]:
            print(f"Khoảng giao {match['start_s']:.3f}-{match['end_s']:.3f} giây")
            print(f"Ảnh đại diện {match['image_path']}")
