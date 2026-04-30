CATEGORIES = {
    "annual_report": {
        "label": "年度报告",
        "keywords": ["年度报告", "年报"],
    },
    "quarterly_report": {
        "label": "季度报告",
        "keywords": ["第一季度报告", "第三季度报告", "季度报告"],
    },
    "performance_forecast": {
        "label": "业绩预告/业绩快报",
        "keywords": ["业绩预告", "业绩快报", "业绩修正", "盈利预告"],
    },
    "share_reduction": {
        "label": "股份减持",
        "keywords": ["减持", "股份减持", "股东减持"],
    },
    "share_increase": {
        "label": "股份增持",
        "keywords": ["增持", "股份增持", "股东增持"],
    },
    "merger_restructuring": {
        "label": "并购重组",
        "keywords": ["重大资产重组", "收购", "并购", "购买资产", "股权转让"],
    },
    "litigation": {
        "label": "诉讼仲裁",
        "keywords": ["诉讼", "仲裁", "判决", "起诉"],
    },
    "guarantee": {
        "label": "对外担保",
        "keywords": ["担保", "保证责任", "被担保"],
    },
    "related_transaction": {
        "label": "关联交易",
        "keywords": ["关联交易", "日常关联交易"],
    },
    "major_contract": {
        "label": "重大合同/中标",
        "keywords": ["重大合同", "合同", "中标", "订单"],
    },
    "dividend": {
        "label": "利润分配/分红",
        "keywords": ["利润分配", "分红", "权益分派", "派息"],
    },
    "repurchase": {
        "label": "股份回购",
        "keywords": ["回购", "股份回购"],
    },
}


def match_category(title: str) -> tuple[str, str] | tuple[None, None]:
    for category, info in CATEGORIES.items():
        if any(keyword in title for keyword in info["keywords"]):
            return category, info["label"]
    return None, None
