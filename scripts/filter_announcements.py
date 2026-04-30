import argparse
import json
from collections import defaultdict
from pathlib import Path

from announcement_categories import match_category


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/cninfo_announcements.jsonl")
    parser.add_argument("--output", default="data/raw/filtered_announcements.jsonl")
    parser.add_argument("--per-class", type=int, default=60)
    parser.add_argument("--target-total", type=int, default=500)
    args = parser.parse_args()

    grouped = defaultdict(list)
    seen_urls = set()

    for item in load_jsonl(Path(args.input)):
        title = item.get("title", "")
        category, label = match_category(title)
        if not category:
            continue

        pdf_url = item.get("pdf_url")
        if not pdf_url or pdf_url in seen_urls:
            continue

        seen_urls.add(pdf_url)
        item["event_category"] = category
        item["event_type"] = label
        grouped[category].append(item)

    selected = []
    for category in sorted(grouped):
        selected.extend(grouped[category][: args.per_class])

    selected = selected[: args.target_total]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for item in selected:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"saved: {output_path} records: {len(selected)}")
    for category in sorted(grouped):
        print(f"{category}: selected {min(len(grouped[category]), args.per_class)} / matched {len(grouped[category])}")


if __name__ == "__main__":
    main()
