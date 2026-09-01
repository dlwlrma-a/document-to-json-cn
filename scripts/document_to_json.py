#!/usr/bin/env python3
"""Extract supported documents into schema-checked JSON chunks."""
import argparse
import csv
import html.parser
import json
import os
import re
import ssl
import urllib.request
from pathlib import Path


class TextHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def load_text(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8-sig")
    if suffix == ".html" or suffix == ".htm":
        parser = TextHTMLParser()
        parser.feed(path.read_text(encoding="utf-8-sig"))
        return "\n".join(parser.parts)
    if suffix == ".json":
        return json.dumps(json.loads(path.read_text(encoding="utf-8-sig")), ensure_ascii=False, indent=2)
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return "\n".join(json.dumps(row, ensure_ascii=False) for row in csv.DictReader(handle))
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires: pip install pypdf") from exc
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support requires: pip install python-docx") from exc
        return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
    raise ValueError("unsupported input type")


def chunks(text, size):
    if size < 500 or size > 50000:
        raise ValueError("chunk size must be between 500 and 50000")
    return [text[pos:pos + size] for pos in range(0, len(text), size)]


def validate(value, schema, path="$"):
    errors = []
    expected = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "number": (int, float), "integer": int, "boolean": bool, "null": type(None)}
    if expected in types and (not isinstance(value, types[expected]) or expected in ("number", "integer") and isinstance(value, bool)):
        return [f"{path}: expected {expected}"]
    if expected == "object" and isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required")
        for key, child in schema.get("properties", {}).items():
            if key in value:
                errors.extend(validate(value[key], child, f"{path}.{key}"))
    if expected == "array" and isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate(item, schema["items"], f"{path}[{index}]"))
    return errors


def parse_json_content(content):
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I)
    return json.loads(content)


def extract(base_url, api_key, model, schema, text, timeout=90):
    prompt = "Extract facts from the document into JSON matching this schema. Use null for unknown values. Return JSON only.\nSCHEMA:\n" + json.dumps(schema, ensure_ascii=False) + "\nDOCUMENT:\n" + text
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0}).encode()
    request = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body, method="POST", headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        payload = json.load(response)
    return parse_json_content(payload["choices"][0]["message"]["content"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--chunk-chars", type=int, default=10000)
    parser.add_argument("--max-chunks", type=int, default=20)
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--model")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--confirm-live-run", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.max_chunks <= 50:
        raise SystemExit("--max-chunks must be between 1 and 50")
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8-sig"))
    text = load_text(args.input).strip()
    if not text:
        raise SystemExit("document contains no extractable text; OCR may be required")
    parts = chunks(text, args.chunk_chars)
    if len(parts) > args.max_chunks:
        raise SystemExit(f"document has {len(parts)} chunks; raise --max-chunks deliberately or reduce scope")
    report = {"input": str(args.input), "characters": len(text), "chunks": len(parts), "schema": schema, "results": []}
    if args.prepare_only:
        report["preview"] = [{"chunk": i + 1, "characters": len(part), "start": part[:160]} for i, part in enumerate(parts)]
    else:
        if not args.confirm_live_run:
            raise SystemExit("live extraction requires --confirm-live-run")
        if not args.model:
            raise SystemExit("--model is required")
        key = os.environ.get(args.api_key_env)
        if not key:
            raise SystemExit("missing API key environment variable: " + args.api_key_env)
        for index, part in enumerate(parts, 1):
            try:
                data = extract(args.base_url, key, args.model, schema, part)
                errors = validate(data, schema)
                report["results"].append({"chunk": index, "data": data, "valid": not errors, "errors": errors})
            except Exception as exc:
                report["results"].append({"chunk": index, "data": None, "valid": False, "errors": [f"{type(exc).__name__}: {exc}"[:500]]})
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"characters": len(text), "chunks": len(parts), "output": args.output}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
