import re

import streamlit as st


FIELDS = [
    "事件类型",
    "涉及主体",
    "关键金额/时间",
    "对公司的可能影响",
    "风险提示",
    "不能判断的部分",
]


def detect_event_type(text: str) -> str:
    rules = [
        ("业绩预告/业绩变动", ["净利润", "业绩预告", "同比增长", "同比下降", "扭亏", "亏损"]),
        ("股份减持", ["减持", "股东拟减持", "集中竞价", "大宗交易"]),
        ("并购重组", ["收购", "并购", "重大资产重组", "购买资产", "股权转让"]),
        ("诉讼仲裁", ["诉讼", "仲裁", "判决", "起诉", "被告"]),
        ("对外担保", ["担保", "保证责任", "被担保方"]),
        ("合同/订单", ["合同", "订单", "中标", "项目金额"]),
    ]
    for event_type, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return event_type
    return "暂无法明确分类"


def extract_entities(text: str) -> str:
    matches = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9（）()]{2,30}(?:股份有限公司|有限公司|集团|公司)", text)
    unique = list(dict.fromkeys(matches))
    return "、".join(unique[:5]) if unique else "当前材料未明确提供"


def extract_amounts_and_dates(text: str) -> str:
    amount_pattern = r"\d+(?:\.\d+)?\s*(?:亿元|万元|元|%|股|万股|亿股)"
    date_pattern = r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\d{4}\s*年度|\d{4}\s*年"
    amounts = re.findall(amount_pattern, text)
    dates = re.findall(date_pattern, text)
    items = list(dict.fromkeys(amounts + dates))
    return "、".join(items[:10]) if items else "当前材料未明确提供"


def explain_announcement(text: str) -> dict[str, str]:
    event_type = detect_event_type(text)
    entities = extract_entities(text)
    amounts_and_dates = extract_amounts_and_dates(text)

    return {
        "事件类型": event_type,
        "涉及主体": entities,
        "关键金额/时间": amounts_and_dates,
        "对公司的可能影响": "该事项可能影响公司的经营表现、财务结果或市场预期，具体影响需要结合完整公告、财务数据和后续进展判断。",
        "风险提示": "当前解读仅基于用户提供的片段，不构成投资建议；公告信息可能存在不完整、未审计或后续变化的情况。",
        "不能判断的部分": "无法仅凭当前材料判断公司估值、股价走势、投资价值，或公告未披露的事实。",
    }


def render_result(result: dict[str, str]) -> None:
    for field in FIELDS:
        st.markdown(f"**{field}：** {result[field]}")


st.set_page_config(page_title="中文上市公司公告解读助手", page_icon="📄", layout="centered")

st.title("中文上市公司公告解读助手")

announcement = st.text_area(
    "公告或财报片段",
    height=260,
    placeholder="请粘贴上市公司公告、财报或研报片段...",
)

if st.button("解读公告", type="primary"):
    if not announcement.strip():
        st.warning("请先输入公告片段。")
    else:
        render_result(explain_announcement(announcement.strip()))
