import json
from pathlib import Path


SYSTEM_FALLBACK = (
    "你是一个中文金融公告解读助手。你只能基于用户提供的公告、财报或研报片段回答。"
    "不得编造事实，不得给出投资建议。"
)


def convert_item(item: dict) -> dict:
    messages = item["messages"]
    system = SYSTEM_FALLBACK
    conversations = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "system":
            system = content
        elif role == "user":
            conversations.append({"from": "human", "value": content})
        elif role == "assistant":
            conversations.append({"from": "gpt", "value": content})

    return {
        "system": system,
        "conversations": conversations,
    }


def convert_file(input_path: Path, output_path: Path) -> None:
    data = []
    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                data.append(convert_item(json.loads(line)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    convert_file(
        input_path=Path("data/demo.jsonl"),
        output_path=Path("data/finance_sft_demo.json"),
    )
    print("converted: data/finance_sft_demo.json")


if __name__ == "__main__":
    main()
