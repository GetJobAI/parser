from __future__ import annotations

import re
from collections.abc import Iterable

from app.schemas.content import TextBlock

WHITESPACE_RE = re.compile(r"\s+")
BULLET_PREFIX_RE = re.compile(r"^[\u2022\u2023\u25E6\u2043\u2219\-\*\▪\‣]\s*")


def collapse_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def normalize_bullet_prefix(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if BULLET_PREFIX_RE.match(text):
        return f"- {BULLET_PREFIX_RE.sub('', text).strip()}"
    return text


def blocks_to_text(blocks: Iterable[TextBlock]) -> str:
    return "\n".join(block.text for block in blocks if block.text.strip()).strip()


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def compact_lines(lines: Iterable[str]) -> list[str]:
    return [collapse_whitespace(line) for line in lines if collapse_whitespace(line)]


def merge_text(left: str, right: str) -> str:
    if left.endswith("-") and right[:1].islower():
        return f"{left[:-1]}{right}"
    return f"{left} {right}".strip()


def is_likely_bullet(line: str) -> bool:
    return normalize_bullet_prefix(line).startswith("- ")


def is_short_line(line: str, *, max_words: int = 8, max_chars: int = 72) -> bool:
    return len(line) <= max_chars and len(line.split()) <= max_words
