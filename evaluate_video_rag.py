import json
import re
from urllib.request import Request, urlopen

MINIMUM_TIME = (
    "Ít nhất 20 giây",
    "Ít nhất là 20 giây",
    "tối thiểu 20 giây",
    "tối thiểu là 20 giây",
    "20 giây trở lên",
)

CASES = [
    (
        "Một nguồn và đủ điều kiện",
        "Nên chà tay trong bao nhiêu giây?",
        (MINIMUM_TIME,),
        {("speech", 15.08, 22.08)},
    ),
    (
        "Câu trả lời cần hai nguồn",
        "Cần chà tay ít nhất bao nhiêu giây và sau khi rửa sạch tay thì lau khô bằng gì?",
        (MINIMUM_TIME, ("khăn giấy",), ("máy sấy khô",)),
        {("speech", 15.08, 22.08), ("speech", 27.58, 32.58)},
    ),
    (
        "Thiếu bằng chứng",
        "Trong video, số điện thoại của cửa hàng xe đạp là gì?",
        None,
        set(),
    ),
]


def main():
    passed_count = 0

    for name, question, required_phrases, expected_sources in CASES:
        body = json.dumps({"question": question, "video_id": "speech"}).encode("utf-8")
        request = Request(
            "http://127.0.0.1:5000/api/answer",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=100) as response:
            result = json.load(response)

        answer = result["answer"]
        actual_sources = {
            (source["video_id"], round(source["start_s"], 2), round(source["end_s"], 2))
            for source in result["sources"]
        }
        if required_phrases is None:
            answer_ok = answer is None
        else:
            normalized = " ".join((answer or "").casefold().split())
            answer_ok = all(
                any(
                    re.search(rf"\b{re.escape(phrase.casefold())}\b", normalized)
                    for phrase in group
                )
                for group in required_phrases
            )

        sources_ok = actual_sources == expected_sources
        passed = answer_ok and sources_ok
        passed_count += passed

        print(f"{'ĐẠT' if passed else 'CHƯA ĐẠT'} | {name}")
        print(f" Câu trả lời: {answer!r}")
        print(f" Nguồn: {sorted(actual_sources)}")
        print(f" Nội dung đạt: {answer_ok}, nguồn đạt: {sources_ok}")

    print(f"Đạt {passed_count}/{len(CASES)} ca Video RAG")


if __name__ == "__main__":
    main()
