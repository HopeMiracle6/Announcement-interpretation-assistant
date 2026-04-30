import argparse
import json
import time
from pathlib import Path

import requests


def safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)[:120]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/filtered_announcements.jsonl")
    parser.add_argument("--output", default="data/raw/downloaded_announcements.jsonl")
    parser.add_argument("--pdf-dir", default="data/raw/pdfs")
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--use-env-proxy", action="store_true")
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    session.trust_env = args.use_env_proxy
    count = 0
    with Path(args.input).open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue

            item = json.loads(line)
            pdf_path = pdf_dir / f"{safe_name(item['id'])}.pdf"
            if not pdf_path.exists():
                response = session.get(item["pdf_url"], headers=headers, timeout=30)
                response.raise_for_status()
                pdf_path.write_bytes(response.content)
                time.sleep(args.sleep)

            item["pdf_path"] = str(pdf_path)
            target.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    print(f"saved: {output_path} records: {count}")


if __name__ == "__main__":
    main()
