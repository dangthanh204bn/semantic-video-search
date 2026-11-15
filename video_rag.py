import json
import sys
from urllib.request import Request, urlopen

from search_transcript import find_transcripts


def answer_question(index_path, question):
    hits = find_transcripts(index_path, question)
    if not hits:
        return {"answer": None, "sources": []}

    evidence = {f"E{i}": hit for i, hit in enumerate(hits, start=1)}
    transcript = "\n".join(
        f"[{code}] {hit['text']}" for code, hit in evidence.items()
    )

    payload = {
        "model": "qwen3:4b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Chỉ trả lời bằng tiếng Việt dựa vào các đoạn lời chép. "
                    "Giữ nguyên số liệu, điều kiện và các lựa chọn. "
                    "Ghi mã của mọi đoạn dùng để trả lời vào evidence_ids. "
                    "Nếu thiếu dữ kiện cho bất kỳ ý nào trong câu hỏi, "
                    "đặt answer thành null và evidence_ids thành []."
                ),
            },
            {
                "role": "user",
                "content": f"Câu hỏi: {question}\nCác đoạn lời chép:\n {transcript}"
            },
        ],
        "stream": False,
        "think": False,
        "format": {
            "type": "object",
            "properties": {
                "answer": {"type": ["string", "null"]},
                "evidence_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(evidence)},
                },
            },
        "required": ["answer", "evidence_ids"],
        },
        "options": {"temperature": 0, "num_predict": 256},
    }

    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urlopen(request, timeout=90) as response:
        result = json.load(response)

    parsed = json.loads(result["message"]["content"])
    answer = parsed["answer"]
    codes = list(dict.fromkeys(parsed["evidence_ids"]))

    if answer and codes and all(code in evidence for code in codes):
        return {"answer": answer, "sources": [evidence[code] for code in codes]}

    return {"answer": None, "sources":[]}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit('Cách chạy: python video_rag.py INDEX_PATH "Câu hỏi"')

    index_path, question = sys.argv[1:]
    result = answer_question(index_path, question)

    if result["answer"] is None:
        print("Chưa đủ bằng chứng trong đoạn tìm được.")
    else:
        print(result["answer"])
        for hit in result["sources"]:
            print(f"Nguồn {hit['video_id']}, {hit['start_s']:.2f}-{hit['end_s']:.2f} giây")
