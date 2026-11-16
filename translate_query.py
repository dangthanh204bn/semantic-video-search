import json
from argparse import ArgumentParser
from urllib.request import Request, urlopen

def translate_visual_query(query):
    payload = {
        "model": "qwen3:4b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Translate the input into natural English for visual video search. "
                    "In traffic descriptions, use 'red light' for 'đèn đỏ' and 'green light' for 'đèn xanh'. "
                    "Preserve objects, colors, actions, locations, quantities and negation. "
                    "Preserve explicit counts exactly. For example, 'ba người' means 'three people'. "
                    "Translate clothing as something worn by a person. Preserve the color of each object. "
                    "For English input, return the input as-is. "
                    "Put the translation in the translation field."
                ),
            },
            {"role": "user", "content": query},
        ],
        "stream": False,
        "think": False,
        "format": {
            "type": "object",
            "properties": {"translation": {"type": "string"}},
            "required": ["translation"],
        },
        "options": {"temperature": 0, "num_predict": 96},
    }

    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=60) as response:
        data = json.load(response)

    translation = json.loads(data["message"]["content"])["translation"].strip()
    if not translation:
        raise ValueError("Ollama trả về bản dịch rỗng.")
    return translation

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    print(translate_visual_query(args.query))
