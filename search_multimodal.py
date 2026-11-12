import sys
from search_frames import find_frames
from search_transcript import find_transcript


def overlaps(visual_hit, speech_hit):
    return (
        visual_hit["video_id"] == speech_hit["video_id"]
        and visual_hit["start_s"] <= speech_hit["end_s"]
        and speech_hit["start_s"] <= visual_hit["end_s"]
    )

if __name__ == "__main__":
    image_path, _, visual_hits = find_frames(sys.argv[1], sys.argv[3])
    speech_hit = find_transcript(sys.argv[2], sys.argv[4])

    matches = [hit for hit in visual_hits if overlaps(hit, speech_hit)]

    if matches:
        print(f"{speech_hit['video_id']} {speech_hit['start_s']:.2f} - {speech_hit['end_s']:.2f} giây")
        for hit in matches:
            print(f"Ảnh ở {hit['start_s']:.3f} giây {image_path}")
        print(speech_hit["text"])
    else:
        print("Không tìm thấy kết quả giao thời gian.")