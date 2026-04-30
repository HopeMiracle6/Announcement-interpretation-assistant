import argparse
import json
import re
from pathlib import Path


SYSTEM_PROMPT = (
    "你是一个中文金融公告解读助手。你只能基于用户提供的公告、财报或研报片段回答。"
    "你需要使用清晰、稳健、非投资建议的表达。如果材料不足，请明确说明“仅凭当前材料无法判断”。"
    "不得编造公告中没有出现的事实、数字、日期或结论。不得给出买入、卖出、持有等投资建议。"
)


RISK_TEMPLATES = {
    "业绩预告/业绩快报": "该信息可能为预告或快报，最终结果仍需以正式定期报告为准。",
    "股份减持": "减持计划存在是否实施、实施数量、实施价格和市场反应不确定等因素。",
    "股份增持": "增持计划存在实施进度、资金安排和市场环境变化等不确定因素。",
    "并购重组": "交易尚可能受审批、估值、交割、整合效果等因素影响。",
    "诉讼仲裁": "案件结果、执行情况及对公司财务影响仍存在不确定性。",
    "对外担保": "需关注被担保方偿债能力及公司可能承担的担保责任。",
    "关联交易": "需关注交易定价公允性、审批程序和对公司独立性的影响。",
    "重大合同/中标": "合同履行进度、回款、成本变化和项目验收仍存在不确定性。",
    "利润分配/分红": "分配方案仍需关注审批进展、实施安排和公司后续资金需求。",
    "股份回购": "回购存在实施进度、价格区间、资金安排和市场波动不确定性。",
}


def extract_amounts_and_dates(text: str) -> str:
    amount_pattern = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*(?:亿元|万元|万股|亿股|元|股|%)"
    date_pattern = r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\d{4}\s*年度|\d{4}\s*年|\d+\s*个月|\d+\s*个交易日"
    items = re.findall(amount_pattern, text) + re.findall(date_pattern, text)
    unique = list(dict.fromkeys(items))
    return "、".join(unique[:12]) if unique else "当前材料未明确提供"


def build_user_content(item: dict) -> str:
    return (
        "请解读下面公告片段：\n\n"
        f"【公告标题】{item.get('title', '')}\n\n"
        f"【公告片段】{item.get('text', '')}\n\n"
        "请按“事件类型、涉及主体、关键金额/时间、对公司的可能影响、风险提示、不能判断的部分”输出。"
    )


def build_assistant_content(item: dict) -> str:
    event_type = item.get("event_type") or "当前材料未明确提供"
    combined_text = f"{item.get('title', '')} {item.get('text', '')}"
    key_items = extract_amounts_and_dates(combined_text)
    risk = RISK_TEMPLATES.get(event_type, "当前材料有限，相关事项的后续进展和实际影响仍存在不确定性。")

    return (
        f"事件类型：{event_type}。\n\n"
        f"涉及主体：{item.get('sec_name') or '当前材料未明确提供'}。\n\n"
        f"关键金额/时间：{key_items}。\n\n"
        "对公司的可能影响：该事项可能影响公司的经营表现、财务结果、治理结构或市场预期，"
        "具体影响需要结合完整公告、财务数据和后续进展判断。\n\n"
        f"风险提示：{risk} 当前解读仅基于用户提供的公告片段，不构成投资建议。\n\n"
        "不能判断的部分：无法仅凭当前材料判断公司估值、股价走势、投资价值，或公告未披露的事实。"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/announcement_texts.jsonl")
    parser.add_argument("--output", default="data/raw/sft_candidates.jsonl")
    parser.add_argument("--min-text-chars", type=int, default=300)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with Path(args.input).open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue

            item = json.loads(line)
            if len(item.get("text", "")) < args.min_text_chars:
                continue

            sample = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_content(item)},
                    {"role": "assistant", "content": build_assistant_content(item)},
                ],
                "meta": {
                    "task": "announcement_explanation",
                    "domain": "finance",
                    "source": "cninfo",
                    "source_id": item.get("id"),
                    "sec_code": item.get("sec_code"),
                    "sec_name": item.get("sec_name"),
                    "event_category": item.get("event_category"),
                    "event_type": item.get("event_type"),
                    "needs_human_review": True,
                },
            }
            target.write(json.dumps(sample, ensure_ascii=False) + "\n")
            count += 1

    print(f"saved: {output_path} records: {count}")


if __name__ == "__main__":
    main()
