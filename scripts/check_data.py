import json
from pathlib import Path


FORBIDDEN_WORDS = ["买入", "卖出", "持有", "稳赚", "必涨", "推荐股票"]


def check_file(path: Path) -> list[tuple[int, str]]:
    bad = []
    if not path.exists():
        return [(0, "文件不存在")]

    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, 1):
            try:
                obj = json.loads(line)
                messages = obj["messages"]

                assert messages[0]["role"] == "system"
                assert messages[-1]["role"] == "assistant"
                assert len(messages[-1]["content"]) > 20

                answer = messages[-1]["content"]
                for word in FORBIDDEN_WORDS:
                    assert word not in answer, f"包含禁止表达：{word}"
            except Exception as exc:
                bad.append((line_no, str(exc)))

    return bad


def main() -> None:
    files = [Path("data/demo.jsonl")]
    for path in files:
        bad = check_file(path)
        print(f"{path} bad: {len(bad)}")
        if bad[:5]:
            print(bad[:5])


if __name__ == "__main__":
    main()
