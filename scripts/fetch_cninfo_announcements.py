import argparse
import json
import time
from pathlib import Path

import requests


CNINFO_QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"


def normalize_date(value: str) -> str:
    return value.replace("-", "")


def fetch_page(start_date: str, end_date: str, page_num: int, page_size: int, searchkey: str = "", use_env_proxy: bool = False) -> dict:
    data = {
        "pageNum": page_num,
        "pageSize": page_size,
        "column": "szse",
        "tabName": "fulltext",
        "plate": "",
        "stock": "",
        "searchkey": searchkey,
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": f"{start_date}~{end_date}",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        "X-Requested-With": "XMLHttpRequest",
    }
    session = requests.Session()
    session.trust_env = use_env_proxy
    response = session.post(CNINFO_QUERY_URL, data=data, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def iter_announcements(start_date: str, end_date: str, page_size: int, max_pages: int, sleep: float, searchkey: str, use_env_proxy: bool):
    for page_num in range(1, max_pages + 1):
        payload = fetch_page(start_date, end_date, page_num, page_size, searchkey, use_env_proxy)
        announcements = payload.get("announcements") or []
        if not announcements:
            break

        for item in announcements:
            adjunct_url = item.get("adjunctUrl") or ""
            yield {
                "id": f"{item.get('secCode', '')}_{item.get('announcementTime', '')}_{Path(adjunct_url).stem}",
                "sec_code": item.get("secCode"),
                "sec_name": item.get("secName"),
                "org_id": item.get("orgId"),
                "title": item.get("announcementTitle", "").replace("<em>", "").replace("</em>", ""),
                "announcement_time": item.get("announcementTime"),
                "adjunct_url": adjunct_url,
                "pdf_url": f"http://static.cninfo.com.cn/{adjunct_url}" if adjunct_url else "",
                "source": "cninfo",
            }

        time.sleep(sleep)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True, help="开始日期，例如 2024-01-01")
    parser.add_argument("--end-date", required=True, help="结束日期，例如 2024-12-31")
    parser.add_argument("--page-size", type=int, default=30)
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--searchkey", default="")
    parser.add_argument("--use-env-proxy", action="store_true")
    parser.add_argument("--output", default="data/raw/cninfo_announcements.jsonl")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as file:
        for item in iter_announcements(args.start_date, args.end_date, args.page_size, args.max_pages, args.sleep, args.searchkey, args.use_env_proxy):
            file.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    print(f"saved: {output_path} records: {count}")


if __name__ == "__main__":
    main()
