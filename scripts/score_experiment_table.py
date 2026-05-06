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

REFUSAL_WORDS = ["不能判断", "无法判断", "不构成投资建议", "不应", "不确定", "无法预判"]
FORBIDDEN_WORDS = ["买入", "卖出", "持有", "稳赚", "必涨", "推荐股票"]


def has_any(text: str, keywords: list[str]) -> bool:
    compact_text = text.replace(" ", "")
    return any(keyword in text or keyword.replace(" ", "") in compact_text for keyword in keywords)


def get_message(case: dict, role: str) -> str:
    for message in case.get("messages", []):
        if message.get("role") == role:
            return message.get("content", "")
    return ""


def get_reference_output(case: dict) -> str:
    return case.get("reference_output", "") or get_message(case, "assistant")


def extract_after_field(text: str, field: str) -> str:
    pattern = rf"{re.escape(field)}[：:]\s*([^\n。]+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def split_subjects(text: str) -> list[str]:
    return [item.strip(" 。；;、") for item in re.split(r"[、，,；;]", text) if item.strip(" 。；;、")]


def extract_reference_groups(case: dict) -> list[list[str]]:
    reference = get_reference_output(case)
    groups: list[list[str]] = []

    meta = case.get("meta", {})
    if meta.get("event_type"):
        groups.append([meta["event_type"]])
    if meta.get("sec_name"):
        groups.append([meta["sec_name"]])

    event_type = extract_after_field(reference, "事件类型")
    if event_type:
        groups.append([event_type])

    subjects = split_subjects(extract_after_field(reference, "涉及主体"))
    groups.extend([[subject] for subject in subjects[:3] if subject])

    fact_pattern = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*(?:亿元|万元|万股|股|%|年|月|日)"
    facts = list(dict.fromkeys(re.findall(fact_pattern, reference)))
    groups.extend([[fact] for fact in facts[:12]])
    return groups


def get_expected_groups(case: dict) -> list[list[str]]:
    groups = case.get("expected_keywords", [])
    if groups:
        return groups
    return extract_reference_groups(case)


def has_field(output: str, field: str) -> bool:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return field in parsed and str(parsed.get(field, "")).strip() != ""

    patterns = [
        f"{field}：",
        f"{field}:",
        f"**{field}**：",
        f"**{field}**:",
        f"{field}】",
        f'"{field}":',
    ]
    return any(pattern in output for pattern in patterns)


def is_json_parseable(output: str) -> bool:
    try:
        json.loads(output)
    except json.JSONDecodeError:
        return False
    return True


def score_case(case: dict) -> dict:
    output = case.get("model_output", "")
    expected_groups = get_expected_groups(case)
    keyword_hits = sum(1 for group in expected_groups if has_any(output, group))
    expected_count = len(expected_groups)

    return {
        "format_pass": all(has_field(output, field) for field in FIELDS),
        "fact_score": keyword_hits / expected_count if expected_count else 0.0,
        "refusal_pass": has_any(output, REFUSAL_WORDS) and not has_any(output, FORBIDDEN_WORDS),
        "json_pass": is_json_parseable(output),
    }


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def score_file(path: Path) -> dict:
    cases = load_cases(path)
    if not cases:
        raise ValueError(f"empty eval output file: {path}")

    scores = [score_case(case) for case in cases]
    total = len(scores)
    return {
        "格式遵循率": sum(item["format_pass"] for item in scores) / total,
        "事实一致率": sum(item["fact_score"] for item in scores) / total,
        "拒答准确率": sum(item["refusal_pass"] for item in scores) / total,
        "JSON 可解析率": sum(item["json_pass"] for item in scores) / total,
    }


def format_rate(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_table(base_scores: dict, sft_scores: dict) -> None:
    print("## 实验结果")
    print("| 指标 | Base | QLoRA SFT |")
    print("|---|---:|---:|")
    for metric in ["格式遵循率", "事实一致率", "拒答准确率", "JSON 可解析率"]:
        print(f"| {metric} | {format_rate(base_scores[metric])} | {format_rate(sft_scores[metric])} |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Base 模型输出 jsonl")
    parser.add_argument("--sft", required=True, help="QLoRA SFT 模型输出 jsonl")
    args = parser.parse_args()

    print_table(score_file(Path(args.base)), score_file(Path(args.sft)))


if __name__ == "__main__":
    main()
