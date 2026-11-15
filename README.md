# Semantic Video Search & Video RAG

A local video search demo that finds moments from Vietnamese or English descriptions, answers questions from Vietnamese speech, and opens the corresponding timestamp in the right video.

| Mode | What it does |
| --- | --- |
| **Tìm cảnh** | Search the frames of one video or the entire demo library. Results link directly to their timestamps. |
| **Hỏi** | Retrieve Vietnamese transcript segments, have Qwen answer from them, and display timestamped sources. |
| **Ghép hình và lời thoại** | Find overlapping visual and transcript matches in the same video. Enter a single query or provide separate wording for the speech search. |

## Run locally on Windows

Use Python 3.12. Install [Ollama for Windows](https://docs.ollama.com/windows) for the **Hỏi** mode. Open PowerShell in the folder where you want the repository.

```powershell
git clone https://github.com/dangthanh204bn/semantic-video-search.git
Set-Location -LiteralPath '.\semantic-video-search'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
ollama pull qwen3:4b
```

The first indexing and search runs download the required Hugging Face models. Ollama serves Qwen locally at `127.0.0.1:11434`.

### Index videos

Place three local videos in the repository root using the filenames below. Use a video with Vietnamese speech for `speech.webm` and any two MP4 clips for visual search. Keep source videos and generated indexes on your machine.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\speech.webm
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\static.mp4
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\sample.mp4

.\.venv\Scripts\python.exe -X utf8 .\transcribe_video.py .\speech.webm
.\.venv\Scripts\python.exe -X utf8 .\embed_transcript.py .\outputs\speech\transcript.csv
```

Run the visual indexing commands first. The indexer creates a new directory under `outputs/` for each video stem. The transcript steps then write into `outputs/speech/`.

### Start the app

```powershell
.\.venv\Scripts\python.exe -X utf8 .\app.py
```

Open [the local demo](http://127.0.0.1:5000/). Select a video or **Tất cả video**, enter a description of a scene in your clips, and click **Tìm cảnh**. Click a result to open the source video and seek to that moment. For **Hỏi**, enter a question about the speech in `speech.webm`.

You can also search a single image index directly from PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\search_frames.py .\outputs\sample\image_embeddings.npz "Describe a scene in your video"
```

## How it works

- **Visual pipeline.** PyAV samples timestamped frames. OpenCV groups similar frames and CLIP embeds the representatives. The search API encodes a query once, compares it across the selected indexes, filters weak results and suppresses nearby timestamps within each video.
- **Speech pipeline.** Faster-Whisper produces timestamped Vietnamese transcript segments. Multilingual E5 retrieves relevant segments. Qwen3 4B via Ollama generates an answer and selects evidence IDs. Python resolves the IDs to the original source timestamps.
- **Playback.** Flask serves the video library and supports byte-range requests. The browser uses the result's video ID to select the file and seek to the supplied timestamp.

The current web demo uses all three clips for visual search. The speech modes use `speech.webm`. Visual matches depend on the sampled frames and similarity threshold, so short actions can fall between samples.
