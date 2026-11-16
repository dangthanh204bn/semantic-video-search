import json
from urllib.request import Request, urlopen
from argparse import ArgumentParser

CASES = [
    (
        "Người mặc áo sọc đang rửa tay ở bồn inox",
        "A person in a striped shirt washing their hands at a stainless steel sink",
        ("speech", 15.0, 22.0),
    ),
    (
        "Chiếc ly màu trắng đặt trên bàn",
        "A white cup on a table",
        ("static", 4.0, 9.0),
    ),
    (
        "A white cup on a white tray",
        "A white cup on a white tray",
        ("static", 4.0, 9.0),
    ),
    (
        "Nhiều ô tô dừng đèn đỏ ở ngã tư",
        "Several cars stopped at a red light at an intersection",
        ("sample", 3.0, 19.1),
    ),
    (
        "Xe bồn màu trắng đi qua ngã tư",
        "A white tanker truck driving through an intersection",
        ("sample", 11.011, 17.017),
    ),
    ("Một con hổ chạy trong rừng", "A tiger running through a forest", None),
    (
        "Người mặc áo sọc đang đánh răng trước bồn rửa",
        "A person in a striped shirt brushing their teeth in front of a sink",
        None,
    ),
]


def main(use_english=False):
    positive_checks = []
    negative_checks = []

    for original_query, english_query, expected in CASES:
        query = english_query if use_english else original_query
        body = json.dumps({"query": query, "video_id": "all"}).encode("utf-8")
        request = Request(
            "http://127.0.0.1:5000/api/search-frames",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            hits = json.load(response)["hits"]

        top_hits = hits[:3]
        if expected is None:
            passed = not hits
            negative_checks.append(passed)
        else:
            video_id, start_s, end_s = expected
            passed = any(
                hit["video_id"] == video_id
                and hit["start_s"] <= end_s
                and start_s <= hit["end_s"]
                for hit in top_hits
            )
            positive_checks.append(passed)

        print(f"{'ĐẠT' if passed else 'CHƯA ĐẠT'} | {query}")
        for hit in top_hits:
            print(
                f"  {hit['video_id']} {hit['start_s']:.3f}-{hit['end_s']:.3f}s "
                f"({hit['score']:.4f})"
            )

    print(f"Tìm đúng trong top 3: {sum(positive_checks)}/{len(positive_checks)}")
    print(f"Từ chối đúng truy vấn không có cảnh: {sum(negative_checks)}/{len(negative_checks)}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--english", action="store_true")
    args = parser.parse_args()
    main(use_english=args.english)
