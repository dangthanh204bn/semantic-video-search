import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

def index_video(video_path, project_dir):
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

        if (
            not staged_output.resolve().is_relative_to(work_dir.resolve())
            or output_dir.resolve().parent != outputs_dir.resolve()
        ):
            raise SystemExit("Đường dẫn đầu ra không hợp lệ.")

        staged_output.rename(output_dir)

    return output_dir / "image_embeddings.npz"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit('Cách chạy: python index_video.py "đường dẫn video"')

    project_dir = Path(__file__).resolve().parent
    video_path = Path(sys.argv[1]).expanduser().resolve()
    index_path = index_video(video_path, project_dir)
    print(f"Đã tạo chỉ mục: {index_path}")