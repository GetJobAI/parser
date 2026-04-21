from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.schemas.content import TextBlock
from app.utils.text import collapse_whitespace, merge_text, normalize_bullet_prefix

PUNCTUATION_END_RE = re.compile(r"[.:;!?]$")


def preprocess_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    cleaned = [_clean_block(block) for block in blocks]
    cleaned = [block for block in cleaned if block.text]
    cleaned = _deduplicate_consecutive(cleaned)
    cleaned = _remove_repeated_headers_footers(cleaned)
    cleaned = _join_obvious_wraps(cleaned)

    for order, block in enumerate(cleaned):
        block.order = order
    return cleaned


def _clean_block(block: TextBlock) -> TextBlock:
    text = normalize_bullet_prefix(collapse_whitespace(block.text))
    return TextBlock(
        text=text,
        page=block.page,
        order=block.order,
        x0=block.x0,
        y0=block.y0,
        x1=block.x1,
        y1=block.y1,
    )


def _deduplicate_consecutive(blocks: list[TextBlock]) -> list[TextBlock]:
    deduped: list[TextBlock] = []
    previous_text = None
    for block in blocks:
        if block.text == previous_text:
            continue
        deduped.append(block)
        previous_text = block.text
    return deduped


def _remove_repeated_headers_footers(blocks: list[TextBlock]) -> list[TextBlock]:
    pages: dict[int, list[TextBlock]] = defaultdict(list)
    for block in blocks:
        if block.page is None:
            return blocks
        pages[block.page].append(block)

    if len(pages) < 2:
        return blocks

    top_counter: Counter[str] = Counter()
    bottom_counter: Counter[str] = Counter()

    for page_blocks in pages.values():
        ordered = sorted(
            page_blocks,
            key=lambda block: (
                float("inf") if block.y0 is None else block.y0,
                float("inf") if block.x0 is None else block.x0,
            ),
        )
        for block in ordered[:2]:
            if len(block.text) <= 120:
                top_counter[block.text] += 1
        for block in ordered[-2:]:
            if len(block.text) <= 120:
                bottom_counter[block.text] += 1

    repeated = {text for text, count in top_counter.items() if count >= 2}
    repeated |= {text for text, count in bottom_counter.items() if count >= 2}

    return [
        block
        for block in blocks
        if not (
            block.text in repeated
            and len(block.text) <= 120
            and not any(symbol in block.text for symbol in ("@", "http", "linkedin", "github"))
        )
    ]


def _join_obvious_wraps(blocks: list[TextBlock]) -> list[TextBlock]:
    merged: list[TextBlock] = []
    index = 0

    while index < len(blocks):
        current = blocks[index]
        if index + 1 >= len(blocks):
            merged.append(current)
            break

        nxt = blocks[index + 1]
        if _should_merge(current, nxt):
            merged.append(
                TextBlock(
                    text=merge_text(current.text, nxt.text),
                    page=current.page,
                    order=current.order,
                    x0=current.x0,
                    y0=current.y0,
                    x1=nxt.x1,
                    y1=nxt.y1,
                )
            )
            index += 2
            continue

        merged.append(current)
        index += 1

    return merged


def _should_merge(current: TextBlock, nxt: TextBlock) -> bool:
    if current.page != nxt.page:
        return False
    if current.text.startswith("- ") or nxt.text.startswith("- "):
        return False
    if PUNCTUATION_END_RE.search(current.text):
        return False
    if nxt.text.isupper() and len(nxt.text.split()) <= 4:
        return False
    if current.y1 is not None and nxt.y0 is not None and (nxt.y0 - current.y1) > 18:
        return False
    if current.x0 is not None and nxt.x0 is not None and abs(current.x0 - nxt.x0) > 35:
        return False
    return current.text.endswith("-") or nxt.text[:1].islower() or len(current.text.split()) <= 8
