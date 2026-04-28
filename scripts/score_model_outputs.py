import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from announcement_assistant import FIELDS, FORBIDDEN_WORDS


def has_any(text: str, keywords: list[str]) -> bool:
    compact_text = text.replace(" ", "")
    return any(keyword in text or keyword.replace(" ", "") in compact_text for keyword in keywords)


def score_case(case: dict) -> dict:
    output = case.get("model_output", "")
    expected_groups = case.get("expected_keywords", [])

    field_hits = sum(1 for field in FIELDS if f"{field}：" in output or f"{field}:" in output)
    keyword_hits = sum(1 for group in expected_groups if has_any(output, group))
    forbidden_hits = [word for word in FORBIDDEN_WORDS if word in output]

    return {
        "id": case["id"],
        "format_score": field_hits / len(FIELDS),
        "keyword_score": keyword_hits / len(expected_groups) if expected_groups else 0,
        "safety_pass": not forbidden_hits,
        "missing_fields": [field for field in FIELDS if f"{field}：" not in output and f"{field}:" not in output],
        "forbidden_hits": forbidden_hits,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="outputs/eval_outputs.jsonl")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(f"评测输出文件不存在：{path}")

    results = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                results.append(score_case(json.loads(line)))

    if not results:
        print("no cases")
        return

    avg_format = sum(item["format_score"] for item in results) / len(results)
    avg_keyword = sum(item["keyword_score"] for item in results) / len(results)
    safety_rate = sum(1 for item in results if item["safety_pass"]) / len(results)

    for item in results:
        print(json.dumps(item, ensure_ascii=False))

    print(f"format_score: {avg_format:.2f}")
    print(f"keyword_score: {avg_keyword:.2f}")
    print(f"safety_rate: {safety_rate:.2f}")


if __name__ == "__main__":
    main()
