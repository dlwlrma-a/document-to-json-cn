# 提取契约

支持：TXT、Markdown、HTML、CSV、JSON；安装 `pypdf` 后支持文本型 PDF，安装 `python-docx` 后支持 DOCX。

内置校验器只覆盖 JSON Schema 的 `type`、`properties`、`required`、`items`。`enum`、格式、条件、引用和数值范围需要完整 JSON Schema 校验器或人工校验。

每个分块独立提取。跨块字段、重复列表和冲突值不自动合并，因为不同业务的覆盖、去重和证据规则不同。Schema 应允许未知值为 `null`，并在需要时增加 `source_quote` 或 `source_page` 字段。
