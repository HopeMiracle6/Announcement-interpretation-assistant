# 中文金融公告解读助手：基于 Qwen3-4B 的 QLoRA SFT

## 项目简介

本项目面向中文上市公司公告解读场景，构建了一个中文金融公告解读助手。项目支持对公告片段进行结构化解读，覆盖事件分类、关键信息抽取、风险提示和拒答边界控制等能力。

模型路线为 `Qwen/Qwen3-4B + QLoRA SFT`。训练数据来自巨潮资讯网公开公告，经过公告抓取、PDF 下载、正文抽取、SFT 数据构造和训练/验证/测试集切分。

## 技术栈

- Base Model: `Qwen/Qwen3-4B`
- Fine-tuning: QLoRA
- Framework: Transformers, PEFT, LLaMA Factory
- Quantization: 4-bit
- Demo: Streamlit
- Data Source: 巨潮资讯网公开公告

## 数据任务

1. 公告摘要
2. 事件分类
3. 信息抽取
4. 风险识别
5. 材料内问答
6. 投资建议拒答

当前模型输出目标为合法 JSON 对象，包含以下字段：

- `事件类型`
- `涉及主体`
- `关键金额/时间`
- `对公司的可能影响`
- `风险提示`
- `不能判断的部分`

## 数据流程

```powershell
D:\Anaconda\envs\torch-env\python.exe scripts\fetch_cninfo_announcements.py --start-date 2023-01-01 --end-date 2025-12-31 --page-size 30 --max-pages 80
D:\Anaconda\envs\torch-env\python.exe scripts\fetch_balanced_cninfo_announcements.py --start-date 2023-01-01 --end-date 2025-12-31 --per-class 60 --page-size 30 --max-pages-per-keyword 10 --output data/raw/cninfo_balanced_announcements.jsonl
D:\Anaconda\envs\torch-env\python.exe scripts\filter_announcements.py --input data/raw/cninfo_balanced_announcements.jsonl data/raw/cninfo_announcements.jsonl --per-class 60 --target-total 500
D:\Anaconda\envs\torch-env\python.exe scripts\download_pdfs.py
D:\Anaconda\envs\torch-env\python.exe scripts\extract_pdf_text.py --max-pages 8 --max-chars 6000
D:\Anaconda\envs\torch-env\python.exe scripts\build_sft_dataset.py --min-text-chars 300
D:\Anaconda\envs\torch-env\python.exe scripts\split_dataset.py
D:\Anaconda\envs\torch-env\python.exe scripts\convert_sft_to_json_format.py data\train.jsonl data\valid.jsonl data\test.jsonl
```

## 训练

先同步数据和配置到 LLaMA Factory：

```powershell
D:\Anaconda\envs\torch-env\python.exe scripts\prepare_llamafactory.py D:\LLaMA-Factory
```

然后在 `D:\LLaMA-Factory` 中训练：

```powershell
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set HF_ENDPOINT=https://hf-mirror.com
D:\Anaconda\envs\torch-env\python.exe -m llamafactory.cli train examples\train_lora\qwen3_4b_finance_qlora.yaml
```

训练配置见：

- `configs/qwen3_4b_finance_qlora.yaml`
- `configs/qwen3_4b_finance_lora_infer.yaml`

## Demo

启动本地 Demo：

```powershell
D:\Anaconda\envs\torch-env\python.exe -m streamlit run app.py
```

浏览器打开：

```text
http://localhost:8501
```

Demo 展示：

- 输入一段公告材料
- 输出结构化解读
- 遇到投资建议问题进行拒答
- 展示 Base 与 QLoRA SFT 的 Before / After 差异

## 实验结果

| 指标 | Base | QLoRA SFT |
|---|---:|---:|
| 格式遵循率 | 63.3% | 100.0% |
| 事实一致率 | 42.1% | 84.5% |
| 拒答准确率 | 98.0% | 100.0% |
| JSON 可解析率 | 100.0% | 98.0% |

完整评测报告见：

- `outputs/eval_report.md`

## 局限性

- SFT 不适合长期记忆事实知识，公告事实仍应以用户输入材料为准。
- 长文档、多主体、多表格场景仍可能遗漏信息。
- 少量样本可能出现 JSON 字符串转义错误。
- 当前 Demo 为轻量展示版，不实时加载 4B 模型，便于本地快速演示。
- 后续可加入 RAG、引用溯源和更严格的 JSON 修复机制。
