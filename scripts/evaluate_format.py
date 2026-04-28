import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from announcement_assistant import FIELDS, FORBIDDEN_WORDS, explain_announcement


def check_result(result: dict[str, str]) -> list[str]:
    errors = []
    for field in FIELDS:
        if field not in result:
            errors.append(f"缺少字段：{field}")
        elif not str(result[field]).strip():
            errors.append(f"字段为空：{field}")

    answer = "\n".join(str(result.get(field, "")) for field in FIELDS)
    for word in FORBIDDEN_WORDS:
        if word in answer:
            errors.append(f"包含禁止表达：{word}")

    return errors


def main() -> None:
    path = Path("data/eval_questions.jsonl")
    total = 0
    passed = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            total += 1
            case = json.loads(line)
            result = explain_announcement(case["input"])
            errors = check_result(result)

            if errors:
                print(case["id"], "failed:", errors)
            else:
                passed += 1

    print(f"format_passed: {passed}/{total}")


if __name__ == "__main__":
    main()
