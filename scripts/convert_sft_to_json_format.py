import argparse
import json
import re
from pathlib import Path


FIELDS = [
    "事件类型",
    "涉及主体",
    "关键金额/时间",
    "对公司的可能影响",
    "风险提示",
    "不能判断的部分",
]

JSON_INSTRUCTION = (
    "请只输出一个合法 JSON 对象，不要使用 Markdown，不要输出多余解释。"
    "JSON 必须包含这些字段：事件类型、涉及主体、关键金额/时间、对公司的可能影响、风险提示、不能判断的部分。"
)


def extract_field(text: str, field: str) -> str:
    next_fields = "|".join(re.escape(item) for item in FIELDS if item != field)
    pattern = rf"{re.escape(field)}[：:]\s*(.*?)(?=\n\s*(?:{next_fields})[：:]|\Z)"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return ""
    return match.group(1).strip().strip("。")


def text_answer_to_json(answer: str) -> str:
    data = {field: extract_field(answer, field) for field in FIELDS}
    return json.dumps(data, ensure_ascii=False)


def update_user_content(content: str) -> str:
    old_instruction = "请按“事件类型、涉及主体、关键金额/时间、对公司的可能影响、风险提示、不能判断的部分”输出。"
    if old_instruction in content:
        return content.replace(old_instruction, JSON_INSTRUCTION)
    if JSON_INSTRUCTION in content:
        return content
    return content.rstrip() + "\n\n" + JSON_INSTRUCTION


def convert_file(path: Path) -> int:
    converted = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            item = json.loads(line)
            for message in item.get("messages", []):
                if message.get("role") == "user":
                    message["content"] = update_user_content(message.get("content", ""))
                elif message.get("role") == "assistant":
                    content = message.get("content", "")
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        message["content"] = text_answer_to_json(content)
                    else:
                        message["content"] = json.dumps({field: str(parsed.get(field, "")) for field in FIELDS}, ensure_ascii=False)

            converted.append(item)

    with path.open("w", encoding="utf-8") as file:
        for item in converted:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    return len(converted)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    for raw_path in args.paths:
        path = Path(raw_path)
        count = convert_file(path)
        print(f"converted: {path} records: {count}")


if __name__ == "__main__":
    main()
