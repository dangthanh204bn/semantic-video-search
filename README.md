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

#### Download the demo videos

Save the downloads in the repository root under the filenames below. Start with `speech.webm` to try all three modes on one clip. The visual evaluation also uses the two MP4 clips.

| Save as | Source and creator | Download |
| --- | --- | --- |
| `speech.webm` | [SFDPH WASH HANDS VIETNAMESE](https://commons.wikimedia.org/wiki/File:20200303_-_SFGovTV_-_SFDPH_WASH_HANDS_VIETNAMESE.webm) by San Francisco Government Television, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) | [Original WebM](https://upload.wikimedia.org/wikipedia/commons/5/56/20200303_-_SFGovTV_-_SFDPH_WASH_HANDS_VIETNAMESE.webm) |
| `sample.mp4` | [Cars Waiting in a Traffic Light](https://www.pexels.com/video/cars-waiting-in-a-traffic-light-5675618/) by Erkan Avanoğlu, [Pexels License](https://www.pexels.com/license/) | [1920 × 1080 MP4](https://videos.pexels.com/video-files/5675618/5675618-hd_1920_1080_30fps.mp4) |
| `static.mp4` | [A Glass on the Table](https://www.pexels.com/video/a-glass-on-the-table-6801658/) by Artem Podrez, [Pexels License](https://www.pexels.com/license/) | [2160 × 3840 MP4](https://videos.pexels.com/video-files/6801658/6801658-uhd_2160_3840_30fps.mp4) |

#### Index videos

For the two additional clips used in the visual evaluation, generate their image indexes.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\sample.mp4
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\static.mp4
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

For **Tìm cảnh**, select **Thử tìm lại bằng tiếng Anh khi chưa thấy cảnh** to enable an English retry. If the original query returns an empty list, the app uses local Ollama with `qwen3:4b` and searches the selected video scope again when the translation differs from the original query. API clients can add `"translate_on_miss": true` to the JSON body for `POST /api/search-frames`. The response includes `translated_query` after a successful translation.

For **Hỏi** or **Ghép hình và lời thoại**, select a video with a transcript index. For **Hỏi**, enter a question about its speech. For combined search, enter a scene description and optionally provide separate speech wording. With **Tất cả video** selected, both speech modes use `speech.webm`.

With `speech.webm` selected, try these example queries.

| Mode | Input | Expected result on the demo clip |
| --- | --- | --- |
| **Tìm cảnh** | `Người mặc áo sọc đang rửa tay ở bồn inox` | Top result near **16.003 s** |
| **Ghép hình và lời thoại** | Same scene description, with `Chà tay ít nhất 20 giây` in the speech field | Frames near **16.003 s** and **17.003 s** within the matching speech segment |
| **Hỏi** | `Nên chà tay trong bao nhiêu giây?` | `Chà tay ít nhất 20 giây`, citing **15.08–22.08 s** |

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

### Visual search evaluation

The local evaluation compares the original wording, manually written English, and Ollama translations for seven cases across `speech.webm`, `static.mp4`, and `sample.mp4`. All three runs use the same expected clips and timestamps, a score threshold of `0.28`, and suppression of results whose start times are less than 5 seconds apart within the same video.

| Measure | Original (six Vietnamese, one English) | Manual English | Ollama translation |
| --- | --- | --- | --- |
| Queries with a matching scene and a hit in the top three | 4/5 | 5/5 | 5/5 |
| Queries with no matching scene and an empty result list | 1/2 | 1/2 | 1/2 |

A hit must identify the expected video and overlap the annotated time span. The original white tanker query missed the scene at **11.011–17.017 s** in `sample.mp4`. Both English versions ranked the matching frame at **13.013 s** first, with scores of **0.3315** for the manual wording and **0.3201** for the Ollama translation. The toothbrushing query returned handwashing frames in all three runs.

Keep Flask running for all three commands. `--auto-english` also needs local Ollama with `qwen3:4b` installed. In that mode, [the evaluation script](evaluate_visual_search.py) translates each query before submitting it to the search API.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py --english
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py --auto-english
```

### Video RAG evaluation

The local `speech.webm` evaluation checks answer content and exact source timestamps. **All three cases passed with `qwen3:4b`**, up from two of three before the prompt update. The short handwashing question now returns “at least 20 seconds” in Vietnamese and cites **15.08–22.08 s**. The two-part question cites both expected segments, and the question without evidence returns `answer: null` and `sources: []`.

With Flask and Ollama running, run [the Video RAG evaluation](evaluate_video_rag.py).

```powershell
.\.venv\Scripts\python.exe -X utf8 .\evaluate_video_rag.py
```

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

#### Tải video demo

Lưu các tệp tải về vào thư mục gốc dự án với đúng tên trong bảng. Dùng `speech.webm` để thử cả ba chế độ trên cùng một clip. Bộ đánh giá tìm kiếm hình ảnh sử dụng thêm hai clip MP4.

| Tên lưu | Nguồn và tác giả | Tệp tải về |
| --- | --- | --- |
| `speech.webm` | [SFDPH WASH HANDS VIETNAMESE](https://commons.wikimedia.org/wiki/File:20200303_-_SFGovTV_-_SFDPH_WASH_HANDS_VIETNAMESE.webm) của San Francisco Government Television, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) | [WebM gốc](https://upload.wikimedia.org/wikipedia/commons/5/56/20200303_-_SFGovTV_-_SFDPH_WASH_HANDS_VIETNAMESE.webm) |
| `sample.mp4` | [Cars Waiting in a Traffic Light](https://www.pexels.com/video/cars-waiting-in-a-traffic-light-5675618/) của Erkan Avanoğlu, [giấy phép Pexels](https://www.pexels.com/license/) | [MP4 1920 × 1080](https://videos.pexels.com/video-files/5675618/5675618-hd_1920_1080_30fps.mp4) |
| `static.mp4` | [A Glass on the Table](https://www.pexels.com/video/a-glass-on-the-table-6801658/) của Artem Podrez, [giấy phép Pexels](https://www.pexels.com/license/) | [MP4 2160 × 3840](https://videos.pexels.com/video-files/6801658/6801658-uhd_2160_3840_30fps.mp4) |

#### Lập chỉ mục video

Nếu chạy bộ đánh giá hình ảnh, lập chỉ mục ảnh cho hai clip MP4 bổ sung.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\sample.mp4
.\.venv\Scripts\python.exe -X utf8 .\index_video.py .\static.mp4
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

Khi dùng **Tìm cảnh**, chọn **Thử tìm lại bằng tiếng Anh khi chưa thấy cảnh** để bật chế độ thử lại. Nếu câu gốc trả danh sách rỗng, ứng dụng dùng Ollama cục bộ với `qwen3:4b` và tìm lại trong phạm vi video đã chọn khi câu dịch khác câu gốc. Khi gọi API trực tiếp, thêm `"translate_on_miss": true` vào JSON gửi tới `POST /api/search-frames`. Phản hồi có trường `translated_query` khi dịch thành công.

Với **Hỏi** hoặc **Ghép hình và lời thoại**, chọn video đã có chỉ mục lời thoại. Với **Hỏi**, nhập một câu hỏi về lời thoại. Với tìm kiếm kết hợp, nhập mô tả cảnh và điền nội dung lời thoại riêng nếu cần. Khi chọn **Tất cả video**, cả hai chế độ dùng lời thoại đều lấy `speech.webm` làm mặc định.

Chọn `speech.webm` rồi thử các câu sau.

| Chế độ | Nội dung nhập | Kết quả kỳ vọng trên video demo |
| --- | --- | --- |
| **Tìm cảnh** | `Người mặc áo sọc đang rửa tay ở bồn inox` | Kết quả đầu gần **16.003 giây** |
| **Ghép hình và lời thoại** | Cùng mô tả cảnh, điền `Chà tay ít nhất 20 giây` vào ô lời thoại | Các khung hình gần **16.003** và **17.003 giây** nằm trong đoạn lời thoại khớp |
| **Hỏi** | `Nên chà tay trong bao nhiêu giây?` | `Chà tay ít nhất 20 giây`, dẫn nguồn **15.08–22.08 giây** |

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

### Đánh giá tìm kiếm hình ảnh

Bộ đánh giá cục bộ so sánh câu gốc, câu tiếng Anh viết tay và bản dịch Ollama cho bảy ca trên ba video `speech.webm`, `static.mp4` và `sample.mp4`. Cả ba lượt dùng chung video và mốc thời gian kỳ vọng, ngưỡng điểm `0.28` và bước lọc các kết quả có mốc bắt đầu cách nhau dưới 5 giây trong cùng video.

| Tiêu chí | Bộ gốc (6 câu Việt, 1 câu Anh) | Tiếng Anh viết tay | Bản dịch Ollama |
| --- | --- | --- | --- |
| Truy vấn có cảnh thật và tìm được cảnh trong ba kết quả đầu | 4/5 | 5/5 | 5/5 |
| Truy vấn không có cảnh khớp và trả danh sách rỗng | 1/2 | 1/2 | 1/2 |

Một kết quả hợp lệ phải thuộc đúng video và giao với khoảng thời gian đã đối chiếu. Truy vấn xe bồn trắng gốc bỏ sót cảnh ở **11.011–17.017 giây** trong `sample.mp4`. Cả hai câu tiếng Anh xếp khung hình đúng tại **13.013 giây** lên đầu, với điểm **0.3315** cho câu viết tay và **0.3201** cho bản dịch Ollama. Truy vấn đánh răng trả nhầm cảnh rửa tay trong cả ba lượt.

Giữ Flask đang chạy khi dùng cả ba lệnh. Chế độ `--auto-english` cần thêm Ollama cục bộ với mô hình `qwen3:4b` đã cài. Ở chế độ đó, [script đánh giá](evaluate_visual_search.py) dịch từng câu rồi gửi câu dịch đến API tìm kiếm.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py --english
.\.venv\Scripts\python.exe -X utf8 .\evaluate_visual_search.py --auto-english
```

### Đánh giá Video RAG

Bộ đánh giá trên `speech.webm` kiểm tra nội dung câu trả lời và mốc thời gian chính xác của nguồn. **Cả ba ca đều đạt với `qwen3:4b`**, tăng từ hai ca trước khi cập nhật prompt. Câu hỏi ngắn về thời gian chà tay trả lời «ít nhất 20 giây» và dẫn đúng đoạn **15.08–22.08 giây**. Câu hỏi hai ý trích đúng cả hai đoạn. Câu thiếu bằng chứng trả `answer: null` và `sources: []`.

Giữ Flask và Ollama đang chạy rồi gọi [script đánh giá Video RAG](evaluate_video_rag.py).

```powershell
.\.venv\Scripts\python.exe -X utf8 .\evaluate_video_rag.py
```
