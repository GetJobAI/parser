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
        name = _extract_full_name(lines)

        return ContactInfo(
            name=name,
            email=extract_first_email(text),
            phone=extract_first_phone(text),
            location=_extract_location(lines, name),
            linkedin=_strip_scheme(links["linkedin"]),
            github=_strip_scheme(links["github"]),
        )


def _extract_full_name(lines: list[str]) -> str | None:
    for line in lines[:8]:
        for segment in _split_contact_segments(line):
            if "," in segment:
                words = segment.split()
                if len(words) >= 3 and all(word[:1].isupper() for word in words[:2]):
                    return " ".join(words[:2])
            words = segment.split()
            if 2 <= len(words) <= 4 and all(word[:1].isupper() for word in words if word):
                return segment

        words = line.split()
        if not (2 <= len(words) <= 4):
            if "," in line and len(words) >= 3:
                first_two = words[:2]
                if all(word[:1].isupper() for word in first_two):
                    return " ".join(first_two)
            continue
        if any(char.isdigit() for char in line):
            continue
        if any(symbol in line for symbol in ("@", "http", "|", "/", "\\")):
            continue
        if line.isupper() or all(word[:1].isupper() for word in words):
            return line
    return None


def _extract_location(lines: list[str], name: str | None) -> str | None:
    for line in lines[:6]:
        working_line = line
        if name and working_line.startswith(name + " "):
            working_line = working_line[len(name) :].strip()

        for segment in _split_contact_segments(working_line):
            if "," in segment and not any(char.isdigit() for char in segment):
                return segment

        lower_line = working_line.lower()
        if any(marker in lower_line for marker in ("@", "http", "linkedin", "github")):
            continue
        if "," in working_line and not any(char.isdigit() for char in working_line):
            return working_line
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


def _strip_scheme(url: str | None) -> str | None:
    if not url:
        return None
    return url.removeprefix("https://").removeprefix("http://")
