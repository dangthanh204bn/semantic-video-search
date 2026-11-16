# Semantic Video Search & Video RAG

[English](#english) · [Tiếng Việt](#tieng-viet)

## English

A local video search demo that finds moments from Vietnamese or English descriptions, answers questions from Vietnamese speech, and opens the corresponding timestamp in the right video.

| Mode | What it does |
| --- | --- |
| **Tìm cảnh** | Search the frames of one video or the entire demo library. Results link directly to their timestamps. |
| **Hỏi** | Ask about a selected video. Qwen answers from its Vietnamese transcript and the app displays timestamped sources. |
| **Ghép hình và lời thoại** | Find overlapping visual and transcript matches in the selected video. Enter a single query or provide separate wording for the speech search. |

### Run locally on Windows

Use Python 3.12. Install [Ollama for Windows](https://docs.ollama.com/windows) for the **Hỏi** mode. Open PowerShell in the folder where you want the repository.

```powershell
git clone https://github.com/dangthanh204bn/semantic-video-search.git
Set-Location -LiteralPath '.\semantic-video-search'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
ollama pull qwen3:4b
```

The first indexing and search runs download the required Hugging Face models. Ollama serves Qwen locally at `127.0.0.1:11434`.

#### Index videos

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

#### Start the app

```powershell
.\.venv\Scripts\python.exe -X utf8 .\app.py
```

Open [the local demo](http://127.0.0.1:5000/). Select a video or **Tất cả video**, enter a description of a scene in your clips, and click **Tìm cảnh**. Click a result to open the source video and seek to that moment.

For **Hỏi** or **Ghép hình và lời thoại**, select a video with a transcript index. For **Hỏi**, enter a question about its speech. For combined search, enter a scene description and optionally provide separate speech wording. With **Tất cả video** selected, both speech modes use `speech.webm`.

You can also search a single image index directly from PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\search_frames.py .\outputs\sample\image_embeddings.npz "Describe a scene in your video"
```

#### Ask about a selected video through the API

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

### How it works

- **Visual pipeline.** PyAV samples timestamped frames. OpenCV groups similar frames and CLIP embeds the representatives. The search API encodes a query once, compares it across the selected indexes, filters weak results and suppresses nearby timestamps within each video.
- **Speech pipeline.** Faster-Whisper produces timestamped Vietnamese transcript segments. Multilingual E5 retrieves relevant segments. Qwen3 4B via Ollama generates an answer and selects evidence IDs. Python resolves the IDs to the original source timestamps.
- **Playback.** Flask serves the video library and supports byte-range requests. The browser uses the result's video ID to select the file and seek to the supplied timestamp.

Visual search uses the discovered library. Visual matches depend on the sampled frames and similarity threshold, so short actions can fall between samples.

---

<a name="tieng-viet"></a>

## Tiếng Việt

Ứng dụng chạy cục bộ để tìm các đoạn video bằng mô tả tiếng Việt hoặc tiếng Anh, trả lời câu hỏi dựa trên lời thoại tiếng Việt và mở đúng video tại mốc thời gian của kết quả.

| Chế độ | Chức năng |
| --- | --- |
| **Tìm cảnh** | Tìm theo hình ảnh trong một video hoặc toàn bộ thư viện demo. Bấm kết quả để tua đến mốc tìm được. |
| **Hỏi** | Đặt câu hỏi về video đã chọn. Qwen trả lời dựa trên bản chép lời tiếng Việt của video và ứng dụng hiển thị các đoạn nguồn kèm mốc thời gian. |
| **Ghép hình và lời thoại** | Tìm các kết quả hình ảnh và lời thoại có khoảng thời gian giao nhau trong video đã chọn. Bạn có thể dùng chung một truy vấn hoặc nhập riêng nội dung cần tìm trong lời thoại. |

### Chạy cục bộ trên Windows

Dùng Python 3.12. Cài [Ollama cho Windows](https://docs.ollama.com/windows) để dùng chế độ **Hỏi**. Mở PowerShell tại thư mục bạn muốn tải dự án về.

```powershell
git clone https://github.com/dangthanh204bn/semantic-video-search.git
Set-Location -LiteralPath '.\semantic-video-search'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
ollama pull qwen3:4b
```

Trong lần đầu lập chỉ mục và tìm kiếm, ứng dụng tải các mô hình cần thiết từ Hugging Face. Ollama chạy Qwen cục bộ tại `127.0.0.1:11434`.

#### Lập chỉ mục video

Đặt các tệp MP4 hoặc WebM vào thư mục gốc của dự án. Chạy lệnh lập chỉ mục ảnh một lần cho mỗi tệp và dùng đúng tên tệp. Thử với `sample.mp4`.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\sample.mp4
```

Khi khởi động, Flask tự nhận các video đã có đủ dữ liệu chỉ mục ảnh. Khởi động lại Flask sau khi lập chỉ mục cho video mới. Đặt tên gốc khác nhau cho mỗi video. Phần tên trước đuôi tệp được dùng làm mã video và tên thư mục đầu ra. Mã `all` dành cho tìm kiếm toàn thư viện. Video nguồn và các tệp chỉ mục được lưu trên máy của bạn.

Để chuẩn bị video mặc định cho các chế độ dùng lời thoại, đặt một video có lời thoại tiếng Việt với tên `speech.webm`. Cờ `--with-transcript` tạo chỉ mục ảnh và chỉ mục lời thoại trong cùng một lần chạy.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\speech.webm --with-transcript
```

Script tạo một thư mục riêng trong `outputs/` cho mỗi tên video. Khi dùng `--with-transcript`, script chép lời từ luồng âm thanh vào `transcript.csv`. Nếu tìm thấy lời thoại, script tạo thêm `transcript_embedding.npz`. Video không có luồng âm thanh vẫn được lập chỉ mục ảnh.

Để bổ sung lời thoại cho video đã có chỉ mục ảnh, chạy trực tiếp hai script xử lý lời thoại.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\transcribe_video.py .\speech.webm
.\.venv\Scripts\python.exe -X utf8 .\embed_transcript.py .\outputs\speech\transcript.csv
```

#### Khởi động ứng dụng

```powershell
.\.venv\Scripts\python.exe -X utf8 .\app.py
```

Mở [trang demo cục bộ](http://127.0.0.1:5000/). Chọn một video hoặc **Tất cả video**, nhập mô tả về một cảnh trong các video của bạn rồi bấm **Tìm cảnh**. Bấm một kết quả để mở đúng video và tua tới mốc tương ứng.

Với **Hỏi** hoặc **Ghép hình và lời thoại**, chọn video đã có chỉ mục lời thoại. Với **Hỏi**, nhập một câu hỏi về lời thoại. Với tìm kiếm kết hợp, nhập mô tả cảnh và điền nội dung lời thoại riêng nếu cần. Khi chọn **Tất cả video**, cả hai chế độ dùng lời thoại đều lấy `speech.webm` làm mặc định.

Bạn cũng có thể tìm trực tiếp trong một chỉ mục ảnh từ PowerShell.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\search_frames.py .\outputs\sample\image_embeddings.npz "Mô tả một cảnh trong video của bạn"
```

#### Hỏi về một video qua API

Khi Flask đang chạy, gửi câu hỏi và mã video. Mã video là tên tệp bỏ phần mở rộng của một video trong thư viện. Tạo chỉ mục lời thoại cho video bằng `--with-transcript` trước khi gửi câu hỏi.

```powershell
$body = @{ question = 'Nên chà tay trong bao nhiêu giây?'; video_id = 'speech' } | ConvertTo-Json
$answer = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:5000/api/answer' `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$answer.answer
$answer.sources | Select-Object video_id, start_s, end_s
```

Khi bỏ qua `video_id`, API dùng `speech`. Với video có trong thư viện nhưng thiếu chỉ mục lời thoại, API trả HTTP `404`.

### Cách hoạt động

- **Luồng hình ảnh.** PyAV lấy mẫu các khung hình kèm mốc thời gian. OpenCV nhóm các khung hình tương tự và CLIP mã hóa khung hình đại diện. API mã hóa truy vấn một lần, so sánh vector với các chỉ mục được chọn, lọc kết quả có điểm thấp và loại các mốc quá gần nhau trong cùng một video.
- **Luồng lời thoại.** Faster-Whisper tạo các đoạn chép lời tiếng Việt kèm mốc thời gian. Multilingual E5 truy xuất các đoạn liên quan. Qwen3 4B chạy qua Ollama để tạo câu trả lời và chọn mã đoạn nguồn. Python tra lại các mã đó để lấy mốc thời gian gốc.
- **Phát video.** Flask phục vụ thư viện video và hỗ trợ yêu cầu tải từng phần tệp. Trình duyệt dùng mã video của kết quả để mở đúng tệp và tua tới mốc được trả về.

Tìm kiếm hình ảnh chạy trên thư viện do Flask phát hiện. Kết quả phụ thuộc vào các khung hình được lấy mẫu và ngưỡng tương đồng. Một hành động rất ngắn có thể xảy ra giữa hai khung hình được lấy mẫu.
