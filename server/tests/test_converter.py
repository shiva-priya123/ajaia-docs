"""Unit tests for file → TipTap JSON conversion (no HTTP, no DB)."""
from __future__ import annotations

import io
import json

import pytest
from docx import Document as DocxDocument

from app.upload.converter import (
    ConversionError,
    convert_file_to_tiptap_json,
    html_to_tiptap,
    markdown_to_tiptap,
)


def _marks(node: dict) -> set[str]:
    return {m["type"] for m in node.get("marks", [])}


def _find(node: dict, node_type: str) -> list[dict]:
    """All descendants of the given type (depth-first)."""
    found = [node] if node.get("type") == node_type else []
    for child in node.get("content", []):
        found.extend(_find(child, node_type))
    return found


def _assert_no_empty_text(node: dict) -> None:
    """ProseMirror rejects empty text nodes — the converter must never emit them."""
    if node.get("type") == "text":
        assert node["text"] != ""
    for child in node.get("content", []):
        _assert_no_empty_text(child)


class TestMarkdown:
    def test_headings_marks_and_lists_are_preserved(self) -> None:
        doc = markdown_to_tiptap(
            "# Title\n\n## Section\n\nSome **bold**, *italic*, ~~gone~~ and `code`.\n\n"
            "- one\n- two\n\n1. first\n2. second\n"
        )
        h1, h2 = _find(doc, "heading")
        assert h1["attrs"]["level"] == 1 and h1["content"][0]["text"] == "Title"
        assert h2["attrs"]["level"] == 2

        texts = {t["text"]: _marks(t) for t in _find(doc, "text")}
        assert texts["bold"] == {"bold"}
        assert texts["italic"] == {"italic"}
        assert texts["gone"] == {"strike"}
        assert texts["code"] == {"code"}

        assert len(_find(doc, "bulletList")[0]["content"]) == 2
        assert len(_find(doc, "orderedList")[0]["content"]) == 2
        _assert_no_empty_text(doc)

    def test_fenced_code_and_blockquote(self) -> None:
        doc = markdown_to_tiptap("> quoted\n\n```python\nprint('hi')\n```\n")
        assert _find(doc, "blockquote")
        code = _find(doc, "codeBlock")[0]
        assert code["attrs"]["language"] == "python"
        assert code["content"][0]["text"] == "print('hi')"

    def test_unsupported_html_keeps_text(self) -> None:
        """Links/images have no node in the editor schema: keep the text, drop the wrapper."""
        doc = html_to_tiptap('<p>See <a href="https://x.com">the site</a><img src="a.png"> now</p>')
        assert doc["content"] == [
            {"type": "paragraph", "content": [{"type": "text", "text": "See the site now"}]}
        ]

    def test_list_item_always_starts_with_paragraph(self) -> None:
        doc = html_to_tiptap("<ul><li><ul><li>nested only</li></ul></li></ul>")
        item = _find(doc, "listItem")[0]
        assert item["content"][0]["type"] == "paragraph"


class TestDocx:
    def _docx_bytes(self) -> bytes:
        d = DocxDocument()
        d.add_heading("Quarterly Plan", level=1)
        p = d.add_paragraph("Plain ")
        p.add_run("bold").bold = True
        p.add_run(" and ")
        p.add_run("underlined").underline = True
        d.add_paragraph("First bullet", style="List Bullet")
        d.add_paragraph("Second bullet", style="List Bullet")
        buf = io.BytesIO()
        d.save(buf)
        return buf.getvalue()

    def test_docx_formatting_is_preserved(self) -> None:
        doc = json.loads(convert_file_to_tiptap_json(self._docx_bytes(), "plan.docx"))
        heading = _find(doc, "heading")[0]
        assert heading["attrs"]["level"] == 1
        assert heading["content"][0]["text"] == "Quarterly Plan"

        texts = {t["text"]: _marks(t) for t in _find(doc, "text")}
        assert texts["bold"] == {"bold"}
        assert texts["underlined"] == {"underline"}

        bullets = _find(doc, "bulletList")
        assert bullets and len(bullets[0]["content"]) == 2
        _assert_no_empty_text(doc)

    def test_corrupt_docx_raises_conversion_error(self) -> None:
        with pytest.raises(ConversionError):
            convert_file_to_tiptap_json(b"definitely not a zip file", "broken.docx")


class TestText:
    def test_lines_become_paragraphs(self) -> None:
        doc = json.loads(convert_file_to_tiptap_json(b"line one\n\nline two", "a.txt"))
        assert [n["type"] for n in doc["content"]] == ["paragraph"] * 3
        assert doc["content"][0]["content"][0]["text"] == "line one"
        assert "content" not in doc["content"][1]  # blank line → empty paragraph

    def test_binary_disguised_as_text_is_rejected(self) -> None:
        with pytest.raises(ConversionError):
            convert_file_to_tiptap_json(b"\x00\x01\x02binary", "fake.txt")

    def test_utf8_bom_is_stripped(self) -> None:
        doc = json.loads(convert_file_to_tiptap_json("﻿hello".encode("utf-8"), "bom.txt"))
        assert doc["content"][0]["content"][0]["text"] == "hello"
