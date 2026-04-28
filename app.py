import streamlit as st

from announcement_assistant import FIELDS, explain_announcement, result_to_text


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
        result = explain_announcement(announcement.strip())
        render_result(result)
        st.download_button(
            "下载解读结果",
            data=result_to_text(result),
            file_name="announcement_explanation.txt",
            mime="text/plain",
        )
