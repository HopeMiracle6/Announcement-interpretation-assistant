import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


def extract_text(path: Path, max_pages: int) -> str:
    reader = PdfReader(str(path))
    pages = reader.pages[:max_pages] if max_pages > 0 else reader.pages
    text = "\n".join(page.extract_text() or "" for page in pages)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/downloaded_announcements.jsonl")
    parser.add_argument("--output", default="data/raw/announcement_texts.jsonl")
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=6000)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    failed = 0

    with Path(args.input).open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue

            item = json.loads(line)
            try:
                text = extract_text(Path(item["pdf_path"]), args.max_pages)
            except Exception as exc:
                item["extract_error"] = str(exc)
                failed += 1
                continue

            item["text"] = text[: args.max_chars]
            target.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    print(f"saved: {output_path} records: {count} failed: {failed}")


if __name__ == "__main__":
    main()
