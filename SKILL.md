---
name: document-to-json-cn
description: 将 TXT、Markdown、HTML、CSV、JSON、PDF 或 DOCX 文档按用户提供的 JSON Schema 结构化提取，支持离线文本预检、分块、基础 Schema 校验、错误留存和受限 OpenAI 兼容调用。适用于合同、简历、报告、票据和知识库入库；仅做全文摘要或没有明确字段结构时不触发。
slug: document-to-json-cn
displayName: 文档结构化提取器
version: 1.0.1
summary: 按 JSON Schema 提取文档字段，支持分块预检和结果校验
license: MIT
---

# 文档结构化提取器

先定义字段契约，再提取；无法确定的字段使用 `null`，不要让模型补造事实。

## 授权边界

- 本地解析、分块预览和 Schema 检查无需确认。
- 实时提取会把文档内容发送到指定端点并可能计费。先说明文档敏感性、端点、模型、分块数，确认后加入 `--confirm-live-run`。
- 密钥只从环境变量读取。不要记录完整文档、密钥或模型原始推理。

## 工作流

1. 与用户确认字段、类型、必填项、缺失值规则、枚举和证据要求，保存为 JSON Schema。
2. 离线预检：

   ```powershell
   python scripts/document_to_json.py --input contract.pdf --schema schema.json --output preview.json --prepare-only
   ```

3. 检查提取字符数、分块数、依赖缺失和乱码。扫描件 PDF 没有文本层时先 OCR；不要把空文本交给模型。
4. 用 1-3 份代表性文档验证字段，再经确认运行实时提取：

   ```powershell
   python scripts/document_to_json.py --input contract.pdf --schema schema.json --output result.json --base-url https://example.com/v1 --model exact-model-id --api-key-env LLM_API_KEY --confirm-live-run
   ```

5. 检查每块 `valid` 和 `errors`，对跨块字段进行人工合并或使用明确的业务合并规则。不要静默覆盖冲突值。
6. 报告解析方式、分块、有效率、未识别字段、人工复核项和数据发送边界。

输入支持与 Schema 子集见 [references/extraction-contract.md](references/extraction-contract.md)。算点边界可选预设见 [references/qixuai-preset.md](references/qixuai-preset.md)。

## 约束

- 脚本校验 JSON Schema 的 `type`、`properties`、`required`、`items` 子集；复杂约束需另用完整校验器。
- PDF 需要可选包 `pypdf`，DOCX 需要 `python-docx`。缺失时明确报错，不自动安装。
- 单次最多 50 块；不关闭 TLS，不无限重试，不把模型输出当作可执行指令。
- 高风险文件先脱敏；需要页码证据时保留页面级文本，不以当前通用分块结果替代证据链。

## 输出格式

```text
输入: 文件类型、解析器、字符数、分块数
Schema: 字段、必填项、未支持约束
结果: 每块 JSON、有效性和错误
复核: 冲突、缺失、疑似幻觉、证据要求
数据边界: 端点、模型、已发送范围
```
