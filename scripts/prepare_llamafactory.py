import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.convert_to_llamafactory import convert_file


DATASET_INFO = {
    "file_name": "finance_sft.json",
    "formatting": "sharegpt",
    "columns": {
        "messages": "conversations",
        "system": "system",
    },
    "tags": {
        "role_tag": "from",
        "content_tag": "value",
        "user_tag": "human",
        "assistant_tag": "gpt",
    },
}


def load_dataset_info(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_dataset_info(path: Path, dataset_info: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(dataset_info, file, ensure_ascii=False, indent=2)
        file.write("\n")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copied: {src} -> {dst}")


def prepare(llamafactory_dir: Path) -> None:
    if not llamafactory_dir.exists():
        raise FileNotFoundError(f"LLaMA Factory 目录不存在：{llamafactory_dir}")

    dataset_info_path = llamafactory_dir / "data" / "dataset_info.json"
    if not dataset_info_path.exists():
        raise FileNotFoundError(f"未找到 dataset_info.json：{dataset_info_path}")

    project_root = Path(__file__).resolve().parents[1]
    source_jsonl = project_root / "data" / "demo.jsonl"
    local_sharegpt = project_root / "data" / "finance_sft_demo.json"

    convert_file(source_jsonl, local_sharegpt)
    copy_file(local_sharegpt, llamafactory_dir / "data" / "finance_sft.json")
    copy_file(
        project_root / "configs" / "qwen3_4b_finance_qlora.yaml",
        llamafactory_dir / "examples" / "train_lora" / "qwen3_4b_finance_qlora.yaml",
    )
    copy_file(
        project_root / "configs" / "qwen3_4b_finance_lora_infer.yaml",
        llamafactory_dir / "examples" / "inference" / "qwen3_4b_finance_lora_infer.yaml",
    )

    dataset_info = load_dataset_info(dataset_info_path)
    dataset_info["finance_sft"] = DATASET_INFO
    save_dataset_info(dataset_info_path, dataset_info)
    print("registered dataset: finance_sft")
    print("train: llamafactory-cli train examples/train_lora/qwen3_4b_finance_qlora.yaml")
    print("chat:  llamafactory-cli chat examples/inference/qwen3_4b_finance_lora_infer.yaml")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("llamafactory_dir", help="LLaMA-Factory 项目目录")
    args = parser.parse_args()
    prepare(Path(args.llamafactory_dir).resolve())


if __name__ == "__main__":
    main()
