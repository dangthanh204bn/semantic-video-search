from pathlib import Path
from search_multimodal import find_overlapping_hits
from search_transcript import find_transcripts
from flask import Flask, jsonify, request, send_file, url_for
from search_frames import (
    encode_frame_query,
    find_frame_candidates,
    find_frame_candidates_by_embedding,
)
from video_rag import answer_question

app = Flask(__name__)
project_dir = Path(__file__).resolve().parent

@app.get("/")
def home():
    return send_file(project_dir / "seek_demo.html")

@app.get("/api/videos")
def list_videos():
    videos = [
        {
            "video_id": video_id,
            "filename": path.name,
            "url": url_for("play_video", video_id=video_id),
        }
        for video_id, path in video_files.items()
    ]
    return jsonify(videos=videos)

@app.get("/videos/<video_id>")
def play_video(video_id):
    path = video_files.get(video_id)
    if path is None or not path.is_file():
        return jsonify(error="Không tìm thấy video."), 404

    return send_file(path, conditional=True)

@app.get("/speech.webm")
def speech_video():
    return play_video("speech")

@app.get("/static.mp4")
def static_video():
    return play_video("static")

@app.get("/sample.mp4")
def sample_video():
    return play_video("sample")

@app.post("/api/answer")
def api_answer():
    body = request.get_json(silent=True)
    question = body.get("question") if isinstance(body, dict) else None

    if not isinstance(question, str) or not question.strip():
        return jsonify(error= "Bạn cần nhập câu hỏi"), 400

    video_id = body.get("video_id", "speech")
    if not isinstance(video_id, str) or video_id not in video_files:
        return jsonify(error="video không có trong danh sách."), 400

    transcript_index = project_dir / "outputs" / video_id / "transcript_embedding.npz"
    if not transcript_index.is_file():
        return jsonify(error="video chưa có chỉ mục lời thoại."), 404

    result = answer_question(transcript_index, question.strip())
    return jsonify(result)

def discover_index_videos(root):
    files_by_stem = {}
    media_paths = sorted(
        root.iterdir(),
        key=lambda path: (path.stem.casefold() != "speech", path.name.casefold()),
    )
    for path in media_paths:
        if not path.is_file() or path.suffix.lower() not in {".mp4", ".webm"}:
            continue

        stem = path.stem.casefold()
        if stem != "all":
            files_by_stem.setdefault(stem, []).append(path)

    videos = {}
    for paths in files_by_stem.values():
        if len(paths) != 1:
            continue

        path = paths[0]
        index_dir = root / "outputs" / path.stem
        if (
            (index_dir / "image_embeddings.npz").is_file()
            and (index_dir / "frames_dedup.csv").is_file()
        ):
            videos[path.stem] = path

    return videos


video_files = discover_index_videos(project_dir)

image_index_paths = {
    video_id: project_dir / "outputs" / video_id / "image_embeddings.npz"
    for video_id in video_files
}

image_score_threshold = 0.28

def suppress_nearby_hits(hits, min_gap_s=5.0):
    kept = []

    for hit in sorted(hits, key=lambda item: item["score"], reverse=True):
        too_close = any(
            hit["video_id"] == previous["video_id"]
            and abs(hit["start_s"] - previous["start_s"]) < min_gap_s
            for previous in kept
        )
        if not too_close:
            kept.append(hit)
    return kept

@app.post("/api/search-frames")
def api_search_frames():
    body = request.get_json(silent=True)
    query = body.get("query") if isinstance(body, dict) else None

    if not isinstance(query, str) or not query.strip():
        return jsonify(error="Bạn cần nhập mô tả hình ảnh."), 400

    video_id = body.get("video_id", "speech")
    if video_id == "all":
        selected_paths = image_index_paths.values()
    elif isinstance(video_id, str) and video_id in image_index_paths:
        selected_paths = [image_index_paths[video_id]]
    else:
        return jsonify(error="Video không có chỉ mục hình ảnh."), 400

    if not selected_paths:
        return jsonify(hits=[])

    query_embedding = encode_frame_query(query.strip())
    hits = []
    for selected_path in selected_paths:
        candidates = find_frame_candidates_by_embedding(
            selected_path, query_embedding, top_k=3
        )
        for candidate in candidates:
            if candidate["score"] < image_score_threshold:
                continue

            for hit in candidate["hits"]:
                hits.append({**hit, "score": candidate["score"]})

    return jsonify(hits=suppress_nearby_hits(hits))

@app.post("/api/search-multimodal")
def api_search_multimodal():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Bạn cần nhập mô tả hình ảnh và lời thoại."), 400

    visual_query = body.get('visual_query')
    speech_query = body.get("speech_query")
    if (
        not isinstance(visual_query, str) or not visual_query.strip()
        or not isinstance(speech_query, str) or not speech_query.strip()
    ):
        return jsonify(error="Bạn cần nhập mô tả hình ảnh và lời thoại."), 400

    if "video_id" not in body and "speech" not in image_index_paths:
        return jsonify(groups=[])

    video_id = body.get("video_id", "speech")
    if not isinstance(video_id, str) or video_id not in image_index_paths:
        return jsonify(error="Video không có trong danh sách."), 400

    visual_index = image_index_paths[video_id]
    transcript_index = visual_index.with_name("transcript_embedding.npz")
    if not transcript_index.is_file():
        return jsonify(error="Video chưa có chỉ mục lời thoại."), 404

    visual_candidates = find_frame_candidates(
        visual_index, visual_query.strip(), top_k=3
    )
    visual_candidates = [
        candidate for candidate in visual_candidates
        if candidate["score"] >= image_score_threshold
    ]
    if not visual_candidates:
        return jsonify(groups = [])

    speech_hits = find_transcripts(transcript_index, speech_query.strip(), top_k=3)
    groups = find_overlapping_hits(visual_candidates, speech_hits)
    return jsonify(groups=groups)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
