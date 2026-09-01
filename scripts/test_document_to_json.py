import json
import tempfile
import unittest
from pathlib import Path

import document_to_json as tool


class DocumentTest(unittest.TestCase):
    def test_html_and_chunks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "a.html")
            path.write_text("<h1>Title</h1><p>Hello</p>", encoding="utf-8")
            self.assertEqual(tool.load_text(path), "Title\nHello")
        self.assertEqual(len(tool.chunks("x" * 1001, 500)), 3)

    def test_schema_validation_and_json_fence(self):
        schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}}
        self.assertEqual(tool.validate({"name": "Ada", "tags": ["a"]}, schema), [])
        self.assertTrue(tool.validate({"tags": [1]}, schema))
        self.assertEqual(tool.parse_json_content("```json\n{\"ok\": true}\n```"), {"ok": True})


if __name__ == "__main__":
    unittest.main()
