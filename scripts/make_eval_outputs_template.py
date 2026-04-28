import json
from pathlib import Path


def main() -> None:
    input_path = Path("data/eval_questions.jsonl")
    output_path = Path("outputs/eval_outputs_template.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue

            case = json.loads(line)
            target.write(
                json.dumps(
                    {
                        "id": case["id"],
                        "task": case["task"],
                        "input": case["input"],
                        "reference_points": case["reference_points"],
                        "expected_keywords": case.get("expected_keywords", []),
                        "model_output": "",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"created: {output_path}")


if __name__ == "__main__":
    main()
