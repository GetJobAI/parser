from __future__ import annotations

from app.schemas.content import ContactInfo, TextBlock
from app.utils.regexes import detect_profile_links, extract_first_email, extract_first_phone, extract_urls
from app.utils.text import blocks_to_text


class ContactParser:
    def parse(self, blocks: list[TextBlock]) -> ContactInfo:
        text = blocks_to_text(blocks)
        lines = [block.text.strip() for block in blocks if block.text.strip()]
        urls = extract_urls(text)
        links = detect_profile_links(urls)

        return ContactInfo(
            full_name=_extract_full_name(lines),
            email=extract_first_email(text),
            phone=extract_first_phone(text),
            location=_extract_location(lines),
            linkedin=links["linkedin"],
            github=links["github"],
            website=links["website"],
            raw_text=text or None,
        )


def _extract_full_name(lines: list[str]) -> str | None:
    for line in lines[:8]:
        words = line.split()
        if not (2 <= len(words) <= 4):
            continue
        if any(char.isdigit() for char in line):
            continue
        if any(symbol in line for symbol in ("@", "http", "|", "/", "\\")):
            continue
        if line.isupper() or all(word[:1].isupper() for word in words):
            return line
    return None


def _extract_location(lines: list[str]) -> str | None:
    for line in lines[:6]:
        for segment in _split_contact_segments(line):
            if "," in segment and not any(char.isdigit() for char in segment):
                return segment

        lower_line = line.lower()
        if any(marker in lower_line for marker in ("@", "http", "linkedin", "github")):
            continue
        if "," in line and not any(char.isdigit() for char in line):
            return line
    return None


def _split_contact_segments(line: str) -> list[str]:
    separators = ("·", "|")
    segments = [line]
    for separator in separators:
        next_segments: list[str] = []
        for segment in segments:
            next_segments.extend(part.strip() for part in segment.split(separator) if part.strip())
        segments = next_segments
    return segments
