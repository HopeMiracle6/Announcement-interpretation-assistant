import argparse
import json
import time
from pathlib import Path

from announcement_categories import CATEGORIES
from fetch_cninfo_announcements import fetch_page


def normalize_item(item: dict, category: str, label: str, keyword: str) -> dict:
    adjunct_url = item.get("adjunctUrl") or ""
    return {
        "id": f"{item.get('secCode', '')}_{item.get('announcementTime', '')}_{Path(adjunct_url).stem}",
        "sec_code": item.get("secCode"),
        "sec_name": item.get("secName"),
        "org_id": item.get("orgId"),
        "title": item.get("announcementTitle", "").replace("<em>", "").replace("</em>", ""),
        "announcement_time": item.get("announcementTime"),
        "adjunct_url": adjunct_url,
        "pdf_url": f"http://static.cninfo.com.cn/{adjunct_url}" if adjunct_url else "",
        "source": "cninfo",
        "event_category": category,
        "event_type": label,
        "matched_keyword": keyword,
    }


def fetch_category(start_date: str, end_date: str, category: str, target: int, page_size: int, max_pages_per_keyword: int, sleep: float) -> list[dict]:
    info = CATEGORIES[category]
    label = info["label"]
    selected = []
    seen_urls = set()

    for keyword in info["keywords"]:
        if len(selected) >= target:
            break

        for page_num in range(1, max_pages_per_keyword + 1):
            payload = fetch_page(start_date, end_date, page_num, page_size, keyword, use_env_proxy=False)
            announcements = payload.get("announcements") or []
            if not announcements:
                break

            for raw_item in announcements:
                item = normalize_item(raw_item, category, label, keyword)
                if not item["pdf_url"] or item["pdf_url"] in seen_urls:
                    continue

                seen_urls.add(item["pdf_url"])
                selected.append(item)
                if len(selected) >= target:
                    break

            if len(selected) >= target:
                break
            time.sleep(sleep)

    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--per-class", type=int, default=60)
    parser.add_argument("--page-size", type=int, default=30)
    parser.add_argument("--max-pages-per-keyword", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--output", default="data/raw/cninfo_balanced_announcements.jsonl")
    args = parser.parse_args()

    all_items = []
    for category in CATEGORIES:
        items = fetch_category(
            start_date=args.start_date,
            end_date=args.end_date,
            category=category,
            target=args.per_class,
            page_size=args.page_size,
            max_pages_per_keyword=args.max_pages_per_keyword,
            sleep=args.sleep,
        )
        all_items.extend(items)
        print(f"{category}: {len(items)}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for item in all_items:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"saved: {output_path} records: {len(all_items)}")


if __name__ == "__main__":
    main()
