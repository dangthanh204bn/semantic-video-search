# Semantic Video Search & Video RAG

A local video search demo that finds moments from Vietnamese or English descriptions, answers questions from Vietnamese speech, and opens the corresponding timestamp in the right video.

| Mode | What it does |
| --- | --- |
| **Tìm cảnh** | Search the frames of one video or the entire demo library. Results link directly to their timestamps. |
| **Hỏi** | Ask about a selected video. Qwen answers from its Vietnamese transcript and the app displays timestamped sources. |
| **Ghép hình và lời thoại** | Find overlapping visual and transcript matches in the selected video. Enter a single query or provide separate wording for the speech search. |

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

Place MP4 or WebM files in the repository root. Run the image indexer once for each file using its actual name. For example, start with `sample.mp4`.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\sample.mp4
```

Flask discovers videos with a complete image index at startup. Restart Flask after indexing a new video. Use distinct filename stems for your clips because each stem is a video ID and identifies an output directory. The ID `all` is reserved for the library-wide search. Source videos and generated indexes stay local.

For the default video used by the speech modes, place a clip with Vietnamese speech at `speech.webm`. Use `--with-transcript` to build its visual index and transcript index together.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\speech.webm --with-transcript
```

The indexer creates a new directory under `outputs/` for each video stem. With `--with-transcript`, an audio track is transcribed to `transcript.csv`. When the transcript contains speech, the indexer also creates `transcript_embedding.npz`. A clip without an audio track produces the visual index.

To add a transcript to an existing visual index, run the speech scripts directly.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\transcribe_video.py .\speech.webm
.\.venv\Scripts\python.exe -X utf8 .\embed_transcript.py .\outputs\speech\transcript.csv
```

### Start the app

```powershell
.\.venv\Scripts\python.exe -X utf8 .\app.py
```

Open [the local demo](http://127.0.0.1:5000/). Select a video or **Tất cả video**, enter a description of a scene in your clips, and click **Tìm cảnh**. Click a result to open the source video and seek to that moment.

For **Hỏi** or **Ghép hình và lời thoại**, select a video with a transcript index. For **Hỏi**, enter a question about its speech. For combined search, enter a scene description and optionally provide separate speech wording. With **Tất cả video** selected, both speech modes use `speech.webm`.

You can also search a single image index directly from PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\search_frames.py .\outputs\sample\image_embeddings.npz "Describe a scene in your video"
```

### Ask about a selected video through the API

With Flask running, send a question and the video ID. The ID is the filename stem of a video in the library. Create its transcript index with `--with-transcript` first.

```powershell
$body = @{ question = 'Nên chà tay trong bao nhiêu giây?'; video_id = 'speech' } | ConvertTo-Json
$answer = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:5000/api/answer' `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$answer.answer
$answer.sources | Select-Object video_id, start_s, end_s
```

Omitting `video_id` selects `speech`. A video in the library without a transcript index returns HTTP `404`.

## How it works

- **Visual pipeline.** PyAV samples timestamped frames. OpenCV groups similar frames and CLIP embeds the representatives. The search API encodes a query once, compares it across the selected indexes, filters weak results and suppresses nearby timestamps within each video.
- **Speech pipeline.** Faster-Whisper produces timestamped Vietnamese transcript segments. Multilingual E5 retrieves relevant segments. Qwen3 4B via Ollama generates an answer and selects evidence IDs. Python resolves the IDs to the original source timestamps.
- **Playback.** Flask serves the video library and supports byte-range requests. The browser uses the result's video ID to select the file and seek to the supplied timestamp.

Visual search uses the discovered library. Visual matches depend on the sampled frames and similarity threshold, so short actions can fall between samples.
