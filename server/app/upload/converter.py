"""Convert uploaded files into TipTap (ProseMirror) JSON documents.

Pipeline:
    .txt  -> one paragraph per line
    .md   -> HTML (python-markdown) -> TipTap JSON
    .docx -> HTML (mammoth)         -> TipTap JSON

Going through HTML means one well-tested mapping (``html_to_tiptap``) handles
formatting for every rich format. Only node/mark types available in the editor
schema are emitted (TipTap StarterKit + Underline); anything else is reduced to
its plain text so the editor never receives JSON it cannot load.
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any

import markdown as md
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor

SUPPORTED_EXTENSIONS = (".txt", ".md", ".docx")


class ConversionError(ValueError):
    """Raised when a file cannot be turned into a document."""


def convert_file_to_tiptap_json(content: bytes, filename: str) -> str:
    """Convert raw file bytes to a TipTap JSON string based on the file extension."""
    lower = filename.lower()
    if lower.endswith(".txt"):
        doc = text_to_tiptap(_decode_text(content))
    elif lower.endswith(".md"):
        doc = markdown_to_tiptap(_decode_text(content))
    elif lower.endswith(".docx"):
        doc = docx_to_tiptap(content)
    else:
        raise ConversionError(
            f"Unsupported file type. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return json.dumps(doc)


# ── Format-specific entry points ─────────────────────────────────────────────

def text_to_tiptap(text: str) -> dict[str, Any]:
    """Plain text: every line becomes a paragraph (blank lines kept as spacing)."""
    paragraphs: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.strip():
            paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": line}]})
        else:
            paragraphs.append({"type": "paragraph"})
    return _doc(paragraphs)


class _StrikethroughExtension(Extension):
    """GitHub-style ~~strikethrough~~ (not part of core python-markdown)."""

    def extendMarkdown(self, md_instance: md.Markdown) -> None:  # noqa: N802 (library API)
        md_instance.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()~~(.+?)~~", "del"), "strikethrough", 175
        )


def markdown_to_tiptap(text: str) -> dict[str, Any]:
    html = md.markdown(
        text, extensions=["fenced_code", "sane_lists", "tables", _StrikethroughExtension()]
    )
    return html_to_tiptap(html)


# mammoth ignores underline by default; map it explicitly.
_DOCX_STYLE_MAP = "u => u"


def docx_to_tiptap(content: bytes) -> dict[str, Any]:
    import mammoth

    # Skip image extraction entirely — the editor has no image node, and this
    # avoids base64-encoding embedded media into memory for nothing.
    skip_images = mammoth.images.img_element(lambda _image: {})
    try:
        result = mammoth.convert_to_html(
            io.BytesIO(content), style_map=_DOCX_STYLE_MAP, convert_image=skip_images
        )
    except Exception as exc:  # corrupt zip, missing parts, not really a .docx, ...
        raise ConversionError(
            "Could not read this .docx file. It may be corrupted or not a Word document."
        ) from exc
    return html_to_tiptap(result.value)


def _decode_text(content: bytes) -> str:
    if b"\x00" in content[:4096]:
        raise ConversionError("This file does not look like a text file.")
    return content.decode("utf-8-sig", errors="replace")


# ── Minimal DOM built with the stdlib HTML parser ────────────────────────────

_VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "col", "area", "base", "wbr"}


@dataclass
class _El:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[_El | str] = field(default_factory=list)


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _El("root")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        el = _El(tag, {k: v or "" for k, v in attrs})
        self._stack[-1].children.append(el)
        if tag not in _VOID_TAGS:
            self._stack.append(el)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._stack[-1].children.append(_El(tag, {k: v or "" for k, v in attrs}))

    def handle_endtag(self, tag: str) -> None:
        # Pop to the matching open tag; ignore stray closing tags.
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


# ── HTML -> TipTap mapping ───────────────────────────────────────────────────

_MARK_TAGS = {
    "strong": "bold", "b": "bold",
    "em": "italic", "i": "italic",
    "u": "underline", "ins": "underline",
    "s": "strike", "del": "strike", "strike": "strike",
    "code": "code",
}
_HEADINGS = {f"h{n}": n for n in range(1, 7)}
_BLOCK_TAGS = {
    "p", "ul", "ol", "li", "blockquote", "pre", "hr", "table", "thead", "tbody",
    "tfoot", "tr", "div", "section", "article", "header", "footer", "main", "body",
    "html", "dl", "dt", "dd", "figure", "root", *_HEADINGS,
}
_SKIP_TAGS = {"script", "style", "head", "title", "img"}


def html_to_tiptap(html: str) -> dict[str, Any]:
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    return _doc(_blocks(builder.root.children))


def _doc(content: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "doc", "content": content or [{"type": "paragraph"}]}


def _is_block(node: _El | str) -> bool:
    return isinstance(node, _El) and node.tag in _BLOCK_TAGS


def _blocks(children: list[_El | str]) -> list[dict[str, Any]]:
    """Convert a mixed list of children into block nodes, wrapping loose inline runs."""
    out: list[dict[str, Any]] = []
    inline_run: list[_El | str] = []

    def flush() -> None:
        if inline_run:
            content = _inline(inline_run)
            if content:  # drop whitespace-only runs between blocks
                out.append({"type": "paragraph", "content": content})
            inline_run.clear()

    for child in children:
        if isinstance(child, _El) and child.tag in _SKIP_TAGS:
            continue
        if _is_block(child):
            flush()
            out.extend(_block(child))  # type: ignore[arg-type]
        else:
            inline_run.append(child)
    flush()
    return out


def _block(el: _El) -> list[dict[str, Any]]:
    tag = el.tag
    if tag == "p":
        return [_with_content({"type": "paragraph"}, _inline(el.children))]
    if tag in _HEADINGS:
        level = _HEADINGS[tag]
        return [_with_content({"type": "heading", "attrs": {"level": level}}, _inline(el.children))]
    if tag in ("ul", "ol"):
        items = [_list_item(c) for c in el.children if isinstance(c, _El) and c.tag == "li"]
        if not items:
            return []
        node: dict[str, Any] = {"type": "bulletList" if tag == "ul" else "orderedList", "content": items}
        if tag == "ol":
            node["attrs"] = {"start": _int(el.attrs.get("start"), 1)}
        return [node]
    if tag == "li":  # stray <li> outside a list
        return [{"type": "bulletList", "content": [_list_item(el)]}]
    if tag == "blockquote":
        return [{"type": "blockquote", "content": _blocks(el.children) or [{"type": "paragraph"}]}]
    if tag == "pre":
        return [_code_block(el)]
    if tag == "hr":
        return [{"type": "horizontalRule"}]
    if tag == "tr":
        return [_table_row(el)]
    # Transparent containers (div, table, tbody, section, ...)
    return _blocks(el.children)


def _list_item(li: _El) -> dict[str, Any]:
    content = _blocks(li.children)
    # ProseMirror schema: listItem = paragraph block*
    if not content or content[0]["type"] != "paragraph":
        content.insert(0, {"type": "paragraph"})
    return {"type": "listItem", "content": content}


def _code_block(pre: _El) -> dict[str, Any]:
    language = None
    for child in pre.children:
        if isinstance(child, _El) and child.tag == "code":
            for cls in child.attrs.get("class", "").split():
                if cls.startswith("language-"):
                    language = cls[len("language-"):]
    text = _text_content(pre).rstrip("\n")
    node: dict[str, Any] = {"type": "codeBlock", "attrs": {"language": language}}
    if text:
        node["content"] = [{"type": "text", "text": text}]
    return node


def _table_row(tr: _El) -> dict[str, Any]:
    """No table node in the editor schema: render a row as 'cell | cell | cell'."""
    content: list[dict[str, Any]] = []
    cells = [c for c in tr.children if isinstance(c, _El) and c.tag in ("td", "th")]
    for i, cell in enumerate(cells):
        if i:
            content.append({"type": "text", "text": " | "})
        cell_inline = _inline(_flatten_blocks(cell.children))
        if cell.tag == "th":
            cell_inline = [_add_mark(n, "bold") for n in cell_inline]
        content.extend(cell_inline)
    return _with_content({"type": "paragraph"}, _merge_text(content))


def _flatten_blocks(children: list[_El | str]) -> list[_El | str]:
    """Inline view of block content (used inside table cells)."""
    out: list[_El | str] = []
    for child in children:
        if _is_block(child):
            if out:
                out.append(" ")
            out.extend(_flatten_blocks(child.children))  # type: ignore[union-attr]
        else:
            out.append(child)
    return out


def _inline(nodes: list[_El | str]) -> list[dict[str, Any]]:
    """Convert inline HTML to TipTap text/hardBreak nodes with collapsed whitespace."""
    raw: list[dict[str, Any]] = []
    _collect_inline(nodes, [], raw)

    # Collapse whitespace like a browser would.
    for node in raw:
        if node["type"] == "text":
            node["text"] = re.sub(r"\s+", " ", node["text"])
    # Trim at the edges of the block and around hard breaks.
    for i, node in enumerate(raw):
        if node["type"] != "text":
            continue
        prev_is_edge = i == 0 or raw[i - 1]["type"] == "hardBreak"
        next_is_edge = i == len(raw) - 1 or raw[i + 1]["type"] == "hardBreak"
        if prev_is_edge:
            node["text"] = node["text"].lstrip()
        if next_is_edge:
            node["text"] = node["text"].rstrip()
    # Drop double spaces created at element boundaries ("a " + " b").
    for i in range(1, len(raw)):
        a, b = raw[i - 1], raw[i]
        if a["type"] == "text" and b["type"] == "text" and a["text"].endswith(" ") and b["text"].startswith(" "):
            b["text"] = b["text"][1:]
    # ProseMirror forbids empty text nodes.
    cleaned = [n for n in raw if n["type"] != "text" or n["text"]]
    while cleaned and cleaned[-1]["type"] == "hardBreak":
        cleaned.pop()
    return _merge_text(cleaned)


def _collect_inline(nodes: list[_El | str], marks: list[str], out: list[dict[str, Any]]) -> None:
    for node in nodes:
        if isinstance(node, str):
            text_node: dict[str, Any] = {"type": "text", "text": node}
            if marks:
                text_node["marks"] = [{"type": m} for m in marks]
            out.append(text_node)
            continue
        if node.tag in _SKIP_TAGS:
            continue
        if node.tag == "br":
            out.append({"type": "hardBreak"})
            continue
        mark = _MARK_TAGS.get(node.tag)
        child_marks = marks + [mark] if mark and mark not in marks else marks
        # Links, spans, sup/sub, etc. are unwrapped: text kept, wrapper dropped.
        _collect_inline(node.children, child_marks, out)


def _merge_text(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for node in nodes:
        prev = merged[-1] if merged else None
        if (
            prev is not None
            and node["type"] == "text"
            and prev["type"] == "text"
            and prev.get("marks") == node.get("marks")
        ):
            prev["text"] += node["text"]
        else:
            merged.append(dict(node))
    return merged


def _add_mark(node: dict[str, Any], mark: str) -> dict[str, Any]:
    if node["type"] != "text":
        return node
    marks = node.get("marks", [])
    if any(m["type"] == mark for m in marks):
        return node
    return {**node, "marks": [*marks, {"type": mark}]}


def _with_content(node: dict[str, Any], content: list[dict[str, Any]]) -> dict[str, Any]:
    if content:
        node["content"] = content
    return node


def _text_content(el: _El) -> str:
    parts: list[str] = []
    for child in el.children:
        parts.append(child if isinstance(child, str) else _text_content(child))
    return "".join(parts)


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default
