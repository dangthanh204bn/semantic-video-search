import csv
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory

import av

def index_video(video_path, project_dir, with_transcript=False):
    if not video_path.is_file():
        raise SystemExit(f"Không tìm thấy video: {video_path}")

    outputs_dir = project_dir / "outputs"
    output_dir = outputs_dir / video_path.stem
    if output_dir.exists():
        raise SystemExit(f"Thư mục đầu ra đã tồn tại: {output_dir}")

    outputs_dir.mkdir(exist_ok=True)

    with TemporaryDirectory(prefix=".index-", dir=outputs_dir) as staging:
        work_dir = Path(staging)
        staged_output = work_dir / "outputs" / video_path.stem

        def run_step(script, argument):
            subprocess.run(
                [sys.executable, str(project_dir / script), str(argument)],
                cwd=work_dir,
                check=True,
            )

        frames_csv = staged_output / "frames.csv"
        run_step("extract_frames.py", video_path)

        with frames_csv.open(newline="", encoding = "utf-8") as manifest:
            if next(csv.DictReader(manifest), None) is None:
                raise SystemExit("Không trích được khung hình nào.")

        run_step("deduplicate_frames.py", frames_csv)
        run_step("embed_frames.py", staged_output / "frames_dedup.csv")

        if with_transcript:
            with av.open(str(video_path)) as container:
                has_audio = bool(container.streams.audio)

            if has_audio:
                run_step("transcribe_video.py", video_path)
                transcript_csv = staged_output / "transcript.csv"

                with transcript_csv.open(newline="", encoding="utf-8") as manifest:
                    has_speech = any(
                        row["text"].strip() for row in csv.DictReader(manifest)
                    )

                if has_speech:
                    run_step("embed_transcript.py", transcript_csv)
                else:
                    print("Không tìm thấy lời thoại. Đã tạo chỉ mục ảnh.")
            else:
                print("Video không có luồng âm thanh. Đã tạo chỉ mục ảnh.")

        if (
            not staged_output.resolve().is_relative_to(work_dir.resolve())
            or output_dir.resolve().parent != outputs_dir.resolve()
        ):
            raise SystemExit("Đường dẫn đầu ra không hợp lệ.")

        staged_output.rename(output_dir)

    return output_dir / "image_embeddings.npz"

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("video_path", type=Path)
    parser.add_argument("--with-transcript", action="store_true")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent
    video_path = args.video_path.expanduser().resolve()
    index_path = index_video(
        video_path, project_dir, with_transcript=args.with_transcript
    )
    print(f"Đã tạo chỉ mục: {index_path}")
