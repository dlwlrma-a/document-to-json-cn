# 文档结构化提取器

按 JSON Schema 将常见文档分块提取成可校验 JSON。支持纯离线预检，实时 API 调用必须显式确认。

```powershell
python scripts/document_to_json.py --input report.md --schema schema.json --output preview.json --prepare-only
```

MIT License。
