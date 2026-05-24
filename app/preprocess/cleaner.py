from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.schemas.content import TextBlock
from app.utils.regexes import extract_date_range
from app.utils.text import collapse_whitespace, merge_text, normalize_bullet_prefix

PUNCTUATION_END_RE = re.compile(r"[.:;!?]$")
SECTION_HEADER_NAMES = (
    "SUMMARY",
    "EXPERIENCE",
    "EDUCATION",
    "SKILLS",
    "CERTIFICATIONS",
    "LANGUAGES",
    "PROJECTS",
    "CONTACT",
)
SECTION_HEADER_RE = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in SECTION_HEADER_NAMES) + r")\b",
)
LEADING_SECTION_RE = re.compile(
    r"^\s*(" + "|".join(re.escape(name) for name in SECTION_HEADER_NAMES) + r")\b(?:\s*[:|])?\s+(.+)$",
)
TRAILING_COMPANY_RE = re.compile(
    r"^(?P<bullet>- .+?)\.\s+(?P<company>[A-Z].*(?:sp\. z o\.o\.|inc|llc|ltd|corp|gmbh|plc))\.?$",
    re.IGNORECASE,
)


def preprocess_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    cleaned: list[TextBlock] = []
    for block in blocks:
        cleaned.extend(_clean_block(block))
    cleaned = [block for block in cleaned if block.text.strip()]
    cleaned = _deduplicate_consecutive(cleaned)
    cleaned = _remove_repeated_headers_footers(cleaned)
    cleaned = _join_obvious_wraps(cleaned)

    for order, block in enumerate(cleaned):
        block.order = order
    return cleaned


def _clean_block(block: TextBlock) -> list[TextBlock]:
    text = normalize_bullet_prefix(collapse_whitespace(block.text))
    if not text:
        return []

    fragments = [text]
    fragments = _split_embedded_section_headers(fragments)
    fragments = _split_leading_section_headers(fragments)
    fragments = _split_inline_bullets(fragments)
    fragments = _split_mixed_bullet_and_entry_lines(fragments)
    fragments = _split_trailing_company_suffixes(fragments)

    return [
        TextBlock(
            text=fragment,
            page=block.page,
            order=block.order,
            x0=block.x0,
            y0=block.y0,
            x1=block.x1,
            y1=block.y1,
        )
        for fragment in fragments
        if fragment
    ]


def _split_embedded_section_headers(fragments: list[str]) -> list[str]:
    result: list[str] = []
    for text in fragments:
        matches = [match for match in SECTION_HEADER_RE.finditer(text) if _is_valid_header_boundary(text, match.start())]
        if len(matches) <= 1:
            result.append(text)
            continue

        split_points = [match.start() for match in matches]
        split_points.append(len(text))
        for index, start in enumerate(split_points[:-1]):
            end = split_points[index + 1]
            chunk = text[start:end].strip(" -|")
            if chunk:
                result.append(chunk)
    return result


def _split_leading_section_headers(fragments: list[str]) -> list[str]:
    result: list[str] = []
    for text in fragments:
        match = LEADING_SECTION_RE.match(text)
        if not match:
            result.append(text)
            continue

        header = match.group(1).upper()
        body = match.group(2).strip()
        result.append(header)
        if body:
            result.append(body)
    return result


def _split_inline_bullets(fragments: list[str]) -> list[str]:
    result: list[str] = []
    for text in fragments:
        if "•" not in text:
            result.append(text)
            continue

        starts_as_bullet = text.startswith("- ")
        parts = [part.strip(" -") for part in text.split("•") if part.strip(" -")]
        if len(parts) <= 1:
            result.append(text)
            continue

        if starts_as_bullet:
            result.append(f"- {parts[0]}")
        else:
            result.append(parts[0])
        result.extend(f"- {part}" for part in parts[1:])
    return result


def _split_mixed_bullet_and_entry_lines(fragments: list[str]) -> list[str]:
    result: list[str] = []
    for text in fragments:
        if not text.startswith("- "):
            result.append(text)
            continue

        date_range = extract_date_range(text)
        if not date_range:
            result.append(text)
            continue

        date_index = text.find(date_range)
        sentence_boundary = text.rfind(". ", 0, date_index)
        if sentence_boundary == -1 or sentence_boundary < 10:
            result.append(text)
            continue

        bullet_part = text[: sentence_boundary + 1].strip()
        entry_part = text[sentence_boundary + 2 :].strip()
        if bullet_part:
            result.append(bullet_part)
        if entry_part:
            result.append(entry_part)
    return result


def _split_trailing_company_suffixes(fragments: list[str]) -> list[str]:
    result: list[str] = []
    for text in fragments:
        match = TRAILING_COMPANY_RE.match(text)
        if not match:
            result.append(text)
            continue

        bullet_part = match.group("bullet").strip()
        company_part = match.group("company").strip().rstrip(".")
        if bullet_part:
            result.append(f"{bullet_part}.")
        if company_part:
            result.append(company_part)
    return result


def _is_valid_header_boundary(text: str, index: int) -> bool:
    if index == 0:
        return True
    previous_char = text[index - 1]
    return previous_char.isspace() or previous_char in "|-—–/:;"


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
    repeated = _find_repeated_headers_footers(blocks)
    if not repeated:
        return blocks

    return [
        block
        for block in blocks
        if not (
            block.text in repeated
            and len(block.text) <= 120
            and not any(symbol in block.text for symbol in ("@", "http", "linkedin", "github"))
        )
    ]


def detect_repeated_headers_footers(blocks: list[TextBlock]) -> bool:
    return bool(_find_repeated_headers_footers(blocks))


def _find_repeated_headers_footers(blocks: list[TextBlock]) -> set[str]:
    pages: dict[int, list[TextBlock]] = defaultdict(list)
    for block in blocks:
        if block.page is None:
            return set()
        pages[block.page].append(block)

    if len(pages) < 2:
        return set()

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
    return repeated


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
    if _is_section_header_line(current.text) or _is_section_header_line(nxt.text):
        return False
    if _looks_like_name_line(current.text) and _contains_contact_markers(nxt.text):
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


def _is_section_header_line(text: str) -> bool:
    stripped = text.strip(" :|-")
    return bool(SECTION_HEADER_RE.fullmatch(stripped))


def _contains_contact_markers(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("@", "http", "linkedin", "github", ".com", ".io"))


def _looks_like_name_line(text: str) -> bool:
    words = text.strip().split()
    if not (2 <= len(words) <= 4):
        return False
    if any(char.isdigit() for char in text):
        return False
    if any(symbol in text for symbol in ("@", "http", "|", "/", "\\")):
        return False
    return all(word[:1].isupper() for word in words if word)
