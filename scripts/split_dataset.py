import argparse
import json
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/sft_candidates.jsonl")
    parser.add_argument("--train", default="data/train.jsonl")
    parser.add_argument("--valid", default="data/valid.jsonl")
    parser.add_argument("--test", default="data/test.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    args = parser.parse_args()

    with Path(args.input).open("r", encoding="utf-8") as file:
        samples = [json.loads(line) for line in file if line.strip()]

    random.Random(args.seed).shuffle(samples)
    total = len(samples)
    test_size = int(total * args.test_ratio)
    valid_size = int(total * args.valid_ratio)

    splits = {
        Path(args.test): samples[:test_size],
        Path(args.valid): samples[test_size : test_size + valid_size],
        Path(args.train): samples[test_size + valid_size :],
    }

    for path, items in splits.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for item in items:
                file.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"saved: {path} records: {len(items)}")


if __name__ == "__main__":
    main()
