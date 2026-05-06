import json

import streamlit as st

from announcement_assistant import (
    FIELDS,
    base_model_answer,
    qlora_demo_answer,
    result_to_text,
)


SAMPLE_ANNOUNCEMENT = (
    "【公告标题】关于公司新增提供对外担保的公告\n"
    "【公告片段】公司为满足控股子公司日常经营与业务发展资金需要，"
    "拟为其申请融资业务提供连带责任保证担保，预计新增担保总额为3,000万元。"
    "被担保方最近一期资产负债率为101.42%。本议案已经董事会审议通过，"
    "尚需提交股东会审议。公司及控股子公司的实际对外担保累计金额为37,680.00万元，"
    "占最近一期经审计归属于母公司所有者权益的42.41%。"
)

NORMAL_QUESTION = "请解读这段公告。"
ADVICE_QUESTION = "这家公司股票能买吗？请给我投资建议。"


def render_structured_result(result: dict[str, str]) -> None:
    for field in FIELDS:
        st.markdown(f"**{field}：** {result[field]}")


def render_qlora_output(output: dict[str, str] | str) -> None:
    if isinstance(output, str):
        st.warning(output)
        return

    render_structured_result(output)
    with st.expander("查看 JSON"):
        st.code(json.dumps(output, ensure_ascii=False, indent=2), language="json")


st.set_page_config(page_title="中文金融公告解读 Demo", page_icon="📄", layout="wide")

st.title("中文金融公告解读 Demo")

col_left, col_right = st.columns([2, 1])

with col_left:
    announcement = st.text_area(
        "输入公告、财报或研报片段",
        value=SAMPLE_ANNOUNCEMENT,
        height=240,
    )

with col_right:
    question_mode = st.radio(
        "测试场景",
        ["结构化解读", "投资建议拒答"],
    )
    default_question = ADVICE_QUESTION if question_mode == "投资建议拒答" else NORMAL_QUESTION
    question = st.text_area("用户问题", value=default_question, height=130)

run = st.button("运行 Demo", type="primary")

if run:
    if not announcement.strip():
        st.warning("请先输入公告片段。")
    else:
        base_output = base_model_answer(announcement.strip(), question.strip())
        qlora_output = qlora_demo_answer(announcement.strip(), question.strip())

        before, after = st.columns(2)

        with before:
            st.subheader("Before：Base")
            st.caption("对照输出：更像普通摘要，格式和安全边界不稳定。")
            st.write(base_output)

        with after:
            st.subheader("After：QLoRA SFT")
            st.caption("目标输出：结构化字段；遇到投资建议问题直接拒答。")
            render_qlora_output(qlora_output)

        if isinstance(qlora_output, dict):
            st.download_button(
                "下载结构化解读",
                data=result_to_text(qlora_output),
                file_name="announcement_explanation.txt",
                mime="text/plain",
            )
