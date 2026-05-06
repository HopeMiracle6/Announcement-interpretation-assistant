import argparse
import gc
import json
import os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


SYSTEM_PROMPT = (
    "你是一个中文金融公告解读助手。你只能基于用户提供的公告、财报或研报片段回答。"
    "不得编造事实，不得给出投资建议。请按用户要求的字段输出。"
)


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def get_message(case: dict, role: str) -> str:
    for message in case.get("messages", []):
        if message.get("role") == role:
            return message.get("content", "")
    return ""


def get_case_id(case: dict, index: int) -> str:
    if "id" in case:
        return str(case["id"])
    meta = case.get("meta", {})
    return str(meta.get("source_id") or f"case_{index:04d}")


def get_user_input(case: dict) -> str:
    if "input" in case:
        return case["input"]
    user_input = get_message(case, "user")
    if user_input:
        return user_input
    raise KeyError("case must contain input or a user message")


def resolve_local_model_path(model_name_or_path: str) -> str:
    path = Path(model_name_or_path)
    if path.exists():
        return str(path)

    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    cache_name = "models--" + model_name_or_path.replace("/", "--")
    snapshots_dir = cache_root / cache_name / "snapshots"
    if snapshots_dir.exists():
        snapshots = sorted(snapshots_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
        if snapshots:
            return str(snapshots[0])

    return model_name_or_path


def save_cases(path: Path, cases: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for case in cases:
            file.write(json.dumps(case, ensure_ascii=False) + "\n")


def build_prompt(tokenizer, user_input: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def load_model(model_name_or_path: str, tokenizer_path: str, local_files_only: bool):
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_path,
        trust_remote_code=True,
        local_files_only=local_files_only,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        trust_remote_code=True,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        local_files_only=local_files_only,
    )
    model.eval()
    return tokenizer, model


def generate_one(tokenizer, model, user_input: str, args: argparse.Namespace) -> str:
    prompt = build_prompt(tokenizer, user_input)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=args.do_sample,
            temperature=args.temperature if args.do_sample else None,
            top_p=args.top_p if args.do_sample else None,
            repetition_penalty=args.repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def generate_file(tokenizer, model, cases: list[dict], output_path: Path, args: argparse.Namespace, label: str) -> None:
    outputs = []
    total = len(cases)
    for index, case in enumerate(cases, start=1):
        item = dict(case)
        item.setdefault("id", get_case_id(case, index))
        item.setdefault("input", get_user_input(case))
        reference_output = get_message(case, "assistant")
        if reference_output:
            item.setdefault("reference_output", reference_output)
        item["model_output"] = generate_one(tokenizer, model, item["input"], args)
        outputs.append(item)
        print(f"{label}: {index}/{total} {item['id']}")

    save_cases(output_path, outputs)
    print(f"saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/eval_questions.jsonl")
    parser.add_argument("--base-output", default="outputs/base_eval_outputs.jsonl")
    parser.add_argument("--sft-output", default="outputs/qlora_eval_outputs.jsonl")
    parser.add_argument("--model", default="Qwen/Qwen3-4B")
    parser.add_argument("--adapter", default=r"D:\LLaMA-Factory\saves\qwen3-4b\lora\finance_sft_json")
    parser.add_argument("--tokenizer", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--repetition-penalty", type=float, default=1.1)
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--skip-base", action="store_true")
    parser.add_argument("--skip-sft", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    model_path = resolve_local_model_path(args.model)
    tokenizer_path = args.tokenizer or args.adapter or model_path

    cases = load_cases(Path(args.input))
    tokenizer, model = load_model(model_path, tokenizer_path, local_files_only=not args.allow_download)

    if not args.skip_base:
        generate_file(tokenizer, model, cases, Path(args.base_output), args, "base")

    if not args.skip_sft:
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
        model.eval()
        generate_file(tokenizer, model, cases, Path(args.sft_output), args, "qlora")

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
