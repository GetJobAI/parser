from __future__ import annotations

import re

from app.schemas.content import EducationEntry, TextBlock
from app.utils.regexes import extract_date_range, split_date_range

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
}
INSTITUTION_MARKERS = {"university", "college", "school", "institute", "academy", "faculty"}


class EducationParser:
    def parse(self, blocks: list[TextBlock]) -> list[EducationEntry]:
        lines = [block.text for block in blocks if block.text.strip()]
        if not lines:
            return []

        entries = [self._parse_entry(group) for group in self._split_entries(lines)]
        return [entry for entry in entries if entry.raw_text]

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
        raw_text = "\n".join(lines).strip()
        date_range_raw = next((extract_date_range(line) for line in lines if extract_date_range(line)), None)
        start_date, end_date = split_date_range(date_range_raw)

        institution = next(
            (line for line in lines if any(marker in line.lower() for marker in INSTITUTION_MARKERS)),
            lines[0] if lines else None,
        )
        degree_line = next(
            (line for line in lines if any(marker in line.lower() for marker in DEGREE_MARKERS)),
            None,
        )
        degree, field = _split_degree_and_field(degree_line)
        location = next(
            (
                line
                for line in lines
                if "," in line and not any(char.isdigit() for char in line)
            ),
            None,
        )

        return EducationEntry(
            institution=_remove_date_text(institution),
            degree=degree,
            field=field,
            start_date=start_date,
            end_date=end_date,
            date_range_raw=date_range_raw,
            location=location,
            raw_text=raw_text or None,
        )


def _split_degree_and_field(line: str | None) -> tuple[str | None, str | None]:
    if not line:
        return None, None
    cleaned = _remove_date_text(line)
    if " in " in cleaned.lower():
        parts = re.split(r"\bin\b", cleaned, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            return parts[0].strip() or None, parts[1].strip() or None
    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",", maxsplit=1)]
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
