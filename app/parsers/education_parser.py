from __future__ import annotations

import re

from app.schemas.content import EducationEntry, TextBlock
from app.utils.regexes import extract_date_range

DEGREE_MARKERS = {
    "bachelor",
    "master",
    "phd",
    "doctor",
    "associate",
    "b.sc",
    "m.sc",
    "bs",
    "ms",
    "mba",
    "certificate",
    "vocational",
}
INSTITUTION_MARKERS = {"university", "college", "school", "institute", "academy", "faculty"}
class EducationParser:
    def parse(self, blocks: list[TextBlock]) -> list[EducationEntry]:
        lines = [block.text for block in blocks if block.text.strip()]
        if not lines:
            return []

        entries = [self._parse_entry(group) for group in self._split_entries(lines)]
        return [entry for entry in entries if any([entry.institution, entry.degree, entry.dates, entry.location, entry.grade])]

    def _split_entries(self, lines: list[str]) -> list[list[str]]:
        entries: list[list[str]] = []
        current: list[str] = []

        for line in lines:
            if current and self._starts_new_entry(line, current):
                entries.append(current)
                current = [line]
                continue
            current.append(line)

        if current:
            entries.append(current)

        return entries

    def _starts_new_entry(self, line: str, current: list[str]) -> bool:
        if extract_date_range(line) and any(extract_date_range(existing) for existing in current):
            return True
        lower_line = line.lower()
        return any(marker in lower_line for marker in INSTITUTION_MARKERS) and len(current) >= 2

    def _parse_entry(self, lines: list[str]) -> EducationEntry:
        date_range_raw = next((extract_date_range(line) for line in lines if extract_date_range(line)), None)
        cleaned_lines = [_remove_date_text(line) for line in lines if _remove_date_text(line)]

        location = next((_extract_location(line) for line in cleaned_lines if _extract_location(line)), None)

        institution = next(
            (line for line in cleaned_lines if any(marker in line.lower() for marker in INSTITUTION_MARKERS)),
            cleaned_lines[0] if cleaned_lines else None,
        )

        if institution and _contains_degree_marker(institution):
            institution, inline_degree = _split_institution_and_degree(institution)
        else:
            inline_degree = None

        degree_line = inline_degree or next(
            (line for line in cleaned_lines if any(marker in line.lower() for marker in DEGREE_MARKERS)),
            None,
        )
        if degree_line and institution and degree_line.startswith(institution):
            degree_line = degree_line[len(institution) :].strip(" ,")
        degree, field = _split_degree_and_field(degree_line)
        grade = next(
            (
                line.split("Grade:", maxsplit=1)[1].strip()
                for line in lines
                if "grade:" in line.lower()
            ),
            None,
        )
        combined_degree = degree
        if degree and field:
            combined_degree = f"{degree} — {field}"

        return EducationEntry(
            institution=_strip_location(institution),
            degree=combined_degree,
            dates=date_range_raw,
            location=location,
            grade=grade,
        )


def _split_degree_and_field(line: str | None) -> tuple[str | None, str | None]:
    if not line:
        return None, None
    cleaned = _remove_date_text(line)
    if cleaned is None:
        return None, None
    cleaned = re.sub(r"\bGrade:\s*.+$", "", cleaned, flags=re.IGNORECASE).strip(" ,")
    location = _extract_location(cleaned)
    if location:
        cleaned = cleaned[: cleaned.rfind(location)].strip(" ,")
    if " in " in cleaned.lower():
        parts = re.split(r"\bin\b", cleaned, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            return parts[0].strip() or None, parts[1].strip() or None
    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",", maxsplit=1)]
        if len(parts) == 2:
            return parts[0] or None, parts[1] or None
    if "—" in cleaned:
        parts = [part.strip() for part in cleaned.split("—", maxsplit=1)]
        if len(parts) == 2:
            return parts[0] or None, parts[1] or None
    return cleaned or None, None


def _remove_date_text(line: str | None) -> str | None:
    if line is None:
        return None
    date_range = extract_date_range(line)
    if not date_range:
        return line.strip()
    return line.replace(date_range, "").strip(" |,-")


def _extract_location(line: str) -> str | None:
    cleaned = re.sub(r"\bGrade:\s*.+$", "", line, flags=re.IGNORECASE).strip()
    if "," not in cleaned:
        return None
    left, right = cleaned.rsplit(",", maxsplit=1)
    country = right.strip()
    if not country or any(char.isdigit() for char in country):
        return None
    left_tokens = left.strip().split()
    if not left_tokens:
        return None
    city = left_tokens[-1]
    return f"{city}, {country}".strip() or None


def _strip_location(line: str | None) -> str | None:
    if line is None:
        return None
    stripped = line.strip()
    location = _extract_location(stripped)
    if not location or not stripped.endswith(location):
        return stripped
    return stripped[: -len(location)].strip(" ,") or None


def _contains_degree_marker(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in DEGREE_MARKERS)


def _split_institution_and_degree(line: str) -> tuple[str | None, str | None]:
    lowered = line.lower()
    positions = [lowered.find(marker) for marker in DEGREE_MARKERS if marker in lowered]
    if not positions:
        return _strip_location(line), None
    index = min(position for position in positions if position >= 0)
    institution = _strip_location(line[:index])
    degree_part = _strip_location(line[index:])
    return institution, degree_part
